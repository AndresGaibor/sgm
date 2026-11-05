"""Excepción de las construcciones de SAS que el oráculo no traduce con fidelidad.

Vive aparte para que los módulos de traducción la usen sin importar `traduccion_sql` (que los usa a
ellos). `traduccion_sql` la vuelve a exportar.
"""

from __future__ import annotations


class NoSoportado(Exception):
    """Construcción de SAS que el oráculo no traduce con fidelidad."""

    def __init__(self, construccion: str) -> None:
        self.construccion = construccion
        super().__init__(f"Construcción SAS no soportada por el oráculo: {construccion}")
