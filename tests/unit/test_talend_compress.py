"""Casos de seguridad semántica para COMPRESS SAS."""

import pytest

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
    ],
)
def test_compress_deja_combinaciones_no_demostradas_pendientes(sas):
    with pytest.raises(Unsupported):
        translate_to_talend(sas)


@pytest.mark.parametrize("sas", ["compress(value,'a\\b')", "compress(value,'a\nb')"])
def test_compress_deja_escapes_que_no_puede_serializar_pendientes(sas):
    with pytest.raises(Unsupported):
        translate_to_talend(sas)
