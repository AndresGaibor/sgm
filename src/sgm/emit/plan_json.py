"""Plan en JSON: operadores, aristas, no migrados, huecos y jobs, con su evidencia."""

from __future__ import annotations

from typing import Any

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


def plan_to_dict(plan: Plan) -> dict[str, Any]:
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
                "default": p.default,
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
