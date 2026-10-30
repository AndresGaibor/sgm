"""SQL de base para cadenas lineales de operadores (R5): qué se puede ejecutar en la base y cómo.

Solo entran los operadores con equivalente SQL exacto y sin esquema: `filter` (WHERE), `derive`
(columnas calculadas), `aggregate` (GROUP BY), `sort` (ORDER BY) y `dedup` sin claves (DISTINCT).
`join` y `union` quedan en flujo: sin esquemas no se pueden calificar las columnas con seguridad.

Las expresiones vienen en sintaxis de SAS; `sas_to_sql` las pasa a SQL. Si una expresión no se
puede escribir como SQL que `sqlglot` lee, la cadena no es renderable y el operador queda en flujo.
"""

from __future__ import annotations

import re

import sqlglot

from sgm.ir.models import Graph, Operator

DB_KINDS = frozenset({"filter", "derive", "aggregate", "sort", "dedup"})
_MISSING = re.compile(r"(?i)\bNOT\s+missing\(\s*([\w.]+)\s*\)")
_MISSING_FN = re.compile(r"(?i)\bmissing\(\s*([\w.]+)\s*\)")
_SAS_NE = re.compile(r"(\^=|~=|¬=)")


def sas_to_sql(expression: str) -> str | None:
    """Expresión de SAS en SQL. None si no se puede escribir como SQL que `sqlglot` lee."""
    text = _MISSING.sub(lambda m: f"{m.group(1)} IS NOT NULL", expression)
    text = _MISSING_FN.sub(lambda m: f"{m.group(1)} IS NULL", text)
    text = _SAS_NE.sub("<>", text)
    if "&" in text or "%" in text:
        return None  # macro variable: su valor sale de la ejecución
    try:
        sqlglot.parse_one(f"SELECT {text}")
    except sqlglot.errors.SqlglotError:
        return None
    return text


def _source_table(op: Operator) -> str | None:
    """Tabla de la base de la que sale una cadena: una lectura de base o una carga única."""
    if op.kind == "read" and op.placement and op.placement.startswith("db:"):
        return str(op.params.get("dataset") or "") or None
    if op.kind == "external_load" and op.params.get("destination"):
        return str(op.params["destination"])
    return None


def _step_sql(op: Operator, query: str) -> str | None:
    """Consulta de un paso sobre la consulta `query` (subconsulta `t`). None si no es renderable."""
    if op.kind == "filter":
        cond = sas_to_sql(str(op.params.get("expression", "")))
        return None if cond is None else f"SELECT * FROM ({query}) t WHERE {cond}"
    if op.kind == "derive":
        parts = []
        for a in op.params.get("assignments", []):
            expr = sas_to_sql(str(a.get("expression", "")))
            if expr is None or not a.get("target"):
                return None
            parts.append(f"{expr} AS {a['target']}")
        return f"SELECT *, {', '.join(parts)} FROM ({query}) t" if parts else query
    if op.kind == "aggregate":
        keys = [str(k) for k in op.params.get("group_by", [])]
        aggs = []
        for agg in op.params.get("aggregations", []):
            expr = sas_to_sql(str(agg.get("expression", "")))
            if expr is None or not agg.get("alias"):
                return None
            aggs.append(f"{expr} AS {agg['alias']}")
        if not aggs:
            return None
        select = ", ".join(keys + aggs)
        group = f" GROUP BY {', '.join(keys)}" if keys else ""
        return f"SELECT {select} FROM ({query}) t{group}"
    if op.kind == "sort":
        by = [str(k) for k in op.params.get("by", [])]
        if not by:
            return query
        desc = list(op.params.get("descending", []))
        order = [f"{k} DESC" if i < len(desc) and desc[i] else k for i, k in enumerate(by)]
        return f"SELECT * FROM ({query}) t ORDER BY {', '.join(order)}"
    if op.kind == "dedup":
        return f"SELECT DISTINCT * FROM ({query}) t" if not op.params.get("by") else None
    return None


def chain(graph: Graph, sink: Operator) -> list[Operator] | None:
    """Cadena lineal que termina en `sink`, desde su lectura de base (en orden). None si no lo es.

    Cada paso tiene un único predecesor y cada intermedio, un único sucesor: así la cadena se puede
    sustituir por una sola sentencia sin que otro operador necesite una salida intermedia.
    """
    steps = [sink]
    current = sink
    while True:
        preds = graph.predecessors(current.id)
        if len(preds) != 1:
            return None
        previous = graph.operator(preds[0])
        if _source_table(previous) is not None:
            steps.insert(0, previous)
            return steps
        in_base = (previous.placement or "").startswith("db:")
        if not in_base or previous.kind not in DB_KINDS or len(graph.successors(previous.id)) != 1:
            return None
        steps.insert(0, previous)
        current = previous


def render(steps: list[Operator]) -> str | None:
    """Consulta SQL de una cadena (`steps[0]` es la fuente). None si algún paso no es renderable."""
    query = f"SELECT * FROM {_source_table(steps[0])}"
    for op in steps[1:]:
        query = _step_sql(op, query)
        if query is None:
            return None
    return query
