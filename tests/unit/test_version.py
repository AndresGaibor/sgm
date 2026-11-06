"""Versión única: `pyproject.toml`, `sgm.__version__`, `sgm --version` y `CHANGELOG.md`."""

import tomllib
from pathlib import Path

from typer.testing import CliRunner

import sgm
from sgm import __version__
from sgm import cli as cli_mod

RAIZ = Path(__file__).resolve().parents[2]


def _version_pyproject() -> str:
    with (RAIZ / "pyproject.toml").open("rb") as archivo:
        return tomllib.load(archivo)["project"]["version"]


def test_version_de_pyproject_es_la_del_paquete():
    assert __version__ == _version_pyproject()


def test_sgm_version_imprime_la_version_y_sale_con_cero():
    resultado = CliRunner().invoke(cli_mod.app, ["--version"])
    assert resultado.exit_code == 0
    assert resultado.output.strip() == f"sgm {_version_pyproject()}"


def test_la_ayuda_sigue_funcionando_con_la_opcion_raiz():
    resultado = CliRunner().invoke(cli_mod.app, ["--help"])
    assert resultado.exit_code == 0
    assert "--version" in resultado.output


def test_changelog_menciona_la_version_actual_y_sin_publicar():
    texto = (RAIZ / "CHANGELOG.md").read_text(encoding="utf-8")
    assert f"[{_version_pyproject()}]" in texto
    assert "[Sin publicar]" in texto


def test_sin_paquete_instalado_queda_el_respaldo(monkeypatch):
    def no_instalado(_nombre):
        raise sgm.PackageNotFoundError(_nombre)

    monkeypatch.setattr(sgm, "version", no_instalado)
    assert sgm._version_instalada() == "0+desconocida"
