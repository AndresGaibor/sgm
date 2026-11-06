"""Pruebas del traductor de expresiones SAS a Java de Talend (WP-A4).

Cada función del mapeo tiene aquí el Java que debe emitir. Además, una prueba de contrato comprueba que **todo** lo que se
emite son rutinas de sistema que cualquier proyecto de Studio 8.0 trae de fábrica: si alguien inventa un método, la prueba
falla. No hay rutina propia que instalar.
"""

import re

import pytest

from sgm.expressions.talend_translator import (
    Unsupported,
    translate_to_talend,
)

#: Firmas de las rutinas de sistema de Studio 8.0 que usa el traductor, leídas de la instalación.
TALEND_SIGNATURES = {
    "StringHandling.UPCASE",
    "StringHandling.DOWNCASE",
    "StringHandling.TRIM",
    "StringHandling.RTRIM",
    "StringHandling.LTRIM",
    "StringHandling.CHANGE",
    "StringHandling.COUNT",
    "StringHandling.LEN",
    "StringHandling.EREPLACE",
    "StringHandling.LPAD",
    "TalendDate.getCurrentDate",
    "TalendDate.parseDate",
    "TalendDate.parseDateLocale",
    "TalendDate.formatDate",
    "TalendDate.addDate",
    "TalendDate.diffDate",
    "TalendDate.getPartOfDate",
    "TalendDate.getFirstDayOfMonth",
    "TalendDate.getLastDayOfMonth",
    "Mathematical.SQRT",
    "Mathematical.EXP",
    "Mathematical.LN",
    "Mathematical.MOD",
    "Mathematical.REAL",
    "Relational.ISNULL",
}


def java(sas: str) -> str:
    return translate_to_talend(sas).java


def test_texto_usa_las_rutinas_de_talend():
    assert java("upcase(nombre)") == "StringHandling.UPCASE(input_row.nombre)"
    assert java("lowcase(x)") == "StringHandling.DOWNCASE(input_row.x)"
    assert java("strip(x)") == "StringHandling.TRIM(input_row.x)"
    assert java("trim(x)") == "StringHandling.RTRIM(input_row.x)"
    assert java("left(x)") == "StringHandling.LTRIM(input_row.x)"
    assert java("tranwrd(x,'a','b')") == 'StringHandling.CHANGE(input_row.x, "a", "b")'
    assert java("count(x,'a')") == 'StringHandling.COUNT(input_row.x, "a")'


def test_longitud_y_conteo_de_caracteres():
    assert java("length(x)") == (
        "(input_row.x == null ? null : StringHandling.LEN(StringHandling.RTRIM(input_row.x)))"
    )
    assert java("lengthc(x)") == "(input_row.x == null ? null : StringHandling.LEN(input_row.x))"


def test_concatenacion_respeta_el_perdido():
    assert java("a || b") == (
        '((input_row.a == null ? "" : input_row.a) + (input_row.b == null ? "" : input_row.b))'
    )
    assert java("cats(a,b)") == (
        '(StringHandling.TRIM((input_row.a == null ? "" : input_row.a))'
        ' + StringHandling.TRIM((input_row.b == null ? "" : input_row.b)))'
    )
    assert java("catx('-',a,b)") == (
        'String.join("-", java.util.stream.Stream.of('
        'StringHandling.TRIM((input_row.a == null ? "" : input_row.a)), '
        'StringHandling.TRIM((input_row.b == null ? "" : input_row.b))'
        ").filter(s -> !s.isEmpty()).toArray(String[]::new))"
    )


