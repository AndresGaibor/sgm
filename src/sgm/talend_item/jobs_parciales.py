"""Jobs parciales: un Job unido a un hueco sin traducción no se escribe (B-17).

El hueco (`unsupported`) deja su pendiente con código estable; el Job del que forma parte no sale,
porque sería un Job a medias. Se sigue la componente conexa del grafo, no la partición del plan.
"""

from __future__ import annotations

from sgm.ir.models import Plan

# Pendientes estables de los `OUTPUT` que no se pueden demostrar (B-17, casos negativos).
CODIGO_DETALLE = {
    "OUTPUT_DESTINO_REPETIDO": "P-OUTPUT-DESTINO-REPETIDO",
    "OUTPUT_DESTINO_NO_DECLARADO": "P-OUTPUT-DESTINO-NO-DECLARADO",
}


def tiene_hueco(plan: Plan, job, emitidos: frozenset[str] | set[str] = frozenset()) -> bool:
    """Si el Job está unido a un hueco sin traducción por el grafo: el Job queda parcial (B-17).

    La partición del plan no siempre pone el hueco dentro del Job (queda entre la lectura y la
    escritura), así que se sigue la componente conexa de sus operadores. Un operador de `emitidos`
    ya tiene su componente (p. ej. un `tJavaRow` de LAG), y no cuenta como hueco.
    """
    vecinos: dict[str, set[str]] = {}
    for arista in plan.graph.edges():
        vecinos.setdefault(arista.src, set()).add(arista.dst)
        vecinos.setdefault(arista.dst, set()).add(arista.src)
    pila = [op for sub in job.subjobs for op in sub if op in plan.graph]
    visitados: set[str] = set()
    while pila:
        actual = pila.pop()
        if actual in visitados:
            continue
        visitados.add(actual)
        op = plan.graph.operator(actual)
        if actual not in emitidos:
            # Un `stateful_row` (RETAIN, suma, FIRST./LAST.) sin emisor es hueco (decisión 5; B-13).
            if op.status == "hueco" or op.kind in ("unsupported", "stateful_row"):
                return True
        pila.extend(vecinos.get(actual, ()))
    return False
