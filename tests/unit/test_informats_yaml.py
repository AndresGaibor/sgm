"""Informats desde `rules/sas/informats.yaml` (F1.4): los nombres y umbrales vienen del archivo."""

from sgm.ir import types_code


def test_los_nombres_de_fecha_del_yaml_dan_date():
    for nombre in ("yymmdd8.", "ddmmyy10.", "datetime20.", "monyy7."):
        assert types_code.informat_type(nombre) == types_code.CodeType("Date"), nombre


def test_el_umbral_numerico_sale_del_yaml():
    assert types_code.numeric_type(18, 0) == types_code.CodeType("Long")
    assert types_code.numeric_type(19, 0) == types_code.CodeType("Double")
    assert types_code.numeric_type(6, 2) == types_code.CodeType("BigDecimal")


def test_el_informat_de_caracter_usa_la_marca_del_yaml():
    assert types_code.informat_type("$10.") == types_code.CodeType("String", 10)
    assert types_code.informat_type("char8.") == types_code.CodeType("String", 8)
