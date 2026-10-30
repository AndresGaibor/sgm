"""Pasada 1: construye las aristas de datos entre operadores por nombre de dataset.

- Cada dataset escrito y luego leído es una arista del productor al consumidor.
- Si un dataset se reescribe, la versión nueva se marca con `@vN` (`WORK.x@v2`), y las lecturas
  posteriores se conectan a esa versión.
- Un dataset permanente (biblioteca distinta de WORK) leído sin productor es un `read` fuente.
- Un dataset escrito que nadie lee, o que pertenece a una biblioteca permanente, termina en `write`.
"""

from __future__ import annotations

from sgm.ir.builder import qualify
from sgm.ir.models import Edge, Graph, Operator
from sgm.ir.signature import signature
from sgm.passes.base import PassContext, PassLog

NAME = "p01_graph"


def _consumed(op: Operator) -> list[str]:
    if op.kind == "read" and op.params.get("dataset"):
        return [op.params["dataset"]]
    names: list[str] = []
    for key in ("inputs", "sources"):
        names += [n for n in op.params.get(key, []) if isinstance(n, str)]
    return names


def _produced(op: Operator) -> list[str]:
    names = [n for n in op.params.get("outputs", []) if isinstance(n, str)]
    if op.kind == "split" and op.params.get("target"):
        names.append(qualify(op.params["target"]))
    return names


def _is_permanent(dataset: str) -> bool:
    return not dataset.upper().startswith("WORK.")


def run(graph: Graph, ctx: PassContext) -> PassLog:
    log = PassLog(NAME)
    operators = sorted(graph.operators(), key=lambda o: o.id)  # el id sigue el orden del programa
    current: dict[str, tuple[str, str]] = {}  # dataset -> (id del productor, nombre con versión)
    versions: dict[str, int] = {}
    final: list[tuple[str, str, str]] = []  # (productor, versión, dataset) de cada escritura
    consumed_versions: set[str] = set()
    sources = 0

    for op in operators:
        for dataset in _consumed(op):
            if dataset in current:
                producer, version = current[dataset]
                graph.add_edge(Edge(producer, op.id, version))
                consumed_versions.add(version)
            elif _is_permanent(dataset):
                sources += 1
        for dataset in _produced(op):
            versions[dataset] = versions.get(dataset, 0) + 1
            version = dataset if versions[dataset] == 1 else f"{dataset}@v{versions[dataset]}"
            current[dataset] = (op.id, version)
            final.append((op.id, version, dataset))

    last_version = {dataset: version for _, version, dataset in final}
    for number, (producer_id, version, dataset) in enumerate(final, 1):
        if version in consumed_versions and not (
            _is_permanent(dataset) and last_version[dataset] == version
        ):
            continue
        producer = graph.operator(producer_id)
        sink = Operator(
            id=f"w{number:05d}",
            kind="write",
            params={"dataset": version},
            evidence=list(producer.evidence),
            signature=signature("write", {"dataset": version}),
            notes=["salida final o de biblioteca permanente"],
        )
        graph.add_operator(sink)
        graph.add_edge(Edge(producer_id, sink.id, version))
        log.created.append(sink.id)

    log.metrics["fuentes_permanentes"] = sources
    log.metrics["aristas"] = len(graph.edges())
    log.notes.append(
        f"{len(graph.edges())} aristas por dataset; {len(log.created)} escrituras finales"
    )
    return log
