"""Tipo de cada columna de un `PROC IMPORT` demostrado por su muestra de filas.

Fuente SAS: `proc.pdf`, sección «PROC IMPORT Statement», p. 1380. Para archivos delimitados se
leen las primeras 20 filas (`GUESSINGROWS=`) y la columna es numérica si sus valores no vacíos
son numéricos; si alguno no lo es, es carácter. Las filas que SAS no lee quedan marcadas.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

GUESSINGROWS_POR_OMISION = 20


@dataclass(frozen=True)
class TipoDemostrado:
    tipo_sas: str  # "numerico" o "caracter"
    fuente: str
    evidencia: int  # filas no vacías leídas
    pendientes: tuple[str, ...] = field(default=())


def _es_numero(valor: str) -> bool:
    try:
        float(valor)
    except ValueError:
        return False
    return True


def tipo_desde_muestra(
    valores: list[str], guessingrows: int = GUESSINGROWS_POR_OMISION
) -> TipoDemostrado | None:
    """`numerico` si todos los valores no vacíos de las primeras `guessingrows` filas son numéricos,
    `caracter` si alguno no lo es, `None` si la muestra no tiene valores."""
    muestra = [v.strip() for v in valores[:guessingrows] if v.strip()]
    if not muestra:
        return None
    fuente = f"PROC IMPORT, GUESSINGROWS={guessingrows}"
    if not all(_es_numero(v) for v in muestra):
        return TipoDemostrado("caracter", fuente, len(muestra))
    fuera = [v for v in valores[guessingrows:] if v.strip() and not _es_numero(v.strip())]
    pendientes = ("P-TIPO-FUERA-DE-MUESTRA",) if fuera else ()
    return TipoDemostrado("numerico", fuente, len(muestra), pendientes)


def tipos_de_archivo(
    ruta: Path,
    delimiter: str | None,
    nombres: list[str],
    guessingrows: int = GUESSINGROWS_POR_OMISION,
) -> dict[str, TipoDemostrado]:
    """Tipo demostrado de cada columna de `nombres` leyendo el archivo delimitado en `ruta`."""
    try:
        lineas = Path(ruta).read_text(encoding="utf-8-sig", errors="replace").splitlines()
    except OSError:
        return {}
    if not lineas:
        return {}
    separador = delimiter or (";" if ";" in lineas[0] else ",")
    cabecera = [c.strip().strip("'\"") for c in lineas[0].split(separador)]
    filas = [
        [c.strip().strip("'\"") for c in linea.split(separador)]
        for linea in lineas[1:]
        if linea.strip()
    ]
    tipos: dict[str, TipoDemostrado] = {}
    for nombre in nombres:
        if nombre not in cabecera:
            continue
        pos = cabecera.index(nombre)
        valores = [fila[pos] for fila in filas if pos < len(fila)]
        tipo = tipo_desde_muestra(valores, guessingrows)
        if tipo is not None:
            tipos[nombre] = tipo
    return tipos


__all__ = ["GUESSINGROWS_POR_OMISION", "TipoDemostrado", "tipo_desde_muestra", "tipos_de_archivo"]
