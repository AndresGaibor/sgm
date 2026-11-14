from __future__ import annotations

import pytest

from sgm.compile import compile_file, project_base
from sgm.expressions.talend_translator import translate_to_talend
from sgm.formatos.informat_archivo import leer_campo
from sgm.formatos.informat_fecha import dias_sas, informat_fecha_soportado, leer_fecha
from sgm.frontend.program import analyze_program
from sgm.ir.types_code import CodeType, informat_type
from sgm.migrar.esquemas import esquemas_de_entrada
from sgm.migrar.interprete_errores import NoSoportadoEnInterprete
from sgm.migrar.interprete_infile import leer_lista
from sgm.talend_item.desde_plan import plan_a_jobs

PROGRAMA = (
    "data work.fechas;\n"
    "infile '/datos/fechas.txt' dlm=';' dsd missover;\n"
    "input id :$1. d1 :YYMMDD10. d2 :DDMMYY10. d3 :DATE9. d4 :ANYDTDTE10.;\n"
    "run;\n"
    "proc export data=work.fechas outfile='/datos/fechas.csv' dbms=csv replace;\n"
    "run;"
)


def _plan(text: str = PROGRAMA):
    analysis = analyze_program({"programa.sas": text})
    return compile_file(analysis, "programa.sas", project_base()).plan


@pytest.mark.parametrize(
    ("year", "month", "day", "expected"),
    [(1960, 1, 1, 0), (2000, 1, 1, 14610), (2026, 9, 28, 24377)],
)
def test_dias_sas_usa_la_epoca_documentada(year, month, day, expected):
    assert dias_sas(year, month, day) == expected


@pytest.mark.parametrize(
    ("text", "informat"),
    [
        ("2026-09-28", "YYMMDD10."),
        ("20260928", "YYMMDD8."),
        ("28/09/2026", "DDMMYY10."),
        ("28SEP2026", "DATE9."),
        ("28sep2026", "DATE9."),
        ("2026-09-28", "ANYDTDTE10."),
    ],
)
def test_leer_fecha_convierte_los_formatos_de_cuatro_digitos(text, informat):
    assert leer_fecha(text, informat) == 24377


def test_leer_fecha_devuelve_faltante_para_fecha_invalida_documentada():
    assert leer_fecha("2023-02-29", "YYMMDD10.") is None


def test_leer_fecha_acepta_separadores_especiales_documentados():
    assert leer_fecha("2026/09-28", "YYMMDD10.") == 24377


@pytest.mark.parametrize(
    ("text", "informat"),
    [("240229", "YYMMDD8."), ("29FEB24", "DATE7."), ("28/09/26", "DDMMYY8.")],
)
def test_leer_fecha_no_inventa_siglo_si_falta_yearcutoff(text, informat):
    with pytest.raises(NoSoportadoEnInterprete) as error:
        leer_fecha(text, informat)

    assert error.value.detalle == "P-YEARCUTOFF-EXPLICITO"


def test_anydtdte_ambiguo_queda_pendiente_sin_datestyle():
    with pytest.raises(NoSoportadoEnInterprete) as error:
        leer_fecha("03/04/2026", "ANYDTDTE10.")

    assert error.value.detalle == "P-ANYDTDTE-DATESTYLE"


def test_anydtdte_solo_acepta_iso_estricto_en_este_subconjunto():
    with pytest.raises(NoSoportadoEnInterprete) as error:
        leer_fecha("2026/09/28", "ANYDTDTE10.")

    assert error.value.detalle == "P-ANYDTDTE-DATESTYLE"


def test_informat_fecha_vacio_es_missing_y_fecha_ignorada_no_se_acepta():
    assert leer_fecha("", "DATE9.") is None
    with pytest.raises(NoSoportadoEnInterprete) as error:
        leer_fecha("14:30", "TIME8.")
    assert error.value.detalle == "P-INFORMAT-SIN-SOPORTE"


def test_informat_fecha_rechaza_anchos_fuera_del_subconjunto_documentado():
    assert informat_fecha_soportado("YYMMDD10.")
    assert not informat_fecha_soportado("YYMMDD12.")
    with pytest.raises(NoSoportadoEnInterprete) as error:
        leer_fecha("2026-09-28", "YYMMDD12.")
    assert error.value.detalle == "P-INFORMAT-SIN-SOPORTE"


def test_leer_campo_y_leer_lista_delegan_a_informats_fecha():
    assert leer_campo("2026-09-28", "yymmdd10.") == "24377"
    rows = leer_lista(
        ["1;2026-09-28;28/09/2026;28SEP2026;2026-09-28", "2;;;;"],
        [
            ("id", "$1."),
            ("d1", "YYMMDD10."),
            ("d2", "DDMMYY10."),
            ("d3", "DATE9."),
            ("d4", "ANYDTDTE10."),
        ],
        ";",
        dsd=True,
        missover=True,
    )

    assert rows == [
        {"id": "1", "d1": "24377", "d2": "24377", "d3": "24377", "d4": "24377"},
        {"id": "2", "d1": None, "d2": None, "d3": None, "d4": None},
    ]


def test_informats_fecha_conservan_tipo_date():
    for spec in ("yymmdd10.", "ddmmyy10.", "date9.", "anydtdte10."):
        assert informat_type(spec) == CodeType("Date")


def test_input_talend_parsea_strictamente_los_formatos_fecha_y_expone_sus_limites():
    translated = translate_to_talend("input(fecha, yymmdd10.)").java

    assert "java.time.LocalDate.of" in translated
    assert "YearMonth.of" in translated
    assert "P-YEARCUTOFF-EXPLICITO" in translated
    assert "java.sql.Date.valueOf" in translated

    ambiguous = translate_to_talend("input(fecha, anydtdte10.)").java
    assert "P-ANYDTDTE-DATESTYLE" in ambiguous


def test_esquema_y_emisor_convierten_fechas_desde_texto_en_tmap():
    plan = _plan()
    schemas, pending = esquemas_de_entrada(plan, {}, None)

    assert [(column.name, column.type) for column in schemas["work.fechas"]] == [
        ("id", "String"),
        ("d1", "Date"),
        ("d2", "Date"),
        ("d3", "Date"),
        ("d4", "Date"),
    ]
    assert pending == []

    result = plan_a_jobs(plan, schemas)

    assert len(result.jobs) == 1
    assert result.pendientes == []
    job = result.jobs[0]
    reader = next(node for node in job.nodos if node.componente == "tFileInputDelimited")
    convert = next(node for node in job.nodos if node.componente == "tMap")
    writer = next(node for node in job.nodos if node.componente == "tFileOutputDelimited")
    assert [column.tipo for column in reader.metadatas[0].columnas] == ["id_String"] * 5
    assert [column.tipo for column in convert.metadatas[0].columnas] == [
        "id_String",
        "id_Date",
        "id_Date",
        "id_Date",
        "id_Date",
    ]
    assert "java.time.LocalDate.of" in convert.datos
    assert any(edge.origen == reader.unico and edge.destino == convert.unico for edge in job.conexiones)
    assert any(edge.origen == convert.unico and edge.destino == writer.unico for edge in job.conexiones)
