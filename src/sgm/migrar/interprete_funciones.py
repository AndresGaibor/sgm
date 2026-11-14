"""Despacho único de las funciones que ejecuta el intérprete."""

from __future__ import annotations

from collections.abc import Callable

from .interprete_errores import NoSoportadoEnInterprete
from .interprete_fechas import FUNCIONES as FUNCIONES_FECHAS
from .interprete_formatos import FUNCIONES as FUNCIONES_FORMATOS
from .interprete_numerico import FUNCIONES as FUNCIONES_NUMERICAS
from .interprete_texto import FUNCIONES as FUNCIONES_TEXTO

Funcion = Callable[[list], object]
FUNCIONES: dict[str, Funcion] = {
    **FUNCIONES_TEXTO,
    **FUNCIONES_NUMERICAS,
    **FUNCIONES_FECHAS,
    **FUNCIONES_FORMATOS,
}


def llamar(nombre: str, argumentos: list) -> object:
    """Quita los prefijos del árbol o la fila y despacha a la función correspondiente."""
    if nombre.startswith("sgm_"):
        nombre = nombre[4:]
    if nombre.startswith("row_"):
        nombre = nombre[4:]
    try:
        funcion = FUNCIONES[nombre]
    except KeyError:
        raise NoSoportadoEnInterprete("funcion", nombre) from None
    return funcion(argumentos)
