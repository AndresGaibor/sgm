"""Asignaciones condicionales del DATA step (IF/ELSE con asignación) y operador por sentencia.

Se extrajo de `lower_data.py` sin cambio de comportamiento (B-5, límite de 300 líneas).
"""

from __future__ import annotations

import re

from sgm.frontend.datastep import DsStatement
from sgm.ir import operadores
from sgm.ir.builder import Builder
from sgm.ir.lower_data_salidas import _conditional_output
from sgm.ir.models import Evidence, Operator
from sgm.ir.pasos import op_validado

_IF_ASSIGN = re.compile(r"(?is)^if\s+(.*?)\s+then\s+([\w]+)\s*=\s*(.+)$")
_ELSE_IF_ASSIGN = re.compile(r"(?is)^else\s+if\s+(.*?)\s+then\s+([\w]+)\s*=\s*(.+)$")
_ELSE_ASSIGN = re.compile(r"(?is)^else\s+([\w]+)\s*=\s*(.+)$")


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
    s: DsStatement,
    kind: str,
    before: DsStatement | None,
    ev: Evidence,
    b: Builder,
    default_outputs: list[str],
) -> Operator | None:
    """Operador de una sentencia que no es asignación. None si no tiene traducción directa."""
    if kind == "where":
        expresion = s.fields["expression"]
        return op_validado(
            b,
            lambda: operadores.filtrar("_", expresion, evidence=[ev]),
            "filter",
            {"expression": expresion},
            ev,
        )
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
            expresion = re.sub(r"(?i)^if\s+", "", s.text)
            return op_validado(
                b,
                lambda: operadores.filtrar("_", expresion, evidence=[ev]),
                "filter",
                {"expression": expresion},
                ev,
            )
        return b.op(
            "derive",
            {"conditional": s.text},
            ev,
            status="parcial",
            notes=["asignación condicional: traducir como expresión condicional"],
        )
    if kind in ("keep", "drop"):
        nombres = [n.lower() for n in s.fields["names"]]
        return op_validado(
            b,
            lambda: operadores.proyectar("_", kind, nombres, evidence=[ev]),
            "select",
            {"mode": kind, "names": nombres},
            ev,
        )
    if kind == "rename":
        pares = [[a.lower(), c.lower()] for a, c in s.fields["pairs"]]
        return op_validado(
            b,
            lambda: operadores.renombrar("_", [(a, c) for a, c in pares], evidence=[ev]),
            "rename",
            {"pairs": pares},
            ev,
        )
    if kind == "output":
        condition = before.text if before is not None and before.kind == "if" else ""
        targets = s.fields.get("targets") or default_outputs
        target = targets[0] if targets else None
        params = {"target": target, "condition": condition}
        if len(targets) > 1:
            params["targets"] = targets
        return b.op(
            "split",
            params,
            ev,
            status="soportado" if target else "parcial",
            notes=(
                []
                if target
                else ["OUTPUT sin destino explícito requiere semántica de salida por defecto"]
            ),
        )
    if kind in ("retain", "lag", "call_symput"):
        notes = ["estado entre filas: en Talend requiere tJavaRow o tMap con variables"]
        return b.op(
            "stateful_row", {"reason": kind, "text": s.text}, ev, status="parcial", notes=notes
        )
    return None
