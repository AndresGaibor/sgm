"""Pruebas del frontend: nodos por etiqueta, pasos, PROC SQL y DATA step."""

from pathlib import Path

from sgm.frontend.datastep import DataStep
from sgm.frontend.splitter import split_nodes
from sgm.frontend.sql import parse_sql_statement
from sgm.frontend.steps import (
    Include,
    Let,
    Libname,
    MacroCall,
    MacroDef,
    Proc,
    ProcSql,
    Unparsed,
    XCommand,
    parse_node,
)

ROOT = Path(__file__).resolve().parents[2]
CLIENT_LARGE = ROOT / "tests" / "fixtures" / "sas" / "client" / "client_large.sas"


def _steps(text: str):
    nodes = split_nodes(text)
    assert len(nodes) == 1
    return parse_node(nodes[0]).steps


def _ds(steps) -> DataStep:
    (step,) = steps
    assert isinstance(step, DataStep)
    return step


# --- splitter -------------------------------------------------------------


def test_nodos_por_etiqueta_con_lineas_y_cabecera_sin_etiqueta():
    text = "libname a 'x';\n/* Etiqueta: Carga inicial */\ndata a.t; set b; run;\n/* Etiqueta: Fin */\nquit;\n"
    nodes = split_nodes(text)
    assert [n.label for n in nodes] == [None, "Carga inicial", "Fin"]
    assert (nodes[1].line_start, nodes[2].line_start) == (2, 4)


def test_quita_el_caracter_de_ancho_cero_sin_mover_lineas():
    text = "​/* Etiqueta: A */\n​data t; set s; run;\n"
    nodes = split_nodes(text)
    assert nodes[0].label == "A" and "​" not in nodes[0].text
    assert nodes[0].line_start == 1


def test_el_programa_grande_tiene_un_nodo_por_etiqueta():
    text = CLIENT_LARGE.read_text(encoding="utf-8")
    labels = text.count("/* Etiqueta:")
    nodes = split_nodes(text)
    assert sum(1 for n in nodes if n.label is not None) == labels == 610
    assert nodes[-1].line_end <= text.count("\n") + 1


# --- pasos ----------------------------------------------------------------


def test_data_step_con_salidas_y_sentencias():
    steps = _steps("data work.a b(keep=x) ; set src; where x > 1; y = x + 1; output a; run;")
    step = _ds(steps)
    assert step.outputs == ["work.a", "b"]
    assert [s.kind for s in step.statements] == ["set", "where", "assign", "output"]


def test_proc_sql_con_create_y_select():
    steps = _steps(
        "proc sql;\n create table lz.t as select * from src;\n select count(*) from lz.t;\nquit;"
    )
    (sql,) = steps
    assert isinstance(sql, ProcSql)
    assert [s.kind for s in sql.statements] == ["create_table", "select"]
    assert sql.statements[0].target == "lz.t" and sql.statements[0].sources == ("src",)


def test_proc_generico_con_datos_salida_y_clausulas():
    (proc,) = _steps("proc sort data=work.x out=work.y nodupkey; by k1 k2; run;")
    assert isinstance(proc, Proc)
    assert proc.name == "sort" and proc.options == {"data": "work.x", "out": "work.y"}
    assert "nodupkey" in proc.flags and proc.clauses["by"] == "by k1 k2"


def test_macro_definida_con_parametros_y_cuerpo():
    (macro,) = _steps("%macro carga(tabla=, anio);\n data &tabla; set s; run;\n%mend carga;")
    assert isinstance(macro, MacroDef)
    assert macro.name == "carga" and macro.params == ["tabla", "anio"]
    assert isinstance(macro.body[0], DataStep)


def test_llamada_de_macro_con_y_sin_argumentos():
    with_args, without = _steps("%carga(tabla=x, 2020);"), _steps("%ambiente;")
    assert isinstance(with_args[0], MacroCall) and with_args[0].args == "tabla=x, 2020"
    assert isinstance(without[0], MacroCall) and without[0].args == ""


