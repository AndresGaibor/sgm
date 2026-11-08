"""Backend de Talend que habla con el servidor MCP de `talend-mcp`.

El servidor usa HTTP JSON-RPC en `http://127.0.0.1:3927/mcp` y responde JSON o SSE. El transporte
se inyecta para probar el protocolo sin arrancar `bun` ni Studio. La petición es la misma que usa
la CLI (`tools/call`), pero aquí no hay proceso intermedio: el servidor ya conoce el proyecto.

Un fallo nunca sale como traza: o es `BackendNoDisponible` con el motivo, o es `ValueError` cuando
lo pedido está prohibido (un secreto en el contexto).
"""

from __future__ import annotations

import http.client
import json
import os
import threading
import urllib.error
import urllib.request
from collections.abc import Callable

from sgm.backend_talend.archivos import ArchivosBackend
from sgm.backend_talend.base import BackendNoDisponible, ResultadoLote, Veredicto
from sgm.backend_talend.comun import (
    PARALELISMO,
    TOOL_LOTE,
    TOOL_REFRESCO,
    TOOL_VERIFICAR,
    resultado_lote,
    sin_secretos,
    veredicto,
)

URL_POR_OMISION = "http://127.0.0.1:3927/mcp"
# Recibe la petición JSON-RPC y el tiempo máximo; devuelve la respuesta JSON-RPC ya decodificada.
Transporte = Callable[[dict, float], dict]

_PROTOCOLO = "2024-11-05"


class SesionRequerida(BackendNoDisponible):
    """El servidor pide `initialize` antes de atender `tools/call`."""


def _json_o_sse(cuerpo: str, tipo: str | None) -> dict:
    """Decodifica una respuesta JSON o un flujo SSE del MCP.

    El SDK responde `application/json`, pero un cliente que acepta `text/event-stream` puede
    recibir eventos `data: {...}`. El cliente anterior solo entendía JSON y fallaba con el segundo.
    """
    if not cuerpo.strip():
        return {}
    if (tipo and "text/event-stream" in tipo) or cuerpo.lstrip().startswith(("event:", "data:")):
        eventos: list[dict] = []
        for linea in cuerpo.splitlines():
            if not linea.startswith("data:"):
                continue
            try:
                cargado = json.loads(linea[5:].strip())
            except ValueError:
                continue
            if isinstance(cargado, dict):
                eventos.append(cargado)
        if not eventos:
            raise BackendNoDisponible("respuesta SSE del MCP sin datos JSON")
        return eventos[-1]
    try:
        cargado = json.loads(cuerpo)
    except ValueError as error:
        raise BackendNoDisponible(
            f"respuesta no válida del MCP: {cuerpo[:200]!r}"
        ) from error
    if isinstance(cargado, list):
        objetos = [item for item in cargado if isinstance(item, dict)]
        if not objetos:
            raise BackendNoDisponible("respuesta JSON-RPC del MCP sin objetos")
        return objetos[-1]
    if not isinstance(cargado, dict):
        raise BackendNoDisponible("respuesta JSON-RPC del MCP que no es un objeto")
    return cargado


class TransporteHttp:
    """Transporte real por `urllib`, sin dependencias ni procesos externos."""

    def __init__(self, url: str = URL_POR_OMISION, token: str | None = None) -> None:
        self.url = url
        self.token = token or os.environ.get("TALEND_MCP_TOKEN")
        self.sesion: str | None = None

    def __call__(self, peticion: dict, tiempo_max: float) -> dict:
        cabeceras = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if self.token:
            cabeceras["Authorization"] = f"Bearer {self.token}"
        if self.sesion:
            cabeceras["Mcp-Session-Id"] = self.sesion
        solicitud = urllib.request.Request(
            self.url,
            data=json.dumps(peticion, ensure_ascii=False).encode("utf-8"),
            headers=cabeceras,
            method="POST",
        )
        try:
            with urllib.request.urlopen(solicitud, timeout=tiempo_max) as respuesta:
                cuerpo = respuesta.read().decode("utf-8", errors="replace")
                tipo = respuesta.headers.get_content_type()
                sesion = respuesta.headers.get("Mcp-Session-Id")
        except urllib.error.HTTPError as error:
            detalle = error.read().decode("utf-8", errors="replace")[:500]
            mensaje = f"el MCP respondió {error.code}: {detalle}"
            if error.code in (400, 406) and (
                "session" in detalle.lower() or "initialize" in detalle.lower()
            ):
                raise SesionRequerida(mensaje) from error
            raise BackendNoDisponible(mensaje) from error
        except http.client.HTTPException as error:
            raise BackendNoDisponible(
                f"respuesta incompleta del MCP en {self.url}: {error}"
            ) from error
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            raise BackendNoDisponible(
                f"no se pudo contactar al MCP en {self.url}: {error}"
            ) from error
        if sesion:
            self.sesion = sesion
        return _json_o_sse(cuerpo, tipo)