def test_recorte_de_texto():
    assert java("substr(x,1,3)") == (
        "(input_row.x == null ? null : input_row.x.substring((int) 1 - 1, (int) (1 - 1 + 3)))"
    )
    assert (
        java("substr(x,2)") == "(input_row.x == null ? null : input_row.x.substring((int) 2 - 1))"
    )
    assert java("compress(x)") == (
        '(input_row.x == null ? null : StringHandling.CHANGE(input_row.x, " ", ""))'
    )
    assert java("compress(x,'ABCD','k')").startswith("(input_row.x == null ? null : ")
    assert "replaceAll" in java("compress(x,'ABCD','k')")
    assert "\\Q" in java("compress(x,'ABCD','k')")
    assert "[0-9]" in java("compress(x,'','d')")
    assert "(?i:" in java("compress(x,'a','i')")
    assert java("compress(x,'','k')") == '(input_row.x == null ? null : "")'
    assert (
        java("compbl(x)")
        == '(input_row.x == null ? null : StringHandling.EREPLACE(input_row.x, " +", " "))'
    )
    assert java("reverse(x)") == (
        "(input_row.x == null ? null : new StringBuilder(input_row.x).reverse().toString())"
    )


def test_scan_usa_tokens_y_devuelve_blanco_si_no_hay_esa_palabra():
    result = translate_to_talend("scan(x,2)")
    assert 'replaceAll("^[\\\\s!$%&()*+,\\\\-./;\\\\x3c^]+", "")' in result.java
    assert '.split("[\\\\s!$%&()*+,\\\\-./;\\\\x3c^]+")' in result.java
    assert "java.util.Arrays.stream" in result.java
    assert ".skip(1).findFirst().orElse(\"\")" in result.java
    assert ".length >=" not in result.java
    assert any("delimitadores" in w for w in result.warnings)


def test_scan_con_delimitador_literal_y_cero_devuelve_blanco():
    assert ".split(" in java("scan(x,2,',')")
    with pytest.raises(Unsupported, match="distinta de cero"):
        java("scan(x,0,',')")


def test_index_es_base_uno():
    assert java("index(x,'a')") == '(input_row.x.indexOf("a") + 1)'


def test_aritmetica_propaga_el_perdido():
    assert java("a + b") == (
        "(input_row.a == null || input_row.b == null ? null : Double.valueOf("
        "((Number) input_row.a).doubleValue() + ((Number) input_row.b).doubleValue()))"
    )
    assert java("a / b") == (
        "((input_row.a == null || input_row.b == null ? null : "
        "(((Number) input_row.b).doubleValue() == 0 ? null : Double.valueOf("
        "((Number) input_row.a).doubleValue() / ((Number) input_row.b).doubleValue()))))"
    )


def test_redondeo_de_sas_va_fuera_del_cero():
    assert java("round(a)") == (
        "(input_row.a == null ? null : Double.valueOf(((Number) input_row.a).doubleValue() < 0 "
        "? -Math.round(-((Number) input_row.a).doubleValue()) "
        ": Math.round(((Number) input_row.a).doubleValue())))"
    )


def test_matematicas_usan_la_rutina_matematica():
    assert java("sqrt(a)") == "Mathematical.SQRT(input_row.a)"
    assert java("mod(a,2)") == "Mathematical.MOD(input_row.a, 2)"
    assert java("abs(a)") == (
        "(input_row.a == null ? null : Double.valueOf(Math.abs(((Number) input_row.a).doubleValue())))"
    )
    assert (
        java("int(a)")
        == "(input_row.a == null ? null : Long.valueOf(((Number) input_row.a).longValue()))"
    )


def test_agregados_ignoran_perdidos_y_el_maximo_vacio_es_perdido():
    assert java("sum(a,b,.)") == (
        "Double.valueOf((input_row.a == null ? 0 : ((Number) input_row.a).doubleValue()) "
        "+ (input_row.b == null ? 0 : ((Number) input_row.b).doubleValue()))"
    )
    assert java("n(a,.)") == "((input_row.a != null ? 1 : 0))"
    assert java("max(a,b)") == (
        "(input_row.a == null && input_row.b == null ? null : Double.valueOf("
        "(input_row.a == null ? ((Number) input_row.b).doubleValue() : Math.max("
        "((Number) input_row.a).doubleValue(), ((Number) input_row.b).doubleValue()))))"
    )


