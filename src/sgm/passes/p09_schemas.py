"""Pasada 9: asigna esquemas a cada operador y los propaga por el grafo.

Fuentes de esquema:
- `env/schemas.json` para las lecturas de un dataset del entorno (origen `catalog`).
- Código (origen `code`, R7): una derivación cuyo tipo fija el propio código (`input`, `put`,
  `cast`, literales, aritmética, o `length`/`format` del DATA step) recibe ese tipo.
- Derivación: `derive` añade columnas (origen `derived`, tipo desconocido si el código no lo fija);
  `select` las reduce; `rename` las renombra; `join` y `union` las unen; un agregado no conoce sus
  columnas de salida.

Prioridad: catálogo, encabezado, código, derivado. Una columna que ya tiene tipo no se cambia.

Una columna sin tipo queda con `type=None` y `source="unknown"`; genera un hueco
`TIPO_DESCONOCIDO` con la firma del operador que la introduce. Nunca se inventa un tipo.
"""

from __future__ import annotations

from sgm.ir.models import Column, Gap, Graph, Operator
from sgm.ir.types_code import CodeType, expression_type
from sgm.passes.base import PassContext, PassLog

NAME = "p09_schemas"


def _derived_column(target: str, expression: str, declared: dict) -> Column:
    """Columna que deja una asignación: el tipo que el código demuestra, o desconocido."""
    if target in declared:
        found = CodeType(declared[target][0], declared[target][1])
    else:
        found = expression_type(expression) if expression else None
    if found is None:
        return Column(target, None, None, "derived")
    return Column(target, found.type, found.length, "code")


def _with_derived(base: list[Column], assignments: list[dict], declared: dict) -> list[Column]:
    """Esquema tras las asignaciones de un `derive`: columnas nuevas y tipos que faltaban."""
    columns = _copy(base) or []
    index = {c.name: i for i, c in enumerate(columns)}
    for assignment in assignments:
        target = str(assignment.get("target", "")).lower()
        if not target:
            continue
        derived = _derived_column(target, str(assignment.get("expression", "")), declared)
        if target not in index:
            columns.append(derived)
            index[target] = len(columns) - 1
        elif columns[index[target]].type is None:
            columns[index[target]] = derived
    return columns


def _copy(columns: list[Column] | None) -> list[Column] | None:
    if columns is None:
        return None
    return [Column(c.name, c.type, c.length, c.source) for c in columns]


def _merge(parts: list[list[Column] | None]) -> list[Column] | None:
    if any(p is None for p in parts):
        return None
    seen: dict[str, Column] = {}
    for part in parts:
        for column in part or []:
            seen.setdefault(
                column.name, Column(column.name, column.type, column.length, column.source)
            )
    return list(seen.values())


def _from_inputs(graph: Graph, op: Operator) -> list[Column] | None:
    inputs = [graph.operator(p).schema for p in graph.predecessors(op.id)]
    return _merge(inputs) if inputs else None


def _apply(kind: str, params: dict, base: list[Column] | None) -> list[Column] | None:
    """Esquema de salida de un paso de flujo (de un `map`) dado el esquema de entrada."""
    if base is None:
        return None
    if kind == "derive":
        return _with_derived(base, params.get("assignments", []), params.get("declared", {}))
    if kind == "select":
        listed = set(params.get("names", []))
        keep = params.get("mode") == "keep"
        return [c for c in _copy(base) if (c.name in listed) == keep]
    if kind == "rename":
        pairs = {old: new for old, new in params.get("pairs", [])}
        return [Column(pairs.get(c.name, c.name), c.type, c.length, c.source) for c in base]
    return _copy(base)


def _schema_of(graph: Graph, op: Operator, schemas: dict[str, list[Column]]) -> list[Column] | None:
    if op.kind == "read":
        return _copy(schemas.get(str(op.params.get("dataset", "")).lower()))
    if op.kind in ("filter", "sort", "dedup", "write", "split", "iterate", "external_load"):
        return _from_inputs(graph, op)
    if op.kind == "map" and "steps" in op.params:
        # Sin esquema de entrada, las derivaciones que el código tipa siguen siendo ciertas.
        columns = _from_inputs(graph, op) or []
        for step in op.params["steps"]:
            columns = _apply(step["kind"], step["params"], columns)
        return columns
    if op.kind == "derive":
        # Sin esquema de entrada, las columnas que el código tipa igual son ciertas: se conservan.
        base = _from_inputs(graph, op) or []
        return _with_derived(base, op.params.get("assignments", []), op.params.get("declared", {}))
    if op.kind == "select":
        base = _from_inputs(graph, op)
        if base is None:
            return None
        listed = set(op.params.get("names", []))
        if op.params.get("mode") == "keep":
            return [c for c in base if c.name in listed]
        return [c for c in base if c.name not in listed]
    if op.kind == "rename":
        base = _from_inputs(graph, op)
        if base is None:
            return None
        pairs = {old: new for old, new in op.params.get("pairs", [])}
        return [Column(pairs.get(c.name, c.name), c.type, c.length, c.source) for c in base]
    if op.kind in ("join", "union"):
        return _merge([graph.operator(p).schema for p in graph.predecessors(op.id)])
    return None


def run(graph: Graph, ctx: PassContext, schemas: dict[str, list[Column]] | None = None) -> PassLog:
    log = PassLog(NAME)
    schemas = schemas or {}
    for op_id in graph.topological():
        op = graph.operator(op_id)
        op.schema = _schema_of(graph, op, schemas)
        if op.schema is None:
            continue
        for column in op.schema:
            if column.type is None:
                column.source = "unknown"
                ctx.plan.gaps.append(
                    Gap(
                        signature=op.signature,
                        reason="TIPO_DESCONOCIDO",
                        evidence=list(op.evidence),
                    )
                )
                log.notes.append(f"{op.id}: columna {column.name} sin tipo")
                break
    log.metrics["operadores_con_esquema"] = sum(
        1 for op in graph.operators() if op.schema is not None
    )
    return log
