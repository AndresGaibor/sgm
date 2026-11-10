"""Fusión de dos pasos encadenados por una tabla intermedia en un solo `map` (un solo `tMap`).

El SAS escribe `WORK.a` en un paso y la lee en el siguiente. Si nadie más la lee ni se exporta, esa
tabla no es un dato del proceso: es la forma que tiene SAS de encadenar dos sentencias. Una persona
que diseña el Job en Talend hace las dos cosas en el mismo `tMap`: junta los cruces como lookups,
une los filtros y escribe cada columna de la salida con la expresión completa.

La fusión solo se hace cuando se puede demostrar que el resultado es el mismo. Si no, `fundir`
devuelve el motivo y el plan queda como estaba:

* los dos pasos tienen la forma cruces, filtros y como mucho una proyección al final, sin `modo:
  agrega`, `KEEP`/`DROP`, `RENAME` ni ramas;
* la tabla intermedia la lee un solo paso, una sola vez, y no es salida del programa;
* cada columna que el segundo paso nombra se puede atribuir sin duda al primero o a otra entrada;
* si la intermedia entra por el lado de consulta de un cruce, el primer paso es una proyección
  pura: un filtro suyo, aplicado después de un cruce externo, quitaría filas que el SAS conserva.
"""

from __future__ import annotations

import copy

from sgm.ir.models import Edge, Operator, Plan
from sgm.optimizar.forma import (
    FUSIONABLES,
    NoFusionable,
    forma_de,
    nombre_tabla,
    parte_de_paso,
)
from sgm.optimizar.reescribir import (
    primero_de,
    proyeccion_fundida,
    reescribir,
    union_reescrita,
)


def _pasos_fundidos(plan: Plan, a: Operator, b: Operator, tabla: str | None) -> list[dict]:
    forma_a, forma_b = forma_de(a), forma_de(b)
    if tabla is None:
        # Un cruce suelto que alimenta al paso siguiente: este ya nombra las tablas originales.
        if forma_a.filtros or forma_a.proyeccion:
            raise NoFusionable("un paso sin tabla de salida que filtra o proyecta")
        return [*forma_a.uniones, *forma_b.uniones, *forma_b.filtros] + (
            [forma_b.proyeccion] if forma_b.proyeccion else []
        )
    primero = primero_de(plan, a, forma_a, tabla)
    cruza = bool(forma_b.uniones)
    parte_de = parte_de_paso(plan, b, forma_b)
    if nombre_tabla(parte_de) == tabla:
        parte_de = primero.principal
    elif forma_a.uniones or forma_a.filtros:
        raise NoFusionable("la intermedia entra como consulta y el paso anterior filtra o cruza")
    uniones = [*forma_a.uniones, *(union_reescrita(union, primero) for union in forma_b.uniones)]
    if uniones and not (uniones[0]["params"].get("sources")):
        uniones[0] = copy.deepcopy(uniones[0])
        uniones[0]["params"]["sources"] = [parte_de]
    filtros = list(forma_a.filtros)
    for filtro in forma_b.filtros:
        nuevo = copy.deepcopy(filtro)
        nuevo["params"]["expression"] = reescribir(
            str(filtro["params"].get("expression") or ""), primero, cruza
        )
        filtros.append(nuevo)
    salidas = b.params.get("outputs") or []
    ultima = proyeccion_fundida(forma_b, primero, forma_a, salidas)
    return [*uniones, *filtros] + ([ultima] if ultima else [])


def lecturas_por_tabla(plan: Plan) -> dict[str, set[str]]:
    """Tabla -> ids de los `read` que la leen. Se calcula una vez por pasada, no por operador."""
    indice: dict[str, set[str]] = {}
    for op in plan.graph.operators():
        if op.kind == "read":
            indice.setdefault(nombre_tabla(op.params.get("dataset")), set()).add(op.id)
    return indice


def _consumo(
    plan: Plan, a: Operator, tabla: str | None, lecturas_de: dict[str, set[str]]
) -> tuple[str, list[str]]:
    """El único operador que consume al primero y los `read` de la intermedia que hay en medio."""
    grafo = plan.graph
    consumidores: list[str] = []
    lecturas: list[str] = []
    for siguiente in dict.fromkeys(grafo.successors(a.id)):
        op = grafo.operator(siguiente)
        if op.kind == "read" and tabla and nombre_tabla(op.params.get("dataset")) == tabla:
            lecturas.append(siguiente)
            consumidores += grafo.successors(siguiente)
        else:
            consumidores.append(siguiente)
    unicos = list(dict.fromkeys(consumidores))
    if len(unicos) != 1 or len(lecturas) > 1:
        raise NoFusionable("la tabla intermedia la lee más de un paso, o ninguno")
    if tabla:
        otras = lecturas_de.get(tabla, set()) - set(lecturas)
        if otras or tabla in {nombre_tabla(f) for f in plan.fronteras}:
            raise NoFusionable("la tabla intermedia se usa fuera de este paso")
    return unicos[0], lecturas


def _aristas(plan: Plan, origen: str, destino: str) -> list[Edge]:
    return [e for e in plan.graph.in_edges(destino) if e.src == origen]


def fundir(
    plan: Plan, a_id: str, lecturas_de: dict[str, set[str]]
) -> tuple[str, list[str], str | None]:
    """Funde el operador `a_id` con su único consumidor, en el plan.

    Devuelve el id del operador que queda, los ids que absorbió y la tabla intermedia que ya no
    existe. Lanza `NoFusionable` sin haber tocado el plan.
    """
    grafo = plan.graph
    a = grafo.operator(a_id)
    salidas = a.params.get("outputs") or []
    if len(salidas) > 1:
        raise NoFusionable("el paso escribe más de una tabla")
    tabla = nombre_tabla(salidas[0]) if salidas else None
    if tabla is None and a.kind != "join":
        raise NoFusionable("el paso no nombra su salida")
    b_id, lecturas = _consumo(plan, a, tabla, lecturas_de)
    b = grafo.operator(b_id)
    pasos = _pasos_fundidos(plan, a, b, tabla)
    # A partir de aquí no falla nada: se cambia el plan.
    quitados = {a_id, *lecturas}
    # Las entradas del primero ocupan el lugar que tenía la intermedia entre las del segundo.
    nuevas: list[Edge] = []
    puesta = False
    for previo in grafo.predecessors(b_id):
        if previo not in quitados:
            nuevas += _aristas(plan, previo, b_id)
        elif not puesta:
            puesta = True
            for origen in grafo.predecessors(a_id):
                nuevas += _aristas(plan, origen, a_id)
    b.kind = "map"
    b.params = {"steps": pasos, "outputs": list(b.params.get("outputs") or [])}
    b.inherit_expression_evidence(a)
    b.evidence += [ev for ev in a.evidence if ev not in b.evidence]
    grafo.rewire_inputs(b_id, [Edge(e.src, b_id, e.dataset, e.materialize) for e in nuevas])
    for op_id in quitados:
        grafo.remove_operator(op_id)
    if tabla:
        lecturas_de.get(tabla, set()).difference_update(lecturas)
    return b_id, sorted(quitados), tabla


__all__ = ["FUSIONABLES", "NoFusionable", "fundir", "lecturas_por_tabla"]
