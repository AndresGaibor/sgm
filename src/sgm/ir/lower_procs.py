"""PROC genéricos a operadores. Sin regla: `unsupported` con PROC_NO_SOPORTADO."""

from __future__ import annotations

from sgm.frontend.steps import Proc
from sgm.ir.builder import Builder, qualify
from sgm.ir.models import Evidence, Operator


def _names(clause: str | None) -> list[str]:
    """Nombres de una cláusula (`by a b;` → ['a', 'b']) en minúsculas."""
    if not clause:
        return []
    words = clause.split(None, 1)[1] if len(clause.split(None, 1)) > 1 else ""
    return [w.lower() for w in words.replace(";", " ").split() if w]


def lower_proc(step: Proc, ev: Evidence, b: Builder) -> None:
    name = step.name
    data = step.options.get("data")
    out = step.options.get("out")
    if name == "sort":
        _sort(step, ev, b, data, out)
    elif name == "append":
        base, data_option = step.options.get("base"), step.options.get("data")
        if base and data_option:
            b.op("union", {"sources": [qualify(base), qualify(data_option)]}, ev)
        else:
            _unsupported(step, ev, b, "PROC APPEND sin BASE= y DATA=")
    elif name == "import":
        params = {
            "datafile": step.options.get("datafile"),
            "outputs": [qualify(out)] if out else [],
        }
        b.op("read_file", params, ev)
    elif name == "export":
        b.op(
            "write_file",
            {"inputs": [qualify(data)] if data else [], "outfile": step.options.get("outfile")},
            ev,
        )
    elif name in ("means", "summary", "freq"):
        params = {
            "procedure": name,
            "inputs": [qualify(data)] if data else [],
            "class": _names(step.clauses.get("class")),
            "var": _names(step.clauses.get("var")),
        }
        b.op("aggregate", params, ev)
    else:
        _unsupported(step, ev, b, f"PROC {name.upper()} sin regla de migración")


def _sort(step: Proc, ev: Evidence, b: Builder, data: str | None, out: str | None) -> None:
    by = _names(step.clauses.get("by"))
    nodup = "nodupkey" in step.flags or "nodup" in step.flags
    sort = b.op(
        "sort",
        {"by": by, "inputs": [qualify(data)] if data else []},
        ev,
        status="soportado" if by else "parcial",
        notes=[] if by else ["PROC SORT sin BY: no se puede deducir la clave"],
    )
    current: Operator = sort
    if nodup:
        dedup = b.op(
            "dedup",
            {"by": by, "keep": "first"},
            ev,
            status="soportado" if by else "parcial",
            notes=[] if by else ["NODUP sin clave: deduplicación parcial"],
        )
        b.link(sort, dedup)
        current = dedup
    target = out or data
    if target:
        current.params["outputs"] = [qualify(target)]
        b.refresh(current)


def _unsupported(step: Proc, ev: Evidence, b: Builder, note: str) -> None:
    b.op(
        "unsupported",
        {"statement": step.text, "procedure": step.name, "reason": "PROC_NO_SOPORTADO"},
        ev,
        status="hueco",
        notes=[note],
    )
