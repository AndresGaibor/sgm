"""Funciones SQL portables: qué funciones de una expresión de PROC SQL pueden ir a una base.

La lista sale de `rules/sas/sql-functions.json`: solo cuentan las funciones con `status: portable`.
Una función que no aparece ahí (o que tiene `translated` o `sas_only`) hace que la expresión no sea
portable. La regla es conservadora: una función desconocida no se da por buena.

Las palabras clave de SQL (`case`) no son funciones y no se miran: el propio JSON lo indica.
`sqlglot` escribe algunas funciones con otro nombre (`SUBSTR` queda como `SUBSTRING`), por eso
hay un mapa de alias antes de comparar.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import sqlglot
from sqlglot import exp

ROOT_DIR = Path(__file__).resolve().parents[3]
SQL_FUNCTIONS_PATH = ROOT_DIR / "rules" / "sas" / "sql-functions.json"

KEYWORDS = frozenset({"case"})  # palabras clave de SQL que sqlglot modela como función
OPERATOR_NODES = (exp.Connector, exp.Not, exp.Paren)  # sqlglot los marca como Func; no lo son
ALIASES = {"substring": "substr"}  # nombre que da sqlglot -> nombre del JSON


def load_sql_portable(path: Path | None = None) -> frozenset[str]:
    """Nombres de funciones SQL portables (status `portable` en el JSON)."""
    source = path or SQL_FUNCTIONS_PATH
    data = json.loads(source.read_text(encoding="utf-8"))
    return frozenset(
        name for name, info in data["functions"].items() if info.get("status") == "portable"
    )


@lru_cache(maxsize=1)
def portable_names() -> frozenset[str]:
    return load_sql_portable()


def function_names(sql: str) -> list[str]:
    """Nombres (en minúsculas) de las funciones de una expresión SQL, anidadas incluidas.

    Lanza `sqlglot.errors.SqlglotError` si la expresión no se puede leer.
    """
    tree = sqlglot.parse_one(f"SELECT {sql}")
    names: list[str] = []
    for node in tree.find_all(exp.Func):
        if isinstance(node.parent, exp.Case):
            continue  # cada WHEN de un CASE se modela como If: forma parte de la palabra clave
        if isinstance(node, OPERATOR_NODES):
            continue  # AND, OR, NOT y paréntesis: operadores, no funciones
        name = node.name.lower() if isinstance(node, exp.Anonymous) else node.sql_name().lower()
        name = ALIASES.get(name, name)
        if name not in KEYWORDS:
            names.append(name)
    return names


def unportable_functions(sql: str) -> list[str]:
    """Funciones de la expresión que no son portables. Lista vacía si todas lo son."""
    portable = portable_names()
    return [name for name in function_names(sql) if name not in portable]


def is_portable(sql: str) -> bool:
    """La expresión se puede leer y todas sus funciones son portables."""
    try:
        return not unportable_functions(sql)
    except sqlglot.errors.SqlglotError:
        return False
