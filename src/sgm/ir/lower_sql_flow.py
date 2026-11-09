"""PROC SQL sobre datasets de flujo (WORK, o bibliotecas sin motor) a operadores lógicos.

Cada consulta se convierte en una cadena de operadores de flujo, en el orden lógico de SQL:
lecturas y uniones, filtro (WHERE), agregado (GROUP BY y funciones de agregado), filtro del
agregado (HAVING), expresiones calculadas (derive), deduplicado (DISTINCT) y orden (ORDER BY).
Un UNION une las ramas. Así el SQL nunca se queda como `exec_sql` opaco, que la escalera
traduciría a `tJava`.

Las expresiones se guardan como texto SQL (con las macro variables restauradas). Si una función no
tiene equivalente Talend, la pasada 10 la deja pendiente (`FUNCION_NO_MAPEADA`) sin cambiar el
componente.
"""

from __future__ import annotations

import re

from sgm.frontend.sql_normalize import NormalizedSql
from sgm.ir import sql_semantics
from sgm.ir.builder import Builder, qualify
from sgm.ir.models import Evidence, Operator
from sgm.ir.sql_tree import SelectSpec, Source, SqlTree

_AGGREGATE = re.compile(r"(?i)\b(sum|count|avg|mean|min|max|std|stddev|n|nmiss|range|median)\s*\(")
_DOTTED = re.compile(r"\b([A-Za-z_]\w*)\.([A-Za-z_]\w*)")
_SIMPLE_COLUMN = re.compile(r"(?i)^(?:[a-z_]\w*\.)*([a-z_]\w*)$")


def _restore(text: str, normalized: NormalizedSql) -> str:
    """Devuelve las macro variables a su forma SAS (`mv_x` -> `&x`) en un texto."""
    for placeholder, original in normalized.macros.items():
        text = re.sub(rf"\b{re.escape(placeholder)}\b", original, text)
    return text


_NOT_NULL = re.compile(r"(?i)\bNOT\s+([\w.]+)\s+IS\s+NULL\b")
_IS_NOT_NULL = re.compile(r"(?i)\b([\w.]+)\s+IS\s+NOT\s+NULL\b")
_IS_NULL = re.compile(r"(?i)\b([\w.]+)\s+IS\s+NULL\b")


def _null_tests(text: str) -> str:
    """`x IS NULL` y `x IS NOT NULL` (como los escribe sqlglot) a `missing(x)`, la forma SAS."""
    text = _NOT_NULL.sub(lambda m: f"NOT missing({m.group(1)})", text)
    text = _IS_NOT_NULL.sub(lambda m: f"NOT missing({m.group(1)})", text)
    return _IS_NULL.sub(lambda m: f"missing({m.group(1)})", text)


def _column(text: str, aliases: set[str]) -> str:
    """Nombre de columna de una referencia (`a.k` -> `k`) si el prefijo es un alias de fuente."""
    return _null_tests(
        _DOTTED.sub(lambda m: m.group(2) if m.group(1).lower() in aliases else m.group(0), text)
    )


def _tablas(spec: SelectSpec) -> dict[str, str]:
    """Alias y nombre de tabla, en minúsculas, al nombre de tabla sin biblioteca (`work.x` -> `x`).

    El `tMap` no conoce los alias del SAS: sus llaves y sus expresiones llevan la tabla delante.
    """
    mapa: dict[str, str] = {}
    for source in [spec.base, *(join.source for join in spec.joins)]:
        if source is None:
            continue
        tabla = source.name.lower().split(".")[-1]
        mapa[source.alias.lower() if source.alias else tabla] = tabla
        mapa.setdefault(tabla, tabla)
    return mapa


def _calificar(text: str, tablas: dict[str, str]) -> str:
    """`v.monto` -> `ventas.monto` cuando `v` es un alias de la consulta."""

    def cambiar(m: re.Match) -> str:
        tabla = tablas.get(m.group(1).lower())
        return f"{tabla}.{m.group(2)}" if tabla else m.group(0)

    return _DOTTED.sub(cambiar, text)


def _asignacion(item, tablas: dict[str, str], normalized: NormalizedSql) -> dict:
    """Una columna del SELECT como asignación del `derive`: destino, expresión y origen."""
    expresion = _calificar(_restore(item.expression, normalized), tablas)
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


def _target_name(expression: str) -> str:
    """Nombre de columna para una expresión sin alias: su texto, sin signos, en minúsculas."""
    name = re.sub(r"\W+", "_", expression).strip("_").lower()
    return name or "expr"


def _names(items) -> list[str]:
    """Nombres de salida de los elementos del SELECT (alias o columna); `*` no tiene nombre."""
    return [it.alias or it.column for it in items if not it.star and (it.alias or it.column)]


def _plain_items(spec: SelectSpec) -> list[str]:
    """Elementos del SELECT que no son agregados (ni `*`): columnas que quedarían sin agrupar."""
    return [
        it.alias or it.column or it.expression
        for it in spec.items
        if not it.star and not _AGGREGATE.search(it.expression)
    ]


def _group_outputs(spec: SelectSpec, aliases: set[str]) -> tuple[list[dict], list[str]]:
    """Columnas simples de GROUP BY seleccionadas y columnas que requieren remezcla."""
    group_names = set()
    for group in spec.group_by:
        match = _SIMPLE_COLUMN.fullmatch(_column(group, aliases).strip())
        if match:
            group_names.add(match.group(1).lower())

    outputs = []
    pendientes = []
    for item in spec.items:
        if item.star:
            pendientes.append("*")
            continue
        if _AGGREGATE.search(item.expression):
            continue
        expression = _column(item.expression, aliases).strip()
        match = _SIMPLE_COLUMN.fullmatch(expression)
        nombre = item.alias or item.column or (match.group(1) if match else item.expression)
        if match is None or match.group(1).lower() not in group_names:
            pendientes.append(nombre)
        else:
            outputs.append({"expression": expression, "alias": nombre})
    return outputs, pendientes


