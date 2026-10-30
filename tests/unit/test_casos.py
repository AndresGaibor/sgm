"""Casos declarativos (F1.3): cada carpeta de `tests/cases/` se compara con lo que produce `compile`.

`expected.yaml` dice el entorno (`default`, `push_to_db`, `reports_log`, `flow`) y lo que debe salir:
`components` (deben aparecer), `operators` (`kind` y `component`), `gaps` (motivos exactos) y
`max_tjava`. Un caso `ir` no tiene SAS: describe un operador de la IR y comprueba la escalera.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from sgm.catalog.config import Engines, Env, Project, load_env
from sgm.compile import compile_project
from sgm.ir.models import Operator
from sgm.passes.p10_components import ROOT, _tjava, choose, load_engines, load_rules

CASES = ROOT / "tests" / "cases"


def _env(name: str) -> Env:
    if name == "default":
        return load_env(ROOT / "env")
    if name == "push_to_db":
        return Env(
            engines=Engines(),
            project=Project(placement_strategy="push_to_db", target_engine="impala"),
        )
    if name == "reports_log":
        return Env(project=Project(reports="log"))
    if name == "flow":
        return Env(project=Project(placement_strategy="flow"))
    raise ValueError(f"entorno de caso desconocido: {name}")


def _folders() -> list[Path]:
    return sorted(p for p in CASES.iterdir() if (p / "expected.yaml").exists())


def _check_sas(folder: Path, doc: dict) -> None:
    text = (folder / doc["input"]).read_text(encoding="utf-8")
    compiled, _ = compile_project({"caso.sas": text}, env=_env(doc["env"]))
    plan = compiled["caso.sas"].plan
    expect = doc["expect"]
    operators = [op for op in plan.graph.operators() if op.component]
    names = {op.component["name"] for op in operators}
    for name in expect.get("components", []):
        assert name in names, f"falta el componente {name}; hay {sorted(names)}"
    for wanted in expect.get("operators", []):
        found = [
            op
            for op in plan.graph.operators()
            if op.kind == wanted["kind"]
            and (op.component or {}).get("name", "none") == wanted.get("component", op.kind)
        ]
        assert found, f"falta un operador {wanted}"
    if "gaps" in expect:
        assert sorted(g.reason for g in plan.gaps) == sorted(expect["gaps"])
    tjava = sum(1 for op in operators if op.component["name"] == "tJava")
    assert tjava <= expect.get("max_tjava", tjava)


def _check_ir(doc: dict) -> None:
    rules = load_rules()
    op = Operator(
        id="x",
        kind=doc["ir"]["kind"],
        placement=doc["ir"]["placement"],
        status=doc["ir"]["status"],
        signature="s",
    )
    found = choose(op, rules, load_engines()) or _tjava(op, rules)
    assert found is not None
    assert found[1] in doc["expect"]["components"]


@pytest.mark.parametrize("folder", _folders(), ids=lambda p: p.name)
def test_caso_da_lo_que_dice_su_expected(folder: Path):
    doc = yaml.safe_load((folder / "expected.yaml").read_text(encoding="utf-8"))
    if "ir" in doc:
        _check_ir(doc)
    else:
        _check_sas(folder, doc)
