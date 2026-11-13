"""Propuestas de esquemas basadas en lo que el programa demuestra."""

from __future__ import annotations

import re

from sgm.compile import compile_file, project_base
from sgm.flow.model import build_flows
from sgm.frontend.program import analyze_program
from sgm.ir.builder import qualify
from sgm.ir.models import Column, Plan
from sgm.migrar.esquemas import PendienteMigracion, esquemas_de_entrada
from sgm.migrar.esquemas_limpieza import mascara_codigo
from sgm.migrar.esquemas_tipos import _columnas_numericas
from sgm.proceso.columnas_fuente import columnas_usadas
from sgm.proceso.entradas_salidas import entradas_y_salidas


def _nombre_literal(nombre: str) -> bool:
    partes = nombre.split(".")
    return len(partes) == 2 and all(p.isidentifier() for p in partes)


def _fuentes(texto: str, nombre: str):
    for modelo in build_flows({nombre: texto}).values():
        for fuente in entradas_y_salidas(modelo, {}).fuentes:
            if fuente.tipo == "tabla_base":
                yield fuente.ubicacion


def _copias(texto: str):
    limpio = mascara_codigo(texto)
    patron = r"\bdata\s+([\w.]+)\s*;\s*(.*?)\brun\s*;"
    for match in re.finditer(patron, limpio, re.I | re.S):
        destino, cuerpo = match.groups()
        copia = re.fullmatch(r"\s*set\s+([\w.]+)\s*;\s*", cuerpo, re.I | re.S)
        origen = re.search(r"\bset\s+([\w.]+)", cuerpo, re.I)
        if origen:
            yield (
                destino,
                origen.group(1),
                bool(copia),
                texto.count("\n", 0, match.start()) + 1,
                match.end(),
            )


def _columnas_copia(texto: str, destino: str, desde: int) -> list[str]:
    """Limita las columnas a la versión de la copia antes de otra escritura."""
    restante = texto[desde:]
    limpio = mascara_codigo(restante)
    nombre = qualify(destino).lower()
    patron = r"(?i)\b(?:data\s+|create\s+table\s+|out\s*=\s*)([\w.]+)"
    for escritura in re.finditer(patron, limpio):
        if qualify(escritura.group(1)).lower() == nombre:
            restante = restante[: escritura.start()]
            break
    buscado = nombre[5:] if nombre.startswith("work.") else nombre
    return columnas_usadas(restante, buscado)


def _numericas_por_lectura(plan: Plan) -> dict[str, set[str]]:
    """Demuestra tipos solo en expresiones conectadas directamente a una lectura única."""
    resultado: dict[str, set[str]] = {}
    for op in plan.graph.operators():
        previos = plan.graph.predecessors(op.id)
        if len(previos) != 1:
            continue
        previo = plan.graph.operator(previos[0])
        if previo.kind == "read":
            anteriores = plan.graph.predecessors(previo.id)
            if len(anteriores) == 1:
                previo = plan.graph.operator(anteriores[0])
        if previo.kind == "read_file":
            nombres = previo.params.get("outputs") or []
        elif previo.kind == "read" and not plan.graph.predecessors(previo.id):
            nombres = [previo.params.get("dataset")]
        else:
            continue
        parcial = Plan(program=plan.program)
        parcial.graph.add_operator(op)
        numericas = _columnas_numericas(parcial)
        for nombre in nombres:
            if nombre:
                resultado.setdefault(str(nombre).lower(), set()).update(numericas)
    return resultado


def _detalle_fuentes(texto: str, nombre: str, atribuir_copias: bool):
    vistas = {}
    omitidas = []
    copias = list(_copias(texto)) if atribuir_copias else []
    for fuente in _fuentes(texto, nombre):
        clave = fuente.lower()
        if clave in vistas:
            continue
        if not _nombre_literal(fuente):
            omitidas.append((fuente, "nombre no literal biblioteca.tabla"))
            continue
        columnas = columnas_usadas(texto, fuente)
        for destino, origen, simple, _, desde in copias:
            if simple and origen.lower() == clave:
                columnas.extend(_columnas_copia(texto, destino, desde))
        unicas = list({c.lower(): c for c in reversed(columnas)}.values())[::-1]
        if not unicas:
            omitidas.append((fuente, "el programa no usa columnas identificables"))
            continue
        vistas[clave] = unicas
    return vistas, omitidas


