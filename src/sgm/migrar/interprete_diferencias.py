"""Conteos de fronteras y diferencias SAS entre fechas de calendario."""

from __future__ import annotations

from calendar import monthrange
from datetime import date

from .interprete_errores import NoSoportadoEnInterprete

_BASES_DATDIF = {"30/360", "360", "act/act", "actual", "act/360", "act/365"}
_BASES_YRDIF = {"30/360", "360", "act/act", "actual", "act/360", "act/365", "age"}


def _fecha(valor: object) -> date | None:
    from .interprete_fechas import _fecha_de_dias, _numero

    numero = _numero(valor)
    return None if numero is None else _fecha_de_dias(numero)


def _limite(fecha: date, intervalo: str) -> int:
    if intervalo == "year":
        return fecha.year
    if intervalo == "qtr":
        return fecha.year * 4 + (fecha.month - 1) // 3
    if intervalo == "month":
        return fecha.year * 12 + fecha.month - 1
    if intervalo == "week":
        return fecha.toordinal() // 7
    return fecha.toordinal()


def intck(intervalo: object, inicio: object, fin: object, metodo: object = None) -> int | None:
    """Cuenta las fronteras discretas de día, semana, mes, trimestre o año."""
    if not isinstance(intervalo, str):
        raise NoSoportadoEnInterprete("funcion", "Pendiente: P-INTCK-INTERVALO")
    nombre = intervalo.strip().lower()
    if nombre not in {"day", "week", "month", "qtr", "year"}:
        motivo = "P-INTCK-DESPLAZADO" if "." in nombre else "P-INTCK-INTERVALO"
        raise NoSoportadoEnInterprete("funcion", f"Pendiente: {motivo}")
    if metodo is not None:
        if not isinstance(metodo, str) or metodo.strip().lower() not in {
            "d", "disc", "discrete"
        }:
            raise NoSoportadoEnInterprete("funcion", "Pendiente: P-INTCK-CONTINUO")
    fecha_inicio, fecha_fin = _fecha(inicio), _fecha(fin)
    if fecha_inicio is None or fecha_fin is None:
        return None
    return _limite(fecha_fin, nombre) - _limite(fecha_inicio, nombre)


def _dias_30_360(inicio: date, fin: date) -> int:
    """Aplica las reglas SAS EOM y de días 31 para la base 30/360."""
    signo = 1
    if fin < inicio:
        inicio, fin = fin, inicio
        signo = -1
    inicio_febrero_fin = (
        inicio.month == 2 and inicio.day == monthrange(inicio.year, 2)[1]
    )
    fin_febrero_fin = fin.month == 2 and fin.day == monthrange(fin.year, 2)[1]
    d1, d2 = inicio.day, fin.day
    if inicio_febrero_fin:
        d1 = 30
    if inicio_febrero_fin and fin_febrero_fin:
        d2 = 30
    if d2 == 31 and d1 in (30, 31):
        d2 = 30
    if d1 == 31:
        d1 = 30
    dias = (fin.year - inicio.year) * 360 + (fin.month - inicio.month) * 30 + d2 - d1
    return signo * dias


def _edad(inicio: date, fin: date) -> int:
    signo = 1
    if fin < inicio:
        inicio, fin = fin, inicio
        signo = -1
    if (
        inicio.month == 2
        and inicio.day == 29
        and fin.year == inicio.year + 1
        and (fin.month, fin.day) == (2, 28)
    ):
        raise NoSoportadoEnInterprete("funcion", "Pendiente: P-YRDIF-AGE-29FEB")
    anios = fin.year - inicio.year
    if (fin.month, fin.day) < (inicio.month, inicio.day):
        anios -= 1
    return signo * anios


def _act_act(inicio: date, fin: date) -> float:
    signo = 1.0
    if fin < inicio:
        inicio, fin = fin, inicio
        signo = -1.0
    total = 0.0
    cursor = inicio
    while cursor < fin:
        limite_anio = date(cursor.year + 1, 1, 1) if cursor.year < 9999 else fin
        tramo_fin = min(fin, limite_anio)
        total += (tramo_fin - cursor).days / (366 if _bisiesto(cursor.year) else 365)
        cursor = tramo_fin
    return signo * total


def _bisiesto(anio: int) -> bool:
    return anio % 4 == 0 and (anio % 100 != 0 or anio % 400 == 0)


def datdif(inicio: object, fin: object, base: object) -> int | None:
    """Devuelve días con las bases SAS ACT/ACT y 30/360 documentadas."""
    if not isinstance(base, str) or base.strip().lower() not in _BASES_DATDIF:
        raise NoSoportadoEnInterprete("funcion", "Pendiente: P-DATDIF-BASE")
    primero, segundo = _fecha(inicio), _fecha(fin)
    if primero is None or segundo is None:
        return None
    nombre = base.strip().lower()
    if nombre in {"30/360", "360"}:
        return _dias_30_360(primero, segundo)
    return (segundo - primero).days


def yrdif(inicio: object, fin: object, base: object = "AGE") -> float | int | None:
    """Devuelve la diferencia anual según las bases SAS documentadas."""
    if not isinstance(base, str) or base.strip().lower() not in _BASES_YRDIF:
        raise NoSoportadoEnInterprete("funcion", "Pendiente: P-YRDIF-BASE")
    primero, segundo = _fecha(inicio), _fecha(fin)
    if primero is None or segundo is None:
        return None
    nombre = base.strip().lower()
    if nombre == "age":
        return _edad(primero, segundo)
    if nombre in {"30/360", "360"}:
        return _dias_30_360(primero, segundo) / 360
    diferencia = (segundo - primero).days
    if nombre == "act/360":
        return diferencia / 360
    if nombre == "act/365":
        return diferencia / 365
    return _act_act(primero, segundo)
