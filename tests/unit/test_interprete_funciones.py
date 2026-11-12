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
        "left",
        "substr",
        "substrn",
        "compress",
        "scan",
        "coalescec",
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
        ("left", ["  ab"], "ab  "),
        ("substr", ["abcdef", 2, 3], "bcd"),
        ("substrn", ["abcdef", 2, 3], "bcd"),
        ("input", ["1234", 6.2], 12.34),
        ("compress", ["a b 1", "1"], "a b "),
        ("scan", ["a b c", 2], "b"),
        ("abs", [-2], 2.0),
        ("sum", [1, None, 3], 4.0),
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
