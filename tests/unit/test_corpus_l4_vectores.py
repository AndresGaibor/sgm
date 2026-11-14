"""Los vectores documentados de funciones también son casos ejecutables del corpus L4."""

from __future__ import annotations

import csv
import importlib
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

import proponer_esquemas_caso as propuesta  # noqa: E402
from corpus_lib.csv_tabla import Tabla, escribir_csv  # noqa: E402
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


def test_funciones_texto_nuevas_no_renumeran_casos_y_omiten_longitudes_ambiguas() -> None:
    api = _api()
    specs = api.especificaciones_de_vectores(cargar_vectores())

    assert "l4_100_vec_input_6_2" in specs
    assert "l4_131_vec_round_sin_literales" in specs
    assert "l4_132_vec_propcase_sin_literales" in specs
    assert "l4_133_vec_reverse_sin_literales" in specs
    assert specs["l4_133_vec_reverse_sin_literales"]["entrada"][2] == [("abc",)]
    assert "l4_134_vec_repeat_2" in specs
    assert "l4_135_vec_repeat_0" in specs
    assert "l4_136_vec_trimn_sin_literales" in specs
    assert "l4_137_vec_length_sin_literales" in specs
    assert tuple(specs)[-33:-21] == (
        "l4_138_vec_compbl_sin_literales",
        "l4_139_vec_tranwrd_sabc_sx",
        "l4_140_vec_tranwrd_sz_sy",
        "l4_141_vec_translate_sxy_sab",
        "l4_142_vec_index_sc",
        "l4_143_vec_index_sb",
        "l4_144_vec_find_sb_si",
        "l4_145_vec_find_sc_omitido_4",
        "l4_146_vec_count_san",
        "l4_147_vec_count_sa_si",
        "l4_148_vec_lengthc_sin_literales",
        "l4_149_vec_lengthn_sin_literales",
    )
    assert tuple(specs)[-12:] == (
        "l4_159_vec_sum_sin_literales_a2_NN",
        "l4_160_vec_sum_sin_literales_a3_NNN",
        "l4_161_vec_mean_sin_literales_a3_NNN",
        "l4_162_vec_mean_sin_literales_a1_N",
        "l4_163_vec_min_sin_literales",
        "l4_164_vec_max_sin_literales",
        "l4_165_vec_n_sin_literales",
        "l4_166_vec_nmiss_sin_literales",
        "l4_167_vec_ifn_sin_literales_a3_NNN",
        "l4_168_vec_ifn_sin_literales_a4_NNNN",
        "l4_169_vec_ifc_sin_literales_a3_NTT",
        "l4_170_vec_ifc_sin_literales_a4_NTTT",
    )
    assert tuple(specs)[-21:-12] == (
        "l4_150_vec_int_sin_literales",
        "l4_151_vec_ceil_sin_literales",
        "l4_152_vec_floor_sin_literales",
        "l4_153_vec_mod_sin_literales",
        "l4_154_vec_abs_sin_literales",
        "l4_155_vec_sqrt_sin_literales",
        "l4_156_vec_log_sin_literales",
        "l4_157_vec_exp_sin_literales",
        "l4_158_vec_sign_sin_literales",
    )
    assert not any("right" in nombre for nombre in specs)


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


def test_escribir_csv_cita_espacios_de_borde_y_preserva_los_valores(tmp_path: Path) -> None:
    ruta = tmp_path / "entrada.csv"

    escribir_csv(ruta, Tabla(["TEXTO"], [("abc   ",), (" ",)]), citar_espacios_borde=True)

    lineas = ruta.read_text(encoding="utf-8").splitlines()
    assert lineas == ["TEXTO", '"abc   "', '" "']
    with ruta.open(encoding="utf-8", newline="") as archivo:
        assert list(csv.reader(archivo)) == [["TEXTO"], ["abc   "], [" "]]
