"""Pasada 8: parte el grafo en subjobs y decide qué aristas se materializan.

Un subjob es un componente conexo de conexiones de filas: los operadores unidos por una arista
entre sí forman un único subjob, en orden topológico. Ya no se crea un subjob por nodo SAS ni por
etiqueta: la etiqueta de SAS Studio es solo la etiqueta del componente.

Los operadores de control van cada uno en su propio subjob, y el orden lo da el encadenamiento de
Talend (OnSubjobOk), no una conexión de filas:
- `exec_sql`: una sentencia de base de datos (ya fusionada por la pasada 5).
- `external_load`: la carga única de un archivo o de una región de carga.
- `iterate`: la llamada a un Job hijo.

Un componente que supera `max_components_per_job` (`env/project.json`) se parte en trozos en orden
topológico. Es el único corte que rompe una conexión de filas, y queda anotado como tamaño máximo.

Además, un agregado que vuelve a unirse con su detalle en flujo necesita decidir si su arista se
materializa. Su volumen no se conoce: la arista no se materializa y queda como decisión pendiente,
con `temp_table` como sugerencia no aplicada.
"""

from __future__ import annotations

from sgm.ir.models import Graph, Job, Pending
from sgm.passes.base import PassContext, PassLog

NAME = "p08_partition"
CONTROL = frozenset({"exec_sql", "external_load", "iterate"})


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
                # No se materializa: la elección depende del volumen, que no se conoce. La arista
                # queda sin materializar y la decisión lleva la sugerencia, no aplicada.
                log.metrics["pendientes_materializacion"] = (
                    log.metrics.get("pendientes_materializacion", 0) + 1
                )
                ctx.plan.pending.append(
                    Pending(
                        signature=agg.signature,
                        options=[
                            {
                                "opcion": "temp_table",
                                "confianza": "media",
                                "supuesto": "volumen grande",
                                "aplicado": False,
                            },
                            {
                                "opcion": "hash",
                                "confianza": "media",
                                "supuesto": "volumen pequeño",
                                "aplicado": False,
                            },
                        ],
                        default="temp_table",
                    )
                )
                break


def _find(parent: dict[str, str], op_id: str) -> str:
    while parent[op_id] != op_id:
        parent[op_id] = parent[parent[op_id]]
        op_id = parent[op_id]
    return op_id


def _has_component(op) -> bool:
    """Operadores que p10 convertirá en componente. Los demás no ocupan subjob, pero sí unen a sus
    vecinos a través de ellos: configuración, huecos, pasos ya reemplazados, y los `read` y `write`
    de flujo (solo traspasan un dataset WORK entre dos pasos: su componente es `none`)."""
    if op.kind == "unsupported" or op.status in ("hueco", "reemplazado"):
        return False
    return not (op.kind in ("read", "write") and (op.placement or "flow") == "flow")


def _subjobs(graph: Graph, max_components: int) -> tuple[list[list[str]], list[str]]:
    """Subjobs en orden topológico, y el motivo de cada uno (para el diagnóstico)."""
    order = graph.topological()
    operators = {op_id: graph.operator(op_id) for op_id in order}
    control = {op_id for op_id, op in operators.items() if op.kind in CONTROL}
    flow = {op_id for op_id, op in operators.items() if op_id not in control and _has_component(op)}
    parent = {op_id: op_id for op_id in flow}
    for edge in graph.edges():
        if edge.src in flow and edge.dst in flow:
            parent[_find(parent, edge.src)] = _find(parent, edge.dst)
    for op_id in order:  # un operador sin componente une a todos sus vecinos con componente
        if op_id in flow or op_id in control:
            continue
        neighbours = [n for n in graph.predecessors(op_id) + graph.successors(op_id) if n in flow]
        for other in neighbours[1:]:
            parent[_find(parent, neighbours[0])] = _find(parent, other)
    groups: dict[str, list[str]] = {}
    for op_id in order:  # el primer miembro de cada grupo fija su posición
        if op_id not in flow and op_id not in control:
            continue
        root = _find(parent, op_id) if op_id in flow else op_id
        groups.setdefault(root, []).append(op_id)
    subjobs: list[list[str]] = []
    cuts: list[str] = []
    for members in groups.values():
        if len(members) == 1 and members[0] not in flow:
            subjobs.append(members)
            cuts.append(graph.operator(members[0]).kind)
            continue
        for start in range(0, len(members), max_components):
            chunk = members[start : start + max_components]
            subjobs.append(chunk)
            cuts.append("componente_conexo" if len(members) <= max_components else "tamano_maximo")
    return subjobs, cuts


def run(graph: Graph, ctx: PassContext) -> PassLog:
    log = PassLog(NAME)
    _materialize(graph, ctx, log)
    subjobs, cuts = _subjobs(graph, ctx.project.max_components_per_job)
    if not ctx.plan.jobs:
        ctx.plan.jobs = [Job(name=ctx.plan.program)]
    ctx.plan.jobs[0].subjobs = subjobs
    log.metrics["subjobs"] = len(subjobs)
    log.metrics["operadores_maximo_por_subjob"] = max((len(s) for s in subjobs), default=0)
    log.metrics["cortes"] = {reason: cuts.count(reason) for reason in sorted(set(cuts))}
    return log
