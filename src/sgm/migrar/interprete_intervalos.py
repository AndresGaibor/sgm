"""Intervalos de calendario de SAS con conteo desde la época de 1960."""

from __future__ import annotations

import re
from calendar import monthrange
from datetime import date, timedelta

from .interprete_errores import NoSoportadoEnInterprete

_INTERVALOS = {"day", "week", "month", "qtr", "year"}
_ALINEACIONES = {
    "b": "b",
    "beginning": "b",
    "e": "e",
    "end": "e",
    "s": "s",
    "same": "s",
    "sameday": "s",
}


def _mes_movido(fecha: date, desplazamiento: int, dia: int) -> date:
    indice = fecha.year * 12 + fecha.month - 1 + desplazamiento
    anio, mes_cero = divmod(indice, 12)
    mes = mes_cero + 1
    if anio < 1 or anio > 9999:
        raise OverflowError("fecha fuera del calendario admitido")
    return date(anio, mes, min(dia, monthrange(anio, mes)[1]))


def _resultado(intervalo: str, fecha: date, incremento: int, alineacion: str) -> date:
    if intervalo == "day":
        return fecha + timedelta(days=incremento)
    if intervalo == "week":
        if alineacion == "s":
            return fecha + timedelta(weeks=incremento)
        inicio = fecha - timedelta(days=(fecha.weekday() + 1) % 7)
        destino = inicio + timedelta(weeks=incremento)
        return destino + timedelta(days=6) if alineacion == "e" else destino
    if intervalo == "month":
        inicio = _mes_movido(fecha, incremento, 1)
        if alineacion == "s":
            return _mes_movido(fecha, incremento, fecha.day)
        if alineacion == "e":
            return date(inicio.year, inicio.month, monthrange(inicio.year, inicio.month)[1])
        return inicio
    if intervalo == "qtr":
        mes_inicio = ((fecha.month - 1) // 3) * 3 + 1
        inicio = _mes_movido(date(fecha.year, mes_inicio, 1), incremento * 3, 1)
        if alineacion == "s":
            return _mes_movido(fecha, incremento * 3, fecha.day)
        if alineacion == "e":
            proximo = _mes_movido(inicio, 3, 1)
            return proximo - timedelta(days=1)
        return inicio
    anio = fecha.year + incremento
    if anio < 1 or anio > 9999:
        raise OverflowError("fecha fuera del calendario admitido")
    if alineacion == "s":
        return _mes_movido(fecha, incremento * 12, fecha.day)
    return date(anio, 12, 31) if alineacion == "e" else date(anio, 1, 1)


def intnx(
    intervalo: object,
    fecha: object,
    incremento: object,
    alineacion: object = "b",
) -> int | None:
    """Desplaza una fecha por intervalos SAS demostrados; formas no cubiertas quedan pendientes."""
    from .interprete_fechas import _fecha_de_dias, _numero, fecha_a_dias

    if not isinstance(intervalo, str):
        raise NoSoportadoEnInterprete("funcion", "Pendiente: P-INTNX-INTERVALO")
    nombre = intervalo.strip().lower()
    if re.fullmatch(r"[a-z]+\d+(?:\.\d+)?", nombre):
        raise NoSoportadoEnInterprete("funcion", "Pendiente: P-INTNX-MULTIUNIDAD")
    if "." in nombre:
        raise NoSoportadoEnInterprete("funcion", "Pendiente: P-INTNX-DESPLAZADO")
    if nombre not in _INTERVALOS:
        raise NoSoportadoEnInterprete("funcion", "Pendiente: P-INTNX-INTERVALO")

    if not isinstance(alineacion, str):
        raise NoSoportadoEnInterprete("funcion", "Pendiente: P-INTNX-ALINEACION")
    alineacion_normalizada = alineacion.strip().lower()
    if alineacion_normalizada in {"m", "middle"}:
        raise NoSoportadoEnInterprete("funcion", "Pendiente: P-INTNX-ALINEACION-M")
    alineacion_normalizada = _ALINEACIONES.get(alineacion_normalizada)
    if alineacion_normalizada is None:
        raise NoSoportadoEnInterprete("funcion", "Pendiente: P-INTNX-ALINEACION")

    numero_fecha = _numero(fecha)
    numero_incremento = _numero(incremento)
    if numero_fecha is None or numero_incremento is None:
        return None
    if not numero_incremento.is_integer():
        raise NoSoportadoEnInterprete("funcion", "Pendiente: P-INTNX-INCREMENTO-NO-ENTERO")

    inicio = _fecha_de_dias(numero_fecha)
    try:
        salida = _resultado(nombre, inicio, int(numero_incremento), alineacion_normalizada)
        return fecha_a_dias(salida)
    except (OverflowError, ValueError) as error:
        raise NoSoportadoEnInterprete("funcion", "Pendiente: P-FECHA-FUERA-DE-RANGO") from error
