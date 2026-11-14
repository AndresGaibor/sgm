"""Contrato de despacho de funciones del intérprete, separado de su motor de expresiones."""

from __future__ import annotations

import pytest

from sgm.migrar.interprete import NoSoportadoEnInterprete as ErrorInterprete
from sgm.migrar.interprete import _funcion
from sgm.migrar.interprete_errores import NoSoportadoEnInterprete
from sgm.migrar.interprete_funciones import FUNCIONES, llamar


def test_la_clase_de_error_se_reexporta_desde_interprete():
    assert ErrorInterprete is NoSoportadoEnInterprete


def test_funciones_reune_las_familias_actuales():
    assert set(FUNCIONES) == {
        "trim",
        "strip",
        "upcase",
        "lowcase",
        "length",
        "lengthc",
        "lengthn",
        "propcase",
        "reverse",
        "repeat",
        "right",
        "trimn",
        "compbl",
        "tranwrd",
        "translate",
        "index",
        "find",
        "count",
        "left",
        "substr",
        "substrn",
        "compress",
        "scan",
        "cat",
        "cats",
        "catt",
        "coalescec",
        "catx",
        "substr_asignar",
        "mean",
        "min",
        "max",
        "sum",
        "abs",
        "coalesce",
        "missing",
        "input",
    }


@pytest.mark.parametrize(
    ("nombre", "argumentos", "esperado"),
    [
        ("mean", [1, None, 3], 2.0),
        ("min", [3, None, 2], 2.0),
        ("max", [3, None, 2], 3.0),
        ("missing", [None], True),
        ("coalesce", [None, "", "x"], "x"),
        ("coalescec", [None, "", "x"], "x"),
        ("trim", ["ab  "], "ab"),
        ("strip", ["  ab  "], "ab"),
        ("upcase", ["Ab"], "AB"),
        ("lowcase", ["Ab"], "ab"),
        ("length", ["abc"], 3),
        ("length", ["abc   "], 3),
        ("length", [" "], 1),
        ("compbl", ["a   b  c"], "a b c"),
        ("compbl", ["  a  b"], " a b"),
        ("tranwrd", ["abc def abc", "abc", "x"], "x def x"),
        ("tranwrd", ["abc", "z", "y"], "abc"),
        ("tranwrd", ["abc", "b", ""], "a c"),
        ("translate", ["abc", "xy", "ab"], "xyc"),
        ("index", ["abcabc", "c"], 3),
        ("index", ["ABC", "b"], 0),
        ("find", ["ABC", "b", "i"], 2),
        ("find", ["abcabc", "c", None, 4], 6),
        ("count", ["banana", "an"], 2),
        ("count", ["aAa", "a", "i"], 3),
        ("lengthc", ["abc   "], 6),
        ("lengthn", [""], 0),
        ("propcase", ["hELLO wORLD"], "Hello World"),
        ("propcase", ["mc-donald"], "Mc-Donald"),
        ("reverse", ["abc"], "cba"),
        ("reverse", ["ab  "], "  ba"),
        ("repeat", ["ab", 2], "ababab"),
        ("repeat", ["ab", 0], "ab"),
        ("right", ["ab  "], "  ab"),
        ("trimn", [" "], ""),
        ("left", ["  ab"], "ab  "),
        ("substr", ["abcdef", 2, 3], "bcd"),
        ("substrn", ["abcdef", 2, 3], "bcd"),
        ("input", ["1234", 6.2], 12.34),
        ("compress", ["a b 1", "1"], "a b "),
        ("scan", ["a b c", 2], "b"),
        ("abs", [-2], 2.0),
        ("sum", [1, None, 3], 4.0),
        ("cat", ["a ", " b"], "a  b"),
        ("cats", [" a ", " b "], "ab"),
        ("catt", ["a  ", " b  "], "a b"),
        ("catx", [",", "a", "", "b"], "a,b"),
        ("substr_asignar", ["abcdef", 2, 3, "XY"], "aXY ef"),
        ("substr_asignar", ["abcdef", 2, 3, "XYZW"], "aXYZef"),
        ("substr_asignar", ["abcdef", 4, None, "Z"], "abcZef"),
    ],
)
def test_llamar_conserva_las_funciones_y_sus_resultados(nombre, argumentos, esperado):
    assert llamar(nombre, argumentos) == esperado


