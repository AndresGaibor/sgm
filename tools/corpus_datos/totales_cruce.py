"""Motor del cruce de los casos L8 de totales con el oráculo SQL (SQLite) del corpus.

Recorre el programa SAS en orden: `%let` y las llamadas a `%macro` se resuelven; cada sentencia de
`PROC SQL` se traduce con `corpus_lib.traduccion_sql.a_sqlite` y se ejecuta en SQLite. Lo que el
oráculo no puede ejecutar (INTO, `connect to IMPALA`) se anota como pendiente; los DATA steps y
PROC SORT se reproducen antes, en Python, y entran como tablas de entrada
(`totales_cruce_casos.py`).

Las celdas vacías siguen las convenciones de `corpus_lib` (ver DIFERENCIAS.md, "Faltantes de
texto"): en una columna de texto el blanco es `''`; en una numérica, NULL. Las tablas se crean con
`corpus_lib.esquema_sql` (COLLATE RTRIM), así que los blancos finales no cuentan al comparar.
OBS=, NE y OUTER UNION CORR los traduce el propio oráculo. La única sustitución que queda es la de
los nombres 'AÑO'n, que el traductor rechaza a propósito.
"""

from __future__ import annotations

import re
import sqlite3
import sys
from collections import Counter
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from corpus_lib.csv_tabla import Tabla as TablaCsv  # noqa: E402
from corpus_lib.esquema_sql import Esquema, crear_desde_consulta, crear_entrada  # noqa: E402
from corpus_lib.sas_texto import sentencias  # noqa: E402
from corpus_lib.traduccion_sql import NoSoportado, a_sqlite  # noqa: E402
from totales_cruce_io import Tabla, ordenado  # noqa: E402

# Sustituciones que aplica el cruce a cada sentencia SQL: (patrón, reemplazo, motivo).
SUSTITUCIONES_GENERALES = [
    (r"'([^']+)'n\b", r"\1", "nombre SAS con sufijo n ('AÑO'n) como identificador"),
]


class Pendiente(Exception):
    """Sentencia que el cruce no ejecuta; el mensaje es el motivo."""


@dataclass
class Resultado:
    """Lo que dejó la corrida de un caso: tablas de SQLite, pendientes y sustituciones."""

    caso: str
    tablas: dict[str, Tabla] = field(default_factory=dict)
    pendientes: list[str] = field(default_factory=list)
    sustituciones: Counter = field(default_factory=Counter)
    macros: dict[str, str] = field(default_factory=dict)
    preparadas: list[str] = field(default_factory=list)
    renombres: list[str] = field(default_factory=list)


def _texto(valor: object) -> str | None:
    """Texto de una celda de SQLite para compararla con el CSV esperado."""
    if valor is None:
        return None
    if isinstance(valor, float):
        return format(Decimal(repr(valor)).normalize(), "f")
    return str(valor)


def _sql(valor: object, numerico: bool) -> object:
    """Valor de Python a SQLite: los decimales de SAS entran como REAL. Un blanco es NULL en una
    columna numérica y cadena vacía en una de texto (ver DIFERENCIAS.md)."""
    if isinstance(valor, Decimal):
        return float(valor)
    if valor == "" and numerico:
        return None
    return valor


def _numerica(columna: str, tipos: dict[str, str], valores: list) -> bool:
    """Una columna es numérica si lo dice `tipos` o si todos sus valores presentes son números."""
    if columna in tipos:
        return tipos[columna] in ("INTEGER", "REAL")
    presentes = [v for v in valores if v is not None and v != ""]
    return bool(presentes) and all(isinstance(v, (Decimal, int)) for v in presentes)