def tablas_base_del_programa(
    texto: str, nombre: str = "programa", atribuir_copias: bool = True
) -> dict[str, list[str]]:
    """Devuelve columnas usadas de fuentes literales, opcionalmente atribuyendo copias simples."""
    return _detalle_fuentes(texto, nombre, atribuir_copias)[0]


def esquemas_desde_programa(
    texto: str, nombre: str = "programa", fixtures: dict[str, list[Column]] | None = None
):
    """Infiera solo tipos demostrados y deje pendientes los tipos desconocidos."""
    archivo = f"{nombre}.sas"
    plan = compile_file(analyze_program({archivo: texto}), archivo, project_base()).plan
    esquemas, pendientes = esquemas_de_entrada(plan, {}, None)
    pendientes = [p for p in pendientes if p.codigo != "P-TIPO-DESCONOCIDO"]
    tipos_input = {
        str(salida).lower(): {str(k).lower() for k in (op.params.get("input_types") or {})}
        for op in plan.graph.operators()
        if op.kind == "read_file"
        for salida in op.params.get("outputs") or []
    }
    numericas = _numericas_por_lectura(plan)
    for tabla, columnas in list(esquemas.items()):
        esquemas[tabla] = [
            Column(
                c.name,
                (
                    "String"
                    if c.type == "Double"
                    and c.name.lower() not in numericas.get(tabla, set())
                    and c.name.lower() not in tipos_input.get(tabla, set())
                    else c.type
                ),
                c.length,
                "unknown"
                if c.name.lower() not in tipos_input.get(tabla, set())
                and (c.type == "String" or c.name.lower() not in numericas.get(tabla, set()))
                else c.source,
            )
            for c in columnas
        ]
    bases, omitidas = _detalle_fuentes(texto, archivo, True)
    for tabla, columnas in bases.items():
        esquemas.setdefault(
            tabla,
            [
                Column(c, "Double", None, "derived")
                if c.lower() in numericas.get(tabla, set())
                else Column(c, "String", None, "unknown")
                for c in columnas
            ],
        )
    for destino, origen, simple, linea, desde in _copias(texto):
        if not simple and _nombre_literal(origen) and _columnas_copia(texto, destino, desde):
            pendientes.append(
                PendienteMigracion(
                    "P-COLUMNAS-NO-ATRIBUIDAS",
                    f"{origen}: copia con operaciones que cambian columnas",
                    linea,
                )
            )
    dinamicas = [nombre for nombre, motivo in omitidas if motivo.startswith("nombre no literal")]
    dinamicas.extend(re.findall(r"(?i)\b(?:from|join|set)\s+(&[\w.]+)", texto))
    for dinamica in dict.fromkeys(dinamicas):
        pendientes.append(
            PendienteMigracion("P-TABLA-DINAMICA", f"{dinamica}: nombre de tabla dinámico", None)
        )
    fichas = {k.lower(): {c.name.lower(): c for c in v} for k, v in (fixtures or {}).items()}
    for tabla, columnas in esquemas.items():
        for i, columna in enumerate(columnas):
            ficha = fichas.get(tabla.lower(), {}).get(columna.name.lower())
            if ficha:
                columnas[i] = Column(ficha.name, ficha.type, ficha.length, "fixture")
        desconocidas = [c.name for c in columnas if c.source == "unknown" or c.type is None]
        if desconocidas:
            match = re.search(re.escape(tabla), texto, re.I)
            linea = texto.count("\n", 0, match.start()) + 1 if match else None
            pendientes.append(
                PendienteMigracion(
                    "P-TIPO-DESCONOCIDO",
                    f"{tabla}: sin tipo demostrado: {', '.join(desconocidas)}",
                    linea,
                )
            )
    return esquemas, pendientes


def a_json(esquemas: dict[str, list[Column]], programa: str) -> dict[str, dict]:
    """Serializa la propuesta sin presentar como demostrado el tipo por omisión."""
    salida = {}
    for nombre, columnas in esquemas.items():
        biblioteca, _, tabla = nombre.lower().partition(".")
        if not tabla:
            biblioteca, tabla = "work", biblioteca
        esquema = salida.setdefault(
            biblioteca,
            {
                "schema": biblioteca,
                "source": f"inferido del programa {programa}",
                "_inferido": True,
                "tables": {},
            },
        )
        esquema["tables"][tabla] = [
            {"name": c.name, "type": None if c.source == "unknown" else c.type, "source": c.source}
            for c in columnas
        ]
    return salida
