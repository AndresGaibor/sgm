"""Backend de Talend: escribir Jobs, compilarlos en lote y verificarlos.

`ArchivosBackend` no necesita nada; `TalendCliBackend` usa la CLI de `talend-mcp` y `McpBackend` su
servidor MCP. Ningún módulo del núcleo los importa: solo este paquete.
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
from sgm.backend_talend.mcp import URL_POR_OMISION, McpBackend
from sgm.backend_talend.talend_cli import TalendCliBackend

__all__ = [
    "NIVELES_VEREDICTO",
    "URL_POR_OMISION",
    "ArchivosBackend",
    "BackendNoDisponible",
    "BackendTalend",
    "McpBackend",
    "ResultadoLote",
    "TalendCliBackend",
    "Veredicto",
]
