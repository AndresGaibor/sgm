"""Pruebas de la IR lógica: una prueba por regla de lowering y firmas por nombres."""

from sgm.frontend.program import analyze_program
from sgm.ir.lower import lower_items
from sgm.ir.models import Graph, Operator, Plan
from sgm.ir.signature import signature


def _ops(text: str, graph_only: bool = False) -> list[Operator]:
    plan = Plan(program="p.sas")
    items = analyze_program({"p.sas": text}).items
    lower_items(items, plan.graph)
    return plan.graph.operators()


def _kinds(ops: list[Operator]) -> list[str]:
    return [o.kind for o in ops]


def _by_kind(ops: list[Operator], kind: str) -> list[Operator]:
    return [o for o in ops if o.kind == kind]


def test_set_where_asignacion_es_lectura_filtro_y_derivacion():
    ops = _ops("data out; set src; where x > 1; y = x * 2; run;")
    assert _kinds(ops) == ["read", "filter", "derive"]
    assert ops[0].params["dataset"] == "WORK.src"
    assert ops[2].params["outputs"] == ["WORK.out"]
    assert ops[2].params["assignments"][0]["target"] == "y"


def test_merge_con_if_and_es_inner():
    ops = _ops("data j; merge a(in=ina) b(in=inb); by id; if ina and inb; run;")
    (join,) = _by_kind(ops, "join")
    assert join.params["join_type"] == "inner" and join.status == "soportado"


def test_merge_con_if_solo_primera_tabla_es_left():
    ops = _ops("data j; merge a(in=ina) b(in=inb); by id; if ina; run;")
    (join,) = _by_kind(ops, "join")
    assert join.params["join_type"] == "left"


def test_merge_sin_condicion_es_full():
    ops = _ops("data j; merge a b; by id; run;")
    (join,) = _by_kind(ops, "join")
    assert join.params["join_type"] == "full"


def test_merge_con_condicion_no_deducible_queda_parcial():
    ops = _ops("data j; merge a(in=ina) b(in=inb); by id; if ina and not inb; run;")
    (join,) = _by_kind(ops, "join")
    assert join.params["join_type"] is None and join.status == "parcial"
    assert join.notes


def test_output_if_else_se_baja_a_ramas_de_un_map():
    ops = _ops("data a b; set src; if x = 1 then output a; else output b; run;")
    (mapa,) = _by_kind(ops, "map")
    assert [rama["outputs"] for rama in mapa.params["branches"]] == [["WORK.a"], ["WORK.b"]]
    assert mapa.params["branches"][0]["expression"] == "(x = 1)"
    assert mapa.params["branches"][1]["expression"] == "not (x = 1)"


def test_output_else_if_encadenado_conserva_prioridad_en_las_condiciones():
    ops = _ops(
        "data a b c; set src; if x = 1 then output a; "
        "else if x = 2 then output b; else output c; run;"
    )
    (mapa,) = _by_kind(ops, "map")
    ramas = mapa.params["branches"]
    assert [rama["expression"] for rama in ramas] == [
        "(x = 1)",
        "not (x = 1) and (x = 2)",
        "not (x = 1) and not (x = 2)",
    ]


def test_output_else_if_sin_else_no_agrega_rama_implicita():
    ops = _ops(
        "data a b; set src; if x = 1 then output a; "
        "else if x = 2 then output b; run;"
    )
    (mapa,) = _by_kind(ops, "map")
    assert [rama["expression"] for rama in mapa.params["branches"]] == [
        "(x = 1)",
        "not (x = 1) and (x = 2)",
    ]


def test_output_explicito_sin_condicion_no_se_descarta():
    ops = _ops("data a; set src; output a; run;")
    (split,) = _by_kind(ops, "split")
    assert split.params["target"] == "a"
    assert split.params["condition"] == ""
    assert split.params.get("outputs", []) == []


def test_retain_lag_y_first_last_son_estado_por_fila():
    ops = _ops("data t; set s; by g; retain acc 0; prev = lag(x); if first.g then acc = 0; run;")
    stateful = _by_kind(ops, "stateful_row")
    assert len(stateful) == 3
    assert all(o.status == "parcial" for o in stateful)


def test_proc_sort_nodupkey_es_sort_y_dedup():
    ops = _ops("proc sort data=x out=y nodupkey; by k1 k2; run;")
    assert _kinds(ops) == ["sort", "dedup"]
    assert ops[1].params["by"] == ["k1", "k2"]
    assert ops[1].params["outputs"] == ["WORK.y"]


