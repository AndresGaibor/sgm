"""Utilidades para leer SQL por niveles de paréntesis, sin tocar cadenas ni comentarios.

Las cadenas ya están protegidas por marcadores antes de llegar aquí (ver `traduccion_sql.py`), así
que una coma o un paréntesis dentro de un texto no cuenta.
"""

from __future__ import annotations

import re

from .traduccion_error import NoSoportado


def profundidades(texto: str) -> list[int]:
    """Nivel de paréntesis en el que está cada carácter (0 = fuera de cualquier paréntesis)."""
    niveles: list[int] = []
    nivel = 0
    for caracter in texto:
        if caracter == ")":
            nivel -= 1
        niveles.append(nivel)
        if caracter == "(":
            nivel += 1
    return niveles


def buscar_fuera_de_parentesis(texto: str, patron: re.Pattern[str]) -> list[re.Match[str]]:
    """Coincidencias de `patron` que empiezan fuera de cualquier paréntesis."""
    niveles = profundidades(texto)
    return [m for m in patron.finditer(texto) if niveles[m.start()] == 0]


def dividir_fuera_de_parentesis(texto: str, separador: str = ",") -> list[str]:
    """Parte el texto por el separador, sin cortar dentro de paréntesis. Quita blancos sobrantes."""
    partes: list[str] = []
    nivel = 0
    inicio = 0
    for i, caracter in enumerate(texto):
        if caracter == "(":
            nivel += 1
        elif caracter == ")":
            nivel -= 1
        elif caracter == separador and nivel == 0:
            partes.append(texto[inicio:i].strip())
            inicio = i + 1
    partes.append(texto[inicio:].strip())
    return partes


def argumentos(texto: str, inicio: int) -> tuple[list[str], int]:
    """Argumentos de una llamada cuyo `(` ya se leyó; `inicio` es la posición después de él.

    Devuelve (argumentos, posición justo después del `)` de cierre).
    """
    nivel = 0
    for i in range(inicio, len(texto)):
        caracter = texto[i]
        if caracter == "(":
            nivel += 1
        elif caracter == ")":
            if nivel == 0:
                cuerpo = texto[inicio:i].strip()
                lista = dividir_fuera_de_parentesis(cuerpo) if cuerpo else []
                return lista, i + 1
            nivel -= 1
    raise NoSoportado("paréntesis sin cerrar en una llamada de función")
