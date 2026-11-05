"""La comparación de texto del `tMap` pone el literal a la izquierda: aguanta `null`."""

from __future__ import annotations

import pytest

from sgm.talend_item.expresiones import null_safe_equals


def test_el_literal_va_a_la_izquierda_de_equals():
    assert null_safe_equals("row2.tipo", "CC") == '"CC".equals(row2.tipo)'


def test_el_valor_se_escapa_como_literal_de_java():
    assert null_safe_equals("row1.x", 'a"b\\c') == '"a\\"b\\\\c".equals(row1.x)'


def test_una_expresion_vacia_se_rechaza():
    with pytest.raises(ValueError, match="expresión"):
        null_safe_equals("   ", "CC")


def test_el_valor_vacio_sigue_siendo_una_comparacion_valida():
    assert null_safe_equals("row1.x", "") == '"".equals(row1.x)'
