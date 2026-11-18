"""Tipos SAS demostrados por el plan, sin consultar el contenido de las filas."""

from __future__ import annotations

import re

from sgm.ir.models import Graph, Operator
from sgm.ir.types_code import expression_type

_COLUMN = re.compile(r"(?:[a-z_]\w*\.)*([a-z_]\w*)", re.I)
_PASSTHROUGH = frozenset({"filter", "sort", "dedup", "write", "join"})


def _expression_type(text: str, types: dict[str, str]) -> str | None:
    if column := _COLUMN.fullmatch(text.strip()):
        return types.get(column[1].casefold())
    inferred = expression_type(text)
    return inferred.type if inferred else None


def step_types(kind: str, params: dict, types: dict[str, str]) -> dict[str, str]:
    """Conserva los tipos al pasar por una proyección o un cambio de nombre."""
    if kind == "derive":
        if not params.get("assignments"):
            return types
        additive = params.get("modo") == "agrega"
        declared = {name.casefold(): value[0] for name, value in params.get("declared", {}).items()}
        available = {**declared, **types}
        output = dict(available) if additive else {}
        for assignment in params.get("assignments", []):
            name = assignment["target"].casefold()
            known = available.get(name) if additive else None
            if not known and not assignment.get("conditional"):
                known = _expression_type(assignment["expression"], available)
            if known:
                output[name] = known
                if additive:
                    available[name] = known
        return output
    if kind == "aggregate":
        keys = params.get("group_outputs")
        if keys is None:
            keys = [{"expression": key, "alias": key} for key in params.get("group_by", [])]
        return {
            item["alias"].casefold(): known
            for item in [*keys, *params["aggregations"]]
            if (known := _expression_type(item["expression"], types)) is not None
        }
    if kind == "select":
        names = {name.casefold() for name in params.get("names", [])}
        return {name: known for name, known in types.items()
                if (name in names) == (params.get("mode") == "keep")}
    if kind == "rename":
        renames = {old.casefold(): new.casefold() for old, new in params.get("pairs", [])}
        return {renames.get(name, name): known for name, known in types.items()}
    return types if kind in _PASSTHROUGH else {}


def output_types(graph: Graph, op: Operator) -> dict[str, str]:
    """Aplica la lista de columnas proyectadas de cada rama a su propia fuente."""
    parents = graph.predecessors(op.id)
    if op.kind == "map" or op.kind in {"derive", "aggregate", "select", "rename", *_PASSTHROUGH}:
        if len(parents) == 1:
            types = output_types(graph, graph.operator(parents[0]))
        elif op.kind == "map":
            types = {}
            ambiguous = set()
            for parent in parents:
                for name, kind in output_types(graph, graph.operator(parent)).items():
                    if name in types and types[name] != kind:
                        ambiguous.add(name)
                        types.pop(name)
                    elif name not in ambiguous:
                        types[name] = kind
        else:
            types = {}
        steps = op.params.get("steps") or [{"kind": op.kind, "params": op.params}]
        for step in steps:
            types = step_types(step["kind"], step["params"], types)
        if op.kind == "map" and len(parents) > 1:
            schema = {column.name.casefold(): column.type for column in op.schema or []
                      if column.type and column.source in {"catalog", "code"}}
            projected = {
                assignment["target"].casefold()
                for step in steps if step["kind"] == "derive"
                for assignment in step["params"].get("assignments", [])
                if assignment.get("origin") == "columna"
                and _COLUMN.fullmatch(str(assignment.get("expression") or "").strip())
            }
            for name in projected & schema.keys():
                types.setdefault(name, schema[name])
        return types
    explicit = {column.name.casefold(): column.type for column in op.schema or []
                if column.type and column.source in {"catalog", "code"}}
    if op.kind == "read" and len(parents) == 1:
        return {**explicit, **output_types(graph, graph.operator(parents[0]))}
    return explicit if op.kind in {"read", "read_file"} else {}
