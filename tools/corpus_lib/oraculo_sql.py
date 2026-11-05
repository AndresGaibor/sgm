"""Oráculo de capa A: ejecuta el PROC SQL de un programa SAS en SQLite sobre las entradas CSV.

Cada sentencia debe ser `CREATE TABLE WORK.X AS SELECT ...`. Cualquier otra forma se rechaza.
La conexión usa `case_sensitive_like` para que LIKE distinga mayúsculas, como en SAS
(ver DIFERENCIAS.md).
"""

from __future__ import annotations

import re
import sqlite3

from .csv_tabla import Tabla
from .traduccion_sql import NoSoportado, a_sqlite

_CREATE = re.compile(r"CREATE\s+TABLE\s+WORK\.([A-Za-z_]\w*)\s+AS\s+", re.IGNORECASE)


class ErrorSql(Exception):
    """SQLite rechazó una sentencia traducida: falla la traducción o el programa SAS."""


def ejecutar_proc_sql(
    sentencias: list[str], entradas: dict[str, Tabla], salidas: list[str]
) -> dict[str, Tabla]:
    """Ejecuta las sentencias sobre las entradas y devuelve las tablas pedidas en `salidas`."""
    con = sqlite3.connect(":memory:")
    try:
        con.execute("PRAGMA case_sensitive_like = ON")
        for nombre, tabla in entradas.items():
            _cargar(con, nombre, tabla)
        for sentencia in sentencias:
            if not _CREATE.match(sentencia):
                primeras = " ".join(sentencia.split()[:4])
                raise NoSoportado(f"sentencia que no es CREATE TABLE WORK.X AS ({primeras} ...)")
            _ejecutar(con, a_sqlite(sentencia))
        return {nombre: _leer(con, nombre) for nombre in salidas}
    finally:
        con.close()


def _cargar(con: sqlite3.Connection, nombre: str, tabla: Tabla) -> None:
    definicion = ", ".join(
        f'"{columna}" {tipo}' for columna, tipo in zip(tabla.columnas, tabla.tipos, strict=True)
    )
    _ejecutar(con, f'CREATE TABLE "{nombre}" ({definicion})')
    marcas = ", ".join("?" * len(tabla.columnas))
    con.executemany(f'INSERT INTO "{nombre}" VALUES ({marcas})', tabla.filas)


def _ejecutar(con: sqlite3.Connection, sql: str) -> None:
    try:
        con.execute(sql)
    except sqlite3.Error as error:
        raise ErrorSql(f"SQLite rechazó la sentencia ({error}): {sql[:120]}") from None


def _leer(con: sqlite3.Connection, nombre: str) -> Tabla:
    try:
        cursor = con.execute(f'SELECT * FROM "{nombre}"')
    except sqlite3.Error:
        raise ErrorSql(f"la salida '{nombre}' no se creó con CREATE TABLE WORK.{nombre}") from None
    columnas = [descripcion[0] for descripcion in cursor.description]
    return Tabla(columnas, [tuple(fila) for fila in cursor.fetchall()])
