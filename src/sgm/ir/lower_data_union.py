"""Tipo de unión de un MERGE (lrcon, p. 584 y siguientes): `left`, `right`, `inner` o `full`."""

from __future__ import annotations

import re

from sgm.frontend.datastep import DsStatement


def tipo_de_union(stmts: list[DsStatement], refs: list[dict]) -> str | None:
    """Tipo de unión de un MERGE según la primera condición `if`. None si no se puede deducir."""
    conditions = [s for s in stmts if s.kind == "if" and s.text.lower().startswith("if ")]
    if not conditions:
        # MERGE sin condición: une todas las filas por llave. No es un JOIN de producto: el
        # intérprete empareja fila con fila dentro de cada grupo (migrar/interprete.py, _mezclar).
        return "full"
    expr = re.sub(r"(?i)^if\s+", "", conditions[0].text).strip()
    expr = re.sub(r"(?i)\s+then\b.*$", "", expr)
    expr = re.sub(r"\s+", " ", expr).strip().lower()
    if len(refs) < 2:
        return None
    first, second = refs[0].get("in"), refs[1].get("in")
    if not first or not second:
        return None
    if expr in (f"{first} and {second}", f"{second} and {first}"):
        return "inner"
    if expr == first:
        return "left"
    if expr == second:
        return "right"
    if expr in (f"{first} or {second}", f"{second} or {first}"):
        return "full"
    return None
