"""Casos de seguridad semántica para la función SCAN SAS."""

import pytest

from sgm.expressions.talend_translator import Unsupported, translate_to_talend


def test_scan_escapa_el_delimitador_de_punto_para_java():
    result = translate_to_talend("scan(filename,2,'.')")

    assert result.java == (
        r'(input_row.filename == null ? null : '
        r'(input_row.filename.replaceAll("^[\\.]+", "").split("[\\.]+").length >= 2 ? '
        r'input_row.filename.replaceAll("^[\\.]+", "").split("[\\.]+")[1] : null))'
    )


def test_scan_deja_delimitadores_vacios_pendientes():
    with pytest.raises(Unsupported, match="delimitadores"):
        translate_to_talend("scan(filename,1,'')")


@pytest.mark.parametrize(
    ("delimiter", "java_delimiter"),
    [("&", r"\\&"), ("\\", r"\\\\")],
)
def test_scan_escapa_delimitadores_especiales_en_regex_y_java(delimiter, java_delimiter):
    result = translate_to_talend(f"scan(filename,1,'{delimiter}')")

    assert f'.replaceAll("^[{java_delimiter}]+", "")' in result.java


def test_scan_con_posicion_negativa_cuenta_desde_el_final():
    result = translate_to_talend("scan(name,-1,' ')")

    assert ".length >= 1 ?" in result.java
    assert "+ -1]" in result.java
    assert "[-2]" not in result.java


@pytest.mark.parametrize("position", ["0", "1.5", "-1.5", "2147483648"])
def test_scan_deja_posiciones_cero_fraccionarias_o_fuera_de_rango_pendientes(position):
    with pytest.raises(Unsupported, match="posición"):
        translate_to_talend(f"scan(name,{position})")