def test_condicionales():
    assert java("coalesce(a,.)") == "(input_row.a != null ? input_row.a : null)"
    assert java("ifn(x,1,2)") == (
        "((input_row.x != null && ((Number) input_row.x).doubleValue() != 0) ? 1 : 2)"
    )
    assert java("case when x = 1 then 'uno' else 'otro' end") == (
        '((input_row.x != null && ((Number) input_row.x).doubleValue() == 1) ? "uno" : "otro")'
    )
    assert java("case x when 1 then 'a' when 2 then 'b' end") == (
        '((input_row.x != null && ((Number) input_row.x).doubleValue() == 1) ? "a" : '
        '((input_row.x != null && ((Number) input_row.x).doubleValue() == 2) ? "b" : null))'
    )


def test_perdido_de_sas_en_comparaciones():
    """En SAS el perdido es el menor: `x < 5` es cierto con x perdido y `x > 5` no."""
    assert java("x = .") == "Relational.ISNULL(input_row.x)"
    assert java("x is missing") == "Relational.ISNULL(input_row.x)"
    assert java("missing(x)") == "Relational.ISNULL(input_row.x)"
    assert java("x < 5") == "(input_row.x == null || ((Number) input_row.x).doubleValue() < 5)"
    assert java("x > 5") == "(input_row.x != null && ((Number) input_row.x).doubleValue() > 5)"
    assert java("x is not missing") == "!Relational.ISNULL(input_row.x)"


def test_comparaciones_con_literal():
    assert java("x = 'A'") == '"A".equals(input_row.x)'
    assert java("x = 5") == "(input_row.x != null && ((Number) input_row.x).doubleValue() == 5)"
    assert java("x in (1,2)") == (
        "((input_row.x != null && ((Number) input_row.x).doubleValue() == 1) || "
        "(input_row.x != null && ((Number) input_row.x).doubleValue() == 2))"
    )
    assert java("x between 1 and 3") == (
        "((input_row.x != null && ((Number) input_row.x).doubleValue() >= 1) && "
        "(input_row.x == null || ((Number) input_row.x).doubleValue() <= 3))"
    )
    assert java("x like 'A%'") == '(input_row.x != null && input_row.x.matches("A.*"))'


def test_fechas_usan_talenddate():
    assert java("today()") == "TalendDate.getCurrentDate()"
    assert java("datetime()") == "TalendDate.getCurrentDate()"
    assert java("'01JAN2020'd") == 'TalendDate.parseDateLocale("ddMMMyyyy", "01JAN2020", "en")'
    assert java("input(f,yymmdd10.)") == 'TalendDate.parseDate("yyyy-MM-dd", input_row.f)'
    assert java("put(d,yymmdd10.)") == 'TalendDate.formatDate("yyyy-MM-dd", input_row.d)'
    assert (
        java("year(d)")
        == '(input_row.d == null ? null : (TalendDate.getPartOfDate("YEAR", input_row.d)))'
    )
    assert java("month(d)") == (
        '(input_row.d == null ? null : (TalendDate.getPartOfDate("MONTH", input_row.d) + 1))'
    )
    assert java("weekday(d)") == (
        '(input_row.d == null ? null : (TalendDate.getPartOfDate("DAY_OF_WEEK", input_row.d)))'
    )
    assert java("intnx('month',fecha,1)") == (
        "(input_row.fecha == null ? null : TalendDate.getFirstDayOfMonth("
        'TalendDate.addDate(input_row.fecha, (int) 1, "MM")))'
    )
    assert java("intnx('month',d,2,'e')") == (
        "(input_row.d == null ? null : TalendDate.getLastDayOfMonth("
        'TalendDate.addDate(input_row.d, (int) 2, "MM")))'
    )
    assert java("intck('month',a,b)") == (
        "(input_row.a == null || input_row.b == null ? null : Long.valueOf("
        'TalendDate.diffDate(input_row.b, input_row.a, "MM")))'
    )
    assert java("mdy(1,15,2020)") == (
        '(TalendDate.parseDate("yyyy-MM-dd", String.format("%04d-%02d-%02d", (int) 2020, (int) 1, (int) 15)))'
    )


