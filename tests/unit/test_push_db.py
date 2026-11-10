"""Estrategia `push_to_db` (R5): cargar una vez, calcular en la base, exportar desde el flujo.

El caso del plan: un CSV que se carga, un cálculo en SQL (WHERE, columna calculada) y una
exportación a CSV. Con `push_to_db` sale una carga única, un `exec_sql` fusionado en la base y un
`write_file` en el flujo. Con `flow`, el equivalente en componentes de flujo.
"""

from pathlib import Path

from sgm.catalog.config import Engines, Env, Project
from sgm.compile import compile_project
from sgm.talend_item.desde_plan import plan_a_jobs
from sgm.talend_item.escritura import escribir_job

PROGRAMA = """
proc import datafile="/data/clientes.csv" out=work.clientes dbms=csv replace;
run;
proc sql;
create table work.limpio as
select id, saldo * 2 as doble from work.clientes where saldo > 10;
quit;
proc export data=work.limpio outfile="/data/salida.csv" dbms=csv replace;
run;
"""


def _env(strategy: str) -> Env:
    return Env(
        engines=Engines(),
        project=Project(placement_strategy=strategy, target_engine="impala"),
    )


def _plan(strategy: str):
    compiled, _ = compile_project({"p.sas": PROGRAMA}, env=_env(strategy))
    return compiled["p.sas"].plan


def _components(plan) -> list[tuple[str, str | None, str]]:
    """(tipo, ubicación, componente) de cada operador con componente."""
    return [
        (op.kind, op.placement, op.component["name"])
        for op in plan.graph.operators()
        if op.component and op.component["name"] != "none"
    ]


def test_push_to_db_una_carga_un_exec_sql_y_un_write_file():
    components = _components(_plan("push_to_db"))
    kinds = [kind for kind, _, _ in components]
    assert kinds.count("external_load") == 1
    assert kinds.count("exec_sql") == 1
    assert kinds.count("write_file") == 1
    load = next(c for c in components if c[0] == "external_load")
    assert load[1] == "db:impala" and load[2] == "tImpalaOutput"
    sql = next(c for c in components if c[0] == "exec_sql")
    assert sql[1] == "db:impala" and sql[2] == "tImpalaRow"


def test_push_to_db_el_sql_fusionado_contiene_el_filtro_y_la_columna_calculada():
    plan = _plan("push_to_db")
    sql_ops = [op for op in plan.graph.operators() if op.kind == "exec_sql"]
    assert len(sql_ops) == 1
    text = sql_ops[0].params["sql"].lower()
    assert "where" in text and "saldo > 10" in text
    assert "doble" in text and "saldo * 2" in text
    assert "create table" in text


def test_push_to_db_no_deja_tjava_en_la_cadena():
    components = _components(_plan("push_to_db"))
    assert not any(name == "tJava" for _, _, name in components)


def test_push_to_db_la_exportacion_queda_en_flujo_con_frontera():
    plan = _plan("push_to_db")
    export = [op for op in plan.graph.operators() if op.kind == "write_file"]
    assert export and export[0].placement == "flow"
    boundary = [op for op in plan.graph.operators() if op.kind == "read" and op.placement == "flow"]
    assert boundary, "la salida desde la base necesita un read de frontera"


def test_flow_mantiene_los_componentes_de_flujo():
    components = _components(_plan("flow"))
    names = {name for _, _, name in components}
    assert "tFileInputDelimited" in names and "tFileOutputDelimited" in names
    assert not any(name in ("tImpalaRow", "tImpalaOutput") for _, _, name in components)


def test_push_to_db_conserva_el_destino_calificado_en_la_misma_base():
    ruta = (
        Path(__file__).resolve().parents[1]
        / "corpus"
        / "L2"
        / "l2_16_sql_en_misma_base"
        / "programa.sas"
    )
    env = _env("push_to_db")
    compiled, _ = compile_project(
        {ruta.name: ruta.read_text(encoding="utf-8")},
        env=env,
        library_engines={"LZ": "impala"},
    )

    sql_ops = [op for op in compiled[ruta.name].plan.graph.operators() if op.kind == "exec_sql"]

    assert len(sql_ops) == 1
    assert sql_ops[0].placement == "db:impala"
    assert sql_ops[0].params["sql"].startswith("CREATE TABLE LZ.salida AS")
    assert "FROM LZ.origen" in sql_ops[0].params["sql"]


def test_exec_sql_de_impala_se_emite_en_un_timpalarow_sin_inventar_conexion(tmp_path):
    ruta = (
        Path(__file__).resolve().parents[1]
        / "corpus"
        / "L2"
        / "l2_16_sql_en_misma_base"
        / "programa.sas"
    )
    compiled, _ = compile_project(
        {ruta.name: ruta.read_text(encoding="utf-8")},
        env=_env("push_to_db"),
        library_engines={"LZ": "impala"},
    )
    plan = compiled[ruta.name].plan

    resultado = plan_a_jobs(plan, {})
    job = resultado.jobs[0]
    filas = [nodo for nodo in job.nodos if nodo.componente == "tImpalaRow"]
    assert len(filas) == 1
    parametros = {fila[1]: fila[2] for fila in filas[0].parametros if isinstance(fila, tuple)}
    assert parametros["QUERY"] == '"' + next(
        op.params["sql"] for op in plan.graph.operators() if op.kind == "exec_sql"
    ) + '"'
    assert parametros["USE_EXISTING_CONNECTION"] == "false"
    assert any(
        pendiente.codigo == "P-OPERADOR-SIN-SOPORTE"
        and "configuración de sesión" in pendiente.mensaje
        for pendiente in resultado.pendientes
    )
    assert any(pendiente.codigo == "P-CONEXION-BASE" for pendiente in resultado.pendientes)

    item, _ = escribir_job(job, tmp_path)
    texto = item.read_text(encoding="utf-8")
    assert "CREATE TABLE LZ.salida AS" in texto
