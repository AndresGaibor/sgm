"""Generador de joblets por grupo de regiones, joblet de contexto y Job padre (fase de diseño).

Pasos deterministas:
1. Regiones: cada definición de la macro que más veces se define en el programa (empates: la que
   aparece antes en el archivo). No se usa ningún nombre de cliente.
2. Grupos: `sgm.agrupacion` (vocabulario de conjuntos de datos, sin palabras comunes), con el
   umbral que el equipo fijó en `UMBRAL_DE_AGRUPACION`. Si el equipo declaró la agrupación en
   `decisiones/`, se usa esa en lugar de la similitud: es una decisión, no un hecho del SAS.
3. Joblet por grupo: unión de firmas de componente distintas de sus miembros, en orden de primera
   aparición. Cada miembro aporta un contexto con los conjuntos de datos que usa, en orden.
4. Joblet de contexto: las sentencias de entorno del encabezado del programa (macrovariables,
   opciones de sesión remota, transferencias y codificación de contraseña) y las variables de
   contexto que el archivo permite declarar. El resto del encabezado se queda en el Job padre.

Lo que varía entre miembros (nombres y literales) queda en los contextos, no en el joblet.
"""

from __future__ import annotations

import bisect
import re
from collections import Counter, defaultdict

from sgm.agrupacion import (
    Declaracion,
    agrupar,
    grupos_declarados,
    inicios_de,
    palabras_por_region,
)
from sgm.facts.model import MASK, Fact

_DEF_MACRO = re.compile(r"^\s*%macro\s+([A-Za-z_]\w*)", re.I)
# Sentencias que describen el entorno de ejecución, no el flujo de datos.
_DE_CONTEXTO = re.compile(
    r"^\s*(?:%let\b|proc\s+(?:pwencode|download)\b|rsubmit\b|signon\b|signoff\b|endrsubmit\b)",
    re.I,
)
_OPTIONS_REMOTO = re.compile(r"^\s*options\b[^;]*\bremote\s*=", re.I)
_INTO = re.compile(r"\binto\s*:\s*([A-Za-z_]\w*)", re.I)
_LET = re.compile(r"^\s*%let\s+([A-Za-z_]\w*)", re.I)
# Un componente real es el que tiene nombre propio; `tRunJob` es una llamada, no un componente.
_SIN_COMPONENTE = (None, "none", "-", "tRunJob")

UMBRAL_DE_AGRUPACION = 0.2
"""Umbral de Jaccard entre regiones. Decisión del equipo (3 de noviembre de 2026): 0,2 deja dos
joblets y el canvas más chico; 0,3 dejaría cinco joblets y tres nodos más en el Job padre."""


def marcador_de_regiones(lineas: list[str]) -> list[int]:
    """Líneas donde empieza cada región: definiciones de la macro más repetida del programa."""
    nombres = []
    for i, linea in enumerate(lineas):
        m = _DEF_MACRO.match(linea)
        if m:
            nombres.append((i + 1, m.group(1).lower()))
    conteo = Counter(n for _, n in nombres)
    if not conteo:
        return []
    repetida = max(conteo.values())
    if repetida < 2:
        return []
    ganador = next(n for _, n in nombres if conteo[n] == repetida)
    return [i for i, n in nombres if n == ganador]


def _reparto(
    plan_ops, hechos: list[Fact], lineas: list[str], declaracion: Declaracion | None = None
):
    """Inicios de región, grupos de dos o más miembros y operadores por región (sin región: -1)."""
    if declaracion is not None:
        inicios = inicios_de(lineas, declaracion.marcador)
        grupos = list(grupos_declarados(hechos, inicios, declaracion))
    else:
        inicios = marcador_de_regiones(lineas)
        grupos = [
            g
            for g in agrupar(palabras_por_region(hechos, inicios), UMBRAL_DE_AGRUPACION).grupos
            if len(g) >= 2
        ] if len(inicios) >= 2 else []
    if len(inicios) < 2:
        return inicios, [], {}
    por_region: dict[int, list] = defaultdict(list)
    for op in plan_ops:
        if op.evidence:
            por_region[bisect.bisect_right(inicios, op.evidence[0].line_start) - 1].append(op)
    return inicios, grupos, por_region


