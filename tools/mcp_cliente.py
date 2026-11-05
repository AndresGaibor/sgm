"""Cliente JSON-RPC del MCP de `talend-mcp` para los validadores de `tools/`.

Sin dependencias: usa `urllib` contra `http://127.0.0.1:3927/mcp`. Incluye la descarga de los
poms públicos de Maven que la exportación de un Job pide cuando la caché de Studio está incompleta.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path

CENTRAL = "https://repo1.maven.org/maven2"
URL_MCP = os.environ.get("TALEND_MCP_URL", "http://127.0.0.1:3927/mcp")


class ErrorValidacion(RuntimeError):
    """Fallo explícito del protocolo, con el paso que lo produjo."""


class MCP:
    """Cliente JSON-RPC mínimo del servidor talend-mcp."""

    def __init__(self, url: str = URL_MCP, timeout: int = 900) -> None:
        self.url = url
        self.timeout = timeout

    def llamar(self, tool: str, argumentos: dict | None = None):
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": tool, "arguments": argumentos or {}},
        }
        peticion = urllib.request.Request(
            self.url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )
        try:
            with urllib.request.urlopen(peticion, timeout=self.timeout) as respuesta:
                cuerpo = json.loads(respuesta.read().decode("utf-8"))
        except urllib.error.URLError as error:
            raise ErrorValidacion(
                f"{tool}: no se pudo contactar al MCP en {self.url}: {error}"
            ) from error
        if "error" in cuerpo:
            raise ErrorValidacion(f"{tool}: {cuerpo['error']}")
        resultado = cuerpo.get("result", {})
        datos = resultado.get("structuredContent")
        if datos is None:
            texto = " ".join(c.get("text", "") for c in resultado.get("content", []))
            try:
                datos = json.loads(texto)
            except json.JSONDecodeError:
                datos = {"text": texto}
        if resultado.get("isError"):
            raise ErrorValidacion(f"{tool}: {json.dumps(datos, ensure_ascii=False)[:800]}")
        return datos


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
