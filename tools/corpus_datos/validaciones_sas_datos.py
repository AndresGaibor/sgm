"""Pasos de datos del puente de cruce: PROC IMPORT (DLM y EXCELCS) y DATA step de los casos.

Las tablas viven en SQLite (la misma conexión que el PROC SQL del oráculo). Los DATA step se evalúan
con las funciones de la capa B (`corpus_semantica_funciones`), igual que `preparacion.py`. Lo que
no entiende (una función fuera de `input`, `left` y `compress`) lanza `ValueError` con el motivo.
"""

from __future__ import annotations

import csv
import re
import sqlite3
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from corpus_lib.csv_tabla import Tabla, tipo_sql
from corpus_semantica_funciones import Faltante, evaluar

_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
_CELDA = re.compile(r"([A-Z]+)\d+$")
_SET = re.compile(
    r"(?:work\.)?(\w+)(?:\(\s*rename\s*=\s*\(?\s*(\w+)\s*=\s*(\w+)\s*\)?\s*\))?", re.I
)
_ASIGNACION = re.compile(r"(\w+)\s*=\s*(.+)", re.S)


def _convertir(valor: str | None, tipo: str) -> object:
    if valor is None or valor == "":
        return None
    if tipo == "INTEGER":
        return int(valor)
    if tipo == "REAL":
        return float(valor)
    return valor


def leer_dlm(ruta: Path) -> Tabla:
    """PROC IMPORT DBMS=DLM con GETNAMES=NO: columnas VAR1..VARn, tipo por convención del corpus."""
    with ruta.open(encoding="utf-8-sig", newline="") as archivo:
        crudas = [fila for fila in csv.reader(archivo, delimiter=";") if fila]
    if not crudas:
        raise ValueError(f"{ruta.name}: archivo vacío")
    n = len(crudas[0])
    tipos = [tipo_sql([fila[j] if fila[j] != "" else None for fila in crudas]) for j in range(n)]
    filas = [tuple(_convertir(fila[j], tipos[j]) for j in range(n)) for fila in crudas]
    return Tabla([f"VAR{j + 1}" for j in range(n)], filas, tipos)


def leer_excelcs(ruta: Path) -> Tabla:
    """PROC IMPORT DBMS=EXCELCS de la primera hoja: la fila 1 es la cabecera; celdas de texto."""
    with zipfile.ZipFile(ruta) as paquete:
        raiz = ET.fromstring(paquete.read("xl/worksheets/sheet1.xml"))
    filas: list[dict[int, str]] = []
    for fila in raiz.iter(f"{_NS}row"):
        celdas: dict[int, str] = {}
        for celda in fila.findall(f"{_NS}c"):
            letras = _CELDA.match(celda.get("r", ""))
            if letras is None:
                raise ValueError(f"{ruta.name}: referencia de celda no válida")
            indice = _indice_columna(letras.group(1))
            celdas[indice] = "".join(t.text or "" for t in celda.iter(f"{_NS}t"))
        filas.append(celdas)
    if not filas:
        raise ValueError(f"{ruta.name}: hoja vacía")
    ancho = max(max(f) if f else 0 for f in filas) + 1
    matriz = [[f.get(j, "") for j in range(ancho)] for f in filas]
    columnas = matriz[0]
    cuerpo = [tuple(fila) for fila in matriz[1:]]
    return Tabla(columnas, cuerpo, ["TEXT"] * len(columnas))


def _indice_columna(letras: str) -> int:
    indice = 0
    for letra in letras:
        indice = indice * 26 + (ord(letra) - ord("A") + 1)
    return indice - 1


def tipo_columna(valores: list[object]) -> str:
    """Tipo SQLite de una columna creada por un DATA step: entero, real o texto."""
    presentes = [v for v in valores if v is not None]
    if all(isinstance(v, int) and not isinstance(v, bool) for v in presentes):
        return "INTEGER"
    if all(isinstance(v, (int, float)) for v in presentes):
        return "REAL"
    return "TEXT"


def crear_tabla(con: sqlite3.Connection, nombre: str, tabla: Tabla) -> None:
    """Reemplaza `nombre` en SQLite con las filas y los tipos de `tabla`."""
    tipos = [
        tipo_columna([fila[j] for fila in tabla.filas]) for j in range(len(tabla.columnas))
    ]
    definicion = ", ".join(f'"{c}" {t}' for c, t in zip(tabla.columnas, tipos, strict=True))
    con.execute(f'DROP TABLE IF EXISTS "{nombre}"')
    con.execute(f'CREATE TABLE "{nombre}" ({definicion})')
    if tabla.filas:
        marcas = ", ".join("?" * len(tabla.columnas))
        con.executemany(f'INSERT INTO "{nombre}" VALUES ({marcas})', tabla.filas)


def leer_tabla(con: sqlite3.Connection, nombre: str) -> Tabla:
    """Lee una tabla de SQLite con sus nombres de columna tal como quedaron."""
    cursor = con.execute(f'SELECT * FROM "{nombre}"')
    columnas = [descripcion[0] for descripcion in cursor.description]
    return Tabla(columnas, [tuple(fila) for fila in cursor.fetchall()])


