"""Pasos DATA a operadores lógicos: lecturas, filtros, derivaciones, uniones y estado por fila."""

from __future__ import annotations

import re

from sgm.frontend.datastep import DataStep, DsStatement
from sgm.ir.builder import Builder, qualify
from sgm.ir.models import Evidence, Operator
from sgm.ir.types_code import declared_types

_HEAD_KINDS = frozenset({"set", "merge", "by", "infile", "input", "datalines"})
_IF_ASSIGN = re.compile(r"(?is)^if\s+(.*?)\s+then\s+([\w]+)\s*=\s*(.+)$")
_ELSE_IF_ASSIGN = re.compile(r"(?is)^else\s+if\s+(.*?)\s+then\s+([\w]+)\s*=\s*(.+)$")
_ELSE_ASSIGN = re.compile(r"(?is)^else\s+([\w]+)\s*=\s*(.+)$")


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
    entradas: list[Operator] = []
    for ref, read in zip(refs, reads, strict=True):
        where = ref.get("where")
        if where:
            filtrado = b.op("filter", {"expression": where}, ev)
            b.link(read, filtrado)
            entradas.append(filtrado)
        else:
            entradas.append(read)
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
        for read in entradas:
            b.link(read, join)
        return reads, join
    if len(reads) > 1:
        union = b.op("union", {"sources": [qualify(r["name"]) for r in refs]}, ev)
        for read in entradas:
            b.link(read, union)
        return reads, union
    return reads, entradas[0] if refs and refs[0].get("where") else None


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
    omit: set[int] = set()
    for index, s in enumerate(stmts):
        if index in omit:
            continue
        kind = s.kind
        before, prev = prev, s
        if kind in _HEAD_KINDS:
            continue
        conditional = _conditional_assignment(stmts, index)
        if conditional is not None:
            assignment, siguiente = conditional
            if pending_derive is None:
                pending_derive = b.op("derive", {"assignments": [], "modo": "agrega"}, ev)
                if current is not None:
                    b.link(current, pending_derive)
                current = pending_derive
            pending_derive.params["assignments"].append(assignment)
            b.refresh(pending_derive)
            omit.update(range(index + 1, siguiente))
            prev = stmts[siguiente - 1]
            continue
        if kind == "assign":
            assignment = {"target": s.fields["target"], "expression": s.fields["expression"]}
            if pending_derive is None:
                # `modo`: una asignación de DATA step conserva las columnas que ya venían; el
                # `derive` de un `SELECT` las reemplaza. Sin la marca, el emisor escribiría un
                # `tMap` con una sola columna y el Job perdería el resto de la fila.
                pending_derive = b.op("derive", {"assignments": [], "modo": "agrega"}, ev)
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


def _conditional_assignment(
    stmts: list[DsStatement], index: int
) -> tuple[dict, int] | None:
    """Combina ramas de asignación con destino común.

    SAS exige que ELSE siga inmediatamente al IF-THEN; se conserva esa condición del lenguaje
    (`lestmtsref`, p. 132-133) y no se emparejan ramas separadas por otras sentencias.
    """
    current = stmts[index]
    if current.kind != "if":
        return None
    first = _IF_ASSIGN.fullmatch(current.text.strip())
    if first is None:
        return None
    target = first.group(2).lower()
    branches = [{"condition": first.group(1).strip(), "expression": first.group(3).strip()}]
    cursor = index + 1
    while cursor < len(stmts):
        else_if = _ELSE_IF_ASSIGN.fullmatch(stmts[cursor].text.strip())
        if else_if is None:
            break
        if else_if.group(2).lower() != target:
            return None
        branches.append(
            {"condition": else_if.group(1).strip(), "expression": else_if.group(3).strip()}
        )
        cursor += 1
    if cursor >= len(stmts):
        return None
    otherwise = _ELSE_ASSIGN.fullmatch(stmts[cursor].text.strip())
    if otherwise is None or otherwise.group(1).lower() != target:
        return None
    alternativa = otherwise.group(2).strip()
    condicional = (
        {"condition": branches[0]["condition"], "otherwise": alternativa}
        if len(branches) == 1
        else {"branches": branches, "otherwise": alternativa}
    )
    return (
        {
            "target": target,
            "expression": branches[0]["expression"],
            "conditional": condicional,
        },
        cursor + 1,
    )


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
