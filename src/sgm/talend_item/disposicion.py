"""Disposición automática de los nodos en el lienzo de Studio.

Studio dibuja cada nodo en las coordenadas `posX`/`posY` del `.item`. Si todos quedan en (0, 0),
el lienzo se ve como una sola pila de cajas encimadas y nadie puede seguir el flujo. Este módulo
calcula una posición nueva para cada nodo, de izquierda a derecha, en el orden en que se ejecutan:

- La columna de un nodo (`x`) es 200 veces su profundidad: el camino más largo desde un nodo sin
  entradas hasta él, siguiendo las conexiones.
- Dentro de una columna, las filas (`y`) siguen el orden de aparición en `job.nodos`: la fila `k`
  queda en `y = 96 * k`.

Así dos nodos nunca comparten (x, y). Si el Job tiene un ciclo, la conexión que lo cierra se ignora
para el cálculo de profundidad y el ciclo no cuelga la función.

La función es pura: devuelve un Job nuevo y deja el de entrada como estaba.
"""

from __future__ import annotations

from collections import deque
from dataclasses import replace

from sgm.talend_item.modelo import Job, Nodo

ANCHO_COLUMNA = 200  # separación horizontal entre profundidades
ALTO_FILA = 96  # separación vertical entre nodos de una misma columna


def _profundidades(job: Job) -> dict[str, int]:
    """Profundidad de cada UNIQUE_NAME: el camino más largo desde una fuente del grafo.

    Es un Kahn sobre las aristas que sí existen en el Job. Cuando la cola se vacía y aún quedan
    nodos, es que hay un ciclo: se corta por el primer nodo pendiente en orden de `job.nodos` y se
    sigue. Los nodos ya encolados no vuelven a recibir profundidad, y eso corta las aristas de
    retorno.
    """
    unicos = [nodo.unico for nodo in job.nodos]
    existentes = set(unicos)
    salen: dict[str, list[str]] = {unico: [] for unico in existentes}
    pendientes: dict[str, int] = {unico: 0 for unico in existentes}
    for conexion in job.conexiones:
        if conexion.origen in existentes and conexion.destino in existentes:
            if conexion.origen == conexion.destino:
                continue
            salen[conexion.origen].append(conexion.destino)
            pendientes[conexion.destino] += 1

    profundidad = {unico: 0 for unico in existentes}
    encolados: set[str] = set()
    cola: deque[str] = deque()

    def encolar(unico: str) -> None:
        encolados.add(unico)
        cola.append(unico)

    for unico in unicos:
        if unico not in encolados and pendientes[unico] == 0:
            encolar(unico)
    while len(encolados) < len(existentes):
        if not cola:
            # Ciclo: se fuerza el primer nodo que aún no entró, cortando sus entradas pendientes.
            encolar(next(unico for unico in unicos if unico not in encolados))
        actual = cola.popleft()
        for destino in salen[actual]:
            if destino in encolados:
                continue
            profundidad[destino] = max(profundidad[destino], profundidad[actual] + 1)
            pendientes[destino] -= 1
            if pendientes[destino] == 0:
                encolar(destino)
    return profundidad


def disponer(job: Job) -> Job:
    """Devuelve un Job nuevo con `x` e `y` asignados por columna y orden de aparición."""
    profundidad = _profundidades(job)
    filas: dict[int, int] = {}
    nodos: list[Nodo] = []
    for nodo in job.nodos:
        columna = profundidad[nodo.unico]
        fila = filas.get(columna, 0)
        filas[columna] = fila + 1
        nodos.append(replace(nodo, x=ANCHO_COLUMNA * columna, y=ALTO_FILA * fila))
    return replace(job, nodos=nodos)


__all__ = ["disponer"]
