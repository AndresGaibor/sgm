"""Cruces de SQL que no son un JOIN de tabla: subconsultas `IN` / `NOT IN` y parámetros de `unir`.

Extraído de `lower_sql_flow.py` (B-6) sin cambio de comportamiento.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sgm.frontend.sql_normalize import NormalizedSql
from sgm.ir import operadores
from sgm.ir.lower_sql_texto import _calificar, _column, _restore, _tablas
from sgm.ir.models import Operator
from sgm.ir.pasos import paso as _paso
from sgm.ir.sql_tree import SemiSpec, Source

if TYPE_CHECKING:  # solo para anotar
    from sgm.ir.lower_sql_flow import _Chain

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
    source_read = chain.read(sub.base)
    actual = source_read
    if sub.where:
        filtro = _restore(_column(sub.where, alias_sub), normalized)
        actual = _paso(
            chain, "filter", {"expression": filtro}, lambda: operadores.filtrar("_", filtro), actual
        )
    leida = _calificar(_restore(semi.key, normalized), tablas_sub)
    proyeccion = [{"target": clave, "expression": leida, "origin": "columna"}]
    actual = _paso(
        chain,
        "derive",
        {"assignments": proyeccion},
        lambda: operadores.calcular("_", proyeccion),
        actual,
    )
    actual = _paso(
        chain,
        "dedup",
        {"by": [clave], "keep": "first", "outputs": [tabla]},
        lambda: operadores.deduplicar("_", [clave], "first", [tabla]),
        actual,
    )
    derecha = chain.read(Source(tabla))
    chain.b.link(actual, derecha)
    izquierda = _calificar(_restore(semi.column, normalized), tablas)
    params = _params_de_union(
        "left" if semi.negate else "inner",
        [[izquierda, f"{tabla.split('.')[-1].lower()}.{clave}"]],
        [],
        None,
        legado={
            "by": [izquierda.split(".")[-1]],
            "keys": [[izquierda, f"{tabla.split('.')[-1].lower()}.{clave}"]],
            "join_type": "left" if semi.negate else "inner",
            "sources": [],
            "condition": None,
        },
    )
    params["interpreter_subquery"] = {
        "expression": _restore(semi.expression, normalized),
        "source_read": source_read.id,
    }
    cruce = chain.b.op("join", params, chain.ev)
    chain.b.link(current, cruce)
    chain.b.link(derecha, cruce)
    if not semi.negate:
        return cruce
    return _paso(
        chain,
        "filter",
        {"expression": f"missing({clave})"},
        lambda: operadores.filtrar("_", f"missing({clave})"),
        cruce,
    )


def _params_de_union(
    join_type: str,
    keys: list[list[str]],
    sources: list[str],
    condition: str | None,
    *,
    legado: dict,
) -> dict:
    """Parámetros de un JOIN de SQL, validados por el constructor `unir` (ir/operadores.py).

    Si el constructor rechaza la unión (tipo desconocido, sin llaves), se devuelve la forma anterior
    `legado`, para que el operador salga como antes y no se pierda el caso.
    """
    try:
        pares = [(izquierda, derecha) for izquierda, derecha in keys]
        return operadores.unir("_", join_type, pares, sources, condition).params
    except ValueError:
        return legado
