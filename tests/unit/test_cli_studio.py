"""Comandos `sgm studio` con un backend falso: no arrancan Studio ni el servidor MCP."""

from __future__ import annotations

import pytest
import typer
from typer.testing import CliRunner

from sgm.backend_talend import (
    BackendNoDisponible,
    ResultadoLote,
    TalendCliBackend,
    Veredicto,
)
from sgm.cli import app
from sgm.cli_studio import _elegir_backend

runner = CliRunner()


class BackendFalso:
    """Backend en memoria: anota lo pedido y devuelve una respuesta preparada."""

    def __init__(
        self,
        lote: ResultadoLote | None = None,
        veredicto: Veredicto | None = None,
        error: BackendNoDisponible | None = None,
        escribe: bool = True,
    ) -> None:
        self.lote = lote or ResultadoLote(compilan=(), no_compilan={})
        self.veredicto = veredicto or Veredicto("ok", ())
        self.error = error
        self.escribe = escribe
        self.eventos: list[str] = []
        self.nombres: list[str] = []
        self.contexto: dict[str, str] = {}

    def llamar(self, tool: str, entrada: dict, tiempo_max: float | None = None) -> dict:
        self.eventos.append(tool)
        if tool == "talend_bridge_ping":
            return {"data": {"mode": "readWrite" if self.escribe else "readOnly"}}
        return {"data": {"blocked": False, "dialogs": []}}

    def refrescar(self) -> None:
        self.eventos.append("refrescar")

    def compilar_lote(self, nombres: list[str]) -> ResultadoLote:
        if self.error:
            raise self.error
        self.nombres = list(nombres)
        return self.lote

    def verificar(self, nombre: str, contexto: dict[str, str]) -> Veredicto:
        if self.error:
            raise self.error
        self.contexto = dict(contexto)
        return self.veredicto


def _correr(monkeypatch, backend: BackendFalso, *args: str):
    monkeypatch.setattr("sgm.cli_studio._elegir_backend", lambda *a, **k: backend)
    return runner.invoke(app, ["studio", *args])


def test_salud_ok_sale_cero(monkeypatch):
    resultado = _correr(monkeypatch, BackendFalso(), "salud")

    assert resultado.exit_code == 0, resultado.output
    assert "responde y deja escribir" in resultado.output


def test_salud_sin_escritura_sale_uno(monkeypatch):
    resultado = _correr(monkeypatch, BackendFalso(escribe=False), "salud")

    assert resultado.exit_code == 1
    assert "escritura" in resultado.output


def test_compilar_informa_los_que_compilan_y_los_que_no(monkeypatch):
    backend = BackendFalso(ResultadoLote(compilan=("a",), no_compilan={"b": "javac"}))
    resultado = _correr(monkeypatch, backend, "compilar", "a", "b")

    assert resultado.exit_code == 1
    assert "OK a" in resultado.output
    assert "FALLA b: javac" in resultado.output
    assert backend.nombres == ["a", "b"]


def test_compilar_refresca_antes_si_se_pide(monkeypatch):
    backend = BackendFalso(ResultadoLote(compilan=("a",), no_compilan={}))
    resultado = _correr(monkeypatch, backend, "compilar", "a", "--refrescar")

    assert resultado.exit_code == 0, resultado.output
    assert backend.eventos[0] == "refrescar"


def test_compilar_sin_jobs_falla(monkeypatch):
    resultado = _correr(monkeypatch, BackendFalso(), "compilar")

    assert resultado.exit_code == 2


def test_verificar_pasa_el_contexto_y_no_falla_con_avisos(monkeypatch):
    backend = BackendFalso(veredicto=Veredicto("ok_con_avisos", ("[WARN] revisar",)))
    resultado = _correr(
        monkeypatch, backend, "verificar", "a", "--contexto", "A=1", "--contexto", "B=x=y"
    )

    assert resultado.exit_code == 0, resultado.output
    assert "Veredicto: ok_con_avisos" in resultado.output
    assert backend.contexto == {"A": "1", "B": "x=y"}


def test_verificar_con_error_sale_uno(monkeypatch):
    backend = BackendFalso(veredicto=Veredicto("error", ("[ERROR] no compila",)))
    resultado = _correr(monkeypatch, backend, "verificar", "a")

    assert resultado.exit_code == 1
    assert "[ERROR] no compila" in resultado.output


def test_contexto_sin_igual_es_uso_incorrecto(monkeypatch):
    resultado = _correr(monkeypatch, BackendFalso(), "verificar", "a", "--contexto", "A")

    assert resultado.exit_code == 2


def test_backend_talend_exige_sus_dos_rutas(monkeypatch):
    monkeypatch.delenv("SGM_TALEND_DIR", raising=False)
    monkeypatch.delenv("SGM_TALEND_PROJECT", raising=False)

    with pytest.raises(typer.BadParameter, match="--talend-dir"):
        _elegir_backend("talend", None, None, None, 10.0)


def test_backend_talend_usa_el_entorno(monkeypatch, tmp_path):
    monkeypatch.setenv("SGM_TALEND_DIR", str(tmp_path / "cli"))
    monkeypatch.setenv("SGM_TALEND_PROJECT", str(tmp_path / "proyecto"))

    backend = _elegir_backend("talend", None, None, None, 10.0)

    assert isinstance(backend, TalendCliBackend)
    assert backend.talend_dir == tmp_path / "cli"
    assert backend.proyecto == tmp_path / "proyecto"


def test_backend_desconocido_se_rechaza():
    with pytest.raises(typer.BadParameter, match="backend desconocido"):
        _elegir_backend("otro", None, None, None, 10.0)


def test_un_backend_caido_no_deja_traza(monkeypatch):
    backend = BackendFalso(error=BackendNoDisponible("sin conexión"))
    resultado = _correr(monkeypatch, backend, "compilar", "a")

    assert resultado.exit_code == 1
    assert "sin conexión" in resultado.output
