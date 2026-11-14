"""Emisión Talend de INTNX para fechas de calendario documentadas por SAS."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sgm.expressions.talend_parser import _P

from sgm.expressions.talend_base import E, Unsupported, _guard, _need, _num

_COLUMN = re.compile(r"[A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)+")


def _incremento_entero(value: str) -> bool:
    try:
        number = Decimal(value)
    except InvalidOperation:
        return False
    return number.is_finite() and number == number.to_integral_value()


def _mismo_dia(fecha: str, inicio_mes: str) -> str:
    fin_mes = f"TalendDate.getLastDayOfMonth({inicio_mes})"
    dia_origen = f'TalendDate.getPartOfDate("DAY_OF_MONTH", {fecha})'
    dia_destino = f'TalendDate.getPartOfDate("DAY_OF_MONTH", {fin_mes})'
    dia_ajustado = f"Math.min({dia_origen}, {dia_destino})"
    return f'TalendDate.addDate({inicio_mes}, (int) ({dia_ajustado} - 1), "dd")'


def _primer_dia_anio(fecha: str, incremento: str) -> str:
    inicio = (
        'TalendDate.parseDate("yyyy-MM-dd", '
        f'TalendDate.formatDate("yyyy", {fecha}) + "-01-01")'
    )
    return f'TalendDate.addDate({inicio}, (int) ({incremento}), "yyyy")'


def _intnx(_p: _P, args: list[E]) -> E:
    _need(args, 3, 4, "intnx")
    unidad_arg, fecha_valor, incremento = args[:3]
    unidad = unidad_arg.literal.lower() if unidad_arg.literal is not None else ""
    if unidad_arg.kind != "str":
        raise Unsupported("Pendiente: P-INTNX-INTERVALO (se requiere un literal)")
    if re.fullmatch(r"[a-z]+\d+(?:\.\d+)?", unidad):
        raise Unsupported("Pendiente: P-INTNX-MULTIUNIDAD")
    if "." in unidad:
        raise Unsupported("Pendiente: P-INTNX-DESPLAZADO")
    if unidad not in {"day", "week", "month", "qtr", "year"}:
        raise Unsupported("Pendiente: P-INTNX-INTERVALO")
    if fecha_valor.kind == "null" or incremento.kind == "null":
        return E("null", "date")
    if fecha_valor.kind not in {"date", "num", "any"}:
        raise Unsupported("Pendiente: P-INTNX-FECHA-TIPO")
    if incremento.kind not in {"num", "any"}:
        raise Unsupported("Pendiente: P-INTNX-INCREMENTO-TIPO")

    escala = {"week": 7, "qtr": 3}.get(unidad, 1)
    if incremento.kind == "num":
        if not _incremento_entero(incremento.java.strip()):
            raise Unsupported("Pendiente: P-INTNX-INCREMENTO-NO-ENTERO")
        try:
            desplazamiento = Decimal(incremento.java.strip()) * escala
            if not -(2**31) <= desplazamiento <= 2**31 - 1:
                raise Unsupported("Pendiente: P-INTNX-RANGO-TALEND")
        except InvalidOperation as error:
            raise Unsupported("intnx requiere un incremento entero literal") from error
    elif not _COLUMN.fullmatch(incremento.java.strip()):
        raise Unsupported("Pendiente: P-INTNX-INCREMENTO-DINAMICO")

    if len(args) == 4 and args[3].kind != "str":
        raise Unsupported("Pendiente: P-INTNX-ALINEACION-DINAMICA")
    alineacion = args[3].literal.lower() if len(args) == 4 else "b"
    alineacion = {
        "beginning": "b",
        "middle": "m",
        "end": "e",
        "same": "s",
        "sameday": "s",
    }.get(alineacion, alineacion)
    if alineacion == "m":
        raise Unsupported("Pendiente: P-INTNX-ALINEACION-M")
    if alineacion not in {"b", "e", "s"}:
        raise Unsupported("Pendiente: P-INTNX-ALINEACION")

    from sgm.expressions.talend_funciones_fecha import _fecha_java

    fecha = _fecha_java(fecha_valor, "intnx")
    cantidad = _num(incremento)
    pasos = f"(int) ({cantidad} * {escala})" if escala != 1 else f"(int) ({cantidad})"
    if unidad == "day":
        resultado = f'TalendDate.addDate({fecha}, {pasos}, "dd")'
    elif unidad == "week":
        domingo = (
            f'TalendDate.addDate({fecha}, (int) '
            f'({cantidad} * 7 - (TalendDate.getPartOfDate("DAY_OF_WEEK", {fecha}) - 1)), "dd")'
        )
        resultado = (
            f'TalendDate.addDate({fecha}, {pasos}, "dd")'
            if alineacion == "s"
            else domingo
            if alineacion == "b"
            else f'TalendDate.addDate({domingo}, 6, "dd")'
        )
    elif unidad == "month":
        inicio_mes = f'TalendDate.addDate(TalendDate.getFirstDayOfMonth({fecha}), {pasos}, "MM")'
        resultado = (
            _mismo_dia(fecha, inicio_mes)
            if alineacion == "s"
            else f"TalendDate.getLastDayOfMonth({inicio_mes})"
            if alineacion == "e"
            else inicio_mes
        )
    elif unidad == "qtr":
        mes = f'(TalendDate.getPartOfDate("MONTH", {fecha}) + 1)'
        offset = f"(({mes} - 1) % 3)"
        inicio_actual = (
            f'TalendDate.addDate(TalendDate.getFirstDayOfMonth({fecha}), '
            f'(int) (-{offset}), "MM")'
        )
        inicio_trimestre = f'TalendDate.addDate({inicio_actual}, {pasos}, "MM")'
        if alineacion == "s":
            mes_destino = f'TalendDate.addDate({inicio_trimestre}, (int) {offset}, "MM")'
            resultado = _mismo_dia(fecha, mes_destino)
        elif alineacion == "e":
            resultado = (
                f'TalendDate.addDate(TalendDate.addDate({inicio_trimestre}, 3, "MM"), -1, "dd")'
            )
        else:
            resultado = inicio_trimestre
    else:
        mes = f'(TalendDate.getPartOfDate("MONTH", {fecha}) + 1)'
        inicio_anio = _primer_dia_anio(fecha, cantidad)
        if alineacion == "s":
            mes_destino = f'TalendDate.addDate({inicio_anio}, (int) ({mes} - 1), "MM")'
            resultado = _mismo_dia(fecha, mes_destino)
        elif alineacion == "e":
            resultado = f'TalendDate.addDate(TalendDate.addDate({inicio_anio}, 1, "yyyy"), -1, "dd")'
        else:
            resultado = inicio_anio

    guarded = _guard(
        [fecha_valor, incremento],
        f"({fecha} == null ? null : {resultado})",
    )
    if incremento.kind == "any":
        inferior = f"(Integer.MIN_VALUE / {escala}.0)"
        superior = f"(Integer.MAX_VALUE / {escala}.0)"
        rango = f"({cantidad} >= {inferior} && {cantidad} <= {superior})"
        entero = f"Double.isFinite({cantidad}) && {cantidad} == Math.rint({cantidad})"
        guarded = _guard(
            [fecha_valor, incremento],
            f"(({rango}) && ({entero}) && {fecha} != null ? {resultado} : null)",
        )
    _p.warnings.add(
        "intnx usa fecha SAS desde 1960 y límites de calendario; validar el Job en Studio"
    )
    return E(guarded, "date")
