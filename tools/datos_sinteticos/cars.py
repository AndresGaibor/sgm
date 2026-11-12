"""Datos inventados de vehículos; no son una exportación de SASHELP."""

from __future__ import annotations

import random
from pathlib import Path

from corpus_lib.datos_ficticios import SEMILLA, escribir_entrada

from .ficha import Ficha, escribir_ficha

SEMILLA_CARS = 20261111
COLUMNAS: tuple[tuple[str, str], ...] = (
    ("Make", "String"), ("Model", "String"), ("Type", "String"),
    ("Origin", "String"), ("DriveTrain", "String"), ("MSRP", "Double"),
    ("Invoice", "Double"), ("EngineSize", "Double"), ("Cylinders", "Double"),
    ("Horsepower", "Double"), ("MPG_City", "Double"), ("MPG_Highway", "Double"),
    ("Weight", "Double"), ("Wheelbase", "Double"), ("Length", "Double"),
)
MARCAS: dict[str, int] = {
    "Acura": 4, "Audi": 3, "BMW": 6, "Chevrolet": 8,
    "Ford": 5, "Honda": 4, "Jaguar": 3, "Toyota": 7,
}


def generar_cars(semilla: int = SEMILLA_CARS) -> tuple[list[str], list[list[str]]]:
    """Genera cuarenta filas en orden de marca fijo, con una semilla local independiente."""
    rng = random.Random(f"{semilla}:sashelp.cars")
    rows = []
    for brand, count in MARCAS.items():
        for index in range(1, count + 1):
            kind = rng.choice(("Sedan", "SUV", "Sports", "Wagon", "Truck"))
            origin = rng.choice(("Asia", "Europe", "USA"))
            drive = rng.choice(("Front", "Rear", "All"))
            msrp = rng.randint(18000, 90000)
            engine = f"{rng.uniform(1.4, 5.0):.1f}"
            cylinders = rng.choice((4, 6, 8))
            horsepower = rng.randint(110, 450)
            city = rng.randint(12, 35)
            highway = city + rng.randint(5, 9)
            weight = rng.randint(2400, 5500)
            wheelbase = rng.randint(96, 125)
            length = rng.randint(160, 215)
            rows.append([
                brand, f"{brand} SIM-{index:02d}", kind, origin, drive, str(msrp),
                str(round(msrp * 0.93)), engine, str(cylinders), str(horsepower),
                str(city), str(highway), str(weight), str(wheelbase), str(length),
            ])
    return [name for name, _ in COLUMNAS], rows


def escribir_cars(destino: Path, semilla: int = SEMILLA_CARS) -> Path:
    """Escribe cars.csv y su ficha explícitamente sintética; devuelve la ruta del CSV."""
    header, rows = generar_cars(semilla)
    escribir_entrada(destino, "cars", header, rows)
    ficha = Ficha(
        tabla="sashelp.cars",
        origen="sintetico",
        filas=len(rows),
        columnas=dict(COLUMNAS),
        semilla=semilla,
        generador="tools/datos_sinteticos/cars.py:generar_cars",
        nota=(
            "Conjunto sintetico con las 15 columnas de sashelp.cars; los valores son inventados. "
            "Reemplazar por la exportacion real cuando el usuario la aporte. "
            "El tipo de cada columna lo declara el fixture, no el SAS. "
            f"La semilla base del corpus ({SEMILLA}) es solo referencia y no interviene "
            "en estos valores; este generador usa exclusivamente la semilla de esta ficha."
        ),
    )
    escribir_ficha(ficha, destino / "cars.ficha.yaml")
    return destino / "cars.csv"
