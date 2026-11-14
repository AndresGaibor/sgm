"""Traducción IR de `PROC IMPORT` y `PROC EXPORT` a operaciones de archivo."""

from __future__ import annotations

import re

from sgm.frontend.steps import Proc
from sgm.ir.builder import Builder, qualify
from sgm.ir.models import Evidence

# Opciones que el PROC IMPORT y el PROC EXPORT escriben como sentencia del cuerpo (`GETNAMES=YES;`)
# o en la cabecera. Se leen del texto y no se suponen: el valor que falta queda en `None`.
_OPCION = re.compile(
    r"(?i)\b(dbms|delimiter|getnames|datarow|sheet|guessingrows|putnames)\s*=\s*"
    r"('[^']*'|\"[^\"]*\"|[^\s;]+)"
)


def _sin_comillas(valor: str) -> str:
    return valor.strip().strip("'\"")


def _opciones(step: Proc) -> dict[str, str]:
    """Opciones de archivo del paso, tal como las escribe el SAS (cabecera y cuerpo)."""
    texto = " ".join([step.text, *step.body])
    return {m.group(1).lower(): m.group(2) for m in _OPCION.finditer(texto)}


def _dbms(opciones: dict[str, str]) -> str | None:
    valor = opciones.get("dbms")
    return _sin_comillas(valor).lower() if valor else None


def _entero(valor: str | None) -> int | str | None:
    """Convierte el límite literal y conserva MAX o una expresión sin evaluar."""
    texto = _sin_comillas(valor) if valor else ""
    return int(texto) if texto.isdigit() else texto or None


def _getnames(opciones: dict[str, str]) -> bool:
    """Valor por omisión: `proc`, p. 1387 para delimitados; `acpcref`, p. 93 para Excel."""
    valor = opciones.get("getnames")
    return True if valor is None else _sin_comillas(valor).upper() != "NO"


def _putnames(valor: str) -> bool | None:
    """Preserva solo los literales YES/NO; una expresión dinámica no se adivina."""
    texto = _sin_comillas(valor).upper()
    return {"YES": True, "NO": False}.get(texto)


def _read_file(step: Proc, ev: Evidence, b: Builder, out: str | None) -> None:
    """`PROC IMPORT`: archivo de entrada con su formato, separador, cabecera y hoja."""
    opciones = _opciones(step)
    datafile = step.options.get("datafile")
    params = {
        "datafile": datafile,
        "outputs": [qualify(out)] if out else [],
        "dbms": _dbms(opciones),
        "delimiter": _sin_comillas(opciones["delimiter"]) if "delimiter" in opciones else None,
        "getnames": _getnames(opciones),
        "sheet": _sin_comillas(opciones["sheet"]) if "sheet" in opciones else None,
        "guessingrows": _entero(opciones.get("guessingrows")),
    }
    if datafile and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", datafile.strip()):
        params["fileref"] = datafile.strip()
        params["datafile"] = None
    if "datarow" in opciones:
        params["datarow"] = _entero(opciones["datarow"])
    b.op("read_file", params, ev)


def _write_file(step: Proc, ev: Evidence, b: Builder, data: str | None) -> None:
    """`PROC EXPORT`: archivo de salida con su formato y separador."""
    opciones = _opciones(step)
    params = {
        "inputs": [qualify(data)] if data else [],
        "outfile": step.options.get("outfile"),
        "dbms": _dbms(opciones),
        "delimiter": _sin_comillas(opciones["delimiter"]) if "delimiter" in opciones else None,
    }
    if "sheet" in opciones:
        params["sheet"] = _sin_comillas(opciones["sheet"])
    if "putnames" in opciones:
        params["putnames"] = _putnames(opciones["putnames"])
    b.op("write_file", params, ev)
