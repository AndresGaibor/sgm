"""Funciones auxiliares del expansor de macros: cálculo entero de %eval y partición de argumentos.

Son puras: no tocan el estado del expansor. Ver `expansor_macros.py`.
"""

from __future__ import annotations

import ast
import re


class ErrorMacro(ValueError):
    """Macro que no se puede expandir: construcción no soportada, variable o macro no definida."""


def _entero_seguro(nodo: ast.AST) -> int:
    """Evalúa una expresión de enteros con `+`, `-` y `*` (y paréntesis). Otra cosa falla."""
    if isinstance(nodo, ast.Constant) and isinstance(nodo.value, int):
        return nodo.value
    if isinstance(nodo, ast.BinOp) and isinstance(nodo.op, (ast.Add, ast.Sub, ast.Mult)):
        izquierda = _entero_seguro(nodo.left)
        derecha = _entero_seguro(nodo.right)
        if isinstance(nodo.op, ast.Add):
            return izquierda + derecha
        if isinstance(nodo.op, ast.Sub):
            return izquierda - derecha
        return izquierda * derecha
    raise ErrorMacro("%eval con una operación no permitida")


def _argumento(texto: str) -> object:
    return int(texto) if re.fullmatch(r"\d+", texto) else texto


def _partir(texto: str) -> list[str]:
    """Parte los argumentos por comas que no están dentro de paréntesis."""
    if not texto.strip():
        return []
    partes: list[str] = []
    actual, profundidad = "", 0
    for c in texto:
        if c == "(":
            profundidad += 1
        elif c == ")":
            profundidad -= 1
        if c == "," and profundidad == 0:
            partes.append(actual)
            actual = ""
        else:
            actual += c
    partes.append(actual)
    return partes
