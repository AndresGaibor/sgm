"""`SELECT (expr); WHEN ...; OTHERWISE ...; END;` y `IF cond THEN DELETE;` del DATA step (B-15).

`SELECT` no es un operador nuevo: se reduce a la cadena `IF / ELSE IF / ELSE` que ya existe
(`lower_data_bloques._como_asignaciones`). SAS evalúa los `WHEN` en orden y ejecuta el primero que
se cumple, igual que la cadena. Sin `OTHERWISE` SAS aborta si ninguna rama se cumple; eso no se
traduce como un valor por omisión, así que la sentencia queda sin traducir y lleva el código
`P-SELECT-SIN-OTHERWISE` (`lestmtsref`, p. 340; ver `select_sin_otherwise`).

`DELETE` condicional es un `filter` con la condición negada. Solo vale si no hay `OUTPUT` antes en
el paso: con `OUTPUT` previo, una fila puede salir varias veces y el filtro no lo representa
(`P-DELETE-CON-OUTPUT`, aún sin código emitido).
"""

from __future__ import annotations

import re

from sgm.frontend.datastep import DsStatement
from sgm.ir.lower_data_bloques import Rama, _como_asignaciones, _rama

_SELECT = re.compile(r"(?is)^select\s*\((.+)\)$")
_WHEN = re.compile(r"(?is)^when\s*\(([^()]*)\)\s*(.+)$")
_OTHERWISE = re.compile(r"(?is)^otherwise\s+(.+)$")
_BORRADO = re.compile(r"(?is)^if\s+(.*?)\s+then\s+delete$")


def _valores_en_condicion(selector: str, valores: str) -> str:
    """`x` y `1, 2` -> `(x = 1) or (x = 2)`: la forma que ya entiende el resto del traductor."""
    return " or ".join(f"({selector} = {v.strip()})" for v in valores.split(","))


def bloque_select(stmts: list[DsStatement], index: int) -> tuple[list[dict], int] | None:
    """Asignaciones de un `SELECT` con `OTHERWISE`, y la sentencia que sigue al `END`."""
    cabecera = _SELECT.fullmatch(stmts[index].text.strip())
    if cabecera is None:
        return None
    selector = cabecera.group(1).strip()
    ramas: list[Rama] = []
    cursor = index + 1
    while cursor < len(stmts):
        texto = stmts[cursor].text.strip()
        when = _WHEN.fullmatch(texto)
        if when is None:
            break
        resultado = _rama(stmts, cursor + 1, when.group(2))
        if resultado is None:
            return None
        asignaciones, cursor = resultado
        ramas.append((_valores_en_condicion(selector, when.group(1)), asignaciones))
    if cursor >= len(stmts):
        return None
    otherwise = _OTHERWISE.fullmatch(stmts[cursor].text.strip())
    if not ramas or otherwise is None:
        return None  # sin WHEN o sin OTHERWISE: SAS aborta, no se inventa el valor
    resultado = _rama(stmts, cursor + 1, otherwise.group(1))
    if resultado is None:
        return None
    por_defecto, cursor = resultado
    if cursor >= len(stmts) or stmts[cursor].kind != "end":
        return None
    ramas.append((None, por_defecto))
    return _como_asignaciones(ramas, cursor + 1)


def select_sin_otherwise(stmts: list[DsStatement], index: int) -> bool:
    """True si `SELECT (expr);` tiene `WHEN` y ninguna rama `OTHERWISE`. Si ningún `WHEN` coincide,
    SAS emite un error y detiene el paso (`lestmtsref`, p. 340): por eso el caso lleva el código
    `P-SELECT-SIN-OTHERWISE` y no se reduce a un `IF` sin `ELSE`."""
    if _SELECT.fullmatch(stmts[index].text.strip()) is None:
        return False
    cursor = index + 1
    hay_when = False
    while cursor < len(stmts):
        when = _WHEN.fullmatch(stmts[cursor].text.strip())
        if when is None:
            break
        resultado = _rama(stmts, cursor + 1, when.group(2))
        if resultado is None:
            return False  # cuerpo que el traductor no entiende: lo decide el camino normal
        hay_when = True
        cursor = resultado[1]
    if not hay_when or cursor >= len(stmts):
        return False
    return _OTHERWISE.fullmatch(stmts[cursor].text.strip()) is None


def condicion_de_borrado(stmts: list[DsStatement], index: int) -> str | None:
    """La condición de `IF cond THEN DELETE;`, o None si la sentencia no es esa."""
    encontrada = _BORRADO.fullmatch(stmts[index].text.strip())
    return encontrada.group(1).strip() if encontrada else None
