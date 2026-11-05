"""Backend de Talend: escribir Jobs, compilarlos en lote y verificarlos.

`ArchivosBackend` no necesita nada; `TalendCliBackend` usa la CLI de `talend-mcp`. Ningún módulo del
núcleo importa la CLI: solo este paquete.
"""

from __future__ import annotations

from sgm.backend_talend.archivos import ArchivosBackend
from sgm.backend_talend.base import (
    NIVELES_VEREDICTO,
    BackendNoDisponible,
    BackendTalend,
    ResultadoLote,
    Veredicto,
)

__all__ = [
    "NIVELES_VEREDICTO",
    "ArchivosBackend",
    "BackendNoDisponible",
    "BackendTalend",
    "ResultadoLote",
    "Veredicto",
]