def test_let_include_libname_options_y_comando_x():
    steps = _steps(
        '%let anio = 2025;\n%include "inc/macros.sas";\nlibname lz "/data";\n'
        'options mprint;\nx "ls -la";'
    )
    assert isinstance(steps[0], Let) and steps[0].value == "2025"
    assert isinstance(steps[1], Include) and steps[1].path == "inc/macros.sas"
    assert isinstance(steps[2], Libname) and steps[2].name == "lz"
    assert steps[3].__class__.__name__ == "Options"
    assert isinstance(steps[4], XCommand) and steps[4].command == "ls -la"


# --- fragmentos rotos -----------------------------------------------------


def test_fragmento_roto_produce_unparsed_y_sigue():
    steps = _steps("data ; set s; run;\nproc sort data=x; by k; run;")
    assert isinstance(steps[0], Unparsed) and steps[0].reason == "DATA sin salidas"
    assert isinstance(steps[1], Proc) and steps[1].name == "sort"


def test_proc_sin_nombre_es_unparsed():
    (step,) = _steps("proc ;")
    assert isinstance(step, Unparsed)


# --- PROC SQL -------------------------------------------------------------


def test_pass_through_guarda_el_sql_intacto():
    sql = "select a, b from tabla where x = 'ok'"
    st = parse_sql_statement(f"select * from connection to oracle ({sql})", 1)
    assert st.kind == "select_passthrough" and st.engine == "oracle"
    assert st.inner_sql == sql


def test_execute_en_ambas_formas_y_conexion():
    a = parse_sql_statement("execute (drop table x) by impala", 1)
    b = parse_sql_statement("EXECUTE BY impala (create table x as select 1 from y)", 2)
    assert a.kind == b.kind == "execute" and a.engine == b.engine == "impala"
    assert a.inner_sql == "drop table x"
    assert b.inner_sql == "create table x as select 1 from y"


def test_connect_disconnect_insert_delete_drop():
    kinds = [
        parse_sql_statement("connect to impala (server='h')", 1).kind,
        parse_sql_statement("disconnect from impala", 2).kind,
        parse_sql_statement("insert into t values (1)", 3).kind,
        parse_sql_statement("delete from t", 4).kind,
        parse_sql_statement("drop table t", 5).kind,
    ]
    assert kinds == ["connect", "disconnect", "insert", "delete", "drop_table"]


def test_execute_con_punto_y_coma_dentro_de_parentesis():
    steps = _steps(
        "proc sql;\n execute (create table t as\n select 1 from s;\n ) by impala;\nquit;"
    )
    (sql,) = steps
    assert [s.kind for s in sql.statements] == ["execute"]


# --- DATA step ------------------------------------------------------------


def test_merge_con_in_by_y_if_compuesto():
    steps = _steps("data j; merge a(in=ina) b(in=inb); by id; if ina and inb; run;")
    step = _ds(steps)
    kinds = [s.kind for s in step.statements]
    assert kinds == ["merge", "by", "if"]
    assert step.statements[0].fields["sources"][0]["in"] == "ina"


def test_retain_lag_first_last_array_do_y_end():
    steps = _steps(
        "data t; set s; by g; retain acc 0; prev = lag(x); "
        "if first.g then acc = 0; array v{3} v1-v3; do i = 1 to 3; end; run;"
    )
    kinds = [s.kind for s in _ds(steps).statements]
    assert (
        "retain" in kinds
        and "lag" in kinds
        and "array" in kinds
        and "do" in kinds
        and "end" in kinds
    )
    flags = [s.fields.get("first_last") for s in _ds(steps).statements if s.kind == "if"]
    assert flags == [["first.g"]]


def test_keep_drop_rename_output_infile_input_datalines_symput():
    steps = _steps(
        "data t; infile 'a.csv' dlm=','; input a b; keep a; drop b; rename a=x; "
        "call symputx('n', 5); output t; datalines;\n1,2\n;\nrun;"
    )
    kinds = [s.kind for s in _ds(steps).statements]
    assert kinds == [
        "infile",
        "input",
        "keep",
        "drop",
        "rename",
        "call_symput",
        "output",
        "datalines",
    ]
    datalines = _ds(steps).statements[-1]
    assert datalines.fields["rows"] == 1
