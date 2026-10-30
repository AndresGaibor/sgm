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
from dataclasses import dataclass, field

import sqlglot
from sqlglot import exp

# `sqlglot` avisa por el log cuando cae a un comando; aquí el resultado ya lo trata el lowering.
logging.getLogger("sqlglot").setLevel(logging.ERROR)


class SqlParseError(ValueError):
    """El texto no es SQL que `sqlglot` pueda leer."""


class SqlNotSelect(ValueError):
    """Sentencia de otro tipo (insert, delete, drop...) que no es una consulta."""


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


@dataclass
class Item:
    expression: str  # texto SQL de la expresión
    alias: str | None = None
    column: str | None = None  # si es solo una columna (sin función ni operador)
    star: bool = False  # `select *`


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
    subqueries: bool = False  # hay subconsultas: no se traducen todavía
    windows: bool = False  # hay funciones de ventana: no se traducen todavía


@dataclass
class SqlTree:
    target: str | None  # tabla que crea el CREATE TABLE AS, o None si es solo un SELECT
    selects: list[SelectSpec]  # una por rama de UNION; una sola si no hay unión
    union_all: bool = False  # las ramas se unen con UNION ALL (sin quitar duplicados)


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


def _equality(condition: exp.Expression) -> tuple[str, str] | None:
    """`a.x = b.y` entre dos columnas: (x, y). None en cualquier otro caso."""
    if isinstance(condition, exp.EQ) and isinstance(condition.left, exp.Column):
        if isinstance(condition.right, exp.Column):
            return condition.left.name, condition.right.name
    return None


def _join_keys(on: exp.Expression | None) -> tuple[list[tuple[str, str]], str | None]:
    """Pares de igualdad del ON, y el resto de condiciones como texto."""
    if on is None:
        return [], None
    keys: list[tuple[str, str]] = []
    rest: list[str] = []
    for part in on.flatten() if isinstance(on, exp.And) else [on]:
        pair = _equality(part)
        if pair is None or isinstance(part, exp.Or):
            rest.append(part.sql())
        else:
            keys.append(pair)
    return keys, (" AND ".join(rest) if rest else None)


def _join(join: exp.Join) -> JoinSpec:
    side = (join.args.get("side") or "").lower()
    kind = (join.args.get("kind") or "").lower()
    if side in ("left", "right", "full"):
        flavor = side
    elif kind == "cross" or (not join.args.get("on") and not side):
        flavor = "cross"
    else:
        flavor = "inner"
    keys, condition = _join_keys(join.args.get("on"))
    on = join.args.get("on")
    return JoinSpec(_source(join.this), flavor, keys, condition, on.sql() if on else None)


def _item(node: exp.Expression) -> Item:
    if isinstance(node, exp.Star):
        return Item("*", star=True)
    if isinstance(node, exp.Alias):
        inner = node.this
        column = inner.name if isinstance(inner, exp.Column) else None
        return Item(inner.sql(), alias=node.alias, column=column)
    column = node.name if isinstance(node, exp.Column) else None
    return Item(node.sql(), column=column)


def _select(node: exp.Select) -> SelectSpec:
    spec = SelectSpec()
    from_ = node.args.get("from_")
    if from_ is not None:
        spec.base = _source(from_.this)
    spec.joins = [_join(j) for j in node.args.get("joins") or []]
    spec.items = [_item(e) for e in node.expressions]
    spec.distinct = node.args.get("distinct") is not None
    where = node.args.get("where")
    if where is not None:
        spec.where = where.this.sql()
    group = node.args.get("group")
    if group is not None:
        spec.group_by = [g.sql() for g in group.expressions]
    having = node.args.get("having")
    if having is not None:
        spec.having = having.this.sql()
    order = node.args.get("order")
    if order is not None:
        spec.order_by = [(o.this.sql(), bool(o.args.get("desc"))) for o in order.expressions]
    spec.subqueries = any(True for _ in node.find_all(exp.Subquery))
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
    target = None
    body = tree
    if isinstance(tree, exp.Create):
        if tree.args.get("kind", "").upper() != "TABLE" or tree.expression is None:
            raise SqlNotSelect("CREATE que no es CREATE TABLE ... AS SELECT")
        target = _name(tree.this) if isinstance(tree.this, exp.Table) else tree.this.sql()
        body = tree.expression
    branches, union_all = _branches(body)
    return SqlTree(target, [_select(b) for b in branches], union_all=union_all)