def _es_componente(op) -> bool:
    return (op.component or {}).get("name") not in _SIN_COMPONENTE


def _componentes(ops) -> list:
    """Los operadores que son componentes con nombre, en orden (cada aparición cuenta)."""
    return [op for op in ops if _es_componente(op)]


def _firmas(ops) -> list[str]:
    """Firmas de componente distintas, en orden de primera aparición."""
    firmas: list[str] = []
    for op in _componentes(ops):
        if op.signature not in firmas:
            firmas.append(op.signature)
    return firmas


def _datasets_por_region(hechos: list[Fact], inicios: list[int]) -> dict[int, list[str]]:
    datasets: dict[int, list[str]] = defaultdict(list)
    for h in hechos:
        if h.tipo not in ("tabla_escrita", "tabla_leida") or h.detalle.get("dinamico") == "si":
            continue
        r = bisect.bisect_right(inicios, h.linea_inicio) - 1
        if r >= 0 and h.valor not in datasets[r]:
            datasets[r].append(h.valor)
    return datasets


def _joblets_de(grupos, por_region, datasets) -> list[dict]:
    salida = []
    for k, grupo in enumerate(grupos, 1):
        firmas = _firmas(op for r in grupo for op in por_region.get(r, []))
        contextos = [
            {f"tabla_{i + 1}": v for i, v in enumerate(datasets.get(r, []))} for r in grupo
        ]
        salida.append(
            {
                "id": f"jl_grupo_{k:02d}",
                "miembros": len(grupo),
                "regiones": list(grupo),
                "firmas_de_componente": len(firmas),
                "contextos": contextos,
            }
        )
    return salida


def joblets_por_grupo(
    plan_ops, hechos: list[Fact], lineas: list[str], declaracion: Declaracion | None = None
) -> list[dict]:
    """Un joblet por grupo de dos o más regiones, con sus contextos por miembro."""
    inicios, grupos, por_region = _reparto(plan_ops, hechos, lineas, declaracion)
    if not grupos:
        return []
    return _joblets_de(grupos, por_region, _datasets_por_region(hechos, inicios))


def operadores_de_contexto(plan_ops, lineas: list[str], fin: int) -> list:
    """Operadores del encabezado cuya fuente describe el entorno de ejecución."""
    return [
        op
        for op in plan_ops
        if op.evidence
        and op.evidence[0].line_start < fin
        and (
            _DE_CONTEXTO.match(lineas[op.evidence[0].line_start - 1])
            or _OPTIONS_REMOTO.match(lineas[op.evidence[0].line_start - 1])
        )
    ]


def _valores(hechos: list[Fact], tipo: str) -> list[str]:
    valores: list[str] = []
    for h in hechos:
        if h.tipo == tipo and h.valor not in valores:
            valores.append(h.valor)
    return valores


def _variables_de_contexto(
    hechos_encabezado: list[Fact], lineas_encabezado: list[str]
) -> list[dict]:
    """Variables que el archivo permite declarar, con valor observado o como pendiente."""
    variables: list[dict] = []
    # Un `rsubmit` sobre una macrovariable no es un servidor: es el nombre de la variable.
    macrovariables = {
        m.group(1).lower() for linea in lineas_encabezado if (m := _LET.match(linea))
    }
    servidores = [
        v for v in _valores(hechos_encabezado, "servidor") if v.lower() not in macrovariables
    ]
    if servidores:
        variables.append(
            {
                "nombre": "servidor_remoto",
                "tipo": "String",
                "valor": servidores,
                "origen": "sesión remota del archivo",
            }
        )
    motores = _valores(hechos_encabezado, "conexion_base")
    if motores:
        variables.append(
            {
                "nombre": "base_de_datos",
                "tipo": "String",
                "valor": motores,
                "origen": "conexiones SQL del archivo",
            }
        )
    if any(h.tipo == "credencial" for h in hechos_encabezado):
        variables.append(
            {
                "nombre": "credencial",
                "tipo": "String",
                "valor": MASK,
                "origen": "el archivo la trae codificada; nunca en claro",
            }
        )
    vistos: list[str] = []
    for linea in lineas_encabezado:
        for m in _INTO.finditer(linea):
            nombre = m.group(1).lower()
            if nombre in vistos:
                continue
            vistos.append(nombre)
            variables.append(
                {
                    "nombre": nombre,
                    "tipo": "String",
                    "valor": None,
                    "origen": f"SELECT ... INTO: {nombre}",
                    "pendiente": {
                        "motivo": "DATO_NO_EN_ARCHIVO",
                        "dueno": "usuario",
                        "se_cierra_con": f"valor de {nombre} en cada ejecución",
                    },
                }
            )
    return variables


