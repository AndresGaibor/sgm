"""Funciones de fecha con equivalencia SAS conservadora para el traductor Talend."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sgm.expressions.talend_parser import _P

from sgm.expressions.talend_base import _UNIT, E, Unsupported, _guard, _need, _num

_COLUMN = re.compile(r"[A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)+")


def _literal_increment_is_integer(value: str) -> bool:
    try:
        number = Decimal(value)
    except InvalidOperation:
        return False
    return number.is_finite() and number == number.to_integral_value()


def _intnx(_p: _P, args: list[E]) -> E:
    _need(args, 3, 4, "intnx")
    unit_arg, date_value, increment = args[:3]
    unit = unit_arg.literal.lower() if unit_arg.literal is not None else ""
    if unit_arg.kind != "str" or unit not in _UNIT:
        raise Unsupported("intnx con un intervalo no literal o no soportado; queda pendiente")
    if unit in {"hour", "minute", "second"}:
        raise Unsupported("intnx de hora requiere tipo SAS Time/DateTime explícito; queda pendiente")
    if date_value.kind not in {"date", "any"}:
        raise Unsupported("intnx requiere un valor SAS Date; queda pendiente")
    if increment.kind not in {"num", "any"}:
        raise Unsupported("intnx requiere un incremento numérico; queda pendiente")
    interval_multiplier = 7 if unit == "week" else 1
    if increment.kind == "num":
        if not _literal_increment_is_integer(increment.java.strip()):
            raise Unsupported(
                "intnx requiere un incremento entero literal o columna numérica; queda pendiente"
            )
        try:
            number = Decimal(increment.java.strip()) * interval_multiplier
            if not Decimal(-(2**31)) <= number < Decimal(2**31):
                raise Unsupported("intnx excede el rango entero de Talend; queda pendiente")
        except InvalidOperation as exc:
            raise Unsupported("intnx requiere un incremento entero literal") from exc
    elif not _COLUMN.fullmatch(increment.java.strip()):
        raise Unsupported("intnx requiere una columna numérica directa; queda pendiente")

    if len(args) == 4 and args[3].kind != "str":
        raise Unsupported("intnx con alineación dinámica; queda pendiente de resolución")
    alignment = args[3].literal.lower() if len(args) == 4 else "b"
    alignment = {
        "beginning": "b",
        "middle": "m",
        "end": "e",
        "same": "s",
        "sameday": "s",
    }.get(alignment, alignment)
    if alignment not in {"b", "m", "e", "s"}:
        raise Unsupported("intnx con alineación no soportada")

    if unit in {"month", "year"}:
        if alignment == "m":
            raise Unsupported("intnx con alineación MIDDLE; queda pendiente su semántica de fecha")
        code = "MM" if unit == "month" else "yyyy"
        moved = f'TalendDate.addDate({date_value.java}, (int) {_num(increment)}, "{code}")'
        if unit == "month" and alignment == "b":
            moved = f"TalendDate.getFirstDayOfMonth({moved})"
        elif unit == "month" and alignment == "e":
            moved = f"TalendDate.getLastDayOfMonth({moved})"
        elif unit == "year" and alignment in {"b", "e"}:
            suffix = "-01-01" if alignment == "b" else "-12-31"
            moved = (
                'TalendDate.parseDate("yyyy-MM-dd", '
                f'TalendDate.formatDate("yyyy", {moved}) + "{suffix}")'
            )
    elif unit == "week":
        if alignment != "s":
            raise Unsupported("intnx WEEK requiere WEEKSTART y alineación de límites; queda pendiente")
        moved = f'TalendDate.addDate({date_value.java}, (int) ({_num(increment)} * 7), "dd")'
    elif unit == "day":
        if alignment not in {"b", "e", "s"}:
            raise Unsupported("intnx DAY con alineación MIDDLE queda pendiente")
        moved = f'TalendDate.addDate({date_value.java}, (int) {_num(increment)}, "dd")'
    else:
        raise Unsupported("intnx requiere un intervalo de fecha soportado")

    guarded = _guard([date_value, increment], moved)
    if increment.kind == "any":
        numeric_value = _num(increment)
        if interval_multiplier == 7:
            lower_bound = "(Integer.MIN_VALUE / 7.0)"
            upper_bound = "(Integer.MAX_VALUE / 7.0)"
        else:
            lower_bound = "Integer.MIN_VALUE"
            upper_bound = "Integer.MAX_VALUE"
        in_range = f"({numeric_value} >= {lower_bound} && {numeric_value} <= {upper_bound})"
        is_integer = f"Double.isFinite({numeric_value}) && {numeric_value} == Math.rint({numeric_value})"
        guarded = _guard(
            [date_value, increment],
            f"(({in_range}) && ({is_integer}) ? {moved} : null)",
        )
    _p.warnings.add(
        "intnx requiere valores SAS Date compatibles; validar época SAS (1960), incremento entero y resultados en Studio"
    )
    return E(guarded, "date")


def _intck(_p: _P, args: list[E]) -> E:
    if len(args) == 4:
        method = args[3]
        value = method.literal.lower() if method.literal is not None else ""
        if method.kind != "str" or value not in {"discrete", "d", "disc"}:
            raise Unsupported("intck con método no discreto o dinámico; queda pendiente")
        args = args[:3]
    _need(args, 3, 3, "intck")
    unit_arg, start, end = args
    unit = unit_arg.literal.lower() if unit_arg.literal is not None else ""
    if unit_arg.kind != "str" or unit not in _UNIT:
        raise Unsupported("intck con un intervalo que no es literal o no está soportado")
    if start.kind not in {"date", "any"} or end.kind not in {"date", "any"}:
        raise Unsupported("intck requiere valores SAS Date; queda pendiente")
    if unit == "year":
        years = (
            f'TalendDate.getPartOfDate("YEAR", {end.java}) - '
            f'TalendDate.getPartOfDate("YEAR", {start.java})'
        )
        result = f"Long.valueOf({years})"
    elif unit == "month":
        year_delta = (
            f'TalendDate.getPartOfDate("YEAR", {end.java}) - '
            f'TalendDate.getPartOfDate("YEAR", {start.java})'
        )
        month_delta = (
            f'TalendDate.getPartOfDate("MONTH", {end.java}) - '
            f'TalendDate.getPartOfDate("MONTH", {start.java})'
        )
        result = f"Long.valueOf(({year_delta}) * 12 + ({month_delta}))"
    elif unit == "day":
        result = f'TalendDate.diffDate({end.java}, {start.java}, "dd")'
    else:
        raise Unsupported(
            f"intck {unit.upper()} requiere conteo de límites y tipo temporal confirmado; queda pendiente"
        )
    _p.warnings.add(
        "intck asume intervalos SAS Date discretos; validar época SAS (1960), tipos y semántica en Studio"
    )
    return E(_guard([start, end], result), "num")
