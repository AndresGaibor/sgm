"""Pasada 3: carga externa reconocida por estructura, no por nombres.

Una carga externa tiene esta forma, sin importar cómo se llamen sus macros:
1. Lanzamiento: algún paso arma comandos de sistema que terminan en `&` (segundo plano).
2. Espera: algún paso espera con un bucle que cuenta procesos (`until`, `ps`, `wc -l`).

Los pasos de una misma invocación de macro comparten `evidence.call`. Si entre un grupo de
lanzamiento y
un grupo de espera hay invocaciones, todo ese tramo (troceo, comandos, espera, revisión, conteos) se
reemplaza por un único `external_load`: lee el dataset de entrada y carga la tabla destino, con
`placement=db:<motor>` del motor que usa el bloque.

Después de reemplazar, quita los operadores de fontanería que sobrevivieron (p02, `remove_marked`).
"""

from __future__ import annotations

import re
from collections import Counter

from sgm.ir.builder import Builder
from sgm.ir.models import Evidence, Graph, Operator
from sgm.ir.signature import signature
from sgm.passes import p02_plumbing
from sgm.passes.base import PassContext, PassLog

NAME = "p03_intrinsics"
_LAUNCH = re.compile(r"&\s*[\"']")  # comando en segundo plano dentro de un literal: "... &"
_WAIT = re.compile(r"(?is)\buntil\b.*\bwc\s+-l\b|\bps\b.*\bwc\s+-l\b")


def _groups(graph: Graph) -> list[tuple[str, list[Operator]]]:
    """Operadores agrupados por invocación de macro, en orden de aparición."""
    groups: dict[str, list[Operator]] = {}
    for op in graph.operators():
        call = op.evidence[0].call if op.evidence else None
        if call:
            groups.setdefault(call, []).append(op)
    return sorted(groups.items(), key=lambda kv: min(o.id for o in kv[1]))


def _has(ops: list[Operator], pattern: re.Pattern[str]) -> bool:
    return any(pattern.search(p02_plumbing.op_text(op)) for op in ops)


def _engine(block: list[Operator]) -> str | None:
    engines = Counter(
        op.placement.split(":", 1)[1]
        for op in block
        if op.placement and op.placement.startswith("db:")
    )
    return engines.most_common(1)[0][0] if engines else None


def _consumed_in(block: list[Operator]) -> set[str]:
    names: set[str] = set()
    for op in block:
        if op.kind == "read" and op.params.get("dataset"):
            names.add(op.params["dataset"])
        for key in ("inputs", "sources"):
            names.update(n for n in op.params.get(key, []) if isinstance(n, str))
    return names


def _external_load(block: list[Operator], ctx: PassContext, builder: Builder) -> Operator:
    """Operador que reemplaza el bloque. Entrada: lo que el bloque lee y no produce.
    Destino: lo que el bloque produce y no vuelve a leer. Si no se deduce, queda parcial."""
    produced = [name for op in block for name in op.params.get("outputs", [])]
    consumed = _consumed_in(block)
    inputs = [name for name in consumed if name not in produced]
    destinations = [name for name in produced if name not in consumed]
    engine = _engine(block)
    evidence: list[Evidence] = []
    for op in block:
        for ev in op.evidence:
            if ev not in evidence:
                evidence.append(ev)
    params = {
        "input": sorted(inputs)[0] if inputs else None,
        "destination": destinations[-1] if destinations else None,
        "launch": "comandos de sistema en segundo plano (&)",
        "wait": "bucle de espera por procesos (until, ps, wc -l)",
        "groups": len({op.evidence[0].call for op in block}),
    }
    notes = ["reemplaza el bloque de carga externa detectado por estructura"]
    status = "soportado"
    if params["input"] is None:
        notes.append("entrada no declarada en el bloque: la define el programa anterior")
        status = "parcial"
    if params["destination"] is None:
        notes.append("tabla destino no declarada en el SAS: se toma del comando externo")
        status = "parcial"
    if engine is None:
        notes.append("motor del destino no determinado en el bloque")
        status = "parcial"
    return Operator(
        id=builder.next_id(),
        kind="external_load",
        params=params,
        placement=f"db:{engine}" if engine else None,
        evidence=evidence,
        status=status,
        signature=signature("external_load", params),
        notes=notes,
    )


def run(graph: Graph, ctx: PassContext) -> PassLog:
    log = PassLog(NAME)
    builder = Builder(graph)
    groups = _groups(graph)
    i = 0
    while i < len(groups):
        if not _has(groups[i][1], _LAUNCH):
            i += 1
            continue
        end = next((j for j in range(i, len(groups)) if _has(groups[j][1], _WAIT)), None)
        if end is None:
            break
        span = groups[i : end + 1]
        block = [op for _, ops in span for op in ops]
        new = _external_load(block, ctx, builder)
        ids = {op.id for op in block}
        graph.replace(list(ids), new)
        ctx.plan.not_migrated = [nm for nm in ctx.plan.not_migrated if nm.op_id not in ids]
        log.created.append(new.id)
        log.merged += sorted(ids)
        log.notes.append(f"carga externa: {len(span)} invocaciones -> {new.id}")
        groups = groups[:i] + groups[end + 1 :]
    log.metrics["cargas_externas"] = len(log.created)
    removed = p02_plumbing.remove_marked(graph, ctx)
    log.removed += removed.removed
    log.metrics["fontaneria_quitada"] = len(removed.removed)
    return log
