"""Funciones de fechas y conversiones literales para Talend."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sgm.expressions.talend_parser import ExpressionParser as _P

import re

from sgm.expressions.talend_core import E, Unsupported, _guard, _jstr, _need, _num

DATE_FORMATS = {
    "yymmdd10": "yyyy-MM-dd", "yymmdd8": "yy-MM-dd", "yymmddn8": "yyyyMMdd", "ddmmyy10": "dd/MM/yyyy",
    "ddmmyy8": "dd/MM/yy", "mmddyy10": "MM/dd/yyyy", "mmddyy8": "MM/dd/yy", "date9": "ddMMMyyyy",
    "date7": "ddMMMyy", "datetime20": "ddMMMyyyy:HH:mm:ss", "datetime19": "ddMMMyyyy:HH:mm:ss",
    "e8601da": "yyyy-MM-dd", "e8601dt": "yyyy-MM-dd'T'HH:mm:ss", "monyy7": "MMMyyyy", "year4": "yyyy",
    "mmyy": "MM/yyyy", "yymmn6": "yyyyMM", "ddmmyyn8": "ddMMyyyy",
}  # fmt: skip
_UNIT = {
    "day": "dd",
    "month": "MM",
    "year": "yyyy",
    "week": "dd",
    "hour": "HH",
    "minute": "mm",
    "second": "ss",
}
_PART = {"year": "YEAR", "month": "MONTH", "day": "DAY_OF_MONTH", "weekday": "DAY_OF_WEEK"}


def _date_pattern(fmt: str) -> str | None:
    return DATE_FORMATS.get(fmt.lower().strip(".$'\"").rstrip("."))


def _input(p: _P, args: list[E]) -> E:
    _need(args, 2, 2, "input")
    fmt = args[1].java.strip("\"'").lower().rstrip(".")
    pattern = _date_pattern(fmt)
    if pattern:
        return E(
            f"TalendDate.parseDate({_jstr(chr(39) + pattern + chr(39))}, {args[0].java})", "date"
        )
    if fmt.startswith(("$", "char")):
        return E(args[0].java, "str")
    p.warnings.add(
        "input numérico: el valor se convierte con Mathematical.REAL; comprobar el informato"
    )
    return E(_guard(args[:1], f"Mathematical.REAL(StringHandling.TRIM({args[0].java}))"))


def _put(p: _P, args: list[E]) -> E:
    _need(args, 2, 2, "put")
    fmt = args[1].java.strip("\"'").lower().rstrip(".")
    pattern = _date_pattern(fmt)
    if pattern:
        return E(
            f"TalendDate.formatDate({_jstr(chr(39) + pattern + chr(39))}, {args[0].java})", "str"
        )
    zero = re.fullmatch(r"z(\d+)", fmt)
    if zero:
        return E(
            f'StringHandling.LPAD(String.valueOf({args[0].java}), {zero.group(1)}, "0")', "str"
        )
    if re.fullmatch(r"\$?\d*", fmt) or fmt.startswith("$"):
        return E(f"String.valueOf({args[0].java})", "str")
    raise Unsupported(f"put con el formato {fmt}.")


def _intnx(_p: _P, args: list[E]) -> E:
    _need(args, 3, 4, "intnx")
    unit_arg, d, n = args[0], args[1], args[2]
    unit = unit_arg.java.strip('"').lower()
    if unit_arg.kind != "str" or unit not in _UNIT:
        raise Unsupported("intnx con un intervalo que no es literal o no está soportado")
    count = f"(int) ({_num(n)} * 7)" if unit == "week" else f"(int) {_num(n)}"
    moved = f'TalendDate.addDate({d.java}, {count}, "{_UNIT[unit]}")'
    align = args[3].java.strip('"').lower() if len(args) == 4 else "b"
    if unit == "month" and align == "e":
        moved = f"TalendDate.getLastDayOfMonth({moved})"
    elif unit == "month" and align == "b":
        moved = f"TalendDate.getFirstDayOfMonth({moved})"
    return E(_guard([d], moved), "date")


def _intck(_p: _P, args: list[E]) -> E:
    _need(args, 3, 3, "intck")
    unit = args[0].java.strip('"').lower()
    if args[0].kind != "str" or unit not in _UNIT:
        raise Unsupported("intck con un intervalo que no es literal o no está soportado")
    return E(
        _guard(
            args[1:],
            f'Long.valueOf(TalendDate.diffDate({args[2].java}, {args[1].java}, "{_UNIT[unit]}"))',
        )
    )


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
