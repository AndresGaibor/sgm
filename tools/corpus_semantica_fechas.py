"""Oráculo independiente para funciones SAS de fecha (días ordinales desde 1960)."""

from __future__ import annotations

import math
from datetime import date
from typing import Callable

_EPOCA_ORDINAL = date(1960, 1, 1).toordinal()
_SEGUNDOS_DIA = 86400


def crear_funciones_fechas(faltante: object, es_faltante: Callable[[object], bool]) -> dict:
    """Crea funciones de fecha sin importar el conversor ni el intérprete de producción."""

    def numero(valor: object) -> float | None:
        if es_faltante(valor):
            return None
        if isinstance(valor, bool):
            raise TypeError("las funciones de fecha requieren números")
        try:
            convertido = float(valor)
        except (TypeError, ValueError) as error:
            raise TypeError("las funciones de fecha requieren números") from error
        if not math.isfinite(convertido):
            raise ValueError("Pendiente: P-FECHA-NO-FINITA")
        return convertido

    def fecha_desde_dias(dias: float) -> date:
        ordinal = _EPOCA_ORDINAL + math.floor(dias)
        try:
            return date.fromordinal(ordinal)
        except ValueError as error:
            raise ValueError("Pendiente: P-FECHA-FUERA-DE-RANGO") from error

    def mdy(mes: object, dia: object, anio: object) -> int | object:
        valores = [numero(valor) for valor in (mes, dia, anio)]
        if any(valor is None for valor in valores):
            return faltante
        mes_num, dia_num, anio_num = valores
        if any(not valor.is_integer() for valor in valores):
            return faltante
        mes_num, dia_num, anio_num = int(mes_num), int(dia_num), int(anio_num)
        if 0 <= anio_num < 100:
            raise ValueError("Pendiente: P-YEARCUTOFF-EXPLICITO")
        if 100 <= anio_num < 1000:
            raise ValueError("Pendiente: P-MDY-ANIO-3-CIFRAS")
        if anio_num < 0 or anio_num > 9999:
            raise ValueError("Pendiente: P-MDY-ANIO-FUERA-DE-RANGO")
        try:
            return date(anio_num, mes_num, dia_num).toordinal() - _EPOCA_ORDINAL
        except ValueError:
            return faltante

    def parte(nombre: str):
        def aplicar(valor: object) -> int | object:
            numero_fecha = numero(valor)
            if numero_fecha is None:
                return faltante
            fecha = fecha_desde_dias(numero_fecha)
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
            raise KeyError(nombre)

        return aplicar

    def datepart(valor: object) -> int | object:
        segundos = numero(valor)
        return faltante if segundos is None else math.floor(segundos / _SEGUNDOS_DIA)

    def today() -> int:
        return date.today().toordinal() - _EPOCA_ORDINAL

    return {
        "mdy": mdy,
        "year": parte("year"),
        "month": parte("month"),
        "day": parte("day"),
        "weekday": parte("weekday"),
        "qtr": parte("qtr"),
        "datepart": datepart,
        "today": today,
        "date": today,
    }
