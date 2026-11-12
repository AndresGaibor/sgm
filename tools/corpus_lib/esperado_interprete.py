"""Esperados reproducibles del anillo B; no equivalen a una ejecución SAS real."""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

from sgm.compile import compile_file, project_base
from sgm.frontend.lexer import split_statements
from sgm.frontend.program import analyze_program
from sgm.ir.models import Plan
from sgm.migrar.interprete import ejecutar_plan

from .csv_tabla import Tabla, escribir_csv, leer_entradas

if TYPE_CHECKING:
    from .caso import Caso


def _overrides(text: str, values: dict[str, int]) -> str:
    """Cambia solo el literal de declaraciones numéricas completas de una línea."""
    for name, value in values.items():
        if not re.fullmatch(r"[A-Za-z_]\w*", name) or type(value) is not int:
            raise ValueError(f"override inválido para {name!r}: se requiere nombre y entero")
        pattern = re.compile(
            rf"(?im)^([ \t]*%let[ \t]+{re.escape(name)}[ \t]*=[ \t]*)"
            r"([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)"
            r"([ \t]*;[ \t]*)(?=\r?$)"
        )
        declaration = re.compile(rf"(?i)%let\s+{re.escape(name)}\s*=")
        lines = {stmt.line for stmt in split_statements(text) if declaration.match(stmt.text)}
        matches = [
            match for match in pattern.finditer(text)
            if text.count("\n", 0, match.start()) + 1 in lines
        ]
        if not matches:
            raise ValueError(
                f"{name}: falta una declaración numérica de línea '%let {name} = número;'"
            )
        for match in reversed(matches):
            text = text[:match.start(2)] + str(value) + text[match.end(2):]
    return text


def _table_name(name: object) -> str:
    return str(name).lower().split(".")[-1]


def _empty_columns(plan: Plan, name: str) -> list[str]:
    """Consulta la última versión escrita; nunca hereda el esquema de una versión anterior."""
    writers = []
    for index, operator in enumerate(plan.graph.operators()):
        if operator.kind != "write":
            continue
        base, _, version = _table_name(operator.params.get("dataset", "")).partition("@v")
        if base == name:
            writers.append((int(version or "1"), index, operator))
    if writers:
        latest = max(writers, key=lambda item: item[:2])[2]
        if latest.schema:
            return [column.name for column in latest.schema]
        raise ValueError(f"{name}: salida vacía sin cabecera demostrada en el plan")
    for operator in reversed(plan.graph.operators()):
        names = operator.params.get("outputs") or []
        if any(_table_name(output) == name for output in names):
            if operator.schema:
                return [column.name for column in operator.schema]
            break
    raise ValueError(f"{name}: salida vacía sin cabecera demostrada en el plan")


def calcular(caso: Caso, repeticiones: dict[str, int] | None = None) -> dict[str, Tabla]:
    """Analiza, compila y ejecuta sin escribir; devuelve las salidas en su orden declarado."""
    text = _overrides(caso.programa.read_text(encoding="utf-8"), repeticiones or {})
    program = caso.programa.name
    plan = compile_file(analyze_program({program: text}), program, project_base()).plan
    inputs = {
        name: [dict(zip(table.columnas, row, strict=True)) for row in table.filas]
        for name, table in leer_entradas(caso.entradas).items()
    }
    outputs = ejecutar_plan(plan, inputs)
    tables = {}
    for name in caso.salidas:
        key = _table_name(name)
        if key not in outputs:
            raise ValueError(f"{name}: la salida declarada no fue producida por el intérprete")
        rows = outputs[key]
        columns = list(rows[0]) if rows else _empty_columns(plan, key)
        if any(set(row) != set(columns) for row in rows):
            raise ValueError(f"{name}: las filas no tienen una cabecera uniforme")
        tables[name] = Tabla(columns, [tuple(row[column] for column in columns) for row in rows])
    return tables


def escribir(caso: Caso, tablas: dict[str, Tabla]) -> list[Path]:
    """Valida todas las salidas y sus rutas antes de escribir CSV dentro del caso."""
    try:
        root, expected = caso.directorio.resolve(), caso.esperado.resolve()
        if expected == root or not expected.is_relative_to(root):
            raise ValueError(f"ruta de esperado fuera de la carpeta del caso: {caso.esperado}")
        paths = []
        for name in tablas:
            if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z_]\w*", name):
                raise ValueError(f"nombre de salida inválido: {name!r}")
            if name not in caso.salidas:
                raise ValueError(f"salida no declarada en el caso: {name}")
            path = caso.esperado / f"{name}.csv"
            if not path.resolve().is_relative_to(expected):
                raise ValueError(f"ruta de salida fuera de esperado: {path}")
            paths.append(path)
    except (OSError, RuntimeError) as error:
        raise ValueError(f"ruta de salida no verificable: {error}") from None
    for path, table in zip(paths, tablas.values(), strict=True):
        escribir_csv(path, table)
    return paths
