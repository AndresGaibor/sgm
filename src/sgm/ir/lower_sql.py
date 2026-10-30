"""Sentencias de PROC SQL a operadores: pass-through a base de datos, EXECUTE y SQL sobre WORK."""

from __future__ import annotations

import re

from sgm.frontend.sql import SqlStatement
from sgm.frontend.steps import ProcSql
from sgm.ir.builder import Builder, qualify
from sgm.ir.models import Evidence

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
        b.op("read", params, ev, placement=f"db:{st.engine}")
    elif kind == "execute":
        created = _CREATE_TARGET.match(st.inner_sql or "")
        params = {"sql": st.inner_sql, "engine": st.engine}
        if created:
            params["outputs"] = [_base_name(st.engine or "", created.group(1))]
        b.op("exec_sql", params, ev, placement=f"db:{st.engine}")
    elif kind == "create_table":
        b.op(
            "exec_sql",
            {
                "sql": st.text,
                "inputs": [qualify(s) for s in st.sources],
                "outputs": [qualify(st.target or "")],
            },
            ev,
            status="parcial",
            notes=[
                "SQL sobre datasets de WORK: se traduce en las pasadas de fusión SQL o de flujo"
            ],
        )
    elif kind in ("select", "insert", "delete", "drop_table", "create_like"):
        params = {"sql": st.text, "inputs": [qualify(s) for s in st.sources]}
        if st.target:
            params["outputs"] = [qualify(st.target)]
        b.op(
            "exec_sql",
            params,
            ev,
            status="parcial",
            notes=[f"sentencia {kind} de PROC SQL sobre WORK: pendiente de traducción"],
        )
    elif kind in ("connect", "disconnect"):
        b.op(
            "unsupported",
            {"statement": kind, "engine": st.engine, "reason": "CONEXION_SQL"},
            ev,
            status="hueco",
            notes=["conexión a motor: lo resuelve la pasada de particiones y de plomería"],
        )
    else:
        b.op(
            "unsupported",
            {"statement": st.text, "reason": "PROC_NO_SOPORTADO"},
            ev,
            status="hueco",
            notes=[f"sentencia SQL no reconocida: {st.text[:60]}"],
        )
