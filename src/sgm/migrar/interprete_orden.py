"""Orden y quitar duplicados del intérprete: ordenar, quitar duplicados y llaves de ordenación.

Movido desde interprete_filas.py sin cambio de comportamiento (hito 242m).
"""

from __future__ import annotations

from sgm.migrar.interprete_base import _clave, _nombre_de_columna
from sgm.migrar.interprete_valores import _columna


def _llaves(filas: list[dict], params: dict) -> list[str]:
    """Columnas del `BY`; `_ALL_` son todas las de la fila."""
    nombres: list[str] = []
    for nombre in params.get("by") or []:
        if str(nombre).strip().lower() == "_all_":
            nombres += list(filas[0]) if filas else []
        else:
            nombres.append(_nombre_de_columna(filas, nombre))
    return nombres


def _ordenar(filas: list[dict], params: dict) -> list[dict]:
    """`ORDER BY` de PROC SQL: el faltante va primero en ascendente (`sqlproc`); orden estable.

    Se ordena de la última llave a la primera, cada una con su sentido; como el orden de Python es
    estable, las filas que empatan en todas las llaves conservan el orden en que llegaron.
    """
    llaves = _llaves(filas, params)
    sentidos = list(params.get("descending") or [])
    resultado = list(filas)
    for posicion in range(len(llaves) - 1, -1, -1):
        descendente = posicion < len(sentidos) and bool(sentidos[posicion])
        llave = llaves[posicion]
        resultado.sort(
            key=lambda fila, llave=llave: _clave(_columna(fila, llave)), reverse=descendente
        )
    return resultado


def _unicos(filas: list[dict], params: dict) -> list[dict]:
    """`SELECT DISTINCT`: la primera fila de cada combinación de llaves; faltante = faltante."""
    llaves = _llaves(filas, params)
    vistas: set[tuple] = set()
    resultado: list[dict] = []
    for fila in filas:
        clave = tuple(_clave(_columna(fila, llave)) for llave in llaves)
        if clave not in vistas:
            vistas.add(clave)
            resultado.append(fila)
    return resultado


