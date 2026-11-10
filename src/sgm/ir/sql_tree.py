"""Árbol lógico de un PROC SQL: fuentes, uniones, filtros, agregados, selección y orden.

El SQL ya normalizado (`frontend/sql_normalize.py`) se parsea con `sqlglot`. De ese árbol se extrae
solo la estructura que el lowering necesita: no se traduce nada aquí. Las expresiones se devuelven
como texto SQL, y el traductor de expresiones decide después si tienen equivalente en Talend.

Si `sqlglot` no puede parsear el texto, `build` lanza `SqlParseError` (la sentencia queda como
`PARSE_ERROR`). Una sentencia que sí parsea pero no es un SELECT ni un CREATE TABLE AS SELECT lanza
`SqlNotSelect`: el lowering la deja como hueco, no como código Java.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

import sqlglot
from sqlglot import exp

# `sqlglot` avisa por el log cuando cae a un comando; aquí el resultado ya lo trata el lowering.
logging.getLogger("sqlglot").setLevel(logging.ERROR)


class SqlParseError(ValueError):
    """El texto no es SQL que `sqlglot` pueda leer."""


class SqlNotSelect(ValueError):
    """Sentencia de otro tipo (insert, delete, drop...) que no es una consulta."""


class SqlUnsafeIdentifier(ValueError):
    """El AST contiene un identificador que no se puede emitir de forma portable."""


_PORTABLE_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")


@dataclass(frozen=True)
class Source:
    name: str  # tabla o dataset, con su biblioteca si la tiene (WORK.x, LZ.y)
    alias: str | None = None


@dataclass
class JoinSpec:
    source: Source
    kind: str  # inner, left, right, full o cross
    keys: list[tuple[str, str]] = field(default_factory=list)  # pares de columnas `a = b` del ON
    condition: str | None = None  # resto del ON que no es igualdad entre columnas
    on: str | None = None  # texto completo del ON, con sus alias (para generar SQL de base)
    # Los mismos pares que `keys` con la tabla delante (`ventas.id = clientes.id`): el `tMap` no
    # conoce los alias del SAS y necesita el nombre de la tabla.
    qualified: list[tuple[str, str]] = field(default_factory=list)


@dataclass
class Item:
    expression: str  # texto SQL de la expresión
    alias: str | None = None
    column: str | None = None  # si es solo una columna (sin función ni operador)
    star: bool = False  # `select *`


@dataclass
class SemiSpec:
    """`col [NOT] IN (SELECT k FROM t [WHERE ...])`: un cruce de existencia, no una condición."""

    column: str  # la columna de la consulta, quizá con su alias de tabla
    negate: bool
    sub: SelectSpec
    key: str  # la columna que la subconsulta devuelve
    expression: str  # expresión SAS/SQL original, para validar sus límites en el anillo B


@dataclass
class SelectSpec:
    base: Source | None = None
    joins: list[JoinSpec] = field(default_factory=list)
    items: list[Item] = field(default_factory=list)
    distinct: bool = False
    where: str | None = None
    group_by: list[str] = field(default_factory=list)
    having: str | None = None
    order_by: list[tuple[str, bool]] = field(default_factory=list)  # (expresión, descendente)
    subqueries: bool = False  # hay subconsultas sin traducir
    semis: list[SemiSpec] = field(default_factory=list)  # IN / NOT IN con subconsulta simple
    windows: bool = False  # hay funciones de ventana: no se traducen todavía


@dataclass
class SqlTree:
    target: str | None  # tabla que crea el CREATE TABLE AS, o None si es solo un SELECT
    selects: list[SelectSpec]  # una por rama de UNION; una sola si no hay unión
    union_all: bool = False  # las ramas se unen con UNION ALL (sin quitar duplicados)
    identifiers_portable: bool = True


def validate_portable_identifiers(tree: SqlTree) -> None:
    """Falla si el AST actual contiene nombres fuera de la gramática portable."""
    if not tree.identifiers_portable:
        raise SqlUnsafeIdentifier("identificador SQL no representable para Talend")
    nombres = [tree.target] if tree.target else []
    for select in tree.selects:
        fuentes = [select.base, *(join.source for join in select.joins)]
        for source in fuentes:
            if source is not None:
                nombres.append(source.name)
                nombres.append(source.alias)
        for item in select.items:
            nombres.extend((item.alias, None if item.star or item.column == "*" else item.column))
        nombres.extend(
            nombre for pareja in select.group_by for nombre in _nombres_calificados(pareja)
        )
        nombres.extend(
            nombre for pareja in select.order_by for nombre in _nombres_calificados(pareja[0])
        )
        for join in select.joins:
            nombres.extend(nombre for pair in join.keys for nombre in pair)
            nombres.extend(nombre for pair in join.qualified for nombre in pair)
    if any(nombre is not None and not _nombre_portable(nombre) for nombre in nombres):
        raise SqlUnsafeIdentifier("identificador SQL no representable para Talend")


def _nombre_portable(nombre: str) -> bool:
    partes = nombre.split(".")
    return bool(partes) and all(_PORTABLE_IDENTIFIER.fullmatch(parte) for parte in partes)


def _nombres_calificados(expresion: str) -> list[str]:
    """Extrae tokens de nombre separados por punto para las cláusulas estructuradas."""
    return re.findall(r"[A-Za-z_][A-Za-z0-9_.]*", expresion, re.ASCII)


def _name(table: exp.Table) -> str:
    parts = [
        part.name for part in (table.args.get("catalog"), table.args.get("db"), table.this) if part
    ]
    return ".".join(p for p in parts if p)


def _source(node: exp.Expression) -> Source:
    if not isinstance(node, exp.Table):
        raise SqlNotSelect("origen que no es una tabla")
    alias = node.args.get("alias")
    return Source(_name(node), alias.name if alias else None)


def _unwrap(node: exp.Expression) -> exp.Expression:
    """Quita los paréntesis que envuelven una condición: `( a = b )` es la misma igualdad."""
    while isinstance(node, exp.Paren):
        node = node.this
    return node


def _reference(column: exp.Column) -> str:
    """`tabla.columna` si la columna trae tabla; si no, solo la columna."""
    return f"{column.table}.{column.name}" if column.table else column.name


def _equality(condition: exp.Expression) -> tuple[exp.Column, exp.Column] | None:
    """`a.x = b.y` entre dos columnas: las dos columnas. None en cualquier otro caso."""
    condition = _unwrap(condition)
    if isinstance(condition, exp.EQ):
        if isinstance(condition.left, exp.Column) and isinstance(condition.right, exp.Column):
            return condition.left, condition.right
    return None


def _join_keys(
    on: exp.Expression | None,
) -> tuple[list[tuple[str, str]], list[tuple[str, str]], str | None]:
    """Pares de igualdad del ON (sin y con tabla) y el resto de condiciones como texto."""
    if on is None:
        return [], [], None
    plano = _unwrap(on)
    partes = plano.flatten() if isinstance(plano, exp.And) else [plano]
    keys: list[tuple[str, str]] = []
    qualified: list[tuple[str, str]] = []
    rest: list[str] = []
    for part in partes:
        pair = _equality(part)
        if pair is None or isinstance(_unwrap(part), exp.Or):
            rest.append(part.sql())
        else:
            left, right = pair
            keys.append((left.name, right.name))
            qualified.append((_reference(left), _reference(right)))
    return keys, qualified, (" AND ".join(rest) if rest else None)


def _join(join: exp.Join) -> JoinSpec:
    side = (join.args.get("side") or "").lower()
    kind = (join.args.get("kind") or "").lower()
    if side in ("left", "right", "full"):
        flavor = side
    elif kind == "cross" or (not join.args.get("on") and not side):
        flavor = "cross"
    else:
        flavor = "inner"
    keys, qualified, condition = _join_keys(join.args.get("on"))
    on = join.args.get("on")
    return JoinSpec(
        _source(join.this), flavor, keys, condition, on.sql() if on else None, qualified
    )


def _item(node: exp.Expression) -> Item:
    if isinstance(node, exp.Star):
        return Item("*", star=True)
    if isinstance(node, exp.Alias):
        inner = node.this
        column = inner.name if isinstance(inner, exp.Column) else None
        return Item(inner.sql(), alias=node.alias, column=column)
    column = node.name if isinstance(node, exp.Column) else None
    return Item(node.sql(), column=column)


def _semi(conjunto: exp.Expression) -> SemiSpec | None:
    """`col IN (SELECT k FROM t WHERE ...)` o su negación, si la subconsulta es simple.

    Simple es: una tabla, sin cruces ni agrupación, una sola columna y una columna a la izquierda.
    Cualquier otra forma se deja donde está y queda como pendiente.
    """
    negado = isinstance(conjunto, exp.Not)
    en = _unwrap(conjunto.this) if negado else conjunto
    if not isinstance(en, exp.In) or not isinstance(en.this, exp.Column):
        return None
    consulta = en.args.get("query")
    consulta = consulta.this if isinstance(consulta, exp.Subquery) else consulta
    if not isinstance(consulta, exp.Select) or en.args.get("expressions"):
        return None
    try:
        sub = _select(consulta)
    except SqlNotSelect:
        return None
    simple = (
        sub.base is not None and not sub.joins and not sub.group_by and not sub.subqueries
        and not sub.distinct and len(sub.items) == 1 and sub.items[0].column
    )
    if not simple:
        return None
    return SemiSpec(
        _reference(en.this), negado, sub, sub.items[0].expression, conjunto.sql()
    )


def _select(node: exp.Select) -> SelectSpec:
    spec = SelectSpec()
    from_ = node.args.get("from_")
    if from_ is not None:
        spec.base = _source(from_.this)
    spec.joins = [_join(j) for j in node.args.get("joins") or []]
    spec.items = [_item(e) for e in node.expressions]
    spec.distinct = node.args.get("distinct") is not None
    where = node.args.get("where")
    sin_extraer = 0
    if where is not None:
        plano = _unwrap(where.this)
        partes = plano.flatten() if isinstance(plano, exp.And) else [plano]
        restantes: list[exp.Expression] = []
        for parte in partes:
            semi = _semi(_unwrap(parte))
            if semi is None:
                restantes.append(parte)
            else:
                spec.semis.append(semi)
                sin_extraer += sum(1 for _ in parte.find_all(exp.Subquery))
        if not spec.semis:
            spec.where = where.this.sql()  # nada que extraer: el texto original, sin tocar
        else:
            spec.where = " AND ".join(p.sql() for p in restantes) if restantes else None
    group = node.args.get("group")
    if group is not None:
        spec.group_by = [g.sql() for g in group.expressions]
    having = node.args.get("having")
    if having is not None:
        spec.having = having.this.sql()
    order = node.args.get("order")
    if order is not None:
        spec.order_by = [(o.this.sql(), bool(o.args.get("desc"))) for o in order.expressions]
    spec.subqueries = sum(1 for _ in node.find_all(exp.Subquery)) > sin_extraer
    spec.windows = any(True for _ in node.find_all(exp.Window))
    return spec


def _branches(node: exp.Expression) -> tuple[list[exp.Select], bool]:
    """Ramas de una unión (aplanadas) y si son UNION ALL."""
    if isinstance(node, exp.Union):
        left, left_all = _branches(node.this)
        right, right_all = _branches(node.expression)
        return left + right, left_all and right_all and not node.args.get("distinct")
    if isinstance(node, exp.Select):
        return [node], True
    raise SqlNotSelect(type(node).__name__)


def build(sql: str) -> SqlTree:
    """Árbol de un SELECT o de un CREATE TABLE ... AS SELECT (texto ya normalizado)."""
    try:
        tree = sqlglot.parse_one(sql)
    except sqlglot.errors.ParseError as error:
        raise SqlParseError(str(error)) from error
    identifiers_portable = all(
        _PORTABLE_IDENTIFIER.fullmatch(identifier.name)
        for identifier in tree.find_all(exp.Identifier)
    )
    target = None
    body = tree
    if isinstance(tree, exp.Create):
        if tree.args.get("kind", "").upper() != "TABLE" or tree.expression is None:
            raise SqlNotSelect("CREATE que no es CREATE TABLE ... AS SELECT")
        target = _name(tree.this) if isinstance(tree.this, exp.Table) else tree.this.sql()
        body = tree.expression
    branches, union_all = _branches(body)
    return SqlTree(
        target,
        [_select(b) for b in branches],
        union_all=union_all,
        identifiers_portable=identifiers_portable,
    )
