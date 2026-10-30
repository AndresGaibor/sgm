"""Pasada 4: decide dónde se ejecuta cada operador, en la base de datos o en el flujo.

Estrategia ávida: se recorre el grafo en orden topológico y cada operador se empuja a la base
si todas sus entradas están en el mismo motor y su tipo se expresa en SQL portable.
Si no, va al flujo.

Cada arista que cruza entre base y flujo se corta con un operador de frontera:
- de base a flujo: un `read` en el flujo;
- de flujo a base: un `write` en la base.

Así cada cambio de ubicación queda explícito y se cuenta en el registro de la pasada.
"""

from __future__ import annotations

import re

from sgm.ir.builder import Builder
from sgm.ir.models import Graph, Operator
from sgm.ir.signature import signature
from sgm.passes.base import PassContext, PassLog

NAME = "p04_placement"
SQL_KINDS = frozenset(
    {"filter", "derive", "join", "aggregate", "union", "sort", "dedup", "select", "rename"}
)
_FUNCTION = re.compile(r"\b([A-Za-z_]\w*)\s*\(")


def _library(dataset: str) -> str:
    return dataset.split(".", 1)[0].upper() if "." in dataset else "WORK"


def _portable(expressions: list[str], ctx: PassContext) -> bool:
    """Toda función que aparece en las expresiones tiene equivalente SQL portable."""
    for text in expressions:
        for name in _FUNCTION.findall(text):
            if name.lower() not in ctx.sql_portable:
                return False
    return True


def _expressible(op: Operator, ctx: PassContext) -> bool:
    """Si el operador se puede escribir como SQL portable sin perder lógica."""
    if op.kind not in SQL_KINDS or op.params.get("untranslated"):
        return False
    if op.kind == "filter":
        return _portable([str(op.params.get("expression", ""))], ctx)
    if op.kind == "derive":
        if op.params.get("conditional"):
            return False
        return _portable(
            [str(a.get("expression", "")) for a in op.params.get("assignments", [])], ctx
        )
    return True


def _engine_placement(dataset: str, ctx: PassContext) -> str | None:
    engine = ctx.library_engines.get(_library(dataset))
    return f"db:{engine}" if engine else None


def _boundary(src: Operator, dst: Operator, dataset: str, to_db: bool, op_id: str) -> Operator:
    if to_db:
        engine = dst.placement or src.placement or "db:?"
        params = {"dataset": dataset, "from": "flow"}
        kind, placement = "write", engine
    else:
        params = {"dataset": dataset, "from": src.placement or "db"}
        kind, placement = "read", "flow"
    return Operator(
        id=op_id,
        kind=kind,
        params=params,
        placement=placement,
        evidence=list(src.evidence),
        signature=signature(kind, params),
        notes=["frontera entre base de datos y flujo"],
    )


def run(graph: Graph, ctx: PassContext) -> PassLog:
    log = PassLog(NAME)
    for op_id in graph.topological():
        op = graph.operator(op_id)
        if op.placement is not None:
            continue
        preds = [graph.operator(p) for p in graph.predecessors(op_id)]
        if op.kind == "read":
            op.placement = _engine_placement(str(op.params.get("dataset", "")), ctx) or "flow"
        elif op.kind == "write":
            op.placement = _engine_placement(str(op.params.get("dataset", "")), ctx) or "flow"
        elif preds and _expressible(op, ctx) and _same_db(preds):
            op.placement = preds[0].placement
        else:
            op.placement = "flow"
    crossings = _cut_crossings(graph, log, Builder(graph))
    counts = {"db": 0, "flow": 0}
    for op in graph.operators():
        counts["flow" if op.placement == "flow" else "db"] += 1
    log.metrics.update(
        {
            "operadores_en_base": counts["db"],
            "operadores_en_flujo": counts["flow"],
            "cruces_base_a_flujo": crossings["to_flow"],
            "cruces_flujo_a_base": crossings["to_db"],
        }
    )
    log.notes.append(f"{crossings['to_flow']} cruces base→flujo y {crossings['to_db']} flujo→base")
    return log


def _same_db(preds: list[Operator]) -> bool:
    placements = {p.placement for p in preds}
    return (
        len(placements) == 1
        and next(iter(placements)) is not None
        and next(iter(placements)).startswith("db:")
    )


def _cut_crossings(graph: Graph, log: PassLog, builder: Builder) -> dict[str, int]:
    crossings = {"to_flow": 0, "to_db": 0}
    for edge in list(graph.edges()):
        src, dst = graph.operator(edge.src), graph.operator(edge.dst)
        src_db = bool(src.placement and src.placement.startswith("db:"))
        dst_db = bool(dst.placement and dst.placement.startswith("db:"))
        if src_db == dst_db:
            continue
        crossings["to_db" if dst_db else "to_flow"] += 1
        if dst.kind in ("read", "write") and dst.params.get("dataset") == edge.dataset:
            # El `read` o `write` que ya consume ese dataset es la frontera: no se añade otro.
            dst.params.setdefault("from", src.placement)
            continue
        boundary = _boundary(src, dst, edge.dataset, dst_db, builder.next_id())
        graph.split_edge(edge.src, edge.dst, edge.dataset, boundary)
        log.created.append(boundary.id)
    return crossings
