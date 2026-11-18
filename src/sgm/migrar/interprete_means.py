"""Exclusión tipada de faltantes CLASS de MEANS/SUMMARY (proc.pdf, p. 1571)."""

from __future__ import annotations

import re

from sqlglot import exp

from sgm.ir.lower_procs_agregados import NUMERIC_TYPES, class_type
from sgm.ir.models import Operator, Plan
from sgm.migrar.interprete_valores import NoSoportadoEnInterprete, _arbol, _columna

_SPECIAL_MISSING = re.compile(r"\.[a-z_]?", re.I)


def exclude_special_class_missing(
    rows: list[dict], expression: str, operator: Operator, plan: Plan,
) -> list[dict]:
    """`.A` se excluye solo con tipo numérico probado; como carácter es texto válido.

    Una representación especial sin tipo no demuestra si es texto o missing numérico. Ese caso
    queda pendiente; no se deduce el tipo a partir del valor ni del nombre de CLASS.
    """
    names = {column.name for column in _arbol(expression).find_all(exp.Column)}
    types = {name: class_type(plan.graph, operator, name) for name in names}
    result = []
    for row in rows:
        missing = False
        for name, column_type in types.items():
            value = _columna(row, name)
            if not isinstance(value, str) or not _SPECIAL_MISSING.fullmatch(value.strip()):
                continue
            if column_type in NUMERIC_TYPES:
                missing = True
            elif column_type != "String":
                raise NoSoportadoEnInterprete(
                    "filter", "Pendiente: P-MEANS-CLASS-TIPO-NO-DEMOSTRADO; "
                    f"CLASS {name} contiene {value!r} sin tipo numérico o carácter demostrado",
                )
        if not missing:
            result.append(row)
    return result
