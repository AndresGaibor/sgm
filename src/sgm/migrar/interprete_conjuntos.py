"""EXCEPT e INTERSECT de PROC SQL en el intérprete del anillo B (plan C, tarea C-10).

Son operaciones de conjuntos: las filas se comparan por posición de columna (sqlproc, p. 129),
sin repetidos, y un faltante casa con otro faltante (sqlproc, p. 102). El resultado sale en el
orden de la primera rama.
"""

from __future__ import annotations

from sgm.migrar.interprete_base import NoSoportadoEnInterprete, _clave


def _llave(fila: dict) -> tuple:
    return tuple(_clave(valor) for valor in fila.values())


def conjunto(operacion: str, entradas: list[list[dict]]) -> list[dict]:
    if len(entradas) != 2:
        raise NoSoportadoEnInterprete("union", f"{operacion} necesita exactamente dos ramas")
    izquierda, derecha = entradas
    en_derecha = {_llave(fila) for fila in derecha}
    vistas: set[tuple] = set()
    salida: list[dict] = []
    for fila in izquierda:
        llave = _llave(fila)
        if llave in vistas:
            continue
        vistas.add(llave)
        if (operacion == "intersect") == (llave in en_derecha):
            salida.append(fila)
    return salida
