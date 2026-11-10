"""Validación conservadora de expresiones Java antes de insertarlas en un Job."""

from __future__ import annotations

import re

_UNICODE_ESCAPE = re.compile(r"\\u+([0-9a-fA-F]{4})")


def _rangos_cadenas(expression: str) -> list[tuple[int, int]] | None:
    rangos: list[tuple[int, int]] = []
    indice = 0
    while indice < len(expression):
        if expression[indice] not in "\"'":
            indice += 1
            continue
        quote = expression[indice]
        inicio = indice
        indice += 1
        while indice < len(expression):
            if expression[indice] in "\r\n":
                return None
            if expression[indice] == "\\":
                indice += 2
                continue
            if expression[indice] == quote:
                indice += 1
                rangos.append((inicio, indice))
                break
            indice += 1
        else:
            return None
    return rangos


def _en_rango(indice: int, rangos: list[tuple[int, int]]) -> bool:
    return any(inicio <= indice < fin for inicio, fin in rangos)


def _elegible_unicode_escape(expression: str, indice: int) -> bool:
    """Aplica la paridad de barras para distinguir `\\u` activo del escapado."""
    barras = 0
    indice -= 1
    while indice >= 0 and expression[indice] == "\\":
        barras += 1
        indice -= 1
    return barras % 2 == 0


def is_safe_java_expression(expression: str) -> bool:
    """Rechaza separadores, comentarios y escapes Unicode que puedan crear tokens Java."""
    rangos = _rangos_cadenas(expression)
    if rangos is None:
        return False
    for match in _UNICODE_ESCAPE.finditer(expression):
        if not _elegible_unicode_escape(expression, match.start()):
            continue
        codepoint = int(match.group(1), 16)
        # Java traduce escapes Unicode antes de reconocer cadenas y comentarios.
        if codepoint < 128 or not _en_rango(match.start(), rangos):
            return False
    codigo = list(expression)
    for inicio, fin in rangos:
        codigo[inicio:fin] = " " * (fin - inicio)
    exterior = "".join(codigo)
    return not any(caracter in exterior for caracter in ";{}\r\n") and not any(
        comentario in exterior for comentario in ("//", "/*", "*/")
    )


__all__ = ["is_safe_java_expression"]
