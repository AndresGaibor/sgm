"""Pasos DATA a operadores lógicos: lecturas, filtros, derivaciones, uniones y estado por fila."""

from __future__ import annotations

import re

from sgm.frontend.datastep import DataStep, DsStatement
from sgm.ir.builder import Builder, qualify
from sgm.ir.models import Evidence, Operator
from sgm.ir.types_code import declared_types

_HEAD_KINDS = frozenset({"set", "merge", "by", "infile", "input", "datalines"})


def _join_type(stmts: list[DsStatement], refs: list[dict]) -> str | None:
    """Tipo de unión de un MERGE según la primera condición `if`. None si no se puede deducir."""
    conditions = [s for s in stmts if s.kind == "if" and s.text.lower().startswith("if ")]
    if not conditions:
        return "full"  # MERGE sin condición: une todas las filas (equivale a full outer)
    expr = re.sub(r"(?i)^if\s+", "", conditions[0].text).strip()
    expr = re.sub(r"(?i)\s+then\b.*$", "", expr)
    expr = re.sub(r"\s+", " ", expr).strip().lower()
    if len(refs) < 2:
        return None
    first, second = refs[0].get("in"), refs[1].get("in")
    if not first or not second:
        return None
    if expr in (f"{first} and {second}", f"{second} and {first}"):
        return "inner"
    if expr == first:
        return "left"
    if expr == second:
        return "right"
    if expr in (f"{first} or {second}", f"{second} or {first}"):
        return "full"
    return None


def _lower_sources(
    stmts: list[DsStatement], ev: Evidence, b: Builder
) -> tuple[list[Operator], Operator | None]:
    """Lecturas de entrada y la operación que las combina (join, union) si hay más de una."""
    refs: list[dict] = []
    for s in stmts:
        if s.kind in ("set", "merge"):
            refs += [dict(r, mode=s.kind) for r in s.fields["sources"]]
    reads = [
        b.op("read", {"dataset": qualify(r["name"]), "in": (r.get("in") or None)}, ev) for r in refs
    ]
    if any(s.kind == "merge" for s in stmts):
        by = next((s.fields["names"] for s in stmts if s.kind == "by"), [])
        join_type = _join_type(stmts, refs)
        notes = (
            [] if join_type and by else ["tipo de unión o clave no deducible del MERGE: revisar"]
        )
        status = "soportado" if join_type and by else "parcial"
        join = b.op(
            "join",
            {
                "by": [n.lower() for n in by],
                "join_type": join_type,
                "sources": [qualify(r["name"]) for r in refs],
            },
            ev,
            status=status,
            notes=notes,
        )
        for read in reads:
            b.link(read, join)
        return reads, join
    if len(reads) > 1:
        union = b.op("union", {"sources": [qualify(r["name"]) for r in refs]}, ev)
        for read in reads:
            b.link(read, union)
        return reads, union
    return reads, None


def _read_file(stmts: list[DsStatement], ev: Evidence, b: Builder) -> Operator | None:
    if not any(s.kind in ("infile", "input", "datalines") for s in stmts):
        return None
    rows = next((s.fields.get("rows") for s in stmts if s.kind == "datalines"), None)
    params = {"datalines_rows": rows} if rows is not None else {}
    return b.op(
        "read_file", params, ev, notes=["lectura de archivo o de datos en línea del DATA step"]
    )


def lower_data(step: DataStep, ev: Evidence, b: Builder) -> None:
    """Pasos de un DATA step a operadores. Las declaraciones de tipo (length, format,
    informat) se guardan en las derivaciones del paso (`declared`), para la pasada 9."""
    start = len(b.created)
    _lower_data_steps(step, ev, b)
    declarations = [
        (s.fields["declaration"], s.text.split(None, 1)[1] if " " in s.text else "")
        for s in step.statements
        if s.kind == "declare"
    ]
    declared = declared_types(declarations)
    if declared:
        for op in b.created[start:]:
            if op.kind == "derive":
                op.params["declared"] = {k: [v.type, v.length] for k, v in declared.items()}
                b.refresh(op)