def _aggregate_order_by(
    spec: SelectSpec, aliases: set[str]
) -> tuple[list[tuple[str, bool]], list[str]]:
    """Resuelve ORDER BY con salidas seleccionadas; las otras referencias remezclan SAS."""
    selected = {}
    for item in spec.items:
        if item.star:
            continue
        target = item.alias or item.column or item.expression
        expression = _column(item.expression, aliases).strip()
        selected[expression.casefold()] = target
        selected[target.casefold()] = target

    outputs = []
    pendientes = []
    for expression, descending in spec.order_by:
        nombre = _column(expression, aliases).strip()
        destino = selected.get(nombre.casefold())
        if destino is None:
            pendientes.append(f"ORDER BY {nombre}")
        else:
            outputs.append((destino, descending))
    return outputs, pendientes


def _necesita_proyeccion(spec: SelectSpec, assignments: list[dict]) -> bool:
    """Si el SELECT cambia algo: una lista de columnas deja solo esas, y un alias o una expresión
    cambian lo que hay.

    `select a, b from s` **sí** necesita proyección: la lectura trae todas las columnas de `s` y el
    resultado de SAS trae solo `a` y `b`. Sin ella, la tabla de salida arrastra columnas de más y el
    Job escribe un archivo que no es el del SAS. Solo `select *` la evita, porque no recorta nada.
    """
    if spec.group_by or any(
        not it.star and _AGGREGATE.search(it.expression) for it in spec.items
    ):
        # El agregado recibe las llaves seleccionadas y sus agregados en `group_outputs`.
        return False
    if spec.joins:
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
        keys = [
            [_calificar(left, tablas), _calificar(derecha, tablas)] for left, derecha in pares
        ]
        params = {
            "by": [left for left, _ in join.keys],
            "keys": keys,
            "join_type": join.kind,
            "sources": [qualify(_restore(spec.base.name, normalized))] if spec.base else [],
            "condition": _restore(join.condition, normalized) if join.condition else None,
        }
        status = "soportado" if join.keys or join.kind == "cross" else "parcial"
        op = chain.b.op("join", params, chain.ev, status=status)
        chain.b.link(current, op)
        chain.b.link(right, op)
        current = op
    if spec.where:
        current = chain.step(
            "filter",
            {"expression": _restore(_column(spec.where, aliases), normalized)},
            current,
            status="parcial" if spec.subqueries else "soportado",
        )
    aggregates = [it for it in spec.items if not it.star and _AGGREGATE.search(it.expression)]
    if spec.group_by or aggregates:
        aggregate_order, remezcla_order = _aggregate_order_by(spec, aliases)
        params = {
            "group_by": [_column(g, aliases) for g in spec.group_by],
            "output_order": [
                str(it.alias or it.column or it.expression).lower()
                for it in spec.items
                if not it.star
            ],
            "aggregations": [
                {
                    "expression": _restore(_column(it.expression, aliases), normalized),
                    "alias": it.alias or it.column or it.expression,
                }
                for it in aggregates
            ],
        }
        if spec.group_by:
            group_outputs, remezcla = _group_outputs(spec, aliases)
            params["group_outputs"] = group_outputs
            remezcla.extend(remezcla_order)
            if remezcla:
                params["pendiente"] = remezcla
                note = (
                    "REMEZCLA_GROUP_BY_PENDIENTE: referencias no seleccionadas o no agrupadas "
                    f"{', '.join(remezcla)}; no se implementa la remezcla SAS"
                )
                current = chain.step("aggregate", params, current, status="parcial")
                current.notes.append(note)
            else:
                current = chain.step("aggregate", params, current)
        else:
            plain = _plain_items(spec)
            sin_agrupar = []
            if sql_semantics.tratamiento(sql_semantics.AGREGADO) == "pendiente":
                sin_agrupar.extend(plain)
            if any(item.star for item in spec.items):
                sin_agrupar.append("*")
            sin_agrupar.extend(remezcla_order)
            if sin_agrupar:
                # Sin equivalencia para la remezcla, no producir filas resumen parciales.
                params["pendiente"] = sin_agrupar
                label = sql_semantics.reglas()[sql_semantics.AGREGADO].etiqueta
                note = (
                    f"{label}: columnas sin agregar {', '.join(sin_agrupar)}; pendiente de decidir"
                )
                current = chain.step("aggregate", params, current, status="parcial")
                current.notes.append(note)
            else:
                current = chain.step("aggregate", params, current)
        if spec.having:
            having = _column(spec.having, aliases)
            for it in aggregates:
                having = having.replace(_column(it.expression, aliases), it.alias or it.expression)
            current = chain.step(
                "filter",
                {"expression": _restore(_null_tests(having), normalized)},
                current,
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
        current = chain.step("dedup", {"by": _names(spec.items), "keep": "first"}, current)
    if spec.order_by:
        if spec.group_by or aggregates:
            by = [expression for expression, _ in aggregate_order]
        else:
            by = [_column(expr, aliases) for expr, _ in spec.order_by]
        desc = [desc for _, desc in spec.order_by]
        current = chain.step("sort", {"by": by, "descending": desc}, current)
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
