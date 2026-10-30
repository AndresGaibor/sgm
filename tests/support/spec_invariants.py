"""Invariantes de un plan compilado, adaptadas de `spec_invariants.py` del repositorio anterior.

La versión anterior revisaba especificaciones de Jobs Talend (componentes, conexiones, contextos). Esta IR
todavía no genera esas especificaciones: revisa el grafo, la evidencia, los nombres de Job y el texto
exportado. Las invariantes de componentes Talend se añaden en el hito 8.

Cada función devuelve una lista de problemas en texto; vacía significa que se cumple.
"""

from __future__ import annotations

import re

from sgm.ir.models import MATERIALIZE, OPERATOR_KINDS, STATUSES, Plan

JOB_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")
CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
PLACEMENTS = re.compile(r"^(db:[a-z0-9_]+|flow|db:\?)$")


def operator_problems(plan: Plan) -> list[str]:
    problems: list[str] = []
    seen: set[str] = set()
    for op in plan.graph.operators():
        where = f"{plan.program}:{op.id}"
        if op.id in seen:
            problems.append(f"{where}: id duplicado")
        seen.add(op.id)
        if op.kind not in OPERATOR_KINDS:
            problems.append(f"{where}: tipo desconocido {op.kind}")
        if op.status not in STATUSES:
            problems.append(f"{where}: estado desconocido {op.status}")
        if op.placement is not None and not PLACEMENTS.match(op.placement):
            problems.append(f"{where}: ubicación desconocida {op.placement}")
        if not op.signature:
            problems.append(f"{where}: sin firma")
        if not op.evidence:
            problems.append(f"{where}: sin evidencia")
        for ev in op.evidence:
            if not ev.file or ev.line_start < 1 or ev.line_end < ev.line_start:
                problems.append(f"{where}: evidencia inválida {ev}")
        if CONTROL.search(str(op.params)):
            problems.append(f"{where}: caracteres de control en los parámetros")
        if op.status == "reemplazado" and op.kind == "external_load":
            problems.append(f"{where}: una carga externa no puede estar reemplazada")
    return problems


def edge_problems(plan: Plan) -> list[str]:
    problems: list[str] = []
    ids = {op.id for op in plan.graph.operators()}
    for edge in plan.graph.edges():
        where = f"{plan.program}:{edge.src}->{edge.dst}"
        if edge.src not in ids or edge.dst not in ids:
            problems.append(f"{where}: extremo inexistente")
        if not edge.dataset:
            problems.append(f"{where}: arista sin dataset")
        if edge.materialize is not None and edge.materialize not in MATERIALIZE:
            problems.append(f"{where}: materialización desconocida {edge.materialize}")
    return problems


def job_problems(plan: Plan) -> list[str]:
    problems: list[str] = []
    for job in plan.jobs:
        if not JOB_NAME.match(job.name):
            problems.append(f"{plan.program}: nombre de Job no válido: {job.name}")
    return problems


def coverage_problems(plan: Plan, labels: set[str]) -> list[str]:
    """Cada etiqueta del programa debe aparecer en la evidencia de un operador o en no migrado."""
    cited = {ev.label for op in plan.graph.operators() for ev in op.evidence}
    cited |= {ev.label for nm in plan.not_migrated for ev in nm.evidence}
    return [f"{plan.program}: etiqueta sin evidencia: {label}" for label in sorted(labels - cited)]


def plan_problems(plan: Plan) -> list[str]:
    return operator_problems(plan) + edge_problems(plan) + job_problems(plan)
