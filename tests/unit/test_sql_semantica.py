"""Reglas de `rules/sas/sql-semantica.yaml` aplicadas por el lowering y el generador de SQL.

Cada prueba mira un comportamiento con un programa SAS mínimo escrito en la propia prueba.
"""

from pathlib import Path

import pytest

from sgm.catalog.config import Engines, Env, Project
from sgm.compile import compile_project
from sgm.frontend.sql_normalize import normalize
from sgm.ir import sql_semantics
from sgm.ir.models import Operator

PROGRAMA_PUSH = """
proc import datafile="/data/clientes.csv" out=work.clientes dbms=csv replace;
run;
proc sql;
%s
quit;
"""


def _plan(program: str, strategy: str = "flow"):
    env = Env(
        engines=Engines(),
        project=Project(placement_strategy=strategy, target_engine="impala"),
    )
    compiled, _ = compile_project({"p.sas": program}, env=env)
    return compiled["p.sas"].plan


def _operators(plan, kind: str) -> list[Operator]:
    return [op for op in plan.graph.operators() if op.kind == kind]


def _sql_pass(body: str) -> str:
    return f"proc sql;\n{body}\nquit;\n"


def test_el_yaml_trae_las_dos_reglas_con_su_tratamiento():
    reglas = sql_semantics.reglas()
    assert reglas[sql_semantics.AGREGADO].tratamiento == "pendiente"
    assert reglas[sql_semantics.SELECT_INTO].tratamiento == "programa_anfitrion"


