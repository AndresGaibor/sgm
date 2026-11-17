"""Segundo programa SAS, distinto del cliente y no usado para diseñar reglas.

`independiente/inventario_mensual.sas` tiene un %let, un WHERE, un SORT con OUT=, un MERGE con
IN=, un PROC MEANS con CLASS y un DATA step con macrovariable en el nombre de salida. Las
pruebas fijan lo que el compilador demuestra con ese código; las tablas de origen no tienen
esquema en el repositorio, así que sus tipos quedan como huecos y no se inventan.
"""

from pathlib import Path

import pytest

from sgm.compile import compile_project
from sgm.emit.guide_md import render_guide
from sgm.frontend.splitter import ZERO_WIDTH
from tests.support.spec_invariants import plan_problems

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "sas"
REL = "independiente/inventario_mensual.sas"


@pytest.fixture(scope="module")
def plan():
    text = (FIXTURES / REL).read_text(encoding="utf-8", errors="replace").replace(ZERO_WIDTH, "")
    compiled, _ = compile_project({REL: text})
    return compiled[REL].plan


def _operadores(plan, kind):
    return [op for op in plan.graph.operators() if op.kind == kind]


def test_programa_independiente_compila_sin_problemas_de_plan(plan):
    assert plan_problems(plan) == []


def test_sort_con_out_queda_soportado_y_ordena_por_las_claves(plan):
    (orden,) = _operadores(plan, "sort")
    assert orden.status == "soportado"
    assert orden.params["by"] == ["sucursal", "producto"]


def _tipo_y_estado_del_join(plan):
    """El join puede quedar suelto o como paso dentro de un tMap fundido (pasada 6)."""
    for op in plan.graph.operators():
        if op.kind == "join":
            return op.params["join_type"], op.status
        if op.kind == "map":
            for st in op.params.get("steps", []):
                if st.get("kind") == "join":
                    return st["params"]["join_type"], op.status
    raise AssertionError("sin join")


def test_merge_con_in_se_compila_como_join(plan):
    tipo, estado = _tipo_y_estado_del_join(plan)
    assert estado == "soportado"
    assert tipo == "inner"  # `if en_stock and en_precio;` filtra a interior


def test_proc_means_sin_nway_ni_drop_conserva_pendiente_de_esquema(plan):
    # proc.pdf, pp. 1572–1573: CLASS genera tipos y columnas automáticas aún no modelados.
    assert _operadores(plan, "aggregate") == []
    (pendiente,) = [op for op in _operadores(plan, "unsupported")
                   if op.params.get("procedure") == "means"]
    assert pendiente.status == "hueco"
    assert pendiente.params["pending_code"] == "P-MEANS-TYPE-NO-DEMOSTRADO"
    assert pendiente.params["inputs"] == ["WORK.precios_vigentes"]
    assert not pendiente.params.get("outputs")


def test_macrovariable_del_nombre_de_salida_se_resuelve(plan):
    (escritura,) = [op for op in plan.graph.operators() if op.kind == "write"]
    assert escritura.params["dataset"] == "OUT.inventario_202501"


def test_tablas_sin_esquema_quedan_como_huecos_de_tipo_desconocido(plan):
    """El repositorio no trae el DESCRIBE de `src.*`: sin tipos no se migra, no se adivina."""
    assert plan.gaps, "debe haber huecos porque no hay esquema de origen"
    assert {gap.reason for gap in plan.gaps} == {"TIPO_DESCONOCIDO", "PROC_NO_SOPORTADO"}
    (proc_gap,) = [gap for gap in plan.gaps if gap.reason == "PROC_NO_SOPORTADO"]
    assert proc_gap.evidence[0].line_start == 22


def test_la_guia_pide_confirmar_el_tipo_del_map_parcial(plan):
    guia = render_guide(plan)
    assert "tipo no confirmado" in guia
    assert "confirmar con el esquema real" in guia
