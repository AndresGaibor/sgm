"""Ficha de procedencia y validación de un CSV de prueba."""

from __future__ import annotations

import csv as csv_module
from dataclasses import asdict, dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class Ficha:
    """Origen y tipos declarados por el fixture; no se infieren de los valores."""

    tabla: str
    origen: str
    filas: int
    columnas: dict[str, str]
    semilla: int | None = None
    generador: str | None = None
    procedencia: str | None = None
    nota: str = ""


def leer_ficha(ruta: Path) -> Ficha:
    """Lee una ficha YAML conservando el orden declarado de las columnas."""
    return Ficha(**yaml.safe_load(ruta.read_text(encoding="utf-8")))


def escribir_ficha(ficha: Ficha, ruta: Path) -> None:
    """Escribe los campos y columnas en orden estable, sin etiquetas propias de Python."""
    content = yaml.safe_dump(asdict(ficha), sort_keys=False, allow_unicode=True)
    ruta.write_text(content, encoding="utf-8", newline="\n")


def validar_ficha(ficha: Ficha, csv: Path) -> list[str]:
    """Comprueba procedencia, cabecera en orden y cantidad de filas del CSV."""
    errors = []
    if ficha.origen not in {"sintetico", "real"}:
        errors.append(f"origen no permitido: {ficha.origen}")
    if ficha.origen == "sintetico":
        if ficha.semilla is None:
            errors.append("origen sintetico sin semilla")
        if not ficha.generador:
            errors.append("origen sintetico sin generador")
    if ficha.origen == "real" and not ficha.procedencia:
        errors.append("origen real sin procedencia")
    with csv.open(encoding="utf-8", newline="") as stream:
        reader = csv_module.reader(stream)
        header = next(reader, [])
        count = sum(1 for _ in reader)
    if header != list(ficha.columnas):
        errors.append("encabezado distinto de columnas")
    if count != ficha.filas:
        errors.append(f"numero de filas distinto: ficha={ficha.filas}, csv={count}")
    return errors
