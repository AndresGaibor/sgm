"""Regresiones de seguridad del emisor SQL con identificadores ficticios."""

from __future__ import annotations

import pytest
import sqlglot
from sqlglot import exp

from sgm.catalog.config import Env, Project
from sgm.compile import compile_project
from sgm.frontend.sql_normalize import normalize
from sgm.ir.sql_render import render as render_sql
from sgm.ir.sql_tree import Item, SelectSpec, Source, SqlTree, SqlUnsafeIdentifier, build

_PAYLOAD_SQL = "x JOIN archivo_auxiliar a ON 1=1"


def _plan_sql(body: str):
    source = f"proc sql;\n{body.rstrip().rstrip(';')};\nquit;"
    env = Env(project=Project(placement_strategy="push_to_db", target_engine="impala"))
    compiled, _ = compile_project(
        {"caso.sas": source}, library_engines={"LZ": "impala"}, env=env
    )
    return compiled["caso.sas"].plan


@pytest.mark.parametrize(
    "body",
    [
        f"create table work.out as select * from LZ.'{_PAYLOAD_SQL}'n",
        "create table work.out as select q.k from LZ.tabla as "
        "'q JOIN archivo_auxiliar a ON 1=1'n",
        "create table work.out as select k as 'k FROM archivo_auxiliar a'n from LZ.tabla",
    ],
)
def test_sql_con_identificador_hostil_no_emite_consulta(body):
    plan = _plan_sql(body)

    assert not [op for op in plan.graph.operators() if op.kind == "exec_sql"]
    pendientes = [op for op in plan.graph.operators() if op.params.get("reason")]
    assert any(op.params["reason"] == "SQL_NO_SOPORTADO" for op in pendientes)
    assert all(_PAYLOAD_SQL not in " ".join(op.notes) for op in pendientes)


def test_sql_tree_parsea_identificador_hostil_pero_emisores_lo_rechazan():
    normalized = normalize('CREATE TABLE "out AS SELECT 1; --" AS SELECT k FROM LZ.tabla')
    tree = build(normalized.text)

    assert getattr(tree, "identifiers_portable", None) is False
    with pytest.raises(SqlUnsafeIdentifier, match="identificador SQL no representable"):
        render_sql(tree, normalized)


def test_render_sql_revalida_los_identificadores_actuales_del_arbol():
    normalized = normalize("SELECT k FROM LZ.tabla")
    tree = build(normalized.text)
    tree.selects[0].base = Source("LZ.tabla JOIN archivo_auxiliar a ON 1=1")

    with pytest.raises(SqlUnsafeIdentifier):
        render_sql(tree, normalized)


def test_render_sql_rechaza_un_arbol_manual_con_fuente_no_portable():
    tree = SqlTree(None, [SelectSpec(base=Source("tabla JOIN auxiliar"), items=[Item("1")])])

    with pytest.raises(SqlUnsafeIdentifier):
        render_sql(tree, normalize("SELECT 1"))


def test_apostrofe_duplicado_en_lateral_sql_no_abre_una_clausula():
    plan = _plan_sql(
        "create table work.out as select texto from LZ.tabla "
        "where texto = 'O''Reilly'"
    )
    (consulta,) = [op for op in plan.graph.operators() if op.kind == "exec_sql"]
    sql = consulta.params["sql"]

    arbol = sqlglot.parse_one(sql, read="hive")
    literales = [n.this for n in arbol.find_all(exp.Literal) if n.is_string]
    assert "O'Reilly" in literales
