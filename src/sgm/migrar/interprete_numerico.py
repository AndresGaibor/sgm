"""Funciones numéricas y de faltantes del intérprete."""

from __future__ import annotations

import math
from collections.abc import Callable
from decimal import ROUND_HALF_UP, Decimal

from sgm.migrar import semantica

from .interprete_errores import NoSoportadoEnInterprete


def _mean(argumentos: list) -> float | None:
    valores = _numeros("MEAN", argumentos)
    presentes = [valor for valor in valores if valor is not None]
    return sum(presentes) / len(presentes) if presentes else None


def _min(argumentos: list) -> float | None:
    valores = _numeros("MIN", argumentos)
    presentes = [valor for valor in valores if valor is not None]
    return min(presentes) if presentes else None


def _max(argumentos: list) -> float | None:
    valores = _numeros("MAX", argumentos)
    presentes = [valor for valor in valores if valor is not None]
    return max(presentes) if presentes else None


def _sum(argumentos: list) -> float | None:
    valores = _numeros("SUM", argumentos)
    presentes = [valor for valor in valores if valor is not None]
    return sum(presentes) if presentes else None


def _numeros(nombre: str, argumentos: list) -> list[float | None]:
    if not argumentos:
        raise NoSoportadoEnInterprete("funcion", f"{nombre} requiere argumentos")
    valores = [semantica.como_numero(valor) for valor in argumentos]
    if any(
        convertido is None and not semantica.es_faltante(valor)
        for valor, convertido in zip(argumentos, valores, strict=True)
    ):
        if nombre in ("MIN", "MAX"):
            raise NoSoportadoEnInterprete("funcion", "MIN/MAX de texto")
        raise NoSoportadoEnInterprete("funcion", f"{nombre} requiere argumentos numéricos")
    return valores


def _n(argumentos: list) -> int:
    return sum(valor is not None for valor in _numeros("N", argumentos))


def _nmiss(argumentos: list) -> int:
    return sum(valor is None for valor in _numeros("NMISS", argumentos))


def _cmiss(argumentos: list) -> int:
    if not argumentos:
        raise NoSoportadoEnInterprete("funcion", "CMISS requiere argumentos")
    return sum(_faltante_funcion(valor) for valor in argumentos)


def _faltante_funcion(valor: object) -> bool:
    """En funciones SAS, solo espacios ASCII hacen missing un valor de carácter."""
    if isinstance(valor, str):
        return valor.strip(" ") == ""
    return semantica.es_faltante(valor)


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
    if any(isinstance(valor, str) for valor in argumentos):
        if any(valor is not None and not isinstance(valor, str) for valor in argumentos):
            raise NoSoportadoEnInterprete("funcion", "COALESCE requiere argumentos del mismo tipo")
        return next(
            (valor for valor in argumentos if isinstance(valor, str) and valor.strip(" ")),
            None,
        )
    valores = _numeros("COALESCE", argumentos)
    return next((valor for original, valor in zip(argumentos, valores, strict=True)
                 if not semantica.es_faltante(original)), None)


def _missing(argumentos: list) -> bool:
    if len(argumentos) != 1:
        raise NoSoportadoEnInterprete("funcion", "MISSING requiere un argumento")
    return _faltante_funcion(argumentos[0] if argumentos else None)


def _condicion(argumento: object, nombre: str) -> float | None:
    if isinstance(argumento, bool):
        return float(argumento)
    valor = semantica.como_numero(argumento)
    if valor is None and not semantica.es_faltante(argumento):
        raise NoSoportadoEnInterprete("funcion", f"{nombre} requiere condición numérica")
    return valor


def _ifn(argumentos: list) -> object:
    if len(argumentos) not in (3, 4):
        raise NoSoportadoEnInterprete("funcion", "IFN requiere tres o cuatro argumentos")
    condicion = _condicion(argumentos[0], "IFN")
    elegido = argumentos[1] if condicion is not None and condicion != 0 else argumentos[2]
    if condicion is None and len(argumentos) == 4:
        elegido = argumentos[3]
    if elegido is None or semantica.es_faltante(elegido):
        return None
    convertido = semantica.como_numero(elegido)
    if convertido is None:
        raise NoSoportadoEnInterprete("funcion", "IFN requiere valores numéricos")
    return convertido


def _ifc(argumentos: list) -> object:
    if len(argumentos) not in (3, 4):
        raise NoSoportadoEnInterprete("funcion", "IFC requiere tres o cuatro argumentos")
    condicion = _condicion(argumentos[0], "IFC")
    indice = 1 if condicion is not None and condicion != 0 else 2
    if condicion is None and len(argumentos) == 4:
        indice = 3
    elegido = argumentos[indice]
    if _faltante_funcion(elegido):
        return None
    if not isinstance(elegido, str):
        raise NoSoportadoEnInterprete("funcion", "IFC requiere valores de texto")
    return elegido


FUNCIONES: dict[str, Callable[[list], object]] = {
    "mean": _mean,
    "min": _min,
    "max": _max,
    "sum": _sum,
    "n": _n,
    "nmiss": _nmiss,
    "cmiss": _cmiss,
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
    "ifn": _ifn,
    "ifc": _ifc,
}
