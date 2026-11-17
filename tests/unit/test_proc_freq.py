"""FREQ sin tabla demostrada: reporte o pendiente, nunca agregado supuesto."""

from pathlib import Path

import pytest

from sgm.catalog.config import Env, Project
from sgm.compile import compile_project
from sgm.frontend.lexer import split_statements
from sgm.frontend.steps import parse_steps
from sgm.ir.builder import Builder
from sgm.ir.lower_procs import lower_proc
from sgm.ir.models import Evidence, Graph
from sgm.ir.proc_rules import declared
from sgm.yaml_io import cargar_yaml

ROOT = Path(__file__).resolve().parents[2]
CASE = ROOT / "tests/corpus/L3/l3_32_freq_out_sin_pagina"
CODE = "P-FREQ-OUT-SIN-PAGINA"


def _lower(body):
    step = parse_steps(split_statements(f"PROC FREQ DATA=ventas; {body} RUN;"))[0][0]
    builder = Builder(Graph())
    lower_proc(step, Evidence("p.sas", 1, 1, None), builder)
    return builder.created


def test_freq_sin_out_es_reporte():
    [op] = _lower("TABLES region;")
    assert op.kind == "unsupported"
    assert op.params["reason"] == "REPORTE"
    assert op.params["inputs"] == ["WORK.ventas"]


@pytest.mark.parametrize("body", [
    "TABLES region / OUT=fr;",
    "tables region / missing out = work.fr;",
    "TABLES monto; TABLES region / OUT=fr;",
])
def test_freq_out_en_tables_conserva_pendiente(body):
    [op] = _lower(body)
    assert op.kind == "unsupported"
    assert op.params["reason"] == "PROC_NO_SOPORTADO"
    assert op.params["pending_code"] == CODE
    assert op.params["inputs"] == ["WORK.ventas"]
    assert not op.params.get("outputs")
    assert any(CODE in note for note in op.notes)


@pytest.mark.parametrize("policy", ["discard", "log", "csv"])
@pytest.mark.parametrize("out", [False, True])
def test_freq_respeta_politica_solo_sin_out(policy, out):
    body = "TABLES region / OUT=fr;" if out else "TABLES region;"
    compiled, _ = compile_project(
        {"p.sas": f"PROC FREQ DATA=ventas; {body} RUN;"},
        env=Env(project=Project(reports=policy)),
    )
    plan = compiled["p.sas"].plan
    assert not any(op.kind == "aggregate" for op in plan.graph.operators())
    if out:
        assert any(g.reason == "PROC_NO_SOPORTADO" for g in plan.gaps)
        assert any(CODE in note for op in plan.graph.operators() for note in op.notes)
    elif policy == "discard":
        assert any("PROC FREQ" in item.what for item in plan.not_migrated)
        assert not plan.gaps
    else:
        assert any(g.reason == "REPORTE" for g in plan.gaps)


def test_regla_freq_parcial_sin_agregado():
    spec = declared("freq")
    assert spec["status"] == "parcial"
    assert not spec["ops"]
    assert spec["fallback"]["reason"] == "PROC_NO_SOPORTADO"
    assert CODE in spec["fallback"]["note"]


def test_corpus_freq_sin_esperado(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "tools"))
    from corpus_lib.caso import cargar_caso

    case = cargar_caso(CASE)
    assert case.estado == "sin_esperado"
    assert case.motivo == CODE
    assert not case.esperado.exists()
    assert (case.entradas / "ventas.csv").is_file()
    text = case.programa.read_text(encoding="utf-8")
    assert "OUT=WORK.fr" in text


def test_catalogo_general_limita_cita_a_missprint():
    catalog = cargar_yaml(ROOT / "rules/sas/catalogo/procedimientos-migrador.yaml")
    entry = next(entry for entry in catalog["entries"] if entry["id"] == "freq")
    assert entry["estado"] == "no_verificada"
    assert entry["fuente"] == "proc.pdf, p. 89"
    assert "MISSPRINT" in entry["nota"]
    assert CODE in entry["nota"]
