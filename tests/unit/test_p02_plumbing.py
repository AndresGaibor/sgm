"""La pasada no debe descartar efectos de PROC DELETE sobre bibliotecas permanentes."""

from sgm.compile import compile_file, project_base
from sgm.frontend.program import analyze_program
from sgm.ir.models import Graph, Operator, Plan
from sgm.passes.base import PassContext
from sgm.passes.p02_plumbing import mark


def test_delete_permanente_permanece_como_hueco_y_no_se_quita_del_plan():
    statement = "proc delete library=clientes data=tabla;"
    graph = Graph()
    operator = Operator(
        id="delete-1",
        kind="unsupported",
        params={"statement": statement, "procedure": "delete", "reason": "PROC_NO_SOPORTADO"},
        status="hueco",
    )
    graph.add_operator(operator)
    plan = Plan(program="programa.sas")

    mark(graph, PassContext(plan=plan))

    assert operator.status == "hueco"
    assert "plumbing" not in operator.params
    assert plan.not_migrated == []


def test_compilacion_conserva_el_hueco_del_borrado_permanente():
    source = "proc delete library=clientes data=tabla; run;"
    plan = compile_file(analyze_program({"programa.sas": source}), "programa.sas", project_base()).plan

    (operator,) = plan.graph.operators()
    assert operator.kind == "unsupported"
    assert operator.status == "hueco"
