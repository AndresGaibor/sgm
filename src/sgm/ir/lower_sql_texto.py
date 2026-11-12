"""Texto de las consultas SQL: macros, alias, columnas y nombres de salida.

Extraído de `lower_sql_flow.py` (B-6) sin cambio de comportamiento.
"""

from __future__ import annotations

import re

from sgm.frontend.sql_normalize import NormalizedSql
from sgm.ir.sql_tree import SelectSpec

_AGGREGATE = re.compile(r"(?i)\b(sum|count|avg|mean|min|max|std|stddev|n|nmiss|range|median)\s*\(")


_DOTTED = re.compile(r"\b([A-Za-z_]\w*)\.([A-Za-z_]\w*)")


_SIMPLE_COLUMN = re.compile(r"(?i)^(?:[a-z_]\w*\.)*([a-z_]\w*)$")


_NOT_NULL = re.compile(r"(?i)\bNOT\s+([\w.]+)\s+IS\s+NULL\b")


_IS_NOT_NULL = re.compile(r"(?i)\b([\w.]+)\s+IS\s+NOT\s+NULL\b")


_IS_NULL = re.compile(r"(?i)\b([\w.]+)\s+IS\s+NULL\b")


def _restore(text: str, normalized: NormalizedSql) -> str:
    """Devuelve las macro variables a su forma SAS (`mv_x` -> `&x`) en un texto."""
    for placeholder, original in normalized.macros.items():
        text = re.sub(rf"\b{re.escape(placeholder)}\b", original, text)
    return text


def _null_tests(text: str) -> str:
    """`x IS NULL` y `x IS NOT NULL` (como los escribe sqlglot) a `missing(x)`, la forma SAS."""
    text = _NOT_NULL.sub(lambda m: f"NOT missing({m.group(1)})", text)
    text = _IS_NOT_NULL.sub(lambda m: f"NOT missing({m.group(1)})", text)
    return _IS_NULL.sub(lambda m: f"missing({m.group(1)})", text)


def _column(text: str, aliases: set[str]) -> str:
    """Nombre de columna de una referencia (`a.k` -> `k`) si el prefijo es un alias de fuente."""
    return _null_tests(
        _DOTTED.sub(lambda m: m.group(2) if m.group(1).lower() in aliases else m.group(0), text)
    )


def _tablas(spec: SelectSpec) -> dict[str, str]:
    """Alias y nombre de tabla, en minúsculas, al nombre de tabla sin biblioteca (`work.x` -> `x`).

    El `tMap` no conoce los alias del SAS: sus llaves y sus expresiones llevan la tabla delante.
    """
    mapa: dict[str, str] = {}
    for source in [spec.base, *(join.source for join in spec.joins)]:
        if source is None:
            continue
        tabla = source.name.lower().split(".")[-1]
        mapa[source.alias.lower() if source.alias else tabla] = tabla
        mapa.setdefault(tabla, tabla)
    return mapa


def _calificar(text: str, tablas: dict[str, str]) -> str:
    """`v.monto` -> `ventas.monto` cuando `v` es un alias de la consulta."""

    def cambiar(m: re.Match) -> str:
        tabla = tablas.get(m.group(1).lower())
        return f"{tabla}.{m.group(2)}" if tabla else m.group(0)

    return _DOTTED.sub(cambiar, text)


def _target_name(expression: str) -> str:
    """Nombre de columna para una expresión sin alias: su texto, sin signos, en minúsculas."""
    name = re.sub(r"\W+", "_", expression).strip("_").lower()
    return name or "expr"


def _names(items) -> list[str]:
    """Nombres de salida de los elementos del SELECT (alias o columna); `*` no tiene nombre."""
    return [it.alias or it.column for it in items if not it.star and (it.alias or it.column)]


def _plain_items(spec: SelectSpec) -> list[str]:
    """Elementos del SELECT que no son agregados (ni `*`): columnas que quedarían sin agrupar."""
    return [
        it.alias or it.column or it.expression
        for it in spec.items
        if not it.star and not _AGGREGATE.search(it.expression)
    ]
