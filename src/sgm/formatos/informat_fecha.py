"""Lectura acotada de informats de fecha SAS con año explícito de cuatro dígitos."""

from __future__ import annotations

import re
from datetime import date

from sgm.migrar.interprete_errores import NoSoportadoEnInterprete

_SPEC = re.compile(r"(?i)^([a-z]+)(\d*)\.(\d*)$")
_FORMATOS = {"yymmdd", "ddmmyy", "date", "anydtdte", "e8601da"}
_MESES = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}
_EPOCA_SAS = date(1960, 1, 1)


def dias_sas(anio: int, mes: int, dia: int) -> int:
    """Devuelve días desde 1960-01-01, la época de fechas SAS."""
    return (date(anio, mes, dia) - _EPOCA_SAS).days


def _pendiente(codigo: str) -> NoSoportadoEnInterprete:
    return NoSoportadoEnInterprete("informat", codigo)


def _partes(texto: str, base: str) -> tuple[int, int, int] | None:
    if base == "yymmdd":
        if re.fullmatch(r"\d{6}|\d{2}[-/]\d{2}[-/]\d{2}", texto):
            raise _pendiente("P-YEARCUTOFF-EXPLICITO")
        match = re.fullmatch(r"(\d{4})(\d{2})(\d{2})|(\d{4})[-/](\d{2})[-/](\d{2})", texto)
        if match:
            values = next(group for group in (match.groups()[:3], match.groups()[3:]) if group[0])
            return tuple(map(int, values))
    elif base == "ddmmyy":
        if re.fullmatch(r"\d{6}|\d{2}[-/]\d{2}[-/]\d{2}", texto):
            raise _pendiente("P-YEARCUTOFF-EXPLICITO")
        match = re.fullmatch(r"(\d{2})(\d{2})(\d{4})|(\d{2})[-/](\d{2})[-/](\d{4})", texto)
        if match:
            values = next(group for group in (match.groups()[:3], match.groups()[3:]) if group[0])
            day, month, year = map(int, values)
            return year, month, day
    elif base == "date":
        if re.fullmatch(r"\d{2}[A-Za-z]{3}\d{2}", texto):
            raise _pendiente("P-YEARCUTOFF-EXPLICITO")
        match = re.fullmatch(r"(\d{2})([A-Za-z]{3})(\d{4})", texto)
        if match:
            day, month_name, year = match.groups()
            month = _MESES.get(month_name.casefold())
            return (int(year), month, int(day)) if month else None
    elif base == "anydtdte":
        if re.fullmatch(r"\d{1,2}[-/]\d{1,2}[-/]\d{2}", texto):
            raise _pendiente("P-YEARCUTOFF-EXPLICITO")
        if re.fullmatch(r"\d{1,2}[-/]\d{1,2}[-/]\d{4}", texto):
            raise _pendiente("P-ANYDTDTE-DATESTYLE")
        match = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", texto)
        if match:
            return tuple(map(int, match.groups()))
        if re.search(r"\d", texto) and re.search(r"[-/ ]", texto):
            raise _pendiente("P-ANYDTDTE-DATESTYLE")
    elif base == "e8601da":
        match = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", texto)
        if match:
            return tuple(map(int, match.groups()))

    raise _pendiente("P-INFORMAT-SIN-SOPORTE")


def leer_fecha(texto: str, informat: str) -> int | None:
    """Convierte los informats admitidos; sin inferir siglo ni DATESTYLE."""
    spec = _SPEC.fullmatch(informat.strip())
    if spec is None or not informat_fecha_soportado(informat):
        raise _pendiente("P-INFORMAT-SIN-SOPORTE")
    base = spec.group(1).casefold()
    value = texto.strip()
    if value in {"", "."}:
        return None
    parts = _partes(value, base)
    if parts is None:
        return None
    try:
        return dias_sas(*parts)
    except ValueError:
        # SAS marca como perdido un valor que el informat no puede leer como fecha válida.
        return None


def informat_fecha_soportado(informat: str) -> bool:
    """Indica si hay conversión fechada implementada para el informat."""
    match = _SPEC.fullmatch(informat.strip())
    if match is None or match.group(3):
        return False
    base, width = match.group(1).casefold(), int(match.group(2) or 0)
    if base == "e8601da":
        return True
    widths = {
        "yymmdd": {6, 8, 10},
        "ddmmyy": {6, 8, 10},
        "date": {7, 9},
        "anydtdte": {10},
    }
    return width in widths.get(base, set())


__all__ = ["dias_sas", "informat_fecha_soportado", "leer_fecha"]
