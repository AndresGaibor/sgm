"""Pasos del plan lógico con su forma validada (B-5).

`paso` añade un paso con los parámetros del constructor de `ir/operadores.py`; si el constructor
rechaza los datos, usa la forma `legado`. Lo usan los lowering de SQL, del DATA step y de los PROC.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

from sgm.ir.models import Operator

if TYPE_CHECKING:  # solo para anotar
    from sgm.ir.builder import Builder


class Cadena(Protocol):
    """Lo que `paso` necesita de la cadena de una rama: añadir un paso enlazado con el anterior."""

    def step(
        self, kind: str, params: dict, previous: Operator, status: str = "soportado"
    ) -> Operator: ...


def paso(
    chain: Cadena,
    kind: str,
    legado: dict,
    construir: Any,
    previous: Operator,
    status: str = "soportado",
) -> Operator:
    """Añade un paso con los parámetros del constructor; si lo rechaza, usa la forma `legado`."""
    try:
        params = construir().params
    except ValueError:
        params = legado
    return chain.step(kind, params, previous, status=status)


def op_validado(
    builder: "Builder",
    construir: Any,
    kind: str,
    legado: dict,
    ev: Any,
    *,
    status: str = "soportado",
    notes: list[str] | None = None,
) -> Operator:
    """Como `paso`, pero añade el operador con el `Builder` del lowering de DATA step y PROC."""
    try:
        params = construir().params
    except ValueError:
        params = legado
    return builder.op(kind, params, ev, status=status, notes=notes)


__all__ = ["Cadena", "op_validado", "paso"]
