"""Conversión acotada de campos de archivo con informats SAS demostrados."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

from sgm.formatos.informat_fecha import informat_fecha_soportado, leer_fecha
from sgm.migrar.interprete_errores import NoSoportadoEnInterprete

_SIMPLE = re.compile(r"(?i)^(\$?)(\d+)\.(\d*)$")
_NUMERICO = re.compile(r"(?i)^(?:(comma|dollar)(\d+)|(\d+))\.(\d*)$")


def informat_numerico_soportado(informat: str) -> bool:
    """Indica si el informat tiene una conversión numérica demostrada."""
    return _NUMERICO.fullmatch(informat.strip()) is not None


def leer_campo(texto: str, informat: str) -> str | None:
    """Convierte informats numéricos, de carácter y el subconjunto fechado demostrado."""
    if informat_fecha_soportado(informat):
        value = leer_fecha(texto, informat)
        return None if value is None else str(value)
    match = _SIMPLE.fullmatch(informat.strip())
    numeric = _NUMERICO.fullmatch(informat.strip())
    if match is None and numeric is None:
        raise NoSoportadoEnInterprete("informat", "P-INFORMAT-SIN-SOPORTE")
    if texto.strip() == "":
        return None
    if match is not None and match.group(1):
        return texto
    valor_texto = texto.strip()
    decimales_texto = numeric.group(4) if numeric is not None else match.group(3)
    modo = numeric.group(1) if numeric is not None else None
    if valor_texto == "." and modo is None:
        return None
    negativo = False
    if modo is not None:
        if "(" in valor_texto:
            if not valor_texto.startswith("(") or valor_texto.count("(") != 1:
                raise NoSoportadoEnInterprete("informat", "P-INFORMAT-VALOR-INVALIDO")
            negativo = True
            valor_texto = valor_texto[1:]
        valor_texto = (
            valor_texto.replace(",", "")
            .replace(" ", "")
            .replace("$", "")
            .replace("%", "")
            .replace("-", "")
            .replace(")", "")
        )
        if not re.fullmatch(r"(?:\d+(?:\.\d*)?|\.\d+)", valor_texto):
            raise NoSoportadoEnInterprete("informat", "P-INFORMAT-VALOR-INVALIDO")
    try:
        valor = Decimal(valor_texto)
    except InvalidOperation as error:
        raise NoSoportadoEnInterprete("informat", "P-INFORMAT-VALOR-INVALIDO") from error
    if not valor.is_finite():
        raise NoSoportadoEnInterprete("informat", "P-INFORMAT-VALOR-INVALIDO")
    if negativo:
        valor = -valor
    decimales = int(decimales_texto or 0)
    if decimales and "." not in valor_texto:
        valor /= Decimal(10) ** decimales
    return format(valor.normalize(), "f")


__all__ = ["informat_numerico_soportado", "leer_campo"]
