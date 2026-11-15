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
    elif unit == "qtr":
        q_start = f'(TalendDate.getPartOfDate("MONTH", {start.java}) - 1) / 3'
        q_end = f'(TalendDate.getPartOfDate("MONTH", {end.java}) - 1) / 3'
        year_delta = (
            f'TalendDate.getPartOfDate("YEAR", {end.java}) - '
            f'TalendDate.getPartOfDate("YEAR", {start.java})'
        )
        result = f"Long.valueOf(({year_delta}) * 4 + ({q_end}) - ({q_start}))"
    elif unit == "week":
        def inicio_semana(fecha: str) -> str:
            dias = f'TalendDate.diffDate({fecha}, {_EPOCA_JAVA}, "dd")'
            domingo_cero = f'(TalendDate.getPartOfDate("DAY_OF_WEEK", {fecha}) - 1)'
            return f"(({dias}) - ({domingo_cero}))"

        inicio_fin = inicio_semana(end.java)
        inicio_inicio = inicio_semana(start.java)
        result = f"Long.valueOf((({inicio_fin}) - ({inicio_inicio})) / 7)"
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


def _base_literal(argumento: E, nombre: str) -> str:
    if argumento.kind != "str" or argumento.literal is None:
        raise Unsupported(f"{nombre} requiere una base literal; queda pendiente")
    return argumento.literal.strip().lower()


def _partes_fecha_dias(inicio: str, fin: str) -> tuple[str, str, str, str, str, str]:
    def parte(fecha: str, nombre: str) -> str:
        return f'TalendDate.getPartOfDate("{nombre}", {fecha})'

    return (
        parte(inicio, "YEAR"), parte(fin, "YEAR"),
        parte(inicio, "MONTH"), parte(fin, "MONTH"),
        parte(inicio, "DAY_OF_MONTH"), parte(fin, "DAY_OF_MONTH"),
    )


def _dias_30_360(inicio: str, fin: str) -> str:
    y1, y2, m1, m2, d1, d2 = _partes_fecha_dias(inicio, fin)
    fin_mes_1 = f'TalendDate.getPartOfDate("DAY_OF_MONTH", TalendDate.getLastDayOfMonth({inicio}))'
    fin_mes_2 = f'TalendDate.getPartOfDate("DAY_OF_MONTH", TalendDate.getLastDayOfMonth({fin}))'
    febrero_fin_1 = f"(({m1}) == 2 && ({d1}) == ({fin_mes_1}))"
    febrero_fin_2 = f"(({m2}) == 2 && ({d2}) == ({fin_mes_2}))"
    dia_inicio = f"(({febrero_fin_1} || ({d1}) == 31) ? 30 : ({d1}))"
    dia_fin = (
        f"((({febrero_fin_1} && {febrero_fin_2}) || "
        f"(({d2}) == 31 && (({dia_inicio}) == 30 || ({dia_inicio}) == 31))) "
        f"? 30 : ({d2}))"
    )
    return (
        f"Long.valueOf((({y2}) - ({y1})) * 360 + "
        f"(({m2}) - ({m1})) * 30 + ({dia_fin}) - ({dia_inicio}))"
    )


def _fechas_diferencia(args: list[E], nombre: str, max_args: int = 3) -> tuple[str, str, str | None]:
    _need(args, 2, max_args, nombre)
    inicio_arg, fin_arg = args[:2]
    if inicio_arg.kind not in {"date", "any", "num"} or fin_arg.kind not in {"date", "any", "num"}:
        raise Unsupported(f"{nombre} requiere fechas SAS numéricas")
    inicio = _fecha_java(inicio_arg, nombre)
    fin = _fecha_java(fin_arg, nombre)
    base = _base_literal(args[2], nombre) if len(args) == 3 else None
    return inicio, fin, base


def _datdif(_p: _P, args: list[E]) -> E:
    inicio, fin, base = _fechas_diferencia(args, "datdif")
    if base not in {"act/act", "actual", "30/360", "360", "act/360", "act/365"}:
        raise Unsupported("datdif requiere una base SAS literal admitida")
    if base in {"30/360", "360"}:
        resultado = _dias_30_360(inicio, fin)
    else:
        resultado = f'Long.valueOf(TalendDate.diffDate({fin}, {inicio}, "dd"))'
    java = f"({inicio} == null || {fin} == null ? null : {resultado})"
    return E(java, "num")


def _yrdif(_p: _P, args: list[E]) -> E:
    inicio, fin, base = _fechas_diferencia(args, "yrdif", 3)
    base = "age" if base is None else base
    if base == "age":
        raise Unsupported("Pendiente: P-JAVA-YRDIF-AGE")
    if base == "act/act" or base == "actual":
        raise Unsupported("Pendiente: P-JAVA-YRDIF-ACTACT")
    if base in {"30/360", "360"}:
        dias = _dias_30_360(inicio, fin)
        resultado = f"Double.valueOf(({dias}).doubleValue() / 360.0)"
    elif base == "act/360":
        resultado = f'TalendDate.diffDate({fin}, {inicio}, "dd") / 360.0'
    elif base == "act/365":
        resultado = f'TalendDate.diffDate({fin}, {inicio}, "dd") / 365.0'
    else:
        raise Unsupported("yrdif requiere una base literal SAS admitida")
    return E(f"({inicio} == null || {fin} == null ? null : {resultado})", "num")
