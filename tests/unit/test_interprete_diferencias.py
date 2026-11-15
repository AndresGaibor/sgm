"""Semántica documentada de INTCK, DATDIF y YRDIF."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from sgm.expressions.talend_translator import Unsupported, translate_to_talend
from sgm.migrar.interprete_errores import NoSoportadoEnInterprete
from sgm.migrar.interprete_funciones import llamar

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

import corpus_semantica as cs  # noqa: E402
from corpus_lib.especificaciones_l4_vectores import ESPECIFICACIONES_L4V  # noqa: E402

_IDS_DIFERENCIAS = {
    *(f"intck-{n:02d}" for n in range(1, 9)),
    *(f"datdif-{n:02d}" for n in range(1, 7)),
    *(f"yrdif-{n:02d}" for n in range(1, 7)),
}
_VECTORES_DIFERENCIAS = [
    vector
    for vector in cs.cargar_vectores()
    if vector["id"] in _IDS_DIFERENCIAS and vector["confianza"] != "incierto"
]


@pytest.mark.parametrize("vector", _VECTORES_DIFERENCIAS, ids=lambda vector: vector["id"])
def test_interprete_calcula_cada_vector_de_diferencia(vector: dict) -> None:
    obtenido = llamar(vector["funcion"], vector["entrada"])

    assert cs._coincide_interprete(obtenido, vector["esperado"]), (
        f"{vector['id']}: esperado {vector['esperado']!r}, obtenido {obtenido!r}"
    )


def test_intck_no_asume_semantica_del_metodo_continuo():
    with pytest.raises(NoSoportadoEnInterprete, match="P-INTCK-CONTINUO"):
        llamar("intck", ["month", 23406, 23407, "c"])


def test_yrdif_deja_el_cumpleanos_29_febrero_pendiente():
    with pytest.raises(NoSoportadoEnInterprete, match="P-YRDIF-AGE-29FEB"):
        llamar("yrdif", [21974, 22339, "AGE"])


def test_oraculo_e_interprete_coinciden_en_el_corpus_de_diferencias():
    assert {vector["id"] for vector in _VECTORES_DIFERENCIAS} == _IDS_DIFERENCIAS
    assert cs.verificar()["fallos"] == []
    resultado = cs.verificar(motor="interprete")
    assert resultado["fallos"] == []
    assert resultado["diferencias_motores"] == []


def test_vectores_de_diferencias_generan_casos_l4_estables():
    ids = {f"l4_{numero}_" for numero in range(195, 208)}
    casos = {nombre for nombre in ESPECIFICACIONES_L4V if any(nombre.startswith(id_) for id_ in ids)}

    assert len(casos) == 13
    assert all((REPO / "tests" / "corpus" / "L4" / caso / "programa.sas").is_file() for caso in casos)
    assert ESPECIFICACIONES_L4V[
        "l4_203_vec_yrdif_s4143542f414354"
    ]["pendiente"].startswith("P-JAVA-YRDIF-ACTACT")
    assert ESPECIFICACIONES_L4V["l4_205_vec_yrdif_sAGE"]["pendiente"].startswith(
        "P-JAVA-YRDIF-AGE"
    )


def test_talend_deja_yrdif_age_pendiente():
    with pytest.raises(Unsupported, match="P-JAVA-YRDIF-AGE"):
        translate_to_talend("yrdif(a, b, 'AGE')")
