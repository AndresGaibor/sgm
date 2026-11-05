"""Hito 86 / R1-04: los `expressionFilter` del `tMap` son nulo-seguros y salen de la regla."""

from __future__ import annotations

from pathlib import Path

import pytest

from sgm.proceso.reglas_fila import ReglaFila
from sgm.talend_item.filtros_fila import (
    faltante_o_cero,
    filtro,
    no_faltante_ni_cero,
    salidas_filtro,
)
from sgm.talend_item.modelo import Columna

V02 = (
    Path(__file__).resolve().parents[2]
    / "tests" / "corpus" / "L8" / "validaciones" / "v02_vacios_ceros" / "programa.sas"
)

TIT_COT = ReglaFila("T", "NRO_DOC", "tit_cot", 1, "RELACION", "9902", "<>")
FA = ReglaFila("F", "NRO_DOC", "fa", 2, "RELACION", "9902", "=")
VALIDO = ReglaFila("V", "NRO_DOC", "valido", 3)


def test_el_faltante_o_cero_es_texto_vacio_o_cero_y_aguanta_null():
    expresion = faltante_o_cero("NRO_DOC")
    assert "row1.NRO_DOC == null" in expresion
    assert '"".equals(row1.NRO_DOC)' in expresion
    assert '"0".equals(row1.NRO_DOC)' in expresion
    assert "row1.NRO_DOC.equals" not in expresion
    assert ";" not in expresion


def test_el_valido_es_la_negacion_del_faltante_o_cero():
    assert no_faltante_ni_cero("NRO_DOC") == f"!{faltante_o_cero('NRO_DOC')}"


def test_el_filtro_usa_el_prefijo_de_fila_que_recibe():
    assert "normalizados.NRO_DOC" in filtro(VALIDO, "normalizados")
    assert "row1.NRO_DOC" not in filtro(VALIDO, "normalizados")


def test_tit_cot_y_fa_se_distinguen_solo_por_la_negacion_de_la_relacion():
    t, f = filtro(TIT_COT), filtro(FA)
    assert '!"9902".equals(row1.RELACION)' in t
    assert '"9902".equals(row1.RELACION)' in f
    assert '!"9902".equals' not in f
    assert t.replace("!", "") == f


def test_la_regla_de_validos_no_lleva_relacion_y_es_nulo_segura():
    expresion = filtro(VALIDO)
    assert "RELACION" not in expresion
    assert "row1.NRO_DOC == null" in expresion
    assert expresion.startswith("!")


@pytest.mark.parametrize("regla", [TIT_COT, FA, VALIDO])
def test_ningun_filtro_contiene_sentencias_ni_llama_equals_sobre_la_columna(regla):
    expresion = filtro(regla)
    assert ";" not in expresion
    assert "row1.NRO_DOC.equals" not in expresion
    assert "row1.RELACION.equals" not in expresion


def test_salidas_filtro_genera_una_salida_por_regla_con_su_filtro():
    esquemas = {m: [Columna("A"), Columna("B")] for m in ("tit_cot", "fa", "valido")}
    salidas = salidas_filtro([TIT_COT, FA, VALIDO], esquemas, "normalizados")
    assert [s.nombre for s in salidas] == ["tit_cot", "fa", "valido"]
    for salida, regla in zip(salidas, [TIT_COT, FA, VALIDO], strict=True):
        assert salida.filtro == filtro(regla, "normalizados")
        assert salida.expresiones == {"A": "normalizados.A", "B": "normalizados.B"}
        assert salida.rechazo is False and salida.rechazo_union is False


def test_un_modo_sin_esquema_falla_en_lugar_de_inventar_columnas():
    with pytest.raises(ValueError, match="Falta el esquema"):
        salidas_filtro([FA], {"tit_cot": [Columna("A")]})


def test_las_reglas_reales_de_v02_generan_tres_filtros():
    from sgm.proceso.reglas_fila import reglas_fila

    reglas = reglas_fila(V02.read_text(encoding="utf-8"))
    esquemas = {m: [Columna("NRO_DOC")] for m in ("tit_cot", "fa", "valido")}
    salidas = salidas_filtro(reglas, esquemas)
    assert len(salidas) == 3
    assert all(s.filtro for s in salidas)
    assert len({s.filtro for s in salidas}) == 3
