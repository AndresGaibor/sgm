"""Subconsulta escalar no correlacionada del WHERE en el intérprete del anillo B (plan C, C-8).

Forma soportada: `(SELECT AGREGADO(columna | *) FROM tabla [WHERE ...])`, con una sola tabla, sin
JOIN, GROUP BY, HAVING, ORDER BY ni DISTINCT. Lo que no encaja se rechaza.
Un agregado sin filas o sin valores presentes es un faltante (sqlproc, p. 83 y 84).
"""

from __future__ import annotations

from collections.abc import Callable
from decimal import Decimal, InvalidOperation

from sqlglot import exp

from sgm.migrar import semantica

Filtrar = Callable[[list[dict], str, dict | None], list[dict]]
Evaluar = Callable[[exp.Expression, dict], object]
Columna = Callable[[dict, str], object]

_FUNCIONES = {"avg", "sum", "min", "max", "count"}
_CLAUSULAS_NO_SOPORTADAS = ("distinct", "group", "having", "order", "limit", "offset", "joins")


class SubconsultaEscalarNoSoportada(ValueError):
    """Forma de subconsulta escalar que el intérprete no puede calcular con seguridad."""


def _decimal(valor: object) -> Decimal | None:
    if semantica.es_faltante(valor):
        return None
    try:
        return Decimal(str(valor).strip())
    except InvalidOperation as error:
        mensaje = f"valor no numérico en la subconsulta: {valor!r}"
        raise SubconsultaEscalarNoSoportada(mensaje) from error


def escalar(
    consulta: exp.Expression,
    tablas: dict[str, list[dict]],
    *,
    filtrar: Filtrar,
    evaluar: Evaluar,
    columna: Columna,
) -> object:
    """Valor de la subconsulta escalar: un número, un faltante (None) o un conteo entero."""
    select = consulta.this if isinstance(consulta, exp.Subquery) else consulta
    if not isinstance(select, exp.Select):
        raise SubconsultaEscalarNoSoportada("la subconsulta escalar debe ser un SELECT")
    if any(select.args.get(nombre) is not None for nombre in _CLAUSULAS_NO_SOPORTADAS):
        raise SubconsultaEscalarNoSoportada("cláusula de subconsulta escalar no soportada")
    proyeccion = select.expressions
    if len(proyeccion) != 1 or not isinstance(proyeccion[0], exp.AggFunc):
        raise SubconsultaEscalarNoSoportada("la subconsulta escalar debe devolver un agregado")
    agregado = proyeccion[0]
    funcion = agregado.key.lower()
    if funcion not in _FUNCIONES:
        raise SubconsultaEscalarNoSoportada(f"agregado no soportado en subconsulta: {funcion}")

    desde = select.args.get("from_")
    fuente = desde.this if isinstance(desde, exp.From) else None
    if not isinstance(fuente, exp.Table):
        raise SubconsultaEscalarNoSoportada("la subconsulta escalar requiere una sola tabla")
    nombre = fuente.name.lower()
    filas_fuente = tablas.get(nombre)
    if not filas_fuente:
        raise SubconsultaEscalarNoSoportada(f"la fuente '{nombre}' no está disponible")
    alias = fuente.alias.lower() if fuente.alias else nombre
    where = select.args.get("where")
    if fuente.alias and isinstance(where, exp.Where):
        # Con alias, la subconsulta se escribió calificada. Una columna sin calificar en su WHERE
        # puede ser externa (el lowering quitó su alias): no se supone que no correlacione.
        if any(not columna_sql.table for columna_sql in where.find_all(exp.Column)):
            raise SubconsultaEscalarNoSoportada(
                "WHERE sin calificar en subconsulta con alias: posible correlación"
            )
    for referencia in select.find_all(exp.Column):
        if referencia.table and referencia.table.lower() not in {alias, nombre}:
            raise SubconsultaEscalarNoSoportada(
                f"referencia correlacionada no soportada: {referencia.sql()}"
            )

    if isinstance(where, exp.Where):
        filas = filtrar(filas_fuente, where.this.sql(), tablas)
    else:
        filas = filas_fuente

    argumento = agregado.this
    if isinstance(argumento, exp.Star) or argumento is None:
        if funcion != "count":
            raise SubconsultaEscalarNoSoportada(f"{funcion}(*) no es válido")
        return len(filas)
    if not isinstance(argumento, exp.Column):
        raise SubconsultaEscalarNoSoportada("el agregado debe tomar una columna simple")
    valores = [evaluar(argumento, fila) for fila in filas]
    presentes = [valor for valor in valores if not semantica.es_faltante(valor)]
    if funcion == "count":
        return len(presentes)
    numeros = [_decimal(valor) for valor in presentes]
    if not numeros:
        return None
    if funcion == "sum":
        return sum(numeros, Decimal(0))
    if funcion == "avg":
        return sum(numeros, Decimal(0)) / len(numeros)
    if funcion == "min":
        return min(numeros)
    return max(numeros)
