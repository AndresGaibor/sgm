"""Pasada 3: la región de carga externa, reconocida por estructura y no por nombres.

Una carga externa tiene esta forma, sin importar cómo se llamen sus macros:
1. Lanzamiento: algún paso arma comandos de sistema que terminan en `&` (segundo plano).
2. Espera: algún paso espera con un bucle que cuenta procesos (`until`, `ps`, `wc -l`).

Desde el lanzamiento y la espera, la región crece por la maquinaria de carga vecina
(`region.grow`). Después se sustituye por un único `external_load` con la evidencia de todas sus
líneas. Las reglas de crecimiento están en `region.py`; el modelo de datos, en el docstring de ese
módulo.
"""

from __future__ import annotations

import re

from sgm.ir.builder import Builder
from sgm.ir.models import Evidence, Graph, Operator
from sgm.ir.signature import signature
from sgm.passes import p02_plumbing, region
from sgm.passes.base import PassContext, PassLog

NAME = "p03_intrinsics"
_COUNT = re.compile(r"(?i)\bcount\s*\(\s*\*\s*\)")


def _engine(block: list[Operator]) -> str | None:
    engines: dict[str, int] = {}
    for op in block:
        if op.placement and op.placement.startswith("db:"):
            engine = op.placement.split(":", 1)[1]
            engines[engine] = engines.get(engine, 0) + 1
    return max(engines, key=engines.get) if engines else None


def _external_load(block: list[Operator], builder: Builder, facts: region.FactBook) -> Operator:
    """Operador que reemplaza la región. Entrada: lo que la región lee y no produce.
    Destino: lo que produce y no vuelve a leer. Si no se deduce, queda parcial."""
    produced = {name for op in block for kind, name in facts.of(op).defs if kind == "d"}
    consumed = {name for op in block for kind, name in facts.of(op).uses if kind == "d"}
    inputs = sorted(consumed - produced)
    destinations = sorted(produced - consumed)
    engine = _engine(block)
    evidence: list[Evidence] = []
    for op in block:
        for ev in op.evidence:
            if ev not in evidence:
                evidence.append(ev)
    params = {
        "input": inputs[0] if inputs else None,
        "destination": destinations[-1] if destinations else None,
        "launch": "comandos de sistema en segundo plano (&)",
        "wait": "bucle de espera por procesos (until, ps, wc -l)",
        "verify_count": any(_COUNT.search(p02_plumbing.op_text(op)) for op in block),
        "absorbed": len(block),
    }
    notes = ["reemplaza la región de carga externa detectada por estructura"]
    status = "soportado"
    if params["input"] is None:
        notes.append("entrada no declarada en la región: la define el programa anterior")
        status = "parcial"
    if params["destination"] is None:
        notes.append("tabla destino no declarada en el SAS: se toma del comando externo")
        status = "parcial"
    if engine is None:
        notes.append("motor del destino no determinado en la región")
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
    facts = region.FactBook()
    seq = graph.operators()
    facts.mark_remote(seq)
    floor = 0  # primer operador que una región puede absorber (después de la región anterior)
    while True:
        flow = region.Flow(seq, facts, ctx.macro_params)
        units = region.units(seq)
        starts = [k for k, (a, _) in enumerate(units) if a >= floor]
        launch = next((k for k in starts if _has(seq, units, k, facts, "launch")), None)
        if launch is None:
            break
        wait = next(
            (k for k in range(launch + 1, len(units)) if _has(seq, units, k, facts, "wait")), None
        )
        if wait is None:
            break
        ceiling = next(
            (k for k in range(wait + 1, len(units)) if _has(seq, units, k, facts, "launch")),
            len(units),
        )
        first, last = region.grow(seq, units, launch, wait, starts[0], ceiling, flow)
        lo, hi = units[first][0], units[last][1]
        block = seq[lo : hi + 1]
        new = _external_load(block, builder, facts)
        ids = [op.id for op in block]
        graph.replace(ids, new)
        ctx.plan.not_migrated = [nm for nm in ctx.plan.not_migrated if nm.op_id not in set(ids)]
        log.created.append(new.id)
        log.merged += ids
        log.notes.append(f"carga externa: {len(block)} operadores -> {new.id}")
        seq[lo : hi + 1] = [new]
        floor = lo + 1
    log.metrics["cargas_externas"] = len(log.created)
    removed = p02_plumbing.remove_marked(graph, ctx)
    log.removed += removed.removed
    log.metrics["fontaneria_quitada"] = len(removed.removed)
    return log


def _has(
    seq: list[Operator], units: list[tuple[int, int]], k: int, facts: region.FactBook, what: str
) -> bool:
    """Si alguna sentencia de la unidad k es de lanzamiento (`launch`) o de espera (`wait`)."""
    a, b = units[k]
    return any(getattr(facts.of(op), what) for op in seq[a : b + 1])
