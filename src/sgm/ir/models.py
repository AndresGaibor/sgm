"""Modelos de la IR lógica: evidencia, columnas, operadores, aristas, grafo, jobs y plan.

Reglas de estos modelos:
1. La firma (`signature`) es la llave de overrides, huecos, plantillas y caché.
   El `id` de un operador cambia con cada compilación: no es llave persistente.
2. `evidence` es una lista. Al fusionar operadores, se unen las listas.
3. Cada pasada transforma el grafo y devuelve su registro (`PassLog`); no guarda estado propio.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any

import networkx as nx

OPERATOR_KINDS = frozenset(
    {
        "read",
        "read_file",
        "filter",
        "derive",
        "rename",
        "select",
        "join",
        "lookup",
        "aggregate",
        "sort",
        "dedup",
        "union",
        "split",
        "write",
        "write_file",
        "exec_sql",
        "external_load",
        "stateful_row",
        "iterate",
        "map",
        "unsupported",
    }
)
STATUSES = frozenset({"soportado", "parcial", "reemplazado", "hueco"})
MATERIALIZE = frozenset({"hash", "temp_table", "file"})


@dataclass(frozen=True)
class Evidence:
    file: str
    line_start: int
    line_end: int
    label: str | None
    call: str | None = None
    # invocación de macro de origen (la más externa), "archivo:línea:nombre"


@dataclass
class Column:
    name: str
    type: str | None = None  # String, Integer, Long, Double, BigDecimal, Date, Boolean o None
    length: int | None = None
    source: str = "unknown"  # catalog, file_header, derived o unknown


@dataclass
class Operator:
    id: str
    kind: str
    params: dict[str, Any] = field(default_factory=dict)
    placement: str | None = None  # "db:<motor>", "flow" o None
    schema: list[Column] | None = None
    evidence: list[Evidence] = field(default_factory=list)
    status: str = "soportado"
    signature: str = ""
    notes: list[str] = field(default_factory=list)
    component: dict[str, Any] | None = None  # componente Talend candidato (pasada 10)
    origin: str | None = None  # constructo SAS de origen (diagnóstico; no entra en la firma)


@dataclass(frozen=True)
class Edge:
    src: str
    dst: str
    dataset: str  # WORK.X, LIB.tabla, ruta; "@vN" si se reescribe; "(interno)" dentro de un paso
    materialize: str | None = None  # None, "hash", "temp_table", "file"


class Graph:
    """Grafo dirigido de operadores (envuelve un `networkx.MultiDiGraph`)."""

    def __init__(self) -> None:
        self._g: nx.MultiDiGraph = nx.MultiDiGraph()

    def add_operator(self, op: Operator) -> None:
        if op.kind not in OPERATOR_KINDS:
            raise ValueError(f"tipo de operador desconocido: {op.kind}")
        if op.status not in STATUSES:
            raise ValueError(f"estado desconocido: {op.status}")
        self._g.add_node(op.id, op=op)

    def operator(self, op_id: str) -> Operator:
        return self._g.nodes[op_id]["op"]

    def operators(self) -> list[Operator]:
        return [data["op"] for _, data in self._g.nodes(data=True)]

    def __contains__(self, op_id: object) -> bool:
        return op_id in self._g

    def __len__(self) -> int:
        return self._g.number_of_nodes()

    def remove_operator(self, op_id: str) -> None:
        self._g.remove_node(op_id)

    def add_edge(self, edge: Edge) -> None:
        if edge.materialize is not None and edge.materialize not in MATERIALIZE:
            raise ValueError(f"materialización desconocida: {edge.materialize}")
        self._g.add_edge(edge.src, edge.dst, edge=edge)

    def edges(self) -> list[Edge]:
        return [data["edge"] for _, _, data in self._g.edges(data=True)]

    def set_edge_materialize(self, edge: Edge, materialize: str) -> None:
        """Marca una arista como materializada (la decide la pasada de particionado)."""
        for key, data in self._g[edge.src][edge.dst].items():
            if data["edge"] == edge:
                self._g[edge.src][edge.dst][key]["edge"] = Edge(
                    edge.src, edge.dst, edge.dataset, materialize
                )
                return
        raise KeyError(f"arista no encontrada: {edge.src}->{edge.dst} {edge.dataset}")

    def bypass(self, op_id: str) -> None:
        """Quita un operador y conecta cada predecesor con cada sucesor (con el dataset de entrada).
        Quita un operador y conecta cada predecesor con cada sucesor (con el dataset de entrada)."""
        for pred in list(self._g.predecessors(op_id)):
            for data in list(self._g[pred][op_id].values()):
                for succ in list(self._g.successors(op_id)):
                    if succ != pred:
                        self._g.add_edge(pred, succ, edge=Edge(pred, succ, data["edge"].dataset))
        self._g.remove_node(op_id)

    def _add_once(self, edge: Edge) -> None:
        """Añade una arista salvo que ya exista una igual (mismos extremos y dataset)."""
        if edge.dst in self._g[edge.src] and any(
            d["edge"].dataset == edge.dataset for d in self._g[edge.src][edge.dst].values()
        ):
            return
        self.add_edge(edge)

    def replace(self, op_ids: list[str], new: Operator) -> None:
        """Sustituye un conjunto de operadores por `new`, reconectando las aristas que cruzan el
        borde."""
        group = set(op_ids)
        self.add_operator(new)  # antes de las aristas: el nodo nuevo tiene que existir
        for op_id in op_ids:
            for pred in list(self._g.predecessors(op_id)):
                if pred in group:
                    continue
                for data in list(self._g[pred][op_id].values()):
                    self._add_once(Edge(pred, new.id, data["edge"].dataset))
            for succ in list(self._g.successors(op_id)):
                if succ in group:
                    continue
                for data in list(self._g[op_id][succ].values()):
                    self._add_once(Edge(new.id, succ, data["edge"].dataset))
        for op_id in op_ids:
            self._g.remove_node(op_id)

    def topological(self) -> list[str]:
        """Ids en orden topológico (productores antes que consumidores)."""
        return list(nx.topological_sort(self._g))

    def split_edge(self, src: str, dst: str, dataset: str, new: Operator) -> None:
        """Inserta `new` entre `src` y `dst`: la arista con ese dataset pasa por `new`."""
        for key, data in list(self._g[src][dst].items()):
            if data["edge"].dataset == dataset:
                self._g.remove_edge(src, dst, key=key)
                break
        else:
            raise KeyError(f"arista no encontrada: {src}->{dst} {dataset}")
        self.add_operator(new)
        self.add_edge(Edge(src, new.id, dataset))
        self.add_edge(Edge(new.id, dst, dataset))

    def ancestors(self, op_id: str) -> set[str]:
        return set(nx.ancestors(self._g, op_id))

    def reaches(self, src: str, dst: str) -> bool:
        return nx.has_path(self._g, src, dst)

    def successors(self, op_id: str) -> list[str]:
        return list(self._g.successors(op_id))

    def predecessors(self, op_id: str) -> list[str]:
        return list(self._g.predecessors(op_id))

    def merge(self, keep: str, drop: str) -> None:
        """Fusiona `drop` en `keep`: une la evidencia y redirige sus aristas."""
        kept, dropped = self.operator(keep), self.operator(drop)
        for ev in dropped.evidence:
            if ev not in kept.evidence:
                kept.evidence.append(ev)
        for pred in list(self._g.predecessors(drop)):
            if pred == keep:
                continue
            for data in list(self._g[pred][drop].values()):
                self._g.add_edge(pred, keep, edge=data["edge"])
        for succ in list(self._g.successors(drop)):
            if succ == keep:
                continue
            for data in list(self._g[drop][succ].values()):
                self._g.add_edge(keep, succ, edge=data["edge"])
        self._g.remove_node(drop)

    def subgraph_ids(self) -> Iterator[list[str]]:
        """Componentes débilmente conexas, cada una como lista de ids."""
        for comp in nx.weakly_connected_components(self._g):
            yield sorted(comp)


@dataclass
class Job:
    name: str
    subjobs: list[list[str]] = field(
        default_factory=list
    )  # cada subjob: ids de operadores en orden
    contexts: dict[str, Any] = field(default_factory=dict)
    children: list[Job] = field(default_factory=list)


@dataclass
class NotMigrated:
    op_id: str
    what: str
    talend: str
    evidence: list[Evidence]


@dataclass
class Pending:
    signature: str
    options: list[dict[str, Any]]
    default: str
    occurrences: int = 1


@dataclass
class Gap:
    signature: str
    reason: str
    evidence: list[Evidence]
    text: str = ""  # sentencia que causa el hueco, recortada


@dataclass
class Plan:
    program: str
    graph: Graph = field(default_factory=Graph)
    jobs: list[Job] = field(default_factory=list)
    not_migrated: list[NotMigrated] = field(default_factory=list)
    pending: list[Pending] = field(default_factory=list)
    gaps: list[Gap] = field(default_factory=list)
