"""Casos de seguridad semántica para COMPRESS SAS."""

import pytest

from sgm.expressions.expressions import translate
from sgm.expressions.talend_translator import Unsupported, translate_to_talend


def test_compress_conserva_solo_digitos_con_el_modificador_demostrado():
    result = translate_to_talend("compress(value,,'kd')")

    assert result.java == (
        '(input_row.value == null ? null : '
        'StringHandling.EREPLACE(input_row.value, "[^0-9]", ""))'
    )


def test_compress_conserva_digitos_y_punto_decimal_demostrados():
    result = translate_to_talend("compress(value,'.','kd')")

    assert result.java == (
        '(input_row.value == null ? null : '
        'StringHandling.EREPLACE(input_row.value, "[^0-9.]", ""))'
    )


def test_compress_escapa_caracteres_de_lista_para_java_y_regex():
    result = translate_to_talend("compress(phone,' ()-.')")

    assert result.java == (
        r'(input_row.phone == null ? null : '
        r'StringHandling.EREPLACE(input_row.phone, "[\\ \\(\\)\\-\\.]", ""))'
    )


def test_compress_no_duplica_el_escape_regex_de_ampersand():
    result = translate_to_talend("compress(value,'a&b')")

    assert result.java == (
        r'(input_row.value == null ? null : '
        r'StringHandling.EREPLACE(input_row.value, "[a\\&b]", ""))'
    )


def test_compress_predeterminado_en_el_flujo_publico_solo_quita_espacios():
    result = translate("compress(value)")

    assert result.talend == (
        '(input_row.value == null ? null : input_row.value.replaceAll(" ", ""))'
    )


def test_compress_usa_el_literal_sas_para_escapar_barra_invertida():
    result = translate_to_talend(r"compress(value,'a\b')")

    assert result.java == (
        r'(input_row.value == null ? null : '
        r'StringHandling.EREPLACE(input_row.value, "[a\\\\b]", ""))'
    )


@pytest.mark.parametrize(
    "sas",
    [
        "compress(value,,'d')",
        "compress(value,,'ka')",
        "compress(value,'-','kd')",
        "compress(value,,'dk')",
        "compress(value,,kd)",
        "compress(value,.,'kd')",
        "compress(value,',','kd')",
        "compress(value,'..','kd')",
        "compress(value,'')",
    ],
)
def test_compress_deja_formas_no_demostradas_pendientes(sas):
    with pytest.raises(Unsupported):
        translate_to_talend(sas)


@pytest.mark.parametrize("sas", ["compress(value,'a\nb')"])
def test_compress_deja_caracteres_de_control_pendientes(sas):
    with pytest.raises(Unsupported):
        translate_to_talend(sas)
