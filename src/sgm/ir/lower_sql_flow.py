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
from sgm.ir.sql_tree import Item, SelectSpec, SemiSpec, Source, SqlTree

_AGGREGATE = re.compile(r"(?i)\b(sum|count|avg|mean|min|max|std|stddev|n|nmiss|range|median)\s*\(")
_DOTTED = re.compile(r"\b([A-Za-z_]\w*)\.([A-Za-z_]\w*)")


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
        # El agregado ya entrega solo su llave y sus agregados: proyectar detrás no recorta nada,
        # tenga o no uniones delante.
        return False
    if spec.joins or spec.semis:
        return True
    return bool(assignments)


_ARGUMENTO = re.compile(
    r"(?is)^\s*\w+\s*\(\s*(?:distinct\s+)?([A-Za-z_]\w*(?:\.[A-Za-z_]\w*)?)\s*\)\s*$"
)


def _columnas_del_agregado(
    spec: SelectSpec, aggregates: list, tablas: dict[str, str], normalized: NormalizedSql
) -> list[dict]:
    """Columnas que un `GROUP BY` lee de un cruce: las llaves y el argumento de cada agregado.

    Tras un `JOIN` el agregado no puede leer «lo que haya»: necesita que el cruce entregue, con el
    nombre y la tabla de origen, las columnas que agrupa y suma. Un argumento que no es una columna
    sola (`SUM(a * b)`) no se proyecta: el agregado lo deja pendiente.
    """
    textos = [str(g) for g in spec.group_by]
    for it in aggregates:
        encontrado = _ARGUMENTO.match(it.expression)
        if encontrado:
            textos.append(encontrado.group(1))
    columnas: dict[str, dict] = {}
    for texto in textos:
        expresion = _calificar(_restore(texto, normalized), tablas)
        destino = expresion.split(".")[-1]
        columnas.setdefault(
            destino.lower(), {"target": destino, "expression": expresion, "origin": "columna"}
        )
    return list(columnas.values())


_LLAMADA_AGREGADO = re.compile(
    r"(?i)\b(?:count|sum|avg|mean|min|max)\s*\(\s*(?:distinct\s+)?"
    r"(?:\*|[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)?)\s*\)"
)


def _descomponer(expresion: str, ocultas: dict[str, str]) -> str | None:
    """Una expresión sobre agregados (`COUNT(*) - COUNT(x)`) con cada llamada por un nombre.

    Devuelve el texto con los nombres (`agg_1 - agg_2`) y deja en `ocultas` llamada -> nombre.
    `None` si no es de esa clase: ya es una llamada sola, lleva una subconsulta o trae un agregado
    que no es `FUNCION(columna)`.
    """
    if re.search(r"(?i)\bselect\b", expresion) or _LLAMADA_AGREGADO.fullmatch(expresion.strip()):
        return None

    locales = dict(ocultas)

    def cambiar(m: re.Match) -> str:
        return locales.setdefault(m.group(0), f"agg_{len(locales) + 1}")

    reemplazada = _LLAMADA_AGREGADO.sub(cambiar, expresion)
    if reemplazada == expresion or _AGGREGATE.search(reemplazada):
        return None
    ocultas.update(locales)
    return reemplazada


