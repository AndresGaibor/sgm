"""Guía de migración en Markdown: por nodo, operadores con estado, ubicación y evidencia.

Los operadores idénticos que vienen de la misma línea (una macro llamada varias veces) se agrupan
en una fila con `×N`, para que la guía no repita lo mismo.
"""

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
    """Lo que hace el operador, en una línea: la sentencia si la hay; si no, el dataset o las
    asignaciones."""
    text = op.params.get("statement") or op.params.get("sql") or op.params.get("text")
    if text:
        return str(text)
    if op.params.get("dataset"):
        return f"{op.kind} {op.params['dataset']}"
    if op.params.get("assignments"):
        targets = ", ".join(str(a.get("target", "")) for a in op.params["assignments"])
        return f"{op.kind}: {targets}"
    if op.params.get("outputs"):
        return f"{op.kind} -> {', '.join(op.params['outputs'])}"
    return op.kind


def _component(op: Operator) -> str:
    if not op.component:
        return "—"
    name = op.component.get("name", "—")
    return f"{name} (revisar)" if op.component.get("needs_review") else str(name)


def _group_key(op: Operator) -> tuple:
    first = op.evidence[0] if op.evidence else None
    span = (first.file, first.line_start, first.line_end) if first else ("", 0, 0)
    return (
        _label(op),
        op.kind,
        op.status,
        op.placement or "",
        _component(op),
        span,
        _statement(op),
    )


def _group_rows(operators: list[Operator]) -> list[tuple[list[Operator], int]]:
    """Operadores agrupados por clave, en el orden de su primera aparición."""
    groups: dict[tuple, list[Operator]] = {}
    for op in operators:
        groups.setdefault(_group_key(op), []).append(op)
    return [(members, len(members)) for members in groups.values()]


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
        "- Por ubicación: "
        + (", ".join(f"{k} {v}" for k, v in sorted(by_place.items())) or "ninguna"),
        f"- No migrado (fontanería y equivalentes): {len(plan.not_migrated)}",
        f"- Huecos: {len(plan.gaps)} firmas",
        f"- Pendientes de decisión: {len(plan.pending)}",
        "",
        "## Operadores por nodo",
    ]
    by_label: dict[str, list[Operator]] = {}
    for op in operators:
        by_label.setdefault(_label(op), []).append(op)
    for label, members in by_label.items():
        lines += [
            "",
            f"### {label}",
            "",
            "| operador | tipo | estado | ubicación | componente | evidencia | paso | notas "
            "| veces |",
            "|---|---|---|---|---|---|---|---|---|",
        ]
        for group, count in _group_rows(members):
            head = group[0]
            notes = "; ".join(head.notes)
            lines.append(
                f"| `{head.id}` | {head.kind} | {head.status} | {head.placement or '—'} "
                f"| {_cell(_component(head))} | {_ev(head.evidence)} | {_cell(_statement(head))} "
                f"| {_cell(notes)} | ×{count} |"
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
        lines += [
            "| firma | motivo | ocurrencias | sentencia | evidencia |",
            "|---|---|---|---|---|",
        ]
        lines += [
            f"| `{g.signature}` | {g.reason} | {len(g.evidence)} | {_cell(g.text)} "
            f"| {_ev(g.evidence)} |"
            for g in plan.gaps
        ]
    else:
        lines.append("Nada.")
    return "\n".join(lines) + "\n"
