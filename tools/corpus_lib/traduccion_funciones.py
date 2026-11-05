"""Reescritura de funciones y opciones de SAS que SQLite no tiene igual (ROUND, OBS=, faltantes).

Cada función reescribe el texto ya protegido y con los nombres de función renombrados. Las
expresiones de los argumentos se reescriben primero, así que los anidamientos funcionan.
"""

from __future__ import annotations

import re
from collections.abc import Callable

from .sql_partes import argumentos
from .traduccion_error import NoSoportado

# Palabras que pueden seguir a `tabla (OBS=n)` y que no son un alias de tabla.
_PALABRAS_NO_ALIAS = (
    "AS|WHERE|LEFT|RIGHT|INNER|FULL|CROSS|OUTER|JOIN|GROUP|ORDER|HAVING|UNION|ON|USING|LIMIT|AND|OR"
)
_OBS = re.compile(
    rf"(?i)\b([A-Za-z_]\w*)\s*\(\s*OBS\s*=\s*(\d+)\s*\)"
    rf"(?:\s+(?:AS\s+)?(?!(?:{_PALABRAS_NO_ALIAS})\b)([A-Za-z_]\w*))?"
)


def expandir_obs(texto: str) -> str:
    """`tabla (OBS=n)` lee solo las n primeras observaciones: `(SELECT * FROM tabla LIMIT n)`.

    Si la tabla lleva alias, se conserva; si no, la subconsulta se llama como la tabla.
    """

    def reemplazo(m: re.Match[str]) -> str:
        tabla, n, alias = m.group(1), m.group(2), m.group(3) or m.group(1)
        return f"(SELECT * FROM {tabla} LIMIT {n}) AS {alias}"

    texto = _OBS.sub(reemplazo, texto)
    if re.search(r"(?i)\bOBS\s*=", texto):
        raise NoSoportado("OBS= fuera de `tabla (OBS=n)` (por ejemplo, con una coma en FROM)")
    return texto


def _reescribir_llamadas(
    texto: str, nombre: str, reescribir: Callable[[list[str]], str]
) -> str:
    """Sustituye cada llamada `nombre(...)` por lo que devuelve `reescribir(argumentos)`."""
    patron = re.compile(rf"(?i)\b{nombre}\s*\(")
    pos = 0
    while True:
        m = patron.search(texto, pos)
        if m is None:
            return texto
        lista, fin = argumentos(texto, m.end())
        lista = [_reescribir_llamadas(arg, nombre, reescribir) for arg in lista]
        reemplazo = reescribir(lista)
        texto = texto[: m.start()] + reemplazo + texto[fin:]
        pos = m.start() + len(reemplazo)


def _round(args: list[str]) -> str:
    """ROUND(x, u): redondea x al múltiplo u, con los empates alejados de cero (como SAS).

    `floor(x/u + 0.5)` se escribe con CAST, que trunca hacia cero: como el valor es no negativo
    (la rama negativa usa -x), trunca igual que floor. `round(..., 10)` quita el error de coma
    flotante (12.345 / 0.01 da 1234.4999999999998) antes de sumar 0.5.
    """
    if len(args) == 1:
        x, unidad = args[0], "1"
    elif len(args) == 2:
        x, unidad = args
    else:
        raise NoSoportado("ROUND con más de dos argumentos")
    return (
        f"round((CASE WHEN ({x}) >= 0 THEN CAST(round(({x}) / ({unidad}), 10) + 0.5 AS INTEGER) "
        f"ELSE -CAST(round(-({x}) / ({unidad}), 10) + 0.5 AS INTEGER) END) * ({unidad}), 10)"
    )


def _coalesce(args: list[str]) -> str:
    """En SAS un texto en blanco es faltante: COALESCE lo salta. Igual que NULLIF(x, '')."""
    return "coalesce(" + ", ".join(f"NULLIF({arg}, '')" for arg in args) + ")"


def _count(args: list[str]) -> str:
    """COUNT(col) no cuenta faltantes; un texto en blanco tampoco. COUNT(*) queda igual."""
    if len(args) != 1:
        raise NoSoportado("COUNT con un número de argumentos distinto de uno")
    arg = args[0]
    if arg == "*":
        return "count(*)"
    distinto = re.match(r"(?is)DISTINCT\s+(.*)$", arg)
    if distinto:
        return f"count(DISTINCT NULLIF({distinto.group(1)}, ''))"
    return f"count(NULLIF({arg}, ''))"


def expandir_funciones(texto: str) -> str:
    """Aplica ROUND, COALESCE y COUNT a todas sus llamadas, con el tratamiento de blancos SAS."""
    texto = _reescribir_llamadas(texto, "round", _round)
    texto = _reescribir_llamadas(texto, "coalesce", _coalesce)
    return _reescribir_llamadas(texto, "count", _count)
