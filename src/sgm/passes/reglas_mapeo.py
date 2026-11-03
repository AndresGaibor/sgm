"""Reglas de mapeo a componente: carga, emparejamiento y resolución por prioridad (fase 2).

Lo usa la pasada 10. Una regla dice `cuando` (kind, placement, file_format), `produce` y su
`prioridad`. Si dos reglas de igual prioridad proponen componentes distintos, `resolve` lo
reporta como conflicto en lugar de elegir una en silencio.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from sgm.ir.models import Operator

ROOT = Path(__file__).resolve().parents[3]
RULES_DIR = ROOT / "rules" / "mapping"
ENGINES_PATH = ROOT / "rules" / "talend" / "engines.json"

_REQUIRED = (
    "id",
    "version",
    "prioridad",
    "cuando",
    "produce",
    "confidence",
    "alternatives",
    "casos",
)


@dataclass(frozen=True)
class Rule:
    """Regla de mapeo. `prioridad` (100 = la más alta) decide entre reglas que coinciden;
    `rung` es el peldaño derivado (1 = motor, 5 = último recurso) que usan las métricas."""

    id: str
    version: int
    prioridad: int
    cuando: dict[str, Any]
    produce: dict[str, Any]
    confidence: str
    alternatives: tuple[str, ...]
    description: str = ""

    @property
    def rung(self) -> int:
        return (100 - self.prioridad) // 10


def load_rules(directory: Path = RULES_DIR) -> list[Rule]:
    """Reglas de la escalera, por peldaño y por id. Falla si una regla no tiene la forma."""
    rules: list[Rule] = []
    for path in sorted(directory.glob("*.yaml")):
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        missing = [key for key in _REQUIRED if key not in raw]
        if missing:
            raise ValueError(f"{path.name}: faltan campos {missing}")
        rules.append(
            Rule(
                id=str(raw["id"]),
                version=int(raw["version"]),
                prioridad=int(raw["prioridad"]),
                cuando=dict(raw["cuando"]),
                produce=dict(raw["produce"]),
                confidence=str(raw["confidence"]),
                alternatives=tuple(raw["alternatives"]),
                description=str(raw.get("description", "")),
            )
        )
    ids = [r.id for r in rules]
    if len(ids) != len(set(ids)):
        raise ValueError("ids de regla duplicados")
    return sorted(rules, key=lambda r: (-r.prioridad, r.id))


def load_engines(path: Path = ENGINES_PATH) -> dict[str, dict[str, str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data["engines"]


def _file_format(op: Operator) -> str:
    datafile = str(op.params.get("datafile") or "").strip("\"' ").lower()
    return "excel" if datafile.endswith((".xlsx", ".xls")) else "delimited"


def _matches(rule: Rule, op: Operator) -> bool:
    match = rule.cuando
    if match.get("kind") not in (None, "*") and op.kind != match["kind"]:
        return False
    if "placement" in match:
        placement = op.placement or "flow"
        if match["placement"] == "db":
            if not placement.startswith("db:"):
                return False
        elif placement != match["placement"]:
            return False
    if "file_format" in match and _file_format(op) != match["file_format"]:
        return False
    return True


def _resolve(rule: Rule, op: Operator, engines: dict[str, dict[str, str]]) -> str | None:
    component = str(rule.produce["component"])
    if component.startswith("engine:"):
        placement = op.placement or ""
        if not placement.startswith("db:"):
            return None
        engine = placement.split(":", 1)[1]
        return engines.get(engine, {}).get(component.split(":", 1)[1]) or None
    return component


@dataclass(frozen=True)
class Conflicto:
    """Reglas de la misma prioridad que proponen componentes distintos para un operador.

    No se elige una en silencio: el operador queda para revisión y la decisión lo recoge.
    """

    opciones: tuple[tuple[str, str], ...]  # (id de la regla, componente)


def resolve(
    op: Operator, rules: list[Rule], engines: dict[str, dict[str, str]]
) -> tuple[tuple[Rule, str] | None, Conflicto | None]:
    """Regla ganadora y componente, o None; y el conflicto si las de mayor prioridad chocan.

    Solo cuentan los peldaños de componente (1 a 4); el último recurso lo aplica `_tjava`.
    Entre las que coinciden gana la de mayor prioridad y, a igual prioridad, la de id menor
    (el orden de `load_rules`). Si a igual prioridad proponen componentes distintos, hay conflicto.
    """
    candidatos: list[tuple[Rule, str]] = []
    for rule in rules:
        if rule.rung >= 5 or not _matches(rule, op):
            continue
        component = _resolve(rule, op, engines)
        if component:
            candidatos.append((rule, component))
    if not candidatos:
        return None, None
    mejor = max(rule.prioridad for rule, _ in candidatos)
    top = [(rule, component) for rule, component in candidatos if rule.prioridad == mejor]
    if len({component for _, component in top}) > 1:
        opciones = tuple((rule.id, component) for rule, component in top)
        return top[0], Conflicto(opciones)
    return top[0], None


def choose(
    op: Operator, rules: list[Rule], engines: dict[str, dict[str, str]]
) -> tuple[Rule, str] | None:
    """Regla ganadora y su componente; None si ninguna aplica (ver `resolve` para conflictos)."""
    found, _ = resolve(op, rules, engines)
    return found
