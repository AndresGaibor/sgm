"""Criterios de salida del hito 6: fixtures, evidencia de cada nodo, carga externa, CLI y secretos."""

import json
import re
from pathlib import Path

from typer.testing import CliRunner

from sgm.cli import app
from sgm.compile import compile_project
from sgm.emit.guide_md import render_guide
from sgm.emit.plan_json import plan_to_dict
from sgm.frontend.splitter import ZERO_WIDTH, split_nodes
from tests.support.spec_invariants import coverage_problems, plan_problems

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "fixtures" / "sas"
CLIENT = FIXTURES / "client"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace").replace(ZERO_WIDTH, "")


def test_todos_los_fixtures_compilan_sin_excepcion():
    files = {
        p.relative_to(FIXTURES).as_posix(): p.read_text(encoding="utf-8", errors="replace")
        for p in sorted(FIXTURES.rglob("*.sas"))
    }
    compiled, _ = compile_project(files)
    assert len(compiled) == len(files) > 0
    problems = [p for c in compiled.values() for p in plan_problems(c.plan)]
    assert problems == []


def test_cada_etiqueta_del_cliente_grande_aparece_en_evidencia_o_no_migrado():
    text = _text(CLIENT / "client_large.sas")
    labels = {n.label for n in split_nodes(text) if n.label is not None}
    compiled, _ = compile_project({"client_large.sas": text})
    plan = compiled["client_large.sas"].plan
    assert coverage_problems(plan, labels) == []
    assert len(labels) >= 300  # hay más de 300 textos de etiqueta distintos


def test_la_carga_externa_del_cliente_se_detecta_como_un_solo_operador():
    compiled, _ = compile_project({"client_poc.sas": _text(CLIENT / "client_poc.sas")})
    plan = compiled["client_poc.sas"].plan
    loads = [o for o in plan.graph.operators() if o.kind == "external_load"]
    assert len(loads) == 1
    assert loads[0].placement == "db:impala"


def test_guia_y_json_no_contienen_secretos_sin_enmascarar():
    compiled, _ = compile_project({"client_large.sas": _text(CLIENT / "client_large.sas")})
    plan = compiled["client_large.sas"].plan
    blob = render_guide(plan) + json.dumps(plan_to_dict(plan), ensure_ascii=False)
    secrets = re.findall(r"(?i)(pass\s*=\s*|pwencode\s+in\s*=\s*)(?!'?\*\*\*)(\S+)", blob)
    assert secrets == []


def test_cli_compile_escribe_guia_y_plan_por_programa(tmp_path):
    result = CliRunner().invoke(
        app, ["compile", str(CLIENT / "client_poc.sas"), "--out", str(tmp_path)]
    )
    assert result.exit_code == 0, result.output
    guide = tmp_path / "client_poc.guide.md"
    plan = tmp_path / "client_poc.plan.json"
    assert guide.exists() and plan.exists()
    assert "# Guía de migración: client_poc.sas" in guide.read_text(encoding="utf-8")
    assert json.loads(plan.read_text(encoding="utf-8"))["program"] == "client_poc.sas"


def test_cli_compile_carpeta_escribe_un_par_por_programa(tmp_path):
    source = FIXTURES / "synthetic" / "migration_matrix"
    result = CliRunner().invoke(app, ["compile", str(source), "--out", str(tmp_path)])
    assert result.exit_code == 0, result.output
    assert len(list(tmp_path.glob("*.plan.json"))) == len(list(tmp_path.glob("*.guide.md"))) >= 1
