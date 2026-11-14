"""Lectura controlada de archivos delimitados para el esperado del anillo B."""

from __future__ import annotations

import csv
import re
from typing import TYPE_CHECKING

from sgm.ir.models import Plan
from sgm.migrar.ficha import leer_ficha
from tools.datos_sinteticos.ficha import validar_ficha

if TYPE_CHECKING:
    from .caso import Caso

_IDENTIFICADOR = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")


def _tabla(nombre: object) -> str:
    return str(nombre or "").strip().casefold().split(".")[-1]


def _relevantes(plan: Plan, salidas: tuple[str, ...]) -> set[str]:
    """Recorre hacia atrás desde salidas declaradas para excluir imports sin uso."""
    esperadas = {_tabla(nombre) for nombre in salidas}
    objetivos = set()
    for operator in plan.graph.operators():
        params = operator.params
        producidas = list(params.get("outputs") or [])
        if operator.kind == "write":
            producidas.append(params.get("dataset", ""))
        consumidas = params.get("inputs") or [] if operator.kind == "write_file" else []
        if any(_tabla(nombre) in esperadas for nombre in [*producidas, *consumidas]):
            objetivos.add(operator.id)

    relevantes = set()
    pendientes = list(objetivos)
    while pendientes:
        actual = pendientes.pop()
        if actual in relevantes:
            continue
        relevantes.add(actual)
        pendientes.extend(plan.graph.predecessors(actual))
    return relevantes


def _nombre_fuente(datafile: object) -> str:
    """Extrae un nombre simple; nunca usa la ruta SAS para leer fuera del caso."""
    literal = str(datafile or "").strip()
    if len(literal) >= 2 and literal[0] == literal[-1] and literal[0] in "'\"":
        literal = literal[1:-1]
    partes = re.split(r"[\\/]", literal)
    if ".." in partes or not partes or not partes[-1]:
        raise ValueError("DATAFILE no identifica un archivo local del caso")
    nombre = partes[-1]
    if not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.-]*\.[A-Za-z0-9]{1,10}", nombre):
        raise ValueError("DATAFILE tiene un nombre de archivo no permitido")
    return nombre


def _leer_dlm(
    operator: object, caso: Caso
) -> tuple[str, list[str], list[dict[str, str]]]:
    params = operator.params
    separator = params.get("delimiter")
    if not isinstance(separator, str) or len(separator) != 1 or separator in '\r\n"':
        raise ValueError("PROC IMPORT DBMS=DLM requiere DELIMITER explícito de un carácter")
    has_header = params.get("getnames")
    if not isinstance(has_header, bool):
        raise ValueError("PROC IMPORT DBMS=DLM no tiene GETNAMES resuelto")
    name = _nombre_fuente(params.get("datafile"))
    case_root = caso.directorio.resolve()
    root = caso.entradas.resolve()
    if root == case_root or not root.is_relative_to(case_root):
        raise ValueError("raíz de entradas fuera de la carpeta del caso")
    path = (root / name).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError(f"no existe el archivo DATAFILE del caso: {name}")
    ficha_path = path.with_suffix(".ficha.yaml").resolve()
    if not ficha_path.is_relative_to(root):
        raise ValueError(f"la ficha del archivo sale de entradas/: {name}")
    if not ficha_path.is_file():
        raise ValueError(f"falta la ficha de procedencia del archivo: {name}")
    ficha = leer_ficha(ficha_path)
    errores = validar_ficha(ficha, path)
    if errores:
        raise ValueError(f"{name}: ficha inválida: {'; '.join(errores)}")
    if ficha.tabla != f"archivo:{name}" or ficha.cabecera is not has_header:
        raise ValueError(f"{name}: la ficha no coincide con GETNAMES del programa")
    if ficha.delimitador != separator:
        raise ValueError(f"{name}: la ficha no coincide con DELIMITER del programa")

    try:
        with path.open(encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.reader(stream, delimiter=separator, strict=True))
    except (OSError, UnicodeError, csv.Error) as error:
        raise ValueError(f"{name}: archivo delimitado inválido") from error
    if not rows:
        raise ValueError(f"{name}: archivo sin filas; no se puede demostrar el esquema")
    if has_header:
        columns, values = rows[0], rows[1:]
        if any(not _IDENTIFICADOR.fullmatch(column) for column in columns):
            raise ValueError(f"{name}: GETNAMES requiere nombres de columna simples en este anillo")
    else:
        columns, values = [f"VAR{index}" for index in range(1, len(rows[0]) + 1)], rows
    if not columns or any(len(row) != len(columns) for row in values):
        raise ValueError(f"{name}: cantidad de campos inconsistente")
    if list(ficha.columnas) != columns:
        raise ValueError(f"{name}: las columnas no coinciden con la ficha")
    return (
        _tabla((params.get("outputs") or [""])[0]),
        columns,
        [dict(zip(columns, row, strict=True)) for row in values],
    )


def entradas_de_archivos(
    plan: Plan, caso: Caso, salidas: tuple[str, ...] | list[str] | None = None
) -> tuple[dict[str, list[dict[str, str]]], dict[str, list[str]]]:
    """Carga únicamente imports necesarios para las salidas y soportados por este anillo."""
    relevantes = _relevantes(plan, caso.salidas if salidas is None else tuple(salidas))
    entradas = {}
    columnas = {}
    for operator in plan.graph.operators():
        if operator.kind != "read_file" or operator.id not in relevantes:
            continue
        dbms = str(operator.params.get("dbms") or "").casefold()
        if dbms != "dlm":
            raise ValueError(
                f"{_tabla((operator.params.get('outputs') or [''])[0])}: "
                f"DBMS={dbms or '(sin DBMS)'} no está soportado en el esperado del anillo B"
            )
        name, names, rows = _leer_dlm(operator, caso)
        if name in entradas:
            raise ValueError(f"{name}: más de un PROC IMPORT produce la misma tabla")
        entradas[name] = rows
        columnas[name] = names
    return entradas, columnas
