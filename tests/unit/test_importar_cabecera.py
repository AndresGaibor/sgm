"""Semántica de cabecera, DATAROW y GUESSINGROWS para archivos delimitados."""

from __future__ import annotations

from pathlib import Path

from sgm.compile import compile_file, project_base
from sgm.frontend.program import analyze_program
from sgm.ir.models import Column, Evidence, Operator
from sgm.migrar.esquemas import esquemas_de_entrada
from sgm.migrar.tipos_import import filas_del_archivo, tipos_de_archivo
from sgm.talend_item.desde_plan import plan_a_jobs
from sgm.talend_item.desde_plan_cabecera import (
    aviso_guessingrows,
    lineas_a_saltar,
    nombres_por_omision,
)
from sgm.talend_item.desde_plan_nodos import nodo_lectura

REPO = Path(__file__).resolve().parents[2]


def _op(**params) -> Operator:
    return Operator(
        id="op_1",
        kind="read_file",
        params=params,
        signature="op_1",
        evidence=[Evidence("programa.sas", 2, 4, None)],
    )


def _valor(nodo, nombre: str) -> str | None:
    return next(
        fila[2]
        for fila in nodo.parametros
        if isinstance(fila, tuple) and fila[1] == nombre
    )


def test_datarow_salta_filas_previas_y_rechaza_datarow_1_con_getnames():
    assert lineas_a_saltar(False, 2) == 1
    assert lineas_a_saltar(True, None) == 1
    assert lineas_a_saltar(False, None) == 0
    try:
        lineas_a_saltar(True, 1)
    except ValueError as error:
        assert "p. 1385" in str(error)
    else:
        raise AssertionError("DATAROW=1 no puede usarse con GETNAMES=YES")


def test_getnames_no_genera_nombres_sas_por_posicion():
    assert nombres_por_omision(3) == ["VAR1", "VAR2", "VAR3"]


def test_guessingrows_es_aviso_si_el_esquema_ya_tiene_todos_los_tipos():
    pending = aviso_guessingrows(
        [Column("id", "String"), Column("valor", "Double")], "max", 7
    )

    assert pending is not None
    assert pending.codigo == "A-GUESSINGROWS-TIPOS-FIJADOS"
    assert pending.linea == 7


def test_guessingrows_sigue_bloqueando_si_falta_un_tipo():
    pending = aviso_guessingrows(
        [Column("id", "String"), Column("valor", None)], 100, 7
    )

    assert pending is not None
    assert pending.codigo == "P-GUESSINGROWS"


def test_guessingrows_numerico_debe_superar_datarow():
    pending = aviso_guessingrows(
        [Column("id", "String")], 3, 7, datarow=3, getnames=False
    )

    assert pending is not None
    assert pending.codigo == "P-GUESSINGROWS"
    assert "mayor que DATAROW=3" in pending.mensaje


def test_guessingrows_por_omision_tambien_debe_superar_datarow():
    pending = aviso_guessingrows(
        [Column("id", "String")], None, 7, datarow=21, getnames=False
    )

    assert pending is not None
    assert pending.codigo == "P-GUESSINGROWS"
    assert "20 (valor por omisión)" in pending.mensaje


def test_parser_conserva_datarow_como_entero_en_la_ir():
    analysis = analyze_program(
        {
            "programa.sas": (
                "proc import datafile='entrada.csv' out=work.d dbms=csv replace;\n"
                "getnames=no; datarow=2; guessingrows=max;\nrun;"
            )
        }
    )
    plan = compile_file(analysis, "programa.sas", project_base()).plan
    operator = next(op for op in plan.graph.operators() if op.kind == "read_file")

    assert operator.params["datarow"] == 2
    assert operator.params["getnames"] is False
    assert operator.params["guessingrows"] == "max"


def test_parser_no_agrega_datarow_si_el_sas_no_lo_declara():
    analysis = analyze_program(
        {
            "programa.sas": (
                "proc import datafile='entrada.csv' out=work.d dbms=csv replace;\n"
                "getnames=yes;\nrun;"
            )
        }
    )
    plan = compile_file(analysis, "programa.sas", project_base()).plan
    operator = next(op for op in plan.graph.operators() if op.kind == "read_file")

    assert "datarow" not in operator.params


def test_lector_delimitado_inicia_en_datarow_para_nombres_y_datos(tmp_path):
    path = tmp_path / "entrada.csv"
    path.write_text("# exportado,ignorar,ignorar\na,1,2\nb,3,4\n", encoding="utf-8")

    names, rows = filas_del_archivo(path, ",", getnames=False, datarow=2)

    assert names == ["VAR1", "VAR2", "VAR3"]
    assert rows == [["a", "1", "2"], ["b", "3", "4"]]


def test_datarow_cuenta_tambien_las_filas_vacias_anteriores(tmp_path):
    path = tmp_path / "entrada.csv"
    path.write_text("id,monto\n\na,1\n", encoding="utf-8")

    names, rows = filas_del_archivo(path, ",", getnames=True, datarow=3)

    assert names == ["id", "monto"]
    assert rows == [["a", "1"]]


