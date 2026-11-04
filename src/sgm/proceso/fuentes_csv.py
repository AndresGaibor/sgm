"""Archivos de texto que un programa SAS baja e importa: ruta, delimitador, cabecera y columnas.

Un `PROC DOWNLOAD INFILE='origen' OUTFILE='temporal'` seguido de `PROC IMPORT DATAFILE='temporal'
... DBMS=DLM; DELIMITER=';'; GETNAMES=NO;` es la lectura de un archivo delimitado. El SAS demuestra
la ruta de origen, el delimitador y si hay cabecera. Sin cabecera (`GETNAMES=NO`) SAS nombra las
columnas `VAR1`, `VAR2`, ...: se cuentan hasta la mayor que el programa usa. Con cabecera los
nombres no están en el SAS y las columnas quedan pendientes. El producto sale de la etiqueta
`/* Etiqueta: ... */` previa y del nombre del archivo; si no es único, queda sin producto.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from sgm.proceso.entradas_salidas import nombre_archivo

_DOWNLOAD = re.compile(
    r"\bPROC\s+DOWNLOAD\b[^;]*?\bINFILE\s*=\s*(['\"])(.*?)\1[^;]*?\bOUTFILE\s*=\s*(['\"])(.*?)\3",
    re.IGNORECASE | re.DOTALL,
)
_IMPORT = re.compile(r"\bPROC\s+IMPORT\b(.*?)\bRUN\s*;", re.IGNORECASE | re.DOTALL)
_DATAFILE = re.compile(r"\bDATAFILE\s*=\s*(['\"])(.*?)\1", re.IGNORECASE)
_OUT = re.compile(r"\bOUT\s*=\s*(?:WORK\.)?(\w+)", re.IGNORECASE)
_DBMS = re.compile(r"\bDBMS\s*=\s*(\w+)", re.IGNORECASE)
_DELIM = re.compile(r"\bDELIMITER\s*=\s*(['\"])(.*?)\1", re.IGNORECASE)
_GETNAMES = re.compile(r"\bGETNAMES\s*=\s*(\w+)", re.IGNORECASE)
_VAR = re.compile(r"\bVAR(\d+)\b", re.IGNORECASE)
_ETIQUETA = re.compile(r"/\*\s*Etiqueta:\s*(.*?)\s*\*/", re.IGNORECASE)


@dataclass(frozen=True)
class FuenteCsv:
    ruta_origen: str  # la del PROC DOWNLOAD (INFILE), la que lee el programa de verdad
    archivo: str
    dataset: str
    delimitador: str
    con_cabecera: bool
    columnas: int  # cuántas VARn usa el SAS; 0 = pendiente (con cabecera o sin uso)
    producto: str | None
    linea: int
    inicio: int = 0  # posición en el texto donde empieza el PROC IMPORT
    fin: int = 0  # donde empieza el siguiente PROC IMPORT (o el final)


def _linea(texto: str, posicion: int) -> int:
    return texto.count("\n", 0, posicion) + 1


def _etiqueta_previa(texto: str, posicion: int) -> str:
    previas = _ETIQUETA.findall(texto[:posicion])
    return previas[-1] if previas else ""


def _producto_por_palabra(texto: str, productos: dict[str, tuple[str, ...]]) -> str | None:
    """Producto con más palabras sueltas suyas (sus sufijos) en el texto; empate o nada: None."""
    cuenta = {
        nombre: sum(len(re.findall(rf"\b{re.escape(s)}\b", texto, re.IGNORECASE)) for s in sufijos)
        for nombre, sufijos in productos.items()
    }
    ordenados = sorted(cuenta.items(), key=lambda kv: -kv[1])
    if not ordenados or ordenados[0][1] == 0:
        return None
    if len(ordenados) > 1 and ordenados[1][1] == ordenados[0][1]:
        return None
    return ordenados[0][0]


def fuentes_csv(texto: str, productos: dict[str, tuple[str, ...]]) -> list[FuenteCsv]:
    """Cada archivo delimitado que el programa baja e importa, en orden de aparición."""
    descargas = {m.group(4).lower(): m for m in _DOWNLOAD.finditer(texto)}
    hallados = []
    for m in _IMPORT.finditer(texto):
        bloque = m.group(1)
        datafile, salida, dbms = _DATAFILE.search(bloque), _OUT.search(bloque), _DBMS.search(bloque)
        if not (datafile and salida and dbms and dbms.group(1).upper() == "DLM"):
            continue
        hallados.append((m, datafile.group(2), salida.group(1), bloque))
    resultado: list[FuenteCsv] = []
    for i, (m, temporal, dataset, bloque) in enumerate(hallados):
        descarga = descargas.get(temporal.lower())
        origen = descarga.group(2) if descarga else temporal
        fin = hallados[i + 1][0].start() if i + 1 < len(hallados) else len(texto)
        nombres = _GETNAMES.search(bloque)
        con_cabecera = not (nombres and nombres.group(1).upper() == "NO")
        usadas = [int(n) for n in _VAR.findall(texto[m.end() : fin])]
        delimitador = _DELIM.search(bloque)
        contexto = f"{_etiqueta_previa(texto, m.start())} {nombre_archivo(origen)}"
        resultado.append(
            FuenteCsv(
                origen,
                nombre_archivo(origen),
                dataset,
                delimitador.group(2) if delimitador else " ",
                con_cabecera,
                0 if con_cabecera else max(usadas, default=0),
                _producto_por_palabra(contexto, productos),
                _linea(texto, m.start()),
                m.start(),
                fin,
            )
        )
    return resultado
