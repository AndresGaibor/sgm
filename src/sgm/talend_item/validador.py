"""Validador estructural de un Job: lo que Studio rechaza, dicho antes de abrirlo.

Un `.item` mal armado no falla al escribirse: falla al abrirlo, o al compilarlo, o al ejecutarlo, y
para entonces el mensaje de Studio habla de un `NullPointerException` que no dice nada del SAS. Este
módulo mira el modelo del Job y devuelve la lista de defectos en castellano, con el nodo y la
conexión que los tienen.

Solo se mira el modelo: no se leen archivos ni se consulta a Studio. Eso lo hace útil en la suite
rápida y en el comando `sgm migrar`, que corre en cualquier máquina.

Las reglas son las que Studio exige para abrir un Job, más una de presentación:

1. Los `UNIQUE_NAME` no se repiten.
2. Cada conexión sale y llega a un nodo que existe.
3. Un nodo no tiene dos salidas (ni dos entradas) con el mismo nombre.
4. Por una conexión de fila viajan las mismas columnas, en el mismo orden, que el destino espera.
5. Un componente que lee un flujo tiene al menos una conexión entrante.
6. Los cuatro grupos de contexto existen y llevan las mismas claves.
7. Dos nodos no comparten (x, y): si lo hacen, Studio los dibuja encimados. Un Job sin disponer
   (todos en 0, 0) lo incumple; `disposicion.disponer` lo resuelve.

La regla 4 no se aplica al destino `tMap`: sus entradas viven en el `<nodeData>` del mapeo, no en
los bloques `<metadata>`, que son las salidas. Compararlas ahí sería comparar dos cosas distintas.
"""

from __future__ import annotations

from collections import Counter

from sgm.talend_item.desde_plan_contextos import GRUPOS
from sgm.talend_item.modelo import Columna, Job, Nodo

# Componentes que leen un flujo. Sin conexión entrante no tienen filas que procesar, y Studio los
# marca en rojo al compilar. La lista es de componentes que este repositorio emite o emitirá; uno
# nuevo que lea un flujo se agrega aquí.
CONSUMEN = frozenset(
    {
        "tAggregateRow",
        "tFileOutputDelimited",
        "tFileOutputExcel",
        "tFilterRow",
        "tJavaRow",
        "tJoin",
        "tLogRow",
        "tMap",
        "tReplace",
        "tSortRow",
        "tUnite",
        "tUniqRow",
    }
)


# Componentes cuyo esquema de entrada lo da la conexión que llega y no el suyo: lo que ellos
# declaran es el de su salida (el `tMap` y el `tAggregateRow` cambian las columnas).
ENTRADA_PROPIA = frozenset({"tMap", "tAggregateRow"})


def _columnas(nodo: Nodo, nombre: str) -> list[Columna]:
    """Columnas del conector `nombre`; si el nodo no tiene uno con ese nombre, las del primero.

    Un nodo simple (`tFileOutputDelimited`) tiene un solo esquema y el nombre de la conexión que
    llega no es el suyo; un `tMap` tiene uno por salida y ahí sí hay que acertar cuál.
    """
    bloques = nodo.metadatas or []
    if not bloques:
        return list(nodo.columnas)
    for bloque in bloques:
        if bloque.nombre == nombre:
            return list(bloque.columnas)
    return list(bloques[0].columnas)


def _repetidos(job: Job) -> list[str]:
    problemas = []
    for unico, veces in sorted(Counter(nodo.unico for nodo in job.nodos).items()):
        if veces > 1:
            problemas.append(f"UNIQUE_NAME repetido: '{unico}' aparece {veces} veces")
    return problemas


