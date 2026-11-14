"""Lectura conservadora de declaraciones globales `LIBNAME`."""

from __future__ import annotations

import re
from dataclasses import dataclass

from sgm.frontend.steps_tipos import Libname
from sgm.redaction import redact

_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")
_MACRO = re.compile(r"[&%]")
_CLEAR = re.compile(r"(?is)^(?:_all_\s+)?clear$")


@dataclass(frozen=True)
class InfoLibname:
    """Forma estática observada en una sentencia `LIBNAME`, sin valores sensibles."""

    nombre: str
    motor: str | None
    ruta: str | None
    opciones: str
    linea: int


def _opciones_seguras(texto: str) -> str:
    return redact(texto, "")


def info_libname(item: Libname) -> InfoLibname:
    """Distingue una ruta literal, un motor y la liberación de un libref."""
    nombre = item.name.casefold()
    valor = item.value.strip().rstrip(";").strip()
    if _CLEAR.fullmatch(valor):
        return InfoLibname(nombre, None, None, "clear", item.line)
    if not valor:
        return InfoLibname(nombre, None, None, "", item.line)

    if valor[0] in "'\"":
        cita = valor[0]
        fin = valor.find(cita, 1)
        if fin >= 0:
            ruta = valor[1:fin]
            resto = valor[fin + 1 :].strip()
            literal = ruta if not _MACRO.search(ruta) else None
            return InfoLibname(nombre, None, literal, _opciones_seguras(resto), item.line)

    partes = valor.split(None, 1)
    motor = partes[0].casefold()
    opciones = _opciones_seguras(partes[1]) if len(partes) == 2 else ""
    if not _IDENTIFIER.fullmatch(motor):
        motor = None
    return InfoLibname(nombre, motor, None, opciones, item.line)


__all__ = ["InfoLibname", "info_libname"]
