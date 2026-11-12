"""Errores del intérprete de referencia."""

from __future__ import annotations


class NoSoportadoEnInterprete(RuntimeError):
    """El plan usa algo que el intérprete no sabe ejecutar; se dice qué, no se salta."""

    def __init__(self, kind: str, detalle: str = "") -> None:
        self.kind = kind
        self.detalle = detalle
        super().__init__(f"{kind}: {detalle}" if detalle else kind)