class McpBackend(ArchivosBackend):
    """Escribe como el backend de archivos y compila o verifica por MCP."""

    def __init__(
        self,
        url: str | None = None,
        transporte: Transporte | None = None,
        tiempo_max: float = 120.0,
        fecha: str | None = None,
        token: str | None = None,
    ) -> None:
        super().__init__(fecha=fecha)
        self.url = url or os.environ.get("TALEND_MCP_URL") or URL_POR_OMISION
        self.tiempo_max = tiempo_max
        self.transporte = transporte or TransporteHttp(self.url, token=token)
        self.protocolo: str | None = None
        self._negociado = False
        self._candado = threading.Lock()
        self._siguiente_id = 0

    def _peticion(self, metodo: str, parametros: dict, tiempo_max: float) -> dict:
        self._siguiente_id += 1
        return self.transporte(
            {
                "jsonrpc": "2.0",
                "id": self._siguiente_id,
                "method": metodo,
                "params": parametros,
            },
            tiempo_max,
        )

    def negociar(self, tiempo_max: float | None = None) -> None:
        """Hace el handshake MCP y guarda el protocolo acordado.

        El servidor actual es stateless y acepta `tools/call` directo; el handshake se usa cuando
        un servidor con sesión responde que hace falta.
        """
        limite = self.tiempo_max if tiempo_max is None else tiempo_max
        with self._candado:
            if self._negociado:
                return
            respuesta = self._peticion(
                "initialize",
                {
                    "protocolVersion": _PROTOCOLO,
                    "capabilities": {},
                    "clientInfo": {"name": "sgm", "version": "0.2.0"},
                },
                limite,
            )
            resultado = respuesta.get("result")
            if isinstance(resultado, dict):
                self.protocolo = str(resultado.get("protocolVersion") or _PROTOCOLO)
            self.transporte(
                {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}, limite
            )
            self._negociado = True

    def _contenido(self, resultado: dict) -> dict:
        """Datos útiles de un resultado MCP: `structuredContent` o el texto JSON."""
        estructurado = resultado.get("structuredContent")
        if isinstance(estructurado, dict):
            return estructurado
        texto = " ".join(
            str(contenido.get("text") or "")
            for contenido in resultado.get("content") or []
            if isinstance(contenido, dict)
        )
        try:
            cargado = json.loads(texto)
        except ValueError:
            return {"text": texto}
        return cargado if isinstance(cargado, dict) else {"data": cargado}

    def llamar(self, tool: str, entrada: dict, tiempo_max: float | None = None) -> dict:
        """Llama a una herramienta MCP y devuelve su contenido, o lanza `BackendNoDisponible`."""
        limite = self.tiempo_max if tiempo_max is None else tiempo_max
        self._siguiente_id += 1
        peticion = {
            "jsonrpc": "2.0",
            "id": self._siguiente_id,
            "method": "tools/call",
            "params": {"name": tool, "arguments": entrada},
        }
        try:
            respuesta = self.transporte(peticion, limite)
        except SesionRequerida:
            self.negociar(limite)
            self._siguiente_id += 1
            peticion["id"] = self._siguiente_id
            respuesta = self.transporte(peticion, limite)

        if respuesta.get("error"):
            error = respuesta["error"]
            motivo = error.get("message") if isinstance(error, dict) else str(error)
            raise BackendNoDisponible(f"el MCP falló en {tool}: {motivo}")
        resultado = respuesta.get("result")
        if not isinstance(resultado, dict):
            raise BackendNoDisponible(f"el MCP no devolvió resultado para {tool}")
        datos = self._contenido(resultado)
        # Un veredicto negativo (`ok: false` con `data`) es un resultado, no un fallo de transporte.
        if resultado.get("isError") and not isinstance(datos.get("data"), dict):
            raise BackendNoDisponible(
                f"el MCP falló en {tool}: {json.dumps(datos, ensure_ascii=False)[:800]}"
            )
        return datos

    def refrescar(self) -> None:
        """Pide a Studio que relea el workspace."""
        self.llamar(TOOL_REFRESCO, {})

    def compilar_lote(self, nombres: list[str]) -> ResultadoLote:
        """Compila los Jobs en una llamada."""
        datos = self.llamar(TOOL_LOTE, {"jobs": list(nombres), "parallelism": PARALELISMO})
        return resultado_lote(datos, nombres)

    def verificar(self, nombre: str, contexto: dict[str, str]) -> Veredicto:
        """Compila el Job y devuelve su veredicto, sin ejecutarlo."""
        sin_secretos(contexto)
        datos = self.llamar(TOOL_VERIFICAR, {"job": nombre, "run": False})
        return veredicto(datos)


__all__ = [
    "URL_POR_OMISION",
    "McpBackend",
    "SesionRequerida",
    "Transporte",
    "TransporteHttp",
]
