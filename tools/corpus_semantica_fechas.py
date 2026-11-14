"""Oráculo independiente para funciones SAS de fecha (días ordinales desde 1960)."""

from __future__ import annotations

import math
import re
from calendar import monthrange
from datetime import date, timedelta
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

    def mes_movido(fecha: date, desplazamiento: int, dia: int) -> date:
        indice = fecha.year * 12 + fecha.month - 1 + desplazamiento
        anio, mes_cero = divmod(indice, 12)
        mes = mes_cero + 1
        if anio < 1 or anio > 9999:
            raise ValueError("Pendiente: P-FECHA-FUERA-DE-RANGO")
        return date(anio, mes, min(dia, monthrange(anio, mes)[1]))

    def intnx(*argumentos: object) -> int | object:
        if len(argumentos) not in {3, 4}:
            raise ValueError("INTNX requiere tres o cuatro argumentos")
        intervalo, fecha_valor, incremento_valor = argumentos[:3]
        alineacion_valor = argumentos[3] if len(argumentos) == 4 else "b"
        if not isinstance(intervalo, str):
            raise ValueError("Pendiente: P-INTNX-INTERVALO")
        nombre = intervalo.strip().lower()
        if re.fullmatch(r"[a-z]+\d+(?:\.\d+)?", nombre):
            raise ValueError("Pendiente: P-INTNX-MULTIUNIDAD")
        if "." in nombre:
            raise ValueError("Pendiente: P-INTNX-DESPLAZADO")
        if nombre not in {"day", "week", "month", "qtr", "year"}:
            raise ValueError("Pendiente: P-INTNX-INTERVALO")
        if not isinstance(alineacion_valor, str):
            raise ValueError("Pendiente: P-INTNX-ALINEACION")
        alineacion = {
            "b": "b",
            "beginning": "b",
            "e": "e",
            "end": "e",
            "s": "s",
            "same": "s",
            "sameday": "s",
        }.get(alineacion_valor.strip().lower())
        if alineacion is None:
            if alineacion_valor.strip().lower() in {"m", "middle"}:
                raise ValueError("Pendiente: P-INTNX-ALINEACION-M")
            raise ValueError("Pendiente: P-INTNX-ALINEACION")

        numero_fecha = numero(fecha_valor)
        numero_incremento = numero(incremento_valor)
        if numero_fecha is None or numero_incremento is None:
            return faltante
        if not numero_incremento.is_integer():
            raise ValueError("Pendiente: P-INTNX-INCREMENTO-NO-ENTERO")

        fecha_inicio = fecha_desde_dias(numero_fecha)
        incremento = int(numero_incremento)
        try:
            if nombre == "day":
                salida = fecha_inicio + timedelta(days=incremento)
            elif nombre == "week":
                if alineacion == "s":
                    salida = fecha_inicio + timedelta(weeks=incremento)
                else:
                    inicio_semana = fecha_inicio - timedelta(
                        days=(fecha_inicio.weekday() + 1) % 7
                    )
                    destino = inicio_semana + timedelta(weeks=incremento)
                    salida = destino + timedelta(days=6) if alineacion == "e" else destino
            elif nombre == "month":
                inicio_mes = mes_movido(fecha_inicio, incremento, 1)
                if alineacion == "s":
                    salida = mes_movido(fecha_inicio, incremento, fecha_inicio.day)
                elif alineacion == "e":
                    salida = date(
                        inicio_mes.year,
                        inicio_mes.month,
                        monthrange(inicio_mes.year, inicio_mes.month)[1],
                    )
                else:
                    salida = inicio_mes
            elif nombre == "qtr":
                mes_inicio = ((fecha_inicio.month - 1) // 3) * 3 + 1
                inicio_trimestre = mes_movido(
                    date(fecha_inicio.year, mes_inicio, 1), incremento * 3, 1
                )
                if alineacion == "s":
                    salida = mes_movido(fecha_inicio, incremento * 3, fecha_inicio.day)
                elif alineacion == "e":
                    salida = mes_movido(inicio_trimestre, 3, 1) - timedelta(days=1)
                else:
                    salida = inicio_trimestre
            else:
                anio = fecha_inicio.year + incremento
                if anio < 1 or anio > 9999:
                    raise OverflowError
                if alineacion == "s":
                    salida = mes_movido(fecha_inicio, incremento * 12, fecha_inicio.day)
                else:
                    salida = date(anio, 12, 31) if alineacion == "e" else date(anio, 1, 1)
            return salida.toordinal() - _EPOCA_ORDINAL
        except (OverflowError, ValueError) as error:
            raise ValueError("Pendiente: P-FECHA-FUERA-DE-RANGO") from error

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
        "intnx": intnx,
    }
