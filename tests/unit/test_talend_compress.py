"""Casos de seguridad semántica para COMPRESS SAS."""

import pytest

from sgm.expressions.talend_translator import Unsupported, translate_to_talend


def test_compress_conserva_solo_digitos_con_el_modificador_demostrado():
    result = translate_to_talend("compress(value,,'kd')")

    assert result.java == (
        '(input_row.value == null ? null : '
        'StringHandling.EREPLACE(input_row.value, "[^0-9]", ""))'
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
    ],
)
def test_compress_deja_combinaciones_no_demostradas_pendientes(sas):
    with pytest.raises(Unsupported):
        translate_to_talend(sas)
