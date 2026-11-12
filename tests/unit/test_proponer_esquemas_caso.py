"""Bloque `esquemas` propuesto desde el migrador para un caso (B-4)."""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

import proponer_esquemas_caso as propuesta  # noqa: E402
from corpus_lib import esquemas_caso  # noqa: E402

PROGRAMA = (
    "proc import datafile='.../clientes.csv' out=work.clientes dbms=csv replace;\n"
    "  getnames=yes;\n"
    "run;\n"
    "data work.t;\n"
    "  length x $8;\n"
    "  x='a';\n"
    "run;\n"
)


def _caso(tmp_path: Path) -> Path:
    (tmp_path / "programa.sas").write_text(PROGRAMA, encoding="utf-8")
    (tmp_path / "entradas").mkdir()
    (tmp_path / "entradas" / "clientes.csv").write_text("id,nombre\n1,Ana\n2,Luis\n", encoding="utf-8")
    return tmp_path


def test_muestra_da_tipo_y_linea_a_cada_columna_leida(tmp_path: Path) -> None:
    bloque = propuesta.bloque_del_caso(_caso(tmp_path))
    clientes = bloque["WORK.CLIENTES"]
    assert clientes["id"]["tipo"] == "Double"
    assert clientes["nombre"]["tipo"] == "String"
    assert clientes["id"]["linea"] == 1


def test_length_da_carácter_con_longitud_y_linea(tmp_path: Path) -> None:
    bloque = propuesta.bloque_del_caso(_caso(tmp_path))
    assert bloque["WORK.T"]["x"] == {"tipo": "String", "linea": 5, "longitud": 8}


def test_el_bloque_propuesto_pasa_la_validacion_del_corpus(tmp_path: Path) -> None:
    bloque = propuesta.bloque_del_caso(_caso(tmp_path))
    assert esquemas_caso.validar(bloque) == bloque


def test_aritmetica_no_demuestra_tipo_en_el_contrato(tmp_path: Path) -> None:
    caso = tmp_path / "c"
    caso.mkdir()
    (caso / "programa.sas").write_text("data work.t; y = x + 1; run;\n", encoding="utf-8")
    bloque = propuesta.bloque_del_caso(caso)
    # una operación no demuestra el tipo en este contrato: solo LENGTH o la muestra lo hacen
    assert bloque["WORK.T"]["y"]["tipo"] == "pendiente"
    assert esquemas_caso.validar(bloque) == bloque
