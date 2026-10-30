"""Partición por componente conexo (R8): un subjob por componente de conexiones de filas."""

from sgm.catalog.config import Env, Project
from sgm.compile import compile_project
from sgm.ir.models import Edge, Graph, Operator
from sgm.passes import p08_partition


def _subjobs(program: str, max_components: int = 200):
    env = Env(project=Project(max_components_per_job=max_components))
    compiled, _ = compile_project({"p.sas": program}, env=env)
    plan = compiled["p.sas"].plan
    return plan, plan.jobs[0].subjobs


def test_dos_flujos_independientes_de_distinta_forma_son_dos_subjobs():
    plan, subjobs = _subjobs("data a; set s1; x = 1; run;\ndata b; set s2; where y > 2; run;\n")
    assert len(subjobs) == 2


def test_una_cadena_de_filas_es_un_solo_subjob():
    plan, subjobs = _subjobs("data a; set s1; where x > 1; y = x + 1; run;\n")
    assert len(subjobs) == 1


def test_una_sentencia_de_base_es_su_propio_subjob():
    plan, subjobs = _subjobs(
        "proc sql;\n execute (create table lz.t as select 1 from s) by impala;\nquit;\n"
    )
    assert all(len(s) == 1 for s in subjobs)
    kinds = [plan.graph.operator(s[0]).kind for s in subjobs]
    assert "exec_sql" in kinds


def _chain(n: int) -> Graph:
    """Cadena de n filtros: cada uno consume al anterior."""
    graph = Graph()
    for i in range(n):
        graph.add_operator(Operator(id=f"op{i:05d}", kind="filter", params={"expression": "x > 1"}))
        if i:
            graph.add_edge(Edge(f"op{i - 1:05d}", f"op{i:05d}", "(interno)"))
    return graph


def test_el_limite_de_componentes_parte_el_subjob_en_trozos():
    graph = _chain(5)
    subjobs, cuts = p08_partition._subjobs(graph, max_components=2)
    assert [len(s) for s in subjobs] == [2, 2, 1]
    assert cuts.count("tamano_maximo") == 3


def test_los_subjobs_siguen_el_orden_topologico():
    plan, subjobs = _subjobs("data a; set s1; x = 1; run;\ndata b; set a; y = 2; run;\n")
    order = plan.graph.topological()
    positions = [order.index(op) for subjob in subjobs for op in subjob]
    assert positions == sorted(positions)
