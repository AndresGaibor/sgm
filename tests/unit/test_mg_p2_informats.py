"""Vectores de informats SAS para MG-P2-03."""

import pytest

from sgm.compile import compile_project
from sgm.expressions.talend_translator import Unsupported, translate_to_talend
from sgm.frontend.datastep import classify_statement
from sgm.ir.types_code import CodeType, expression_type, informat_type


@pytest.mark.parametrize("target", ["label", "format", "informat", "length", "attrib"])
def test_asignacion_con_nombre_de_declaracion_no_se_confunde_con_declaracion(target):
    statement = classify_statement(f"{target}=source_value", 1)

    assert statement.kind == "assign"
    assert statement.fields["target"] == target


def test_put_pendiente_no_se_pierde_en_asignacion_a_variable_label():
    source = "data target; set source; label=put(amount,comma12.2); run;"
    compiled, _ = compile_project({"program.sas": source})
    plan = compiled["program.sas"].plan
    derive = next(op for op in plan.graph.operators() if op.kind == "derive")

    assert derive.params["assignments"] == [
        {"target": "label", "expression": "put(amount,comma12.2)"}
    ]
    assert any(gap.reason == "FUNCION_NO_MAPEADA" for gap in plan.gaps)


def test_tipado_de_informats_conserva_la_semantica_documentada():
    assert informat_type("anydtdte10.") == CodeType("Date")
    assert informat_type("comma12.2") == CodeType("BigDecimal")
    assert informat_type("dollar18.2") == CodeType("BigDecimal")
    assert informat_type("8.") == CodeType("Double")
    assert expression_type("input(valor, 8.)") == CodeType("Double")
    assert informat_type("unknown12.") is None


@pytest.mark.parametrize(
    "informat", ["anydtdte10.", "yymmdd8.", "yymmdd10.", "ddmmyy10.", "date9."]
)
def test_informats_de_fecha_quedan_pendientes_si_faltan_opciones_sas(informat):
    with pytest.raises(Unsupported, match="opciones de fecha"):
        translate_to_talend(f"input(valor, {informat})")


def test_fecha_iso_extendida_tiene_una_conversion_determinista():
    result = translate_to_talend("input(fecha, e8601da10.)")

    assert result.java == 'TalendDate.parseDate("yyyy-MM-dd", input_row.fecha)'


def test_funciones_de_fecha_conservan_las_rutinas_talend_validadas():
    assert translate_to_talend("today()").java == "TalendDate.getCurrentDate()"
    assert translate_to_talend("datetime()").java == "TalendDate.getCurrentDate()"
    assert translate_to_talend("'01JAN2020'd").java == (
        'TalendDate.parseDateLocale("ddMMMyyyy", "01JAN2020", "en")'
    )
    assert translate_to_talend("put(d,yymmdd10.)").java == (
        'TalendDate.formatDate("yyyy-MM-dd", input_row.d)'
    )
    assert translate_to_talend("year(d)").java == (
        '(input_row.d == null ? null : (TalendDate.getPartOfDate("YEAR", input_row.d)))'
    )
    assert translate_to_talend("month(d)").java == (
        '(input_row.d == null ? null : (TalendDate.getPartOfDate("MONTH", input_row.d) + 1))'
    )
    assert translate_to_talend("weekday(d)").java == (
        '(input_row.d == null ? null : (TalendDate.getPartOfDate("DAY_OF_WEEK", input_row.d)))'
    )
    assert translate_to_talend("intnx('month',fecha,1)").java == (
        "(input_row.fecha == null ? null : TalendDate.getFirstDayOfMonth("
        'TalendDate.addDate(input_row.fecha, (int) 1, "MM")))'
    )
    assert translate_to_talend("intnx('month',d,2,'e')").java == (
        "(input_row.d == null ? null : TalendDate.getLastDayOfMonth("
        'TalendDate.addDate(input_row.d, (int) 2, "MM")))'
    )
    assert translate_to_talend("intck('month',a,b)").java == (
        "(input_row.a == null || input_row.b == null ? null : Long.valueOf("
        'TalendDate.diffDate(input_row.b, input_row.a, "MM")))'
    )
    assert translate_to_talend("mdy(1,15,2020)").java == (
        '(TalendDate.parseDate("yyyy-MM-dd", String.format("%04d-%02d-%02d", (int) 2020, (int) 1, (int) 15)))'
    )


def test_informat_comma_usa_limpieza_y_escala_decimal_del_manual_sas():
    result = translate_to_talend("input(importe, comma12.2)")

    assert "new java.math.BigDecimal(" in result.java
    assert '.replace(",", "")' in result.java
    assert '.replace("$", "")' in result.java
    assert '.replace("%", "")' in result.java
    assert ".movePointLeft(" in result.java
    assert 'matches("[0-9,$%() .-]+")' in result.java
    assert 'matches("(?:[0-9]+(?:\\\\.[0-9]*)?|\\\\.[0-9]+)")' in result.java
    assert '.contains(".")' in result.java


def test_informat_dollar_es_alias_del_informat_comma():
    comma = translate_to_talend("input(importe, comma12.2)")
    dollar = translate_to_talend("input(importe, dollar12.2)")

    assert dollar.java == comma.java


def test_informat_numerico_desconocido_no_se_convierte_con_realm():
    with pytest.raises(Unsupported, match="informat no soportado"):
        translate_to_talend("input(valor, mystery12.)")


@pytest.mark.parametrize(
    "expression", ['input(valor, "private_marker")', 'put(valor, "private_marker")']
)
def test_formato_no_soportado_no_repite_el_literal_de_entrada(expression):
    with pytest.raises(Unsupported) as error:
        translate_to_talend(expression)

    assert "private_marker" not in str(error.value)


def test_put_numerico_con_separadores_sigue_pendiente():
    with pytest.raises(Unsupported, match="formato"):
        translate_to_talend("put(importe, comma12.2)")
