"""Rewrite a documented SUBSTR pseudo-variable assignment as a character expression."""

from __future__ import annotations

import re

_CALL = re.compile(r"(?is)^\s*substr\s*\(")
_VARIABLE = re.compile(r"(?i)^[a-z_][a-z0-9_]*$")
_NUMERIC_EXPRESSION = re.compile(r"(?i)^[a-z0-9_.$,+*/%()\s-]+$")


def _argumentos(texto: str, inicio: int) -> list[str] | None:
    """Split function arguments without splitting nested calls or quoted commas."""
    resultado: list[str] = []
    principio = inicio
    profundidad = 1
    comilla = ""
    posicion = inicio
    while posicion < len(texto):
        caracter = texto[posicion]
        if comilla:
            if caracter == comilla:
                if posicion + 1 < len(texto) and texto[posicion + 1] == comilla:
                    posicion += 1
                else:
                    comilla = ""
        elif caracter in "'\"":
            comilla = caracter
        elif caracter == "(":
            profundidad += 1
        elif caracter == ")":
            profundidad -= 1
            if profundidad == 0:
                resultado.append(texto[principio:posicion].strip())
                return resultado if not texto[posicion + 1 :].strip() else None
        elif caracter == "," and profundidad == 1:
            resultado.append(texto[principio:posicion].strip())
            principio = posicion + 1
        posicion += 1
    return None


def reescribir_substr_izquierda(objetivo: str, valor: str) -> tuple[str, str] | None:
    """Rewrite supported `SUBSTR(variable, position <, length>) = value` assignments.

    The expression preserves the original variable width. With an explicit length, a shorter
    replacement is padded and a longer one is truncated. Without it, SAS replaces as many
    characters as the right-hand value contains.
    """
    llamada = _CALL.match(objetivo)
    if llamada is None:
        return None
    argumentos = _argumentos(objetivo, llamada.end())
    if argumentos is None or len(argumentos) not in (2, 3):
        return None
    variable, posicion = argumentos[:2]
    longitud = argumentos[2] if len(argumentos) == 3 else None
    if not _VARIABLE.fullmatch(variable):
        return None
    if not _NUMERIC_EXPRESSION.fullmatch(posicion):
        return None
    if longitud is not None and not _NUMERIC_EXPRESSION.fullmatch(longitud):
        return None
    if not valor.strip():
        return None

    prefijo = f"substrn({variable},1,{posicion}-1)"
    if longitud is None:
        ancho = f"lengthc({valor})"
        reemplazo = f"substrn({valor},1,{ancho})"
        sufijo = f"substr({variable},{posicion}+{ancho})"
    else:
        reemplazo = f"substrn({valor} || repeat(' ',{longitud}),1,{longitud})"
        sufijo = f"substr({variable},{posicion}+{longitud})"
    return variable, " || ".join((prefijo, reemplazo, sufijo))


def es_objetivo_substr_izquierda(objetivo: str) -> bool:
    """Indicate that an unrewritten assignment still targets the SUBSTR pseudo-variable form."""
    return _CALL.match(objetivo) is not None
