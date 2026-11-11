"""Salud de Talend Studio: estado nombrado, si deja escribir y si hay diálogos abiertos.

Se pregunta por `talend_bridge_ping` y por `talend_studio_ui_dialogs`, con un corte de diez segundos
cada una. Un diálogo modal abierto en Studio bloquea la compilación aunque el puente responda: es
justo el caso que hay que detectar antes de lanzar un lote de Jobs, no después de esperar dos
minutos a que falle.

El resultado lleva un `estado` con los mismos literales que `classifyStudioState` de `talend-mcp`
(`READY`, `NOT_RUNNING`, `WAITING_LOGIN`, `BRIDGE_DEAD`, `MODAL_BLOCKING`, `BUSY`), para que el
llamador decida sin leer el motivo. Cuando el estado es `BRIDGE_DEAD` y el llamador pasa
`recuperar=True`, se intenta una sola recuperación con `talend_studio_ensure_ready`; en cualquier
otro estado no se toca Studio.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from sgm.backend_talend.base import BackendNoDisponible
from sgm.backend_talend.comun import TOOL_ENSURE, detalle


class Llamable(Protocol):
    """Backend que puede llamar a una herramienta con un tiempo máximo."""

    def llamar(self, tool: str, entrada: dict, tiempo_max: float | None = None) -> dict: ...

_TOOL_PING = "talend_bridge_ping"
_TOOL_DIALOGOS = "talend_studio_ui_dialogs"
_DIALOGO = "revisa si hay un diálogo abierto en Talend Studio"

ESTADOS = ("READY", "NOT_RUNNING", "WAITING_LOGIN", "BRIDGE_DEAD", "MODAL_BLOCKING", "BUSY")
# Código de error del puente → estado. Un código desconocido deja el bridge como caído.
_ESTADOS_DEL_ERROR = {
    "STUDIO_NOT_RUNNING": "NOT_RUNNING",
    "STUDIO_WAITING_LOGIN": "WAITING_LOGIN",
    "STUDIO_BRIDGE_DOWN": "BRIDGE_DEAD",
    "BRIDGE_UNAVAILABLE": "BRIDGE_DEAD",
    "STUDIO_DIALOG_OPEN": "MODAL_BLOCKING",
    "STUDIO_BUSY": "BUSY",
}


@dataclass(frozen=True)
class Salud:
    """Resultado de la comprobación: si está disponible, por qué no y en qué estado está."""

    ok: bool
    motivo: str
    estado: str = ""


def _sin_salud(estado: str, motivo: str) -> Salud:
    """Salud negativa cuyo motivo empieza por el estado, para que se pueda buscar."""
    return Salud(False, f"{estado}: {motivo}", estado)


def _codigo(error: object) -> str:
    """Código del error de la respuesta, sea un mapa o un texto."""
    if isinstance(error, dict):
        return str(error.get("code") or error.get("message") or "sin código")
    return str(error)


def _escribe(ping: dict) -> bool:
    """El puente deja escribir: `mode` es `readWrite` (es lo que devuelve el ping real)."""
    if ping.get("readWrite") is True:
        return True
    return str(ping.get("mode") or "").strip().lower() == "readwrite"


def _titulos(dialogos: dict) -> str:
    """Títulos de los diálogos que bloquean, para nombrarlos en el motivo."""
    bloquean = dialogos.get("blocking") or dialogos.get("dialogs") or []
    titulos = [str(d.get("title") or "sin título") for d in bloquean if isinstance(d, dict)]
    return ", ".join(titulos) if titulos else "sin título"


def _sonda(backend: Llamable, tiempo_max: float) -> Salud:
    """Mide el estado de Studio con el ping y la lista de diálogos."""
    try:
        # La CLI entrega `data` plano; el MCP lo envuelve en su sobre `{ok, data}`.
        ping = detalle(backend.llamar(_TOOL_PING, {}, tiempo_max), ("mode", "readWrite", "error"))
    except BackendNoDisponible as error:
        return _sin_salud("BRIDGE_DEAD", f"Studio no respondió: {error}. {_DIALOGO}")
    if ping.get("error"):
        codigo = _codigo(ping["error"])
        estado = _ESTADOS_DEL_ERROR.get(codigo, "BRIDGE_DEAD")
        return _sin_salud(estado, f"Studio devolvió un error ({codigo}). {_DIALOGO}")
    if not _escribe(ping):
        return _sin_salud(
            "WAITING_LOGIN",
            f"Studio responde pero no da permiso de escritura (mode={ping.get('mode')!r}). "
            f"{_DIALOGO}",
        )
    try:
        dialogos = detalle(
            backend.llamar(_TOOL_DIALOGOS, {}, tiempo_max), ("blocked", "dialogs", "blocking")
        )
    except BackendNoDisponible as error:
        return _sin_salud(
            "BRIDGE_DEAD", f"no se pudo comprobar si hay diálogos abiertos: {error}. {_DIALOGO}"
        )
    if dialogos.get("blocked"):
        return _sin_salud("MODAL_BLOCKING", f"{_DIALOGO}: {_titulos(dialogos)}")
    return Salud(True, "", "READY")


def _recuperar(backend: Llamable, tiempo_max: float) -> Salud | None:
    """Pide a Studio que se recupere; `None` si no lo logró y sigue valiendo la sonda original."""
    try:
        respuesta = detalle(
            backend.llamar(TOOL_ENSURE, {"restart": True}, tiempo_max),
            ("state", "recovered", "reason"),
        )
    except BackendNoDisponible:
        return None
    estado = str(respuesta.get("state") or "")
    if estado != "READY":
        return None
    # `ensure_ready` ya midió el estado después de recuperar: se cree su READY, sin otra ronda.
    return Salud(True, "", "READY")


def comprobar_salud(backend: Llamable, tiempo_max: float = 10.0, recuperar: bool = False) -> Salud:
    """`Salud(True, "", estado)` si Studio responde, escribe y no tiene diálogos; si no, el motivo.

    Con `recuperar=True` y el bridge caído se intenta una sola recuperación; con un diálogo modal,
    un login pendiente o Studio ocupado no se reintenta nada.
    """
    salud = _sonda(backend, tiempo_max)
    if salud.ok or not recuperar or salud.estado != "BRIDGE_DEAD":
        return salud
    return _recuperar(backend, tiempo_max) or salud


__all__ = ["ESTADOS", "Llamable", "Salud", "comprobar_salud"]
