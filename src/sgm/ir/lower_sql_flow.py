"""PROC SQL sobre datasets de flujo (WORK, o bibliotecas sin motor) a operadores lógicos.

Cada consulta se convierte en una cadena de operadores de flujo, en el orden lógico de SQL:
lecturas y uniones, filtro (WHERE), agregado (GROUP BY y funciones de agregado), filtro del
agregado (HAVING), expresiones calculadas (derive), deduplicado (DISTINCT) y orden (ORDER BY).
Un UNION une las ramas. Así el SQL nunca se queda como `exec_sql` opaco, que la escalera
traduciría a `tJava`.

Las expresiones se guardan como texto SQL (con las macro variables restauradas). Si una función no
tiene equivalente Talend, la pasada 10 la deja pendiente (`FUNCION_NO_MAPEADA`) sin cambiar el
componente. Los helpers de texto, de agregados y de cruces viven en sus módulos `lower_sql_*.py`.
"""

from __future__ import annotations

import re

from sgm.frontend.sql_normalize import NormalizedSql
from sgm.ir import operadores, sql_semantics
from sgm.ir.builder import Builder, qualify
from sgm.ir.lower_sql_agregados import lower_agregado
from sgm.ir.lower_sql_cruces import _cruce_de_existencia, _params_de_union
from sgm.ir.lower_sql_texto import (
    _AGGREGATE,
    _calificar,
    _column,
    _names,
    _restore,
    _tablas,
    _target_name,
)
from sgm.ir.models import Evidence, Operator
from sgm.ir.pasos import paso as _paso
from sgm.ir.sql_tree import SelectSpec, Source, SqlTree


def _asignacion(item, tablas: dict[str, str], normalized: NormalizedSql) -> dict:
    """Una columna del SELECT como asignación del `derive`: destino, expresión y origen."""
    expresion = _calificar(_restore(item.expression, normalized), tablas)
    estrella = re.fullmatch(r"(\w+)\.\*", expresion)
    if estrella and estrella.group(1).lower() in tablas:
        # `t.*`: todas las columnas de `t`; el emisor las expande con el esquema de esa entrada.
        expresion = f"{tablas[estrella.group(1).lower()]}.*"
    return {
        "target": item.alias or item.column or _target_name(expresion),
        "expression": expresion,
        "origin": "columna" if item.column else "expresion",
    }


class _Chain:
    """Constructor de la cadena de una rama: cada paso se enlaza con el anterior."""

    def __init__(self, ev: Evidence, b: Builder, normalized: NormalizedSql) -> None:
        self.ev = ev
        self.b = b
        self.normalized = normalized

    def read(self, source: Source) -> Operator:
        name = qualify(_restore(source.name, self.normalized))
        return self.b.op("read", {"dataset": name}, self.ev)

    def step(
        self, kind: str, params: dict, previous: Operator, status: str = "soportado"
    ) -> Operator:
        op = self.b.op(kind, params, self.ev, status=status)
        self.b.link(previous, op)
        return op


def _necesita_proyeccion(spec: SelectSpec, assignments: list[dict]) -> bool:
    """Si el SELECT cambia algo: una lista de columnas deja solo esas, y un alias o una expresión
    cambian lo que hay.

    `select a, b from s` **sí** necesita proyección: la lectura trae todas las columnas de `s` y el
    resultado de SAS trae solo `a` y `b`. Sin ella, la tabla de salida arrastra columnas de más y el
    Job escribe un archivo que no es el del SAS. Solo `select *` la evita, porque no recorta nada.
    """
    if spec.group_by or any(not it.star and _AGGREGATE.search(it.expression) for it in spec.items):
        # El agregado ya entrega solo su llave y sus agregados: proyectar detrás no recorta nada,
        # tenga o no uniones delante.
        return False
    if spec.joins or spec.semis:
        return True
    return bool(assignments)


