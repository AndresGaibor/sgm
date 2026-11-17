"""Preparación segura de subconsultas independientes usadas por IN en el anillo B."""

from __future__ import annotations

from collections.abc import Callable
from decimal import Decimal

from sqlglot import exp

from sgm.ir.models import Operator
from sgm.migrar import semantica
from sgm.migrar.interprete_subconsultas_orden import (  # noqa: F401 (reexportados)
    SubconsultaNoSoportada,
    _agregar_dependencias_versionadas,
    _expresiones_filtro,
    _fuentes,
    _intervalo_fuente,
    _subconsultas_de_join,
    orden_de_ejecucion,
)

Evaluar = Callable[[exp.Expression, dict], object]
Filtrar = Callable[[list[dict], str, dict | None], list[dict]]
Columna = Callable[[dict, str], object]
Nombres = Callable[[Operator], list[str]]
Parsear = Callable[[str], exp.Expression]


def _lista_inicial(expresion: exp.Expression):
    """Busca los IN de esta expresión sin entrar a la SELECT de otro IN."""
    if isinstance(expresion, exp.In) and expresion.args.get("query") is not None:
        yield expresion
        yield from _lista_inicial(expresion.this)
        for opcion in expresion.expressions:
            yield from _lista_inicial(opcion)
        return
    for hija in expresion.iter_expressions():
        yield from _lista_inicial(hija)


def _valores(
    consulta: exp.Expression,
    tablas: dict[str, list[dict]],
    *,
    filtrar: Filtrar,
    evaluar: Evaluar,
    columna: Columna,
) -> list[object]:
    select = consulta.this if isinstance(consulta, exp.Subquery) else consulta
    if not isinstance(select, exp.Select):
        raise SubconsultaNoSoportada("la consulta IN debe ser un SELECT")

    if select.find(exp.In) and any(
        isinstance(nodo, exp.In) and nodo.args.get("query") is not None
        for nodo in select.find_all(exp.In)
    ):
        raise SubconsultaNoSoportada("subconsulta anidada no soportada")

    clausulas_no_soportadas = (
        "distinct",
        "group",
        "having",
        "order",
        "limit",
        "offset",
        "qualify",
        "with",
        "windows",
    )
    if select.args.get("joins"):
        raise SubconsultaNoSoportada("IN requiere una sola fuente de tabla")
    if any(select.args.get(nombre) is not None for nombre in clausulas_no_soportadas):
        raise SubconsultaNoSoportada("cláusula de subconsulta no soportada")

    proyeccion = select.expressions
    if len(proyeccion) != 1:
        raise SubconsultaNoSoportada("IN requiere una sola columna proyectada")
    proyectada = proyeccion[0]
    if not isinstance(proyectada, exp.Column):
        raise SubconsultaNoSoportada(
            "proyección de subconsulta no soportada; requiere una columna simple"
        )

    desde = select.args.get("from_")
    fuente = desde.this if isinstance(desde, exp.From) else None
    if not isinstance(fuente, exp.Table):
        raise SubconsultaNoSoportada("IN requiere una sola fuente de tabla")
    nombre_fuente = fuente.name.lower()
    filas_fuente = tablas.get(nombre_fuente)
    if not filas_fuente:
        raise SubconsultaNoSoportada(
            f"la fuente '{nombre_fuente}' no está disponible con un esquema verificable"
        )

    alias = fuente.alias.lower() if fuente.alias else nombre_fuente
    calificadores = {alias, nombre_fuente}
    columnas = list(select.find_all(exp.Column))
    for referencia in columnas:
        calificador = referencia.table.lower()
        if calificador and calificador not in calificadores:
            raise SubconsultaNoSoportada(
                f"referencia correlacionada o alias externo no soportado: {referencia.sql()}"
            )
        nombre = referencia.name.lower()
        if any(not any(str(clave).lower() == nombre for clave in fila) for fila in filas_fuente):
            raise SubconsultaNoSoportada(
                f"columna '{nombre}' no verificable en la fuente '{nombre_fuente}'"
            )

    where = select.args.get("where")
    filas = (
        filtrar(filas_fuente, where.this.sql(), tablas)
        if isinstance(where, exp.Where)
        else filas_fuente
    )
    valores = [columna(fila, proyectada.name) for fila in filas]
    return valores


def _literal(valor: object) -> exp.Expression:
    if semantica.es_faltante(valor):
        return exp.Null()
    if isinstance(valor, str):
        return exp.Literal.string(valor)
    if isinstance(valor, (int, float, Decimal)) and not isinstance(valor, bool):
        return exp.Literal.number(str(valor))
    raise SubconsultaNoSoportada(f"tipo de valor no soportado en IN: {type(valor).__name__}")


def preparar(
    arbol: exp.Expression,
    filas: list[dict],
    tablas: dict[str, list[dict]] | None,
    *,
    filtrar: Filtrar,
    evaluar: Evaluar,
    columna: Columna,
) -> exp.Expression:
    """Reemplaza cada IN con SELECT independiente por su lista de literales validada."""
    nodos = list(_lista_inicial(arbol))
    if nodos and tablas is None:
        raise SubconsultaNoSoportada("IN con SELECT requiere el contexto de tablas")
    preparado = arbol.copy()
    reemplazos = list(_lista_inicial(preparado))

    for nodo in reemplazos:
        valores = _valores(
            nodo.args["query"],
            tablas or {},
            filtrar=filtrar,
            evaluar=evaluar,
            columna=columna,
        )
        if any(semantica.es_faltante(evaluar(nodo.this, fila)) for fila in filas):
            raise SubconsultaNoSoportada("el operando externo de IN contiene un valor faltante")
        presentes = [valor for valor in valores if not semantica.es_faltante(valor)]
        if valores and not presentes:
            raise SubconsultaNoSoportada("la columna de la subconsulta contiene un valor faltante")
        nodo.set("expressions", [_literal(valor) for valor in valores])
        nodo.set("query", None)

    return preparado
