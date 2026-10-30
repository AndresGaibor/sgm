"""Compilación: programa SAS (o proyecto) a un `Plan` con sus registros de pasadas.

Un proyecto se analiza completo (las macros se comparten entre archivos) y después se compila un
plan por programa. Cada plan tiene su propio grafo y su propio registro de pasadas.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from sgm.catalog.schemas import load_schemas
from sgm.emit.conventions.naming import DEFAULT_NAME_TEMPLATE, render_job_name
from sgm.frontend.program import ProgramAnalysis, analyze_program
from sgm.ir.lower import lower_items
from sgm.ir.models import Gap, Graph, Job, Plan
from sgm.passes.base import PassContext, PassLog
from sgm.passes.pipeline import run_passes
from sgm.redaction import redact

ROOT_DIR = Path(__file__).resolve().parents[2]
RULES_DIR = ROOT_DIR / "rules"
SCHEMAS_PATH = ROOT_DIR / "env" / "schemas.json"


@dataclass
class Compiled:
    plan: Plan
    logs: list[PassLog] = field(default_factory=list)


def load_sql_portable(path: Path | None = None) -> frozenset[str]:
    """Nombres de funciones SQL portables (status `portable` en `rules/sas/sql-functions.json`)."""
    source = path or RULES_DIR / "sas" / "sql-functions.json"
    data = json.loads(source.read_text(encoding="utf-8"))
    return frozenset(
        name for name, info in data["functions"].items() if info.get("status") == "portable"
    )


def build_gaps(graph: Graph) -> list[Gap]:
    """Huecos agrupados por firma: operadores con estado `hueco`."""
    by_signature: dict[str, Gap] = {}
    for op in graph.operators():
        if op.status != "hueco":
            continue
        reason = str(op.params.get("reason", "SIN_MOTIVO"))
        gap = by_signature.setdefault(op.signature, Gap(op.signature, reason, []))
        for ev in op.evidence:
            if ev not in gap.evidence:
                gap.evidence.append(ev)
    return list(by_signature.values())


def compile_file(analysis: ProgramAnalysis, program: str, ctx_base: dict) -> Compiled:
    """Plan de un programa a partir del análisis del proyecto (solo sus pasos)."""
    plan = Plan(program=program)
    items = [item for item in analysis.items if item.file == program]
    lower_items(items, plan.graph)
    plan.jobs = [
        Job(name=render_job_name(DEFAULT_NAME_TEMPLATE, project="proyecto", program=program))
    ]
    ctx = PassContext(
        plan=plan,
        sql_portable=ctx_base["sql_portable"],
        library_engines=ctx_base["library_engines"],
        schemas=ctx_base["schemas"],
    )
    logs = run_passes(ctx)
    plan.gaps = build_gaps(plan.graph) + plan.gaps
    return Compiled(plan, logs)


def compile_project(
    files: dict[str, str], library_engines: dict[str, str] | None = None
) -> tuple[dict[str, Compiled], ProgramAnalysis]:
    """Compila todos los programas de un proyecto. `files` es {ruta relativa: texto}.

    El texto se redacta antes de analizarlo: ninguna credencial llega a un modelo derivado.
    """
    clean = {path: redact(text, path) for path, text in files.items()}
    analysis = analyze_program(clean)
    base = {
        "sql_portable": load_sql_portable(),
        "library_engines": library_engines or {},
        "schemas": load_schemas(SCHEMAS_PATH),
    }
    compiled = {program: compile_file(analysis, program, base) for program in sorted(clean)}
    return compiled, analysis
