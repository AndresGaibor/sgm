"""Exclusión tipada de faltantes CLASS de MEANS/SUMMARY (proc.pdf, p. 1571)."""

from __future__ import annotations

import re

from sqlglot import exp

from sgm.ir.models import Operator, Plan
from sgm.migrar.interprete_valores import NoSoportadoEnInterprete, _arbol, _columna

_SPECIAL_MISSING = re.compile(r"\.[a-z_]?", re.I)
_NUMERIC = frozenset({"Double", "Float", "BigDecimal", "Long", "Integer", "Short", "Byte"})
_TRANSPARENT = frozenset({"read", "filter", "sort", "dedup", "write"})


def _class_type(plan: Plan, operator: Operator, name: str, seen: frozenset[str]) -> str | None:
    """Busca un tipo demostrado, sin atravesar transformaciones de esquema desconocidas."""
    if operator.id in seen:
        return None
    for column in operator.schema or []:
        if column.name.casefold() == name.casefold():
            return column.type if column.source in {"catalog", "code"} else None
    if operator.kind not in _TRANSPARENT:
        return None
    parents = plan.graph.predecessors(operator.id)
    types = {
        _class_type(plan, plan.graph.operator(parent), name, seen | {operator.id})
        for parent in parents
    }
    return types.pop() if len(types) == 1 else None


def exclude_special_class_missing(
    rows: list[dict], expression: str, operator: Operator, plan: Plan,
) -> list[dict]:
    """`.A` se excluye solo con tipo numérico probado; como carácter es texto válido.

    Una representación especial sin tipo no demuestra si es texto o missing numérico. Ese caso
    queda pendiente; no se deduce el tipo a partir del valor ni del nombre de CLASS.
    """
    names = {column.name for column in _arbol(expression).find_all(exp.Column)}
    types = {name: _class_type(plan, operator, name, frozenset()) for name in names}
    result = []
    for row in rows:
        missing = False
        for name, column_type in types.items():
            value = _columna(row, name)
            if not isinstance(value, str) or not _SPECIAL_MISSING.fullmatch(value.strip()):
                continue
            if column_type in _NUMERIC:
                missing = True
            elif column_type != "String":
                raise NoSoportadoEnInterprete(
                    "filter", "Pendiente: P-MEANS-CLASS-TIPO-NO-DEMOSTRADO; "
                    f"CLASS {name} contiene {value!r} sin tipo numérico o carácter demostrado",
                )
        if not missing:
            result.append(row)
    return result
