"""Ejecuta los pasos de un programa SAS de validaciones con el oráculo SQL, paso a paso.

Recorre el programa en orden (después de expandir sus macros): PROC IMPORT carga la entrada,
DATA step se evalúa con `validaciones_sas_datos`, PROC SQL corre en SQLite con `oraculo_sql`
(su traducción `a_sqlite`), y PROC EXPORT anota qué tabla sale a qué archivo. Lo que no se puede
traducir no se inventa: la tabla queda en `no_verificadas` con el motivo, y las que dependen de ella
también.

Única reescritura sobre el texto SQL: `OUTER UNION CORR` pasa a `UNION ALL`. El traductor del
oráculo no la conoce, y en estos programas las columnas coinciden en nombre y orden (ver el informe
de `validaciones_cruce`).
"""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path

from corpus_lib.csv_tabla import Tabla
from corpus_lib.oraculo_sql import ErrorSql
from corpus_lib.sas_texto import sentencias
from corpus_lib.traduccion_sql import NoSoportado, a_sqlite
from validaciones_sas_datos import (
    crear_tabla,
    leer_dlm,
    leer_excelcs,
    leer_tabla,
    paso_data,
)

_DEFINICION = re.compile(
    r"%macro\s+(\w+)\s*(?:\((\w*)\))?\s*;(.*?)%mend\b[^;]*;", re.S | re.I
)
_LLAMADA = re.compile(r"%(\w+)\s*(?:\(([^()]*)\))?\s*;")
_DATAFILE = re.compile(r"datafile\s*=\s*['\"]([^'\"]+)['\"]", re.I)
_OUT = re.compile(r"\bout\s*=\s*WORK\.(\w+)", re.I)
_DBMS = re.compile(r"\bdbms\s*=\s*(\w+)", re.I)
_EXPORT_DATA = re.compile(r"\bdata\s*=\s*WORK\.(\w+)", re.I)
_OUTFILE = re.compile(r"outfile\s*=\s*['\"]([^'\"]+)['\"]", re.I)
_CREATE = re.compile(r"CREATE\s+TABLE\s+WORK\.(\w+)\s+AS\s", re.I)
_OUTER_UNION = re.compile(r"OUTER\s+UNION\s+CORR", re.I)


@dataclass
class Corrida:
    """Resultado de correr un programa: tablas verificadas, no verificadas y archivos exportados."""

    tablas: dict[str, Tabla] = field(default_factory=dict)
    no_verificadas: dict[str, str] = field(default_factory=dict)
    exportes: dict[str, str] = field(default_factory=dict)
    avisos: list[str] = field(default_factory=list)


def expandir(programa: str) -> str:
    """Expande las macros definidas en el programa, en el orden de sus llamadas."""
    definiciones: dict[str, tuple[str | None, str]] = {}

    def guardar(m: re.Match[str]) -> str:
        definiciones[m.group(1)] = (m.group(2) or None, m.group(3))
        return ""

    texto = _DEFINICION.sub(guardar, programa)
    for _ in range(50):
        cambio = False

        def expandir_una(m: re.Match[str]) -> str:
            nonlocal cambio
            nombre = m.group(1)
            if nombre in definiciones:
                parametro, cuerpo = definiciones[nombre]
                cambio = True
                if parametro is None:
                    return cuerpo
                argumento = (m.group(2) or "").strip()
                cuerpo = re.sub(rf"&{parametro}\.?", lambda _: argumento, cuerpo)
                return cuerpo
            if nombre.lower().startswith("web_"):
                cambio = True
                return ""
            return m.group(0)

        texto = _LLAMADA.sub(expandir_una, texto)
        if not cambio:
            break
    texto = re.sub(r"%(let|put)\b[^;]*;", "", texto, flags=re.I)
    return texto


def _insertar_supuestos(
    sentencias_: list[str], supuestos: list[tuple[str, str]]
) -> list[str]:
    """Pone sentencias extra (un supuesto del caso) justo antes del PROC SQL que crea `tabla`."""
    salida = list(sentencias_)
    for tabla, texto in supuestos:
        indice = next(
            (i for i, s in enumerate(salida)
             if _CREATE.match(s) and _CREATE.match(s).group(1).upper() == tabla.upper()),
            None,
        )  # fmt: skip
        if indice is None:
            raise ValueError(f"supuesto para {tabla}: no hay CREATE de esa tabla")
        inicio = max(i for i in range(indice) if salida[i].upper().startswith("PROC SQL"))
        salida[inicio:inicio] = sentencias(texto)
    return salida


def _bloque(lista: list[str], inicio: int, fin: str) -> int:
    """Índice de la sentencia `fin` (QUIT o RUN) que cierra el paso que empieza en `inicio`."""
    for j in range(inicio + 1, len(lista)):
        if lista[j].strip().upper() == fin:
            return j
    return len(lista)


def _nombre_archivo(ruta: str) -> str:
    return re.split(r"[\\/]", ruta)[-1]