def _texto(valor: object) -> str:
    """Un valor como texto, como lo recibe `left` o `compress`: faltante es blanco."""
    if valor is None:
        return ""
    if isinstance(valor, float) and valor.is_integer():
        return str(int(valor))
    return str(valor)


def _partir(args: str) -> list[str]:
    partes: list[str] = []
    actual = ""
    profundidad = 0
    for caracter in args:
        if caracter == "," and profundidad == 0:
            partes.append(actual.strip())
            actual = ""
            continue
        profundidad += (caracter == "(") - (caracter == ")")
        actual += caracter
    if actual.strip():
        partes.append(actual.strip())
    return partes


def evaluar_expresion(expr: str, fila: dict[str, object]) -> object:
    """Evalúa `expr` sobre una fila del DATA step: nombres, literales, `input`, `left`, `compress`.
    """
    e = expr.strip()
    if len(e) >= 2 and e[0] == e[-1] == "'":
        return e[1:-1]
    if re.fullmatch(r"\d+(\.\d*)?", e):
        return float(e)
    if re.fullmatch(r"[A-Za-z_]\w*", e):
        # Una variable que no está en el `set` ni se asigna queda en faltante (SAS la crea como
        # no inicializada, con una advertencia en el log). Así lo trata este puente.
        return fila.get(e.upper())
    m = re.fullmatch(r"([A-Za-z_]\w*)\((.*)\)", e, re.S)
    if m is None:
        raise ValueError(f"expresión no soportada en el puente: {e}")
    nombre = m.group(1).lower()
    args = [evaluar_expresion(a, fila) for a in _partir(m.group(2))]
    if nombre == "input":
        resultado = evaluar("input", _texto(args[0]), int(args[1]), 0)
        return None if isinstance(resultado, Faltante) else resultado
    if nombre in ("left", "compress"):
        return evaluar(nombre, _texto(args[0]))
    raise ValueError(f"función no soportada en el puente: {nombre}")


def _fuentes(texto: str) -> list[tuple[str, dict[str, str]]]:
    """Tablas de un `set`: nombre y renombrados `(rename=(viejo=nuevo))`."""
    salida = []
    for token in re.findall(r"(?:work\.)?\w+(?:\([^)]*\))?", texto, re.I):
        m = _SET.fullmatch(token)
        if m is None:
            raise ValueError(f"set no soportado en el puente: {token}")
        renombres = {m.group(2): m.group(3)} if m.group(2) else {}
        salida.append((m.group(1), renombres))
    return salida


def paso_data(con: sqlite3.Connection, sentencias: list[str]) -> tuple[str, Tabla]:
    """Ejecuta un DATA step (`set`, asignaciones, `drop`) y devuelve el nombre del destino."""
    m = re.fullmatch(r"data\s+(?:WORK\.)?(\w+)", sentencias[0], re.I)
    if m is None:
        raise ValueError(f"cabecera de DATA step no soportada: {sentencias[0][:60]}")
    destino = m.group(1)
    filas: list[dict[str, object]] = []
    columnas: list[str] | None = None
    asignaciones: list[tuple[str, str]] = []
    descartar: set[str] = set()
    for sentencia in sentencias[1:]:
        if sentencia.lower().startswith("format"):
            continue
        if sentencia.lower().startswith("set "):
            for tabla_origen, renombres in _fuentes(sentencia[4:]):
                origen = leer_tabla(con, tabla_origen)
                nombres = [renombres.get(c, c) for c in origen.columnas]
                if columnas is not None and [c.upper() for c in nombres] != [
                    c.upper() for c in columnas
                ]:
                    raise ValueError("set con tablas de columnas distintas no se soporta")
                columnas = nombres
                filas.extend(dict(zip(nombres, fila, strict=True)) for fila in origen.filas)
            continue
        if sentencia.lower().startswith("drop "):
            descartar.update(x.strip().upper() for x in sentencia[5:].split() if x.strip())
            continue
        m = _ASIGNACION.fullmatch(sentencia)
        if m is None:
            raise ValueError(f"sentencia de DATA step no soportada: {sentencia[:60]}")
        asignaciones.append((m.group(1), m.group(2)))
    if columnas is None:
        raise ValueError("el DATA step no tiene set")
    nombres_salida = list(columnas)
    for nombre, _ in asignaciones:
        if nombre.upper() not in [c.upper() for c in nombres_salida]:
            nombres_salida.append(nombre)
    for fila in filas:
        normal = {k.upper(): v for k, v in fila.items()}
        for nombre, expr in asignaciones:
            normal[nombre.upper()] = evaluar_expresion(expr, normal)
            fila[nombre] = normal[nombre.upper()]
    nombres_salida = [c for c in nombres_salida if c.upper() not in descartar]
    tabla = Tabla(
        nombres_salida,
        [tuple(_valor_sin_mayusculas(fila, c) for c in nombres_salida) for fila in filas],
    )
    crear_tabla(con, destino, tabla)
    return destino, tabla


def _valor_sin_mayusculas(fila: dict[str, object], columna: str) -> object:
    for clave, valor in fila.items():
        if clave.upper() == columna.upper():
            return valor
    return None
