"""Pasos del plan lógico con su forma validada (B-5).

`paso` añade un paso con los parámetros del constructor de `ir/operadores.py`; si el constructor
rechaza los datos, usa la forma `legado`. Lo usan los lowering de SQL, del DATA step y de los PROC.
"""

from __future__ import annotations

from typing import Any, Protocol

from sgm.ir.models import Operator


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


__all__ = ["Cadena", "paso"]
