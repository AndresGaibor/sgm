"""Funciones numéricas y de faltantes del intérprete."""

from __future__ import annotations

import math
from collections.abc import Callable
from decimal import ROUND_HALF_UP, Decimal

from sgm.migrar import semantica

from .interprete_errores import NoSoportadoEnInterprete


def _mean(argumentos: list) -> float | None:
    valores = [semantica.como_numero(valor) for valor in argumentos]
    presentes = [valor for valor in valores if valor is not None]
    return sum(presentes) / len(presentes) if presentes else None


def _min(argumentos: list) -> float | None:
    valores = [semantica.como_numero(valor) for valor in argumentos]
    presentes = [valor for valor in valores if valor is not None]
    return min(presentes) if presentes else None


def _max(argumentos: list) -> float | None:
    valores = [semantica.como_numero(valor) for valor in argumentos]
    presentes = [valor for valor in valores if valor is not None]
    return max(presentes) if presentes else None


def _sum(argumentos: list) -> float | None:
    valores = [semantica.como_numero(valor) for valor in argumentos]
    if any(
        not semantica.es_faltante(valor) and convertido is None
        for valor, convertido in zip(argumentos, valores, strict=True)
    ):
        raise NoSoportadoEnInterprete("funcion", "SUM requiere argumentos numéricos")
    presentes = [valor for valor in valores if valor is not None]
    return sum(presentes) if presentes else None


def _abs(argumentos: list) -> float | None:
    numero = semantica.como_numero(argumentos[0] if argumentos else None)
    return None if numero is None else abs(numero)


def _numero(argumento: object) -> float | None:
    return semantica.como_numero(argumento)


def _entero_cercano(numero: float) -> float:
    entero = round(numero)
    return float(entero) if abs(numero - entero) <= 1e-12 else numero


def _int(argumentos: list) -> float | None:
    if len(argumentos) != 1:
        raise NoSoportadoEnInterprete("funcion", "INT requiere un argumento")
    numero = _numero(argumentos[0])
    return None if numero is None else float(math.trunc(_entero_cercano(numero)))


def _ceil(argumentos: list) -> float | None:
    if len(argumentos) != 1:
        raise NoSoportadoEnInterprete("funcion", "CEIL requiere un argumento")
    numero = _numero(argumentos[0])
    return None if numero is None else float(math.ceil(_entero_cercano(numero)))


def _floor(argumentos: list) -> float | None:
    if len(argumentos) != 1:
        raise NoSoportadoEnInterprete("funcion", "FLOOR requiere un argumento")
    numero = _numero(argumentos[0])
    return None if numero is None else float(math.floor(_entero_cercano(numero)))


def _mod(argumentos: list) -> float | None:
    if len(argumentos) != 2:
        raise NoSoportadoEnInterprete("funcion", "MOD requiere dos argumentos")
    dividendo, divisor = (_numero(argumento) for argumento in argumentos)
    if dividendo is None or divisor is None or divisor == 0:
        return None
    try:
        resultado = math.fmod(dividendo, divisor)
    except (ValueError, OverflowError):
        return None
    return resultado if math.isfinite(resultado) else None


def _unaria(nombre: str, funcion: Callable[[float], float]):
    def aplicar(argumentos: list) -> float | None:
        if len(argumentos) != 1:
            raise NoSoportadoEnInterprete("funcion", f"{nombre.upper()} requiere un argumento")
        numero = _numero(argumentos[0])
        if numero is None:
            return None
        try:
            resultado = funcion(numero)
        except (ValueError, OverflowError):
            return None
        return resultado if math.isfinite(resultado) else None

    return aplicar


def _round(argumentos: list) -> float | None:
    if len(argumentos) not in (1, 2):
        raise NoSoportadoEnInterprete("funcion", "ROUND requiere uno o dos argumentos")
    valor = _numero(argumentos[0])
    unidad = _numero(argumentos[1]) if len(argumentos) == 2 else 1.0
    if valor is None or unidad is None or unidad == 0:
        return None
    try:
        cociente = (Decimal(repr(valor)) / Decimal(repr(unidad))).to_integral_value(
            rounding=ROUND_HALF_UP
        )
        resultado = float(cociente * Decimal(repr(unidad)))
    except (ArithmeticError, ValueError, OverflowError):
        return None
    return resultado if math.isfinite(resultado) else None


def _coalesce(argumentos: list) -> object:
    return next((valor for valor in argumentos if not semantica.es_faltante(valor)), None)


def _missing(argumentos: list) -> bool:
    return semantica.es_faltante(argumentos[0] if argumentos else None)


FUNCIONES: dict[str, Callable[[list], object]] = {
    "mean": _mean,
    "min": _min,
    "max": _max,
    "sum": _sum,
    "abs": _abs,
    "int": _int,
    "ceil": _ceil,
    "floor": _floor,
    "mod": _mod,
    "sqrt": _unaria("sqrt", math.sqrt),
    "log": _unaria("log", math.log),
    "exp": _unaria("exp", math.exp),
    "sign": _unaria("sign", lambda numero: float((numero > 0) - (numero < 0))),
    "round": _round,
    "coalesce": _coalesce,
    "missing": _missing,
}
