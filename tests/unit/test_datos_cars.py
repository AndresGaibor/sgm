"""Fixture inventado de vehículos: contrato, procedencia y regeneración sin deriva."""

from __future__ import annotations

import csv
import re
import sys
from collections import Counter
from dataclasses import replace
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

from datos_sinteticos.cars import MARCAS, escribir_cars, generar_cars  # noqa: E402
from datos_sinteticos.ficha import (  # noqa: E402
    Ficha,
    escribir_ficha,
    leer_ficha,
    validar_ficha,
)

DATA = REPO / "tests/fixtures/datos/sashelp"
HEADER = [
    "Make", "Model", "Type", "Origin", "DriveTrain", "MSRP", "Invoice", "EngineSize",
    "Cylinders", "Horsepower", "MPG_City", "MPG_Highway", "Weight", "Wheelbase", "Length",
]
COUNTS = {"Acura": 4, "Audi": 3, "BMW": 6, "Chevrolet": 8,
          "Ford": 5, "Honda": 4, "Jaguar": 3, "Toyota": 7}


def test_header_and_forty_rows():
    header, rows = generar_cars()
    assert header == HEADER
    assert len(rows) == 40
    assert all(len(row) == 15 and all(isinstance(cell, str) for cell in row) for row in rows)


def test_counts_and_fixed_brand_order():
    _, rows = generar_cars()
    assert Counter(row[0] for row in rows) == COUNTS == MARCAS
    assert [row[0] for row in rows] == [brand for brand, n in COUNTS.items() for _ in range(n)]


def test_seed_determines_data():
    assert generar_cars() == generar_cars(20261111)
    assert generar_cars(1) == generar_cars(1)
    assert generar_cars(1) != generar_cars()


@pytest.mark.parametrize("seed", [20261111, 1])
def test_declared_synthetic_values_and_relationships(seed):
    _, rows = generar_cars(seed)
    for row in rows:
        brand, model, kind, origin, drive, *numbers = row
        msrp, invoice, engine, cylinders, hp, city, highway, weight, wheelbase, length = (
            float(value) for value in numbers
        )
        assert re.fullmatch(rf"{brand} SIM-\d{{2}}", model)
        assert kind in {"Sedan", "SUV", "Sports", "Wagon", "Truck"}
        assert origin in {"Asia", "Europe", "USA"}
        assert drive in {"Front", "Rear", "All"}
        assert 18000 <= msrp <= 90000
        assert int(row[6]) == round(msrp * 0.93) < int(row[5])
        assert 1.4 <= engine <= 5.0 and cylinders in {4, 6, 8}
        assert 110 <= hp <= 450 and 12 <= city <= 35
        assert 5 <= highway - city <= 9 and int(row[11]) > int(row[10])
        assert 2400 <= weight <= 5500 and 96 <= wheelbase <= 125 and 160 <= length <= 215


def test_program_brands_are_present_in_versioned_csv():
    program = (REPO / "tests/fixtures/sas/client/client_poc.sas").read_text(encoding="utf-8")
    brands = set(re.findall(r"Make\s*=\s*'([^']+)'", program))
    assert len(brands) == 4
    with (DATA / "cars.csv").open(encoding="utf-8", newline="") as stream:
        present = {row["Make"] for row in csv.DictReader(stream)}
    assert brands <= present


def test_versioned_csv_and_metadata_regenerate_without_drift(tmp_path):
    generated = escribir_cars(tmp_path)
    assert generated == tmp_path / "cars.csv"
    assert generated.read_bytes() == (DATA / "cars.csv").read_bytes()
    assert b"\r" not in generated.read_bytes()
    assert (tmp_path / "cars.ficha.yaml").read_bytes() == (DATA / "cars.ficha.yaml").read_bytes()
    other = escribir_cars(tmp_path / "other", semilla=1)
    assert other.read_bytes() != generated.read_bytes()
    assert leer_ficha(other.with_suffix(".ficha.yaml")).semilla == 1
    with other.open(encoding="utf-8", newline="") as stream:
        assert list(csv.reader(stream)) == [generar_cars(1)[0], *generar_cars(1)[1]]


def test_metadata_explicitly_declares_synthetic_provenance():
    ficha = leer_ficha(DATA / "cars.ficha.yaml")
    assert validar_ficha(ficha, DATA / "cars.csv") == []
    assert ficha.tabla == "sashelp.cars" and ficha.filas == 40
    assert ficha.origen == "sintetico" and ficha.semilla == 20261111
    assert ficha.generador == "tools/datos_sinteticos/cars.py:generar_cars"
    assert list(ficha.columnas.items()) == [
        (name, "String" if index < 5 else "Double") for index, name in enumerate(HEADER)
    ]
    assert ficha.procedencia is None
    for text in ("inventados", "exportacion real", "tipo", "fixture", "no el SAS"):
        assert text in ficha.nota
    assert "no interviene en estos valores" in ficha.nota


def test_metadata_roundtrip_preserves_column_order(tmp_path):
    ficha = Ficha("demo", "real", 1, {"z": "String", "a": "Double"}, procedencia="exportación local")
    path = tmp_path / "demo.ficha.yaml"
    escribir_ficha(ficha, path)
    assert leer_ficha(path) == ficha
    assert list(leer_ficha(path).columnas) == ["z", "a"]


@pytest.mark.parametrize(("changes", "error"), [
    ({"semilla": None}, "origen sintetico sin semilla"),
    ({"generador": None}, "origen sintetico sin generador"),
    ({"generador": ""}, "origen sintetico sin generador"),
    ({"origen": "desconocido"}, "origen no permitido: desconocido"),
    ({"origen": "real", "procedencia": None}, "origen real sin procedencia"),
    ({"origen": "real", "procedencia": ""}, "origen real sin procedencia"),
    ({"filas": 39}, "numero de filas distinto: ficha=39, csv=40"),
    ({"columnas": {"Model": "String", "Make": "String"}}, "encabezado distinto de columnas"),
    ({"columnas": dict.fromkeys(reversed(HEADER), "String")}, "encabezado distinto de columnas"),
])
def test_invalid_metadata_returns_errors(changes, error):
    ficha = replace(leer_ficha(DATA / "cars.ficha.yaml"), **changes)
    assert validar_ficha(ficha, DATA / "cars.csv") == [error]


def test_zero_seed_and_real_provenance_are_valid():
    ficha = leer_ficha(DATA / "cars.ficha.yaml")
    assert validar_ficha(replace(ficha, semilla=0), DATA / "cars.csv") == []
    real = replace(ficha, origen="real", semilla=None, generador=None, procedencia="exportación")
    assert validar_ficha(real, DATA / "cars.csv") == []


def test_validar_ficha_con_comilla_sin_cerrar_conserva_lectura_historica(tmp_path):
    archivo = tmp_path / 'entrada.csv'
    archivo.write_text('"a', encoding='utf-8')
    ficha = Ficha('lib.t', 'real', 0, {'a': 'String'}, procedencia='prueba')
    assert validar_ficha(ficha, archivo) == []
