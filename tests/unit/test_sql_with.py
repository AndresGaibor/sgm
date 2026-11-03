"""Portabilidad de funciones SQL y cadenas de PROC SQL en `WITH` para la base (Impala).

Cada prueba mira un comportamiento con un programa SAS mínimo escrito en la propia prueba.
"""

import sqlglot

from sgm.catalog.config import Engines, Env, Project
from sgm.compile import compile_project
from sgm.ir.models import Operator
from sgm.ir.sql_portability import is_portable, load_sql_portable, unportable_functions
from sgm.passes import db_sql

PROGRAMA_CADENA = """
proc import datafile="/data/clientes.csv" out=work.clientes dbms=csv replace;
run;
proc sql;
create table work.activos as
select id, saldo from work.clientes where saldo > 10;
create table work.totales as
select id, sum(saldo) as tot from work.activos group by id;
quit;
proc export data=work.totales outfile="/data/salida.csv" dbms=csv replace;
run;
"""

PROGRAMA_CATS = """
proc import datafile="/data/clientes.csv" out=work.clientes dbms=csv replace;
run;
proc sql;
create table work.limpio as
select id from work.clientes where cats(nombre, 'x') = 'yx';
quit;
"""


def _plan(program: str):
    env = Env(
        engines=Engines(),
        project=Project(placement_strategy="push_to_db", target_engine="impala"),
    )
    compiled, _ = compile_project({"p.sas": program}, env=env)
    return compiled["p.sas"].plan


def _sql_de_base(plan) -> list[str]:
    return [str(op.params["sql"]) for op in plan.graph.operators() if op.kind == "exec_sql"]


def _op(kind: str, params: dict, placement: str = "db:impala") -> Operator:
    return Operator(id=kind, kind=kind, params=params, placement=placement)


def test_funcion_portable_se_acepta():
    assert is_portable("upper(a)")


def test_cats_no_es_portable():
    assert unportable_functions("cats(a, b)") == ["cats"]


def test_input_con_formato_no_es_portable():
    assert unportable_functions("input(x, 8.)") == ["input"]


def test_case_es_palabra_clave_y_no_cuenta_como_funcion():
    assert is_portable("CASE WHEN a = 1 THEN 2 END")


def test_substr_se_reconoce_aunque_sqlglot_lo_escriba_como_substring():
    assert is_portable("substr(a, 1, 2)")


def test_funcion_anidada_no_portable_se_detecta_dentro():
    assert unportable_functions("upper(cats(a, b))") == ["cats"]


def test_json_portable_solo_incluye_status_portable():
    portables = load_sql_portable()
    assert "sum" in portables
    assert "cats" not in portables
    assert "substrn" not in portables  # status translated


def test_expresion_con_funcion_sas_no_genera_sql_de_base():
    assert db_sql.sas_to_sql("cats(a, b) = 'x'") is None


def test_expresion_portable_pasa_a_sql_de_base():
    assert db_sql.sas_to_sql("saldo > 10") == "saldo > 10"


def test_and_u_or_no_cuentan_como_funciones():
    assert unportable_functions("saldo > 10 and (id = 1 or not activo)") == []


def test_cadena_de_base_se_escribe_con_with_y_sin_subconsultas():
    lectura = _op("read", {"dataset": "impala.clientes"})
    filtro = _op("filter", {"expression": "saldo > 10"}, placement="db:impala")
    agregado = _op(
        "aggregate",
        {
            "group_by": ["id"],
            "aggregations": [{"expression": "sum(saldo)", "alias": "tot"}],
        },
        placement="db:impala",
    )
    sql = db_sql.render([lectura, filtro, agregado])
    assert sql is not None
    assert sql.startswith("WITH sgm_paso0 AS (SELECT * FROM impala.clientes), ")
    assert "sgm_paso1 AS (SELECT * FROM sgm_paso0 WHERE saldo > 10)" in sql
    assert sql.endswith("SELECT * FROM sgm_paso2")
    assert "FROM (" not in sql


def test_with_generado_es_sql_que_sqlglot_lee_en_dialecto_hive():
    lectura = _op("read", {"dataset": "impala.clientes"})
    filtro = _op("filter", {"expression": "saldo > 10"}, placement="db:impala")
    sql = db_sql.render([lectura, filtro])
    assert sqlglot.transpile(sql, write="hive")[0].startswith("WITH sgm_paso0 AS")


def test_cadena_con_funcion_sas_no_se_renderiza():
    lectura = _op("read", {"dataset": "impala.clientes"})
    filtro = _op("filter", {"expression": "cats(a, b) = 'x'"}, placement="db:impala")
    assert db_sql.render([lectura, filtro]) is None


def test_proc_sql_encadenado_se_fusiona_en_base_con_with():
    sentencias = _sql_de_base(_plan(PROGRAMA_CADENA))
    assert len(sentencias) == 1
    assert "WITH sgm_paso" in sentencias[0]
    assert "FROM (" not in sentencias[0]


def test_filtro_con_funcion_sas_no_entra_a_la_base():
    plan = _plan(PROGRAMA_CATS)
    assert _sql_de_base(plan) == []
    assert any(op.kind == "filter" for op in plan.graph.operators())
