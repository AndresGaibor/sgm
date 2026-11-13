"""Pasos del plan que el intérprete ejecuta uno a uno: entradas, base y ramas de cada operador.

Movido desde `interprete.py` sin cambio de comportamiento (decisión del dueño, hito 242m).
"""

from __future__ import annotations

import re

from sgm.ir.models import Operator, Plan
from sgm.migrar.interprete_agrupado import _agregar, _por_grupo
from sgm.migrar.interprete_filas import (
    _derecha,
    _filtrar,
    _mezclar,
    _ordenar,
    _proyectar,
    _renombrar,
    _seleccionar,
    _unicos,
    _unir,
    _validar_subconsulta_de_union,
)
from sgm.migrar.interprete_valores import NoSoportadoEnInterprete, _columna, _primero, _tabla

# Pasos que el plan también deja sueltos, sin el `map` que los envuelve.
_PASOS_SUELTOS = (
    "filter", "derive", "select", "rename", "sort", "dedup", "aggregate", "stateful_row"
)
def _entradas(
    plan: Plan, op: Operator, por_operador: dict, tablas: dict | None = None
) -> dict[str, list[dict]]:
    """Filas de cada predecesor, por la tabla que entrega."""
    por_tabla: dict[str, list[dict]] = {}
    for previo in plan.graph.predecessors(op.id):
        for nombre in _nombres(plan.graph.operator(previo)):
            por_tabla.setdefault(
                nombre, (tablas or {}).get(nombre, por_operador.get(previo, []))
            )
    return por_tabla


def _base(
    plan: Plan,
    op: Operator,
    derechos: set[str],
    por_operador: dict,
    tablas: dict | None = None,
) -> list[dict]:
    """La entrada que se acumula: el primer predecesor que no es el lado derecho de una unión."""
    previos = plan.graph.predecessors(op.id)
    for previo in previos:
        operador_previo = plan.graph.operator(previo)
        if operador_previo.kind == "map" and any(
            rama.get("continue") for rama in operador_previo.params.get("branches") or []
        ):
            return por_operador.get(previo, [])
        nombres = _nombres(operador_previo)
        if not nombres or not set(nombres) <= derechos:
            nombre = next((nombre for nombre in nombres if nombre in (tablas or {})), None)
            return (tablas or {}).get(nombre, por_operador.get(previo, []))
    return por_operador.get(previos[0], []) if previos else []


def _pasos(op: Operator, plan: Plan, por_operador: dict, tablas: dict | None = None) -> list[dict]:
    """Los pasos de un `map` —o el operador suelto— sobre las entradas, en el orden del plan."""
    pasos = op.params.get("steps")
    if not pasos and op.kind != "map":
        pasos = [{"kind": op.kind, "params": op.params}]
    pasos = pasos or []
    por_tabla = _entradas(plan, op, por_operador, tablas)
    derechos = {
        _derecha(paso.get("params") or {}) for paso in pasos if paso.get("kind") == "join"
    }
    actual = _base(plan, op, {d for d in derechos if d}, por_operador, tablas)
    entrada_declarada = _primero(op.params, "inputs")
    if entrada_declarada:
        actual = por_tabla.get(_tabla(entrada_declarada), actual)
    for paso in pasos:
        clase = str(paso.get("kind") or "")
        params = paso.get("params") or {}
        if clase == "join" and not params.get("keys") and params.get("by"):
            fuentes = [_tabla(s) for s in params.get("sources") or []]
            if len(fuentes) < 2 or any(f not in por_tabla for f in fuentes):
                raise NoSoportadoEnInterprete("join", "MERGE sin las tablas de sus fuentes")
            banderas = {
                _tabla(plan.graph.operator(p).params.get("dataset", "")): plan.graph.operator(
                    p
                ).params.get("in")
                for p in plan.graph.predecessors(op.id)
                if plan.graph.operator(p).kind == "read"
            }
            actual = _mezclar(
                [por_tabla[f] for f in fuentes], [banderas.get(f) for f in fuentes], params
            )
        elif clase == "join":
            _validar_subconsulta_de_union(params, actual, plan, por_operador, por_tabla)
            tabla = _derecha(params)
            if tabla not in por_tabla:
                raise NoSoportadoEnInterprete(
                    "join", f"no hay una entrada para la tabla '{tabla}'"
                )
            actual = _unir(actual, por_tabla[tabla], params)
        elif clase == "filter":
            actual = _filtrar(actual, str(params.get("expression") or ""), por_tabla)
        elif clase == "derive":
            asignaciones = _expandir_estrellas(params.get("assignments") or [], por_tabla)
            actual = _proyectar(
                actual, asignaciones, aditivo=params.get("modo") == "agrega"
            )
        elif clase == "select":
            actual = _seleccionar(actual, params)
        elif clase == "rename":
            actual = _renombrar(actual, params)
        elif clase == "sort":
            actual = _ordenar(actual, params)
        elif clase == "dedup":
            actual = _unicos(actual, params)
        elif clase == "aggregate":
            actual = _agregar(actual, params)
        elif clase == "stateful_row" and params.get("reason") == "by_group":
            actual = _por_grupo(actual, params)
        else:
            raise NoSoportadoEnInterprete(clase or "paso", "el intérprete no lo ejecuta")
    return actual


