"""PROC genéricos a operadores. Sin regla: `unsupported` con PROC_NO_SOPORTADO."""

from __future__ import annotations

import re

from sgm.frontend.steps import Proc
from sgm.ir.builder import Builder, qualify
from sgm.ir.models import Evidence, Operator
from sgm.ir.proc_rules import declared, lower_declared, names_of

_names = names_of

REPORT_PROCS = frozenset({"print", "report", "contents"})

# Opciones que el PROC IMPORT y el PROC EXPORT escriben como sentencia del cuerpo (`GETNAMES=YES;`)
# o en la cabecera. Se leen del texto y no se suponen: el valor que falta queda en `None`.
_OPCION = re.compile(
    r"(?i)\b(dbms|delimiter|getnames|sheet|guessingrows)\s*=\s*('[^']*'|\"[^\"]*\"|[^\s;]+)"
)


def _sin_comillas(valor: str) -> str:
    return valor.strip().strip("'\"")


def _opciones(step: Proc) -> dict[str, str]:
    """Opciones de archivo del paso, tal como las escribe el SAS (cabecera y cuerpo)."""
    texto = " ".join([step.text, *step.body])
    return {m.group(1).lower(): m.group(2) for m in _OPCION.finditer(texto)}


def _dbms(opciones: dict[str, str]) -> str | None:
    valor = opciones.get("dbms")
    return _sin_comillas(valor).lower() if valor else None


def _entero(valor: str | None) -> int | str | None:
    """Convierte el límite literal y conserva MAX o una expresión sin evaluar."""
    texto = _sin_comillas(valor) if valor else ""
    return int(texto) if texto.isdigit() else texto or None


def _getnames(opciones: dict[str, str]) -> bool:
    """`GETNAMES=YES` es el valor por omisión de SAS (`proc`, p. 1387)."""
    valor = opciones.get("getnames")
    return True if valor is None else _sin_comillas(valor).upper() != "NO"


def _read_file(step: Proc, ev: Evidence, b: Builder, out: str | None) -> None:
    """`PROC IMPORT`: archivo de entrada con su formato, separador, cabecera y hoja."""
    opciones = _opciones(step)
    params = {
        "datafile": step.options.get("datafile"),
        "outputs": [qualify(out)] if out else [],
        "dbms": _dbms(opciones),
        "delimiter": _sin_comillas(opciones["delimiter"]) if "delimiter" in opciones else None,
        "getnames": _getnames(opciones),
        "sheet": _sin_comillas(opciones["sheet"]) if "sheet" in opciones else None,
        "guessingrows": _entero(opciones.get("guessingrows")),
    }
    b.op("read_file", params, ev)


def _write_file(step: Proc, ev: Evidence, b: Builder, data: str | None) -> None:
    """`PROC EXPORT`: archivo de salida con su formato y separador."""
    opciones = _opciones(step)
    params = {
        "inputs": [qualify(data)] if data else [],
        "outfile": step.options.get("outfile"),
        "dbms": _dbms(opciones),
        "delimiter": _sin_comillas(opciones["delimiter"]) if "delimiter" in opciones else None,
    }
    if "sheet" in opciones:
        params["sheet"] = _sin_comillas(opciones["sheet"])
    b.op("write_file", params, ev)


def _report(step: Proc, ev: Evidence, b: Builder, data: str | None) -> None:
    """Reporte impreso de un dataset. Su destino lo decide la política `reports` (pasada 2)."""
    statement = "; ".join([step.text, *step.body])
    params = {
        "statement": statement,
        "procedure": step.name,
        "reason": "REPORTE",
        "inputs": [qualify(data)] if data else [],
    }
    b.op(
        "unsupported",
        params,
        ev,
        status="hueco",
        notes=["reporte impreso: lo decide la política reports de env/project.json"],
    )


def lower_proc(step: Proc, ev: Evidence, b: Builder) -> None:
    name = step.name
    data = step.options.get("data")
    out = step.options.get("out")
    if name in REPORT_PROCS and not out:  # con OUT= produce un dataset que otros pasos leen
        _report(step, ev, b, data)
    elif name == "sort":
        _sort(step, ev, b, data, out)
    elif (spec := declared(name)) is not None:  # append, means, summary, freq: en YAML (F1.4)
        if not lower_declared(spec, step, ev, b, data, out):
            _unsupported(step, ev, b, spec["fallback"]["note"])
    elif name == "import":
        _read_file(step, ev, b, out)
    elif name == "export":
        _write_file(step, ev, b, data)
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
    statement = "; ".join([step.text, *step.body])
    b.op(
        "unsupported",
        {"statement": statement, "procedure": step.name, "reason": "PROC_NO_SOPORTADO"},
        ev,
        status="hueco",
        notes=[note],
    )
