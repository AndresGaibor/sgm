"""Guía de migración en Markdown: por nodo, operadores con estado, ubicación y evidencia.

Los operadores idénticos que vienen de la misma línea (una macro llamada varias veces) se agrupan
en una fila con `×N`, para que la guía no repita lo mismo.
"""

from __future__ import annotations

import re
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


def _stages(plan: Plan) -> list[str]:
    """Etapas del Job: un subjob por fila, con sus componentes, etiquetas y líneas de origen."""
    if not plan.jobs or not plan.jobs[0].subjobs:
        return []
    rows = [
        "## Etapas",
        "",
        "Un subjob por fila, en orden. Un componente de control (carga, SQL de base, llamada a "
        "plantilla) va solo en su subjob.",
        "",
        "| # | tipo | componentes | etiquetas | líneas |",
        "|---|---|---|---|---|",
    ]
    for number, subjob in enumerate(plan.jobs[0].subjobs, 1):
        ops = [plan.graph.operator(op_id) for op_id in subjob]
        control = len(ops) == 1 and ops[0].kind in ("exec_sql", "external_load", "iterate")
        names = Counter(
            op.component["name"] for op in ops if op.component and op.component["name"] != "none"
        )
        labels = list(dict.fromkeys(_label(op) for op in ops))
        shown = ", ".join(labels[:3]) + (f" (+{len(labels) - 3})" if len(labels) > 3 else "")
        lines_of = [e.line_start for op in ops for e in op.evidence]
        span = f"{min(lines_of)}-{max(lines_of)}" if lines_of else "—"
        components = ", ".join(f"{k} {v}" for k, v in names.most_common(4)) or "—"
        rows.append(
            f"| {number} | {'control' if control else 'flujo'} | {_cell(components)} "
            f"| {_cell(shown)} | {span} |"
        )
    rows.append("")
    return rows


def _code_block(value: str, language: str) -> list[str]:
    """Usa un fence más largo que cualquier secuencia de backticks en el contenido."""
    longest = max((len(run) for run in re.findall(r"`+", value)), default=0)
    fence = "`" * max(3, longest + 1)
    return [f"{fence}{language}", value, fence]


def _talend_candidates(operators: list[Operator]) -> list[str]:
    candidates = [
        (op, candidate)
        for op in operators
        for candidate in op.params.get("talend_expression_candidates", [])
    ]
    if not candidates:
        return []
    lines = [
        "",
        "## Expresiones candidatas Talend",
        "",
        "Son borradores pendientes de revisión. input_row es un alias provisional, no un enlace "
        "confirmado en Talend Studio.",
    ]
    for op, candidate in candidates:
        columns = ", ".join(candidate.get("columns", [])) or "ninguna identificada"
        warnings = candidate.get("warnings", [])
        lines += [
            "",
            f"### Operador {op.id}",
            "",
            "Origen SAS:",
            "",
            *_code_block(str(candidate.get("source", "")), "sas"),
            "",
            f"Columnas: {_cell(columns)}",
            f"Contexto de fila: {_cell(candidate.get('row_context', 'pendiente'))}",
            "Advertencias: " + ("; ".join(_cell(w) for w in warnings) or "ninguna"),
            f"Evidencia: {_ev(op.evidence)}",
            "",
            "Java candidato:",
            "",
            *_code_block(str(candidate.get("java", "")), "java"),
        ]
    return lines


def _joblets(plan: Plan) -> list[str]:
    """Joblets (fase 4.1): bloque repetido, parámetros y apariciones con su evidencia."""
    if not plan.joblets:
        return []
    lines = ["## Joblets", ""]
    for j in plan.joblets:
        lines += [
            f"### {j['id']}",
            "",
            f"- Por qué se propone: {j['por_que']}.",
            f"- Operaciones del bloque: {', '.join(j['operaciones'])}.",
            "- Parámetros: "
            + (", ".join(f"`{p}`" for p in j["parametros"]) or "ninguno")
            + " (tipo y nombre pendientes: fase 3.8).",
            "- Apariciones:",
        ]
        for aparicion in j["fuente"]:
            rangos = "; ".join(
                f"{ev['file']}:{ev['line_start']}-{ev['line_end']}" for ev in aparicion
            )
            lines.append(f"  - {rangos or 'sin evidencia'}")
        entradas = ", ".join(f"`{d}`" for d in j.get("entradas", [])) or "ninguna"
        salidas = ", ".join(f"`{d}`" for d in j.get("salidas", [])) or "ninguna"
        lines.append(f"- Entradas (de fuera del bloque): {entradas}.")
        lines.append(f"- Salidas (para el resto del programa): {salidas}.")
        if j.get("variable_entre_apariciones"):
            lines.append("- Los conjuntos cambian entre apariciones: ver parámetros.")
        lines.append("")
    return lines


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
        *_stages(plan),
        *_joblets(plan),
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
    lines += _talend_candidates(operators)
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
