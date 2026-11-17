"""Comparación de filas agrupadas con orden entre grupos y empates libres."""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

Fila = list[str]
DiferenciaT = TypeVar("DiferenciaT")
Llave = tuple[str, ...]


def _llaves_iguales(
    esperada: Llave,
    obtenida: Llave,
    iguales: Callable[[str, str, float], bool],
    tolerancia: float,
) -> bool:
    return all(iguales(e, o, tolerancia) for e, o in zip(esperada, obtenida, strict=True))


def _indices_orden_grupo(
    columnas: list[str], orden_grupo: list[dict[str, object]]
) -> list[tuple[int, bool]]:
    """Valida las llaves ordenadas que se exigen entre grupos, no dentro de ellos."""
    if not isinstance(orden_grupo, list) or not orden_grupo:
        raise ValueError("'orden_grupo' debe ser una lista no vacía")
    indices: list[tuple[int, bool]] = []
    usados: set[int] = set()
    for criterio in orden_grupo:
        if not isinstance(criterio, dict) or set(criterio) != {"columna", "descendente"}:
            raise ValueError("cada llave de 'orden_grupo' requiere columna y descendente")
        nombre = criterio["columna"]
        descendente = criterio["descendente"]
        if not isinstance(nombre, str) or not isinstance(descendente, bool):
            raise ValueError("'columna' debe ser texto y 'descendente' un booleano")
        indice = next(
            (i for i, columna in enumerate(columnas) if columna.casefold() == nombre.casefold()),
            None,
        )
        if indice is None:
            raise ValueError(f"'orden_grupo' refiere una columna inexistente: {nombre}")
        if indice in usados:
            raise ValueError(f"'orden_grupo' repite la columna: {nombre}")
        usados.add(indice)
        indices.append((indice, descendente))
    return indices


def _agrupar(
    filas: list[Fila],
    indices: list[tuple[int, bool]],
    iguales: Callable[[str, str, float], bool],
    tolerancia: float,
) -> tuple[dict[tuple[str, ...], list[Fila]], list[tuple[str, ...]], bool]:
    """Forma los grupos de una tabla sin tomar llaves de la otra tabla."""
    grupos: dict[tuple[str, ...], list[Fila]] = {}
    secuencia: list[tuple[str, ...]] = []
    anterior: tuple[str, ...] | None = None
    repetido = False
    for fila in filas:
        llave = tuple(fila[indice] for indice, _ in indices)
        if llave not in grupos:
            llave = next(
                (
                    conocida
                    for conocida in grupos
                    if _llaves_iguales(conocida, llave, iguales, tolerancia)
                ),
                llave,
            )
        if llave != anterior:
            if llave in grupos:
                repetido = True
            secuencia.append(llave)
            grupos.setdefault(llave, [])
            anterior = llave
        grupos[llave].append(fila)
    return grupos, secuencia, repetido


def _ordenar_llaves_grupo(
    llaves: list[tuple[str, ...]],
    indices: list[tuple[int, bool]],
    clave_celda: Callable[[str], tuple],
) -> list[tuple[str, ...]]:
    ordenadas = list(llaves)
    for posicion in reversed(range(len(indices))):
        descendente = indices[posicion][1]
        ordenadas.sort(
            key=lambda llave, posicion=posicion: clave_celda(llave[posicion]),
            reverse=descendente,
        )
    return ordenadas


def _alinear_grupos(
    esperadas: list[Llave],
    obtenidas: list[Llave],
    iguales: Callable[[str, str, float], bool],
    tolerancia: float,
) -> tuple[dict[Llave, Llave], list[Llave]]:
    """Empareja las llaves ordenadas una sola vez, sin fusionar grupos entre tablas."""
    parejas: dict[Llave, Llave] = {}
    libres = list(obtenidas)
    for esperada in esperadas:
        for posicion, obtenida in enumerate(libres):
            if _llaves_iguales(esperada, obtenida, iguales, tolerancia):
                parejas[esperada] = libres.pop(posicion)
                break
    return parejas, libres


def comparar_por_grupos(
    esperadas: list[Fila],
    obtenidas: list[Fila],
    columnas: list[str],
    tolerancia: float,
    orden_grupo: list[dict[str, object]],
    *,
    diferencia: Callable[..., DiferenciaT],
    comparar_conjunto: Callable[..., list[DiferenciaT]],
    iguales: Callable[[str, str, float], bool],
    clave_celda: Callable[[str], tuple],
    unir: Callable[[Fila], str],
) -> list[DiferenciaT]:
    """Compara conjuntos por llave, mantiene orden entre grupos y libera empates internos."""
    indices = _indices_orden_grupo(columnas, orden_grupo)
    grupos_esp, secuencia_esp, _ = _agrupar(esperadas, indices, iguales, tolerancia)
    grupos_obt, secuencia_obt, llaves_separadas = _agrupar(obtenidas, indices, iguales, tolerancia)
    orden_esperado = _ordenar_llaves_grupo(list(grupos_esp), indices, clave_celda)
    orden_obtenido = _ordenar_llaves_grupo(list(grupos_obt), indices, clave_celda)
    parejas, sobrantes = _alinear_grupos(orden_esperado, orden_obtenido, iguales, tolerancia)
    esperada_por_obtenida = {obtenida: esperada for esperada, obtenida in parejas.items()}
    diferencias: list[DiferenciaT] = []
    if secuencia_esp != orden_esperado:
        diferencias.append(
            diferencia(
                "orden",
                f"los grupos esperados no siguen el orden declarado: {orden_esperado}",
            )
        )
    if llaves_separadas:
        diferencias.append(diferencia("orden", "las filas de un grupo aparecen separadas"))
    if [esperada_por_obtenida.get(llave, llave) for llave in secuencia_obt] != orden_esperado:
        diferencias.append(
            diferencia(
                "orden",
                f"orden de grupos: esperado {orden_esperado}, obtenido {secuencia_obt}",
            )
        )

    desplazamiento = 0
    llaves = [(llave, parejas.get(llave)) for llave in orden_esperado]
    llaves.extend((None, llave) for llave in sobrantes)
    for llave_esp, llave_obt in llaves:
        grupo_esp = grupos_esp.get(llave_esp, [])
        grupo_obt = grupos_obt.get(llave_obt, [])
        if grupo_esp and grupo_obt:
            for diferencia_fila in comparar_conjunto(
                grupo_esp, grupo_obt, columnas, tolerancia
            ):
                fila = diferencia_fila.fila
                diferencias.append(
                    diferencia(
                        diferencia_fila.tipo,
                        diferencia_fila.mensaje,
                        fila + desplazamiento if fila is not None else None,
                        diferencia_fila.columna,
                        diferencia_fila.esperado,
                        diferencia_fila.obtenido,
                    )
                )
        elif grupo_esp:
            diferencias.extend(
                diferencia("faltante", fila=desplazamiento + i + 1, esperado=unir(fila))
                for i, fila in enumerate(grupo_esp)
            )
        else:
            diferencias.extend(
                diferencia("sobrante", fila=desplazamiento + i + 1, obtenido=unir(fila))
                for i, fila in enumerate(grupo_obt)
            )
        desplazamiento += len(grupo_esp)
    return diferencias
