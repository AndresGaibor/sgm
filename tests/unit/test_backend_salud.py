"""Salud de Talend Studio: si responde, si deja escribir y si hay diálogos que bloquean.

Las respuestas de prueba son las reales del puente, guardadas en `tests/fixtures/talend_cli/`: el
ping devuelve `mode: "readWrite"` (no un booleano) y los diálogos vienen en `blocking`.
"""

from __future__ import annotations

import json
from pathlib import Path

from sgm.backend_talend import BackendNoDisponible
from sgm.backend_talend.salud import comprobar_salud
from sgm.backend_talend.talend_cli import TalendCliBackend

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "talend_cli"


def _respuesta(nombre: str) -> str:
    return (FIXTURES / nombre).read_text(encoding="utf-8").strip()


class EjecutorPorHerramienta:
    """Ejecutor de prueba: responde según la herramienta que venga en la línea de comandos."""

    def __init__(self, respuestas: dict[str, str]) -> None:
        self.respuestas = respuestas
        self.llamadas: list[tuple[list[str], float]] = []

    def __call__(self, comando: list[str], tiempo_max: float) -> tuple[int, str]:
        self.llamadas.append((list(comando), tiempo_max))
        herramienta = comando[comando.index("call") + 1]
        return 0, self.respuestas.get(herramienta, '{"ok": true, "data": {}}')


class EjecutorQueFalla:
    def __init__(self, error: Exception) -> None:
        self.error = error

    def __call__(self, comando: list[str], tiempo_max: float) -> tuple[int, str]:
        raise self.error


def _backend(ejecutor) -> TalendCliBackend:
    return TalendCliBackend(Path("."), Path("PRJ"), ejecutor=ejecutor, tiempo_max=120.0)


def _libre() -> EjecutorPorHerramienta:
    return EjecutorPorHerramienta(
        {
            "talend_bridge_ping": _respuesta("ping.json"),
            "talend_studio_ui_dialogs": '{"ok": true, "data": {"blocked": false, "dialogs": []}}',
        }
    )


def test_salud_ok_con_la_respuesta_real_del_puente():
    ejecutor = _libre()

    salud = comprobar_salud(_backend(ejecutor))

    assert salud.ok is True
    assert salud.motivo == ""
    assert [comando[comando.index("call") + 1] for comando, _ in ejecutor.llamadas] == [
        "talend_bridge_ping",
        "talend_studio_ui_dialogs",
    ]
    assert all(tiempo == 10.0 for _, tiempo in ejecutor.llamadas)


def test_salud_dialogo_bloqueado():
    ejecutor = EjecutorPorHerramienta(
        {
            "talend_bridge_ping": _respuesta("ping.json"),
            "talend_studio_ui_dialogs": (
                '{"ok": true, "data": {"blocked": true, "blocking": '
                '[{"title": "Network Issue Occured", "blocking": true}]}}'
            ),
        }
    )

    salud = comprobar_salud(_backend(ejecutor))

    assert salud.ok is False
    assert "revisa si hay un diálogo abierto en Talend Studio" in salud.motivo
    assert "Network Issue Occured" in salud.motivo


def test_salud_con_codigo_de_dialogo_en_el_ping():
    ejecutor = EjecutorPorHerramienta(
        {"talend_bridge_ping": '{"ok": false, "error": {"code": "STUDIO_DIALOG_OPEN"}}'}
    )

    salud = comprobar_salud(_backend(ejecutor))

    assert salud.ok is False
    assert "STUDIO_DIALOG_OPEN" in salud.motivo
    assert "revisa si hay un diálogo abierto en Talend Studio" in salud.motivo


def test_salud_tiempo_agotado():
    salud = comprobar_salud(_backend(EjecutorQueFalla(BackendNoDisponible("no respondió"))))

    assert salud.ok is False
    assert "revisa si hay un diálogo abierto en Talend Studio" in salud.motivo


def test_salud_sin_permiso_de_escritura():
    ejecutor = EjecutorPorHerramienta(
        {"talend_bridge_ping": '{"ok": true, "data": {"mode": "readOnly"}}'}
    )

    salud = comprobar_salud(_backend(ejecutor))

    assert salud.ok is False
    assert "escritura" in salud.motivo


