"""Casos de seguridad semántica para el operador LIKE SAS."""

import pytest

from sgm.expressions.talend_translator import Unsupported, translate_to_talend


@pytest.mark.parametrize(
    ("pattern", "expected"),
    [
        ("A.B%", r'(input_row.x != null && input_row.x.matches("A\\.B.*"))'),
        ("A*_%", r'(input_row.x != null && input_row.x.matches("A\\*..*"))'),
        (r"A\B%", r'(input_row.x != null && input_row.x.matches("A\\\\B.*"))'),
    ],
)
def test_like_escapa_regex_literal_y_serializa_java(pattern, expected):
    result = translate_to_talend(f"x like '{pattern}'")

    assert result.java == expected


def test_like_deja_pendientes_los_patrones_calculados():
    with pytest.raises(Unsupported, match="literal"):
        translate_to_talend("x like substr(pattern,1)")


def test_like_deja_pendientes_los_caracteres_de_control():
    with pytest.raises(Unsupported, match="control"):
        translate_to_talend("x like 'A\tB'")
