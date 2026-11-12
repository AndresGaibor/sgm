"""Operadores de expresiones SAS usados por el intérprete."""

from __future__ import annotations

import re

from . import semantica
from .interprete_errores import NoSoportadoEnInterprete


def _como_texto_con_blancos(valor: object) -> str:
    """Preserva espacios de texto para operaciones donde forman parte del resultado."""
    return valor if isinstance(valor, str) else semantica.como_texto(valor)


def concatenar(izquierda: object, derecha: object) -> str:
    """Une valores sin recortar espacios; la longitud variable queda Pendiente (lrcon, p. 151)."""
    return _como_texto_con_blancos(izquierda) + _como_texto_con_blancos(derecha)


def pertenece(buscado: object, opciones: list[object]) -> bool:
    """IN compara con cada valor usando la igualdad SAS (lrcon, p. 145)."""
    return any(semantica.iguales(buscado, opcion) for opcion in opciones)


def entre(valor: object, bajo: object, alto: object) -> bool:
    """BETWEEN incluye ambos extremos (PROC SQL, p. 70)."""
    return semantica.mayor_igual(valor, bajo) and semantica.menor_igual(valor, alto)


def _patron_like(patron: str) -> re.Pattern[str]:
    partes = []
    for caracter in patron:
        partes.append(".*" if caracter == "%" else "." if caracter == "_" else re.escape(caracter))
    return re.compile("".join(partes), re.DOTALL)


def parecido(texto: object, patron: object) -> bool:
    """LIKE conserva blancos; faltantes quedan pendientes (PROC SQL, p. 412)."""
    if semantica.es_faltante(texto) or semantica.es_faltante(patron):
        raise NoSoportadoEnInterprete(
            "operador",
            "Pendiente: P-LIKE-TIPO-Y-LONGITUD-VARIABLE; no se conoce el tipo ni la longitud "
            "declarada del valor faltante",
        )
    valor = texto if isinstance(texto, str) else semantica.como_texto(texto)
    especificacion = patron if isinstance(patron, str) else semantica.como_texto(patron)
    return _patron_like(especificacion).fullmatch(valor) is not None
