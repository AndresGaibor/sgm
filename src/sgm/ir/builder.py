"""Constructor de operadores y aristas con su firma y su evidencia."""

from __future__ import annotations

from typing import Any

from sgm.ir.models import Edge, Evidence, Graph, Operator
from sgm.ir.signature import signature

INTERNAL = "(interno)"


def qualify(name: str) -> str:
    """Nombre de dataset calificado: `WORK.x` si no tiene biblioteca, `LIB.tabla` si la tiene."""
    clean = name.strip()
    if "." in clean:
        lib, table = clean.split(".", 1)
        return f"{lib.upper()}.{table.lower()}"
    return f"WORK.{clean.lower()}"


class Builder:
    """Crea operadores con id secuencial dentro de un plan y los conecta en el grafo."""

    def __init__(self, graph: Graph) -> None:
        self.graph = graph
        self._count = 0

    def op(
        self,
        kind: str,
        params: dict[str, Any],
        ev: Evidence,
        *,
        status: str = "soportado",
        notes: list[str] | None = None,
        placement: str | None = None,
    ) -> Operator:
        self._count += 1
        operator = Operator(
            id=f"op{self._count:05d}",
            kind=kind,
            params=params,
            placement=placement,
            evidence=[ev],
            status=status,
            signature=signature(kind, params),
            notes=list(notes or []),
        )
        self.graph.add_operator(operator)
        return operator

    def link(self, src: Operator, dst: Operator, dataset: str = INTERNAL) -> None:
        self.graph.add_edge(Edge(src.id, dst.id, dataset))

    def refresh(self, operator: Operator) -> None:
        """Recalcula la firma tras cambiar los parámetros de un operador ya creado."""
        operator.signature = signature(operator.kind, operator.params)
