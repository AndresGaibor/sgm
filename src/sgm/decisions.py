"""Decisiones pendientes agrupadas por firma (R9).

Un operador con alternativas genera una decisión pendiente. Muchos operadores comparten firma: el
usuario elige una vez por firma, no una vez por operador. Este módulo agrupa las pendientes por
firma y dice cuántos operadores y cuántos archivos la comparten.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sgm.compile import Compiled


@dataclass
class DecisionGroup:
    signature: str
    options: list[str]
    default: str
    operators: int = 0  # veces que aparece en el proyecto
    files: set[str] = field(default_factory=set)  # programas distintos que la necesitan


def group(compiled: dict[str, Compiled]) -> list[DecisionGroup]:
    """Firmas de decisión pendientes, de la más frecuente a la menos frecuente."""
    groups: dict[str, DecisionGroup] = {}
    for result in compiled.values():
        for pending in result.plan.pending:
            found = groups.get(pending.signature)
            if found is None:
                found = DecisionGroup(
                    pending.signature,
                    [str(o.get("opcion", "")) for o in pending.options],
                    pending.default,
                )
                groups[pending.signature] = found
            found.operators += pending.occurrences
            found.files.add(result.plan.program)
    return sorted(groups.values(), key=lambda g: (-g.operators, g.signature))


def totals(compiled: dict[str, Compiled]) -> dict[str, int]:
    """Decisiones totales y firmas únicas, como las reporta `sgm metrics`."""
    pending = [p for r in compiled.values() for p in r.plan.pending]
    return {
        "decisiones": len(pending),
        "firmas": len({p.signature for p in pending}),
    }