class Corrida:
    """Ejecuta un programa SAS sobre SQLite, con las tablas de entrada ya preparadas."""

    def __init__(self, caso: str, entradas: dict[str, tuple], subs: list[tuple] = ()) -> None:
        self.con = sqlite3.connect(":memory:")
        self.con.execute("PRAGMA case_sensitive_like = ON")
        self.entradas = entradas
        self.res = Resultado(caso)
        self.macros: dict[str, str] = {}
        self.definiciones: dict[str, list[str]] = {}
        self.subs = [*SUSTITUCIONES_GENERALES, *subs]
        for nombre, (cols, filas, tipos) in entradas.items():
            self._cargar(nombre, cols, filas, tipos)

    def _esquema(self) -> Esquema:
        return Esquema.desde_conexion(self.con)

    def _cargar(self, nombre: str, cols: list[str], filas: list, tipos: dict[str, str]) -> None:
        """Crea la tabla de entrada con `corpus_lib`: texto, o número (INTEGER o REAL)."""
        numericas: list[bool] = []
        tipos_sql: list[str] = []
        for i, columna in enumerate(cols):
            valores = [f[i] for f in filas]
            es_numerica = _numerica(columna, tipos, valores)
            numericas.append(es_numerica)
            if not es_numerica:
                tipos_sql.append("TEXT")
            elif columna in tipos:
                tipos_sql.append(tipos[columna])
            else:
                decimal = any(isinstance(v, Decimal) for v in valores)
                tipos_sql.append("REAL" if decimal else "INTEGER")
        filas_sql = [
            tuple(_sql(v, n) for v, n in zip(f, numericas, strict=True)) for f in filas
        ]
        crear_entrada(self.con, nombre, TablaCsv(list(cols), filas_sql, tipos_sql))

    def correr(self, texto: str) -> Resultado:
        """Recorre las sentencias del programa en orden y devuelve el resultado."""
        self._ejecutar_lista(sentencias(texto))
        self.res.macros = dict(self.macros)
        return self.res

    def _ejecutar_lista(self, lista: list[str]) -> None:
        en_sql = False
        i = 0
        while i < len(lista):
            sentencia = lista[i]
            i += 1
            definicion = re.match(r"(?i)%macro\s+(\w+)", sentencia)
            if definicion:
                cuerpo = []
                while i < len(lista) and not re.match(r"(?i)%mend\b", lista[i]):
                    cuerpo.append(lista[i])
                    i += 1
                i += 1  # %mend
                self.definiciones[definicion.group(1).lower()] = cuerpo
                continue
            if re.match(r"(?i)%let\b", sentencia):
                self._let(sentencia)
                continue
            llamada = re.match(r"%(\w+)\s*\((.*)\)\s*$", sentencia, re.S)
            if llamada and llamada.group(1).lower() in self.definiciones:
                self._llamar(llamada.group(1).lower(), llamada.group(2))
                continue
            if en_sql:
                if re.match(r"(?i)QUIT\b", sentencia):
                    en_sql = False
                    continue
                self._sql(sentencia)
            elif re.match(r"(?i)PROC\s+SQL\b", sentencia):
                en_sql = True

    def _llamar(self, nombre: str, argumentos: str) -> None:
        """Llamada a macro: argumentos resueltos al llamar; los parámetros son locales."""
        parametros: dict[str, str] = {}
        for par in argumentos.split(","):
            if "=" in par:
                clave, valor = par.split("=", 1)
                try:
                    parametros[clave.strip().lower()] = self._resolver(valor.strip())
                except Pendiente:
                    pass  # sin valor: el parámetro queda sin definir dentro de la macro
        previos = {k: self.macros[k] for k in parametros if k in self.macros}
        self.macros.update(parametros)
        try:
            self._ejecutar_lista(self.definiciones[nombre])
        finally:
            for clave in parametros:
                self.macros.pop(clave, None)
            self.macros.update(previos)

    def _let(self, sentencia: str) -> None:
        m = re.match(r"(?is)%let\s+(\w+)\s*=\s*(.*)$", sentencia)
        if not m:
            return
        try:
            self.macros[m.group(1).lower()] = self._resolver(m.group(2).strip())
        except Pendiente as motivo:
            self.res.pendientes.append(f"%let {m.group(1)} ({motivo})")

    def _resolver(self, texto: str) -> str:
        """Sustituye &nombre. y &nombre por el valor de la macrovariable; si falta, pendiente."""
        def valor(m: re.Match) -> str:
            nombre = m.group(1).lower()  # las macrovariables de SAS no distinguen mayúsculas
            if nombre not in self.macros:
                raise Pendiente(f"macrovariable &{m.group(1)} sin valor")
            return self.macros[nombre]

        return re.sub(r"&(\w+)\.?", valor, texto)

    def _aplicar_subs(self, sql: str) -> str:
        for patron, reemplazo, _ in self.subs:
            sql, n = re.subn(patron, reemplazo, sql)
            if n:
                self.res.sustituciones[patron] += n
        return sql

    def _sql(self, sentencia: str) -> None:
        try:
            texto = self._aplicar_subs(self._resolver(sentencia))
            self._ejecutar_sql(texto)
        except (Pendiente, NoSoportado, sqlite3.Error) as motivo:
            self.res.pendientes.append(f"{' '.join(sentencia.split()[:4])} ({motivo})")

    def _ejecutar_sql(self, texto: str) -> None:
        if re.match(r"(?i)(connect|disconnect)\b", texto):
            raise Pendiente("conexión a IMPALA: se emula con CSV, no se ejecuta aquí")
        into = re.match(r"(?is)^SELECT\s+(.+?)\s+INTO\s*:\s*(\w+)\s+FROM\s+(.+)$", texto)
        if into:
            consulta = a_sqlite(f"SELECT {into.group(1)} FROM {into.group(3)}", self._esquema())
            cursor = self.con.execute(consulta)
            fila = cursor.fetchone()
            self.macros[into.group(2).lower()] = "" if fila is None else str(_texto(fila[0]))
            return
        paso = re.match(r"(?is)^CREATE\s+TABLE\s+WORK\.(\w+)\s+AS\s+SELECT\s+\*\s+FROM\s+"
                        r"CONNECTION\s+TO\s+IMPALA\s*\((.*)\)\s*$", texto)
        if paso:
            interna = paso.group(2)
            for prefijo in ("resultados_vspc_clientes.", "proceso_vspc_finanzas."):
                interna = interna.replace(prefijo, "")
            self._crear_tabla(paso.group(1), interna)
            return
        crear = re.match(r"(?is)^CREATE\s+TABLE\s+WORK\.(\w+)\s+AS\s+(.*)$", texto)
        if not crear:
            raise Pendiente("sentencia que no es CREATE TABLE ni INTO")
        nombre, resto = crear.group(1), crear.group(2)
        if nombre in self.entradas:
            self._comprobar_renombre(nombre, resto)
            return
        self._crear_tabla(nombre, a_sqlite(resto, self._esquema()))

    def _crear_tabla(self, nombre: str, consulta: str) -> None:
        """Crea `nombre` con el resultado del SELECT (con los tipos y el collation RTRIM)."""
        self.con.execute(f'DROP TABLE IF EXISTS "{nombre}"')
        crear_desde_consulta(self.con, nombre, consulta)
        cursor = self.con.execute(f'SELECT * FROM "{nombre}"')
        columnas = [d[0] for d in cursor.description]
        self.res.tablas[nombre] = (columnas, [[_texto(v) for v in f] for f in cursor.fetchall()])

    def _comprobar_renombre(self, nombre: str, consulta: str) -> None:
        """Una sentencia que crea una tabla ya preparada en Python: se ejecuta bajo otro nombre y
        se compara con la tabla preparada. Así el renombrado de VAR1..VARn se verifica."""
        self.res.preparadas.append(nombre)
        tmp = f"chequeo_{nombre}"
        self._crear_tabla(tmp, a_sqlite(consulta, self._esquema()))
        columnas, filas = self.res.tablas.pop(tmp)
        cols_py, filas_py, _ = self.entradas[nombre]
        posiciones = [cols_py.index(c) for c in columnas]
        # El faltante se compara como '' en ambos lados: un blanco y un NULL son lo mismo aquí.
        esperado = [[_texto(_sql(f[p], False)) or "" for p in posiciones] for f in filas_py]
        filas = [[v or "" for v in fila] for fila in filas]
        estado = "coincide" if ordenado(esperado) == ordenado(filas) else "NO COINCIDE"
        self.res.renombres.append(f"{nombre}: renombrado {estado}")
