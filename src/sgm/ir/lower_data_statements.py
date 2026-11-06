"""Traducción de sentencias DATA step que no son lecturas o asignaciones simples."""

from __future__ import annotations

import re

from sgm.frontend.datastep import DsStatement
from sgm.ir.builder import Builder
from sgm.ir.models import Evidence, Operator

_IF_ASSIGN = re.compile(r"(?is)^if\s+(.*?)\s+then\s+([\w]+)\s*=\s*(.+)$")
_ELSE_IF_ASSIGN = re.compile(r"(?is)^else\s+if\s+(.*?)\s+then\s+([\w]+)\s*=\s*(.+)$")
_ELSE_ASSIGN = re.compile(r"(?is)^else\s+([\w]+)\s*=\s*(.+)$")
_OUTPUT_IN_IF = re.compile(
    r"(?is)^(?:if\s+(?P<cond>.*?)\s+then\s+|else\s+)output\s+(?P<target>[\w.&]+)"
)


def conditional_assignment(stmts: list[DsStatement], index: int) -> tuple[dict, int] | None:
    """Combina ramas inmediatas de asignación con destino común."""
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


def statement_op(
    statement: DsStatement,
    previous: DsStatement | None,
    evidence: Evidence,
    builder: Builder,
) -> Operator | None:
    """Operador de una sentencia sin traducción directa de asignación."""
    kind = statement.kind
    if kind == "where":
        return builder.op("filter", {"expression": statement.fields["expression"]}, evidence)
    if kind == "if":
        split = conditional_output(statement)
        if split is not None:
            return builder.op("split", split, evidence)
        if statement.fields.get("first_last") or "then" not in statement.text.lower():
            if statement.fields.get("first_last"):
                return builder.op(
                    "stateful_row",
                    {"reason": "first_last", "text": statement.text},
                    evidence,
                    status="parcial",
                    notes=["lógica de grupo por first./last.: revisar"],
                )
            return builder.op(
                "filter", {"expression": re.sub(r"(?i)^if\s+", "", statement.text)}, evidence
            )
        return builder.op(
            "derive",
            {"conditional": statement.text},
            evidence,
            status="parcial",
            notes=["asignación condicional: traducir como expresión condicional"],
        )
    if kind in ("keep", "drop"):
        return builder.op(
            "select",
            {"mode": kind, "names": [n.lower() for n in statement.fields["names"]]},
            evidence,
        )
    if kind == "rename":
        return builder.op(
            "rename",
            {"pairs": [[a.lower(), c.lower()] for a, c in statement.fields["pairs"]]},
            evidence,
        )
    if kind == "output":
        condition = previous.text if previous is not None and previous.kind == "if" else ""
        target = statement.fields.get("target")
        return builder.op(
            "split",
            {"target": target, "condition": condition},
            evidence,
            status="soportado" if target else "parcial",
            notes=(
                []
                if target
                else ["OUTPUT sin destino explícito requiere semántica de salida por defecto"]
            ),
        )
    if kind in ("retain", "lag", "call_symput"):
        return builder.op(
            "stateful_row",
            {"reason": kind, "text": statement.text},
            evidence,
            status="parcial",
            notes=["estado entre filas: en Talend requiere tJavaRow o tMap con variables"],
        )
    if kind in ("file", "put"):
        return builder.op(
            "unsupported",
            {
                "reason": "SENTENCIA_NO_SOPORTADA",
                "reason_detail": "FILE_PUT_SIN_PLANTILLA",
                "statement": statement.text,
                "unsupported_statements": [statement.text],
            },
            evidence,
            status="hueco",
            notes=[
                "FILE/PUT conservado: falta una plantilla de salida compatible con la semántica SAS"
            ],
        )
    return None


def record_file_put(statement: DsStatement, current: Operator, builder: Builder) -> None:
    """Adjunta FILE/PUT al paso activo sin cambiar su identidad ni su traducción candidata."""
    raw = statement.text
    es_hueco_file_put = (
        current.kind == "unsupported"
        and current.params.get("reason_detail") == "FILE_PUT_SIN_PLANTILLA"
    )
    if es_hueco_file_put:
        statements = current.params.setdefault("unsupported_statements", [])
        if raw not in statements:
            statements.append(raw)
            current.params["statement"] = " | ".join(statements)
            builder.refresh(current)
        return
    note = f"FILE_PUT_SIN_PLANTILLA: {raw}"
    if note not in current.notes:
        current.notes.append(note)


def conditional_output(statement: DsStatement) -> dict | None:
    """`if c then output t;` o `else output t;` como división."""
    match = _OUTPUT_IN_IF.match(statement.text.strip())
    if not match:
        return None
    condition = match.group("cond")
    return {
        "target": match.group("target"),
        "condition": condition.strip() if condition else None,
        "branch": "then" if condition else "else",
    }
