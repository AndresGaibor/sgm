"""SQL de base para cadenas lineales de operadores (R5): qué se puede ejecutar en la base y cómo.

Solo entran los operadores con equivalente SQL exacto y sin esquema: `filter` (WHERE), `derive`
(columnas calculadas), `aggregate` (GROUP BY), `sort` (ORDER BY) y `dedup` sin claves (DISTINCT).
`join` y `union` quedan en flujo: sin esquemas no se pueden calificar las columnas con seguridad.

Las expresiones vienen en sintaxis de SAS; `sas_to_sql` las pasa a SQL. Si una expresión no se
puede escribir como SQL que `sqlglot` lee, o usa una función que no es portable
(`sql-functions.json`), la cadena no es renderable y el operador queda en flujo.

La cadena se escribe con `WITH`: cada paso es un CTE (`sgm_paso<n>`) que lee del anterior, en vez de
subconsultas anidadas. Es el mismo SQL para el motor (Impala) y más fácil de leer en la guía.
"""

from __future__ import annotations

import re

import sqlglot

from sgm.ir import sql_semantics
from sgm.ir.models import Graph, Operator
from sgm.ir.sql_portability import unportable_functions

DB_KINDS = frozenset({"filter", "derive", "aggregate", "sort", "dedup"})
CTE_PREFIX = "sgm_paso"  # nombre de cada CTE de la cadena; no choca con tablas del cliente
_MISSING = re.compile(r"(?i)\bNOT\s+missing\(\s*([\w.]+)\s*\)")
_MISSING_FN = re.compile(r"(?i)\bmissing\(\s*([\w.]+)\s*\)")
_SAS_NE = re.compile(r"(\^=|~=|¬=)")


def sas_to_sql(expression: str) -> str | None:
    """Expresión de SAS en SQL portable. None si no se puede escribir así."""
    text = _MISSING.sub(lambda m: f"{m.group(1)} IS NOT NULL", expression)
    text = _MISSING_FN.sub(lambda m: f"{m.group(1)} IS NULL", text)
    text = _SAS_NE.sub("<>", text)
    if "&" in text or "%" in text:
        return None  # macro variable: su valor sale de la ejecución
    try:
        names = unportable_functions(text)
    except sqlglot.errors.SqlglotError:
        return None
    return None if names else text


def _source_table(op: Operator) -> str | None:
    """Tabla de la base de la que sale una cadena: una lectura de base o una carga única."""
    if op.kind == "read" and op.placement and op.placement.startswith("db:"):
        return str(op.params.get("dataset") or "") or None
    if op.kind == "external_load" and op.params.get("destination"):
        return str(op.params["destination"])
    return None


def _step_sql(op: Operator, source: str) -> str | None:
    """SELECT de un paso que lee de `source` (tabla o CTE). None si el paso no es renderable."""
    if op.kind == "filter":
        cond = sas_to_sql(str(op.params.get("expression", "")))
        return None if cond is None else f"SELECT * FROM {source} WHERE {cond}"
    if op.kind == "derive":
        parts = []
        for a in op.params.get("assignments", []):
            expr = sas_to_sql(str(a.get("expression", "")))
            if expr is None or not a.get("target"):
                return None
            parts.append(f"{expr} AS {a['target']}")
        return f"SELECT *, {', '.join(parts)} FROM {source}" if parts else f"SELECT * FROM {source}"
    if op.kind == "aggregate":
        if sql_semantics.aggregate_pendiente(op.params):
            return None  # columnas sin agregar junto a agregados: la regla lo deja pendiente
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
        return f"SELECT {select} FROM {source}{group}"
    if op.kind == "sort":
        by = [str(k) for k in op.params.get("by", [])]
        if not by:
            return f"SELECT * FROM {source}"
        desc = list(op.params.get("descending", []))
        order = [f"{k} DESC" if i < len(desc) and desc[i] else k for i, k in enumerate(by)]
        return f"SELECT * FROM {source} ORDER BY {', '.join(order)}"
    if op.kind == "dedup":
        return f"SELECT DISTINCT * FROM {source}" if not op.params.get("by") else None
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
    """Consulta SQL de una cadena en `WITH` (`steps[0]` es la fuente). None si no es renderable.

    Ejemplo de salida: `WITH sgm_paso0 AS (SELECT * FROM t), sgm_paso1 AS (SELECT ... FROM sgm_paso0
    WHERE ...) SELECT * FROM sgm_paso1`. Una cadena sin pasos de SQL es un `SELECT * FROM t`.
    """
    source = _source_table(steps[0])
    if not source:
        return None
    ctes = [(f"{CTE_PREFIX}0", f"SELECT * FROM {source}")]
    for op in steps[1:]:
        body = _step_sql(op, ctes[-1][0])
        if body is None:
            return None
        ctes.append((f"{CTE_PREFIX}{len(ctes)}", body))
    if len(ctes) == 1:
        return ctes[0][1]
    clauses = ", ".join(f"{name} AS ({body})" for name, body in ctes)
    return f"WITH {clauses} SELECT * FROM {ctes[-1][0]}"
