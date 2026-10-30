"""Pruebas de las pasadas 5 a 8: fusión SQL, fusión de flujo, plantillas y particionado."""

from sgm.compile import compile_project


def _plan(text: str, engines: dict[str, str] | None = None):
    compiled, _ = compile_project({"p.sas": text}, library_engines=engines)
    return compiled["p.sas"].plan


def _kind(plan, kind):
    return [o for o in plan.graph.operators() if o.kind == kind]


# --- pasada 5: SQL en base con CTE ----------------------------------------


def test_p05_dos_execute_seguidos_quedan_en_un_exec_sql_con_cte():
    text = (
        "proc sql;\n"
        " execute (create table lz.t1 as select a from src) by impala;\n"
        " execute (create table lz.t2 as select a from lz.t1 where a > 1) by impala;\n"
        "quit;\n"
    )
    plan = _plan(text)
    sql_ops = [o for o in _kind(plan, "exec_sql") if o.placement == "db:impala"]
    assert len(sql_ops) == 1
    fused = sql_ops[0].params["sql"]
    assert fused.lower().startswith("create table lz.t2 as with t1 as (select a from src)")
    assert "from t1" in fused.lower()


def test_p05_no_fusiona_si_el_intermedio_es_salida_final():
    text = (
        "proc sql;\n"
        " execute (create table lz.t1 as select a from src) by impala;\n"
        " execute (create table lz.t2 as select a from lz.t1 where a > 1) by impala;\n"
        "quit;\n"
        "data otro; set impala.lz.t1; run;\n"
    )
    plan = _plan(text, engines={"IMPALA": "impala"})
    assert len(_kind(plan, "exec_sql")) == 2


# --- pasada 6: flujo en un map --------------------------------------------


def test_p06_filtro_derivacion_y_renombre_encadenados_quedan_en_un_map():
    plan = _plan("data a; set s; where x > 1; y = x + 1; rename y = z; run;")
    (mapa,) = _kind(plan, "map")
    assert [paso["kind"] for paso in mapa.params["steps"]] == ["filter", "derive", "rename"]
    assert _kind(plan, "filter") == [] and _kind(plan, "derive") == []


def test_p06_dataset_con_tres_salidas_filtradas_queda_en_un_map_con_tres_ramas():
    text = (
        "data base; set s; run;\n"
        "data a; set base; where k = 1; run;\n"
        "data b; set base; where k = 2; run;\n"
        "data c; set base; where k = 3; run;\n"
    )
    plan = _plan(text)
    mapas = [m for m in _kind(plan, "map") if "branches" in m.params]
    assert len(mapas) == 1
    assert len(mapas[0].params["branches"]) == 3


def test_p06_un_filtro_aislado_no_se_fusiona():
    plan = _plan("data a; set s; where x > 1; run;")
    assert _kind(plan, "map") == []
    assert len(_kind(plan, "filter")) == 1


# --- pasada 7: plantillas -------------------------------------------------


def test_p07_tres_ramas_iguales_salvo_el_sufijo_producen_una_plantilla_con_tres_instancias():
    text = (
        "data r_A; set src_A; where x > 1; y = x; run;\n"
        "data r_B; set src_B; where x > 1; y = x; run;\n"
        "data r_C; set src_C; where x > 1; y = x; run;\n"
    )
    plan = _plan(text)
    instancias = _kind(plan, "iterate")
    assert len(instancias) == 3
    (job,) = plan.jobs[0].children
    assert job.contexts["instancias"] == 3
    assert {i.params["template"] for i in instancias} == {job.name}
    valores = sorted(i.params["context"]["parametro_0"] for i in instancias)
    assert valores == ["WORK.src_a", "WORK.src_b", "WORK.src_c"]


def test_p07_ramas_distintas_no_forman_plantilla():
    """Filtrar y conservar columnas son operadores distintos: no forman plantilla."""
    text = "data r_A; set src_A; where x > 1; run;\ndata r_B; set src_B; keep x; run;\n"
    assert _kind(_plan(text), "iterate") == []


# --- pasada 8: particionado -----------------------------------------------


def test_p08_cadena_lineal_no_se_corta():
    plan = _plan("data a; set s; where x > 1; y = x; run;")
    assert len(plan.jobs[0].subjobs) == 1
    assert len(plan.jobs[0].subjobs[0]) == len(plan.graph)


def test_p08_agregado_que_vuelve_a_unirse_con_su_detalle_materializa_la_arista():
    text = (
        "data det; set src; run;\n"
        "proc means data=det noprint out=agg; class k; var v; run;\n"
        "data j; merge det(in=a) agg(in=b); by k; if a and b; run;\n"
    )
    plan = _plan(text)
    materializadas = [e for e in plan.graph.edges() if e.materialize is not None]
    assert materializadas and materializadas[0].materialize == "temp_table"
    assert any(p.default == "temp_table" for p in plan.pending)
