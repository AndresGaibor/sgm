"""`LAG` y `DIF` del DATA step como estado entre filas (B-13).

Se reconocen dos formas, y solo estas: `x = LAGn(e);` y `IF cond THEN x = DIFn(e);` (también
`LAG`). La expresión tiene que ser exactamente la llamada: `x = LAG(e) + 1;` no entra, y el
paso sigue como antes.

`lefunctionsref`, p. 1164: cada aparición de LAG tiene su cola, y la cola avanza solo cuando la
función se ejecuta. Con `IF` guarda y devuelve valores solo de las observaciones que cumplen la
condición. `DIFn(e) = e - LAGn(e)` (p. 663). Sin emisor en Talend todavía, el operador es un
hueco y el Job no se escribe (decisión 5).
"""

from __future__ import annotations

import re

_CONDICIONAL = re.compile(r"(?is)^if\s+(.+?)\s+then\s+(\w+)\s*=\s*(.+)$")
_ASIGNA = re.compile(r"(?is)^(\w+)\s*=\s*(.+)$")
_LLAMADA = re.compile(r"(?is)^(lag|dif)\d*\s*\(([^()]+)\)$")


def estado_de_lag(texto: str) -> dict | None:
    """Parámetros del operador de estado, o None si la sentencia no tiene una de las formas."""
    cuerpo = texto.strip()
    condicion = None
    if m := _CONDICIONAL.fullmatch(cuerpo):
        condicion, objetivo, expresion = m.group(1).strip(), m.group(2), m.group(3).strip()
    elif m := _ASIGNA.fullmatch(cuerpo):
        objetivo, expresion = m.group(1), m.group(2).strip()
    else:
        return None
    if not _LLAMADA.fullmatch(expresion):
        return None
    return {
        "reason": "lag",
        "target": objetivo,
        "expression": expresion,
        "condition": condicion,
        "codigo": "P-LAG-SIN-EMISOR",
    }
