"""Funciones de entrada y formatos del intérprete."""

from __future__ import annotations

from collections.abc import Callable
from decimal import Decimal, InvalidOperation

from sgm.migrar import semantica

from .interprete_errores import NoSoportadoEnInterprete


def _input_wd(argumentos: list) -> float | None:
    """Subconjunto documentado INPUT(x,w.d): convierte números y aplica d solo sin punto decimal."""
    if len(argumentos) < 2:
        raise NoSoportadoEnInterprete("funcion", "INPUT requiere el valor y un informat w.d")
    texto = semantica.como_texto(argumentos[0]).strip()
    informat = semantica.como_numero(argumentos[1])
    if not texto or texto == "." or informat is None:
        return None
    decimales = int(round((informat - int(informat)) * 10))
    try:
        if "." in texto:
            return float(texto)
        numero = Decimal(texto) / (Decimal(10) ** decimales)
        return float(numero)
    except (InvalidOperation, ValueError):
        return None


FUNCIONES: dict[str, Callable[[list], object]] = {"input": _input_wd}
