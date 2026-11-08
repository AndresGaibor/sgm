"""Salud de Talend Studio: si el puente responde, si deja escribir y si no hay diálogos abiertos.

Se pregunta por `talend_bridge_ping` y por `talend_studio_ui_dialogs`, con un corte de diez segundos
cada una. Un diálogo modal abierto en Studio bloquea la compilación aunque el puente responda: es
justo el caso que hay que detectar antes de lanzar un lote de Jobs, no después de esperar dos
minutos a que falle.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from sgm.backend_talend.base import BackendNoDisponible
from sgm.backend_talend.comun import detalle


class Llamable(Protocol):
    """Backend que puede llamar a una herramienta con un tiempo máximo."""

    def llamar(self, tool: str, entrada: dict, tiempo_max: float | None = None) -> dict: ...

_TOOL_PING = "talend_bridge_ping"
_TOOL_DIALOGOS = "talend_studio_ui_dialogs"
_DIALOGO = "revisa si hay un diálogo abierto en Talend Studio"


@dataclass(frozen=True)
class Salud:
    """Resultado de la comprobación: si está disponible y, si no, por qué."""

    ok: bool
    motivo: str


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


def comprobar_salud(backend: Llamable, tiempo_max: float = 10.0) -> Salud:
    """`Salud(True, "")` si Studio responde, escribe y no tiene diálogos; si no, el motivo."""
    try:
        # La CLI entrega `data` plano; el MCP lo envuelve en su sobre `{ok, data}`.
        ping = detalle(backend.llamar(_TOOL_PING, {}, tiempo_max), ("mode", "readWrite", "error"))
    except BackendNoDisponible as error:
        return Salud(False, f"Studio no respondió: {error}. {_DIALOGO}")
    if ping.get("error"):
        return Salud(False, f"Studio devolvió un error ({_codigo(ping['error'])}). {_DIALOGO}")
    if not _escribe(ping):
        return Salud(
            False,
            f"Studio responde pero no da permiso de escritura (mode={ping.get('mode')!r}). "
            f"{_DIALOGO}",
        )
    try:
        dialogos = detalle(
            backend.llamar(_TOOL_DIALOGOS, {}, tiempo_max), ("blocked", "dialogs", "blocking")
        )
    except BackendNoDisponible as error:
        return Salud(False, f"no se pudo comprobar si hay diálogos abiertos: {error}. {_DIALOGO}")
    if dialogos.get("blocked"):
        return Salud(False, f"{_DIALOGO}: {_titulos(dialogos)}")
    return Salud(True, "")


__all__ = ["Llamable", "Salud", "comprobar_salud"]
