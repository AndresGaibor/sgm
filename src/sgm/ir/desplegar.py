"""Despliegue de las plantillas: cada `iterate` vuelve a ser los operadores que sustituyó.

La pasada 7 (`p07_templates`) recoge en un `iterate` los bloques que se repiten con otros nombres,
por ejemplo una macro llamada dos veces con productos distintos. Un `iterate` solo se puede escribir
como Job hijo (`tRunJob`) cuando el emisor sabe pasar los datos entre Jobs; mientras no sea así,
perder el bloque entero sería lo peor que podría pasar. Aquí se devuelve el plan con cada instancia
en línea, que es lo que el programa SAS ya hacía: el mismo trabajo una vez por cada llamada.
"""

from __future__ import annotations

import copy

from sgm.ir.models import Plan


def plan_desplegado(plan: Plan) -> tuple[Plan, set[str]]:
    """Copia del plan sin `iterate`, y los ids de los `iterate` que se desplegaron."""
    pendientes = [i for i in plan.iteraciones if i in plan.graph]
    if not pendientes:
        return plan, set()
    copia = copy.deepcopy(plan)
    miembros: dict[str, list[str]] = {}
    for iterate_id in pendientes:
        guardado = copia.iteraciones[iterate_id]
        operadores = guardado["operadores"]
        copia.graph.expand(iterate_id, operadores, guardado["aristas"])
        miembros[iterate_id] = [op.id for op in operadores]
    orden = {op_id: posicion for posicion, op_id in enumerate(copia.graph.topological())}
    for job in _todos(copia):
        job.subjobs = [
            [
                nuevo
                for op_id in subjob
                for nuevo in sorted(miembros.get(op_id, [op_id]), key=lambda i: orden.get(i, 0))
            ]
            for subjob in job.subjobs
        ]
    return copia, set(pendientes)


def _todos(plan: Plan):
    pila = list(plan.jobs)
    while pila:
        job = pila.pop()
        yield job
        pila.extend(job.children)


__all__ = ["plan_desplegado"]
