"""Funciones de texto del intérprete, con la semántica que hoy usa el corpus."""

from __future__ import annotations

import re
from collections.abc import Callable

from sgm.migrar import semantica


def _texto_substr(valor: object, funcion: str) -> str:
    """Conversión numérica documentada para SUBSTR/SUBSTRN en las expresiones del corpus."""
    if isinstance(valor, (int, float)):
        texto = format(valor, ".12g")
        return texto if funcion == "substrn" else texto.rjust(12)
    return semantica.como_texto(valor)


def _trim(argumentos: list) -> str:
    return semantica.como_texto(argumentos[0] if argumentos else None).rstrip()


def _strip(argumentos: list) -> str:
    return semantica.como_texto(argumentos[0] if argumentos else None).strip()


def _upcase(argumentos: list) -> str:
    return semantica.como_texto(argumentos[0] if argumentos else None).upper()


def _lowcase(argumentos: list) -> str:
    return semantica.como_texto(argumentos[0] if argumentos else None).lower()


def _length(argumentos: list) -> int:
    return len(semantica.como_texto(argumentos[0] if argumentos else None))


def _left(argumentos: list) -> str:
    texto = semantica.como_texto(argumentos[0] if argumentos else None)
    return texto.lstrip(" ") + " " * (len(texto) - len(texto.lstrip(" ")))


def _subcadena(argumentos: list, funcion: str) -> str:
    if len(argumentos) < 2 or semantica.es_faltante(argumentos[0]):
        return " "
    texto = _texto_substr(argumentos[0], funcion)
    inicio = int(semantica.como_numero(argumentos[1]) or 1) - 1
    longitud = (
        None
        if len(argumentos) < 3 or semantica.es_faltante(argumentos[2])
        else int(semantica.como_numero(argumentos[2]) or 0)
    )
    if inicio < 0:
        inicio = max(len(texto) + inicio, 0)
    return texto[inicio:] if longitud is None else texto[inicio : inicio + max(longitud, 0)]


def _substr(argumentos: list) -> str:
    return _subcadena(argumentos, "substr")


def _substrn(argumentos: list) -> str:
    return _subcadena(argumentos, "substrn")


def _compress(argumentos: list) -> str:
    """COMPRESS con lista de caracteres y modificadores usados por los vectores documentados."""
    texto = semantica.como_texto(argumentos[0] if argumentos else None)
    lista = semantica.como_texto(argumentos[1]) if len(argumentos) > 1 else " "
    modificadores = semantica.como_texto(argumentos[2]).lower() if len(argumentos) > 2 else ""
    quitar: set[str] = set(lista)
    if "d" in modificadores:
        quitar.update("0123456789")
    if "a" in modificadores:
        quitar.update("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
    if "l" in modificadores:
        quitar.update("abcdefghijklmnopqrstuvwxyz")
    if "u" in modificadores:
        quitar.update("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    if "s" in modificadores:
        quitar.update(" \t\n\r\f\v")
    if "i" in modificadores:
        quitar.update(caracter.lower() for caracter in tuple(quitar))
        quitar.update(caracter.upper() for caracter in tuple(quitar))
    if "k" in modificadores:
        return "".join(caracter for caracter in texto if caracter in quitar)
    return "".join(caracter for caracter in texto if caracter not in quitar)


def _scan(argumentos: list) -> str:
    """SCAN con delimitadores explícitos y blancos por omisión, según vectores del corpus."""
    if len(argumentos) < 2:
        return " "
    texto = semantica.como_texto(argumentos[0])
    posicion = int(semantica.como_numero(argumentos[1]) or 0)
    delimitadores = (
        semantica.como_texto(argumentos[2])
        if len(argumentos) > 2
        else " \t\n\r!$%&()*+,-./;<^|"
    )
    if not delimitadores:
        delimitadores = " \t\n\r!$%&()*+,-./;<^|"
    patron = "[" + re.escape(delimitadores) + "]+"
    tokens = [token for token in re.split(patron, texto) if token]
    indice = posicion - 1 if posicion > 0 else len(tokens) + posicion
    return tokens[indice] if 0 <= indice < len(tokens) else " "


def _coalescec(argumentos: list) -> object:
    return next((valor for valor in argumentos if not semantica.es_faltante(valor)), None)


FUNCIONES: dict[str, Callable[[list], object]] = {
    "trim": _trim,
    "strip": _strip,
    "upcase": _upcase,
    "lowcase": _lowcase,
    "length": _length,
    "left": _left,
    "substr": _substr,
    "substrn": _substrn,
    "compress": _compress,
    "scan": _scan,
    "coalescec": _coalescec,
}
