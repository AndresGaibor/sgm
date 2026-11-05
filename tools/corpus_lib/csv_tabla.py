"""Tablas CSV del corpus: lectura con tipos, celdas vacías como NULL y formato de salida.

Convenciones (ver `DIFERENCIAS.md`):
- Una celda vacía es un faltante (NULL). En SAS, un faltante numérico es `.` y de texto es blanco.
- Un entero es un número sin ceros a la izquierda; "007" es texto (un código), no número.
- El CSV de salida usa `,`, comillas solo cuando hacen falta y fin de línea `\n`.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field
from pathlib import Path

_ENTERO = re.compile(r"-?(0|[1-9]\d*)$")
_REAL = re.compile(r"-?(0|[1-9]\d*)\.\d+$")
_NUMERO = re.compile(r"-?\d+(\.\d+)?([eE][-+]?\d+)?$")
_IDENTIFICADOR = re.compile(r"[A-Za-z_]\w*$")


@dataclass
class Tabla:
    """Tabla con nombres de columna, filas de valores Python (None para faltante) y tipos SQL."""

    columnas: list[str]
    filas: list[tuple]
    tipos: list[str] = field(default_factory=list)


def leer_csv(ruta: Path) -> tuple[list[str], list[list[str | None]]]:
    """Lee un CSV con encabezado. Las celdas vacías salen como None."""
    with ruta.open(encoding="utf-8-sig", newline="") as archivo:
        lector = csv.reader(archivo)
        try:
            columnas = next(lector)
        except StopIteration:
            raise ValueError(f"{ruta}: el CSV no tiene encabezado") from None
        for nombre in columnas:
            if not _IDENTIFICADOR.match(nombre):
                raise ValueError(f"{ruta}: nombre de columna no válido '{nombre}'")
        filas: list[list[str | None]] = []
        for numero, fila in enumerate(lector, start=2):
            if not fila:
                continue
            if len(fila) != len(columnas):
                raise ValueError(
                    f"{ruta}, línea {numero}: {len(fila)} campos, se esperaban {len(columnas)}"
                )
            filas.append([valor if valor != "" else None for valor in fila])
    return columnas, filas


def tipo_sql(valores: list[str | None]) -> str:
    """INTEGER si todos los valores presentes son enteros; REAL si son números; TEXT si no."""
    presentes = [valor for valor in valores if valor is not None]
    if presentes and all(_ENTERO.match(valor) for valor in presentes):
        return "INTEGER"
    if presentes and all(_ENTERO.match(valor) or _REAL.match(valor) for valor in presentes):
        return "REAL"
    return "TEXT"


def leer_entradas(carpeta: Path) -> dict[str, Tabla]:
    """Carga cada CSV de la carpeta. Nombre de tabla: el archivo sin extensión, en mayúsculas."""
    if not carpeta.is_dir():
        return {}
    tablas: dict[str, Tabla] = {}
    for ruta in sorted(carpeta.glob("*.csv")):
        columnas, crudas = leer_csv(ruta)
        tipos = [tipo_sql([fila[i] for fila in crudas]) for i in range(len(columnas))]
        filas = [
            tuple(_convertir(valor, tipos[i]) for i, valor in enumerate(fila)) for fila in crudas
        ]
        tablas[ruta.stem.upper()] = Tabla(columnas, filas, tipos)
    return tablas


def _convertir(valor: str | None, tipo: str) -> int | float | str | None:
    if valor is None:
        return None
    if tipo == "INTEGER":
        return int(valor)
    if tipo == "REAL":
        return float(valor)
    return valor


def celda_texto(valor: object) -> str:
    """Texto de una celda para el CSV de salida. None es vacío; los reales usan hasta 12 cifras."""
    if valor is None:
        return ""
    if isinstance(valor, float):
        return format(valor, ".12g")
    return str(valor)


def escribir_csv(ruta: Path, tabla: Tabla) -> None:
    """Escribe la tabla como CSV con encabezado, creando la carpeta si falta."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("w", encoding="utf-8", newline="") as archivo:
        escritor = csv.writer(archivo, lineterminator="\n")
        escritor.writerow(tabla.columnas)
        for fila in tabla.filas:
            escritor.writerow([celda_texto(valor) for valor in fila])


def _clave_valor(valor: object) -> tuple:
    if valor is None:
        return (0, 0.0, "")
    if isinstance(valor, (int, float)):
        return (1, float(valor), "")
    return (2, 0.0, str(valor))


def ordenar_filas(filas: list[tuple]) -> list[tuple]:
    """Orden determinista por todas las columnas: faltantes primero, luego números y luego texto."""
    return sorted(filas, key=lambda fila: tuple(_clave_valor(valor) for valor in fila))


def _clave_texto(celda: str) -> tuple:
    if celda == "":
        return (0, 0.0, "")
    if _NUMERO.match(celda):
        return (1, float(celda), "")
    return (2, 0.0, celda)


def _iguales(esperado: str, obtenido: str, tolerancia: float) -> bool:
    if esperado == obtenido:
        return True
    if _NUMERO.match(esperado) and _NUMERO.match(obtenido):
        return abs(float(esperado) - float(obtenido)) <= tolerancia
    return False


def comparar_con_guardado(
    ruta: Path, tabla: Tabla, tolerancia: float, orden_relevante: bool
) -> list[str]:
    """Compara la tabla calculada con el CSV guardado. Devuelve las diferencias en texto legible."""
    if not ruta.exists():
        return [f"falta el archivo {ruta.name}"]
    with ruta.open(encoding="utf-8", newline="") as archivo:
        guardado = list(csv.reader(archivo))
    if not guardado:
        return [f"{ruta.name} está vacío"]
    if guardado[0] != tabla.columnas:
        return [f"encabezado: esperado {guardado[0]}, obtenido {tabla.columnas}"]
    esperadas = guardado[1:]
    obtenidas = [[celda_texto(valor) for valor in fila] for fila in tabla.filas]
    if len(esperadas) != len(obtenidas):
        return [f"filas: esperado {len(esperadas)}, obtenido {len(obtenidas)}"]
    if not orden_relevante:
        esperadas.sort(key=lambda fila: tuple(_clave_texto(celda) for celda in fila))
        obtenidas.sort(key=lambda fila: tuple(_clave_texto(celda) for celda in fila))
    diferencias: list[str] = []
    for numero, (esp, obt) in enumerate(zip(esperadas, obtenidas, strict=True), start=1):
        if len(esp) != len(obt):
            diferencias.append(f"fila {numero}: {len(esp)} celdas esperadas, {len(obt)} obtenidas")
            continue
        for columna, valor_esp, valor_obt in zip(tabla.columnas, esp, obt, strict=True):
            if not _iguales(valor_esp, valor_obt, tolerancia):
                diferencias.append(
                    f"fila {numero}, columna '{columna}': "
                    f"esperado '{valor_esp}', obtenido '{valor_obt}'"
                )
    return diferencias
