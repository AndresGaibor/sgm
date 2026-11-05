"""Lectura de las entradas y comparación del cruce de los casos L8 de totales.

Lectores: CSV delimitado por `;` (con o sin cabecera), primera hoja de un .xlsx y CSV de
`esperado/` como texto. `comparar` contrasta una tabla de SQLite con el CSV esperado: el orden no
importa y los números se comparan con la tolerancia del caso.
"""

from __future__ import annotations

import csv
import zipfile
from pathlib import Path
from xml.etree import ElementTree

Tabla = tuple[list[str], list[list]]


def leer_dlm(ruta: Path, cabecera: bool) -> Tabla:
    """CSV delimitado por `;`. Sin cabecera, las columnas se llaman VAR1..VARn (PROC IMPORT)."""
    with ruta.open(encoding="utf-8-sig", newline="") as archivo:
        filas = [linea for linea in csv.reader(archivo, delimiter=";") if linea]
    if cabecera:
        return filas[0], filas[1:]
    return [f"VAR{i}" for i in range(1, len(filas[0]) + 1)], filas


def leer_xlsx(ruta: Path) -> Tabla:
    """Primera hoja de un .xlsx: la primera fila son los nombres y las demás, valores."""
    espacio = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with zipfile.ZipFile(ruta) as libro:
        raiz = ElementTree.fromstring(libro.read("xl/worksheets/sheet1.xml"))
    filas = []
    for fila in raiz.iterfind(".//m:row", espacio):
        valores = []
        for celda in fila.iterfind("m:c", espacio):
            texto = "".join(celda.itertext()).strip()
            if celda.get("t") == "inlineStr":
                valores.append(texto)
            else:
                valores.append(int(texto) if texto.lstrip("-").isdigit() else float(texto))
        filas.append(valores)
    return [str(c) for c in filas[0]], filas[1:]


def leer_esperado(ruta: Path) -> Tabla:
    """Lee un CSV de `esperado/` como texto (vacío = faltante, que aquí es None)."""
    with ruta.open(encoding="utf-8", newline="") as archivo:
        filas = list(csv.reader(archivo))
    return filas[0], [[c if c != "" else None for c in f] for f in filas[1:]]


def comparar(nombre: str, obtenido: Tabla, esperado: Tabla, tolerancia: float) -> list[str]:
    """Compara una tabla de SQLite con el CSV esperado: sin orden; los números, con tolerancia."""
    cols_o, filas_o = obtenido
    cols_e, filas_e = esperado
    if cols_o != cols_e:
        return [f"{nombre}: columnas esperadas {cols_e}, obtenidas {cols_o}"]
    if len(filas_o) != len(filas_e):
        return [f"{nombre}: filas esperadas {len(filas_e)}, obtenidas {len(filas_o)}"]
    diferencias = []
    orden_o = sorted(filas_o, key=_clave)
    orden_e = sorted(filas_e, key=_clave)
    for n, (fo, fe) in enumerate(zip(orden_o, orden_e, strict=True), 1):
        for columna, vo, ve in zip(cols_o, fo, fe, strict=True):
            if not _iguales(ve, vo, tolerancia):
                diferencias.append(f"{nombre}, fila {n}, '{columna}': esperado '{ve}', "
                                   f"obtenido '{vo}'")  # fmt: skip
    return diferencias


def ordenado(filas: list[list]) -> list[tuple]:
    """Filas en orden canónico, para comparar conjuntos sin depender del orden de SQLite."""
    return sorted((tuple(f) for f in filas), key=_clave)


def _clave(fila: list) -> tuple:
    def celda(valor: object) -> tuple:
        if valor in (None, ""):
            return (0, 0.0, "")
        if _es_numero(valor):
            return (1, round(float(valor), 2), "")  # type: ignore[arg-type]
        return (2, 0.0, str(valor))

    return tuple(celda(v) for v in fila)


def _es_numero(valor: object) -> bool:
    try:
        float(valor)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return False
    return True


def _iguales(esperado: object, obtenido: object, tolerancia: float) -> bool:
    if esperado in (None, "") or obtenido in (None, ""):
        return esperado in (None, "") and obtenido in (None, "")
    if _es_numero(esperado) and _es_numero(obtenido):
        return abs(float(esperado) - float(obtenido)) <= tolerancia + 1e-9  # type: ignore[arg-type]
    return str(esperado) == str(obtenido)
