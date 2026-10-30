"""Pasada 8: corta el grafo en subjobs y decide qué aristas se materializan.

El job por defecto es uno por programa. Sus subjobs siguen el orden topológico. Se corta solo en
estos casos:
1. Salida final o compartida: después de un `write` o de una carga externa, el subjob termina.
2. Iteración: cada `iterate` (llamada a un Job hijo) ocupa su propio subjob.
3. Más de `MAX_COMPONENTS` operadores en un subjob (parámetro configurable).

Además, un agregado que vuelve a unirse con su detalle en flujo necesita una arista
materializada. Su
volumen no se conoce, así que se marca `temp_table` y queda como decisión pendiente.
"""

from __future__ import annotations

from sgm.ir.models import Graph, Job, Operator, Pending
from sgm.passes.base import PassContext, PassLog

NAME = "p08_partition"
MAX_COMPONENTS = 200
_CUT_AFTER = frozenset({"write", "external_load"})
_CUT_BEFORE_AND_AFTER = frozenset({"iterate"})


def _materialize(graph: Graph, ctx: PassContext, log: PassLog) -> None:
    """Agregado que vuelve a unirse, en flujo, con un dato que comparte con su detalle.

    Se materializa la arista que sale del agregado hacia la lectura que llega al join.
    Como el volumen no se conoce, queda `temp_table` con una decisión pendiente.
    """
    for agg in graph.operators():
        if agg.kind != "aggregate" or (agg.placement or "flow") != "flow":
            continue
        shared = graph.ancestors(agg.id) | {agg.id}
        for edge in [e for e in graph.edges() if e.src == agg.id]:
            if edge.materialize is not None:
                continue
            mid = graph.operator(edge.dst)
            joins = (
                [mid]
                if mid.kind == "join"
                else [
                    graph.operator(s)
                    for s in graph.successors(mid.id)
                    if graph.operator(s).kind == "join"
                ]
            )
            for join in joins:
                others = [p for p in graph.predecessors(join.id) if p != mid.id]
                if not any(p in shared or graph.ancestors(p) & shared for p in others):
                    continue
                graph.set_edge_materialize(edge, "temp_table")
                log.metrics["materializadas"] = log.metrics.get("materializadas", 0) + 1
                ctx.plan.pending.append(
                    Pending(
                        signature=agg.signature,
                        options=[
                            {
                                "opcion": "temp_table",
                                "confianza": "media",
                                "supuesto": "volumen grande",
                            },
                            {"opcion": "hash", "confianza": "media", "supuesto": "volumen pequeño"},
                        ],
                        default="temp_table",
                    )
                )
                break


def _subjobs(graph: Graph) -> tuple[list[list[str]], list[str]]:
    """Subjobs en orden topológico, y el motivo de cada corte (para el diagnóstico)."""
    subjobs: list[list[str]] = []
    cuts: list[str] = []
    current: list[str] = []

    def flush(reason: str) -> None:
        if current:
            subjobs.append(list(current))
            current.clear()
            cuts.append(reason)

    for op_id in graph.topological():
        op: Operator = graph.operator(op_id)
        if op.kind in _CUT_BEFORE_AND_AFTER:
            flush("antes_de_iterate")
            subjobs.append([op_id])
            cuts.append("iterate")
            continue
        current.append(op_id)
        if op.kind in _CUT_AFTER:
            flush(f"despues_de_{op.kind}")
        elif len(current) >= MAX_COMPONENTS:
            flush("tamano_maximo")
    flush("fin_del_programa")
    return subjobs, cuts


def run(graph: Graph, ctx: PassContext) -> PassLog:
    log = PassLog(NAME)
    _materialize(graph, ctx, log)
    subjobs, cuts = _subjobs(graph)
    if not ctx.plan.jobs:
        ctx.plan.jobs = [Job(name=ctx.plan.program)]
    ctx.plan.jobs[0].subjobs = subjobs
    log.metrics["subjobs"] = len(subjobs)
    log.metrics["operadores_maximo_por_subjob"] = max((len(s) for s in subjobs), default=0)
    log.metrics["cortes"] = {reason: cuts.count(reason) for reason in sorted(set(cuts))}
    return log
