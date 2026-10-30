"""Pasada 7: plantillas para subgrafos repetidos con el mismo patrón.

Se agrupan los operadores de una misma etiqueta en componentes conexos. Si dos o más componentes
tienen
la misma forma (mismos tipos de operador y mismas conexiones, sin importar los nombres), se crea una
plantilla: un Job hijo cuyo cuerpo describe el patrón, y una instancia `iterate` por cada
componente, con
los nombres que difieren como contexto (`parametro_k`).

Ejemplo: tres ramas iguales salvo el sufijo `_A`, `_B`, `_C` producen una plantilla con tres
instancias.
"""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict

from sgm.ir.builder import Builder
from sgm.ir.models import Graph, Job, Operator
from sgm.ir.signature import signature
from sgm.passes.base import PassContext, PassLog

NAME = "p07_templates"
_NAME_KEYS = ("dataset", "outputs", "inputs", "sources", "target")


def _label(op: Operator) -> str | None:
    return next((ev.label for ev in op.evidence if ev.label), None)


def _components(graph: Graph) -> list[list[Operator]]:
    """Componentes conexos de una misma etiqueta (solo los de dos o más operadores)."""
    by_label: dict[str | None, list[Operator]] = defaultdict(list)
    for op in graph.operators():
        by_label[_label(op)].append(op)
    found: list[list[Operator]] = []
    for ops in by_label.values():
        ids = {op.id for op in ops}
        seen: set[str] = set()
        for start in sorted(ids):
            if start in seen:
                continue
            stack, comp = [start], []
            seen.add(start)
            while stack:
                current = stack.pop()
                comp.append(graph.operator(current))
                for nxt in graph.successors(current) + graph.predecessors(current):
                    if nxt in ids and nxt not in seen:
                        seen.add(nxt)
                        stack.append(nxt)
            if len(comp) >= 2:
                found.append(comp)
    return found


def _shape(graph: Graph, comp: list[Operator], order: dict[str, int]) -> tuple[str, list[Operator]]:
    """Huella de la forma del componente y sus operadores en orden topológico."""
    ordered = sorted(comp, key=lambda op: order[op.id])
    index = {op.id: i for i, op in enumerate(ordered)}
    edges = sorted(
        (index[e.src], index[e.dst]) for e in graph.edges() if e.src in index and e.dst in index
    )
    raw = json.dumps({"ops": [op.signature for op in ordered], "edges": edges})
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16], ordered


def _names(ordered: list[Operator]) -> list[str]:
    names: list[str] = []
    for op in ordered:
        for key in _NAME_KEYS:
            value = op.params.get(key)
            if isinstance(value, str):
                names.append(value)
            elif isinstance(value, list):
                names += [v for v in value if isinstance(v, str)]
    return names


def run(graph: Graph, ctx: PassContext) -> PassLog:
    log = PassLog(NAME)
    builder = Builder(graph)
    order = {op_id: i for i, op_id in enumerate(graph.topological())}
    groups: dict[tuple[str | None, str], list[tuple[list[Operator], list[str]]]] = defaultdict(list)
    for comp in _components(graph):
        shape, ordered = _shape(graph, comp, order)
        groups[(_label(ordered[0]), shape)].append((ordered, _names(ordered)))
    for (label, shape), instances in sorted(groups.items(), key=lambda kv: str(kv[0])):
        if len(instances) < 2 or any(len(names) != len(instances[0][1]) for _, names in instances):
            continue
        varying = [
            k for k in range(len(instances[0][1])) if len({names[k] for _, names in instances}) > 1
        ]
        if not varying:
            continue
        template = f"tpl_{shape[:8]}"
        body = instances[0][0]
        job = Job(
            name=template,
            contexts={
                "parametros": [f"parametro_{k}" for k in varying],
                "instancias": len(instances),
                "cuerpo": [{"kind": op.kind, "signature": op.signature} for op in body],
            },
        )
        if ctx.plan.jobs:
            ctx.plan.jobs[0].children.append(job)
        for ordered, names in instances:
            context = {f"parametro_{k}": names[k] for k in varying}
            evidence = []
            for op in ordered:
                for ev in op.evidence:
                    if ev not in evidence:
                        evidence.append(ev)
            params = {"template": template, "context": context}
            iterate = Operator(
                id=builder.next_id(),
                kind="iterate",
                params=params,
                placement="flow",
                evidence=evidence,
                status="parcial" if any(o.status == "parcial" for o in ordered) else "soportado",
                signature=signature("iterate", params),
                notes=[f"instancia de la plantilla {template} (etiqueta: {label})"],
            )
            graph.replace([op.id for op in ordered], iterate)
            log.created.append(iterate.id)
            log.merged += [op.id for op in ordered]
        log.notes.append(
            f"plantilla {template}: {len(instances)} instancias, {len(varying)} parámetros"
        )
    log.metrics["plantillas"] = len({n for n in log.notes if n.startswith("plantilla")})
    return log
