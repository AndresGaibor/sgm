"""Linaje entre programas: oleadas de ejecución según los datasets permanentes de cada uno.

WORK es local a cada programa; solo cuentan las bibliotecas permanentes. Si A escribe una tabla que
lee B, B va en una oleada posterior a A. Los ciclos se agrupan en una sola oleada.
"""

from __future__ import annotations

import networkx as nx

from sgm.compile import Compiled


def _datasets(compiled: Compiled) -> tuple[set[str], set[str]]:
    """Datasets permanentes que el programa escribe y que lee (sin WORK)."""
    writes: set[str] = set()
    reads: set[str] = set()
    for op in compiled.plan.graph.operators():
        for name in op.params.get("outputs", []):
            writes.add(name)
        if op.kind == "write" and op.params.get("dataset"):
            writes.add(op.params["dataset"])
        if op.kind == "read" and op.params.get("dataset"):
            reads.add(op.params["dataset"])
        for key in ("inputs", "sources"):
            reads.update(n for n in op.params.get(key, []) if isinstance(n, str))
    return _permanent(writes), _permanent(reads)


def _permanent(names: set[str]) -> set[str]:
    return {n for n in names if not n.upper().startswith("WORK.")}


def graph_of(compiled: dict[str, Compiled]) -> nx.DiGraph:
    """Grafo dirigido de programas: A -> B si A escribe un dataset permanente que B lee."""
    g = nx.DiGraph()
    g.add_nodes_from(compiled)
    data = {name: _datasets(result) for name, result in compiled.items()}
    for a, (writes_a, _) in data.items():
        for b, (_, reads_b) in data.items():
            if a != b and writes_a & reads_b:
                g.add_edge(a, b)
    return g


def waves(compiled: dict[str, Compiled]) -> list[list[str]]:
    """Oleadas de ejecución: cada lista puede correr en paralelo tras la anterior."""
    g = graph_of(compiled)
    condensed = nx.condensation(g)
    result: list[list[str]] = []
    for generation in nx.topological_generations(condensed):
        members: list[str] = []
        for node in generation:
            members += sorted(condensed.nodes[node]["members"])
        result.append(sorted(members))
    return result
