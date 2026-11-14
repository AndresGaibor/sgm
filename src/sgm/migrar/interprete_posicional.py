"""Intérprete controlado de `INFILE` con `INPUT` posicional."""

from __future__ import annotations

from collections.abc import Sequence

from sgm.formatos.informat_archivo import leer_campo
from sgm.migrar.interprete_errores import NoSoportadoEnInterprete


def leer_columnas(
    lineas: Sequence[str],
    campos: Sequence[tuple[str, int, int, str]],
    truncover: bool,
) -> list[dict[str, str | None]]:
    """Lee campos de ancho fijo por registro y conserva el fin de línea con TRUNCOVER."""
    if not truncover:
        raise NoSoportadoEnInterprete("infile", "P-INFILE-FLOWOVER")
    for nombre, inicio, ancho, informat in campos:
        if (
            not nombre
            or isinstance(inicio, bool)
            or not isinstance(inicio, int)
            or inicio < 1
            or isinstance(ancho, bool)
            or not isinstance(ancho, int)
            or ancho < 1
            or not isinstance(informat, str)
        ):
            raise NoSoportadoEnInterprete("infile", "P-INFILE-POSICION-INVALIDA")
    filas: list[dict[str, str | None]] = []
    for linea in lineas:
        fila: dict[str, str | None] = {}
        for nombre, inicio, ancho, informat in campos:
            campo = linea[inicio - 1 : inicio - 1 + ancho]
            fila[nombre] = leer_campo(campo, informat)
        filas.append(fila)
    return filas


__all__ = ["leer_columnas"]
