"""Comportamiento de operadores SAS y despacho universal del intérprete."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import sqlglot.expressions as exp

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

import corpus_semantica as cs  # noqa: E402

from sgm.migrar.interprete import NoSoportadoEnInterprete, _arbol, _valor  # noqa: E402


def test_length_se_despacha_por_la_tabla_del_interprete() -> None:
    assert _valor(_arbol("length(a)"), {"a": "abc   "}) == 3


def test_upcase_se_normaliza_a_la_funcion_sas_del_interprete() -> None:
    arbol = _arbol("UPCASE(a)")

    assert isinstance(arbol, exp.Anonymous)
    assert arbol.name.lower() == "sgm_upcase"
    assert _valor(arbol, {"a": "ab"}) == "AB"


def test_despacho_no_reescribe_literales_de_texto() -> None:
    assert _valor(_arbol("'length('"), {}) == "length("


def test_funcion_ajena_a_la_tabla_sigue_sin_adivinarse() -> None:
    with pytest.raises(NoSoportadoEnInterprete):
        _valor(_arbol("no_es_funcion(a)"), {"a": 1})


def test_operadores_usan_comparacion_sas_con_faltantes() -> None:
    from sgm.migrar.interprete_operadores import entre, pertenece

    assert pertenece(None, [1, 2]) is False
    assert entre(None, 0, 10) is False


def test_like_y_concatenacion_salen_al_modulo_de_operadores() -> None:
    from sgm.migrar.interprete_operadores import concatenar, parecido

    assert parecido("ABC", "A%") is True
    assert parecido("ABC ", "ABC") is False
    assert parecido("ABC ", "ABC%") is True
    assert concatenar("ab ", "c") == "ab c"


def test_like_con_faltante_queda_pendiente_en_ambos_motores() -> None:
    with pytest.raises(NoSoportadoEnInterprete, match="P-LIKE-TIPO-Y-LONGITUD-VARIABLE"):
        _valor(_arbol("NULL LIKE '%'"), {})
    with pytest.raises(ValueError, match="P-LIKE-TIPO-Y-LONGITUD-VARIABLE"):
        cs.evaluar("like", None, "%")


def test_vectores_de_operadores_y_faltantes_pasan_en_ambos_motores() -> None:
    ids = {
        "cmp-in-01",
        "cmp-in-02",
        "cmp-between-01",
        "cmp-between-02",
        "cmp-like-01",
        "cmp-like-02",
        "ar-faltante-01",
        "ar-faltante-02",
        "cat-01",
    }
    vectores = cs.cargar_vectores()
    assert ids <= {v["id"] for v in vectores}

    resultado = cs.verificar(motor="interprete")

    assert resultado["fallos"] == []
    assert resultado["diferencias_motores"] == []
