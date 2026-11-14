"""Pruebas unitarias de traducción conservadora de funciones de fecha."""

import pytest

from sgm.expressions.expressions import translate
from sgm.expressions.talend_translator import Unsupported, translate_to_talend
from sgm.talend_item.desde_plan_expresiones import expresion


def test_intnx_year_begin_returns_calendar_year_boundary():
    result = translate_to_talend("intnx('year', date_value, 1)")

    assert 'TalendDate.formatDate("yyyy",' in result.java
    assert '+ "-01-01")' in result.java
    assert any("fecha SAS desde 1960" in warning for warning in result.warnings)


def test_intnx_year_end_returns_calendar_year_boundary():
    result = translate_to_talend("intnx('year', date_value, 1, 'end')")

    assert 'TalendDate.addDate(TalendDate.addDate(' in result.java
    assert ', 1, "yyyy"), -1, "dd")' in result.java


def test_intnx_year_same_emits_candidate_to_validate_leap_dates():
    java = translate_to_talend("intnx('year', date_value, 2, 'same')").java

    assert "Math.min(" in java
    assert 'TalendDate.getLastDayOfMonth(' in java


@pytest.mark.parametrize(
    ("expression", "motivo"),
    [
        ("intnx('month', date_value, 1, 'middle')", "P-INTNX-ALINEACION-M"),
        ("intnx('year', date_value, 1, 'middle')", "P-INTNX-ALINEACION-M"),
        ("intnx('month', date_value, 1, dynamic_alignment)", "P-INTNX-ALINEACION-DINAMICA"),
        ("intnx('hour', date_value, 1)", "P-INTNX-INTERVALO"),
        ("intnx('hour', date_value, 1, 'same')", "P-INTNX-INTERVALO"),
        ("intnx(dynamic_interval, date_value, 1)", "P-INTNX-INTERVALO"),
        ("intnx('year2', date_value, 1)", "P-INTNX-MULTIUNIDAD"),
        ("intnx('month.2', date_value, 1)", "P-INTNX-DESPLAZADO"),
        ("intnx('month', date_value, increment + 1)", "P-INTNX-INCREMENTO-NO-ENTERO"),
        ("intnx('month', date_value, 1.5)", "P-INTNX-INCREMENTO-NO-ENTERO"),
        ("intnx('week', date_value, 400000000, 'same')", "P-INTNX-RANGO-TALEND"),
        ("intnx('month', date_value, 'not_a_number')", "P-INTNX-INCREMENTO-TIPO"),
    ],
)
def test_intnx_deja_pendientes_las_formas_fuera_del_subconjunto(expression, motivo):
    with pytest.raises(Unsupported, match=motivo):
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

    assert '(int) (1.0)' in java


def test_intnx_no_trata_alineacion_vacia_como_beginning():
    with pytest.raises(Unsupported, match="P-INTNX-ALINEACION"):
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
    expected = translate_to_talend(
        expression, expected_kind="num" if expression.startswith("intnx") else None
    )

    assert result.talend == expected.java
    assert result.kind == expected.kind


def test_fachada_publica_emite_intnx_week_con_inicio_de_domingo(monkeypatch):
    monkeypatch.setenv("SGM_TALEND_EXPRESSIONS", "1")

    result = translate("intnx('week', date_value, 1)")

    assert result.talend is not None
    assert 'TalendDate.getPartOfDate("DAY_OF_WEEK"' in result.talend
    assert result.kind == "num"
    assert "TalendDate.diffDate(" in result.talend


def test_fachada_publica_devuelve_intnx_como_serial_sas_numerico(monkeypatch):
    monkeypatch.setenv("SGM_TALEND_EXPRESSIONS", "1")

    result = translate("intnx('month', fecha_sas, 1)")

    assert result.talend is not None
    assert result.kind == "num"
    assert "TalendDate.diffDate(" in result.talend


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
    assert "TalendDate.getCurrentDate()" in translate_to_talend("today()").java
    with pytest.raises(Unsupported, match="datetime"):
        translate_to_talend("datetime()")
    assert translate_to_talend("'01JAN2020'd").java == (
        'TalendDate.parseDateLocale("ddMMMyyyy", "01JAN2020", "en")'
    )
    assert translate_to_talend("put(d,yymmdd10.)").java == (
        'TalendDate.formatDate("yyyy-MM-dd", input_row.d)'
    )
    for funcion, parte in (("year", "YEAR"), ("month", "MONTH"), ("weekday", "DAY_OF_WEEK")):
        java = translate_to_talend(f"{funcion}(d)").java
        assert f'TalendDate.getPartOfDate("{parte}",' in java
        assert 'TalendDate.parseDate("yyyy-MM-dd", "1960-01-01")' in java
    mes = translate_to_talend("intnx('month',fecha,1)")
    assert mes.kind == "date"
    assert "TalendDate.getFirstDayOfMonth(" in mes.java
    assert 'TalendDate.parseDate("yyyy-MM-dd", "1960-01-01")' in mes.java
    assert "TalendDate.diffDate(" not in mes.java
    fin_mes = translate_to_talend("intnx('month',d,2,'e')")
    assert "TalendDate.getLastDayOfMonth(" in fin_mes.java
    assert '(int) (2)' in fin_mes.java
    mdy = translate_to_talend("mdy(1,15,2020)").java
    assert 'String.format(java.util.Locale.ROOT, "%04d-%02d-%02d"' in mdy
    assert "Math.rint(2020)" in mdy


def test_guardas_internas_de_conversion_fecha_no_se_confunden_con_comparaciones_sas():
    java, motivo = expresion(
        "year(fecha)",
        {"row1": {"fecha"}},
        {"row1.fecha": "id_Double"},
    )

    assert motivo is None
    assert java is not None
    assert 'TalendDate.getPartOfDate("YEAR",' in java


def test_comparacion_de_orden_sas_con_fecha_sigue_pendiente_si_falta_semantica():
    java, motivo = expresion(
        "year(fecha) > 2020",
        {"row1": {"fecha"}},
        {"row1.fecha": "id_Double"},
    )

    assert java is None
    assert "comparación de orden" in (motivo or "")


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
