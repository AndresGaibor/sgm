"""Tipo de cada columna de un `PROC IMPORT` demostrado por su muestra de filas.

Fuente SAS: `proc.pdf`, sección «PROC IMPORT Statement», p. 1380. Para archivos delimitados se
leen las primeras 20 filas (`GUESSINGROWS=`) y la columna es numérica si sus valores no vacíos
son numéricos; si alguno no lo es, es carácter. Las filas que SAS no lee quedan marcadas.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

GUESSINGROWS_POR_OMISION = 20


@dataclass(frozen=True)
class TipoDemostrado:
    tipo_sas: str  # "numerico" o "caracter"
    fuente: str
    evidencia: int  # filas no vacías leídas
    pendientes: tuple[str, ...] = field(default=())


_NUMERO_SAS = re.compile(r"[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?")


def _es_numero(valor: str) -> bool:
    """Decimal con signo y exponente opcionales; `nan`, `inf` y otros textos no son números."""
    return _NUMERO_SAS.fullmatch(valor) is not None


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


def _texto_de(ruta: Path) -> str | None:
    """Contenido del archivo si es texto UTF-8 de verdad; None si no lo es (p. ej. un .xlsx)."""
    try:
        datos = Path(ruta).read_bytes()
    except OSError:
        return None
    if b"\x00" in datos[:4096]:
        return None
    try:
        return datos.decode("utf-8-sig")
    except UnicodeDecodeError:
        return None


def filas_del_archivo(
    ruta: Path, delimiter: str | None, getnames: bool = True
) -> tuple[list[str], list[list[str]]]:
    """Nombres de columna y filas de un archivo delimitado.

    Con `GETNAMES=YES` (por omisión) la primera fila son los nombres. Con `GETNAMES=NO` SAS los
    nombra `VAR1`, `VAR2`, y la primera fila es dato (`proc.pdf`, p. 1387 a 1388).
    """
    texto = _texto_de(ruta)
    if texto is None:
        return [], []
    lineas = texto.splitlines()
    lineas = [linea for linea in lineas if linea.strip()]
    if not lineas:
        return [], []
    separador = delimiter or (";" if ";" in lineas[0] else ",")
    filas = [[c.strip().strip("'\"") for c in linea.split(separador)] for linea in lineas]
    if not getnames:
        return [f"VAR{i}" for i in range(1, len(filas[0]) + 1)], filas
    return [c for c in filas[0] if c], filas[1:]


def tipos_de_archivo(
    ruta: Path,
    delimiter: str | None,
    nombres: list[str],
    guessingrows: int = GUESSINGROWS_POR_OMISION,
    getnames: bool = True,
) -> dict[str, TipoDemostrado]:
    """Tipo demostrado de cada columna de `nombres` leyendo el archivo delimitado en `ruta`."""
    cabecera, filas = filas_del_archivo(ruta, delimiter, getnames)
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


__all__ = [
    "GUESSINGROWS_POR_OMISION",
    "TipoDemostrado",
    "filas_del_archivo",
    "tipo_desde_muestra",
    "tipos_de_archivo",
]
