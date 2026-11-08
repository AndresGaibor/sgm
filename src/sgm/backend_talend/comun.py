"""Mapeo común de las respuestas de Talend, vengan de la CLI o del MCP.

La CLI devuelve `{"ok": true, "data": <resultado>}`; el MCP devuelve el mismo resultado en
`structuredContent`. El puente de Studio, además, anida el detalle en `data.result`. Los dos
backends comparten este módulo para que una forma nueva de respuesta se arregle una sola vez.
"""

from __future__ import annotations

import json
import re
from typing import Any

from sgm.backend_talend.base import ResultadoLote, Veredicto

# Herramientas de `talend-mcp` que usan los backends.
TOOL_LOTE = "talend_job_build_batch"
TOOL_VERIFICAR = "talend_job_verify"
TOOL_REFRESCO = "talend_bridge_refresh_workspace"
TOOL_PING = "talend_bridge_ping"
PARALELISMO = 4

# Un nombre de variable de contexto que huela a credencial no se manda: ni la CLI ni el MCP
# deben verla.
_SECRETO = re.compile(r"(pass|pwd|secret|token|clave)", re.IGNORECASE)


def sin_secretos(contexto: dict[str, str]) -> None:
    """Rechaza un contexto con credenciales antes de armar la petición."""
    culpables = sorted(nombre for nombre in contexto if _SECRETO.search(nombre))
    if culpables:
        raise ValueError(f"el contexto lleva secretos y no se pueden pasar: {culpables}")


def _buscar(datos: Any, claves: tuple[str, ...]) -> dict:
    """Primer diccionario que trae alguna de `claves`, bajando por `result` y `data`.

    El puente anida el detalle en `data.result`; la CLI a veces lo entrega plano. Se recorren las
    dos ramas con una cola y se corta en el primer nivel que tenga la clave buscada.
    """
    cola = [datos]
    vistos: set[int] = set()
    while cola:
        actual = cola.pop(0)
        if not isinstance(actual, dict) or id(actual) in vistos:
            continue
        vistos.add(id(actual))
        if any(clave in actual for clave in claves):
            return actual
        for clave in ("result", "data"):
            siguiente = actual.get(clave)
            if isinstance(siguiente, dict):
                cola.append(siguiente)
    return datos if isinstance(datos, dict) else {}


def _compilo(estado: Any) -> bool:
    """Si un Job del lote compiló, según el mapa de `result.jobs`."""
    return bool(estado.get("ok")) if isinstance(estado, dict) else False


def _motivo(estado: Any) -> str:
    """Motivo por el que un Job del lote no compiló."""
    if isinstance(estado, dict):
        error = estado.get("error") or estado.get("motivo")
        if isinstance(error, dict):
            return str(error.get("message") or error.get("code") or "sin motivo")
        return str(error or "sin motivo")
    return str(estado or "sin motivo")


def _hallazgos(bruto: Any) -> tuple[str, ...]:
    """Hallazgos del veredicto como líneas: `findings` es un mapa de errores y avisos."""
    if isinstance(bruto, dict):
        errores = [f"[ERROR] {_texto(texto)}" for texto in bruto.get("errors") or []]
        avisos = [f"[WARN] {_texto(texto)}" for texto in bruto.get("warnings") or []]
        return tuple(errores + avisos)
    if isinstance(bruto, list):
        return tuple(_texto(item) for item in bruto)
    return ()


def _texto(item: Any) -> str:
    if isinstance(item, dict):
        return str(item.get("message") or item.get("code") or json.dumps(item, ensure_ascii=False))
    return str(item)


def resultado_lote(datos: Any, nombres: list[str]) -> ResultadoLote:
    """Traduce la respuesta de `talend_job_build_batch` a `ResultadoLote`.

    Acepta el mapa por nombre (la forma real), la lista de estados y la forma resumida
    `compilan`/`noCompilan`. Los Jobs que compilan conservan el orden pedido.
    """
    contenedor = _buscar(datos, ("jobs", "compilan", "noCompilan"))
    por_job = contenedor.get("jobs")
    estados: dict[str, Any] = {}
    if isinstance(por_job, dict):
        estados = dict(por_job)
    elif isinstance(por_job, list):
        estados = {
            str(estado.get("name") or estado.get("job") or f"job_{posicion}"): estado
            for posicion, estado in enumerate(por_job)
            if isinstance(estado, dict)
        }

    fallos = {
        str(nombre): _motivo(estado) for nombre, estado in estados.items() if not _compilo(estado)
    }
    for item in contenedor.get("noCompilan") or []:
        if isinstance(item, dict):
            fallos[str(item.get("job") or item.get("name") or "sin nombre")] = _motivo(item)
        else:
            fallos[str(item)] = "sin motivo"

    if estados:
        compilan = [nombre for nombre, estado in estados.items() if _compilo(estado)]
    else:
        compilan = [str(nombre) for nombre in contenedor.get("compilan") or []]
    orden = {nombre: posicion for posicion, nombre in enumerate(nombres)}
    compilan.sort(key=lambda nombre: orden.get(nombre, len(orden)))
    return ResultadoLote(compilan=tuple(compilan), no_compilan=fallos)


def veredicto(datos: Any) -> Veredicto:
    """Traduce la respuesta de `talend_job_verify` a `Veredicto`."""
    contenedor = _buscar(datos, ("verdict", "nivel", "findings"))
    nivel = str(contenedor.get("verdict") or contenedor.get("nivel") or "error")
    return Veredicto(nivel, _hallazgos(contenedor.get("findings")))


__all__ = [
    "PARALELISMO",
    "TOOL_LOTE",
    "TOOL_PING",
    "TOOL_REFRESCO",
    "TOOL_VERIFICAR",
    "resultado_lote",
    "sin_secretos",
    "veredicto",
]
