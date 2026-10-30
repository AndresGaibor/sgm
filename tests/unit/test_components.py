"""Pruebas de la pasada 10: escalera de componentes, reglas en YAML y existencia en el catálogo."""

import json

from sgm.compile import compile_project
from sgm.ir.models import Operator
from sgm.passes.p10_components import ROOT, _tjava, choose, load_engines, load_rules

FIXTURES = ROOT / "tests" / "fixtures" / "sas"
RULES = load_rules()
ENGINES = load_engines()


def _catalog_names() -> set[str]:
    """Nombres de componentes del catálogo de Talend copiado (dos fuentes)."""
    components = json.loads((ROOT / "rules/talend/components.json").read_text(encoding="utf-8"))
    inventory = json.loads(
        (ROOT / "rules/talend/official-component-inventory.json").read_text(encoding="utf-8")
    )
    return set(components["components"]) | {entry["name"] for entry in inventory["components"]}


def _op(kind: str, placement: str | None = None, **params) -> Operator:
    return Operator(id="x", kind=kind, params=params, placement=placement, signature="s")


def _component(op: Operator) -> str | None:
    found = choose(op, RULES, ENGINES) or _tjava(op, RULES)
    return found[1] if found else None


def _plan(text: str):
    compiled, _ = compile_project({"p.sas": text})
    return compiled["p.sas"].plan


def test_reglas_tienen_forma_y_ids_unicos():
    assert len({r.id for r in RULES}) == len(RULES) >= 18
    assert all(r.confidence in {"alta", "media", "baja"} for r in RULES)


def test_escalera_motor_antes_que_componente_especifico():
    assert _component(_op("read", "db:impala")) == "tImpalaInput"
    assert _component(_op("exec_sql", "db:impala")) == "tImpalaRow"


def test_escalera_especifico_antes_que_tmap():
    assert _component(_op("sort", "flow")) == "tSortRow"
    assert _component(_op("map", "flow")) == "tMap"


def test_estado_por_fila_es_tjavarow_con_revision():
    rule, component = choose(_op("stateful_row", "flow"), RULES, ENGINES)
    assert component == "tJavaRow" and rule.rung == 4


def test_tjava_solo_como_ultimo_recurso_y_con_el_sas_original():
    plan = _plan("data a; set s; where x > 1; run;")
    tjava = [o for o in plan.graph.operators() if o.component and o.component["name"] == "tJava"]
    assert tjava == []
    flujo_sin_regla = _op("exec_sql", "flow", sql="create table t as select 1 from s")
    assert _component(flujo_sin_regla) == "tJava"


def test_ningun_componente_se_marca_verificado():
    plan = _plan(
        "data a; set s; where x > 1; run;\nproc sort data=a; by k; run;\n"
        "proc sql;\n execute (create table lz.t as select 1 from s) by impala;\nquit;\n"
    )
    estados = {o.component["status"] for o in plan.graph.operators() if o.component}
    assert estados and estados <= {"candidato"}


def test_funcion_sin_equivalente_queda_como_hueco_con_la_funcion_en_la_firma():
    plan = _plan("data a; set s; z = fn_inventada(x); run;")
    gaps = [g for g in plan.gaps if g.reason == "FUNCION_NO_MAPEADA"]
    assert gaps and any("fn_inventada" in g.signature for g in gaps)


def test_todos_los_componentes_usados_existen_en_el_catalogo():
    """Prueba obligatoria: cada componente que sale de la compilación está en el catálogo copiado."""
    names = _catalog_names()
    usados: set[str] = set()
    for path in sorted(FIXTURES.rglob("*.sas")):
        if "real" in path.parts:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        plan = _plan(text)
        usados |= {o.component["name"] for o in plan.graph.operators() if o.component}
    usados.discard("none")
    assert sorted(usados - names) == []
    assert usados, "la compilación no produjo componentes"


def test_los_motores_de_las_reglas_existen_en_el_catalogo():
    names = _catalog_names()
    for engine, comps in ENGINES.items():
        for comp in comps.values():
            if comp:
                assert comp in names, f"{engine}: {comp} fuera del catálogo"
