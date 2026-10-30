"""Pasada 10: asigna a cada operador un componente Talend candidato, por la escalera.

La escalera tiene un orden fijo y se recorre de arriba abajo; la primera regla que aplica gana:
1. Operador en base: componente de motor (`t<Motor>Input`, `t<Motor>Row`, `t<Motor>Output`).
2. Componente específico: ordenar, deduplicar, agregar, filtrar, seleccionar, unir,
   archivos y Job hijo.
3. `tMap` para mapa, unión por clave, derivación y salidas condicionadas.
4. `tJavaRow` para estado entre filas, con revisión necesaria.
5. `tJava` solo si nada anterior aplica, con revisión necesaria y el SAS original.

Las reglas viven en `rules/mapping/*.yaml`, una por archivo. El código no tiene mapeos fijos.
Todo componente es un candidato: nunca se marca verificado.

Las expresiones se traducen con el traductor copiado. Si una expresión no tiene equivalente, queda
pendiente con motivo `FUNCION_NO_MAPEADA` y la función en la firma del hueco.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from sgm.expressions.expressions import translate
from sgm.ir.models import Gap, Graph, Operator, Pending
from sgm.passes.base import PassContext, PassLog

NAME = "p10_components"
ROOT = Path(__file__).resolve().parents[3]
RULES_DIR = ROOT / "rules" / "mapping"
ENGINES_PATH = ROOT / "rules" / "talend" / "engines.json"
NO_COMPONENT = "none"
CANDIDATE = "candidato"
_FUNCTION = re.compile(r"\b([A-Za-z_]\w*)\s*\(")
_REQUIRED = ("id", "version", "rung", "match", "emit", "confidence", "alternatives", "tests")


@dataclass(frozen=True)
class Rule:
    id: str
    version: int
    rung: int
    match: dict[str, Any]
    emit: dict[str, Any]
    confidence: str
    alternatives: tuple[str, ...]
    description: str = ""


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
                rung=int(raw["rung"]),
                match=dict(raw["match"]),
                emit=dict(raw["emit"]),
                confidence=str(raw["confidence"]),
                alternatives=tuple(raw["alternatives"]),
                description=str(raw.get("description", "")),
            )
        )
    ids = [r.id for r in rules]
    if len(ids) != len(set(ids)):
        raise ValueError("ids de regla duplicados")
    return sorted(rules, key=lambda r: (r.rung, r.id))


def load_engines(path: Path = ENGINES_PATH) -> dict[str, dict[str, str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data["engines"]


def _file_format(op: Operator) -> str:
    datafile = str(op.params.get("datafile") or "").lower()
    return "excel" if datafile.endswith((".xlsx", ".xls")) else "delimited"


def _matches(rule: Rule, op: Operator) -> bool:
    match = rule.match
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
    component = str(rule.emit["component"])
    if component.startswith("engine:"):
        placement = op.placement or ""
        if not placement.startswith("db:"):
            return None
        engine = placement.split(":", 1)[1]
        return engines.get(engine, {}).get(component.split(":", 1)[1]) or None
    return component


def choose(
    op: Operator, rules: list[Rule], engines: dict[str, dict[str, str]]
) -> tuple[Rule, str] | None:
    """Primera regla de la escalera que aplica al operador, con su componente; None si ninguna."""
    for rule in rules:
        if not _matches(rule, op):
            continue
        component = _resolve(rule, op, engines)
        if component:
            return rule, component
    return None


def _expressions(op: Operator) -> list[str]:
    texts: list[str] = []
    if op.kind == "filter":
        texts.append(str(op.params.get("expression", "")))
    if op.kind == "derive":
        texts += [str(a.get("expression", "")) for a in op.params.get("assignments", [])]
    if op.kind == "map":
        for step in op.params.get("steps", []):
            params = step.get("params", {})
            if step.get("kind") == "filter":
                texts.append(str(params.get("expression", "")))
            if step.get("kind") == "derive":
                texts += [str(a.get("expression", "")) for a in params.get("assignments", [])]
        for branch in op.params.get("branches", []):
            texts.append(str(branch.get("expression", "")))
    return [t for t in texts if t.strip()]


def _unmapped(op: Operator, gaps: list[Gap]) -> bool:
    """Registra un hueco por cada expresión sin equivalente Talend. True si hubo alguno."""
    found = False
    for text in _expressions(op):
        result = translate(text)
        if result.talend is not None:
            continue
        functions = _FUNCTION.findall(text)
        name = functions[0] if functions else text.strip()[:40]
        gaps.append(
            Gap(
                signature=f"{op.signature}/{name}",
                reason="FUNCION_NO_MAPEADA",
                evidence=list(op.evidence),
            )
        )
        op.notes.append(f"expresión sin equivalente Talend: {text.strip()[:80]}")
        found = True
    return found


def run(graph: Graph, ctx: PassContext) -> PassLog:
    log = PassLog(NAME)
    rules = load_rules()
    engines = load_engines()
    rung_counts: dict[int, int] = {}
    for op in graph.operators():
        if op.status in ("hueco", "reemplazado") or op.kind == "unsupported":
            continue
        found = choose(op, rules, engines)
        if found is None:
            found = _tjava(op, rules)
        if found is None:
            continue
        rule, component = found
        if component == NO_COMPONENT:
            op.component = {
                "name": NO_COMPONENT,
                "rung": rule.rung,
                "rule": rule.id,
                "status": CANDIDATE,
            }
            continue
        needs_review = bool(rule.emit.get("needs_review")) or rule.rung >= 4
        if rule.rung == 5:
            op.params["sas_source"] = op.params.get("statement") or op.signature
        if _unmapped(op, ctx.plan.gaps):
            op.status = "parcial"
            needs_review = True
        op.component = {
            "name": component,
            "rung": rule.rung,
            "rule": rule.id,
            "version": rule.version,
            "confidence": rule.confidence,
            "status": CANDIDATE,
            "needs_review": needs_review,
            "alternatives": list(rule.alternatives),
        }
        if rule.alternatives:
            ctx.plan.pending.append(
                Pending(
                    signature=op.signature,
                    options=[
                        {
                            "opcion": opt,
                            "confianza": "media",
                            "supuesto": f"alternativa a {component}",
                        }
                        for opt in [component, *rule.alternatives]
                    ],
                    default=component,
                )
            )
        rung_counts[rule.rung] = rung_counts.get(rule.rung, 0) + 1
    log.metrics["por_peldano"] = dict(sorted(rung_counts.items()))
    log.metrics["componentes"] = sum(rung_counts.values())
    return log


def _tjava(op: Operator, rules: list[Rule]) -> tuple[Rule, str] | None:
    """Último peldaño: `tJava` solo si el operador es de flujo con datos y ninguna regla aplica."""
    if op.status == "soportado" and op.kind in ("read", "exec_sql"):
        return None
    for rule in rules:
        if rule.rung == 5 and _matches(rule, op):
            return rule, str(rule.emit["component"])
    return None
