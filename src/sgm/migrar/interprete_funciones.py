"""Funciones SAS del intérprete: input, substr, compress, scan y sus equivalentes.

Movido desde interprete_valores.py sin cambio de comportamiento (hito 242m).
"""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

from sgm.migrar import semantica
from sgm.migrar.interprete_base import NoSoportadoEnInterprete, _numero


def _funcion(nombre: str, argumentos: list) -> object:
    if nombre.startswith("sgm_"):
        nombre = nombre[4:]
    if nombre.startswith("row_"):
        nombre = nombre[4:]
    if nombre == "mean":
        valores = [_numero(valor) for valor in argumentos]
        presentes = [valor for valor in valores if valor is not None]
        return sum(presentes) / len(presentes) if presentes else None
    if nombre in ("min", "max"):
        valores = [_numero(valor) for valor in argumentos]
        presentes = [valor for valor in valores if valor is not None]
        return (min(presentes) if nombre == "min" else max(presentes)) if presentes else None
    if nombre == "missing":
        return semantica.es_faltante(argumentos[0] if argumentos else None)
    if nombre == "coalesce":
        return next((valor for valor in argumentos if not semantica.es_faltante(valor)), None)
    if nombre == "coalescec":
        return next((valor for valor in argumentos if not semantica.es_faltante(valor)), None)
    if nombre == "trim":
        return semantica.como_texto(argumentos[0] if argumentos else None).rstrip()
    if nombre == "strip":
        return semantica.como_texto(argumentos[0] if argumentos else None).strip()
    if nombre == "upcase":
        return semantica.como_texto(argumentos[0] if argumentos else None).upper()
    if nombre == "lowcase":
        return semantica.como_texto(argumentos[0] if argumentos else None).lower()
    if nombre == "length":
        return len(semantica.como_texto(argumentos[0] if argumentos else None))
    if nombre == "left":
        texto = semantica.como_texto(argumentos[0] if argumentos else None)
        return texto.lstrip(" ") + " " * (len(texto) - len(texto.lstrip(" ")))
    if nombre in ("substr", "substrn"):
        if len(argumentos) < 2 or semantica.es_faltante(argumentos[0]):
            return " "
        texto = _texto_substr(argumentos[0], nombre)
        inicio = int(_numero(argumentos[1]) or 1) - 1
        longitud = (
            None
            if len(argumentos) < 3 or semantica.es_faltante(argumentos[2])
            else int(_numero(argumentos[2]) or 0)
        )
        if inicio < 0:
            inicio = max(len(texto) + inicio, 0)
        return texto[inicio:] if longitud is None else texto[inicio : inicio + max(longitud, 0)]
    if nombre == "input":
        return _input_wd(argumentos)
    if nombre == "compress":
        return _compress(argumentos)
    if nombre == "scan":
        return _scan(argumentos)
    if nombre == "abs":
        numero = _numero(argumentos[0] if argumentos else None)
        return None if numero is None else abs(numero)
    if nombre == "sum":
        valores = [_numero(valor) for valor in argumentos]
        if any(not semantica.es_faltante(valor) and convertido is None
               for valor, convertido in zip(argumentos, valores, strict=True)):
            raise NoSoportadoEnInterprete("funcion", "SUM requiere argumentos numéricos")
        presentes = [valor for valor in valores if valor is not None]
        return sum(presentes) if presentes else None
    raise NoSoportadoEnInterprete("funcion", nombre)


def _texto_substr(valor: object, funcion: str) -> str:
    """Conversión numérica documentada para SUBSTR/SUBSTRN en las expresiones del corpus."""
    if isinstance(valor, (int, float)):
        texto = format(valor, ".12g")
        return texto if funcion == "substrn" else texto.rjust(12)
    return semantica.como_texto(valor)


def _input_wd(argumentos: list) -> float | None:
    """Subconjunto documentado INPUT(x,w.d): convierte números y aplica d solo sin punto decimal."""
    if len(argumentos) < 2:
        raise NoSoportadoEnInterprete("funcion", "INPUT requiere el valor y un informat w.d")
    texto = semantica.como_texto(argumentos[0]).strip()
    informat = _numero(argumentos[1])
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
    posicion = int(_numero(argumentos[1]) or 0)
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


