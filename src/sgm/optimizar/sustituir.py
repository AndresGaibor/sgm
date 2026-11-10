"""Sustitución de nombres de columna dentro de una expresión SAS, sin tocar lo que no es columna.

Al fundir dos pasos, el segundo deja de leer la tabla intermedia y pasa a leer lo que leía el
primero: cada columna que nombraba hay que cambiarla por la expresión que la producía. El cambio se
hace sobre el texto, token a token, para que la expresión siga siendo la del SAS y la traduzca el
mismo traductor de siempre. No se tocan los literales de texto, los números, las funciones
(`nombre(`), las macrovariables (`&nombre`) ni el sufijo de un literal de fecha (`'01JAN2020'd`).
"""

from __future__ import annotations

import re
from collections.abc import Callable

_TOKEN = re.compile(
    r"""
    (?P<texto>'(?:[^']|'')*'|"(?:[^"]|"")*")
  | (?P<numero>\d+(?:\.\d*)?(?:[eE][+-]?\d+)?)
  | (?P<nombre>[A-Za-z_]\w*(?:\.(?:[A-Za-z_]\w*|\*))*)
  | (?P<otro>.)
    """,
    re.VERBOSE | re.DOTALL,
)
_COLUMNA = re.compile(r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*")
# Palabras del lenguaje que tienen forma de nombre: nunca son una columna que sustituir.
RESERVADAS = frozenset(
    "and or not in like between is null missing case when then else end eq ne gt lt ge le "
    "contains as distinct calculated".split()
)

# Recibe las partes del nombre en minúsculas (`["ventas", "monto"]`) y devuelve el texto que lo
# reemplaza, o `None` para dejarlo como está.
Resolver = Callable[[list[str]], str | None]


def es_columna(texto: str) -> bool:
    """`monto` o `ventas.monto`: un nombre solo, sin operadores ni funciones."""
    return bool(_COLUMNA.fullmatch(texto.strip()))


def sustituir(expresion: str, resolver: Resolver) -> str:
    """La expresión con cada nombre de columna pasado por `resolver`."""
    partes: list[str] = []
    previo = ""  # clase del token anterior, pegado o no
    pegado = ""  # último carácter escrito, para saber si el nombre va pegado a `&` o a un literal
    for token in _TOKEN.finditer(expresion):
        texto = token.group(0)
        es_nombre = token.lastgroup == "nombre"
        if es_nombre and not _intocable(texto, expresion, token.end(), previo, pegado):
            nuevo = resolver(texto.lower().split("."))
            if nuevo is not None:
                texto = nuevo
        partes.append(texto)
        previo = token.lastgroup or ""
        pegado = token.group(0)[-1]
    return "".join(partes)


def _intocable(texto: str, expresion: str, fin: int, previo: str, pegado: str) -> bool:
    if texto.lower() in RESERVADAS:
        return True
    if pegado in ("&", "%") or previo in ("texto", "numero"):
        return True  # macrovariable, sufijo de literal (`'...'d`) o resto de un número
    return expresion[fin:].lstrip().startswith("(")  # función


__all__ = ["RESERVADAS", "Resolver", "es_columna", "sustituir"]
