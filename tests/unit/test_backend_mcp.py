"""Backend de Talend por MCP, con un transporte inyectado.

No se arranca `bun` ni Studio: el transporte falso devuelve la respuesta MCP y anota la petición.
Las formas de respuesta salen del servidor real y del puente de Studio, no de suposiciones.
"""

from __future__ import annotations

import json

import pytest

from sgm.backend_talend.base import BackendNoDisponible, ResultadoLote, Veredicto
from sgm.backend_talend.mcp import McpBackend, SesionRequerida, _json_o_sse


def _resultado(datos: dict, is_error: bool = False) -> dict:
    return {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "content": [{"type": "text", "text": json.dumps(datos, ensure_ascii=False)}],
            "structuredContent": datos,
            "isError": is_error,
        },
    }


class TransporteFalso:
    """Transporte de prueba: guarda cada petición y devuelve la respuesta preparada."""

    def __init__(self, respuesta: dict) -> None:
        self.respuesta = respuesta
        self.llamadas: list[tuple[dict, float]] = []

    def __call__(self, peticion: dict, tiempo_max: float) -> dict:
        self.llamadas.append((peticion, tiempo_max))
        return self.respuesta


class TransporteConSesion:
    """Simula un servidor que exige `initialize` antes de atender `tools/call`."""

    def __init__(self, resultado: dict) -> None:
        self.resultado = resultado
        self.llamadas: list[dict] = []
        self._inicializado = False

    def __call__(self, peticion: dict, tiempo_max: float) -> dict:
        self.llamadas.append(peticion)
        metodo = peticion.get("method")
        if metodo == "initialize":
            return {"jsonrpc": "2.0", "id": peticion["id"], "result": {"protocolVersion": "2024-11-05"}}
        if metodo == "notifications/initialized":
            self._inicializado = True
            return {}
        if not self._inicializado:
            raise SesionRequerida("el MCP respondió 400: session not initialized")
        return _resultado(self.resultado)


def _backend(transporte, tiempo_max: float = 120.0) -> McpBackend:
    return McpBackend(transporte=transporte, tiempo_max=tiempo_max)


def test_compilar_lote_lee_data_result_jobs():
    """La forma real del MCP anida el detalle en `data.result.jobs`."""
    datos = {
        "ok": True,
        "source": "studio-bridge",
        "endpoint": "/automation/job/build-batch",
        "data": {
            "ok": True,
            "result": {
                "total": 3,
                "correctos": 2,
                "jobs": {
                    "a": {"ok": True},
                    "b": {"ok": False, "error": "no compila"},
                    "c": {"ok": True},
                },
            },
        },
    }
    transporte = TransporteFalso(_resultado(datos))

    resultado = _backend(transporte).compilar_lote(["c", "b", "a"])

    assert resultado == ResultadoLote(compilan=("c", "a"), no_compilan={"b": "no compila"})


def test_compilar_lote_acepta_la_lista_de_estados():
    datos = {"ok": True, "data": {"jobs": [{"name": "a", "ok": True}, {"name": "b", "ok": False}]}}

    resultado = _backend(TransporteFalso(_resultado(datos))).compilar_lote(["a", "b"])

    assert resultado.compilan == ("a",)
    assert resultado.no_compilan == {"b": "sin motivo"}


def test_verificar_lee_el_veredicto_anidado():
    datos = {
        "ok": True,
        "data": {
            "job": "a",
            "compiles": True,
            "verdict": "ok_con_avisos",
            "findings": {"errors": [], "warnings": ["falta una etiqueta"]},
        },
    }
    transporte = TransporteFalso(_resultado(datos))

    veredicto = _backend(transporte).verificar("a", {"ruta_x": "/tmp/x"})

    assert veredicto == Veredicto("ok_con_avisos", ("[WARN] falta una etiqueta",))
    peticion, _ = transporte.llamadas[0]
    assert peticion["params"] == {"name": "talend_job_verify", "arguments": {"job": "a", "run": False}}


def test_un_veredicto_negativo_no_es_un_fallo_de_transporte():
    """`ok: false` con `data` es un Job que no compila, no un error de protocolo."""
    datos = {"ok": False, "data": {"job": "a", "compiles": False, "verdict": "error", "findings": {}}}

    veredicto = _backend(TransporteFalso(_resultado(datos, is_error=True))).verificar("a", {})

    assert veredicto == Veredicto("error", ())


def test_un_error_sin_datos_lanza_backend_no_disponible():
    datos = {"ok": False, "error": {"code": "STUDIO_DIALOG_OPEN", "message": "Studio bloqueado"}}

    with pytest.raises(BackendNoDisponible, match="Studio bloqueado"):
        _backend(TransporteFalso(_resultado(datos, is_error=True))).verificar("a", {})


def test_contexto_con_password_se_rechaza_antes_de_llamar():
    transporte = TransporteFalso(_resultado({}))

    with pytest.raises(ValueError, match="secreto"):
        _backend(transporte).verificar("a", {"DB_PASSWORD": "x"})

    assert transporte.llamadas == []


def test_negocia_cuando_el_servidor_lo_pide():
    datos = {"ok": True, "data": {"result": {"jobs": {"a": {"ok": True}}}}}
    transporte = TransporteConSesion(datos)
    backend = _backend(transporte)

    resultado = backend.compilar_lote(["a"])

    assert resultado.compilan == ("a",)
    metodos = [peticion.get("method") for peticion in transporte.llamadas]
    assert metodos == ["tools/call", "initialize", "notifications/initialized", "tools/call"]
    assert backend.protocolo == "2024-11-05"


def test_transporte_http_decodifica_sse():
    evento = {"jsonrpc": "2.0", "id": 1, "result": {"structuredContent": {"ok": True}}}
    cuerpo = f"event: message\ndata: {json.dumps(evento)}\n\n"

    assert _json_o_sse(cuerpo, "text/event-stream") == evento


def test_transporte_http_decodifica_json():
    evento = {"jsonrpc": "2.0", "id": 1, "result": {"structuredContent": {"ok": True}}}

    assert _json_o_sse(json.dumps(evento), "application/json") == evento


def test_tiempo_maximo_se_propaga():
    transporte = TransporteFalso(_resultado({"ok": True}))

    _backend(transporte, tiempo_max=7.5).compilar_lote(["a"])

    assert transporte.llamadas[0][1] == 7.5