def _conexiones(job: Job) -> list[str]:
    problemas: list[str] = []
    unicos = {nodo.unico for nodo in job.nodos}
    salidas: Counter[tuple[str, str]] = Counter()
    entradas: Counter[tuple[str, str]] = Counter()
    for conexion in job.conexiones:
        if conexion.origen not in unicos:
            problemas.append(
                f"la conexión '{conexion.nombre}' sale de '{conexion.origen}', "
                "que no está en el Job"
            )
        if conexion.destino not in unicos:
            problemas.append(
                f"la conexión '{conexion.nombre}' llega a '{conexion.destino}', "
                "que no está en el Job"
            )
        salidas[(conexion.origen, conexion.nombre)] += 1
        entradas[(conexion.destino, conexion.nombre)] += 1
    for (unico, nombre), veces in sorted(salidas.items()):
        if veces > 1:
            problemas.append(
                f"el nodo '{unico}' tiene {veces} conexiones de salida llamadas '{nombre}'"
            )
    for (unico, nombre), veces in sorted(entradas.items()):
        if veces > 1:
            problemas.append(f"el nodo '{unico}' recibe {veces} conexiones llamadas '{nombre}'")
    return problemas


def _flujos(job: Job) -> list[str]:
    problemas: list[str] = []
    por_unico = {nodo.unico: nodo for nodo in job.nodos}
    for conexion in job.conexiones:
        if conexion.conector != "FLOW":
            continue
        origen = por_unico.get(conexion.origen)
        destino = por_unico.get(conexion.destino)
        if origen is None or destino is None or destino.componente in ENTRADA_PROPIA:
            continue
        dan = [columna.nombre for columna in _columnas(origen, conexion.nombre)]
        piden = [columna.nombre for columna in _columnas(destino, conexion.nombre)]
        if dan != piden:
            problemas.append(
                f"la conexión '{conexion.nombre}' de '{conexion.origen}' a "
                f"'{conexion.destino}' lleva {dan} y el destino espera {piden}"
            )
    return problemas


def _huerfanos(job: Job) -> list[str]:
    con_entrada = {conexion.destino for conexion in job.conexiones}
    return [
        f"el nodo '{nodo.unico}' ({nodo.componente}) no tiene ninguna conexión entrante"
        for nodo in job.nodos
        if nodo.componente in CONSUMEN and nodo.unico not in con_entrada
    ]


def _contextos(job: Job) -> list[str]:
    faltan = [grupo for grupo in GRUPOS if grupo not in job.contextos]
    if faltan:
        return [f"faltan los grupos de contexto {faltan}"]
    base = GRUPOS[0]
    esperadas = [parametro.nombre for parametro in job.contextos[base]]
    problemas = []
    for grupo, parametros in job.contextos.items():
        claves = [parametro.nombre for parametro in parametros]
        if claves == esperadas:
            continue
        sobran = [clave for clave in claves if clave not in esperadas]
        faltan_claves = [clave for clave in esperadas if clave not in claves]
        problemas.append(
            f"el grupo '{grupo}' no tiene las mismas claves que '{base}': "
            f"faltan {faltan_claves}, sobran {sobran}"
        )
    return problemas


def _superposicion(job: Job) -> list[str]:
    """Nodos que comparten (x, y): Studio los dibuja encimados y el lienzo no se puede leer."""
    por_posicion: dict[tuple[int, int], list[str]] = {}
    for nodo in job.nodos:
        por_posicion.setdefault((nodo.x, nodo.y), []).append(nodo.unico)
    problemas = []
    for (x, y), unicos in por_posicion.items():
        if len(unicos) < 2:
            continue
        problemas.append(f"los nodos {_enumerar(unicos)} están en la misma posición (x={x}, y={y})")
    return problemas


def _enumerar(nombres: list[str]) -> str:
    """Une nombres en castellano: «A y B», «A, B y C»."""
    if len(nombres) == 1:
        return nombres[0]
    return f"{', '.join(nombres[:-1])} y {nombres[-1]}"


def validar_job(job: Job) -> list[str]:
    """Lista de defectos estructurales del Job; vacía si Studio lo va a abrir sin quejarse."""
    return [
        *_repetidos(job),
        *_conexiones(job),
        *_flujos(job),
        *_huerfanos(job),
        *_contextos(job),
        *_superposicion(job),
    ]


__all__ = ["CONSUMEN", "validar_job"]
