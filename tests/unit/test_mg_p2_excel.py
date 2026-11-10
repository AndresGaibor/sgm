"""Regresiones de formatos Excel en la entrada/salida del hito MG-P2-01."""

from __future__ import annotations

from sgm.compile import compile_file, project_base
from sgm.frontend.program import analyze_program
from sgm.ir.models import Column, Evidence, Operator
from sgm.passes.p10_components import choose, load_engines, load_rules
from sgm.talend_item.desde_plan_nodos import nodo_escritura, nodo_lectura
from sgm.talend_item.modelo import Columna

RULES = load_rules()
ENGINES = load_engines()


def _op(kind: str, **params) -> Operator:
    return Operator(
        id="op_1",
        kind=kind,
        params=params,
        signature="op_1",
        evidence=[Evidence("programa.sas", 4, 4, None)],
    )


def _componente(kind: str, **params) -> str | None:
    found = choose(_op(kind, **params), RULES, ENGINES)
    return found[1] if found else None


def _valor(nodo, nombre: str) -> str | None:
    return next(fila[2] for fila in nodo.parametros if isinstance(fila, tuple) and fila[1] == nombre)


def test_import_excel_se_clasifica_por_dbms_y_no_por_extension():
    assert _componente("read_file", dbms="xlsx", datafile="datos.csv") == "tFileInputExcel"
    assert _componente("read_file", dbms="csv", datafile="datos.xlsx") == "tFileInputDelimited"


def test_export_excel_se_clasifica_como_escritor_excel():
    assert _componente("write_file", dbms="xlsx", outfile="salida.csv") == "tFileOutputExcel"


def test_dbms_desconocido_no_se_clasifica_por_la_extension_excel():
    assert _componente("read_file", dbms="excelcs", datafile="datos.xlsx") is None


def test_export_sin_dbms_no_se_asume_delimitado():
    assert _componente("write_file", outfile="salida.csv") is None


def test_entrada_data_step_conserva_la_regla_vigente_hasta_modelar_infile():
    assert _componente("read_file") == "tFileInputDelimited"


def test_export_xlsx_conserva_la_hoja_en_la_ir():
    analysis = analyze_program(
        {
            "programa.sas": (
                "proc export data=work.origen outfile='salida.xlsx' dbms=xlsx replace;\n"
                "sheet='Resumen';\nrun;"
            )
        }
    )
    plan = compile_file(analysis, "programa.sas", project_base()).plan
    operador = next(op for op in plan.graph.operators() if op.kind == "write_file")

    assert operador.params["sheet"] == "Resumen"


def test_guessingrows_max_se_conserva_para_el_pendiente_de_inferencia():
    analysis = analyze_program(
        {
            "programa.sas": (
                "proc import datafile='entrada.csv' out=work.origen dbms=csv replace;\n"
                "guessingrows=max;\nrun;"
            )
        }
    )
    plan = compile_file(analysis, "programa.sas", project_base()).plan
    operador = next(op for op in plan.graph.operators() if op.kind == "read_file")

    assert operador.params["guessingrows"] == "max"


def test_lector_excel_ajusta_version_del_libro_segun_dbms():
    xls = nodo_lectura(
        _op("read_file", dbms="xls", datafile="'datos.xls'", getnames=True),
        [Column("id", "String")],
        "tFileInputExcel_1",
        0,
        0,
    )
    xlsx = nodo_lectura(
        _op("read_file", dbms="xlsx", datafile="'datos.xlsx'", getnames=True),
        [Column("id", "String")],
        "tFileInputExcel_2",
        0,
        0,
    )

    assert _valor(xls.nodo, "VERSION_2007") == "false"
    assert _valor(xlsx.nodo, "VERSION_2007") == "true"


def test_export_excel_sin_plantilla_real_queda_pendiente_y_no_se_emite_como_delimitado():
    result = nodo_escritura(
        _op("write_file", dbms="xlsx", outfile="'salida.xlsx'", sheet="Resumen"),
        [Columna("id", "id_String")],
        "tFileOutputExcel_1",
        0,
        0,
    )

    assert result.nodo is None
    assert [pending.codigo for pending in result.pendientes] == ["P-COMPONENTE-SIN-PLANTILLA"]


def test_guessingrows_explicito_deja_pendiente_la_inferencia_que_no_se_emite():
    result = nodo_lectura(
        _op(
            "read_file",
            dbms="csv",
            datafile="'entrada.csv'",
            getnames=True,
            guessingrows=1000,
        ),
        [Column("id", "String")],
        "tFileInputDelimited_1",
        0,
        0,
    )

    assert any(pending.codigo == "P-GUESSINGROWS" for pending in result.pendientes)


def test_guessingrows_max_tambien_deja_pendiente_la_inferencia():
    result = nodo_lectura(
        _op(
            "read_file",
            dbms="csv",
            datafile="'entrada.csv'",
            getnames=True,
            guessingrows="max",
        ),
        [Column("id", "String")],
        "tFileInputDelimited_2",
        0,
        0,
    )

    pendiente = next(p for p in result.pendientes if p.codigo == "P-GUESSINGROWS")
    assert "max" in pendiente.mensaje
