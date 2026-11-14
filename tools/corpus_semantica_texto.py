"""Funciones SAS de texto con semántica documentada para el oráculo."""

from __future__ import annotations

import math


def length(texto: str) -> int:
    """LENGTH excluye blancos finales y devuelve uno para una cadena en blanco."""
    if not texto.isascii():
        raise ValueError("Pendiente: P-LENGTH-CODIFICACION; no se conoce la codificación SAS")
    return max(1, len(texto.rstrip(" ")))


def propcase(texto: str, delimitadores: object = None) -> str:
    """PROPCASE baja el texto y sube el carácter inicial y el siguiente a cada delimitador."""
    lista = " /-.(\t" if delimitadores is None else str(delimitadores).lower()
    if not texto.isascii() or not lista.isascii():
        raise ValueError("Pendiente: P-PROPCASE-TRANTAB-LOCALE; no se conoce la codificación SAS")
    resultado: list[str] = []
    mayuscula = True
    for caracter in texto.lower():
        resultado.append(caracter.upper() if mayuscula else caracter)
        mayuscula = caracter in lista
    return "".join(resultado)


def reverse(texto: str) -> str:
    """REVERSE invierte los caracteres; los blancos finales pasan al inicio."""
    if not texto.isascii():
        raise ValueError("Pendiente: P-REVERSE-CODIFICACION-SBCS; no se conoce la codificación SAS")
    return texto[::-1]


def repeat(texto: str, veces: int) -> str:
    """REPEAT devuelve el argumento original y `veces` copias adicionales."""
    numero = float(veces)
    if not math.isfinite(numero) or numero < 0 or not numero.is_integer():
        raise ValueError("REPEAT requiere un número entero no negativo")
    return texto * (int(numero) + 1)


def right(texto: str) -> str:
    """RIGHT desplaza al inicio los blancos finales sin cambiar la longitud."""
    return texto.rstrip(" ").rjust(len(texto), " ")


def trimn(texto: str) -> str:
    """TRIMN quita los blancos finales y puede devolver una cadena de longitud cero."""
    return texto.rstrip(" ")
