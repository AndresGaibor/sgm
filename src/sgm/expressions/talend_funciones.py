"""Adaptadores de rutinas Talend con firma compatible con el analizador."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sgm.expressions.talend_parser import _P

from sgm.expressions.talend_base import E, _need


def _routine(routine: str, method: str, arity: int | None = None):
    def build(_p: _P, args: list[E]) -> E:
        _need(args, arity or len(args), arity or len(args), method)
        return E(f"{routine}.{method}({', '.join(a.java for a in args)})")

    return build
