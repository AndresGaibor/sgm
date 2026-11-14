"""Ejecución local acotada de SELECT pass-through sobre entradas sintéticas."""

from __future__ import annotations

import re
import sqlite3

import sqlglot
from sqlglot import exp

from sgm.ir.models import Operator
from sgm.ir.sql_portability import is_portable
from sgm.migrar.interprete_errores import NoSoportadoEnInterprete

_IDENTIFICADOR = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")
_DIALECTOS = {"impala": "hive", "postgres": "postgres"}
_ACCIONES_LECTURA = {
    sqlite3.SQLITE_SELECT,
    sqlite3.SQLITE_READ,
    sqlite3.SQLITE_FUNCTION,
}


def _consulta(sql: str, motor: str) -> tuple[exp.Select, str]:
    dialecto = _DIALECTOS.get(motor.lower())
    if dialecto is None:
        raise NoSoportadoEnInterprete("paso_directo", f"motor sin soporte local: {motor}")
    try:
        sentencias = sqlglot.parse(sql, read=dialecto)
    except sqlglot.errors.SqlglotError as error:
        raise NoSoportadoEnInterprete("paso_directo", "SQL pass-through no portable") from error
    if len(sentencias) != 1 or not isinstance(sentencias[0], exp.Select):
        raise NoSoportadoEnInterprete("paso_directo", "solo se ejecuta una consulta SELECT")
    consulta = sentencias[0]
    for funcion in consulta.find_all(exp.Func):
        if not is_portable(funcion.sql(dialect=dialecto)):
            nombre = funcion.sql_name().lower()
            raise NoSoportadoEnInterprete(
                "paso_directo", f"función no portable: {nombre}"
            )
    try:
        traducido = sqlglot.transpile(sql, read=dialecto, write="sqlite")
    except sqlglot.errors.SqlglotError as error:
        raise NoSoportadoEnInterprete("paso_directo", "SQL pass-through no portable") from error
    if len(traducido) != 1:
        raise NoSoportadoEnInterprete("paso_directo", "SQL pass-through no portable")
    return consulta, traducido[0]


def _tabla_de_entrada(nombre: str, entradas: dict[str, list[dict]]) -> list[dict]:
    indice: dict[str, list[dict]] = {
        str(clave).casefold(): filas for clave, filas in entradas.items()
    }
    exacta = indice.get(nombre.casefold())
    if exacta is not None:
        return exacta
    base = nombre.rsplit(".", 1)[-1].casefold()
    coincidencias = [filas for clave, filas in indice.items() if clave.rsplit(".", 1)[-1] == base]
    if len(coincidencias) == 1:
        return coincidencias[0]
    motivo = "tabla de entrada ausente" if not coincidencias else "tabla ambigua por nombre"
    raise NoSoportadoEnInterprete("paso_directo", f"{motivo}: {nombre}")


def _nombre_tabla(tabla: exp.Table) -> tuple[str, str, str]:
    partes = [str(parte) for parte in (tabla.catalog, tabla.db, tabla.name) if parte]
    if not partes or len(partes) > 2 or any(not _IDENTIFICADOR.fullmatch(p) for p in partes):
        raise NoSoportadoEnInterprete("paso_directo", "identificador de tabla no portable")
    if len(partes) == 2:
        return ".".join(partes), partes[0], partes[1]
    return partes[0], "main", partes[0]


def _cargar_tabla(
    conexion: sqlite3.Connection,
    tabla: exp.Table,
    entradas: dict[str, list[dict]],
    adjuntas: set[str],
) -> None:
    nombre, base, tabla_sql = _nombre_tabla(tabla)
    filas = _tabla_de_entrada(nombre, entradas)
    if base != "main" and base not in adjuntas:
        conexion.execute(f"ATTACH DATABASE ':memory:' AS \"{base}\"")
        adjuntas.add(base)

    normalizadas = [
        {str(clave).casefold(): valor for clave, valor in fila.items()} for fila in filas
    ]
    columnas = list(normalizadas[0]) if normalizadas else []
    if not columnas or any(not _IDENTIFICADOR.fullmatch(columna) for columna in columnas):
        raise NoSoportadoEnInterprete(
            "paso_directo", f"esquema de entrada vacío o no portable: {nombre}"
        )
    esperadas = set(columnas)
    if any(set(fila) != esperadas for fila in normalizadas):
        raise NoSoportadoEnInterprete(
            "paso_directo", f"filas con columnas inconsistentes: {nombre}"
        )

    prefijo = f'"{base}".' if base != "main" else ""
    definicion = ", ".join(f'"{columna}" TEXT' for columna in columnas)
    conexion.execute(f"CREATE TABLE {prefijo}\"{tabla_sql}\" ({definicion})")
    marcadores = ", ".join("?" for _ in columnas)
    valores = [tuple(fila[columna] for columna in columnas) for fila in normalizadas]
    if valores:
        conexion.executemany(
            f"INSERT INTO {prefijo}\"{tabla_sql}\" VALUES ({marcadores})", valores
        )


def _autorizar_solo_lectura(accion, arg1, arg2, base, origen) -> int:
    del arg1, arg2, base, origen
    return sqlite3.SQLITE_OK if accion in _ACCIONES_LECTURA else sqlite3.SQLITE_DENY


def leer(op: Operator, entradas: dict[str, list[dict]]) -> list[dict]:
    """Ejecuta SQL portable en SQLite en memoria; no abre conexiones externas."""
    sql = str(op.params.get("sql") or "")
    motor = str(op.params.get("engine") or "")
    consulta, sql_local = _consulta(sql, motor)
    tablas = list(consulta.find_all(exp.Table))
    if not tablas:
        raise NoSoportadoEnInterprete("paso_directo", "SELECT sin tablas de entrada")

    conexion = sqlite3.connect(":memory:")
    try:
        adjuntas: set[str] = set()
        vistas: set[tuple[str, str]] = set()
        for tabla in tablas:
            nombre, base, tabla_sql = _nombre_tabla(tabla)
            clave = (base.casefold(), tabla_sql.casefold())
            if clave in vistas:
                continue
            vistas.add(clave)
            _cargar_tabla(conexion, tabla, entradas, adjuntas)
        conexion.set_authorizer(_autorizar_solo_lectura)
        try:
            cursor = conexion.execute(sql_local)
            columnas = [str(descripcion[0]) for descripcion in cursor.description or ()]
            return [dict(zip(columnas, fila, strict=True)) for fila in cursor.fetchall()]
        except sqlite3.Error as error:
            raise NoSoportadoEnInterprete(
                "paso_directo", "SQLite no pudo ejecutar el SELECT con estas entradas"
            ) from error
    finally:
        conexion.close()


__all__ = ["leer"]