def test_llamar_quita_los_prefijos_del_arbol_y_de_la_fila():
    assert llamar("sgm_trim", ["ab  "]) == "ab"
    assert llamar("row_sum", [1, None, 3]) == 4.0


def test_funcion_no_registrada_conserva_el_error_del_interprete():
    with pytest.raises(NoSoportadoEnInterprete) as error:
        llamar("no_existe", [1])

    assert error.value.kind == "funcion"
    assert error.value.detalle == "no_existe"


def test_el_wrapper_de_interprete_delega_al_mismo_despacho():
    assert _funcion("sgm_trim", ["ab  "]) == llamar("sgm_trim", ["ab  "])


def test_input_respeta_ancho_y_dinamica_de_dos_digitos():
    assert llamar("input", ["1234567", 3.0]) == 123.0
    assert llamar("input", ["1", "8.10"]) == 1e-10


def test_input_en_notacion_cientifica_no_aplica_d():
    assert llamar("input", ["1E3", "8.2"]) == 1000.0


def test_catx_omite_elementos_en_blanco_y_recorta_los_extremos():
    assert llamar("catx", [",", " a ", "b ", "  ", "c"]) == "a,b,c"


def test_cat_conserva_o_quita_blancos_segun_la_funcion_y_trata_blanco_como_faltante():
    assert llamar("cat", ["a", "", "b"]) == "ab"
    assert llamar("cats", [" a ", "", " b "]) == "ab"
    assert llamar("catt", ["a  ", "", " b"]) == "a b"
    assert llamar("catx", [",", "a", "", "b"]) == "a,b"


def test_left_y_trim_conservan_la_semantica_de_un_campo_en_blanco():
    assert llamar("left", ["   "]) == "   "
    assert llamar("trim", ["   "]) == " "


def test_translate_es_simultanea_y_lengthc_cuenta_puntos_unicode():
    assert llamar("translate", ["abc", "xy", "ab"]) == "xyc"
    assert llamar("translate", ["ab", "ba", "ab"]) == "ba"
    with pytest.raises(NoSoportadoEnInterprete, match="P-TRANSLATE-CODIFICACION-SBCS"):
        llamar("translate", ["áb", "xy", "ab"])
    assert llamar("lengthc", ["😀"]) == 1
    assert llamar("lengthn", ["😀  "]) == 1


def test_tranwrd_exige_objetivo_no_vacio_y_trata_reemplazo_vacio_como_blanco():
    with pytest.raises(NoSoportadoEnInterprete, match="P-TRANWRD-OBJETIVO-VACIO"):
        llamar("tranwrd", ["abc", "", "x"])


def test_find_acepta_inicio_positivo_y_negativo_con_modificadores_documentados():
    assert llamar("find", ["abcabc", "c", 4]) == 6
    assert llamar("find", ["abcabc", "c", None, 4]) == 6
    assert llamar("find", ["abcabc", "c", None, -4]) == 3
    assert llamar("find", ["abc", "z", None, 0]) == 0
    assert llamar("find", ["abc ", "c ", "t"]) == 3


@pytest.mark.parametrize(
    ("nombre", "codigo"),
    [
        ("length", "P-LENGTH-CODIFICACION"),
        ("propcase", "P-PROPCASE-TRANTAB-LOCALE"),
        ("reverse", "P-REVERSE-CODIFICACION-SBCS"),
    ],
)
def test_funciones_dependientes_de_codificacion_quedan_pendientes(nombre, codigo):
    with pytest.raises(NoSoportadoEnInterprete, match=codigo):
        llamar(nombre, ["niño"])
