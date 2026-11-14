"""Escritura mínima de una hoja XLSX para los adaptadores locales del migrador."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from sgm.migrar.xlsx_minimo import escribir_xlsx


def escribir_hoja(
    ruta: Path,
    hoja: str,
    encabezado: Sequence[str] | None,
    filas: Sequence[Sequence[object]],
) -> None:
    """Escribe una hoja sin estilos; el llamador determina si debe incluir encabezado."""
    contenido = [list(fila) for fila in filas]
    if encabezado is not None:
        columnas = list(encabezado)
        if not columnas:
            raise ValueError("el encabezado de la hoja no puede estar vacío")
        if any(len(fila) != len(columnas) for fila in contenido):
            raise ValueError("cada fila debe coincidir con el ancho del encabezado")
        contenido.insert(0, columnas)
    escribir_xlsx(ruta, {hoja: contenido})


__all__ = ["escribir_hoja"]
