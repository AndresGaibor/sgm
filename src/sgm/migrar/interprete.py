"""Intérprete del plan: ejecuta los operadores sobre filas y devuelve las tablas de `WORK`.

Es el anillo B de la verificación: prueba que el plan —y por lo tanto el Job que sale de él— calcula
lo que el SAS dice, sin abrir Talend Studio. Sirve para dos cosas que ninguna otra pieza cubre: los
casos donde Studio no está disponible, y el contraste con `esperado/` de todo el corpus.

Soporta lo que la primera rebanada vertical traduce: `read_file`, `write_file`, `map` con pasos
`join` (inner y left), `filter` y `derive`, más los `read` y `write` que solo nombran un
conjunto. Lo demás **no se ignora**: lanza `NoSoportadoEnInterprete` con el operador o el paso
que no entiende. Un intérprete que se salta un `sort` en silencio daría filas correctas en el
conjunto y falsas en el orden, y la prueba pasaría sin probar nada.

Las expresiones se leen con `sqlglot`, que ya es dependencia del proyecto para el SQL, y se evalúan
con la semántica de `sgm.migrar.semantica`. Las columnas se resuelven por nombre y sin distinguir
mayúsculas: el calificador (`ventas.monto`) se ignora, así que en un auto-unión las dos tablas
comparten nombre de columna y la última en entrar gana. Es una limitación conocida, anotada en
`PROGRESS.md`, no un descuido: el plan tampoco distingue los alias de una auto-unión.
"""

from __future__ import annotations

import copy
from contextlib import nullcontext

from sgm.ir.desplegar import plan_desplegado
from sgm.ir.models import Operator, Plan
from sgm.migrar.interprete_conjuntos import conjunto
from sgm.migrar.interprete_esquema import output_types
from sgm.migrar.interprete_filas import _clave, _filtrar, _llaves, _proyectar, _unicos
from sgm.migrar.interprete_formatos_usuario import user_format_types, user_formats
from sgm.migrar.interprete_pasos import _PASOS_SUELTOS, _nombres, _pasos, _ramas
from sgm.migrar.interprete_subconsultas import (
    SubconsultaNoSoportada,
    orden_de_ejecucion,
)

# Operadores que el intérprete sabe ejecutar; el resto detiene la ejecución con su nombre.
SOPORTADOS = frozenset(
    {"read", "read_file", "write", "write_file", "map", "join", "filter", "derive"}
)


from sgm.migrar.interprete_agregados import (  # noqa: E402
    AgregadoNoSoportado,
    agregar,
)
from sgm.migrar.interprete_funciones import _funcion  # noqa: E402
from sgm.migrar.interprete_paso_directo import leer as _leer_paso_directo  # noqa: E402
from sgm.migrar.interprete_valores import (  # noqa: E402 - movido, ver interprete_valores.py
    NoSoportadoEnInterprete,
    _arbol,
    _aritmetica,
    _columna,
    _primero,
    _tabla,
    _valor,
)


def _agregar(filas: list[dict], params: dict) -> list[dict]:
    """Adaptador compatible con el intérprete modular y su excepción pública."""
    try:
        return agregar(
            filas,
            params,
            parsear=_arbol,
            evaluar=_valor,
            columna=_columna,
            clave=_clave,
        )
    except AgregadoNoSoportado as error:
        raise NoSoportadoEnInterprete("aggregate", str(error)) from error


def _apilar(op: Operator, plan: Plan, tablas: dict, por_operador: dict) -> list[dict]:
    """`SET a b` o `UNION ALL`: las filas de cada entrada una tras otra, juntas por nombre.

    Una columna que una entrada no tiene queda faltante en sus filas, como en SAS. Sin `ALL`
    (`UNION` de PROC SQL) se quitan además las filas repetidas.
    """
    fuentes = [_tabla(nombre) for nombre in op.params.get("sources") or []]
    if fuentes:
        entradas = [tablas.get(nombre, []) for nombre in fuentes]
    else:
        entradas = [por_operador.get(previo, []) for previo in plan.graph.predecessors(op.id)]
    columnas: list[str] = []
    declared = op.params.get("columns_by_branch") or []
    if op.params.get("outer_union_corr"):
        shared_types: dict[str, str] = {}
        for prev, names in zip(plan.graph.predecessors(op.id), declared, strict=True):
            types = output_types(plan.graph, plan.graph.operator(prev))
            for name in names if names is not None else types:
                column = name.casefold()
                if (known := types.get(column)) is None:
                    continue
                previous = shared_types.setdefault(column, known)
                if previous != known:
                    raise NoSoportadoEnInterprete(
                        "union",
                        f"Pendiente: P-UNION-TIPO-CONFLICTO; {column}: {previous} y {known}",
                    )
        entradas = [
            [{c.casefold(): v for c, v in fila.items()} for fila in rows] for rows in entradas
        ]
    for index, filas in enumerate(entradas):
        if declared:
            names = declared[index]
            if names is None and not filas:
                raise NoSoportadoEnInterprete(
                    "union", "OUTER UNION CORR con SELECT * vacío sin esquema demostrado"
                )
            columnas += [c for c in names or [] if c not in columnas]
        for fila in filas:
            columnas += [c for c in fila if c not in columnas]
    if op.params.get("op") in ("except", "intersect"):
        return conjunto(str(op.params["op"]), entradas)
    apiladas = [{c: fila.get(c) for c in columnas} for filas in entradas for fila in filas]
    if op.params.get("all", True):
        return apiladas
    vistas: set[tuple] = set()
    unicas = []
    for fila in apiladas:
        clave = tuple(_clave(valor) for valor in fila.values())
        if clave not in vistas:
            vistas.add(clave)
            unicas.append(fila)
    return unicas


