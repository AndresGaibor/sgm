"""Expresiones Java de normalización del `tMap`: forma, nulos y escapes (sin Studio).

La equivalencia semántica con SAS se comprueba ejecutando en Studio (hito 83, `PROGRESS.md`).
Aquí se cubre lo que no necesita Studio: que las expresiones son expresiones (no sentencias),
que aguantan `null`, que los literales no dependen de la codificación del `.java` generado y
que el informat `w.d` se traduce a truncar, validar y mover el punto decimal.
"""

from __future__ import annotations

import pytest

from sgm.talend_item import normalizacion as n


def test_literal_java_escapa_comillas_barras_controles_y_no_ascii():
    assert n.literal_java('a"b\\c') == '"a\\"b\\\\c"'
    assert n.literal_java("\n\r\t") == '"\\n\\r\\t"'
    assert n.literal_java("NIÑO MARÍA") == '"NI\\u00d1O MAR\\u00cdA"'
    assert n.literal_java("abc 123") == '"abc 123"'


@pytest.mark.parametrize(
    "expresion",
    [
        n.left("row1.x"),
        n.strip("row1.x"),
        n.trim("row1.x"),
        n.upcase("row1.x"),
        n.lowcase("row1.x"),
        n.compbl("row1.x"),
        n.compress("row1.x"),
        n.compress("row1.x", "AB", "k"),
        n.input_left_wd("row1.x", 6, 2),
        n.normalizar_nombre("row1.x"),
    ],
)
def test_toda_expresion_es_nulo_segura_y_no_contiene_sentencias(expresion):
    assert expresion.startswith("(")
    assert "row1.x == null ? null :" in expresion
    assert ";" not in expresion


def test_input_left_wd_trunca_valida_y_mueve_el_punto():
    expresion = n.input_left_wd("row1.x", 6, 2)
    assert "substring(0, 6)" in expresion
    assert "new java.math.BigDecimal" in expresion
    assert "movePointLeft(2)" in expresion
    assert ".matches(" in expresion
    assert ": null)" in expresion
    assert "movePointLeft(0)" in n.input_left_wd("row1.x", 8, 0)


@pytest.mark.parametrize("w,d", [(0, 0), (-1, 2), (6, -1)])
def test_input_left_wd_rechaza_informats_invalidos(w, d):
    with pytest.raises(ValueError):
        n.input_left_wd("row1.x", w, d)


def test_compress_por_omision_quita_blancos_y_con_k_conserva_el_conjunto():
    assert '"[ ]+"' in n.compress("row1.x")
    assert '"[12]+"' in n.compress("row1.x", "12")
    assert '"[^ABCD]+"' in n.compress("row1.x", "ABCD", "k")


def test_compress_con_clase_d_y_clase_s_usa_escapes_de_regex():
    assert '"[0123456789]+"' in n.compress("row1.x", "", "d")
    expresion = n.compress("row1.x", None, "s")
    assert "\\\\u0009" in expresion  # dos barras en el .java -> \u0009 para el motor de regex
    assert "\t" not in expresion  # ningún carácter de control crudo en el código generado
    assert "\\\\u000a" in expresion


def test_compress_con_i_anade_el_otro_caso():
    expresion = n.compress("row1.x", "a", "i")
    assert "A" in expresion and "a" in expresion


def test_upcase_y_lowcase_no_dependen_del_locale_del_motor():
    assert "toUpperCase(java.util.Locale.ROOT)" in n.upcase("row1.x")
    assert "toLowerCase(java.util.Locale.ROOT)" in n.lowcase("row1.x")


def test_normalizar_nombre_compone_upcase_strip_y_compbl():
    expresion = n.normalizar_nombre("row1.x")
    assert "toUpperCase" in expresion
    assert '"^ +| +$"' in expresion
    assert '" +", " "' in expresion


def test_as_text_convierte_el_faltante_en_cadena_vacia():
    cuerpo = n.input_left_wd("row1.x", 6, 2)
    assert n.as_text(cuerpo) == f'java.util.Objects.toString({cuerpo}, "")'
