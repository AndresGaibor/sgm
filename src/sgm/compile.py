"""Compilación: programa SAS (o proyecto) a un `Plan` con sus registros de pasadas.

Un proyecto se analiza completo (las macros se comparten entre archivos) y después se compila un
plan por programa. Cada plan tiene su propio grafo y su propio registro de pasadas.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from sgm.catalog.config import Env
from sgm.catalog.schemas import load_schemas
from sgm.catalog.talend import component_names
from sgm.emit.conventions.naming import DEFAULT_NAME_TEMPLATE, render_job_name
from sgm.frontend.program import ProgramAnalysis, analyze_program
from sgm.frontend.selectors import SelectorUse
from sgm.ir.lower import lower_items
from sgm.ir.models import Evidence, Gap, Graph, Job, NotMigrated, Plan
from sgm.passes.base import PassContext, PassLog
from sgm.passes.pipeline import run_passes
from sgm.redaction import redact

ROOT_DIR = Path(__file__).resolve().parents[2]
RULES_DIR = ROOT_DIR / "rules"
SCHEMAS_PATH = ROOT_DIR / "env" / "schemas"


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
        text = str(op.params.get("statement") or op.params.get("sql") or op.kind)
        gap = by_signature.setdefault(op.signature, Gap(op.signature, reason, [], text[:120]))
        for ev in op.evidence:
            if ev not in gap.evidence:
                gap.evidence.append(ev)
    return list(by_signature.values())


def _declared_contexts(plan: Plan, job: Job) -> None:
    """Un `%include` declarado no es hueco: se registra como no migrado y, si `as_context`, sus
    variables pasan a contexto del Job."""
    for op in plan.graph.operators():
        if op.params.get("reason") != "INCLUDE_DECLARADO":
            continue
        origin = f"%include {op.params['file']} (env/externals.json)"
        if op.params.get("as_context"):
            for name in op.params.get("defines", []):
                job.contexts[name] = {"origen": origin, "valor": None}
        plan.not_migrated.append(
            NotMigrated(
                op.id,
                f"%include de {op.params['file']}: su contenido no se conoce en el repositorio",
                "Variables de contexto del Job; el contenido del archivo no se migra",
                list(op.evidence),
            )
        )


def _selector_groups(plan: Plan, job: Job, uses: list[SelectorUse]) -> None:
    """Cada macro de ambiente invocada es un grupo de contexto: una variable por cada `Y`, un
    contexto por cada literal de `X`. Sus ramas no son código, así que no generan operadores."""
    for use in uses:
        sel = use.selector
        if sel.name in job.context_groups:
            continue
        job.context_groups[sel.name] = {
            "selector": sel.variable,
            "variables": sel.variables,
            "contextos": {literal: dict(values) for literal, values in sel.contexts.items()},
        }
        plan.not_migrated.append(
            NotMigrated(
                f"selector:{sel.name}",
                f"macro de ambiente %{sel.name}: elige {', '.join(sel.variables)} "
                f"según &{sel.variable}",
                f"Grupo de contexto del Job ({len(sel.contexts)} contextos)",
                [Evidence(use.file, use.line, use.line, label=None)],
            )
        )


def compile_file(analysis: ProgramAnalysis, program: str, ctx_base: dict) -> Compiled:
    """Plan de un programa a partir del análisis del proyecto (solo sus pasos)."""
    plan = Plan(program=program)
    items = [item for item in analysis.items if item.file == program]
    lower_items(items, plan.graph, ctx_base["externals"])
    job = Job(name=render_job_name(DEFAULT_NAME_TEMPLATE, project="proyecto", program=program))
    plan.jobs = [job]
    _declared_contexts(plan, job)
    _selector_groups(plan, job, [u for u in analysis.selector_uses if u.file == program])
    macro_params = {
        name: [p.lower() for p, _ in entries[0].params]
        for name, entries in analysis.index.entries.items()
        if entries
    }
    ctx = PassContext(
        plan=plan,
        sql_portable=ctx_base["sql_portable"],
        library_engines=ctx_base["library_engines"],
        schemas=ctx_base["schemas"],
        macro_params=macro_params,
        project=ctx_base["project"],
        no_fusionar=ctx_base.get("no_fusionar", frozenset()),
    )
    logs = run_passes(ctx)
    plan.gaps = build_gaps(plan.graph) + plan.gaps + _catalog_and_intrinsic_gaps(plan.graph)
    return Compiled(plan, logs)


def _catalog_and_intrinsic_gaps(graph: Graph) -> list[Gap]:
    """Huecos que no nacen de un operador `hueco`: componentes fuera del catálogo y cargas
    de región que quedaron parciales (F1.1)."""
    known = component_names()
    found: dict[str, Gap] = {}
    for op in graph.operators():
        name = (op.component or {}).get("name")
        if name and name != "none" and name not in known:
            signature = f"COMPONENTE_NO_CATALOGADO:{name}"
            reason, text = "COMPONENTE_NO_CATALOGADO", f"componente {name} fuera del catálogo"
        elif op.kind == "external_load" and op.status == "parcial" and op.params.get("absorbed"):
            signature = f"INTRINSECO_PARCIAL:{op.signature}"
            reason, text = "INTRINSECO_PARCIAL", "carga externa de región parcial: revisar"
        else:
            continue
        gap = found.setdefault(signature, Gap(signature, reason, [], text))
        gap.evidence.extend(ev for ev in op.evidence if ev not in gap.evidence)
    return list(found.values())


def project_base(
    library_engines: dict[str, str] | None = None,
    env: Env | None = None,
    no_fusionar: frozenset[str] = frozenset(),
) -> dict:
    """Lo que todos los programas de un proyecto comparten: motores, esquemas, políticas y externos.

    `library_engines` (si se da) gana sobre `env/engines.json`.
    """
    env = env or Env()
    engines = {**env.engines.library_engines(), **(library_engines or {})}
    return {
        "sql_portable": load_sql_portable(),
        "library_engines": engines,
        "schemas": load_schemas(SCHEMAS_PATH),
        "externals": env.externals,
        "external_files": env.external_files,
        "project": env.project,
        "no_fusionar": frozenset(no_fusionar),
    }


def compile_project(
    files: dict[str, str],
    library_engines: dict[str, str] | None = None,
    env: Env | None = None,
    no_fusionar: frozenset[str] = frozenset(),
) -> tuple[dict[str, Compiled], ProgramAnalysis]:
    """Compila todos los programas de un proyecto. `files` es {ruta relativa: texto}.

    El texto se redacta antes de analizarlo: ninguna credencial llega a un modelo derivado.
    """
    clean = {path: redact(text, path) for path, text in files.items()}
    base = project_base(library_engines, env, no_fusionar)
    externals = {path: redact(text, path) for path, text in base["external_files"].items()}
    analysis = analyze_program(clean, externals)
    compiled = {program: compile_file(analysis, program, base) for program in sorted(clean)}
    from sgm.lineage import fronteras  # import tardío: lineage importa Compiled de este módulo

    for program, lista in fronteras(compiled).items():
        compiled[program].plan.fronteras = lista
    return compiled, analysis
