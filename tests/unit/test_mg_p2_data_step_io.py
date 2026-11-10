"""Emisión conservadora y pendientes de entrada/salida en DATA step."""

from __future__ import annotations

from sgm.compile import compile_file, project_base
from sgm.frontend.program import analyze_program
from sgm.ir.models import Column, Evidence, Operator
from sgm.migrar.esquemas import esquemas_de_entrada
from sgm.talend_item.desde_plan import plan_a_jobs
from sgm.talend_item.desde_plan_nodos import nodo_lectura


def _plan(text: str):
    analysis = analyze_program({"p.sas": text})
    return compile_file(analysis, "p.sas", project_base()).plan


def _archivo(plan, kind: str = "read_file") -> Operator:
    return next(op for op in plan.graph.operators() if op.kind == kind)


def _op(**params) -> Operator:
    return Operator(
        id="read_1",
        kind="read_file",
        params=params,
        signature="read_1",
        evidence=[Evidence("p.sas", 2, 2, None)],
    )


def _valor(nodo, nombre: str) -> str | None:
    return next(fila[2] for fila in nodo.parametros if isinstance(fila, tuple) and fila[1] == nombre)


def test_lectura_delimitada_aplica_separador_y_firstobs():
    result = nodo_lectura(
        _op(
            datafile="'/datos/entrada.txt'",
            file_format="delimited",
            infile_statement="infile '/datos/entrada.txt' dlm='|' firstobs=2",
            input_statement="input codigo",
            input_mode="list",
            infile_options={"dlm": "|", "firstobs": 2},
            delimiter="|",
            firstobs=2,
            input_names=["codigo"],
            outputs=["WORK.entrada"],
        ),
        [Column("codigo", "String")],
        "tFileInputDelimited_1",
        0,
        0,
    )

    assert result.nodo is not None
    assert _valor(result.nodo, "FIELDSEPARATOR") == '"|"'
    assert _valor(result.nodo, "HEADER") == "1"


def test_infile_input_delimitado_llega_al_job_con_sus_opciones():
    plan = _plan(
        "data work.entrada;\n"
        "infile '/datos/entrada.txt' dlm='|' firstobs=3;\n"
        "input codigo;\n"
        "run;"
    )
    esquema = esquemas_de_entrada(plan, {}, None)[0]

    result = plan_a_jobs(plan, esquema)

    nodo = next(n for n in result.jobs[0].nodos if n.componente == "tFileInputDelimited")
    assert _valor(nodo, "FILENAME") == "context.ruta_entrada"
    assert _valor(nodo, "FIELDSEPARATOR") == '"|"'
    assert _valor(nodo, "HEADER") == "2"


def test_opciones_sas_sin_equivalencia_bloquean_el_nodo():
    result = nodo_lectura(
        _op(
            datafile="'/datos/entrada.txt'",
            file_format="delimited",
            infile_statement="infile '/datos/entrada.txt' dsd dlm=','",
            input_statement="input codigo",
            input_mode="list",
            delimiter=",",
            infile_options={"dsd": True, "dlm": ","},
            outputs=["WORK.entrada"],
        ),
        [Column("codigo", "String")],
        "tFileInputDelimited_1",
        0,
        0,
    )

    assert result.nodo is None
    assert any(p.codigo == "P-INFILE-SIN-EQUIVALENCIA" for p in result.pendientes)


def test_fileref_sin_resolver_no_se_trata_como_ruta():
    result = nodo_lectura(
        _op(
            fileref="entrada",
            file_format="delimited",
            input_mode="list",
            delimiter="|",
            infile_options={"dlm": "|"},
            infile_statement="infile entrada dlm='|'",
            input_statement="input codigo",
        ),
        [Column("codigo", "String")],
        "tFileInputDelimited_1",
        0,
        0,
    )

    assert result.nodo is None
    assert any(p.codigo == "P-FILENAME-SIN-RESOLVER" for p in result.pendientes)


def test_datalines_conserva_filas_y_no_genera_archivo_vacio():
    plan = _plan(
        "data work.valores;\n"
        "input codigo monto;\n"
        "datalines;\n"
        "A,10\n"
        "B,20\n"
        ";\n"
        "run;"
    )
    op = _archivo(plan)
    result = nodo_lectura(
        op,
        [Column("codigo", "String"), Column("monto", "String")],
        "tFileInputDelimited_1",
        0,
        0,
    )

    assert op.params["datalines_data"] == ["A,10", "B,20"]
    assert op.params["file_format"] == "datalines"
    assert op.status == "hueco"
    assert op.params["reason"] == "DATALINES_SIN_LECTOR"
    assert result.nodo is None
    assert any(p.codigo == "P-DATALINES-SIN-LECTOR" for p in result.pendientes)


def test_lectura_posicional_queda_pendiente_sin_plantilla_de_studio():
    result = nodo_lectura(
        _op(
            datafile="'/datos/registros.dat'",
            file_format="positional",
            input_names=["id", "region"],
            outputs=["WORK.fijos"],
        ),
        [Column("id", "String"), Column("region", "String")],
        "tFileInputPositional_1",
        0,
        0,
    )

    assert result.nodo is None
    assert any(p.codigo == "P-COMPONENTE-SIN-PLANTILLA" for p in result.pendientes)


def test_informat_reconocido_queda_explicito_hasta_la_traduccion_de_p2_03():
    result = nodo_lectura(
        _op(
            datafile="'/datos/entrada.txt'",
            file_format="positional",
            input_mode="formatted",
            input_statement="input fecha yymmdd10.",
            outputs=["WORK.entrada"],
        ),
        [Column("fecha", "String")],
        "tFileInputPositional_1",
        0,
        0,
    )

    assert result.nodo is None
    assert {p.codigo for p in result.pendientes} == {
        "P-COMPONENTE-SIN-PLANTILLA",
        "P-INFORMAT-SIN-SOPORTE",
    }


def test_file_put_queda_como_pendiente_explicito_con_su_sintaxis():
    plan = _plan(
        "data _null_;\n"
        "file '/salida/resumen.txt';\n"
        "put id $10. monto comma12.2;\n"
        "run;"
    )
    pendientes = [op for op in plan.graph.operators() if op.status == "hueco"]

    assert len(pendientes) == 1
    assert pendientes[0].params["reason"] == "SENTENCIA_NO_SOPORTADA"
    assert pendientes[0].params["reason_detail"] == "FILE_PUT_SIN_PLANTILLA"
    assert pendientes[0].params["unsupported_statements"] == [
        "file '/salida/resumen.txt'",
        "put id $10. monto comma12.2",
    ]


def test_file_put_en_paso_con_set_deja_gap_sin_alterar_el_operador():
    plan = _plan("data work.salida; set work.origen; put codigo; run;")
    read = next(op for op in plan.graph.operators() if op.kind == "read")

    assert read.status == "soportado"
    assert any(note == "FILE_PUT_SIN_PLANTILLA: put codigo" for note in read.notes)
    assert any(g.reason == "SENTENCIA_NO_SOPORTADA" for g in plan.gaps)
