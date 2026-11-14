"""Conversión acotada de campos de archivo con informats SAS demostrados."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

from sgm.migrar.interprete_errores import NoSoportadoEnInterprete

_SIMPLE = re.compile(r"(?i)^(\$?)(\d+)\.(\d*)$")


def leer_campo(texto: str, informat: str) -> str | None:
    """Convierte `$w.`, `w.` o `w.d`; informats restantes se dejan pendientes."""
    match = _SIMPLE.fullmatch(informat.strip())
    if match is None:
        raise NoSoportadoEnInterprete("informat", "P-INFORMAT-SIN-SOPORTE")
    caracter, _ancho, decimales_texto = match.groups()
    if texto.strip() == "":
        return None
    if caracter:
        return texto
    valor_texto = texto.strip()
    if valor_texto == ".":
        return None
    try:
        valor = Decimal(valor_texto)
    except InvalidOperation as error:
        raise NoSoportadoEnInterprete("informat", "P-INFORMAT-VALOR-INVALIDO") from error
    decimales = int(decimales_texto or 0)
    if decimales and "." not in valor_texto:
        valor /= Decimal(10) ** decimales
    return format(valor.normalize(), "f")


__all__ = ["leer_campo"]
