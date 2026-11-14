"""Funciones de fecha con equivalencia SAS conservadora para el traductor Talend."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sgm.expressions.talend_parser import _P

from sgm.expressions.talend_base import _UNIT, E, Unsupported, _guard, _need, _num
from sgm.expressions.talend_intnx import _intnx as _intnx

_EPOCA_JAVA = 'TalendDate.parseDate("yyyy-MM-dd", "1960-01-01")'


def _numero_a_fecha(argumento: E, divisor: int = 1) -> str:
    """Lleva un día SAS o segundos SAS a `Date`, con rango y faltante protegidos."""
    numero = _num(argumento)
    dias = f"Math.floor(({numero}) / {divisor}.0)"
    valido = (
        f"Double.isFinite({numero}) && {dias} >= Integer.MIN_VALUE "
        f"&& {dias} <= Integer.MAX_VALUE"
    )
    return (
        f"(({valido}) ? TalendDate.addDate({_EPOCA_JAVA}, "
        f"(int) ({dias}), \"dd\") : null)"
    )


def _fecha_java(argumento: E, nombre: str, *, segundos: bool = False) -> str:
    if argumento.kind == "null":
        return "null"
    if argumento.kind in {"str", "bool", "omitted"}:
        raise Unsupported(f"{nombre} requiere una fecha SAS numérica")
    if argumento.kind in {"num", "any"}:
        return _numero_a_fecha(argumento, 86400 if segundos else 1)
    return argumento.java


def _mdy(_p: _P, args: list[E]) -> E:
    _need(args, 3, 3, "mdy")
    if any(arg.kind in {"str", "date", "bool"} for arg in args):
        raise Unsupported("mdy requiere argumentos numéricos")
    if any(arg.kind == "null" for arg in args):
        return E("null", "date")
    month, day, year = (_num(arg) for arg in args)
    if args[2].kind != "num":
        raise Unsupported("Pendiente: P-YEARCUTOFF-EXPLICITO (año MDY dinámico)")
    try:
        anio_literal = Decimal(args[2].literal or "")
    except InvalidOperation as error:
        raise Unsupported("mdy requiere un año literal entero de cuatro dígitos") from error
    if anio_literal == anio_literal.to_integral_value():
        anio = int(anio_literal)
        if 0 <= anio < 100:
            raise Unsupported("Pendiente: P-YEARCUTOFF-EXPLICITO")
        if 100 <= anio < 1000:
            raise Unsupported("Pendiente: P-MDY-ANIO-3-CIFRAS")
        if anio < 0 or anio > 9999:
            raise Unsupported("Pendiente: P-MDY-ANIO-FUERA-DE-RANGO")
    fecha_texto = (
        'String.format(java.util.Locale.ROOT, "%04d-%02d-%02d", '
        f"(int) ({year}), (int) ({month}), (int) ({day}))"
    )
    valida = (
        f"Double.isFinite({month}) && {month} == Math.rint({month})"
        f" && Double.isFinite({day}) && {day} == Math.rint({day})"
        f" && Double.isFinite({year}) && {year} == Math.rint({year})"
    )
    parseada = f'TalendDate.parseDate("yyyy-MM-dd", {fecha_texto})'
    calendario_valido = (
        f"({parseada} != null && {fecha_texto}.equals("
        f'TalendDate.formatDate("yyyy-MM-dd", {parseada})))'
    )
    return E(_guard(args, f"(({valida}) && {calendario_valido} ? {parseada} : null)"), "date")


def _datepart(_p: _P, args: list[E]) -> E:
    _need(args, 1, 1, "datepart")
    argumento = args[0]
    fecha = _fecha_java(
        argumento, "datepart", segundos=argumento.kind in {"num", "any"}
    )
    normalizada = (
        f'({fecha} == null ? null : TalendDate.parseDate("yyyy-MM-dd", '
        f'TalendDate.formatDate("yyyy-MM-dd", {fecha})))'
    )
    return E(_guard(args, normalizada), "date")


def _part(name: str):
    def build(_p: _P, args: list[E]) -> E:
        _need(args, 1, 1, name)
        argumento = args[0]
        fecha = _fecha_java(argumento, name)
        if name == "qtr":
            part = f'(TalendDate.getPartOfDate("MONTH", {fecha}) / 3 + 1)'
        else:
            part_name = {"year": "YEAR", "month": "MONTH", "day": "DAY_OF_MONTH", "weekday": "DAY_OF_WEEK"}[name]
            incremento = " + 1" if name == "month" else ""
            part = f'(TalendDate.getPartOfDate("{part_name}", {fecha}){incremento})'
        return E(f"({fecha} == null ? null : {part})", "num")

    return build


def _today(name: str):
    def build(p: _P, args: list[E]) -> E:
        _need(args, 0, 0, name)
        p.warnings.add(
            f"{name}(): validar que la zona horaria del Job coincida con TIMEZONE= de SAS"
        )
        value = (
            'TalendDate.parseDate("yyyy-MM-dd", '
            'TalendDate.formatDate("yyyy-MM-dd", TalendDate.getCurrentDate()))'
        )
        return E(value, "date")

    return build


def _sas_date_number(argumento: E) -> str:
    """Convierte un `Date` Talend al número de días SAS."""
    return f'TalendDate.diffDate({argumento.java}, {_EPOCA_JAVA}, "dd")'


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