def test_guessingrows_max_muestrea_desde_datarow_y_todos_los_datos(tmp_path):
    path = tmp_path / "entrada.csv"
    path.write_text("# exportado,ignorar,ignorar\na,1,2\nb,3,4\n", encoding="utf-8")

    inferred = tipos_de_archivo(
        path,
        ",",
        ["VAR1", "VAR2", "VAR3"],
        guessingrows="max",
        getnames=False,
        datarow=2,
    )

    assert {name: tipo.tipo_sas for name, tipo in inferred.items()} == {
        "VAR1": "caracter",
        "VAR2": "numerico",
        "VAR3": "numerico",
    }


def test_guessingrows_numerico_cuenta_filas_fisicas_del_archivo(tmp_path):
    path = tmp_path / "entrada.csv"
    path.write_text("id,monto\na,1\nb,2\nc,texto\n", encoding="utf-8")

    inferred = tipos_de_archivo(
        path, ",", ["monto"], guessingrows=3, getnames=True, datarow=2
    )

    assert inferred["monto"].tipo_sas == "numerico"
    assert inferred["monto"].pendientes == ("P-TIPO-FUERA-DE-MUESTRA",)


def test_guessingrows_con_esquema_fijado_emite_nodo_y_salta_datarow():
    result = nodo_lectura(
        _op(
            dbms="csv",
            datafile="'entrada.csv'",
            getnames=False,
            datarow=2,
            guessingrows="max",
        ),
        [Column("VAR1", "String"), Column("VAR2", "Double")],
        "tFileInputDelimited_1",
        0,
        0,
    )

    assert result.nodo is not None
    assert _valor(result.nodo, "HEADER") == "1"
    assert [pending.codigo for pending in result.pendientes] == [
        "A-GUESSINGROWS-TIPOS-FIJADOS"
    ]


def test_caso_l0_21_infiere_esquema_y_emite_header_datarow():
    case = REPO / "tests" / "corpus" / "L0" / "l0_21_importar_sin_cabecera_datarow"
    analysis = analyze_program(
        {"programa.sas": (case / "programa.sas").read_text(encoding="utf-8")}
    )
    plan = compile_file(analysis, "programa.sas", project_base()).plan
    schemas, schema_pending = esquemas_de_entrada(plan, {}, case / "entradas")

    result = plan_a_jobs(plan, schemas)
    input_node = next(
        node
        for job in result.jobs
        for node in job.nodos
        if node.componente == "tFileInputDelimited"
    )

    assert [(column.name, column.type) for column in schemas["work.d"]] == [
        ("VAR1", "String"),
        ("VAR2", "Double"),
        ("VAR3", "Double"),
    ]
    assert schema_pending == []
    assert _valor(input_node, "HEADER") == "1"
    assert [pending.codigo for pending in result.pendientes] == [
        "A-GUESSINGROWS-TIPOS-FIJADOS"
    ]


def test_datarow_en_xlsx_se_mantiene_pendiente_sin_plantilla_validada():
    result = nodo_lectura(
        _op(dbms="xlsx", datafile="'entrada.xlsx'", getnames=False, datarow=2),
        [Column("VAR1", "String")],
        "tFileInputExcel_1",
        0,
        0,
    )

    assert result.nodo is None
    assert [pending.codigo for pending in result.pendientes] == [
        "P-DATAROW-EXCEL-SIN-SOPORTE"
    ]


def test_guessingrows_sin_tipo_no_emite_lector_parcial():
    result = nodo_lectura(
        _op(
            dbms="csv",
            datafile="'entrada.csv'",
            getnames=True,
            guessingrows=100,
        ),
        [Column("id", "String"), Column("valor", None)],
        "tFileInputDelimited_2",
        0,
        0,
    )

    assert result.nodo is None
    assert [pending.codigo for pending in result.pendientes] == ["P-GUESSINGROWS"]


def test_guessingrows_sin_tipo_no_publica_un_job_vacio():
    analysis = analyze_program(
        {
            "programa.sas": (
                "proc import datafile='entrada.csv' out=work.d dbms=csv replace;\n"
                "getnames=yes; guessingrows=100; run;\n"
                "data work.s; set work.d; id_salida=id; keep id_salida; run;"
            )
        }
    )
    plan = compile_file(analysis, "programa.sas", project_base()).plan

    result = plan_a_jobs(
        plan,
        {
            "work.d": [Column("id", None)],
            "work.s": [Column("id_salida", None)],
        },
    )

    assert result.jobs == []
    assert "P-GUESSINGROWS" in {pending.codigo for pending in result.pendientes}


def test_datarow_dinamico_no_publica_un_job_parcial():
    analysis = analyze_program(
        {
            "programa.sas": (
                "proc import datafile='entrada.csv' out=work.d dbms=csv replace;\n"
                "getnames=no; datarow=&fila; guessingrows=max; run;\n"
                "data work.s; set work.d; id_salida=VAR1; keep id_salida; run;"
            )
        }
    )
    plan = compile_file(analysis, "programa.sas", project_base()).plan

    result = plan_a_jobs(plan, {"work.d": [Column("VAR1", None)]})

    assert result.jobs == []
    assert "P-DATAROW-DINAMICO" in {pending.codigo for pending in result.pendientes}