def _cruce_de_existencia(
    semi: SemiSpec,
    numero: int,
    current: Operator,
    chain: _Chain,
    tablas: dict[str, str],
    normalized: NormalizedSql,
) -> Operator:
    """`col IN (SELECT k ...)` como un cruce: la subconsulta se reduce a sus llaves sin repetir.

    * `IN`: cruce interno contra las llaves únicas; ninguna fila se repite.
    * `NOT IN`: cruce izquierdo y se quedan las filas sin pareja. En SAS el faltante es un valor
      más, así que `NOT IN` con faltantes en la lista se comporta como una comparación de valores.
    La subconsulta se arma como una cadena aparte que termina en una tabla temporal del programa.
    """
    sub = semi.sub
    linea = chain.ev.line_start
    tabla = f"WORK.__in_l{linea}_{numero}"
    clave = f"clave_in{numero}"
    alias_sub = {sub.base.alias.lower()} if sub.base and sub.base.alias else set()
    tablas_sub = _tablas(sub)
    actual = chain.read(sub.base)
    if sub.where:
        filtro = _restore(_column(sub.where, alias_sub), normalized)
        actual = chain.step("filter", {"expression": filtro}, actual)
    leida = _calificar(_restore(semi.key, normalized), tablas_sub)
    proyeccion = [{"target": clave, "expression": leida, "origin": "columna"}]
    actual = chain.step("derive", {"assignments": proyeccion}, actual)
    actual = chain.step("dedup", {"by": [clave], "keep": "first", "outputs": [tabla]}, actual)
    derecha = chain.read(Source(tabla))
    chain.b.link(actual, derecha)
    izquierda = _calificar(_restore(semi.column, normalized), tablas)
    params = {
        "by": [izquierda.split(".")[-1]],
        "keys": [[izquierda, f"{tabla.split('.')[-1].lower()}.{clave}"]],
        "join_type": "left" if semi.negate else "inner",
        "sources": [],
        "condition": None,
    }
    cruce = chain.b.op("join", params, chain.ev)
    chain.b.link(current, cruce)
    chain.b.link(derecha, cruce)
    if not semi.negate:
        return cruce
    return chain.step("filter", {"expression": f"missing({clave})"}, cruce)


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
    ocultas: dict[str, str] = {}
    compuestos: dict[int, str] = {}
    for it in aggregates:
        reemplazada = _descomponer(it.expression, ocultas)
        if reemplazada is not None:
            compuestos[id(it)] = reemplazada
    if any(not it.alias for it in aggregates):
        ocultas, compuestos = {}, {}  # sin alias no hay nombre con el que volver a leerlos
    simples = [it for it in aggregates if id(it) not in compuestos]
    if spec.joins and (spec.group_by or aggregates):
        leidas = _columnas_del_agregado(
            spec, [*simples, *(Item(llamada) for llamada in ocultas)], tablas, normalized
        )
        if leidas:
            current = chain.step("derive", {"assignments": leidas}, current)
    if spec.group_by or aggregates:
        params = {
            "group_by": [_column(g, aliases) for g in spec.group_by],
            "aggregations": [
                {
                    "expression": _restore(_column(it.expression, aliases), normalized),
                    "alias": it.alias or it.column or it.expression,
                }
                for it in simples
            ]
            + [
                {"expression": _restore(_column(llamada, aliases), normalized), "alias": nombre}
                for llamada, nombre in ocultas.items()
            ],
        }
        plain = _plain_items(spec) if not spec.group_by else []
        if plain and sql_semantics.tratamiento(sql_semantics.AGREGADO) == "pendiente":
            # SAS remezcla las columnas sin agregar en cada fila: no hay SQL equivalente probado.
            params["pendiente"] = plain
            label = sql_semantics.reglas()[sql_semantics.AGREGADO].etiqueta
            note = f"{label}: columnas sin agregar {', '.join(plain)}; pendiente de decidir"
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
    if compuestos:
        # La salida del agregado ya trae grupos, agregados simples y ocultos: el `derive` arma las
        # columnas del SELECT en su orden, con las expresiones sobre los nombres `agg_k`.
        salida = []
        for it in spec.items:
            if it.star:
                continue
            nombre = it.alias or it.column or _target_name(it.expression)
            if id(it) in compuestos:
                texto = compuestos[id(it)]
                salida.append(
                    {
                        "target": nombre,
                        "expression": _restore(texto, normalized),
                        "origin": "expresion",
                    }
                )
            else:
                salida.append({"target": nombre, "expression": nombre, "origin": "columna"})
        current = chain.step("derive", {"assignments": salida}, current)
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
