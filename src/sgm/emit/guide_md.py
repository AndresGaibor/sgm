"""Guía de migración en Markdown: por nodo, los operadores con su estado, ubicación y evidencia."""

from __future__ import annotations

from collections import Counter

from sgm.ir.models import Evidence, Operator, Plan


def _cell(text: object, limit: int = 120) -> str:
    """Texto seguro para una celda de tabla: sin saltos de línea ni barras verticales."""
    clean = " ".join(str(text).split()).replace("|", "\\|")
    return clean if len(clean) <= limit else clean[: limit - 1] + "…"


def _ev(items: list[Evidence]) -> str:
    if not items:
        return "—"
    first = items[0]
    span = (
        f"{first.line_start}"
        if first.line_start == first.line_end
        else f"{first.line_start}-{first.line_end}"
    )
    extra = f" (+{len(items) - 1})" if len(items) > 1 else ""
    return f"`{first.file}:{span}`{extra}"


def _label(op: Operator) -> str:
    for ev in op.evidence:
        if ev.label:
            return ev.label
    return "(sin etiqueta)"


def _statement(op: Operator) -> str:
    return str(
        op.params.get("statement") or op.params.get("sql") or op.params.get("text") or op.kind
    )


def render_guide(plan: Plan) -> str:
    operators = sorted(plan.graph.operators(), key=lambda o: o.id)
    by_status = Counter(op.status for op in operators)
    by_place = Counter(op.placement or "sin asignar" for op in operators)
    lines = [
        f"# Guía de migración: {plan.program}",
        "",
        "Generada por sgm. Cada componente cita su evidencia (archivo y líneas).",
        "Las credenciales del origen se enmascaran antes del análisis.",
        "",
        "## Resumen",
        "",
        f"- Operadores: {len(operators)}",
        f"- Por estado: {', '.join(f'{k} {v}' for k, v in sorted(by_status.items())) or 'ninguno'}",
        f"- Por ubicación: "
        f"{', '.join(f'{k} {v}' for k, v in sorted(by_place.items())) or 'ninguna'}",
        f"- No migrado (fontanería y equivalentes): {len(plan.not_migrated)}",
        f"- Huecos: {len(plan.gaps)} firmas",
        f"- Pendientes de decisión: {len(plan.pending)}",
        "",
        "## Operadores por nodo",
    ]
    current = None
    for op in operators:
        label = _label(op)
        if label != current:
            lines += [
                "",
                f"### {label}",
                "",
                "| id | tipo | estado | ubicación | evidencia | paso | notas |",
                "|---|---|---|---|---|---|---|",
            ]
            current = label
        notes = "; ".join(op.notes) if op.notes else ""
        lines.append(
            f"| `{op.id}` | {op.kind} | {op.status} | {op.placement or '—'} | {_ev(op.evidence)} "
            f"| {_cell(_statement(op))} | {_cell(notes)} |"
        )
    lines += ["", "## No migrado", ""]
    if plan.not_migrated:
        lines += ["| operador | qué es | equivalente en Talend | evidencia |", "|---|---|---|---|"]
        lines += [
            f"| `{nm.op_id}` | {_cell(nm.what)} | {_cell(nm.talend)} | {_ev(nm.evidence)} |"
            for nm in plan.not_migrated
        ]
    else:
        lines.append("Nada.")
    lines += ["", "## Huecos", ""]
    if plan.gaps:
        lines += ["| firma | motivo | ocurrencias | evidencia |", "|---|---|---|---|"]
        lines += [
            f"| `{g.signature}` | {g.reason} | {len(g.evidence)} | {_ev(g.evidence)} |"
            for g in plan.gaps
        ]
    else:
        lines.append("Nada.")
    return "\n".join(lines) + "\n"