class BackendSobreMCP:
    """Devuelve el sobre `{ok, data}` que entrega `McpBackend`."""

    def llamar(self, tool: str, entrada: dict, tiempo_max: float | None = None) -> dict:
        datos = (
            {"mode": "readWrite"}
            if tool == "talend_bridge_ping"
            else {"blocked": False, "dialogs": [], "blocking": []}
        )
        return {"ok": True, "source": "studio-bridge", "data": datos}


def test_salud_lee_el_sobre_data_del_mcp():
    """El MCP anida `mode` y `blocked` en `data`; la CLI los entrega planos."""
    salud = comprobar_salud(BackendSobreMCP())

    assert salud.ok is True
    assert salud.motivo == ""


class BackendQueSeRecupera:
    """Primero el bridge caído; tras `talend_studio_ensure_ready` vuelve a READY."""

    def __init__(self) -> None:
        self.llamadas: list[tuple[str, dict]] = []
        self.recuperado = False

    def llamar(self, tool: str, entrada: dict, tiempo_max: float | None = None) -> dict:
        self.llamadas.append((tool, entrada))
        if tool == "talend_studio_ensure_ready":
            self.recuperado = entrada.get("restart") is True
            return {"ok": True, "data": {"state": "READY", "recovered": True, "elapsedMs": 900}}
        if tool == "talend_bridge_ping":
            if self.recuperado:
                return {"ok": True, "data": {"mode": "readWrite"}}
            return {"ok": False, "error": {"code": "STUDIO_BRIDGE_DOWN"}}
        return {"ok": True, "data": {"blocked": False}}

    def herramientas(self) -> list[str]:
        return [herramienta for herramienta, _ in self.llamadas]


class BackendConDialogo:
    """Studio responde, pero un diálogo modal bloquea el bridge."""

    def __init__(self) -> None:
        self.llamadas: list[str] = []

    def llamar(self, tool: str, entrada: dict, tiempo_max: float | None = None) -> dict:
        self.llamadas.append(tool)
        if tool == "talend_bridge_ping":
            return {"ok": True, "data": {"mode": "readWrite"}}
        if tool == "talend_studio_ui_dialogs":
            return {
                "ok": True,
                "data": {
                    "blocked": True,
                    "blocking": [{"title": "Network Issue Occured", "blocking": True}],
                },
            }
        return {"ok": True, "data": {"state": "READY"}}


def test_salud_nombra_el_estado_listo():
    ejecutor = _libre()

    salud = comprobar_salud(_backend(ejecutor))

    assert salud.estado == "READY"


def test_salud_bridge_caido_sin_recuperar_no_toca_studio():
    backend = BackendQueSeRecupera()

    salud = comprobar_salud(backend, recuperar=False)

    assert salud.ok is False
    assert salud.estado == "BRIDGE_DEAD"
    assert "BRIDGE_DEAD" in salud.motivo
    assert "talend_studio_ensure_ready" not in backend.herramientas()


def test_salud_bridge_caido_se_recupera_una_vez():
    backend = BackendQueSeRecupera()

    salud = comprobar_salud(backend, recuperar=True)

    assert salud.ok is True
    assert salud.estado == "READY"
    assert backend.herramientas().count("talend_studio_ensure_ready") == 1
    assert dict(backend.llamadas)["talend_studio_ensure_ready"] == {"restart": True}


def test_salud_modal_nombra_el_dialogo_y_no_reintenta():
    backend = BackendConDialogo()

    salud = comprobar_salud(backend, recuperar=True)

    assert salud.ok is False
    assert salud.estado == "MODAL_BLOCKING"
    assert "Network Issue Occured" in salud.motivo
    assert "talend_studio_ensure_ready" not in backend.llamadas


def test_salud_de_un_codigo_de_error_desconocido_queda_como_bridge_caido():
    ejecutor = EjecutorPorHerramienta(
        {"talend_bridge_ping": '{"ok": false, "error": {"code": "ALGO_RARO"}}'}
    )

    salud = comprobar_salud(_backend(ejecutor))

    assert salud.estado == "BRIDGE_DEAD"
    assert "ALGO_RARO" in salud.motivo


def test_la_respuesta_guardada_es_la_del_puente():
    """El fixture no es inventado: trae los campos que el mapeo lee."""
    datos = json.loads(_respuesta("ping.json"))["data"]

    assert datos["mode"] == "readWrite"
