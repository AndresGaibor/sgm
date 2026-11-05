"""Oráculo de capa A: ejecuta el PROC SQL de un programa SAS en SQLite sobre las entradas CSV.

Cada sentencia debe ser `CREATE TABLE WORK.X AS SELECT ...`. Cualquier otra forma se rechaza.
La conexión usa `case_sensitive_like` para que LIKE distinga mayúsculas, como en SAS, y las
columnas de texto comparan sin blancos finales (ver `esquema_sql.py` y DIFERENCIAS.md).
"""

from __future__ import annotations

import re
import sqlite3

from .csv_tabla import Tabla
from .esquema_sql import Esquema, crear_desde_consulta, crear_entrada
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
            _ejecutar(crear_entrada, (con, nombre, tabla), f"entrada {nombre}")
        for sentencia in sentencias:
            casa = _CREATE.match(sentencia)
            if not casa:
                primeras = " ".join(sentencia.split()[:4])
                raise NoSoportado(f"sentencia que no es CREATE TABLE WORK.X AS ({primeras} ...)")
            consulta = a_sqlite(sentencia[casa.end() :], Esquema.desde_conexion(con))
            _ejecutar(crear_desde_consulta, (con, casa.group(1), consulta), consulta[:120])
        return {nombre: _leer(con, nombre) for nombre in salidas}
    finally:
        con.close()


def _ejecutar(funcion, argumentos: tuple, etiqueta: str) -> None:
    """Llama a una función de creación de tablas y convierte su error de SQLite en `ErrorSql`."""
    try:
        funcion(*argumentos)
    except sqlite3.Error as error:
        raise ErrorSql(f"SQLite rechazó la sentencia ({error}): {etiqueta}") from None


def _leer(con: sqlite3.Connection, nombre: str) -> Tabla:
    try:
        cursor = con.execute(f'SELECT * FROM "{nombre}"')
    except sqlite3.Error:
        raise ErrorSql(f"la salida '{nombre}' no se creó con CREATE TABLE WORK.{nombre}") from None
    columnas = [descripcion[0] for descripcion in cursor.description]
    return Tabla(columnas, [tuple(fila) for fila in cursor.fetchall()])
