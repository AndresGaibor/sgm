"""SQL de base (dialecto Hive, equivalente a Impala) desde el árbol de un PROC SQL.

Lo usan las pasadas 4 y 5 cuando una consulta queda en la base de datos. Las partes se toman del
SAS ya normalizado, y `sqlglot` las reescribe en el dialecto de destino (Impala no tiene dialecto
propio en `sqlglot`; `hive` es el más cercano). Si el resultado no se puede escribir, `render`
lanza `ValueError` y el llamador se queda en flujo.
"""

from __future__ import annotations

import re

import sqlglot
from sqlglot import exp

from sgm.frontend.sql_normalize import NormalizedSql
from sgm.ir.sql_tree import (
    SelectSpec,
    Source,
    SqlTree,
    SqlUnsafeIdentifier,
    validate_portable_identifiers,
)

_JOIN = {"inner": "INNER JOIN", "left": "LEFT JOIN", "right": "RIGHT JOIN", "full": "FULL JOIN"}
_PORTABLE_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z", re.ASCII)


def _name(source: Source, normalized: NormalizedSql) -> str:
    name = normalized.restore(source.name)
    return f"{name} {source.alias}" if source.alias else name


def _select(spec: SelectSpec, normalized: NormalizedSql) -> str:
    items = ", ".join(
        "*" if it.star else (f"{it.expression} AS {it.alias}" if it.alias else it.expression)
        for it in spec.items
    )
    parts = [f"SELECT {'DISTINCT ' if spec.distinct else ''}{items or '*'}"]
    if spec.base is not None:
        parts.append(f"FROM {_name(spec.base, normalized)}")
    for join in spec.joins:
        if join.kind == "cross":
            parts.append(f"CROSS JOIN {_name(join.source, normalized)}")
            continue
        clause = f"{_JOIN[join.kind]} {_name(join.source, normalized)}"
        parts.append(f"{clause} ON {join.on}" if join.on else clause)
    if spec.where:
        parts.append(f"WHERE {spec.where}")
    if spec.group_by:
        parts.append(f"GROUP BY {', '.join(spec.group_by)}")
    if spec.having:
        parts.append(f"HAVING {spec.having}")
    if spec.order_by:
        order = [f"{expr} DESC" if desc else expr for expr, desc in spec.order_by]
        parts.append(f"ORDER BY {', '.join(order)}")
    return " ".join(parts)


def render(tree: SqlTree, normalized: NormalizedSql, dialect: str = "hive") -> str:
    """SQL completo de la consulta (CREATE TABLE ... AS si hay destino) en el dialecto indicado.

    Lanza `ValueError` si el resultado no se puede escribir: por ejemplo, con una macro variable en
    un nombre (`&tabla`), que solo se resuelve al ejecutar.
    """
    validate_portable_identifiers(tree)
    joiner = " UNION ALL " if tree.union_all else " UNION "
    body = joiner.join(_select(spec, normalized) for spec in tree.selects)
    if tree.target:
        body = f"CREATE TABLE {normalized.restore(tree.target)} AS {body}"
    if "&" in body:
        raise ValueError("macro variable en la consulta: no se escribe SQL de base fijo")
    _validar_sql_emitido(body)
    try:
        return sqlglot.transpile(body, write=dialect)[0]
    except sqlglot.errors.SqlglotError as error:
        raise ValueError(str(error)) from error


def _validar_sql_emitido(sql: str) -> None:
    """Reparsea el texto actual para detectar mutaciones e inyección en el árbol público."""
    try:
        sentencias = sqlglot.parse(sql)
    except sqlglot.errors.SqlglotError as error:
        raise ValueError("SQL generado no supera la validación de salida") from error
    if len(sentencias) != 1 or sentencias[0] is None:
        raise ValueError("SQL generado no supera la validación de salida")
    sentencia = sentencias[0]
    if isinstance(sentencia, exp.Create):
        consulta = sentencia.expression
        valida = (
            sentencia.args.get("kind") == "TABLE"
            and isinstance(consulta, (exp.Select, exp.Union))
        )
    else:
        valida = isinstance(sentencia, (exp.Select, exp.Union))
    if not valida:
        raise ValueError("SQL generado no supera la validación de salida")
    for identifier in sentencia.find_all(exp.Identifier):
        if not _PORTABLE_IDENTIFIER.fullmatch(identifier.name):
            raise SqlUnsafeIdentifier("identificador SQL no representable para Talend")
