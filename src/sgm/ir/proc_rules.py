"""PROC declarados en `rules/sas/procs/` (F1.4): su bajada a operadores de la IR sale del YAML.

Cada archivo tiene `proc` (el nombre del PROC) y `ops`: la lista de operadores que emite, con sus
`params`. Los valores son literales o marcadores que este módulo resuelve con el paso del PROC:

- `{data}` y `{out}`: lista con el dataset calificado de `DATA=` y `OUT=`, o lista vacía.
- `{proc}`: el nombre del PROC.
- `{clause:NOMBRE}`: lista de nombres de la cláusula (`CLASS`, `VAR`, `BY`).
- `{qualified:OPCIÓN}`: el dataset calificado de una opción.

`when_options` exige opciones presentes. Si falta alguna, se usa `fallback` (motivo y nota).
`sort` no está aquí: su estado depende de si hay BY, y vive en `lower_procs.py`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from sgm.ir.builder import Builder, qualify
from sgm.ir.models import Evidence

ROOT = Path(__file__).resolve().parents[3]
PROCS_DIR = ROOT / "rules" / "sas" / "procs"


def names_of(clause: str | None) -> list[str]:
    """Nombres de una cláusula (`by a b;` → ['a', 'b']) en minúsculas."""
    if not clause:
        return []
    words = clause.split(None, 1)[1] if len(clause.split(None, 1)) > 1 else ""
    return [w.lower() for w in words.replace(";", " ").split() if w]


def load(directory: Path = PROCS_DIR) -> dict[str, dict[str, Any]]:
    """Especificaciones de tipo `proc`, por nombre de PROC."""
    specs: dict[str, dict[str, Any]] = {}
    for path in sorted(directory.glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if data.get("kind") == "proc":
            specs[str(data["proc"])] = data
    return specs


SPECS = load()


def declared(name: str) -> dict[str, Any] | None:
    """Especificación del PROC si está declarada en `rules/sas/procs/`, o None."""
    return SPECS.get(name)


def _value(token: str, step: Any, data: str | None, out: str | None) -> Any:
    if token == "{data}":
        return [qualify(data)] if data else []
    if token == "{out}":
        return [qualify(out)] if out else []
    if token == "{proc}":
        return step.name
    if token.startswith("{clause:"):
        return names_of(step.clauses.get(token[len("{clause:") : -1]))
    if token.startswith("{qualified:"):
        return qualify(step.options[token[len("{qualified:") : -1]])
    return token


def _resolve(value: Any, step: Any, data: str | None, out: str | None) -> Any:
    if isinstance(value, str) and value.startswith("{") and value.endswith("}"):
        return _value(value, step, data, out)
    if isinstance(value, list):
        return [_resolve(v, step, data, out) for v in value]
    if isinstance(value, dict):
        return {k: _resolve(v, step, data, out) for k, v in value.items()}
    return value


def lower_declared(spec: dict[str, Any], step: Any, ev: Evidence, b: Builder, data, out) -> bool:
    """Emite los operadores de la especificación. False si faltan opciones y no se emitió nada."""
    when = spec.get("when_options", [])
    if not all(step.options.get(opt) for opt in when):
        return False
    for op in spec["ops"]:
        params = _resolve(op.get("params", {}), step, data, out)
        b.op(op["kind"], params, ev)
    return True
