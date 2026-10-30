"""Orden de las pasadas. Cada una recibe el grafo y el contexto y devuelve su registro."""

from __future__ import annotations

from sgm.passes import (
    p01_graph,
    p02_plumbing,
    p03_intrinsics,
    p04_placement,
    p05_sql_fusion,
    p06_flow_fusion,
    p07_templates,
    p08_partition,
    p09_schemas,
    p10_components,
)
from sgm.passes.base import PassContext, PassLog


def run_passes(ctx: PassContext) -> list[PassLog]:
    graph = ctx.plan.graph
    logs = [p01_graph.run(graph, ctx)]
    logs.append(p02_plumbing.mark(graph, ctx))
    logs.append(p03_intrinsics.run(graph, ctx))
    logs.append(p04_placement.run(graph, ctx))
    logs.append(p05_sql_fusion.run(graph, ctx))
    logs.append(p06_flow_fusion.run(graph, ctx))
    logs.append(p07_templates.run(graph, ctx))
    logs.append(p08_partition.run(graph, ctx))
    logs.append(p09_schemas.run(graph, ctx, ctx.schemas))
    logs.append(p10_components.run(graph, ctx))
    return logs
