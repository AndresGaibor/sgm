"""MEANS/SUMMARY con OUTPUT explícito (proc.pdf, pp. 1555–1558 y 1571–1573)."""

from __future__ import annotations

import re
from collections import Counter

from sgm.frontend.steps import Proc
from sgm.ir import operadores
from sgm.ir.builder import Builder, qualify
from sgm.ir.lower_procs_common import unsupported
from sgm.ir.models import Evidence
from sgm.ir.proc_rules import names_of

_NAME = r"[a-z_]\w*"
_DATASET = rf"{_NAME}(?:\.{_NAME})?"
_OUTPUT = re.compile(
    rf"output\s+out\s*=\s*({_DATASET})(?:\s*\(([^()]*)\))?\s*(.*)", re.I | re.S
)
_STAT = re.compile(rf"({_NAME})\s*=\s*", re.I)
_FUNCTIONS = {"sum": "sum", "mean": "avg", "min": "min", "max": "max",
              "n": "count", "nmiss": "nmiss"}
_TYPE_PENDING = "P-MEANS-TYPE-NO-DEMOSTRADO"
_STAT_PENDING = "P-MEANS-ESTADISTICO-SIN-SOPORTE"


def _names(clause: str | None) -> list[str] | None:
    names = names_of(clause)
    if any(not re.fullmatch(_NAME, name) for name in names) or len(names) != len(set(names)):
        return None
    return names


def _statistics(text: str, variables: list[str]) -> list[dict[str, str]] | None:
    """Asocia los nombres de cada STAT= con las VAR en su orden declarado (p. 1558)."""
    matches = list(_STAT.finditer(text))
    if not matches or text[:matches[0].start()].strip():
        return None
    result = []
    for index, match in enumerate(matches):
        function = _FUNCTIONS.get(match.group(1).lower())
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        aliases = text[match.end():end].lower().split()
        if (function is None or len(aliases) != len(variables)
                or any(not re.fullmatch(_NAME, alias) for alias in aliases)):
            return None
        result.extend(
            {"expression": f"{function}({variable})", "alias": alias}
            for variable, alias in zip(variables, aliases, strict=True)
        )
    return result


def lower_means(step: Proc, ev: Evidence, b: Builder, data: str | None, out: str | None) -> None:
    """Baja solo la forma cuyo esquema y estadísticos están demostrados por el SAS."""
    def pending(code: str, reason: str) -> None:
        inputs = [qualify(data)] if data and re.fullmatch(_DATASET, data, re.I) else None
        unsupported(step, ev, b, f"Pendiente: {code}; {reason}", pending_code=code, inputs=inputs)

    groups = _names(step.clauses.get("class"))
    variables = _names(step.clauses.get("var"))
    counts = Counter(statement.split(None, 1)[0].lower() for statement in step.body if statement)
    if (not data or not re.fullmatch(_DATASET, data, re.I) or out
            or set(step.options) - {"data"} or set(step.flags) - {"nway", "noprint", "print"}
            or set(counts) - {"class", "var", "output"}
            or any(count > 1 for count in counts.values())
            or groups is None or not variables):
        pending(_STAT_PENDING, "opciones, sentencias o variables de PROC aún no modeladas")
        return
    output = _OUTPUT.fullmatch(step.clauses.get("output", "").rstrip("; "))
    if output is None:
        pending(_STAT_PENDING, "OUTPUT requiere OUT= literal y estadísticos con nombres explícitos")
        return
    destination, options, statistics = output.groups()
    aggregations = _statistics(statistics, variables)
    if aggregations is None:
        pending(_STAT_PENDING,
                "OUTPUT solo admite SUM, MEAN, MIN, MAX, N y NMISS con un nombre por VAR")
        return
    drop = re.fullmatch(r"\s*drop\s*=\s*([\w\s]+)\s*", options or "", re.I)
    dropped = set(drop.group(1).lower().split()) if drop else set()
    if dropped != {"_type_", "_freq_"} or (groups and "nway" not in step.flags):
        pending(_TYPE_PENDING, "se requiere DROP=_TYPE_ _FREQ_ y NWAY cuando hay CLASS; "
                "tipos y frecuencias automáticos no implementados (proc.pdf, pp. 1572–1573)")
        return
    aliases = [item["alias"] for item in aggregations]
    if (len(set([*groups, *aliases])) != len(groups) + len(aliases)
            or dropped.intersection([*groups, *aliases])):
        pending(_STAT_PENDING, "nombres de salida repetidos, eliminados por DROP o en conflicto")
        return

    previous = b.read_dataset(data, ev)
    if groups:
        # Los faltantes de CLASS se excluyen; los de VAR se tratan individualmente (p. 1571).
        params = operadores.filtrar(
            "_", " AND ".join(f"NOT MISSING({name})" for name in groups), evidence=[ev],
        ).params
        filtered = b.op("filter", params, ev)
        b.link(previous, filtered)
        previous = filtered
    params = operadores.agregar(
        "_", groups, aggregations, outputs=[qualify(destination)],
        output_order=[*groups, *aliases], evidence=[ev],
    ).params
    aggregate = b.op("aggregate", params, ev)
    b.link(previous, aggregate)
