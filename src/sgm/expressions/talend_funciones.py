"""Adaptador de rutinas y funciones de fecha simples del traductor Talend."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sgm.expressions.talend_parser import _P

from sgm.expressions.talend_base import _PART, E, _guard, _need, _num


def _routine(routine: str, method: str, arity: int | None = None):
    def build(_p: _P, args: list[E]) -> E:
        _need(args, arity or len(args), arity or len(args), method)
        return E(f"{routine}.{method}({', '.join(a.java for a in args)})")

    return build


def _part(name: str):
    def build(_p: _P, args: list[E]) -> E:
        _need(args, 1, 1, name)
        inc = " + 1" if name == "month" else ""
        return E(_guard(args, f'(TalendDate.getPartOfDate("{_PART[name]}", {args[0].java}){inc})'))

    return build


def _mdy(_p: _P, args: list[E]) -> E:
    _need(args, 3, 3, "mdy")
    m, d, y = args
    text = f'String.format("%04d-%02d-%02d", (int) {_num(y)}, (int) {_num(m)}, (int) {_num(d)})'
    return E(_guard(args, f'TalendDate.parseDate("yyyy-MM-dd", {text})'), "date")


def _datepart(_p: _P, args: list[E]) -> E:
    _need(args, 1, 1, "datepart")
    return E(
        _guard(
            args,
            f'TalendDate.parseDate("yyyy-MM-dd", TalendDate.formatDate("yyyy-MM-dd", {args[0].java}))',
        ),
        "date",
    )