def contexto_del_encabezado(plan_ops, hechos: list[Fact], lineas: list[str]) -> dict:
    """Joblet de contexto: sentencias de entorno del encabezado y variables declarables.

    El encabezado es lo que está antes de la primera región. Si el programa no tiene regiones
    repetidas no hay encabezado que separar y el joblet no se genera.
    """
    inicios = marcador_de_regiones(lineas)
    if not inicios:
        return {}
    fin = inicios[0]
    hechos_encabezado = [h for h in hechos if h.linea_inicio < fin]
    variables = _variables_de_contexto(hechos_encabezado, lineas[: fin - 1])
    rutas = _valores(hechos_encabezado, "ruta_literal")
    pendientes = [v["pendiente"] for v in variables if v["valor"] is None]
    if rutas:
        pendientes.append(
            {
                "motivo": "DATO_NO_EN_ARCHIVO",
                "dueno": "usuario",
                "se_cierra_con": "confirmar el papel de cada ruta (insumo o resultado)",
                "nota": f"{len(rutas)} rutas literales; el archivo no distingue su papel",
            }
        )
    return {
        "id": "jl_contexto",
        "operadores": len(operadores_de_contexto(plan_ops, lineas, fin)),
        "variables": variables,
        "pendientes": pendientes,
    }


def diseno_del_job(
    plan_ops, hechos: list[Fact], lineas: list[str], declaracion: Declaracion | None = None
) -> dict:
    """Job padre de diseño: una llamada por grupo, el joblet de contexto y el resto del encabezado.

    Es el equivalente en Talend del bucle `%DO ... %TO` sobre una lista (`%SCAN`), aplicado a
    copias agrupadas de forma determinista, más el joblet que carga el contexto del Job.
    """
    inicios, grupos, por_region = _reparto(plan_ops, hechos, lineas, declaracion)
    joblets = _joblets_de(grupos, por_region, _datasets_por_region(hechos, inicios))
    contexto = contexto_del_encabezado(plan_ops, hechos, lineas)
    en_grupo = {r for g in grupos for r in g}
    encabezado = _componentes(por_region.get(-1, []))
    sueltas = [
        op for r in sorted(por_region) if r >= 0 and r not in en_grupo for op in por_region[r]
    ]
    llamadas = [
        {"joblet": j["id"], "iteraciones": j["miembros"], "contextos": len(j["contextos"])}
        for j in joblets
    ]
    todas = _firmas(encabezado + sueltas)
    for grupo in grupos:
        for s in _firmas(op for r in grupo for op in por_region.get(r, [])):
            if s not in todas:
                todas.append(s)
    nodos = len(llamadas) + (1 if contexto else 0) + len(encabezado) + len(_componentes(sueltas))
    agrupacion = (
        {"modo": "declarada", "productos": list(declaracion.productos)}
        if declaracion
        else {"modo": "similitud", "umbral": UMBRAL_DE_AGRUPACION}
    )
    return {
        "agrupacion": agrupacion,
        "job_padre": {
            "llamadas": llamadas,
            "joblet_de_contexto": contexto["id"] if contexto else None,
            "componentes_del_encabezado": len(encabezado),
            "componentes_sueltos": len(_componentes(sueltas)),
            "nodos": nodos,
        },
        "joblets": [{k: v for k, v in j.items() if k != "contextos"} for j in joblets],
        "contextos": {j["id"]: j["contextos"] for j in joblets},
        "contexto": contexto,
        "regiones": len(inicios),
        "firmas_de_componente": len(todas),
    }
