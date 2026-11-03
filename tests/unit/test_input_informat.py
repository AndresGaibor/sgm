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


@pytest.mark.parametrize("function", ["input", "inputn"])
@pytest.mark.parametrize("informat", ['"&private_marker"', '"best&private_marker.."'])
def test_double_quoted_macro_informat_stays_dynamic(function, informat):
    with pytest.raises(Unsupported, match="informat") as error:
        translate_to_talend(f"{function}(value, {informat})")
    assert "private_marker" not in str(error.value)
    plan = _plan(f"data target; set source; parsed={function}(value, {informat}); run;")
    assert "talend_expression_candidates" not in _derive_for(plan, "parsed").params
    assert any(g.reason == "FUNCION_NO_MAPEADA" for g in plan.gaps)


@pytest.mark.parametrize("function", ["input", "inputn"])
def test_single_quoted_macro_text_keeps_literal_behavior(function):
    assert translate_to_talend(f"{function}(value, '&private_marker')").warnings


def test_expanded_double_quoted_macro_informat_stays_literal():
    plan = _plan('%let fmt = yymmdd10.; data target; set source; parsed=input(value, "&fmt"); run;')
    expression = _derive_for(plan, "parsed").params["assignments"][0]["expression"]
    assert expression == 'input(value, "yymmdd10.")'
    assert "TalendDate.parseDate(" in translate(expression).talend
    assert not any(g.reason == "FUNCION_NO_MAPEADA" for g in plan.gaps)


@pytest.mark.parametrize("informat", ["row.informat", "e8601da. || row.informat"])
def test_qualified_column_or_composed_informat_stays_dynamic(informat):
    with pytest.raises(Unsupported, match="informat"):
        translate_to_talend(f"input(value, {informat})")


def test_lexing_failure_does_not_echo_informat_source():
    with pytest.raises(Unsupported) as error:
        translate_to_talend("input(value, %secret42())")
    assert "secret42" not in str(error.value)


@pytest.mark.parametrize("filter_step", ["", "  where enabled = 1;\n"])
def test_dynamic_assignment_gap_has_precise_file_and_lines(filter_step):
    source = "data target;\n  set source;\n" + filter_step + "  kept = 1;\n  parsed = input(\n    value, &informat);\nrun;"
    plan = _plan(source)
    gap = next(g for g in plan.gaps if g.reason == "FUNCION_NO_MAPEADA")
    start = 5 if filter_step else 4
    assert [(e.file, e.line_start, e.line_end) for e in gap.evidence] == [("program.sas", start, start + 1)]


@pytest.mark.parametrize("function,method", [("input", "parseDate"), ("put", "formatDate")])
@pytest.mark.parametrize("format_name,pattern", [("e8601da.", "yyyy-MM-dd"), ("e8601dt.", "yyyy-MM-dd'T'HH:mm:ss")])
def test_iso_literal_formats_keep_previous_java(function, method, format_name, pattern):
    assert translate_to_talend(f"{function}(value, {format_name})").java == f'TalendDate.{method}("{pattern}", input_row.value)'



def test_translation_wrapper_lexing_diagnostics_do_not_echo_source():
    result = translate("input(value, %secret42())")
    assert result.talend is None
    assert result.warnings
    assert "secret42" not in " ".join(result.warnings)
