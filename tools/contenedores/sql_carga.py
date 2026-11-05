"""Genera el SQL de Impala que crea bases y tablas de prueba.

Dos orígenes: filas ficticias evidentes (`SIM_<columna>_<n>`) para tablas del programa SAS,
o las filas reales de un CSV de entrada. Todas las columnas son STRING, como pide el plan.
"""

import csv
from pathlib import Path

from fuentes_sas import TablaBase


def _identificador(nombre: str) -> str:
    """Identificador de Impala entre comillas invertidas (evita palabras reservadas)."""
    return "`" + nombre.replace("`", "") + "`"


def _literal(valor: str) -> str:
    return "'" + valor.replace("'", "''") + "'"


def _cabecera(biblioteca: str, tabla: str, columnas: tuple[str, ...]) -> list[str]:
    definicion = ",\n  ".join(f"{_identificador(c)} STRING" for c in columnas)
    return [
        f"CREATE DATABASE IF NOT EXISTS {biblioteca};",
        f"DROP TABLE IF EXISTS {biblioteca}.{tabla};",
        f"CREATE TABLE {biblioteca}.{tabla} (\n  {definicion}\n);",
    ]


def sentencias_ficticias(tabla: TablaBase, filas: int = 3) -> list[str]:
    """Crea la tabla y la llena con `filas` filas ficticias evidentes."""
    sentencias = _cabecera(tabla.biblioteca, tabla.tabla, tabla.columnas)
    valores = []
    for n in range(1, filas + 1):
        celdas = [_literal(f"SIM_{c}_{n}") for c in tabla.columnas]
        valores.append("(" + ", ".join(celdas) + ")")
    sentencias.append(
        f"INSERT INTO {tabla.biblioteca}.{tabla.tabla} VALUES\n  " + ",\n  ".join(valores) + ";"
    )
    return sentencias


def sentencias_desde_csv(biblioteca: str, tabla: str, ruta_csv: Path) -> list[str]:
    """Crea la tabla con las columnas de la cabecera del CSV y carga sus filas."""
    with ruta_csv.open(encoding="utf-8", newline="") as archivo:
        lector = csv.reader(archivo)
        columnas = tuple(next(lector))
        filas = [tuple(fila) for fila in lector if fila]
    sentencias = _cabecera(biblioteca.lower(), tabla.lower(), columnas)
    if filas:
        valores = ["(" + ", ".join(_literal(c) for c in fila) + ")" for fila in filas]
        sentencias.append(
            f"INSERT INTO {biblioteca.lower()}.{tabla.lower()} VALUES\n  "
            + ",\n  ".join(valores)
            + ";"
        )
    return sentencias


def sql_completo(bloques: list[list[str]]) -> str:
    """Une las sentencias de todas las tablas en un único script."""
    return "\n".join(s for bloque in bloques for s in bloque) + "\n"
