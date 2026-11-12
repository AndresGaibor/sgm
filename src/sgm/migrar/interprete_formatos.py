"""Funciones de entrada y formatos del intérprete."""

from __future__ import annotations

import math
import re
from collections.abc import Callable
from decimal import Decimal, InvalidOperation

from sgm.migrar import semantica

from .interprete_errores import NoSoportadoEnInterprete

_INFORMAT_WD = re.compile(r"\s*(\d+)(?:\.(\d*))?\s*")


def _partes_informat(valor: object) -> tuple[int, int] | None:
    """Obtiene ancho y decimales del informat w.d; la cadena conserva d de dos cifras."""
    if isinstance(valor, str):
        coincidencia = _INFORMAT_WD.fullmatch(valor)
        if coincidencia is None:
            return None
        ancho = int(coincidencia.group(1))
        decimales = int(coincidencia.group(2) or "0")
    else:
        informat = semantica.como_numero(valor)
        if informat is None or not math.isfinite(informat):
            return None
        ancho = int(informat)
        decimales = int(round((informat - ancho) * 10))
    if not 1 <= ancho <= 32 or not 0 <= decimales <= 31:
        return None
    return ancho, decimales


def _input_wd(argumentos: list) -> float | None:
    """INPUT con informat w.d: lee el campo de ancho w y aplica d si no hay punto decimal."""
    if len(argumentos) < 2:
        raise NoSoportadoEnInterprete("funcion", "INPUT requiere el valor y un informat w.d")
    partes = _partes_informat(argumentos[1])
    if partes is None:
        return None
    ancho, decimales = partes
    texto = semantica.como_texto(argumentos[0])[:ancho].strip()
    if not texto or texto == ".":
        return None
    try:
        if "." in texto or "e" in texto.lower():
            return float(texto)
        numero = Decimal(texto) / (Decimal(10) ** decimales)
        return float(numero)
    except (InvalidOperation, ValueError):
        return None


FUNCIONES: dict[str, Callable[[list], object]] = {"input": _input_wd}
