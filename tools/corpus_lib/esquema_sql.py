"""Esquema de las tablas SQLite del oráculo: tipos de columna y carga de tablas.

Convenciones (ver `DIFERENCIAS.md`, sección "Convenciones de datos"):
- Cada columna se declara con `COLLATE RTRIM`: SQLite compara texto sin los blancos finales, como
  SAS. El collation solo afecta a los textos; los números no cambian.
- Una tabla creada con `CREATE TABLE ... AS SELECT` pierde el collation: se recrea con él.
- `IS MISSING` depende del tipo de la columna (texto: vacío o NULL; número: NULL), así que el
  traductor consulta el `Esquema`.
"""

from __future__ import annotations

import sqlite3

from .csv_tabla import Tabla

TEXTO = "TEXT"
NUMERICO = "NUMERICO"
_NUMERICOS_SQLITE = frozenset({"INTEGER", "INT", "REAL", "NUM", "NUMERIC", "FLOAT", "DOUBLE"})


def _tipo_declarado(declarado: str) -> str | None:
    """Clasifica un tipo declarado de SQLite. None si no es claro (p. ej. expresión sin tipo)."""
    bajo = declarado.strip().upper()
    if bajo == "TEXT":
        return TEXTO
    if bajo in _NUMERICOS_SQLITE:
        return NUMERICO
    return None


class Esquema:
    """Columnas de las tablas de una conexión, con el tipo que importa a `IS MISSING`."""

    def __init__(self, tablas: dict[str, list[tuple[str, str]]]) -> None:
        """`tablas`: nombre de tabla -> [(columna, tipo declarado)]."""
        self._tablas = {nombre.lower(): columnas for nombre, columnas in tablas.items()}

    @classmethod
    def desde_conexion(cls, con: sqlite3.Connection) -> Esquema:
        """Lee el esquema de las tablas de la conexión, también de las que creó el programa."""
        consulta = "SELECT name FROM sqlite_master WHERE type='table'"
        nombres = [fila[0] for fila in con.execute(consulta)]
        tablas: dict[str, list[tuple[str, str]]] = {}
        for nombre in nombres:
            info = con.execute(f'PRAGMA table_info("{nombre}")').fetchall()
            tablas[nombre] = [(fila[1], fila[2] or "") for fila in info]
        return cls(tablas)

    def columnas(self, tabla: str) -> list[str] | None:
        """Nombres de columna de una tabla, o None si la tabla no existe."""
        definicion = self._tablas.get(tabla.lower())
        return None if definicion is None else [columna for columna, _ in definicion]

    def tipo(self, columna: str) -> str | None:
        """TEXT o NUMERICO si todas las tablas que tienen la columna coinciden; si no, None."""
        tipos = {
            _tipo_declarado(declarado)
            for definicion in self._tablas.values()
            for nombre, declarado in definicion
            if nombre.lower() == columna.lower()
        }
        if len(tipos) == 1:
            return tipos.pop()
        return None


def crear_entrada(con: sqlite3.Connection, nombre: str, tabla: Tabla) -> None:
    """Crea una tabla de entrada con sus filas. Las columnas llevan `COLLATE RTRIM`."""
    definicion = ", ".join(
        f'"{columna}" {tipo} COLLATE RTRIM'
        for columna, tipo in zip(tabla.columnas, tabla.tipos, strict=True)
    )
    con.execute(f'CREATE TABLE "{nombre}" ({definicion})')
    marcas = ", ".join("?" * len(tabla.columnas))
    con.executemany(f'INSERT INTO "{nombre}" VALUES ({marcas})', tabla.filas)


def crear_desde_consulta(con: sqlite3.Connection, nombre: str, consulta: str) -> None:
    """Crea `nombre` con el resultado de un SELECT de SQLite, conservando los tipos y el collation.

    Primero se crea una tabla temporal con `CREATE TABLE ... AS`; luego se recrea `nombre` con los
    mismos tipos declarados y `COLLATE RTRIM`, y se copian las filas en el mismo orden.
    """
    temporal = f"_tmp_{nombre}"
    con.execute(f'CREATE TABLE "{temporal}" AS {consulta}')
    try:
        info = con.execute(f'PRAGMA table_info("{temporal}")').fetchall()
        partes = []
        for fila in info:
            piezas = [f'"{fila[1]}"', fila[2] or "", "COLLATE RTRIM"]
            partes.append(" ".join(pieza for pieza in piezas if pieza))
        con.execute(f'CREATE TABLE "{nombre}" ({", ".join(partes)})')
        con.execute(f'INSERT INTO "{nombre}" SELECT * FROM "{temporal}"')
    finally:
        con.execute(f'DROP TABLE "{temporal}"')
