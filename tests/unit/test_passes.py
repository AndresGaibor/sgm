"""Pruebas de las pasadas 1 a 4 sobre programas pequeños."""

from sgm.compile import compile_project


def _compile(text: str, engines: dict[str, str] | None = None):
    compiled, _ = compile_project({"p.sas": text}, library_engines=engines)
    return compiled["p.sas"]


def _kind(plan, kind):
    return [o for o in plan.graph.operators() if o.kind == kind]


# --- pasada 1: grafo ------------------------------------------------------


def test_p01_arista_del_productor_al_consumidor():
    plan = _compile("data a; set s; run;\ndata b; set a; run;").plan
    assert [e.dataset for e in plan.graph.edges()].count("WORK.a") == 1


def test_p01_reescritura_versiona_la_arista():
    """La lectura posterior a la reescritura usa la versión nueva; la primera versión, sin lector, va a write."""
    plan = _compile("data a; set s; run;\ndata a; set s; run;\ndata b; set a; run;").plan
    datasets = {e.dataset for e in plan.graph.edges()}
    assert "WORK.a@v2" in datasets
    assert any(w.params["dataset"] == "WORK.a" for w in _kind(plan, "write"))


def test_p01_escritura_permanente_termina_en_write():
    plan = _compile("data lz.t; set s; run;").plan
    writes = _kind(plan, "write")
    assert [w.params["dataset"] for w in writes] == ["LZ.t"]


def test_p01_lectura_permanente_sin_productor_es_fuente():
    plan = _compile("data b; set lz.t; run;").plan
    (read,) = _kind(plan, "read")
    assert read.params["dataset"] == "LZ.t"
    assert not plan.graph.predecessors(read.id)


# --- pasada 2: fontanería -------------------------------------------------


def test_p02_marca_fontaneria_y_conserva_proc_de_biblioteca_permanente():
    text = (
        "%put traza;\n"
        'x "sleep 3";\n'
        "proc datasets library=work nolist; delete tmp; quit;\n"
        "proc datasets library=lz nolist; delete t; quit;\n"
    )
    plan = _compile(text).plan
    categories = sorted(nm.what for nm in plan.not_migrated)
    assert len(plan.not_migrated) == 3, categories
    remaining = [
        o for o in plan.graph.operators() if "lz" in str(o.params.get("statement", "")).lower()
    ]
    assert remaining and all(o.status == "hueco" for o in remaining)


def test_p02_sentencias_de_sesion_no_son_datos_y_se_registran():
    plan = _compile(
        "proc sql;\n connect to impala (server='h');\n disconnect from impala;\nquit;"
    ).plan
    assert len(plan.not_migrated) == 2
    assert all(o.kind != "unsupported" or o.status != "hueco" for o in plan.graph.operators())


# --- pasada 3: carga externa por estructura -------------------------------


def _bulkload(launch: str, wait: str) -> str:
    return (
        f"%macro {launch};\n"
        'x "nohup run.sh &";\n'
        "%mend;\n"
        f"%macro {wait};\n"
        'x "until [ 1 -eq 0 ]; do n=$(ps -ef | wc -l); done";\n'
        "%mend;\n"
        f"%{launch};\n%{wait};\n"
    )


def test_p03_detecta_carga_externa_por_estructura():
    plan = _compile(_bulkload("lanza_carga", "espera_carga")).plan
    loads = _kind(plan, "external_load")
    assert len(loads) == 1
    assert loads[0].params["launch"].startswith("comandos de sistema en segundo plano")


def test_p03_la_deteccion_no_depende_de_los_nombres_de_macro():
    named = _compile(_bulkload("lanza_carga", "espera_carga")).plan
    random_names = _compile(_bulkload("zq7_a1", "kw3_b9")).plan
    assert [o.signature for o in _kind(named, "external_load")] == [
        o.signature for o in _kind(random_names, "external_load")
    ]
    assert len(_kind(random_names, "external_load")) == 1


def test_p03_sin_espera_no_hay_carga_externa():
    plan = _compile('%macro lanza;\nx "nohup run.sh &";\n%mend;\n%lanza;').plan
    assert _kind(plan, "external_load") == []


# --- pasada 4: ubicación --------------------------------------------------


def test_p04_empuja_a_la_base_y_corta_al_flujo_con_frontera():
    text = (
        "proc sql;\n"
        " create table impala_t as select * from connection to impala (select a from t);\n"
        "quit;\n"
        "data w; set impala.impala_t; where a > 1; run;\n"
        "data w2; set w; y = input(a, 8.); run;\n"
    )
    plan = _compile(text, engines={"IMPALA": "impala"}).plan
    (filtro,) = _kind(plan, "filter")
    (derivacion,) = _kind(plan, "derive")
    assert filtro.placement == "db:impala"
    assert derivacion.placement == "flow"
    boundary = [o for o in _kind(plan, "read") if o.placement == "flow"]
    assert len(boundary) == 1


def test_p04_operador_sin_entrada_de_base_queda_en_flujo():
    plan = _compile("data a; set s; where x > 1; run;").plan
    assert all(o.placement == "flow" for o in _kind(plan, "filter"))