def test_tratamiento_desconocido_en_el_yaml_falla(tmp_path: Path):
    ruta = tmp_path / "semantica.yaml"
    ruta.write_text(
        "reglas:\n"
        "  - id: agregado-sin-group-by\n    tratamiento: magia\n"
        "  - id: select-into-macrovariable\n    tratamiento: pendiente\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="tratamiento no válido"):
        sql_semantics.cargar(ruta)


def test_regla_desconocida_en_el_yaml_falla(tmp_path: Path):
    ruta = tmp_path / "semantica.yaml"
    ruta.write_text("reglas:\n  - id: regla-inventada\n    tratamiento: pendiente\n", encoding="utf-8")
    with pytest.raises(ValueError, match="regla SQL desconocida"):
        sql_semantics.cargar(ruta)


def test_yaml_sin_una_regla_conocida_falla(tmp_path: Path):
    ruta = tmp_path / "semantica.yaml"
    ruta.write_text(
        "reglas:\n  - id: agregado-sin-group-by\n    tratamiento: pendiente\n", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="faltan reglas SQL"):
        sql_semantics.cargar(ruta)


def test_agregado_con_columna_sin_agrupar_queda_parcial_y_pendiente():
    plan = _plan(_sql_pass("create table work.t as select k, sum(v) as tot from work.s;"))
    (agregado,) = _operators(plan, "aggregate")
    assert agregado.status == "parcial"
    assert agregado.params["pendiente"] == ["k"]
    assert any("AGREGADO_SIN_GROUP_BY" in note for note in agregado.notes)


def test_agregado_con_group_by_no_queda_pendiente():
    plan = _plan(_sql_pass("create table work.t as select k, sum(v) as tot from work.s group by k;"))
    (agregado,) = _operators(plan, "aggregate")
    assert agregado.status == "soportado"
    assert "pendiente" not in agregado.params


def test_group_by_conserva_solo_las_llaves_seleccionadas_y_sus_aliases():
    plan = _plan(
        _sql_pass("create table work.t as select k as categoria, sum(v) as total from work.s group by k;")
    )
    (agregado,) = _operators(plan, "aggregate")

    assert agregado.params["group_outputs"] == [{"expression": "k", "alias": "categoria"}]


def test_group_by_conserva_orden_original_de_salidas():
    plan = _plan(
        _sql_pass("create table work.t as select sum(v) as total, k as categoria from work.s group by k;")
    )
    (agregado,) = _operators(plan, "aggregate")

    assert agregado.params["output_order"] == ["total", "categoria"]


def test_group_by_con_columna_no_agrupada_queda_pendiente():
    plan = _plan(
        _sql_pass(
            "create table work.t as select k, detalle, sum(v) as total "
            "from work.s group by k;"
        )
    )
    (agregado,) = _operators(plan, "aggregate")

    assert agregado.status == "parcial"
    assert agregado.params["pendiente"] == ["detalle"]
    assert sql_semantics.aggregate_pendiente(agregado.params)


def test_agregado_pendiente_no_se_lleva_a_la_base():
    plan = _plan(
        PROGRAMA_PUSH % "create table work.t as select id, sum(saldo) as tot from work.clientes;",
        strategy="push_to_db",
    )
    sentencias = [op.params["sql"] for op in _operators(plan, "exec_sql")]
    assert not any("SUM(" in str(sql).upper() for sql in sentencias)


def test_el_generador_lee_la_regla_del_yaml(monkeypatch):
    """Si la regla cambia a otro tratamiento, el agregado deja de quedar pendiente."""
    otra = sql_semantics.Regla(
        id=sql_semantics.AGREGADO,
        tratamiento="programa_anfitrion",
        etiqueta="AGREGADO_SIN_GROUP_BY",
        descripcion="",
    )
    monkeypatch.setattr(
        sql_semantics,
        "reglas",
        lambda: {sql_semantics.AGREGADO: otra, sql_semantics.SELECT_INTO: otra},
    )
    plan = _plan(_sql_pass("create table work.t as select k, sum(v) as tot from work.s;"))
    (agregado,) = _operators(plan, "aggregate")
    assert agregado.status == "soportado"


def test_remezcla_con_group_by_sigue_pendiente_si_cambia_regla_sin_group_by(monkeypatch):
    otra = sql_semantics.Regla(
        id=sql_semantics.AGREGADO,
        tratamiento="programa_anfitrion",
        etiqueta="AGREGADO_SIN_GROUP_BY",
        descripcion="",
    )
    monkeypatch.setattr(
        sql_semantics,
        "reglas",
        lambda: {sql_semantics.AGREGADO: otra, sql_semantics.SELECT_INTO: otra},
    )
    plan = _plan(
        _sql_pass(
            "create table work.t as select k, detalle, sum(v) as total "
            "from work.s group by k;"
        )
    )
    (agregado,) = _operators(plan, "aggregate")

    assert agregado.status == "parcial"
    assert sql_semantics.aggregate_pendiente(agregado.params)


def test_push_to_db_proyecta_solo_llaves_de_group_by_seleccionadas():
    plan = _plan(
        PROGRAMA_PUSH
        % "create table work.t as select sum(saldo) as total from work.clientes group by id;",
        strategy="push_to_db",
    )
    sql_ops = _operators(plan, "exec_sql")

    assert len(sql_ops) == 1
    texto = sql_ops[0].params["sql"].lower()
    assert "sum(saldo) as total" in texto
    assert "group by id" in texto
    assert "select id" not in texto


def test_push_to_db_conserva_orden_de_salidas_del_select():
    plan = _plan(
        PROGRAMA_PUSH
        % "create table work.t as select sum(saldo) as total, id as codigo "
        "from work.clientes group by id;",
        strategy="push_to_db",
    )
    sql_ops = _operators(plan, "exec_sql")

    assert len(sql_ops) == 1
    texto = sql_ops[0].params["sql"].lower()
    assert "sum(saldo) as total, id as codigo" in texto


def test_select_into_con_agregado_va_a_set_variable_sin_sql():
    plan = _plan(_sql_pass("select count(*) into :n from work.s;"))
    (asignacion,) = _operators(plan, "set_variable")
    assert asignacion.params["variable"] == "n"
    assert asignacion.params["expression"] == "COUNT(*)"
    assert asignacion.params["regla"] == sql_semantics.SELECT_INTO
    assert asignacion.status == "soportado"


def test_select_into_no_genera_sql_de_base_aunque_la_consulta_si():
    plan = _plan(PROGRAMA_PUSH % "select count(*) into :n from work.clientes;", "push_to_db")
    assert _operators(plan, "set_variable")
    for op in _operators(plan, "exec_sql"):
        assert "INTO" not in str(op.params["sql"]).upper()


def test_select_into_varias_variables_asigna_cada_una_a_su_posicion():
    plan = _plan(_sql_pass("select count(*), max(v) into :a, :b from work.s;"))
    valores = {
        op.params["variable"]: op.params["expression"] for op in _operators(plan, "set_variable")
    }
    assert valores == {"a": "COUNT(*)", "b": "MAX(v)"}


def test_select_into_con_trimmed_no_rompe_el_analisis():
    normalized = normalize("select count(*) into :n trimmed from work.s")
    assert normalized.into_vars == [("n", None)]
    assert "trimmed" not in normalized.text.lower()


def test_normalize_reconoce_varias_variables_de_into():
    assert normalize("select a, b into :x, :y from t").into_vars == [("x", None), ("y", None)]


def test_select_into_varias_filas_sin_separador_queda_parcial():
    plan = _plan(_sql_pass("select v into :x from work.s;"))
    (asignacion,) = _operators(plan, "set_variable")
    assert asignacion.status == "parcial"
    assert any("SELECT_INTO" in note for note in asignacion.notes)
