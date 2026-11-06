"""Contrato de las rutinas de sistema emitidas para Talend Studio 8.0."""

import re

from sgm.expressions.talend_translator import translate_to_talend

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


def test_solo_se_emiten_rutinas_de_sistema_de_studio():
    """No genera métodos inventados ni requiere instalar funciones propias."""
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
        "input(f,e8601da10.)",
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
        java = translate_to_talend(sas).java
        for owner, method in re.findall(r"\b([A-Z]\w+)\.(\w+)\(", java):
            if owner in {
                "Math",
                "Double",
                "Long",
                "String",
                "StringBuilder",
                "Stream",
                "Arrays",
                "Objects",
            }:
                continue  # Java nativo, no requiere nada instalado
            assert f"{owner}.{method}" in TALEND_SIGNATURES, (
                f"{sas} emite {owner}.{method}, que no está en Studio 8.0"
            )
        assert "SasFunctions" not in java