def _branch(spec: SelectSpec, chain: _Chain, normalized: NormalizedSql) -> Operator:
    """Operadores de una rama de SELECT, en el orden lógico de SQL. Devuelve el último."""
    aliases = {s.alias.lower() for s in [spec.base] if s and s.alias}
    aliases |= {j.source.alias.lower() for j in spec.joins if j.source.alias}
    tablas = _tablas(spec)
    if spec.base is None:
        current = chain.b.op("derive", {"assignments": []}, chain.ev)
    else:
        current = chain.read(spec.base)
    for join in spec.joins:
        right = chain.read(join.source)
        pares = join.qualified or join.keys
        keys = [[_calificar(left, tablas), _calificar(derecha, tablas)] for left, derecha in pares]
        params = _params_de_union(
            join.kind,
            keys,
            [qualify(_restore(spec.base.name, normalized))] if spec.base else [],
            _restore(join.condition, normalized) if join.condition else None,
            legado={
                "by": [left for left, _ in join.keys],
                "keys": keys,
                "join_type": join.kind,
                "sources": [qualify(_restore(spec.base.name, normalized))] if spec.base else [],
                "condition": _restore(join.condition, normalized) if join.condition else None,
            },
        )
        status = "soportado" if join.keys or join.kind == "cross" else "parcial"
        op = chain.b.op("join", params, chain.ev, status=status)
        chain.b.link(current, op)
        chain.b.link(right, op)
        current = op
    for numero, semi in enumerate(spec.semis, start=1):
        current = _cruce_de_existencia(semi, numero, current, chain, tablas, normalized)
    if spec.where:
        current = chain.step(
            "filter",
            {"expression": _restore(_column(spec.where, aliases), normalized)},
            current,
            status="parcial" if spec.subqueries else "soportado",
        )
    aggregates = [it for it in spec.items if not it.star and _AGGREGATE.search(it.expression)]
    # Una expresión sobre agregados (`COUNT(*) - COUNT(x)`): cada llamada se agrega por su cuenta
    # (`agg_1`, `agg_2`) y un `derive` detrás calcula la expresión con esos nombres.
    aggregate_order: list[tuple[str, bool]] = []
    if spec.group_by or aggregates:
        current, aggregate_order = lower_agregado(
            spec, chain, current, aliases, tablas, normalized, aggregates
        )
    assignments = [
        _asignacion(it, tablas, normalized)
        for it in spec.items
        if not it.star and it not in aggregates
    ]
    if (
        (assignments and _necesita_proyeccion(spec, assignments))
        or current.kind == "read"
        or current.kind == "join"
    ):
        current = chain.step(
            "derive",
            {"assignments": assignments},
            current,
            status="parcial" if spec.windows else "soportado",
        )
    if spec.distinct:
        current = _paso(
            chain,
            "dedup",
            {"by": _names(spec.items), "keep": "first"},
            lambda: operadores.deduplicar("_", _names(spec.items)),
            current,
        )
    if spec.order_by:
        if spec.group_by or aggregates:
            by = [expression for expression, _ in aggregate_order]
        else:
            by = [_column(expr, aliases) for expr, _ in spec.order_by]
        desc = [desc for _, desc in spec.order_by]
        current = _paso(
            chain,
            "sort",
            {"by": by, "descending": desc},
            lambda: operadores.ordenar("_", by, desc),
            current,
        )
    return current


def lower_query(tree: SqlTree, normalized: NormalizedSql, ev: Evidence, b: Builder) -> None:
    """Operadores de una consulta (CREATE TABLE ... AS SELECT o SELECT) en flujo."""
    chain = _Chain(ev, b, normalized)
    ends = [_branch(spec, chain, normalized) for spec in tree.selects]
    if len(ends) > 1:
        final = b.op("union", {"sources": [], "all": tree.union_all}, ev)
        for end in ends:
            b.link(end, final)
    else:
        final = ends[0]
    if tree.target:
        final.params["outputs"] = [qualify(_restore(tree.target, normalized))]
        b.refresh(final)
    if normalized.into_vars:
        _host_assignments(tree, normalized, final, chain)


def _host_assignments(
    tree: SqlTree, normalized: NormalizedSql, final: Operator, chain: _Chain
) -> None:
    """SELECT ... INTO :v1, :v2: cada macro variable toma la expresión de su posición.

    La asignación es un operador `set_variable` del programa anfitrión, no SQL. Un valor sale como
    `soportado` si la consulta da una sola fila (todo son agregados sin GROUP BY) o si hay un
    separador; en los demás casos queda `parcial`, porque no está demostrado qué valor toma SAS.
    Si la regla no es `programa_anfitrion` (tratamiento `pendiente`), la asignación siempre es
    `parcial`.
    """
    select = tree.selects[0]
    single_row = (
        len(tree.selects) == 1
        and not select.group_by
        and bool(select.items)
        and all(_AGGREGATE.search(it.expression) for it in select.items if not it.star)
    )
    host = sql_semantics.tratamiento(sql_semantics.SELECT_INTO) == "programa_anfitrion"
    for position, (variable, separator) in enumerate(normalized.into_vars):
        item = select.items[position] if position < len(select.items) else None
        has_item = item is not None and not item.star
        proven = host and has_item and (single_row or separator is not None)
        params = {
            "variable": variable,
            "separator": separator,
            "regla": sql_semantics.SELECT_INTO,
            "column": (item.alias or item.column) if has_item else None,
            "expression": _restore(item.expression, normalized) if has_item else None,
        }
        op = chain.step("set_variable", params, final, status="soportado" if proven else "parcial")
        if not proven:
            op.notes.append(
                f"{sql_semantics.reglas()[sql_semantics.SELECT_INTO].etiqueta}: valor de "
                f"{variable} sin demostrar (varias filas sin separador, elemento no nombrado "
                "o regla pendiente)"
            )
