"""Los vectores documentados de funciones también son casos ejecutables del corpus L4."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

import proponer_esquemas_caso as propuesta  # noqa: E402
from corpus_lib.generar_entradas_l4l6 import calcular_l4, generar_caso  # noqa: E402
from corpus_semantica import cargar_vectores  # noqa: E402


def _api():
    try:
        return importlib.import_module("corpus_lib.especificaciones_l4_vectores")
    except ModuleNotFoundError as exc:
        pytest.fail(f"falta el generador de especificaciones L4 desde vectores: {exc}")


def test_scan_crea_un_caso_por_tupla_de_literales_y_conserva_filas() -> None:
    api = _api()
    vectores = [
        vector
        for vector in cargar_vectores()
        if vector["id"] in {"scan-02", "scan-04"}
    ]
    specs = api.especificaciones_de_vectores(vectores)

    assert list(specs) == ["l4_100_vec_scan_2", "l4_101_vec_scan_3"]
    primero = specs["l4_100_vec_scan_2"]
    assert primero["entrada"][1] == ["TEXTO"]
    assert primero["entrada"][2] == [("a  b",)]
    assert primero["asignaciones"][0][2] == (("scan", 2),)
    assert calcular_l4(primero).filas == [("a  b", "b")]
    assert calcular_l4(specs["l4_101_vec_scan_3"]).filas == [("ab cd", " ")]


def test_diferencia_con_el_oraculo_identifica_el_vector() -> None:
    api = _api()
    vector = next(vector.copy() for vector in cargar_vectores() if vector["id"] == "scan-02")
    vector["esperado"] = "c"

    with pytest.raises(ValueError, match="scan-02"):
        api.especificaciones_de_vectores([vector])


def test_input_emite_el_informat_w_d_como_un_argumento_sas() -> None:
    api = _api()
    spec = next(
        spec for name, spec in api.ESPECIFICACIONES_L4V.items() if "_vec_input_6_2" in name
    )

    assert spec["asignaciones"][0][3] == "RESULTADO=input(TEXTO, 6.2);"


def test_input_conserva_como_texto_los_valores_que_parecen_numericos() -> None:
    api = _api()
    spec = next(
        spec for name, spec in api.ESPECIFICACIONES_L4V.items() if "_vec_input_8_2" in name
    )

    assert "INFILE '.../entradas/ENTRADA_L4.csv' DSD DLM=',' FIRSTOBS=2 TRUNCOVER;" in spec[
        "programa"
    ]
    assert "INPUT TEXTO : $CHAR7.;" in spec["programa"]
    assert "PROC IMPORT" not in spec["programa"]


def test_esquema_de_input_vectorial_respeta_el_informat_caracter() -> None:
    caso = REPO / "tests" / "corpus" / "L4" / "l4_101_vec_input_8_2"

    esquemas = propuesta.bloque_del_caso(caso)

    assert esquemas["WORK.ENTRADA_L4"]["TEXTO"]["tipo"] == "String"
    assert esquemas["WORK.ENTRADA_L4"]["TEXTO"]["linea"] == 4


def test_compress_omitted_argument_uses_documented_empty_string() -> None:
    api = _api()
    spec = next(
        spec
        for name, spec in api.ESPECIFICACIONES_L4V.items()
        if "_vec_compress_omitido_ss" in name
    )

    assert spec["asignaciones"][0][3] == "RESULTADO=compress(TEXTO, '', 's');"


def test_coalescec_separa_llamadas_de_distinta_aridad() -> None:
    api = _api()
    specs = api.especificaciones_de_vectores(cargar_vectores())

    dos = next(spec for name, spec in specs.items() if "coalescec" in name and "a2" in name)
    tres = next(spec for name, spec in specs.items() if "coalescec" in name and "a3" in name)
    assert len(dos["entrada"][1]) == 2
    assert len(tres["entrada"][1]) == 3
    assert len(dos["entrada"][2]) == 2
    assert len(tres["entrada"][2]) == 1


def test_solo_incluye_vectores_con_oraculo_y_confianza_verificable() -> None:
    api = _api()
    vectores = cargar_vectores()
    specs = api.especificaciones_de_vectores(vectores)

    assert api.ESPECIFICACIONES_L4V == specs
    assert all("incierto" not in spec["razonamiento"] for spec in specs.values())


def test_generar_caso_escribe_el_programa_sas_de_la_especificacion(tmp_path: Path) -> None:
    api = _api()
    nombre, spec = next(iter(api.ESPECIFICACIONES_L4V.items()))

    escritos = generar_caso("L4", nombre, spec, tmp_path)

    programa = tmp_path / "L4" / nombre / "programa.sas"
    assert programa in escritos
    assert programa.is_file()
    assert spec["asignaciones"][0][3] in programa.read_text(encoding="utf-8")
