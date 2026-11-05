"""Datos ficticios para las entradas del corpus: columnas con tipo, celdas vacías y semilla fija.

Los nombres, ciudades y productos son inventados y evidentes como tales. La semilla es fija, así que
generar dos veces da los mismos bytes. Cada tabla usa su propia semilla derivada de caso y archivo.
"""

from __future__ import annotations

import csv
import random
from dataclasses import dataclass
from pathlib import Path

SEMILLA = 20261104

NOMBRES = (
    "Ana Prueba", "Bruno Demo", "Carla Muestra", "Diego Ejemplo", "Elena Ficticia",
    "Felipe Dato", "Gabriela Test", "Hugo Simulado", "Irene Modelo", "Jorge Caso",
)
NOMBRES_CON_TILDES = (
    "José Ejemplo", "Mónica Demo", "Ñandú Ficticio", "Águeda Muestra", "Iñaki Dato",
    "Pepé Simulado", "Lucía Prueba", "Óscar Modelo", "Jaime Ñuñez", "Rocío Muestra",
)
CIUDADES = ("Villa Norte", "Puerto Sur", "Valle Alto", "Monte Verde", "Lago Azul")
ESTADOS = ("ACTIVO", "INACTIVO", "PENDIENTE")
CANALES = ("WEB", "TIENDA", "TELEFONO")
CATEGORIAS = ("A", "B", "C")
DESCRIPCIONES = ("Cuaderno", "Lapicero", "Regla", "Borrador", "Goma", "Carpeta", "Cinta")
DESCRIPCIONES_CON_TILDES = ("Lápiz", "Ñandú escolar", "Cuaderno", "Regla", "Sacapuntas")


@dataclass(frozen=True)
class Columna:
    """Una columna generada. `tipo` decide el valor; `vacios` es cuántas celdas quedan vacías."""

    nombre: str
    tipo: str
    args: tuple = ()
    vacios: int = 0


@dataclass(frozen=True)
class Entrada:
    """Un CSV de entrada: número de filas y columnas, en orden."""

    filas: int
    columnas: tuple[Columna, ...]


def col(nombre: str, tipo: str, *args: object, vacios: int = 0) -> Columna:
    """Atajo para declarar una columna.

    Tipos: secuencia, codigo, entero, decimal, texto_blancos, fecha, elige.
    """
    return Columna(nombre, tipo, tuple(args), vacios)


def generar_tabla(
    semilla: str, entrada: Entrada
) -> tuple[list[str], list[list[str]]]:
    """Genera encabezado y filas (texto) para una entrada, con la semilla dada."""
    rng = random.Random(f"{SEMILLA}:{semilla}")
    valores = [
        [_valor(columna, i, rng) for i in range(entrada.filas)] for columna in entrada.columnas
    ]
    for columna, columna_valores in zip(entrada.columnas, valores, strict=True):
        for indice in rng.sample(range(entrada.filas), columna.vacios):
            columna_valores[indice] = ""
    encabezado = [columna.nombre for columna in entrada.columnas]
    filas = [[columna_valores[i] for columna_valores in valores] for i in range(entrada.filas)]
    return encabezado, filas


def _valor(columna: Columna, indice: int, rng: random.Random) -> str:
    args = columna.args
    if columna.tipo == "secuencia":
        return str(args[0] + indice)
    if columna.tipo == "codigo":
        return f"{args[0]}-{args[1] + indice:03d}"
    if columna.tipo == "entero":
        return str(rng.randint(args[0], args[1]))
    if columna.tipo == "decimal":
        return f"{rng.uniform(args[0], args[1]):.2f}"
    if columna.tipo == "texto_blancos":
        # Decimal en texto con blancos iniciales, como lo deja un archivo de ancho fijo.
        return " " * rng.randint(1, 4) + f"{rng.uniform(args[0], args[1]):.2f}"
    if columna.tipo == "fecha":
        return f"{args[0]}-{rng.randint(args[1], args[2]):02d}-{rng.randint(1, 28):02d}"
    if columna.tipo == "elige":
        return rng.choice(args[0])
    raise ValueError(f"tipo de columna desconocido: {columna.tipo}")


def escribir_entrada(
    carpeta: Path, nombre: str, encabezado: list[str], filas: list[list[str]]
) -> None:
    """Escribe un CSV con `,`, comillas mínimas y fin de línea `\\n`."""
    carpeta.mkdir(parents=True, exist_ok=True)
    with (carpeta / f"{nombre}.csv").open("w", encoding="utf-8", newline="") as archivo:
        escritor = csv.writer(archivo, lineterminator="\n")
        escritor.writerow(encabezado)
        escritor.writerows(filas)
