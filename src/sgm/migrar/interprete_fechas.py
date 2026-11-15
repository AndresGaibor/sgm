"""Funciones de fecha SAS en el intérprete, con días desde 1960-01-01."""

from __future__ import annotations

import math
from collections.abc import Callable
from datetime import date, timedelta

from sgm.migrar import semantica

from .interprete_diferencias import datdif, intck, yrdif
from .interprete_errores import NoSoportadoEnInterprete
from .interprete_intervalos import intnx as _intnx

EPOCA_SAS = date(1960, 1, 1)
RELOJ: Callable[[], date] = date.today


def dias_a_fecha(dias: int) -> date:
    """Convierte días SAS enteros a `date`; fechas fuera del rango quedan pendientes."""
    if isinstance(dias, bool) or not isinstance(dias, int):
        raise TypeError("dias_a_fecha requiere un entero")
    try:
        return EPOCA_SAS + timedelta(days=dias)
    except OverflowError as error:
        raise NoSoportadoEnInterprete("funcion", "Pendiente: P-FECHA-FUERA-DE-RANGO") from error


def fecha_a_dias(fecha: date) -> int:
    """Convierte una fecha calendario al número de días SAS."""
    if type(fecha) is not date:
        raise TypeError("fecha_a_dias requiere una fecha")
    return (fecha - EPOCA_SAS).days


def _numero(valor: object) -> float | None:
    if isinstance(valor, bool):
        raise NoSoportadoEnInterprete("funcion", "función de fecha con argumento booleano")
    numero = semantica.como_numero(valor)
    if numero is None:
        if semantica.es_faltante(valor):
            return None
        raise NoSoportadoEnInterprete("funcion", "función de fecha requiere argumentos numéricos")
    if not math.isfinite(numero):
        raise NoSoportadoEnInterprete("funcion", "Pendiente: P-FECHA-NO-FINITA")
    return numero


def _fecha_de_dias(dias: float) -> date:
    try:
        return dias_a_fecha(math.floor(dias))
    except NoSoportadoEnInterprete:
        raise


def _fecha_argumento(argumentos: list, nombre: str) -> date | None:
    if len(argumentos) != 1:
        raise NoSoportadoEnInterprete("funcion", f"{nombre.upper()} requiere un argumento")
    dias = _numero(argumentos[0])
    return None if dias is None else _fecha_de_dias(dias)


def _mdy(argumentos: list) -> int | None:
    if len(argumentos) != 3:
        raise NoSoportadoEnInterprete("funcion", "MDY requiere mes, día y año")
    numeros = [_numero(valor) for valor in argumentos]
    if any(valor is None for valor in numeros):
        return None
    mes, dia, anio = numeros
    if any(not valor.is_integer() for valor in numeros):
        return None
    mes, dia, anio = int(mes), int(dia), int(anio)
    if 0 <= anio < 100:
        raise NoSoportadoEnInterprete("funcion", "Pendiente: P-YEARCUTOFF-EXPLICITO")
    if 100 <= anio < 1000:
        raise NoSoportadoEnInterprete("funcion", "Pendiente: P-MDY-ANIO-3-CIFRAS")
    if anio < 0 or anio > 9999:
        raise NoSoportadoEnInterprete("funcion", "Pendiente: P-MDY-ANIO-FUERA-DE-RANGO")
    try:
        return fecha_a_dias(date(anio, mes, dia))
    except ValueError:
        return None


def _parte(nombre: str):
    def aplicar(argumentos: list) -> int | None:
        fecha = _fecha_argumento(argumentos, nombre)
        if fecha is None:
            return None
        if nombre == "year":
            return fecha.year
        if nombre == "month":
            return fecha.month
        if nombre == "day":
            return fecha.day
        if nombre == "weekday":
            return fecha.isoweekday() % 7 + 1
        if nombre == "qtr":
            return (fecha.month - 1) // 3 + 1
        raise NoSoportadoEnInterprete("funcion", f"función de fecha no implementada: {nombre}")

    return aplicar


def _datepart(argumentos: list) -> int | None:
    if len(argumentos) != 1:
        raise NoSoportadoEnInterprete("funcion", "DATEPART requiere un argumento")
    segundos = _numero(argumentos[0])
    return None if segundos is None else math.floor(segundos / 86400)


def _today(argumentos: list) -> int:
    if argumentos:
        raise NoSoportadoEnInterprete("funcion", "TODAY/DATE no reciben argumentos")
    actual = RELOJ()
    if type(actual) is not date:
        raise NoSoportadoEnInterprete("funcion", "RELOJ debe devolver una fecha")
    return fecha_a_dias(actual)


def _funcion_intnx(argumentos: list) -> int | None:
    if len(argumentos) not in {3, 4}:
        raise NoSoportadoEnInterprete("funcion", "INTNX requiere tres o cuatro argumentos")
    return _intnx(*argumentos)


FUNCIONES = {
    "mdy": _mdy,
    "year": _parte("year"),
    "month": _parte("month"),
    "day": _parte("day"),
    "weekday": _parte("weekday"),
    "qtr": _parte("qtr"),
    "datepart": _datepart,
    "today": _today,
    "date": _today,
    "intnx": _funcion_intnx,
    "intck": lambda argumentos: intck(*argumentos),
    "datdif": lambda argumentos: datdif(*argumentos),
    "yrdif": lambda argumentos: yrdif(*argumentos),
}