def test_formato_cero_rellena_a_la_izquierda():
    assert java("put(n,z8.)") == 'StringHandling.LPAD(String.valueOf(input_row.n), 8, "0")'


def test_macrovariable_va_a_contexto_y_avisa():
    result = translate_to_talend("&anio")
    assert result.java == "context.sas_param_anio"
    assert result.warnings == [
        "Macrovariable &anio -> context.sas_param_anio (crear la variable de contexto)"
    ]


def test_columnas_leidas_se_devuelven_para_el_esquema():
    assert translate_to_talend("cats(a, b) = 'X'").columns == ["a", "b"]


def test_funciones_sas_de_la_expresion_se_devuelven_sin_duplicados():
    result = translate_to_talend("strip(scan(x, 2)) + length(x)")

    assert result.functions == ["length", "scan", "strip"]


@pytest.mark.parametrize(
    "sas",
    [
        "lag(x)",  # estado entre filas: no es una expresion
        "dif(x)",
        "put(n, best32.)",  # formato sin traduccion segura
        "scan(x, &pos)",  # posicion que no es literal
        "compress(x, &chars)",
        "x like &patron",
        "foo(x)",  # funcion que no existe en el mapeo
    ],
)
def test_lo_no_traducible_queda_como_pendiente(sas):
    with pytest.raises(Unsupported):
        translate_to_talend(sas)


def test_solo_se_emiten_rutinas_de_sistema_de_studio():
    """Contrato: nada propio que instalar, ningun metodo inventado."""
    expressions = [
        "upcase(x)",
        "lowcase(x)",
        "strip(x)",
        "trim(x)",
        "left(x)",
        "tranwrd(x,'a','b')",
        "count(x,'a')",
        "length(x)",
        "lengthc(x)",
        "lengthn(x)",
        "compbl(x)",
        "reverse(x)",
        "cats(a,b)",
        "catx('-',a,b)",
        "compress(x,'kd')",
        "substr(x,1,2)",
        "scan(x,1)",
        "index(x,'a')",
        "sqrt(a)",
        "exp(a)",
        "log(a)",
        "mod(a,2)",
        "input(f,yymmdd10.)",
        "put(d,yymmdd10.)",
        "put(n,z8.)",
        "today()",
        "mdy(1,1,2020)",
        "datepart(dt)",
        "intnx('year',d,1)",
        "intck('year',a,b)",
        "year(d)",
        "month(d)",
        "day(d)",
        "weekday(d)",
        "x is missing",
    ]
    for sas in expressions:
        for owner, method in re.findall(r"\b([A-Z]\w+)\.(\w+)\(", java(sas)):
            if owner in {
                "Math", "Double", "Long", "String", "StringBuilder", "Stream", "Arrays", "Objects"
            }:
                continue  # Java nativo, no requiere nada instalado
            assert f"{owner}.{method}" in TALEND_SIGNATURES, (
                f"{sas} emite {owner}.{method}, que no esta en Studio 8.0"
            )
        assert "SasFunctions" not in java(sas)


def test_la_entrada_del_tmap_usa_el_nombre_real_de_la_conexion():
    # En Studio la variable de entrada es el nombre de la conexión (row1, row_origen_a_map...), no `input_row`.
    r = translate_to_talend("upcase(campo_txt)", entrada="row_origen_a_map")
    assert "row_origen_a_map.campo_txt" in r.java
    assert "input_row" not in r.java
    assert r.columns == ["campo_txt"]


def test_el_nombre_de_conexion_invalido_se_rechaza():
    with pytest.raises(Unsupported):
        translate_to_talend("upcase(campo_txt)", entrada="row 1; x")
