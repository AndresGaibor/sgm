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

import networkx as nx

from sgm.ir.builder import Builder
from sgm.ir.models import Graph, Job, Operator
from sgm.ir.signature import signature
from sgm.passes.base import PassContext, PassLog

NAME = "p07_templates"
# Umbrales de joblet (fase 3.7). Pendiente: moverlos a `rules/` como datos.
JOBLET_MIN_OCCURRENCES = 2
JOBLET_MIN_OPERATIONS = 3


def _register_joblet(plan, template: str, label, body, instances, varying, contexts) -> None:
    """Un bloque repetido pasa a joblet: una unidad por forma, con todas sus apariciones.

    Las mismas formas en nodos distintos son el mismo joblet: se suman apariciones e instancias.
    """
    identificador = template.replace("tpl_", "jl_")
    fuente = [
        [
            {"file": ev.file, "line_start": ev.line_start, "line_end": ev.line_end}
            for op in ordered
            for ev in op.evidence[:1]
        ]
        for ordered, _ in instances
    ]
    existente = next((j for j in plan.joblets if j["id"] == identificador), None)
    if existente is None:
        existente = {
            "id": identificador,
            "etiquetas": [],
            "operaciones": [op.kind for op in body],
            "apariciones": 0,
            "parametros": [],
            "instancias": [],
            "fuente": [],
        }
        plan.joblets.append(existente)
    if label not in existente["etiquetas"]:
        existente["etiquetas"].append(label)
    existente["apariciones"] += len(instances)
    existente["parametros"] = sorted(
        set(existente["parametros"]) | {f"parametro_{k}" for k in varying}
    )
    existente["instancias"] += contexts
    existente["fuente"] += fuente
    existente["por_que"] = (
        f"el mismo bloque de {len(body)} operaciones aparece {existente['apariciones']} veces"
    )


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


def _acyclic_after(graph: Graph, members: list[str]) -> bool:
    """Si el grafo sigue siendo acíclico al contraer `members` en un solo nodo.

    Las instancias de una plantilla no tienen aristas entre sí, pero sí pueden depender de un
    operador común: en ese caso colapsarlas crearía un ciclo.
    """
    group = set(members)
    contracted = nx.DiGraph()
    for edge in graph.edges():
        src = "grupo" if edge.src in group else edge.src
        dst = "grupo" if edge.dst in group else edge.dst
        if src != dst:
            contracted.add_edge(src, dst)
    return nx.is_directed_acyclic_graph(contracted)


def _replace_with_iterate(
    graph: Graph,
    builder: Builder,
    log: PassLog,
    template: str,
    label: str | None,
    ops: list[Operator],
    contexts: list[dict],
) -> None:
    """Sustituye `ops` por un `iterate` que llama a la plantilla con `contexts`."""
    evidence = []
    for op in ops:
        for ev in op.evidence:
            if ev not in evidence:
                evidence.append(ev)
    params = {"template": template, "instancias": contexts}
    iterate = Operator(
        id=builder.next_id(),
        kind="iterate",
        params=params,
        placement="flow",
        evidence=evidence,
        status="parcial" if any(o.status == "parcial" for o in ops) else "soportado",
        signature=signature("iterate", params),
        notes=[f"{len(contexts)} instancias de la plantilla {template} (etiqueta: {label})"],
    )
    members = [op.id for op in ops]
    graph.replace(members, iterate)
    log.created.append(iterate.id)
    log.merged += members


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
        contexts = [{f"parametro_{k}": names[k] for k in varying} for _, names in instances]
        every = [op for ordered, _ in instances for op in ordered]
        if _acyclic_after(graph, [op.id for op in every]):
            # Una llamada en bucle (tFlowToIterate) con la lista de contextos de las instancias.
            _replace_with_iterate(graph, builder, log, template, label, every, contexts)
        else:
            # Colapsar rompería el orden (una instancia depende de otra): una llamada por instancia.
            for (ordered, _), context in zip(instances, contexts, strict=True):
                _replace_with_iterate(graph, builder, log, template, label, ordered, [context])
        if len(instances) >= JOBLET_MIN_OCCURRENCES and len(body) >= JOBLET_MIN_OPERATIONS:
            _register_joblet(ctx.plan, template, label, body, instances, varying, contexts)
        log.notes.append(
            f"plantilla {template}: {len(instances)} instancias, {len(varying)} parámetros"
        )
    log.metrics["plantillas"] = len({n for n in log.notes if n.startswith("plantilla")})
    return log
