"""Pasada 6: une operadores de flujo en un solo `map` (tMap).

Dos formas:
1. Cadena: filtros, derivaciones, renombres y selecciones encadenados (cada uno con un solo
   predecesor y un solo sucesor) se unen en un `map` con la lista de pasos en orden.
2. Ramificación: una fuente que alimenta varias ramas `read -> filter` se une en un `map` con una
   salida por rama.

Un filtro o selección aislado no se fusiona: un `map` de un solo paso no aporta nada.
"""

from __future__ import annotations

from sgm.ir.builder import Builder
from sgm.ir.models import Graph, Operator
from sgm.ir.signature import signature
from sgm.passes.base import PassContext, PassLog

NAME = "p06_flow_fusion"
CHAINABLE = frozenset({"filter", "derive", "rename", "select"})
_RANK = {"soportado": 0, "parcial": 1, "reemplazado": 2, "hueco": 3}


def _in_flow(op: Operator) -> bool:
    return op.placement in (None, "flow")


def _worst(ops: list[Operator]) -> str:
    return max((o.status for o in ops), key=lambda s: _RANK.get(s, 0), default="soportado")


def _union(ops: list[Operator]) -> list:
    evidence: list = []
    for op in ops:
        for ev in op.evidence:
            if ev not in evidence:
                evidence.append(ev)
    return evidence


def _chains(graph: Graph) -> list[list[Operator]]:
    """Cadenas maximales de operadores encadenables (de dos o más)."""
    chains: list[list[Operator]] = []
    used: set[str] = set()
    for op_id in graph.topological():
        op = graph.operator(op_id)
        if op_id in used or op.kind not in CHAINABLE or not _in_flow(op):
            continue
        chain = [op]
        used.add(op_id)
        current = op
        while True:
            succs = graph.successors(current.id)
            if len(succs) != 1:
                break
            nxt = graph.operator(succs[0])
            if nxt.kind not in CHAINABLE or not _in_flow(nxt) or succs[0] in used:
                break
            if len(graph.predecessors(nxt.id)) != 1:
                break
            chain.append(nxt)
            used.add(nxt.id)
            current = nxt
        if len(chain) >= 2:
            chains.append(chain)
    return chains


def _step(op: Operator) -> dict:
    return {"kind": op.kind, "params": op.params}


def _branch_pairs(graph: Graph) -> list[tuple[Operator, Operator, Operator]]:
    """(fuente, lectura, filtro) de cada rama: la fuente alimenta una lectura
    cuyo único sucesor es un filtro."""
    pairs = []
    for src_id in graph.topological():
        src = graph.operator(src_id)
        if not _in_flow(src):
            continue
        for read_id in graph.successors(src_id):
            read = graph.operator(read_id)
            if read.kind != "read" or not _in_flow(read) or len(graph.successors(read_id)) != 1:
                continue
            filt = graph.operator(graph.successors(read_id)[0])
            if filt.kind == "filter" and _in_flow(filt) and len(graph.predecessors(filt.id)) == 1:
                pairs.append((src, read, filt))
    return pairs


def run(graph: Graph, ctx: PassContext) -> PassLog:
    log = PassLog(NAME)
    builder = Builder(graph)
    for chain in _chains(graph):
        params = {"steps": [_step(op) for op in chain]}
        outputs = chain[-1].params.get("outputs", [])
        if outputs:
            params["outputs"] = list(outputs)
        merged = Operator(
            id=builder.next_id(),
            kind="map",
            params=params,
            placement="flow",
            evidence=_union(chain),
            status=_worst(chain),
            signature=signature("map", params),
            notes=[f"{len(chain)} operadores de flujo unidos en un tMap (pasada 6)"],
        )
        graph.replace([op.id for op in chain], merged)
        log.created.append(merged.id)
        log.merged += [op.id for op in chain]
    pairs = _branch_pairs(graph)
    by_source: dict[str, list[tuple[Operator, Operator, Operator]]] = {}
    for src, read, filt in pairs:
        by_source.setdefault(src.id, []).append((src, read, filt))
    for group in by_source.values():
        if len(group) < 2:
            continue
        ops = [op for _, read, filt in group for op in (read, filt)]
        params = {
            "branches": [
                {
                    "expression": flt.params.get("expression", ""),
                    "outputs": list(flt.params.get("outputs", [])),
                }
                for _, _, flt in group
            ]
        }
        merged = Operator(
            id=builder.next_id(),
            kind="map",
            params=params,
            placement="flow",
            evidence=_union(ops),
            status=_worst(ops),
            signature=signature("map", params),
            notes=[f"{len(group)} ramas filtradas de un mismo dataset en un tMap (pasada 6)"],
        )
        graph.replace([op.id for op in ops], merged)
        log.created.append(merged.id)
        log.merged += [op.id for op in ops]
    log.metrics["mapas"] = len(log.created)
    return log
