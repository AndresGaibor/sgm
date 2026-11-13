"""Combina dependencias de una rebanada y valores que demuestran sus filtros."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from sgm.compile import compile_file, project_base
from sgm.frontend.datastep import DataStep
from sgm.frontend.lexer import split_statements
from sgm.frontend.program import analyze_program
from sgm.frontend.steps import parse_steps
from sgm.frontend.steps_tipos import Proc, ProcSql
from sgm.migrar.esquemas_programa import tablas_base_del_programa
from sgm.proceso.columnas_fuente import columnas_usadas, datasets_importados
from tools.datos_sinteticos.filtros_sql import (
    _alias_tablas,
    columnas_en_filtros,
    ocultar_cadenas,
    sentencias_sql,
    tablas_sql,
    valores_exigidos,
)


@dataclass(frozen=True)
class Requisitos:
    """Datos que la rebanada lee, produce o exige explícitamente."""

    tablas_locales: dict[str, list[str]] = field(default_factory=dict)
    tablas_base: dict[str, list[str]] = field(default_factory=dict)
    tablas_work_externas: dict[str, list[str]] = field(default_factory=dict)
    archivos: list[str] = field(default_factory=list)
    exigidos: dict[str, dict[str, list[str]]] = field(default_factory=dict)
    dinamicos: list[str] = field(default_factory=list)


def _unir_columnas(*grupos: list[str]) -> list[str]:
    salida: list[str] = []
    vistas: set[str] = set()
    for grupo in grupos:
        for nombre in grupo:
            clave = nombre.casefold()
            if clave not in vistas:
                vistas.add(clave)
                salida.append(nombre)
    return salida


def _tablas_locales_configuradas() -> set[str]:
    ruta = Path.cwd() / "env" / "tablas_locales.json"
    if not ruta.is_file():
        return set()
    configuracion = json.loads(ruta.read_text(encoding="utf-8"))
    if not isinstance(configuracion, dict):
        raise ValueError("env/tablas_locales.json debe ser un objeto")
    return {
        str(nombre).lower()
        for nombre in configuracion
        if not str(nombre).startswith("_")
    }


def _columnas_select_sencillas(texto: str, tabla: str) -> list[str]:
    """Recoge proyecciones simples cuando la consulta tiene una sola tabla."""
    resultado: list[str] = []
    for sentencia in sentencias_sql(texto):
        aliases = _alias_tablas(sentencia)
        if tabla not in set(aliases.values()) or len(set(aliases.values())) != 1:
            continue
        limpio = ocultar_cadenas(sentencia)
        select = re.search(r"\bSELECT\b(.*?)\bFROM\b", limpio, re.IGNORECASE | re.DOTALL)
        if select is None:
            continue
        inicio, fin = select.span(1)
        for expresion in sentencia[inicio:fin].split(","):
            expresion = re.sub(r"(?i)\s+AS\s+[A-Za-z_]\w*\s*$", "", expresion).strip()
            columna = re.fullmatch(
                r"(?:(?:[A-Za-z_]\w*)\s*\.\s*)?([A-Za-z_]\w*)", expresion
            )
            if columna:
                resultado.append(columna.group(1))
                continue
            funcion = re.fullmatch(
                r"[A-Za-z_]\w*\(\s*(?:(?:[A-Za-z_]\w*)\s*\.\s*)?"
                r"([A-Za-z_]\w*)\s*\)",
                expresion,
            )
            if funcion:
                resultado.append(funcion.group(1))
    return resultado


def _nombre_tabla(nombre: object) -> str:
    tabla = str(nombre or "").strip().casefold()
    return tabla if not tabla or "." in tabla else f"work.{tabla}"


def _leer_y_producir(paso: object) -> tuple[list[str], list[str]]:
    """Obtiene entradas y salidas de los pasos que el frontend sí clasificó."""
    if isinstance(paso, DataStep):
        entradas = [
            fuente["name"]
            for sentencia in paso.statements
            if sentencia.kind in {"set", "merge", "update"}
            for fuente in sentencia.fields.get("sources", [])
            if fuente.get("name")
        ]
        return entradas, list(paso.outputs)
    if isinstance(paso, ProcSql):
        return [], []
    if isinstance(paso, Proc):
        opciones = paso.options
        entradas = [] if paso.name.lower() == "import" else [
            opciones[nombre]
            for nombre in ("data", "base")
            if opciones.get(nombre)
        ]
        salidas = [opciones["out"]] if opciones.get("out") else []
        if paso.name.lower() == "append" and opciones.get("base"):
            salidas.append(opciones["base"])
        if paso.name.lower() == "sort" and not opciones.get("out") and opciones.get("data"):
            salidas.append(opciones["data"])
        return entradas, salidas
    return [], []


def _lecturas_work_antes_de_producir(pasos: list[object]) -> set[str]:
    """Conserva una entrada WORK leída antes de que la rebanada la cree."""
    producidas: set[str] = set()
    externas: set[str] = set()
    for paso in pasos:
        if isinstance(paso, ProcSql):
            eventos = [
                (list(sentencia.sources), [sentencia.target] if sentencia.target else [])
                for sentencia in paso.statements
            ]
        else:
            eventos = [_leer_y_producir(paso)]
        for entradas, salidas in eventos:
            for entrada in entradas:
                nombre = _nombre_tabla(entrada)
                if nombre.startswith("work.") and nombre not in producidas:
                    externas.add(nombre)
            producidas.update(
                nombre
                for salida in salidas
                if (nombre := _nombre_tabla(salida)).startswith("work.")
            )
    return externas


def requisitos_de_rebanada(texto: str, nombre: str = "rebanada") -> Requisitos:
    """Combina fuentes K-2, columnas de filtros, WORK externas y rutas de importación."""
    fuentes = tablas_base_del_programa(texto, nombre, atribuir_copias=True)
    exigidos, dinamicos = valores_exigidos(texto)
    columnas_filtro = columnas_en_filtros(texto)
    locales_configuradas = _tablas_locales_configuradas()
    pasos, _ = parse_steps(split_statements(texto))
    archivo = f"{nombre}.sas"
    plan = compile_file(analyze_program({archivo: texto}), archivo, project_base()).plan
    producidas: set[str] = set()
    lecturas_plan: set[str] = set()
    for op in plan.graph.operators():
        if op.kind == "write" and op.params.get("dataset"):
            producidas.add(_nombre_tabla(op.params["dataset"]))
        elif op.kind in {"read", "read_file"}:
            producidas.update(
                _nombre_tabla(salida) for salida in op.params.get("outputs") or []
            )
        if op.kind == "read" and op.params.get("dataset"):
            lecturas_plan.add(_nombre_tabla(op.params["dataset"]))

    tablas = {_nombre_tabla(tabla) for tabla in fuentes}
    tablas.update(tablas_sql(texto))
    tablas.update(tabla for tabla in exigidos)
    tablas.update(columnas_filtro)
    tablas.update(lecturas_plan)
    columnas_por_tabla = {
        _nombre_tabla(tabla): list(columnas) for tabla, columnas in fuentes.items()
    }
    for tabla, columnas in exigidos.items():
        columnas_por_tabla[tabla] = _unir_columnas(
            columnas_por_tabla.get(tabla, []), list(columnas)
        )
    for tabla, columnas in columnas_filtro.items():
        columnas_por_tabla[tabla] = _unir_columnas(
            columnas_por_tabla.get(tabla, []), columnas
        )
    for tabla in tablas:
        columnas_por_tabla[tabla] = _unir_columnas(
            columnas_por_tabla.get(tabla, []), _columnas_select_sencillas(texto, tabla)
        )

    locales: dict[str, list[str]] = {}
    base: dict[str, list[str]] = {}
    trabajo: dict[str, list[str]] = {}
    for tabla in tablas:
        columnas = columnas_por_tabla.get(tabla, [])
        if tabla in locales_configuradas:
            locales[tabla] = columnas
        elif tabla.startswith("work."):
            continue
        else:
            base[tabla] = columnas

    entradas_work = _lecturas_work_antes_de_producir(pasos)
    for tabla in lecturas_plan | entradas_work:
        if not tabla.startswith("work."):
            continue
        if tabla in entradas_work or tabla not in producidas:
            trabajo[tabla] = _unir_columnas(
                trabajo.get(tabla, []),
                columnas_usadas(texto, tabla.removeprefix("work.")),
                columnas_por_tabla.get(tabla, []),
            )

    for tabla in tablas:
        if tabla.startswith("work.") and tabla in trabajo:
            trabajo[tabla] = _unir_columnas(trabajo[tabla], columnas_por_tabla.get(tabla, []))

    archivos = [imp.ruta for imp in datasets_importados(texto)]
    return Requisitos(locales, base, trabajo, archivos, exigidos, dinamicos)
