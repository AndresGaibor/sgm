"""Ficha de procedencia y validación de un CSV de prueba."""

from __future__ import annotations

import csv as csv_module
from dataclasses import asdict
from pathlib import Path

import yaml

from sgm.migrar.ficha import Ficha as Ficha
from sgm.migrar.ficha import leer_ficha as leer_ficha
from sgm.migrar.ficha import validar_procedencia


def escribir_ficha(ficha: Ficha, ruta: Path) -> None:
    """Escribe los campos y columnas en orden estable, sin etiquetas propias de Python."""
    content = yaml.safe_dump(asdict(ficha), sort_keys=False, allow_unicode=True)
    ruta.write_text(content, encoding="utf-8", newline="\n")


def validar_ficha(ficha: Ficha, csv: Path) -> list[str]:
    """Comprueba procedencia, cabecera en orden y cantidad de filas del CSV."""
    errors = validar_procedencia(ficha)
    with csv.open(encoding="utf-8", newline="") as stream:
        reader = csv_module.reader(stream)
        header = next(reader, [])
        count = sum(1 for _ in reader)
    if header != list(ficha.columnas):
        errors.append("encabezado distinto de columnas")
    if count != ficha.filas:
        errors.append(f"numero de filas distinto: ficha={ficha.filas}, csv={count}")
    return errors