def _cargar_entrada(carpeta: Path, paso: str) -> Tabla:
    dbms = _DBMS.search(paso)
    archivo = _DATAFILE.search(paso)
    if dbms is None or archivo is None:
        raise ValueError("PROC IMPORT sin DBMS o DATAFILE")
    ruta = carpeta / _nombre_archivo(archivo.group(1))
    if not ruta.is_file():
        raise ValueError(f"no hay entrada {ruta.name} en el caso")
    if dbms.group(1).upper() == "DLM":
        return leer_dlm(ruta)
    if dbms.group(1).upper() == "EXCELCS":
        return leer_excelcs(ruta)
    raise ValueError(f"DBMS={dbms.group(1)} no soportado en el puente")


def ejecutar(
    programa: str, carpeta: Path, supuestos: list[tuple[str, str]] | None = None
) -> Corrida:
    """Corre el programa sobre las entradas de `carpeta`; `supuestos` son (tabla, pasos SAS)."""
    lista = sentencias(expandir(programa))
    lista = _insertar_supuestos(lista, supuestos or [])
    corrida = Corrida()
    con = sqlite3.connect(":memory:")
    con.execute("PRAGMA case_sensitive_like = ON")
    try:
        i = 0
        while i < len(lista):
            paso = lista[i]
            cabecera = paso.upper()
            if cabecera.startswith("PROC SQL"):
                fin = _bloque(lista, i, "QUIT")
                for sentencia in lista[i + 1 : fin]:
                    _sql(con, corrida, sentencia)
                i = fin + 1
            elif cabecera.startswith("PROC IMPORT"):
                fin = _bloque(lista, i, "RUN")
                _importar(con, corrida, carpeta, " ".join(lista[i:fin]))
                i = fin + 1
            elif cabecera.startswith("PROC EXPORT"):
                fin = _bloque(lista, i, "RUN")
                _exportar(corrida, " ".join(lista[i:fin]))
                i = fin + 1
            elif cabecera.startswith("DATA "):
                fin = _bloque(lista, i, "RUN")
                _data(con, corrida, lista[i:fin])
                i = fin + 1
            else:
                i += 1
        for nombre in list(corrida.no_verificadas):
            corrida.tablas.pop(nombre, None)
        for nombre in _tablas_en_sqlite(con):
            if nombre not in corrida.no_verificadas:
                corrida.tablas[nombre] = leer_tabla(con, nombre)
    finally:
        con.close()
    return corrida


def _tablas_en_sqlite(con: sqlite3.Connection) -> list[str]:
    filas = con.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
    return [fila[0].upper() for fila in filas]


def _sql(con: sqlite3.Connection, corrida: Corrida, sentencia: str) -> None:
    m = _CREATE.match(sentencia)
    if m is None:
        corrida.avisos.append(f"sentencia SQL no CREATE TABLE WORK ignorada: {sentencia[:50]}")
        return
    nombre = m.group(1).upper()
    con.execute(f'DROP TABLE IF EXISTS "{nombre}"')
    try:
        con.execute(a_sqlite(_OUTER_UNION.sub("UNION ALL", sentencia)))
    except (NoSoportado, ErrorSql, sqlite3.Error, ValueError) as fallo:
        corrida.no_verificadas[nombre] = str(fallo)[:200]
        return
    corrida.no_verificadas.pop(nombre, None)


def _importar(con: sqlite3.Connection, corrida: Corrida, carpeta: Path, paso: str) -> None:
    salida = _OUT.search(paso)
    if salida is None:
        raise ValueError("PROC IMPORT sin OUT=WORK.")
    nombre = salida.group(1).upper()
    try:
        crear_tabla(con, nombre, _cargar_entrada(carpeta, paso))
    except (ValueError, OSError) as fallo:
        con.execute(f'DROP TABLE IF EXISTS "{nombre}"')
        corrida.no_verificadas[nombre] = str(fallo)[:200]
        return
    corrida.no_verificadas.pop(nombre, None)


def _exportar(corrida: Corrida, paso: str) -> None:
    origen = _EXPORT_DATA.search(paso)
    archivo = _OUTFILE.search(paso)
    if origen is None or archivo is None:
        raise ValueError("PROC EXPORT sin DATA= u OUTFILE=")
    nombre = _nombre_archivo(archivo.group(1))
    corrida.exportes[nombre[: -len(".csv")] if nombre.endswith(".csv") else nombre] = (
        origen.group(1).upper()
    )


def _data(con: sqlite3.Connection, corrida: Corrida, paso: list[str]) -> None:
    try:
        destino, _ = paso_data(con, paso)
    except (ValueError, ErrorSql, sqlite3.Error) as fallo:
        m = re.match(r"data\s+(?:WORK\.)?(\w+)", paso[0], re.I)
        if m is None:
            raise
        nombre = m.group(1).upper()
        con.execute(f'DROP TABLE IF EXISTS "{nombre}"')
        corrida.no_verificadas[nombre] = str(fallo)[:200]
        return
    corrida.no_verificadas.pop(destino.upper(), None)
