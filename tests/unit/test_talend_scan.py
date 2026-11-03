"""Casos de seguridad semántica para la función SCAN SAS."""

import pytest

from sgm.expressions.talend_translator import Unsupported, translate_to_talend


def test_scan_con_posicion_negativa_cuenta_desde_el_final():
    result = translate_to_talend("scan(name,-1,' ')")

    assert ".length >= 1 ?" in result.java
    assert "+ -1]" in result.java
    assert "[-2]" not in result.java


@pytest.mark.parametrize("position", ["0", "1.5", "-1.5", "2147483648"])
def test_scan_deja_posiciones_cero_fraccionarias_o_fuera_de_rango_pendientes(position):
    with pytest.raises(Unsupported, match="posición"):
        translate_to_talend(f"scan(name,{position})")
