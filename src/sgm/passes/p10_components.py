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

import re

from sgm.expressions.expressions import translate
from sgm.ir.models import Gap, Graph, Operator, Pending
from sgm.passes.base import PassContext, PassLog
from sgm.passes.reglas_mapeo import (  # noqa: F401  (reexport)
    ENGINES_PATH,
    ROOT,
    RULES_DIR,
    Conflicto,
    Rule,
    _matches,
    _resolve,
    choose,
    load_engines,
    load_rules,
    resolve,
)

NO_COMPONENT = "none"
CANDIDATE = "candidato"

NAME = "p10_components"
_FUNCTION = re.compile(r"\b([A-Za-z_]\w*)\s*\(")
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
    """Registra huecos y advertencias de expresiones. True si algo requiere revisión."""
    found = False
    for text in _expressions(op):
        result = translate(text)
        if result.talend is not None:
            for warning in result.warnings:
                if warning not in op.notes:
                    op.notes.append(warning)
            if result.engine == "talend":
                candidate = {
                    "source": text,
                    "java": result.talend,
                    "columns": result.columns,
                    "functions": result.functions,
                    "warnings": result.warnings,
                    "row_context": (
                        "input_row es marcador; reemplazar por el enlace real de fila en Talend."
                    ),
                }
                candidates = op.params.setdefault("talend_expression_candidates", [])
                if candidate not in candidates:
                    candidates.append(candidate)
                note = "Traducción candidata con rutinas de Talend; falta validar en Studio 8.0.1."
                if note not in op.notes:
                    op.notes.append(note)
                found = True
            found = found or bool(result.warnings)
            continue
        functions = _FUNCTION.findall(text)
        name = functions[0] if functions else text.strip()[:40]
        gaps.append(
            Gap(
                signature=f"{op.signature}/{name}",
                reason="FUNCION_NO_MAPEADA",
                evidence=list(op.evidence),
                text=" ".join(text.split())[:120],
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
        found, conflicto = resolve(op, rules, engines)
        if conflicto is not None:
            ctx.plan.pending.append(
                Pending(
                    signature=op.signature,
                    options=[
                        {
                            "opcion": component,
                            "confianza": "media",
                            "supuesto": f"propuesta de la regla {rule_id}",
                        }
                        for rule_id, component in conflicto.opciones
                    ],
                    default=found[1] if found else "",
                )
            )
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
        needs_review = bool(rule.produce.get("needs_review")) or rule.rung >= 4 or bool(
            conflicto
        )
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
    """Último peldaño: `tJava` solo si el operador es de flujo con datos y ninguna regla aplica.

    Una lectura o un SQL soportados que van a la base no son tJava: su motor los resuelve (o, si el
    motor no está declarado, no tienen componente). Un SQL de flujo sin regla sí es tJava.
    """
    in_base = (op.placement or "").startswith("db:")
    if op.status == "soportado" and op.kind in ("read", "exec_sql") and in_base:
        return None
    for rule in rules:
        if rule.rung == 5 and _matches(rule, op):
            return rule, str(rule.produce["component"])
    return None
