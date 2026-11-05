"""Comando `sgm secretos`: códigos de salida, formatos, determinismo y errores de uso."""

from __future__ import annotations

import json

from typer.testing import CliRunner

from sgm.cli import app
from sgm.seguridad.escaner_secretos import escanear_ruta

LIMPIO = "proc print data=work.x;\nrun;\n"
CON_SECRETO = "libname x oracle password=Zx9-ficticio-123;\n"


def test_carpeta_limpia_sale_con_cero(tmp_path) -> None:
    (tmp_path / "a.sas").write_text(LIMPIO, encoding="utf-8")
    resultado = CliRunner().invoke(app, ["secretos", str(tmp_path)])
    assert resultado.exit_code == 0
    assert "0 hallazgo(s)" in resultado.output


def test_carpeta_con_secreto_sale_con_uno_y_nombra_archivo_y_linea(tmp_path) -> None:
    (tmp_path / "a.sas").write_text(LIMPIO, encoding="utf-8")
    (tmp_path / "b.sas").write_text(CON_SECRETO, encoding="utf-8")
    resultado = CliRunner().invoke(app, ["secretos", str(tmp_path)])
    assert resultado.exit_code == 1
    assert resultado.output.splitlines()[0].startswith("b.sas:1: password_en_cadena: Zx***")


def test_salida_json_es_valida_y_con_los_mismos_datos(tmp_path) -> None:

    (tmp_path / "b.sas").write_text(CON_SECRETO, encoding="utf-8")
    resultado = CliRunner().invoke(app, ["secretos", str(tmp_path), "--formato", "json"])
    datos = json.loads(resultado.output)
    assert datos["revisados"] == 1
    assert [h["tipo"] for h in datos["hallazgos"]] == ["password_en_cadena"]


def test_salida_es_determinista(tmp_path) -> None:
    for nombre in ("c.sas", "a.sas", "b.sas"):
        (tmp_path / nombre).write_text(CON_SECRETO, encoding="utf-8")
    primera = CliRunner().invoke(app, ["secretos", str(tmp_path)]).output
    segunda = CliRunner().invoke(app, ["secretos", str(tmp_path)]).output
    assert primera == segunda
    orden = [line.split(":")[0] for line in primera.splitlines()[:3]]
    assert orden == ["a.sas", "b.sas", "c.sas"]


def test_binarios_no_se_revisan(tmp_path) -> None:
    (tmp_path / "x.bin").write_bytes(b"\x00\x01password=Zx9-ficticio-123")
    escaneo = escanear_ruta(tmp_path)
    assert escaneo.revisados == 0
    assert escaneo.hallazgos == ()


def test_formato_desconocido_es_error_de_uso(tmp_path) -> None:
    resultado = CliRunner().invoke(app, ["secretos", str(tmp_path), "--formato", "xml"])
    assert resultado.exit_code != 0


def test_ruta_inexistente_es_error_de_uso(tmp_path) -> None:
    resultado = CliRunner().invoke(app, ["secretos", str(tmp_path / "no_existe")])
    assert resultado.exit_code != 0
