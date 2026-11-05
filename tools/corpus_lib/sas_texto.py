"""Partición de texto SAS en comentarios, cadenas, sentencias y bloques de PROC SQL.

El recorrido es carácter a carácter para que un `;`, un `/*` o un `QUIT;` dentro de una cadena
o de un comentario no se confundan con código.
"""

from __future__ import annotations

import re


class ErrorSas(ValueError):
    """Texto SAS que no se puede partir, por ejemplo una cadena o un comentario sin cerrar."""


def segmentos(texto: str) -> list[tuple[str, str]]:
    """Parte el texto en trozos (tipo, contenido); tipo es 'codigo', 'cadena' o 'comentario'."""
    resultado: list[tuple[str, str]] = []
    inicio = 0  # comienzo del trozo de código que aún no se ha agregado
    i = 0
    while i < len(texto):
        if texto.startswith("/*", i):
            fin = texto.find("*/", i + 2)
            if fin < 0:
                raise ErrorSas("comentario /* sin cerrar")
            _agregar_codigo(resultado, texto[inicio:i])
            resultado.append(("comentario", texto[i : fin + 2]))
            i = inicio = fin + 2
        elif texto[i] in "'\"":
            fin = _cierre_cadena(texto, i)
            _agregar_codigo(resultado, texto[inicio:i])
            resultado.append(("cadena", texto[i : fin + 1]))
            i = inicio = fin + 1
        else:
            i += 1
    _agregar_codigo(resultado, texto[inicio:])
    return resultado


def _agregar_codigo(resultado: list[tuple[str, str]], trozo: str) -> None:
    if trozo:
        resultado.append(("codigo", trozo))


def _cierre_cadena(texto: str, inicio: int) -> int:
    """Devuelve la posición de la comilla que cierra la cadena. Una comilla repetida se escapa."""
    comilla = texto[inicio]
    j = inicio + 1
    while j < len(texto):
        if texto[j] == comilla:
            if j + 1 < len(texto) and texto[j + 1] == comilla:
                j += 2
                continue
            return j
        j += 1
    raise ErrorSas("cadena sin cerrar")


def sentencias(texto: str) -> list[str]:
    """Parte el texto en sentencias terminadas en `;`, sin comentarios y sin el `;` final."""
    resultado: list[str] = []
    actual: list[str] = []
    for tipo, trozo in segmentos(texto):
        if tipo == "comentario":
            actual.append(" ")
        elif tipo == "cadena":
            actual.append(trozo)
        else:
            partes = trozo.split(";")
            actual.append(partes[0])
            for parte in partes[1:]:
                _cerrar(actual, resultado)
                actual.append(parte)
    _cerrar(actual, resultado)
    return resultado


def _cerrar(actual: list[str], resultado: list[str]) -> None:
    sentencia = "".join(actual).strip()
    if sentencia:
        resultado.append(sentencia)
    actual.clear()


_INICIO_PROC_SQL = re.compile(r"PROC\s+SQL\b", re.IGNORECASE)
_FIN_PROC_SQL = re.compile(r"QUIT\b", re.IGNORECASE)
_OTRO_PASO = re.compile(r"(PROC|DATA)\b", re.IGNORECASE)


def sentencias_proc_sql(texto: str) -> list[str]:
    """Devuelve, en orden, las sentencias que están entre `PROC SQL;` y `QUIT;`."""
    dentro = False
    bloque: list[str] = []
    for sentencia in sentencias(texto):
        if _INICIO_PROC_SQL.match(sentencia):
            if dentro:
                raise ErrorSas("PROC SQL dentro de otro PROC SQL sin QUIT")
            dentro = True
            continue
        if not dentro:
            continue
        if _FIN_PROC_SQL.match(sentencia):
            dentro = False
            continue
        if _OTRO_PASO.match(sentencia):
            raise ErrorSas("PROC o DATA dentro de PROC SQL sin QUIT")
        bloque.append(sentencia)
    if dentro:
        raise ErrorSas("PROC SQL sin QUIT")
    return bloque
