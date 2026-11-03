"""Pasos de un nodo: DATA step, PROC SQL, PROC genérico, macros, asignaciones y globales.

El lexer corta el texto en sentencias; aquí se agrupan en pasos. Un paso que no se puede leer se
devuelve como `Unparsed(text, reason)` y el análisis sigue con el resto. Nunca se lanza una excepción
por un paso.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace

from sgm.frontend.datastep import DataStep, classify_statement, parse_data_header
from sgm.frontend.lexer import MACRO_KEYWORDS, Stmt, split_statements
from sgm.frontend.splitter import Node
from sgm.frontend.sql import SqlStatement, parse_sql_statement
from sgm.frontend.steps_tipos import (  # noqa: F401  (reexport para los importadores)
    Global,
    Include,
    Let,
    Libname,
    MacroCall,
    MacroDef,
    Options,
    ParsedNode,
    Proc,
    ProcSql,
    Unparsed,
    XCommand,
)

_DATALINES_HEAD = ("datalines", "cards", "datalines4", "cards4")
_PROC_OPTION = re.compile(r"([A-Za-z_]\w*)\s*=\s*(\S+)")
_PROC_CLAUSES = ("by", "var", "class", "where", "id", "output", "tables", "model")


def _lower(stmt: Stmt) -> str:
    return stmt.text.strip().lower()


def _is_boundary(stmt: Stmt) -> bool:
    low = _lower(stmt)
    return low.startswith(("data ", "data;", "proc ", "%macro ", "%mend")) or low in (
        "data",
        "proc",
    )


def _parse_data(stmts: list[Stmt], i: int) -> tuple[object, int]:
    head = stmts[i]
    outputs = parse_data_header(head.text)
    j = i + 1
    body: list[object] = []
    last = head
    while j < len(stmts):
        s = stmts[j]
        if _lower(s) == "run" or _lower(s) == "run;":
            last = s
            j += 1
            break
        if _is_boundary(s):
            break
        last = s
        if _lower(s) in _DATALINES_HEAD:
            j += 1
            continue
        body.append(classify_statement(s.text, s.line, s.rows))
        j += 1
    if outputs is None:
        return Unparsed(head.text, "DATA sin salidas", head.line, last.end_line), j
    return DataStep(outputs, body, head.line, last.end_line, head.text), j


def _parse_proc(stmts: list[Stmt], i: int) -> tuple[object, int]:
    head = stmts[i]
    words = head.text.split()
    name = words[1].lower() if len(words) > 1 else ""
    if not name:
        return Unparsed(head.text, "PROC sin nombre", head.line, head.end_line), i + 1
    header_rest = head.text.split(None, 2)[2] if len(words) > 2 else ""
    options = {k.lower(): v for k, v in _PROC_OPTION.findall(header_rest)}
    flags = [w.lower() for w in _PROC_OPTION.sub(" ", header_rest).split()]
    j = i + 1
    last = head
    clauses: dict[str, str] = {}
    body: list[str] = []
    sql: list[SqlStatement] = []
    pending: _Pending | None = None
    while j < len(stmts):
        s = stmts[j]
        low = _lower(s)
        if low in ("run", "quit"):
            last = s
            j += 1
            break
        if _is_boundary(s):
            break
        last = s
        body.append(s.text.strip())
        if name == "sql":
            pending = _join_sql(pending, s, sql)
        else:
            key = low.split(None, 1)[0] if low else ""
            if key in _PROC_CLAUSES and key not in clauses:
                clauses[key] = s.text.strip()
        j += 1
    if name == "sql":
        if pending is not None:
            sql.append(parse_sql_statement(pending.text, pending.line))
        return ProcSql(sql, head.line, last.end_line, head.text), j
    return Proc(name, options, flags, clauses, head.line, last.end_line, head.text, body), j


@dataclass
class _Pending:
    """Sentencia de PROC SQL en curso: un pass-through puede traer `;` dentro de sus paréntesis."""

    text: str
    line: int
    depth: int


_QUOTED = re.compile(r"'[^']*'|\"[^\"]*\"")


def _join_sql(pending: _Pending | None, stmt: Stmt, out: list[SqlStatement]) -> _Pending | None:
    """Agrupa fragmentos de una sentencia SQL hasta que cierran sus paréntesis; luego la clasifica."""
    if pending is None:
        pending = _Pending(stmt.text, stmt.line, 0)
    else:
        pending.text = pending.text + ";\n" + stmt.text
    clean = _QUOTED.sub("", stmt.text)
    pending.depth += clean.count("(") - clean.count(")")
    if pending.depth <= 0:
        out.append(parse_sql_statement(pending.text, pending.line))
        return None
    return pending


def _parse_macro_def(stmts: list[Stmt], i: int) -> tuple[object, int]:
    head = stmts[i]
    m = re.match(r"(?is)^%macro\s+(\w+)\s*(?:\((.*)\))?\s*$", head.text.strip())
    if not m:
        return Unparsed(
            head.text, "cabecera de %macro no reconocida", head.line, head.end_line
        ), i + 1
    params = [
        p.split("=")[0].strip().lstrip("&") for p in (m.group(2) or "").split(",") if p.strip()
    ]
    body, j = parse_steps(stmts, i + 1, stop_at_mend=True)
    end = stmts[j] if j < len(stmts) else stmts[-1]
    return MacroDef(m.group(1), params, body, head.line, end.end_line, head.text), j + 1


def _parse_single(stmt: Stmt) -> object:
    text = stmt.text.strip()
    low = text.lower()
    if m := re.match(r"(?is)^%let\s+(\w+)\s*=\s*(.*)$", text):
        return Let(m.group(1), m.group(2).strip(), stmt.line, stmt.end_line, text)
    if low.startswith("%include"):
        path = re.search(r"""['"]([^'"]+)['"]""", text)
        return Include(path.group(1) if path else None, stmt.line, stmt.end_line, text)
    if m := re.match(r"(?is)^%(\w+)\s*(?:\((.*)\))?\s*$", text):
        if m.group(1).lower() not in MACRO_KEYWORDS:
            return MacroCall(m.group(1), (m.group(2) or "").strip(), stmt.line, stmt.end_line, text)
    if m := re.match(r"(?is)^libname\s+(\w+)\s*(.*)$", text):
        return Libname(m.group(1), m.group(2).strip(), stmt.line, stmt.end_line, text)
    if low.startswith("options"):
        return Options(text[len("options") :].strip(), stmt.line, stmt.end_line)
    if re.match(r"(?i)^x(\s|$)", text):
        return XCommand(text[1:].strip().strip("'\""), stmt.line, stmt.end_line, text)
    return Global(text, stmt.line, stmt.end_line)


def parse_steps(
    stmts: list[Stmt], i: int = 0, stop_at_mend: bool = False
) -> tuple[list[object], int]:
    """Agrupa sentencias en pasos desde `i`. Devuelve (pasos, índice donde se paró)."""
    steps: list[object] = []
    j = i
    while j < len(stmts):
        s = stmts[j]
        low = _lower(s)
        if low.startswith("%mend"):
            if stop_at_mend:
                return steps, j
            steps.append(Global(s.text, s.line, s.end_line))
            j += 1
            continue
        try:
            if low.startswith("%macro"):
                step, j = _parse_macro_def(stmts, j)
            elif re.match(r"data\b", low):
                step, j = _parse_data(stmts, j)
            elif re.match(r"proc(\s|$)", low):
                step, j = _parse_proc(stmts, j)
            else:
                step, j = _parse_single(s), j + 1
        except Exception as error:  # un paso malo no detiene el nodo
            step, j = (
                Unparsed(s.text, f"{type(error).__name__}: {error}", s.line, s.end_line),
                j + 1,
            )
        steps.append(step)
    return steps, j


def _shift(stmt: Stmt, offset: int) -> Stmt:
    return replace(stmt, line=stmt.line + offset, end_line=stmt.end_line + offset)


def parse_node(node: Node) -> ParsedNode:
    """Pasos de un nodo. Las líneas quedan en numeración del archivo original."""
    stmts = [_shift(s, node.line_start - 1) for s in split_statements(node.text)]
    steps, _ = parse_steps(stmts)
    return ParsedNode(node.label, node.line_start, node.line_end, steps)
