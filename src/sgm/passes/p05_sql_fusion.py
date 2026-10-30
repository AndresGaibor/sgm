"""Pasada 5: une cadenas de SQL en la misma base de datos en una sola sentencia con CTE.

Dos operadores `exec_sql` del mismo motor se fusionan cuando:
- el primero escribe un dataset `X` que solo consume el segundo (una sola arista de salida);
- `X` no es salida final ni se escribe en otra parte;
- el nombre de `X` aparece en el SQL del segundo, como tabla simple.

El resultado es un `exec_sql` con `WITH X AS (<select del primero>) <sql del segundo>`. Si el
  segundo
es `create table Y as ...`, la sentencia queda `create table Y as with X as (...) select ...`.

Limitación: solo se fusiona cuando el nombre del intermedio es un identificador simple. Un nombre
con
esquema (`lz.t`) se usa como CTE con su último segmento.
"""

from __future__ import annotations

import re

from sgm.ir.builder import Builder
from sgm.ir.models import Graph, Operator, Pending
from sgm.ir.signature import signature
from sgm.passes.base import PassContext, PassLog

NAME = "p05_sql_fusion"
_CREATE = re.compile(r"(?is)^\s*create\s+table\s+([\w.&]+)\s+(?:stored\s+as\s+\w+\s+)?as\s+(.*)$")
_SELECT_AFTER_AS = re.compile(
    r"(?is)^\s*(?:create\s+table\s+[\w.&]+\s+(?:stored\s+as\s+\w+\s+)?as\s+)?(.*)$"
)


def _table_name(dataset: str) -> str:
    return dataset.split(".")[-1].lower()


def _body(sql: str) -> str:
    """Consulta de una sentencia: lo que sigue a `create table X as` (o la sentencia entera)."""
    created = _CREATE.match(sql.strip())
    return created.group(2).strip() if created else sql.strip()


def _compose(first: Operator, second: Operator) -> str | None:
    """SQL con CTE que sustituye a los dos operadores; None si no se puede componer con seguridad.

    El nombre de la CTE sale del `create table` del primer paso; las referencias a esa tabla en el
    segundo se reescriben al nombre corto.
    """
    created = _CREATE.match(str(first.params.get("sql", "")).strip())
    if not created:
        return None
    target = created.group(1)
    name = _table_name(target)
    second_sql = str(second.params.get("sql", ""))
    if not re.search(rf"(?i)\b{re.escape(target)}\b", second_sql):
        return None
    rewritten = re.sub(rf"(?i)\b{re.escape(target)}\b", name, second_sql)
    cte = f"with {name} as ({created.group(2).strip()})"
    second_created = _CREATE.match(rewritten.strip())
    if second_created:
        return f"create table {second_created.group(1)} as {cte} {second_created.group(2).strip()}"
    if rewritten.strip().lower().startswith("select"):
        return f"{cte} {rewritten.strip()}"
    return None


def _candidates(graph: Graph, ctx: PassContext):
    for edge in graph.edges():
        first, second = graph.operator(edge.src), graph.operator(edge.dst)
        if first.kind != "exec_sql" or second.kind != "exec_sql":
            continue
        if (
            not first.placement
            or not first.placement.startswith("db:")
            or first.placement != second.placement
        ):
            continue
        if len(graph.successors(first.id)) != 1 or len(graph.predecessors(second.id)) != 1:
            continue
        if edge.dataset in second.params.get("outputs", []):
            continue
        yield first, second, edge.dataset


def run(graph: Graph, ctx: PassContext) -> PassLog:
    log = PassLog(NAME)
    builder = Builder(graph)
    fused = True
    while fused:
        fused = False
        for first, second, _ in _candidates(graph, ctx):
            sql = _compose(first, second)
            if sql is None:
                continue
            params = {
                "sql": sql,
                "engine": second.params.get("engine"),
                "outputs": list(second.params.get("outputs", [])),
                "fused": [first.signature, second.signature],
            }
            merged = Operator(
                id=builder.next_id(),
                kind="exec_sql",
                params=params,
                placement=second.placement,
                evidence=_union(first, second),
                status="parcial" if "parcial" in (first.status, second.status) else "soportado",
                signature=signature("exec_sql", params),
                notes=["SQL fusionado con CTE (pasada 5)"],
            )
            graph.replace([first.id, second.id], merged)
            log.created.append(merged.id)
            log.merged += [first.id, second.id]
            ctx.plan.pending.append(
                Pending(
                    signature=first.signature,
                    options=[
                        {
                            "opcion": "fundir",
                            "confianza": "media",
                            "supuesto": "ningún otro programa lee la tabla intermedia",
                        },
                        {
                            "opcion": "conservar",
                            "confianza": "alta",
                            "supuesto": "la tabla intermedia se materializa",
                        },
                    ],
                    default="fundir",
                )
            )
            fused = True
            break
    log.metrics["fusiones_sql"] = len(log.created)
    return log


def _union(first: Operator, second: Operator) -> list:
    evidence = list(first.evidence)
    for ev in second.evidence:
        if ev not in evidence:
            evidence.append(ev)
    return evidence
