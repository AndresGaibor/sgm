"""Pasos del plan lógico con su forma validada (B-5).

`paso` añade un paso con los parámetros del constructor de `ir/operadores.py`; si el constructor
rechaza los datos, usa la forma `legado`. Lo usan los lowering de SQL, del DATA step y de los PROC.
"""

from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING, Any, Protocol

from sgm.ir.models import Operator

if TYPE_CHECKING:  # solo para anotar
    from sgm.ir.builder import Builder


# Cuántas veces se usó la forma legado (el constructor rechazó los datos), por tipo de operador.
# Es el contador que mide cuánto queda de la forma anterior (B-5 paso 3, B-6). No vive en el plan:
# añadir un campo a `Plan` cambiaría la serialización de todos los planes.
_LEGADO: Counter[str] = Counter()


def contador_legado() -> dict[str, int]:
    """Copia del contador de formas legado por tipo de operador."""
    return dict(_LEGADO)


def reiniciar_contador_legado() -> None:
    _LEGADO.clear()


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
        _LEGADO[kind] += 1
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
        _LEGADO[kind] += 1
    return builder.op(kind, params, ev, status=status, notes=notes)


__all__ = ["Cadena", "contador_legado", "op_validado", "paso", "reiniciar_contador_legado"]
