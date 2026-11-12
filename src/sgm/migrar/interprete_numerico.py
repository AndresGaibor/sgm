"""Funciones numéricas y de faltantes del intérprete."""

from __future__ import annotations

from collections.abc import Callable

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
    "coalesce": _coalesce,
    "missing": _missing,
}
