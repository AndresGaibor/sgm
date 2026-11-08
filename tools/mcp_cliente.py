"""Cliente MCP para los validadores de `tools/`.

El protocolo vive en `sgm.backend_talend.mcp`: aquí solo se adapta el error a `ErrorValidacion`
(lo que esperan los validadores) y se conserva la descarga de los poms públicos que la exportación
de un Job pide cuando la caché de Studio está incompleta.
"""

from __future__ import annotations

import os
import re
import urllib.error
import urllib.request
from pathlib import Path

from sgm.backend_talend.base import BackendNoDisponible
from sgm.backend_talend.mcp import URL_POR_OMISION, McpBackend

CENTRAL = "https://repo1.maven.org/maven2"
URL_MCP = os.environ.get("TALEND_MCP_URL", URL_POR_OMISION)


class ErrorValidacion(RuntimeError):
    """Fallo explícito del protocolo, con el paso que lo produjo."""


class MCP(McpBackend):
    """Backend MCP con los tiempos largos y el error que esperan los validadores."""

    def __init__(self, url: str = URL_MCP, timeout: int = 900) -> None:
        super().__init__(url=url, tiempo_max=float(timeout))

    def llamar(self, tool: str, argumentos: dict | None = None, tiempo_max: float | None = None):
        try:
            return super().llamar(tool, argumentos or {}, tiempo_max)
        except BackendNoDisponible as error:
            raise ErrorValidacion(str(error)) from error


def descargar_poms(mensaje: str, m2: Path | None) -> list[str]:
    """Descarga de Maven Central las coordenadas `g:a:v` que el mensaje diga que faltan."""
    if m2 is None:
        return []
    descargados: list[str] = []
    for grupo, artefacto, version in set(re.findall(r"([\w.-]+):([\w.-]+):([\w.]+)", mensaje)):
        destino = m2 / Path(*grupo.split(".")) / artefacto / version / f"{artefacto}-{version}.pom"
        if destino.exists():
            continue
        url = f"{CENTRAL}/{grupo.replace('.', '/')}/{artefacto}/{version}/{artefacto}-{version}.pom"
        try:
            with urllib.request.urlopen(url, timeout=60) as respuesta:
                destino.parent.mkdir(parents=True, exist_ok=True)
                destino.write_bytes(respuesta.read())
        except urllib.error.URLError:
            continue
        descargados.append(f"{grupo}:{artefacto}:{version}")
    return descargados