def test_nodup_sin_clave_es_dedup_parcial():
    ops = _ops("proc sort data=x nodupkey; run;")
    dedup = _by_kind(ops, "dedup")[0]
    assert dedup.status == "parcial" and dedup.notes


def test_proc_append_es_union_proc_import_read_file_y_export_write_file():
    text = (
        "proc append base=a data=b; run;\n"
        'proc import datafile="in.csv" out=work.c dbms=csv replace; run;\n'
        'proc export data=work.c outfile="out.csv" dbms=csv; run;\n'
    )
    ops = _ops(text)
    assert _kinds(ops) == ["union", "read_file", "write_file"]


def test_proc_means_es_aggregate():
    ops = _ops("proc means data=x; class g; var v; run;")
    assert _kinds(ops) == ["aggregate"]
    assert ops[0].params["class"] == ["g"] and ops[0].params["var"] == ["v"]


def test_proc_transpose_es_no_soportado_con_motivo():
    (op,) = _ops("proc transpose data=x out=y; by k; var v; run;")
    assert op.kind == "unsupported"
    assert op.status == "hueco" and op.params["reason"] == "PROC_NO_SOPORTADO"


def test_pass_through_select_es_lectura_en_la_base_con_sql_intacto():
    sql = "select a, b from tabla where x = 'ok'"
    text = f"proc sql;\n connect to impala (server='h');\n select * from connection to impala ({sql});\nquit;"
    ops = _ops(text)
    read = _by_kind(ops, "read")[0]
    assert read.placement == "db:impala"
    assert read.params["sql"] == sql


def test_execute_by_es_exec_sql_en_la_base_y_salida_si_crea_tabla():
    ops = _ops(
        "proc sql;\n execute (create table lz.t stored as parquet as select 1 from s) by impala;\nquit;"
    )
    (op,) = _by_kind(ops, "exec_sql")
    assert op.placement == "db:impala"
    assert op.params["outputs"] == ["IMPALA.lz.t"]


def test_sql_sobre_work_se_traduce_a_flujo_sin_exec_sql():
    """Ningún SQL sobre WORK queda como exec_sql opaco (la escalera lo mandaría a tJava)."""
    ops = _ops("proc sql;\n create table t as select a from s join r on s.k = r.k;\nquit;")
    assert not _by_kind(ops, "exec_sql")
    (join,) = _by_kind(ops, "join")
    assert join.params["by"] == ["k"] and join.params["join_type"] == "inner"
    assert {op.params["dataset"] for op in _by_kind(ops, "read")} == {"WORK.s", "WORK.r"}


def test_proc_sin_regla_es_hueco_con_motivo():
    (op,) = _ops("proc univariate data=x; var a; run;")
    assert op.status == "hueco" and op.params["reason"] == "PROC_NO_SOPORTADO"


def test_cada_operador_lleva_evidencia_con_archivo_lineas_y_etiqueta():
    text = "/* Etiqueta: Carga */\ndata a; set s; run;\n"
    ops = _ops(text)
    assert all(o.evidence for o in ops)
    ev = ops[0].evidence[0]
    assert (ev.file, ev.line_start, ev.label) == ("p.sas", 2, "Carga")


def test_firma_no_cambia_si_solo_cambian_nombres():
    a = _ops("data out1; set src1; where campo_a > 10; run;")
    b = _ops("data out2; set src2; where campo_b > 99; run;")
    assert [o.signature for o in a] == [o.signature for o in b]


def test_firma_cambia_si_cambia_la_logica():
    a = _ops("data o; set s; where x > 1; run;")
    b = _ops("data o; set s; where x < 1; run;")
    assert a[1].signature != b[1].signature


def test_firma_de_operador_no_depende_de_id():
    assert signature("filter", {"expression": "x > 1"}) == signature(
        "filter", {"expression": "y > 2"}
    )


def test_grafo_fusion_une_evidencia_y_redirige_aristas():
    g = Graph()
    from sgm.ir.models import Edge, Evidence

    ev1 = Evidence("p.sas", 1, 1, None)
    ev2 = Evidence("p.sas", 2, 2, None)
    from sgm.ir.models import Operator as Op

    g.add_operator(Op("a", "read", evidence=[ev1]))
    g.add_operator(Op("b", "filter", evidence=[ev1]))
    g.add_operator(Op("c", "derive", evidence=[ev2]))
    g.add_edge(Edge("a", "b", "WORK.x"))
    g.add_edge(Edge("b", "c", "WORK.y"))
    g.merge("c", "b")
    assert "b" not in g and len(g) == 2
    assert len(g.operator("c").evidence) == 2
    assert [e.src for e in g.edges()] == ["a"]
