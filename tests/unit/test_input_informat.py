"""Pruebas de procedencia literal del informat de INPUT."""

import pytest

from sgm.compile import compile_project
from sgm.expressions.expressions import translate
from sgm.expressions.talend_translator import Unsupported, translate_to_talend


def test_dynamic_macro_informat_is_unsupported():
    with pytest.raises(Unsupported, match="informat"):
        translate_to_talend("input(value, &informat)")


def test_column_informat_is_unsupported():
    with pytest.raises(Unsupported, match="informat"):
        translate_to_talend("input(value, informat)")


def test_computed_informat_is_unsupported():
    with pytest.raises(Unsupported, match="informat"):
        translate_to_talend("input(value, cats('best', '32.'))")


def test_literal_numeric_informat_keeps_current_candidate():
    result = translate_to_talend("input(value, 10.)")
    assert result.java == (
        "(input_row.value == null ? null : "
        "Mathematical.REAL(StringHandling.TRIM(input_row.value)))"
    )
    assert any("input numérico" in warning for warning in result.warnings)


def test_literal_character_informat_keeps_current_result():
    assert translate_to_talend("input(value, $char10.)").java == "input_row.value"


def test_dynamic_informat_compiles_as_gap_without_candidate():
    plan = _plan("data target; set source; parsed=input(value, &informat); run;")
    operator = _derive_for(plan, "parsed")
    assert "talend_expression_candidates" not in operator.params
    assert any(g.reason == "FUNCION_NO_MAPEADA" for g in plan.gaps)


def test_macro_informat_resuelto_a_literal_sigue_traduciendose():
    plan = _plan(
        "%let fmt = yymmdd10.; data target; set source; parsed=input(value, &fmt); run;"
    )
    operator = _derive_for(plan, "parsed")
    expression = operator.params["assignments"][0]["expression"]
    assert expression == "input(value, yymmdd10.)"
    assert not any(g.reason == "FUNCION_NO_MAPEADA" for g in plan.gaps)
    result = translate(expression)
    assert result.engine == "inline"
    assert "TalendDate.parseDate(" in result.talend


def _plan(source):
    compiled, _ = compile_project({"program.sas": source})
    return compiled["program.sas"].plan


def _derive_for(plan, target):
    return next(
        operator
        for operator in plan.graph.operators()
        if operator.kind == "derive"
        and any(assignment["target"] == target for assignment in operator.params["assignments"])
    )


@pytest.mark.parametrize("informat", ["&private_marker", "private_marker", "'10.' || private_marker", "10. + 2"])
def test_dynamic_informat_error_does_not_echo_source(informat):
    with pytest.raises(Unsupported, match="informat") as error:
        translate_to_talend(f"input(value, {informat})")
    assert "private_marker" not in str(error.value)


@pytest.mark.parametrize("informat", ["'yymmdd10.'", '"yymmdd10."', "yymmdd10."])
def test_literal_date_informat_keeps_current_result(informat):
    result = translate_to_talend(f"input(value, {informat})")
    assert result.java == 'TalendDate.parseDate("yyyy-MM-dd", input_row.value)'


def test_numeric_literals_outside_formats_keep_numeric_kind():
    result = translate_to_talend("10. + 2.5")
    assert result.java == "(10. + 2.5)"
    assert result.kind == "num"


def test_integer_without_informat_dot_is_unsupported():
    with pytest.raises(Unsupported, match="informat"):
        translate_to_talend("input(value, 10)")