def _lower_data_steps(step: DataStep, ev: Evidence, b: Builder) -> None:
    stmts = step.statements
    reads, current = _lower_sources(stmts, ev, b)
    if current is None:
        current = _read_file(stmts, ev, b) or (reads[0] if reads else None)
    pending_derive: Operator | None = None
    loose: list[str] = []
    prev: DsStatement | None = None
    for s in stmts:
        kind = s.kind
        before, prev = prev, s
        if kind in _HEAD_KINDS:
            continue
        if kind == "assign":
            assignment = {"target": s.fields["target"], "expression": s.fields["expression"]}
            if pending_derive is None:
                pending_derive = b.op("derive", {"assignments": []}, ev)
                if current is not None:
                    b.link(current, pending_derive)
                current = pending_derive
            pending_derive.params["assignments"].append(assignment)
            b.refresh(pending_derive)
            continue
        pending_derive = None
        if kind == "declare":
            _note(current, f"declaración sin efecto en la lógica: {s.text}")
            continue
        if kind in ("array", "do", "end"):
            _note(current, f"{kind} no traducido: revisar el bucle o el arreglo", status="parcial")
            continue
        if kind == "output" and (before is None or before.kind != "if"):
            continue  # `output` sin condición: es la salida por defecto del paso
        new = _statement_op(s, kind, before, ev, b)
        if new is None:
            _note(current, f"sentencia sin traducción: {s.text}", status="parcial")
            if current is not None:
                current.params.setdefault("untranslated", []).append(s.text)
                b.refresh(current)
            else:
                loose.append(s.text)  # sin operador aún: se adjunta al operador final
            continue
        if current is not None:
            b.link(current, new)
        current = new
    outputs = step.outputs
    if current is None:
        current = b.op(
            "derive",
            {"assignments": []},
            ev,
            status="parcial",
            notes=["DATA step sin entradas ni sentencias traducibles"],
        )
    if loose:
        current.params.setdefault("untranslated", []).extend(loose)
        b.refresh(current)
    if "_null_" in [o.lower() for o in outputs]:
        current.notes.append("salida _NULL_: no escribe dataset")
    current.params["outputs"] = [qualify(o) for o in outputs if o.lower() != "_null_"]
    b.refresh(current)


def _statement_op(
    s: DsStatement, kind: str, before: DsStatement | None, ev: Evidence, b: Builder
) -> Operator | None:
    """Operador de una sentencia que no es asignación. None si no tiene traducción directa."""
    if kind == "where":
        return b.op("filter", {"expression": s.fields["expression"]}, ev)
    if kind == "if":
        split = _conditional_output(s)
        if split is not None:
            return b.op("split", split, ev)
        if s.fields.get("first_last") or "then" not in s.text.lower():
            if s.fields.get("first_last"):
                return b.op(
                    "stateful_row",
                    {"reason": "first_last", "text": s.text},
                    ev,
                    status="parcial",
                    notes=["lógica de grupo por first./last.: revisar"],
                )
            return b.op("filter", {"expression": re.sub(r"(?i)^if\s+", "", s.text)}, ev)
        return b.op(
            "derive",
            {"conditional": s.text},
            ev,
            status="parcial",
            notes=["asignación condicional: traducir como expresión condicional"],
        )
    if kind in ("keep", "drop"):
        return b.op("select", {"mode": kind, "names": [n.lower() for n in s.fields["names"]]}, ev)
    if kind == "rename":
        return b.op("rename", {"pairs": [[a.lower(), c.lower()] for a, c in s.fields["pairs"]]}, ev)
    if kind == "output":
        condition = before.text if before is not None else ""
        return b.op("split", {"target": s.fields.get("target"), "condition": condition}, ev)
    if kind in ("retain", "lag", "call_symput"):
        notes = ["estado entre filas: en Talend requiere tJavaRow o tMap con variables"]
        return b.op(
            "stateful_row", {"reason": kind, "text": s.text}, ev, status="parcial", notes=notes
        )
    return None


_OUTPUT_IN_IF = re.compile(
    r"(?is)^(?:if\s+(?P<cond>.*?)\s+then\s+|else\s+)output\s+(?P<target>[\w.&]+)"
)


def _conditional_output(s: DsStatement) -> dict | None:
    """`if c then output t;` o `else output t;` como división. None si no aplica."""
    m = _OUTPUT_IN_IF.match(s.text.strip())
    if not m:
        return None
    return {"target": m.group("target"), "condition": (m.group("cond") or "no ").strip()}


def _note(op: Operator | None, text: str, status: str | None = None) -> None:
    if op is None:
        return
    op.notes.append(text)
    if status is not None and op.status == "soportado":
        op.status = status
