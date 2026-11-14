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
    fields = asdict(ficha)
    if ficha.cabecera is None:
        fields.pop("cabecera")
    if ficha.delimitador is None:
        fields.pop("delimitador")
    content = yaml.safe_dump(fields, sort_keys=False, allow_unicode=True)
    ruta.write_text(content, encoding="utf-8", newline="\n")


def validar_ficha(ficha: Ficha, csv: Path) -> list[str]:
    """Comprueba procedencia, formato de cabecera y forma de cada fila."""
    errors = validar_procedencia(ficha)
    delimiter = ficha.delimitador or ","
    if len(delimiter) != 1 or delimiter in "\r\n\"":
        return errors + ["delimitador de ficha no válido"]
    with csv.open(encoding="utf-8", newline="") as stream:
        reader = csv_module.reader(stream, delimiter=delimiter, strict=False)
        first = next(reader, None)
        if ficha.cabecera is False:
            rows = [] if first is None else [first]
            rows.extend(reader)
            for numero, row in enumerate(rows, start=1):
                if len(row) != len(ficha.columnas):
                    errors.append(
                        f"línea {numero}: {len(row)} campos, se esperaban {len(ficha.columnas)}"
                    )
        else:
            if first != list(ficha.columnas):
                errors.append("encabezado distinto de columnas")
            rows = list(reader)
        count = len(rows)
    if count != ficha.filas:
        errors.append(f"numero de filas distinto: ficha={ficha.filas}, csv={count}")
    return errors
