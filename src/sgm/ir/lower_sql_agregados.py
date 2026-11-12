"""Agregados de SQL (GROUP BY, funciones de agregado, HAVING) como operadores del plan lógico.

Extraído de `lower_sql_flow.py` (B-6) sin cambio de comportamiento. El paso `aggregate` sale de
`operadores.agregar`; si rechaza los datos, va la forma legado (`ir/pasos.py`).
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from sgm.frontend.sql_normalize import NormalizedSql
from sgm.ir import operadores, sql_semantics
from sgm.ir.lower_sql_texto import (
    _AGGREGATE,
    _SIMPLE_COLUMN,
    _calificar,
    _column,
    _null_tests,
    _plain_items,
    _restore,
    _target_name,
)
from sgm.ir.models import Operator
from sgm.ir.pasos import paso as _paso
from sgm.ir.sql_tree import Item, SelectSpec

if TYPE_CHECKING:  # solo para anotar
    from sgm.ir.lower_sql_flow import _Chain

def _group_outputs(spec: SelectSpec, aliases: set[str]) -> tuple[list[dict], list[str]]:
    """Columnas simples de GROUP BY seleccionadas y columnas que requieren remezcla."""
    group_names = {
        match.group(1).lower()
        for group in spec.group_by
        if (match := _SIMPLE_COLUMN.fullmatch(_column(group, aliases).strip()))
    }
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


def _agregado(
    chain: _Chain, params: dict, previous: Operator, status: str = "soportado"
) -> Operator:
    """Paso `aggregate` por `operadores.agregar`; si rechaza los datos, va la forma legado."""
    return _paso(
        chain,
        "aggregate",
        params,
        lambda: operadores.agregar(
            "_",
            params["group_by"],
            params["aggregations"],
            pendiente=params.get("pendiente"),
            group_outputs=params.get("group_outputs"),
            output_order=params.get("output_order"),
            evidence=[chain.ev],
        ),
        previous,
        status=status,
    )


def lower_agregado(
    spec: SelectSpec,
    chain: _Chain,
    current: Operator,
    aliases: set[str],
    tablas: dict[str, str],
    normalized: NormalizedSql,
    aggregates: list[Item],
) -> tuple[Operator, list[tuple[str, bool]]]:
    """GROUP BY y agregados de una rama: agregado, filtro del HAVING y `derive` de las expresiones
    sobre agregados. Devuelve el último operador y el orden de `ORDER BY` ya resuelto.

    Extraído de `_branch` (B-6), sin cambios de comportamiento.
    Sin GROUP BY ni agregados no hace nada.
    """
    aggregate_order, remezcla_order = _aggregate_order_by(spec, aliases)
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
            current = _paso(
                chain,
                "derive",
                {"assignments": leidas},
                lambda: operadores.calcular("_", leidas),
                current,
            )
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
            "output_order": [
                str(it.alias or it.column or it.expression).lower()
                for it in spec.items
                if not it.star
            ],
        }
        if spec.group_by:
            group_outputs, remezcla = _group_outputs(spec, aliases)
            params["group_outputs"] = group_outputs
            remezcla.extend(remezcla_order)
            if remezcla:
                params["pendiente"] = remezcla
        if compuestos:
            params["output_order"] = [
                *[str(item["alias"]).lower() for item in params.get("group_outputs", [])],
                *[str(item["alias"]).lower() for item in params["aggregations"]],
            ]
        plain = _plain_items(spec) if not spec.group_by else []
        if params.get("pendiente") or (
            plain and sql_semantics.tratamiento(sql_semantics.AGREGADO) == "pendiente"
        ):
            # SAS remezcla las columnas sin agregar en cada fila: no hay SQL equivalente probado.
            params.setdefault("pendiente", plain)
            label = sql_semantics.reglas()[sql_semantics.AGREGADO].etiqueta
            detalle = ", ".join(params["pendiente"])
            note = f"{label}: columnas sin agregar {detalle}; pendiente de decidir"
            current = _agregado(chain, params, current, status="parcial")
            current.notes.append(note)
        else:
            current = _agregado(chain, params, current)
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
        current = _paso(
            chain,
            "derive",
            {"assignments": salida},
            lambda: operadores.calcular("_", salida),
            current,
        )
    return current, aggregate_order
