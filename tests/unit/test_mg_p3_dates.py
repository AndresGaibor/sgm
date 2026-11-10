"""Pruebas unitarias de traducción conservadora de funciones de fecha."""

import pytest

from sgm.expressions.expressions import translate
from sgm.expressions.talend_translator import Unsupported, translate_to_talend


def test_intnx_year_begin_returns_calendar_year_boundary():
    result = translate_to_talend("intnx('year', date_value, 1)")

    assert 'TalendDate.formatDate("yyyy", TalendDate.addDate(' in result.java
    assert '+ "-01-01")' in result.java
    assert any("SAS Date" in warning for warning in result.warnings)
    assert any("época SAS" in warning for warning in result.warnings)


def test_intnx_year_end_returns_calendar_year_boundary():
    result = translate_to_talend("intnx('year', date_value, 1, 'end')")

    assert '+ "-12-31")' in result.java


def test_intnx_year_same_emits_candidate_to_validate_leap_dates():
    java = translate_to_talend("intnx('year', date_value, 2, 'same')").java

    assert 'TalendDate.addDate(input_row.date_value, (int) 2, "yyyy")' in java


@pytest.mark.parametrize(
    "expression",
    [
        "intnx('month', date_value, 1, 'middle')",
        "intnx('year', date_value, 1, 'middle')",
        "intnx('week', date_value, 1)",
        "intnx('week', date_value, 1, 'beginning')",
        "intnx('month', date_value, 1, dynamic_alignment)",
        "intnx('hour', date_value, 1)",
        "intnx('hour', date_value, 1, 'same')",
        "intnx(dynamic_interval, date_value, 1)",
        "intnx('year2', date_value, 1)",
        "intnx('month', date_value, increment + 1)",
        "intnx('month', date_value, 1.5)",
        "intnx('week', date_value, 400000000, 'same')",
        "intnx('month', 20000, 1)",
        "intnx('month', date_value, 'not_a_number')",
    ],
)
def test_intnx_deja_pendiente_la_semantica_no_modelada(expression):
    with pytest.raises(Unsupported, match="pendiente"):
        translate_to_talend(expression)


def test_intnx_propaga_incremento_perdido_antes_de_sumar_intervalos():
    java = translate_to_talend("intnx('month', date_value, increment)").java

    assert "input_row.date_value == null || input_row.increment == null ? null" in java
    assert "Integer.MIN_VALUE" in java
    assert "Integer.MAX_VALUE" in java
    assert "Double.isFinite" in java
    assert "Math.rint" in java


def test_intnx_acepta_incremento_literal_decimal_si_es_entero():
    java = translate_to_talend("intnx('month', date_value, 1.0)").java

    assert '(int) 1.0' in java


def test_intnx_no_trata_alineacion_vacia_como_beginning():
    with pytest.raises(Unsupported, match="alineación"):
        translate_to_talend("intnx('month', date_value, 1, '')")


def test_intnx_week_limita_el_incremento_antes_de_multiplicar_por_siete():
    java = translate_to_talend("intnx('week', date_value, increment, 'same')").java

    assert "Integer.MIN_VALUE / 7.0" in java
    assert "Integer.MAX_VALUE / 7.0" in java


def test_intck_month_emite_formula_de_limites_discretos():
    java = translate_to_talend("intck('month', start_date, end_date)").java

    assert "TalendDate.diffDate" not in java
    assert 'TalendDate.getPartOfDate("YEAR", input_row.end_date)' in java
    assert 'TalendDate.getPartOfDate("MONTH", input_row.end_date)' in java
    assert "Long.valueOf" in java
    result = translate_to_talend("intck('month', start_date, end_date)")
    assert any("intervalos SAS Date discretos" in warning for warning in result.warnings)
    assert any("época SAS" in warning for warning in result.warnings)


def test_intck_year_emite_formula_de_limites_discretos():
    java = translate_to_talend("intck('year', start_date, end_date)").java

    assert 'TalendDate.getPartOfDate("YEAR", input_row.end_date)' in java
    assert 'TalendDate.getPartOfDate("YEAR", input_row.start_date)' in java


def test_intck_day_usa_fin_menos_inicio_en_unidad_dias():
    java = translate_to_talend("intck('day', start_date, end_date)").java

    assert 'TalendDate.diffDate(input_row.end_date, input_row.start_date, "dd")' in java


@pytest.mark.parametrize(
    "expression",
    [
        "intnx('month', date_value, 1)",
        "intck('month', start_date, end_date)",
    ],
)
def test_fachada_publica_delega_fechas_al_traductor_activo(expression, monkeypatch):
    monkeypatch.setenv("SGM_TALEND_EXPRESSIONS", "1")

    result = translate(expression)
    expected = translate_to_talend(expression)

    assert result.talend == expected.java
    assert result.kind == expected.kind


def test_fachada_publica_no_emite_intnx_week_default_con_alineacion_incorrecta(monkeypatch):
    monkeypatch.setenv("SGM_TALEND_EXPRESSIONS", "1")

    result = translate("intnx('week', date_value, 1)")

    assert result.talend is None
    assert any("WEEKSTART" in warning for warning in result.warnings)


@pytest.mark.parametrize("method", ["discrete", "d", "disc"])
def test_intck_acepta_aliases_del_metodo_discreto(method):
    java = translate_to_talend(
        f"intck('month', start_date, end_date, '{method}')"
    ).java

    assert 'TalendDate.getPartOfDate("YEAR", input_row.end_date)' in java
    assert 'TalendDate.getPartOfDate("MONTH", input_row.end_date)' in java


@pytest.mark.parametrize("method", ["continuous", "c", "cont", "guess"])
def test_intck_metodo_no_discreto_no_se_presenta_como_equivalente(method):
    with pytest.raises(Unsupported, match="método"):
        translate_to_talend(
            f"intck('month', start_date, end_date, '{method}')"
        )


def test_otras_funciones_de_fecha_conservan_las_rutinas_disponibles():
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
    assert translate_to_talend("mdy(1,15,2020)").java == (
        '(TalendDate.parseDate("yyyy-MM-dd", String.format("%04d-%02d-%02d", (int) 2020, (int) 1, (int) 15)))'
    )


@pytest.mark.parametrize(
    "expression",
    [
        "intck('week', start_date, end_date)",
        "intck('hour', start_date, end_date)",
        "intck('month', start_date, end_date, 'continuous')",
        "intck('month', 20000, 20030)",
    ],
)
def test_intck_no_inventa_semantica_de_metodo_o_intervalo(expression):
    with pytest.raises(Unsupported):
        translate_to_talend(expression)


@pytest.mark.parametrize("function", ["datdif", "yrdif"])
def test_diferencias_financieras_siguen_pendientes_hasta_modelar_basis(function):
    with pytest.raises(Unsupported):
        translate_to_talend(f"{function}(start_date, end_date, 'act/act')")
