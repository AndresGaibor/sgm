"""Regresiones de cabecera y raíz del proyecto para tablas locales."""

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from sgm.cli import app
from sgm.migrar.tablas_locales import cargar_tablas_locales


def crear_ficha(root: Path, contenido: str) -> Path:
    (root / "datos.csv").write_text(contenido, encoding="utf-8")
    (root / "datos.ficha.yaml").write_text(
        "tabla: lib.t\norigen: real\nfilas: 1\ncolumnas:\n  a: Double\n  b: String\nprocedencia: prueba\n",
        encoding="utf-8",
    )
    config = root / "locales.json"
    config.write_text(
        json.dumps({"lib.t": {"archivo": "datos.csv", "delimitador": ";"}}), encoding="utf-8"
    )
    return config


@pytest.mark.parametrize("contenido", ["b;a\nx;1\n", "1;x\n", "", '"a;b\n'])
def test_rechaza_cabecera_distinta_ausente_o_malformada(tmp_path, contenido):
    config = crear_ficha(tmp_path, contenido)
    with pytest.raises(ValueError, match=r"lib\.t"):
        cargar_tablas_locales(config, tmp_path)


def test_cli_usa_cwd_como_raiz_del_proyecto_externo(tmp_path, monkeypatch):
    config = crear_ficha(tmp_path, "a;b\n1;x\n")
    source = tmp_path / "p.sas"
    source.write_text("data work.c; set lib.t; run;", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(
        app,
        ["migrar", str(source), "--out", str(tmp_path / "out"), "--tablas-locales", str(config)],
    )
    assert result.exit_code == 0, result.output
    assert list((tmp_path / "out/p/process").glob("*.item"))


def test_cabecera_erronea_detiene_cli_antes_de_escribir(tmp_path, monkeypatch):
    config = crear_ficha(tmp_path, "b;a\nx;1\n")
    source = tmp_path / "p.sas"
    source.write_text("data work.c; set lib.t; run;", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(
        app,
        ["migrar", str(source), "--out", str(tmp_path / "out"), "--tablas-locales", str(config)],
    )
    assert result.exit_code == 2, result.output
    assert "lib.t" in result.output
    assert not (tmp_path / "out").exists()
