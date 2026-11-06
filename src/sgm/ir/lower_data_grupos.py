"""DATA step con `BY` y estado entre filas: `FIRST.`, `LAST.`, `RETAIN` y la sentencia de suma.

SAS lee la tabla fila a fila y lleva un vector de datos (PDV): lo que una fila asigna a una variable
retenida lo ve la siguiente. Eso no es una expresión sobre una fila, es un **programa por fila** con
estado, y se guarda tal cual en un operador `stateful_row`:

* `retain`: variables que conservan su valor entre filas, con su valor inicial si lo hay.
* `asigna`: `x = expr`.
* `si`: `IF cond THEN x = expr`.
* `suma`: `x + expr`, que retiene `x` (empieza en 0) y suma ignorando el faltante.
* `filtra`: `IF cond;` sin `THEN`, que descarta la fila (el estado se actualiza igual).

`FIRST.v` y `LAST.v` valen 1 en la primera y en la última fila de cada grupo de `BY`, y se escriben
en las condiciones y expresiones como en el SAS. La entrada ya viene ordenada por la llave, como
exige el `BY`.

Si el paso trae algo que este modelo no cubre (un `IF` con `ELSE` o con `DO`, `OUTPUT` explícito,
`KEEP`...), se devuelve `None` y el paso sigue el camino de siempre, con su nota.
"""

from __future__ import annotations

import re

from sgm.frontend.datastep import DsStatement

_CABECERA = frozenset({"set", "merge", "by", "declare"})
_SUMA = re.compile(r"(?is)^(\w+)\s*\+\s*(.+)$")
_SI = re.compile(r"(?is)^if\s+(.*?)\s+then\s+(\w+)\s*=\s*(.+)$")
_FILTRA = re.compile(r"(?is)^if\s+(.+)$")
_INICIAL = re.compile(r"""(?is)^\s*(-?\d+(?:\.\d+)?|'[^']*'|"[^"]*")\s*$""")


def _retain(texto: str) -> dict | None:
    """`RETAIN a b 0` -> nombres y valor inicial. Un valor suelto al final vale para todos."""
    resto = re.sub(r"(?is)^retain\s+", "", texto.strip())
    partes = resto.split()
    inicial = None
    if partes and _INICIAL.match(partes[-1]):
        inicial = partes.pop()
    if not partes or not all(re.fullmatch(r"\w+", p) for p in partes):
        return None
    return {"op": "retain", "names": [p.lower() for p in partes], "valor": inicial}


def programa_por_grupo(stmts: list[DsStatement]) -> dict | None:
    """Parámetros del `stateful_row` de un DATA step con `BY`, o `None` si no es de esta clase."""
    por = next((s for s in stmts if s.kind == "by"), None)
    if por is None:
        return None
    programa: list[dict] = []
    estado = False  # hay algo que necesita estado entre filas o saber el límite del grupo
    for s in stmts:
        texto = s.text.strip()
        if s.kind in _CABECERA:
            continue
        if s.kind == "retain":
            retencion = _retain(texto)
            if retencion is None:
                return None
            programa.append(retencion)
            estado = True
        elif s.kind == "assign":
            programa.append(
                {
                    "op": "asigna",
                    "target": s.fields["target"].lower(),
                    "expr": s.fields["expression"],
                }
            )
        elif s.kind == "if":
            con_si = _SI.fullmatch(texto)
            if con_si:
                programa.append(
                    {
                        "op": "si",
                        "cond": con_si.group(1).strip(),
                        "target": con_si.group(2).lower(),
                        "expr": con_si.group(3).strip(),
                    }
                )
            elif re.search(r"(?i)\bthen\b|^else\b", texto) or not _FILTRA.fullmatch(texto):
                return None
            else:
                programa.append({"op": "filtra", "cond": _FILTRA.fullmatch(texto).group(1).strip()})
            estado = estado or bool(s.fields.get("first_last"))
        elif s.kind == "other" and _SUMA.fullmatch(texto):
            suma = _SUMA.fullmatch(texto)
            programa.append({"op": "suma", "target": suma.group(1).lower(), "expr": suma.group(2)})
            estado = True
        else:
            return None
    if not estado:
        return None
    return {
        "reason": "by_group",
        "by": [n.lower() for n in por.fields["names"]],
        "programa": programa,
    }


__all__ = ["programa_por_grupo"]
