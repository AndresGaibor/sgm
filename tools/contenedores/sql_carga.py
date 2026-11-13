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


_RESERVADAS = frozenset(
    """
ADD ALL ALTER ANALYTIC AND ANTI ANY ARRAY AS ASC AUTHORIZATION BETWEEN BIGINT BINARY BOOLEAN
BOTH BY CASE CAST CHANGE CHAR CHARACTER CHECK COLUMN COMMENT COMPUTE CONSTRAINT CREATE CROSS
CUBE CURRENT CURRENT_DATE CURRENT_TIMESTAMP CURRENT_USER DATABASE DATABASES DATE DATETIME DAY
DECIMAL DEFAULT DELETE DESC DESCRIBE DISTINCT DIV DOUBLE DROP ELSE END ESCAPE EXCEPT EXISTS
EXPLAIN EXTERNAL FALSE FETCH FIRST FLOAT FOLLOWING FOR FOREIGN FROM FULL FUNCTION GRANT GROUP
GROUPING HAVING IF ILIKE IN INNER INSERT INT INTEGER INTERSECT INTERVAL INTO INVALIDATE IS
JOIN LATERAL LEFT LIKE LIMIT LOCATION MAP METADATA MODIFY NOT NULL NULLS NUMERIC OFFSET ON OR
ORDER OUTER OVER OVERWRITE PARTITION PRECEDING PRIMARY RANGE REAL REFERENCES REGEXP RENAME REVOKE
RIGHT RLIKE ROLE ROLLUP ROW ROWS SCHEMA SELECT SEMI SET SHOW SMALLINT TABLE TABLES THEN TINYINT
TO TRANSFORM TRUE TRUNCATE UNBOUNDED UNION UNIQUE UPDATE UPSERT USE USER USING VALUES VARCHAR
VIEW WHEN WHERE WINDOW WITH
AGGREGATE APPX_COUNT_DISTINCT AVRO CACHED CLASS COLUMNS DATA DELIMITED DISTRIBUTE FIELDS
FILEFORMAT FORMAT FORMATTED FUNCTIONS IGNORE INCREMENTAL INPATH INTERMEDIATE KEY LAST LINES
LOAD MERGE PARTITIONED PARTITIONS REFRESH REPLACE ROLES SORT STATS STRAIGHT_JOIN STRING
TBLPROPERTIES TERMINATED TIMESTAMP
""".split()
)


def _parte_tabla(nombre: str) -> str:
    """Cita palabras reservadas sin cambiar la salida de nombres ordinarios."""
    return _identificador(nombre) if nombre.upper() in _RESERVADAS else nombre


def _literal(valor: str) -> str:
    return "'" + valor.replace("\\", "\\\\").replace("'", "''") + "'"


def _cabecera(biblioteca: str, tabla: str, columnas: tuple[str, ...]) -> list[str]:
    _nombre_seguro(biblioteca)
    _nombre_seguro(tabla)
    for columna in columnas:
        _nombre_seguro(columna)
    definicion = ",\n  ".join(f"{_identificador(c)} STRING" for c in columnas)
    return [
        f"CREATE DATABASE IF NOT EXISTS {_parte_tabla(biblioteca)};",
        f"DROP TABLE IF EXISTS {_parte_tabla(biblioteca)}.{_parte_tabla(tabla)};",
        f"CREATE TABLE {_parte_tabla(biblioteca)}.{_parte_tabla(tabla)} (\n  {definicion}\n);",
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
            f"INSERT INTO {_parte_tabla(tabla.biblioteca)}.{_parte_tabla(tabla.tabla)} VALUES\n  "
            + ",\n  ".join(valores)
            + ";"
        )
    return sentencias


def sentencias_desde_csv_con_conteo(
    biblioteca: str, tabla: str, ruta_csv: Path
) -> tuple[list[str], int]:
    """Crea SQL desde el CSV y devuelve el número exacto de filas emitidas."""
    with ruta_csv.open(encoding="utf-8", newline="") as archivo:
        lector = csv.reader(archivo)
        columnas = tuple(next(lector))
        filas = [tuple(fila) for fila in lector if fila]
    biblioteca, tabla = biblioteca.lower(), tabla.lower()
    sentencias = _cabecera(biblioteca, tabla, columnas)
    if filas:
        valores = ["(" + ", ".join(_literal(c) for c in fila) + ")" for fila in filas]
        destino = f"{_parte_tabla(biblioteca)}.{_parte_tabla(tabla)}"
        sentencias.append(f"INSERT INTO {destino} VALUES\n  " + ",\n  ".join(valores) + ";")
    return sentencias, len(filas)


def sentencias_desde_csv(biblioteca: str, tabla: str, ruta_csv: Path) -> list[str]:
    """Crea la tabla y carga las filas del CSV, conservando la interfaz anterior."""
    return sentencias_desde_csv_con_conteo(biblioteca, tabla, ruta_csv)[0]


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
        f"CREATE DATABASE IF NOT EXISTS {_parte_tabla(biblioteca)};",
        f"DROP TABLE IF EXISTS {_parte_tabla(biblioteca)}.{_parte_tabla(tabla)};",
        f"CREATE TABLE {_parte_tabla(biblioteca)}.{_parte_tabla(tabla)} (\n  {definicion}\n);",
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
            f"INSERT INTO {_parte_tabla(biblioteca)}.{_parte_tabla(tabla)} VALUES\n  "
            + ",\n  ".join(valores)
            + ";"
        )
    return sentencias


def sql_conteos(tablas: Sequence[tuple[str, str]]) -> str:
    """Devuelve una consulta de conteo por tabla, unidas mediante UNION ALL."""
    sentencias = []
    for biblioteca, tabla in tablas:
        _nombre_seguro(biblioteca)
        _nombre_seguro(tabla)
        nombre = f"{biblioteca}.{tabla}"
        sentencias.append(
            f"select {_literal(nombre)} as tabla, count(*) as filas from "
            f"{_parte_tabla(biblioteca)}.{_parte_tabla(tabla)}"
        )
    return " union all\n".join(sentencias) + (";" if sentencias else "")
