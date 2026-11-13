"""Salida tabular de `impala-shell` para las verificaciones del contenedor."""

from __future__ import annotations

import subprocess

import pytest

from tools.contenedores.consultar import consultar, filas_de_salida


def test_filas_de_salida_separa_comas_y_omite_lineas_vacias():
    assert filas_de_salida("a,1\nb,2\n\n") == [["a", "1"], ["b", "2"]]


def test_filas_de_salida_respeta_comas_entrecomilladas():
    assert filas_de_salida('"a,b",1\n') == [["a,b", "1"]]


def test_consultar_ejecuta_en_cliente_efimero_y_parsea(monkeypatch):
    llamada = {}

    def run(comando, **opciones):
        llamada["comando"] = comando
        llamada["opciones"] = opciones
        return subprocess.CompletedProcess(comando, 0, stdout="a,1\n", stderr="")

    monkeypatch.setattr("tools.contenedores.consultar.subprocess.run", run)

    assert consultar("select a, b from t") == [["a", "1"]]
    comando = llamada["comando"]
    assert "--rm" in comando
    assert "--network" in comando
    assert "-B" in comando
    assert "--output_delimiter=," in comando
    assert "select a, b from t" in comando
    assert llamada["opciones"]["check"] is False


def test_consultar_expone_el_stderr_si_falla(monkeypatch):
    monkeypatch.setattr(
        "tools.contenedores.consultar.subprocess.run",
        lambda comando, **_: subprocess.CompletedProcess(comando, 1, stdout="", stderr="falló"),
    )

    with pytest.raises(RuntimeError, match="falló"):
        consultar("select 1")
