"""Estrategia de ubicación "cargar una vez, calcular en la base" (`placement_strategy: push_to_db`).

Dos pasos, llamados desde las pasadas 4 y 5:
- `place` (pasada 4): una cadena lineal de operadores con equivalente SQL (`db_sql.DB_KINDS`) se
  ubica en la base. Cada archivo de entrada (`read_file`) que alimenta una cadena de base se
  convierte en un único `external_load` hacia una tabla de trabajo: `sgm_<firma corta>`, nunca el
  nombre del script.
- `fuse` (pasada 5): cada cadena de base se sustituye por un solo `exec_sql` con su SQL (dialecto
  Hive). Un operador de la cadena que no tenga SQL no se ubica en la base: el candidato se
  comprueba antes de ubicarlo.

Un `join` o un `union` no entran en la base: sin esquemas no se pueden calificar sus columnas con
seguridad. Quedan en flujo y su entrada desde base se corta con un `read` de frontera.
"""

from __future__ import annotations

import sqlglot

from sgm.ir.builder import Builder
from sgm.ir.models import Graph, Operator
from sgm.ir.signature import signature
from sgm.passes import db_sql
from sgm.passes.base import PassContext, PassLog

TABLE_PREFIX = "sgm_"  # prefijo de las tablas de trabajo que crea la carga única


def _table_name(op: Operator) -> str:
    return f"{TABLE_PREFIX}{op.signature[:8]}"


def _candidates(graph: Graph, target: str) -> set[str]:
    """Operadores que pueden ir a la base: cadenas lineales desde una fuente de base o archivo."""
    found: set[str] = set()
    for op_id in graph.topological():
        op = graph.operator(op_id)
        if op.kind not in db_sql.DB_KINDS:
            continue
        preds = graph.predecessors(op_id)
        if len(preds) != 1 or db_sql._step_sql(op, "SELECT 1") is None:
            continue
        pred = graph.operator(preds[0])
        # Un read_file se convierte en carga única; una carga o lectura de base solo cuenta si
        # tiene una tabla concreta (sin tabla no hay SQL que construir sobre ella).
        source = pred.kind == "read_file" or (
            pred.placement == target and db_sql._source_table(pred) is not None
        )
        chained = pred.id in found and len(graph.successors(pred.id)) == 1
        if source or chained:
            found.add(op_id)
    return found


def _is_work(op: Operator) -> bool:
    dataset = str(op.params.get("dataset", ""))
    return "." not in dataset or dataset.split(".", 1)[0].upper() == "WORK"


def _library_placement(op: Operator, ctx: PassContext) -> None:
    """Lectura o escritura de una biblioteca permanente: el motor de `env/engines.json`."""
    dataset = str(op.params.get("dataset", ""))
    library = dataset.split(".", 1)[0].upper() if "." in dataset else "WORK"
    engine = ctx.library_engines.get(library) if library != "WORK" else None
    op.placement = f"db:{engine}" if engine else "flow"


def place(graph: Graph, ctx: PassContext, builder: Builder) -> PassLog:
    """Ubica en la base las cadenas candidatas y convierte sus archivos de entrada en cargas."""
    log = PassLog("p04_placement.push")
    target = f"db:{ctx.project.target_engine}"
    # Una lectura de WORK con un único productor solo referencia ese dataset: se quita, para que
    # la cadena de base no se corte en ella (el productor pasa directo al consumidor).
    references = 0
    for op in list(graph.operators()):
        if op.kind == "read" and _is_work(op) and len(graph.predecessors(op.id)) == 1:
            graph.bypass(op.id)
            references += 1
    log.metrics["referencias_work_quitadas"] = references
    for op in graph.operators():
        if op.kind in ("read", "write") and op.placement is None:
            _library_placement(op, ctx)
    candidates = _candidates(graph, target)
    for op_id in candidates:
        graph.operator(op_id).placement = target
    # Una carga por archivo: si el mismo archivo se lee en varios sitios (mismo destino), las
    # lecturas repetidas se fusionan en la primera carga.
    loads: dict[str, Operator] = {}
    for op in list(graph.operators()):
        if op.kind != "read_file" or not any(s in candidates for s in graph.successors(op.id)):
            continue
        destination = _table_name(op)
        if destination in loads:
            graph.merge(loads[destination].id, op.id)
            continue
        _load(op, target)
        loads[destination] = op
    log.metrics.update({"candidatos_en_base": len(candidates), "cargas_unicas": len(loads)})
    log.notes.append(f"{len(candidates)} operadores en base; {len(loads)} cargas únicas")
    return log


def _load(op: Operator, target: str) -> None:
    """Convierte un `read_file` en la carga única de su archivo a la tabla de trabajo."""
    datafile = op.params.get("datafile")
    op.kind = "external_load"
    op.params = {"input": datafile, "destination": _table_name(op), "source": "archivo"}
    op.placement = target
    op.signature = signature("external_load", op.params)


def fuse(graph: Graph, ctx: PassContext) -> PassLog:
    """Sustituye cada cadena de base por un `exec_sql` con su SQL, en el dialecto de Hive."""
    log = PassLog("p05_sql_fusion.db")
    target = f"db:{ctx.project.target_engine}"
    builder = Builder(graph)
    fused = 0
    for op in list(graph.operators()):
        if op.kind not in db_sql.DB_KINDS or op.placement != target or op.id not in graph:
            continue
        successors = graph.successors(op.id)
        if len(successors) == 1 and _is_candidate_step(graph.operator(successors[0]), target):
            continue  # el final de la cadena es un paso posterior de la misma base
        steps = db_sql.chain(graph, op)
        if steps is None:
            continue
        query = db_sql.render(steps)
        if query is None:
            continue
        out = _output_name(graph, op)
        text = f"CREATE TABLE {out} AS {query}"
        try:
            sql = sqlglot.transpile(text, write="hive")[0]
        except sqlglot.errors.SqlglotError:
            continue
        # La fuente (carga o lectura de base) se queda: solo se sustituyen los pasos de SQL.
        ids = [s.id for s in steps if db_sql._source_table(s) is None]
        new = Operator(
            id=builder.next_id(),
            kind="exec_sql",
            params={"sql": sql, "outputs": [out], "fused_steps": len(steps)},
            placement=target,
            evidence=[ev for s in steps for ev in s.evidence],
            status="soportado",
            signature=signature("exec_sql", {"sql": sql}),
            notes=[f"cadena de {len(steps)} pasos ejecutada en la base"],
        )
        graph.replace(ids, new)
        log.created.append(new.id)
        log.merged += ids
        fused += 1
    log.metrics["cadenas_en_base"] = fused
    log.notes.append(f"{fused} cadenas de base sustituidas por exec_sql")
    return log


def _is_candidate_step(op: Operator, target: str) -> bool:
    return op.kind in db_sql.DB_KINDS and op.placement == target


def _output_name(graph: Graph, op: Operator) -> str:
    """Tabla que crea la cadena: el dataset que consume el flujo después, o la tabla de trabajo."""
    for edge in graph.edges():
        if edge.src == op.id and not edge.dataset.startswith("("):
            return edge.dataset.split("@")[0].replace("WORK.", "").replace(".", "_")
    return f"{TABLE_PREFIX}{op.signature[:8]}_out"