def _nombres(op: Operator) -> list[str]:
    """Conjuntos de `WORK` bajo los que queda el resultado del operador."""
    clases = (*_PASOS_SUELTOS, "read_file", "map", "join", "union", "split")
    if op.kind in clases:
        outputs = op.params.get("outputs") or []
        if op.kind == "split":
            outputs = op.params.get("targets") or (
                [op.params["target"]] if op.params.get("target") else []
            )
        if op.kind == "dedup":
            outputs = [*outputs, *(op.params.get("duplicate_outputs") or [])]
        return [_tabla(nombre) for nombre in outputs]
    if op.kind == "write_file":
        return [_tabla(nombre) for nombre in op.params.get("inputs") or []]
    if op.kind in ("read", "write"):
        return [_tabla(op.params.get("dataset", ""))]
    return []


def _ramas(
    op: Operator, filas: list[dict], tablas: dict[str, list[dict]] | None = None
) -> dict[str, list[dict]]:
    """Un `map` con ramas es un IF/THEN/ELSE que escribe en varias salidas: cada rama su filtro."""
    resultado = {}
    for rama in op.params.get("branches") or []:
        if rama.get("continue"):
            continue
        filas_rama = filas
        join_key = rama.get("joinKey")
        if join_key:
            if rama.get("rejectInnerJoin"):
                filas_rama = [fila for fila in filas if _columna(fila, str(join_key)) is None]
            elif rama.get("matched"):
                filas_rama = [fila for fila in filas if _columna(fila, str(join_key)) is not None]
        if rama.get("expression"):
            filas_rama = _filtrar(filas_rama, str(rama["expression"]), tablas)
        resultado[_tabla(rama.get("outputs", ["WORK.sin_nombre"])[0])] = filas_rama
    return resultado


def _expandir_estrellas(asignaciones: list[dict], por_tabla: dict[str, list[dict]]) -> list[dict]:
    """Expande `alias.*` solo si las filas disponibles demuestran su esquema."""
    resultado = []
    for asignacion in asignaciones:
        expresion = str(asignacion.get("expression") or "").strip()
        if not re.fullmatch(r"[\w.]+\.\*", expresion):
            resultado.append(asignacion)
            continue
        tabla = expresion[:-2].lower().split(".")[-1]
        filas = por_tabla.get(tabla)
        if not filas:
            raise NoSoportadoEnInterprete(
                "select", f"el esquema de la fuente '{tabla}' no está verificable"
            )
        for columna in filas[0]:
            resultado.append(
                {
                    "target": columna,
                    "expression": f"{tabla}.{columna}",
                    "origin": "columna",
                }
            )
    return resultado


