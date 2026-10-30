"""Sentencias de PROC SQL a operadores: pass-through a base de datos, EXECUTE y SQL sobre WORK."""

from __future__ import annotations

import re

from sgm.frontend.sql import SqlStatement, parse_sql_statement
from sgm.frontend.sql_normalize import normalize
from sgm.frontend.steps import ProcSql
from sgm.ir.builder import Builder
from sgm.ir.lower_sql_flow import lower_query
from sgm.ir.models import Evidence
from sgm.ir.sql_tree import SqlNotSelect, SqlParseError, build

_CREATE_TARGET = re.compile(r"(?is)^create\s+table\s+([\w.&]+)")


def _base_name(engine: str, table: str) -> str:
    return f"{engine.upper()}.{table.lower()}"


def lower_proc_sql(step: ProcSql, ev: Evidence, b: Builder) -> None:
    for st in step.statements:
        _lower_statement(st, ev, b)


def _lower_statement(st: SqlStatement, ev: Evidence, b: Builder) -> None:
    kind = st.kind
    if kind == "select_passthrough":
        params = {"sql": st.inner_sql, "engine": st.engine}
        if st.target:
            params["outputs"] = [_base_name(st.engine or "", st.target)]
        b.op("read", params, ev, placement=f"db:{(st.engine or '').lower()}")
    elif kind == "execute":
        created = _CREATE_TARGET.match(st.inner_sql or "")
        inner = parse_sql_statement(st.inner_sql or "", ev.line_start)
        params = {
            "sql": st.inner_sql,
            "engine": st.engine,
            "inputs": [_base_name(st.engine or "", s) for s in inner.sources],
        }
        if created:
            params["outputs"] = [_base_name(st.engine or "", created.group(1))]
        b.op("exec_sql", params, ev, placement=f"db:{(st.engine or '').lower()}")
    elif kind in ("create_table", "select"):
        _lower_query(st, ev, b)
    elif kind in ("insert", "delete", "drop_table", "create_like"):
        b.op(
            "unsupported",
            {"statement": st.text, "reason": "SQL_NO_SOPORTADO", "sql": st.text},
            ev,
            status="hueco",
            notes=[f"sentencia {kind} de PROC SQL: no es una consulta, no se traduce"],
        )
    elif kind in ("connect", "disconnect"):
        b.op(
            "unsupported",
            {"statement": kind, "engine": st.engine, "reason": "CONEXION_SQL"},
            ev,
            status="hueco",
            notes=["conexión a motor: lo resuelve la pasada de particiones y de plomería"],
        )
    elif st.text.lstrip().startswith("%"):  # llamada de macro dentro de PROC SQL, no un PROC
        b.op(
            "unsupported",
            {"statement": st.text, "reason": "MACRO_NO_EXPANDIDA"},
            ev,
            status="hueco",
            notes=[f"llamada de macro dentro de PROC SQL: {st.text[:60]}"],
        )
    else:
        b.op(
            "unsupported",
            {"statement": st.text, "reason": "PROC_NO_SOPORTADO"},
            ev,
            status="hueco",
            notes=[f"sentencia SQL no reconocida: {st.text[:60]}"],
        )


def _lower_query(st: SqlStatement, ev: Evidence, b: Builder) -> None:
    """Consulta de PROC SQL sobre flujo. Un texto que `sqlglot` no lee es PARSE_ERROR."""
    normalized = normalize(st.text)
    try:
        tree = build(normalized.text)
    except SqlParseError as error:
        b.op(
            "unsupported",
            {"statement": st.text, "reason": "PARSE_ERROR", "sql": st.text},
            ev,
            status="hueco",
            notes=[f"PROC SQL que no se puede analizar: {str(error)[:80]}"],
        )
        return
    except SqlNotSelect as error:
        b.op(
            "unsupported",
            {"statement": st.text, "reason": "SENTENCIA_NO_SOPORTADA", "sql": st.text},
            ev,
            status="hueco",
            notes=[f"consulta fuera de SELECT: {error}"],
        )
        return
    lower_query(tree, normalized, ev, b)