def _ejecutar(
    op: Operator, plan: Plan, tablas: dict, por_operador: dict
) -> tuple[list[dict], dict[str, list[dict]]]:
    """Filas del operador y las tablas que deja, por nombre sin biblioteca.

    Las dos cosas van juntas porque un operador intermedio —un `join` que alimenta un `map`— no
    tiene tabla propia: sus filas solo se pueden encontrar por su id, y el `map` de detrás las pide
    así.
    """
    # Una sentencia sin traducción ignorada daría un resultado falso sin avisar: se detiene. El
    # DATA step ejecuta cada sentencia en orden (lrcon, p. 500); no se puede saltar ninguna.
    sin_traducir = op.params.get("untranslated") or []
    if sin_traducir:
        raise NoSoportadoEnInterprete(op.kind, f"sentencia sin traducción: {sin_traducir[0]}")
    condicional = op.params.get("conditional")
    if op.kind == "derive" and condicional and not op.params.get("assignments"):
        raise NoSoportadoEnInterprete(op.kind, f"asignación condicional sin partes: {condicional}")
    if op.kind == "unsupported" and op.params.get("reason") == "CONFIGURACION":
        return [], {}  # `%LET`, `OPTIONS`: ya sustituidos en el programa, no producen filas
    if op.kind == "read_file" and str(op.params.get("dbms") or "").casefold() == "xls":
        raise NoSoportadoEnInterprete("xls", "formato binario 97-2003: el intérprete no lo lee")
    if (
        op.kind == "read"
        and (op.placement or "").startswith("db:")
        and op.params.get("sql")
    ):
        filas = _leer_paso_directo(op, tablas)
        propias = {
            _tabla(str(nombre)): filas for nombre in op.params.get("outputs") or []
        }
        return filas, propias
    if op.kind in ("read", "read_file"):
        nombre = (
            _tabla(op.params.get("dataset", ""))
            if op.kind == "read"
            else _tabla(_primero(op.params, "outputs"))
        )
        if nombre in tablas:
            return tablas[nombre], {nombre: tablas[nombre]}
        if (
            op.kind == "read_file"
            and str(op.params.get("dbms") or "").casefold() == "xlsx"
        ):
            raise NoSoportadoEnInterprete(
                "xlsx", "el archivo no se cargó desde las entradas locales del caso"
            )
        previos = plan.graph.predecessors(op.id)
        filas = por_operador.get(previos[0], []) if previos else []
        return filas, {nombre: filas}
    if op.kind in ("write", "write_file"):
        previos = plan.graph.predecessors(op.id)
        if not previos:
            if op.kind == "write_file":
                nombre = _tabla(_primero(op.params, "inputs"))
                if nombre in tablas:
                    filas = tablas[nombre]
                    return filas, {nombre: filas}
            raise NoSoportadoEnInterprete(op.kind, "sin operador de origen")
        filas = por_operador.get(previos[0], [])
        return filas, {nombre: tablas.get(nombre, filas) for nombre in _nombres(op)}
    if op.kind == "union":
        filas = _apilar(op, plan, tablas, por_operador)
        return filas, {nombre: filas for nombre in _nombres(op)}
    if op.kind == "dedup" and op.params.get("duplicate_outputs"):
        previos = plan.graph.predecessors(op.id)
        entrada = por_operador.get(previos[0], []) if previos else []
        filas = _unicos(entrada, op.params)
        llaves = _llaves(entrada, op.params)
        vistas: set[tuple] = set()
        duplicadas = []
        for fila in entrada:
            clave = tuple(_clave(_columna(fila, nombre)) for nombre in llaves)
            if clave in vistas:
                duplicadas.append(fila)
            else:
                vistas.add(clave)
        propias = {_tabla(nombre): filas for nombre in op.params.get("outputs") or []}
        propias.update(
            {_tabla(nombre): duplicadas for nombre in op.params.get("duplicate_outputs") or []}
        )
        return filas, propias
    if op.kind in ("map", "join", *_PASOS_SUELTOS):
        previos = plan.graph.predecessors(op.id)
        if op.kind == "map" and op.params.get("branches"):
            ejecutable = op
            rechazo_inner = any(
                rama.get("rejectInnerJoin") for rama in op.params["branches"]
            )
            derivaciones = []
            if any(rama.get("rejectInnerJoin") for rama in op.params["branches"]):
                ejecutable = copy.deepcopy(op)
                derivaciones = [
                    paso
                    for paso in ejecutable.params.get("steps") or []
                    if paso.get("kind") == "derive"
                ]
                ejecutable.params["steps"] = [
                    paso
                    for paso in ejecutable.params.get("steps") or []
                    if paso.get("kind") != "derive"
                ]
                for paso in ejecutable.params.get("steps") or []:
                    if paso.get("kind") == "join":
                        paso["params"]["join_type"] = "left"
            filas = _pasos(ejecutable, plan, por_operador, tablas) if op.params.get("steps") else (
                por_operador.get(previos[0], []) if previos else []
            )
            propias = _ramas(op, filas, tablas)
            if rechazo_inner and derivaciones:
                asignaciones = derivaciones[-1].get("params", {}).get("assignments") or []
                propias = {
                    nombre: _proyectar(rama, asignaciones, aditivo=False)
                    for nombre, rama in propias.items()
                }
            return filas, propias
        filas = _pasos(op, plan, por_operador, tablas)
        return filas, {nombre: filas for nombre in _nombres(op)}
    if op.kind == "split":
        previos = plan.graph.predecessors(op.id)
        filas_entrada = por_operador.get(previos[0], []) if previos else []
        condicion = str(op.params.get("condition") or "").strip()
        if condicion:
            salida = _filtrar(filas_entrada, condicion, tablas)
        elif op.params.get("branch") == "else" and previos:
            anterior = plan.graph.operator(previos[0])
            condicion_anterior = str(anterior.params.get("condition") or "").strip()
            salida = (
                [
                    fila
                    for fila in filas_entrada
                    if not _filtrar([fila], condicion_anterior, tablas)
                ]
                if anterior.kind == "split" and condicion_anterior
                else filas_entrada
            )
        else:
            salida = filas_entrada
        return filas_entrada, {nombre: salida for nombre in _nombres(op)}
    raise NoSoportadoEnInterprete(op.kind, "el intérprete no lo ejecuta")


