"""Genera el SQL de Impala que crea bases y tablas de prueba.

Dos orígenes: filas ficticias evidentes (`SIM_<columna>_<n>`) para tablas del programa SAS,
o las filas reales de un CSV de entrada; los tipos demostrados se emiten explícitamente.
"""

import csv
import re
from collections.abc import Sequence
from pathlib import Path

from fuentes_sas import TablaBase

from sgm.ir.models import Column
from tools.datos_sinteticos.validacion import validar_columnas, validar_valor


def _identificador(nombre: str) -> str:
    """Identificador de Impala entre comillas invertidas (evita palabras reservadas)."""
    return "`" + nombre.replace("`", "") + "`"


def _literal(valor: str) -> str:
    return "'" + valor.replace("\\", "\\\\").replace("'", "''") + "'"


def _cabecera(biblioteca: str, tabla: str, columnas: tuple[str, ...]) -> list[str]:
    _nombre_seguro(biblioteca)
    _nombre_seguro(tabla)
    for columna in columnas:
        _nombre_seguro(columna)
    definicion = ",\n  ".join(f"{_identificador(c)} STRING" for c in columnas)
    return [
        f"CREATE DATABASE IF NOT EXISTS {biblioteca};",
        f"DROP TABLE IF EXISTS {biblioteca}.{tabla};",
        f"CREATE TABLE {biblioteca}.{tabla} (\n  {definicion}\n);",
    ]


def sentencias_ficticias(tabla: TablaBase, filas: int = 3) -> list[str]:
    """Crea la tabla y la llena con `filas` filas ficticias evidentes."""
    if filas < 0:
        raise ValueError("filas no puede ser negativo")
    sentencias = _cabecera(tabla.biblioteca, tabla.tabla, tabla.columnas)
    valores = []
    for n in range(1, filas + 1):
        celdas = [_literal(f"SIM_{c}_{n}") for c in tabla.columnas]
        valores.append("(" + ", ".join(celdas) + ")")
    if valores:
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


_TIPOS = {"Double": "DOUBLE", "Integer": "INT", "Long": "BIGINT"}


def _nombre_seguro(nombre: str) -> None:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*", nombre):
        raise ValueError(f"identificador no permitido: {nombre}")


def _valor_tipado(valor: str, tipo: str | None) -> str:
    validar_valor(valor, tipo)
    return valor if tipo in {"Integer", "Long", "Double"} else _literal(valor)


def sentencias_tipadas(
    biblioteca: str, tabla: str, columnas: Sequence[Column], filas: Sequence[Sequence[str]]
) -> list[str]:
    """Crea SQL tipado validando identificadores y celdas antes de emitirlo."""
    _nombre_seguro(biblioteca)
    _nombre_seguro(tabla)
    validar_columnas([c.name for c in columnas])
    for columna in columnas:
        _nombre_seguro(columna.name)
    definicion = ",\n  ".join(
        f"{_identificador(c.name)} {_TIPOS.get(c.type, 'STRING')}" for c in columnas
    )
    sentencias = [
        f"CREATE DATABASE IF NOT EXISTS {biblioteca};",
        f"DROP TABLE IF EXISTS {biblioteca}.{tabla};",
        f"CREATE TABLE {biblioteca}.{tabla} (\n  {definicion}\n);",
    ]
    valores = []
    for fila in filas:
        if len(fila) != len(columnas):
            raise ValueError(f"{biblioteca}.{tabla}: número incorrecto de celdas")
        valores.append(
            "("
            + ", ".join(_valor_tipado(v, c.type) for v, c in zip(fila, columnas, strict=True))
            + ")"
        )
    if valores:
        sentencias.append(
            f"INSERT INTO {biblioteca}.{tabla} VALUES\n  " + ",\n  ".join(valores) + ";"
        )
    return sentencias


def sql_conteos(tablas: Sequence[tuple[str, str]]) -> str:
    """Devuelve una consulta de conteo por tabla, unidas mediante UNION ALL."""
    sentencias = []
    for biblioteca, tabla in tablas:
        _nombre_seguro(biblioteca)
        _nombre_seguro(tabla)
        nombre = f"{biblioteca}.{tabla}"
        sentencias.append(f"select {_literal(nombre)} as tabla, count(*) as filas from {nombre}")
    return " union all\n".join(sentencias) + (";" if sentencias else "")
