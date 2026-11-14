from __future__ import annotations

from html import unescape
from pathlib import Path

import pytest

from sgm.compile import compile_file, project_base
from sgm.expressions.talend_translator import translate_to_talend
from sgm.formatos.informat_archivo import leer_campo
from sgm.frontend.program import analyze_program
from sgm.ir.types_code import CodeType, informat_type
from sgm.migrar.esquemas import esquemas_de_entrada
from sgm.migrar.interprete_errores import NoSoportadoEnInterprete
from sgm.migrar.interprete_infile import leer_lista
from sgm.talend_item.desde_plan import plan_a_jobs

PROGRAMA = (
    "data work.limpio;\n"
    "infile '/datos/crudo.txt' dlm=';' dsd missover;\n"
    "input a :COMMA12.2 b :DOLLAR10. c :8.2;\n"
    "run;"
)


def _plan(text: str = PROGRAMA):
    analysis = analyze_program({"programa.sas": text})
    return compile_file(analysis, "programa.sas", project_base()).plan


@pytest.mark.parametrize(
    ("texto", "informat", "esperado"),
    [
        ("1,234.50", "COMMA12.2", "1234.5"),
        ("(7)", "COMMA12.2", "-0.07"),
        ("-7", "COMMA12.2", "0.07"),
        ("1.5%", "COMMA12.2", "1.5"),
        ("$1500", "DOLLAR10.", "1500"),
        ("12345", "8.2", "123.45"),
        ("1.5", "8.2", "1.5"),
        ("", "COMMA12.2", None),
        (".", "8.2", None),
    ],
)
def test_leer_campo_aplica_informats_numericos_documentados(texto, informat, esperado):
    assert leer_campo(texto, informat) == esperado


def test_caracter_no_documentado_en_comma_no_se_descarta_silenciosamente():
    with pytest.raises(NoSoportadoEnInterprete) as error:
        leer_campo("1.5*", "COMMA12.2")

    assert error.value.detalle == "P-INFORMAT-VALOR-INVALIDO"


def test_expresion_talend_acepta_parentesis_inicial_documentado_por_comma():
    expression = translate_to_talend("input(importe, comma12.2)").java

    assert '.contains("(")' in expression
    assert '.indexOf("(", 1) == -1' in expression
    assert '.endsWith(")")' not in expression


def test_leer_lista_aplica_informats_por_columna_y_conserva_faltantes():
    rows = leer_lista(
        ["1,234.50;$1500;12345", "(7);$20;5", ";;"],
        [("a", "COMMA12.2"), ("b", "DOLLAR10."), ("c", "8.2")],
        ";",
        dsd=True,
        missover=True,
    )

    assert rows == [
        {"a": "1234.5", "b": "1500", "c": "123.45"},
        {"a": "-0.07", "b": "20", "c": "0.05"},
        {"a": None, "b": None, "c": None},
    ]


def test_comma_y_dollar_declaran_tipo_numerico_con_la_escala_del_informat():
    assert informat_type("comma12.2") == CodeType("BigDecimal")
    assert informat_type("dollar10.") == CodeType("Double")
    assert informat_type("8.2") == CodeType("BigDecimal")


def test_esquema_lista_conserva_precision_de_informats():
    plan = _plan()

    schemas, pending = esquemas_de_entrada(plan, {}, None)

    assert [(column.name, column.type) for column in schemas["work.limpio"]] == [
        ("a", "BigDecimal"),
        ("b", "Double"),
        ("c", "BigDecimal"),
    ]
    assert pending == []


def test_emisor_lee_informats_como_texto_y_los_convierte_en_tmap():
    plan = _plan()
    schemas, _ = esquemas_de_entrada(plan, {}, None)

    result = plan_a_jobs(plan, schemas)

    assert len(result.jobs) == 1
    assert result.pendientes == []
    job = result.jobs[0]
    reader = next(node for node in job.nodos if node.componente == "tFileInputDelimited")
    convert = next(node for node in job.nodos if node.componente == "tMap")
    assert [column.tipo for column in reader.metadatas[0].columnas] == ["id_String"] * 3
    assert [column.tipo for column in convert.metadatas[0].columnas] == [
        "id_BigDecimal",
        "id_Double",
        "id_BigDecimal",
    ]
    assert 'replace(",", "")' in unescape(convert.datos)
    assert "movePointLeft" in convert.datos
    assert any(edge.origen == reader.unico and edge.destino == convert.unico for edge in job.conexiones)


def test_emisor_bloquea_informat_fecha_hasta_implementar_su_conversion():
    plan = _plan(PROGRAMA.replace("COMMA12.2", "DATE9.").replace("DOLLAR10.", "DATE9."))
    schemas, _ = esquemas_de_entrada(plan, {}, None)

    result = plan_a_jobs(plan, schemas)

    assert result.jobs == []
    assert any(pending.codigo == "P-INFORMAT-SIN-SOPORTE" for pending in result.pendientes)


def test_caso_l0_25_documenta_alias_y_ejemplo_con_negativo_parentizado():
    case = Path(__file__).resolve().parents[1] / "corpus" / "L0" / "l0_25_informats_numericos_infile"

    source = (case / "programa.sas").read_text(encoding="utf-8")
    values = (case / "entradas" / "crudo.txt").read_text(encoding="utf-8").splitlines()

    assert "DOLLAR10." in source
    assert "(7)" in values[1]
