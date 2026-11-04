"""Sentencias de PROC SQL. El SQL dentro de un pass-through se guarda intacto como texto.

Reconoce `create table ... as select`, `select`, `insert`, `delete`, `drop`, `connect to <motor>`,
`select ... from connection to <motor> (...)`, `execute (...) by <motor>` y `disconnect from <motor>`.
Lo que no reconoce queda como `other` con su texto, sin lanzar excepciones.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from sgm.frontend.sql_fuentes import extract_sources

_CREATE = re.compile(r"(?is)^create\s+table\s+([\w.&]+)\s+as\s+(.+)$")
_CREATE_LIKE = re.compile(r"(?is)^create\s+table\s+([\w.&]+)\s+like\s+")
_INSERT = re.compile(r"(?is)^insert\s+into\s+([\w.&]+)")
_DELETE = re.compile(r"(?is)^delete\s+from\s+([\w.&]+)")
_DROP = re.compile(r"(?is)^drop\s+table\s+([\w.&]+)")
_CONNECT = re.compile(r"(?is)^connect\s+to\s+(\w+)")
_DISCONNECT = re.compile(r"(?is)^disconnect\s+from\s+(\w+)")
_PASSTHROUGH = re.compile(r"(?is)\bfrom\s+connection\s+to\s+(\w+)\s*\((.*)\)\s*$")
_EXECUTE = re.compile(r"(?is)^execute\s*\((.*)\)\s*by\s+(\w+)\s*$")
_EXECUTE_BY = re.compile(r"(?is)^execute\s+by\s+(\w+)\s*\((.*)\)\s*$")


@dataclass(frozen=True)
class SqlStatement:
    kind: str  # create_table, create_like, select, select_passthrough, insert, delete, drop_table,
    #            connect, disconnect, execute, other
    text: str
    line: int
    target: str | None = None  # tabla que se crea, inserta, borra o elimina
    engine: str | None = None  # motor de un pass-through, conexión o ejecución
    sources: tuple[str, ...] = ()  # tablas que lee la sentencia (FROM y JOIN; en un pass-through, las del motor)
    inner_sql: str | None = None  # SQL del pass-through o de execute, intacto
    fields: dict[str, str] = field(default_factory=dict)


def parse_sql_statement(text: str, line: int) -> SqlStatement:
    """Clasifica una sentencia de PROC SQL (sin el `;` final)."""
    body = text.strip()
    if m := _EXECUTE.match(body):
        return SqlStatement("execute", body, line, engine=m.group(2), inner_sql=m.group(1).strip())
    if m := _EXECUTE_BY.match(body):
        return SqlStatement("execute", body, line, engine=m.group(1), inner_sql=m.group(2).strip())
    if m := _CREATE.match(body):
        target, query = m.group(1), m.group(2)
        if pt := _PASSTHROUGH.search(query):
            return SqlStatement(
                "select_passthrough",
                body,
                line,
                target=target,
                engine=pt.group(1),
                inner_sql=pt.group(2).strip(),
                sources=extract_sources(pt.group(2)),
                fields={"query": query},
            )
        return SqlStatement(
            "create_table", body, line, target=target, sources=extract_sources(query)
        )
    if _CREATE_LIKE.match(body):
        return SqlStatement("create_like", body, line, target=_CREATE_LIKE.match(body).group(1))
    if body.lower().startswith("select") or body.lower().startswith("("):
        if pt := _PASSTHROUGH.search(body):
            return SqlStatement(
                "select_passthrough",
                body,
                line,
                engine=pt.group(1),
                sources=extract_sources(pt.group(2)),
                inner_sql=pt.group(2).strip(),
            )
        return SqlStatement("select", body, line, sources=extract_sources(body))
    if m := _INSERT.match(body):
        return SqlStatement("insert", body, line, target=m.group(1), sources=extract_sources(body))
    if m := _DELETE.match(body):
        return SqlStatement("delete", body, line, target=m.group(1))
    if m := _DROP.match(body):
        return SqlStatement("drop_table", body, line, target=m.group(1))
    if m := _CONNECT.match(body):
        return SqlStatement("connect", body, line, engine=m.group(1))
    if m := _DISCONNECT.match(body):
        return SqlStatement("disconnect", body, line, engine=m.group(1))
    return SqlStatement("other", body, line)
