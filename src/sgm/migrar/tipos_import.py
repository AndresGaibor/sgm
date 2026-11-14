"""Tipo de cada columna de un `PROC IMPORT` demostrado por su muestra de filas.

Fuente SAS: `proc.pdf`, pp. 1380 y 1388. Para archivos delimitados se infiere el tipo con las filas
que cubre `GUESSINGROWS=` (conteo físico desde la fila 1); los valores no vacíos de la muestra
determinan si la columna es numérica o carácter. Texto numérico fuera de la muestra queda marcado.
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
    valores: list[str], guessingrows: int | str = GUESSINGROWS_POR_OMISION
) -> TipoDemostrado | None:
    """`numerico` si todos los valores no vacíos de las primeras `guessingrows` filas son numéricos,
    `caracter` si alguno no lo es, `None` si la muestra no tiene valores."""
    limite = (
        len(valores)
        if isinstance(guessingrows, str) and guessingrows.casefold() == "max"
        else guessingrows
    )
    if not isinstance(limite, int) or limite < 1:
        return None
    muestra = [v.strip() for v in valores[:limite] if v.strip()]
    if not muestra:
        return None
    fuente = f"PROC IMPORT, GUESSINGROWS={guessingrows}"
    if not all(_es_numero(v) for v in muestra):
        return TipoDemostrado("caracter", fuente, len(muestra))
    fuera = [v for v in valores[limite:] if v.strip() and not _es_numero(v.strip())]
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


def nombres_por_omision(cantidad: int) -> list[str]:
    """Nombres que SAS asigna por posición con `GETNAMES=NO` (`proc.pdf`, p. 1387)."""
    return [f"VAR{indice}" for indice in range(1, max(0, cantidad) + 1)]


def filas_del_archivo(
    ruta: Path,
    delimiter: str | None,
    getnames: bool = True,
    datarow: int | None = None,
) -> tuple[list[str], list[list[str]]]:
    """Nombres de columna y filas de un archivo delimitado.

    `DATAROW` indica la primera fila de datos; con `GETNAMES=YES` la primera fila sigue dando los
    nombres. Con `GETNAMES=NO` los nombres son `VAR1`, `VAR2`, ... (`proc.pdf`, pp. 1385, 1387).
    """
    texto = _texto_de(ruta)
    if texto is None:
        return [], []
    lineas = texto.splitlines()
    if datarow is None:
        lineas = [linea for linea in lineas if linea.strip()]
    if not lineas:
        return [], []
    primera_fila_datos = datarow if datarow is not None else (2 if getnames else 1)
    if (
        isinstance(primera_fila_datos, bool)
        or not isinstance(primera_fila_datos, int)
        or primera_fila_datos < (2 if getnames else 1)
    ):
        raise ValueError("DATAROW no es válido con GETNAMES; proc.pdf, p. 1385")
    fila_muestra = min(primera_fila_datos - 1, len(lineas) - 1)
    separador = delimiter or (";" if ";" in lineas[fila_muestra] else ",")
    filas = [[c.strip().strip("'\"") for c in linea.split(separador)] for linea in lineas]
    inicio_datos = primera_fila_datos - 1
    if not getnames:
        datos = filas[inicio_datos:]
        cantidad = len(datos[0]) if datos else 0
        return nombres_por_omision(cantidad), datos
    return [c for c in filas[0] if c], filas[inicio_datos:]


def tipos_de_archivo(
    ruta: Path,
    delimiter: str | None,
    nombres: list[str],
    guessingrows: int | str = GUESSINGROWS_POR_OMISION,
    getnames: bool = True,
    datarow: int | None = None,
) -> dict[str, TipoDemostrado]:
    """Tipo demostrado de cada columna de `nombres` leyendo el archivo delimitado en `ruta`."""
    inicio_datos = datarow if datarow is not None else (2 if getnames else 1)
    if isinstance(inicio_datos, bool) or not isinstance(inicio_datos, int):
        return {}
    limite = (
        guessingrows
        if isinstance(guessingrows, str) and guessingrows.casefold() == "max"
        else guessingrows - inicio_datos + 1
        if isinstance(guessingrows, int) and guessingrows > inicio_datos
        else 0
    )
    cabecera, filas = filas_del_archivo(ruta, delimiter, getnames, datarow)
    tipos: dict[str, TipoDemostrado] = {}
    for nombre in nombres:
        if nombre not in cabecera:
            continue
        pos = cabecera.index(nombre)
        valores = [fila[pos] for fila in filas if pos < len(fila)]
        tipo = tipo_desde_muestra(valores, limite)
        if tipo is not None:
            tipos[nombre] = tipo
    return tipos


__all__ = [
    "GUESSINGROWS_POR_OMISION",
    "TipoDemostrado",
    "filas_del_archivo",
    "nombres_por_omision",
    "tipo_desde_muestra",
    "tipos_de_archivo",
]
