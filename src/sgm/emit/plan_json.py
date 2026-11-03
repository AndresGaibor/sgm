"""Plan en JSON: operadores, aristas, no migrados, huecos y jobs, con su evidencia."""

from __future__ import annotations

from typing import Any

from sgm import motivos
from sgm.ir.models import Evidence, Plan


def _evidence(items: list[Evidence]) -> list[dict[str, Any]]:
    return [
        {
            "file": ev.file,
            "line_start": ev.line_start,
            "line_end": ev.line_end,
            "label": ev.label,
            "call": ev.call,
        }
        for ev in items
    ]


def _valor_componente(op) -> dict[str, Any] | None:
    """Campos por valor (fase 3.1): de dónde sale el componente, con qué regla y con qué confianza.

    `hechos` queda en null: enlazar hechos a operadores no está calculado todavía.
    """
    comp = op.component
    if not comp or comp.get("name") in (None, "none"):
        return None
    return {
        "valor": comp.get("name"),
        "fuente": _evidence(op.evidence),
        "regla": f"{comp.get('rule')}@{comp.get('version')}",
        "confianza": comp.get("confidence"),
        "hechos": None,
    }


def _plan_base(plan: Plan) -> dict[str, Any]:
    """Representación estable del plan: el orden de operadores y aristas es el de sus ids."""
    operators = sorted(plan.graph.operators(), key=lambda o: o.id)
    edges = sorted(plan.graph.edges(), key=lambda e: (e.src, e.dst, e.dataset))
    return {
        "program": plan.program,
        "operators": [
            {
                "id": op.id,
                "kind": op.kind,
                "status": op.status,
                "placement": op.placement,
                "signature": op.signature,
                "params": op.params,
                "evidence": _evidence(op.evidence),
                "notes": op.notes,
                "component": op.component,
                "valor_componente": _valor_componente(op),
            }
            for op in operators
        ],
        "edges": [
            {"src": e.src, "dst": e.dst, "dataset": e.dataset, "materialize": e.materialize}
            for e in edges
        ],
        "not_migrated": [
            {
                "op": nm.op_id,
                "what": nm.what,
                "talend": nm.talend,
                "evidence": _evidence(nm.evidence),
            }
            for nm in plan.not_migrated
        ],
        "pending": [
            {
                "signature": p.signature,
                "options": p.options,
                "sugerido": p.default,
                "aplicado": False,
                "occurrences": p.occurrences,
            }
            for p in plan.pending
        ],
        "gaps": [
            {"signature": g.signature, "reason": g.reason, "evidence": _evidence(g.evidence)}
            for g in plan.gaps
        ],
        "jobs": [
            {
                "name": j.name,
                "subjobs": j.subjobs,
                "contexts": j.contexts,
                "context_groups": j.context_groups,
                "children": [c.name for c in j.children],
            }
            for j in plan.jobs
        ],
    }


def _pendientes(plan: Plan) -> list[dict[str, Any]]:
    """Modelo único de pendiente (fase 3.2): valor null, motivo, dueño, cómo se cierra y nota.

    Reúne huecos (con su motivo de `routing.yaml`) y decisiones sin valor aplicado.
    """
    filas: list[dict[str, Any]] = []
    for gap in plan.gaps:
        motivo = motivos.de(gap.reason)
        filas.append(
            {
                "valor": None,
                "pendiente": {
                    "motivo": gap.reason,
                    "dueno": motivo.dueño if motivo else "sin_dueno",
                    "se_cierra_con": motivo.se_cierra_con if motivo else "por definir",
                    "nota": gap.text,
                },
                "signature": gap.signature,
                "fuente": _evidence(gap.evidence),
            }
        )
    for pend in plan.pending:
        filas.append(
            {
                "valor": None,
                "pendiente": {
                    "motivo": "DECISION_HUMANA",
                    "dueno": "usuario",
                    "se_cierra_con": "sgm decisions set",
                    "nota": f"sugerido {pend.default}; no aplicado",
                },
                "signature": pend.signature,
                "fuente": [],
            }
        )
    return filas


def plan_to_dict(plan: Plan) -> dict[str, Any]:
    """Plan JSON: la base del plan más el bloque de pendientes unificados."""
    datos = _plan_base(plan)
    datos["pendientes"] = _pendientes(plan)
    datos["joblets"] = list(plan.joblets)
    return datos