def ejecutar_plan(
    plan: Plan, entradas: dict[str, list[dict[str, str | None]]]
) -> dict[str, list[dict[str, str | None]]]:
    """Ejecuta el plan con sus formatos, sin contaminar otras ejecuciones."""
    with user_formats(plan.formatos):
        return _execute_plan(plan, entradas)


def _execute_plan(
    plan: Plan, entradas: dict[str, list[dict[str, str | None]]]
) -> dict[str, list[dict[str, str | None]]]:
    """Ejecuta el plan y devuelve las tablas de `WORK` que produce, por nombre sin biblioteca.

    `entradas` trae las filas de las tablas que el programa lee, con el nombre de la tabla como
    clave (`WORK.clientes`, `clientes` o `CLIENTES` dan igual). Las columnas de cada fila se buscan
    sin distinguir mayúsculas.
    """
    plan, _ = plan_desplegado(plan)  # una plantilla se ejecuta instancia por instancia
    tablas: dict[str, list[dict]] = {
        _tabla(nombre): [{str(c).lower(): v for c, v in fila.items()} for fila in filas]
        for nombre, filas in entradas.items()
    }
    por_operador: dict[str, list[dict]] = {}
    try:
        orden = orden_de_ejecucion(plan, nombres=_nombres, parsear=_arbol)
    except SubconsultaNoSoportada as error:
        raise NoSoportadoEnInterprete("subconsulta", str(error)) from error
    for op_id in orden:
        op = plan.graph.operator(op_id)
        scope = nullcontext()
        if plan.formatos:
            parents = plan.graph.predecessors(op_id)
            types = (
                output_types(plan.graph, plan.graph.operator(parents[0]))
                if len(parents) == 1 else {}
            )
            scope = user_format_types(types)
        with scope:
            filas, propias = _ejecutar(op, plan, tablas, por_operador)
        por_operador[op.id] = filas
        tablas.update(propias)
    return tablas


__all__ = [
    "SOPORTADOS",
    "NoSoportadoEnInterprete",
    "ejecutar_plan",
    "_agregar",
    "_arbol",
    "_aritmetica",
    "_funcion",
    "_valor",
]
