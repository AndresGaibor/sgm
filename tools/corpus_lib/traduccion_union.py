"""Traducción de `SELECT ... OUTER UNION CORR SELECT ...` de SAS a `UNION ALL` de SQLite.

SAS apila las filas de los dos SELECT alineando las columnas por nombre (CORR). Las columnas que
solo tiene un lado quedan en NULL para el otro. Aquí se calcula la lista de nombres de los dos
lados y cada SELECT se envuelve en una subconsulta que rellena con `NULL AS nombre` las que faltan.

Solo se soportan dos SELECT. Los nombres de salida salen de la lista de columnas: `AS nombre`,
`tabla.columna` o `columna`; `SELECT *` solo sobre una tabla conocida por el esquema.
"""

from __future__ import annotations

import re

from .esquema_sql import Esquema
from .sql_partes import buscar_fuera_de_parentesis, dividir_fuera_de_parentesis
from .traduccion_error import NoSoportado

_OUTER_UNION = re.compile(r"(?i)\bOUTER\s+UNION\s+CORR\b")
_CREATE_PREFIJO = re.compile(r"(?is)^\s*(CREATE\s+TABLE\s+[A-Za-z_]\w*\s+AS\s+)")
_FROM = re.compile(r"(?i)\bFROM\b")
_CON_ALIAS = re.compile(r"(?is)^(.*\S)\s+AS\s+([A-Za-z_]\w*)$")
_COLUMNA_CON_TABLA = re.compile(r"^[A-Za-z_]\w*\.([A-Za-z_]\w*)$")
_COLUMNA = re.compile(r"^[A-Za-z_]\w*$")


def expandir_outer_union(texto: str, esquema: Esquema) -> str:
    """Reemplaza las cadenas de `OUTER UNION CORR` de la sentencia por `UNION ALL`."""
    separadores = buscar_fuera_de_parentesis(texto, _OUTER_UNION)
    if not separadores:
        return texto
    prefijo = ""
    primera = texto[: separadores[0].start()]
    prefijo_m = _CREATE_PREFIJO.match(primera)
    if prefijo_m:
        prefijo = prefijo_m.group(1)
    selects: list[str] = []
    inicio = prefijo_m.end() if prefijo_m else 0
    for separador in separadores:
        selects.append(texto[inicio : separador.start()].strip())
        inicio = separador.end()
    selects.append(texto[inicio:].strip())
    return prefijo + _union_all(selects, esquema)


def _union_all(selects: list[str], esquema: Esquema) -> str:
    """Une los SELECT por nombre de columna: cada uno se envuelve y rellena lo que le falta."""
    columnas = [_columnas_del_select(select, esquema) for select in selects]
    nombres: list[str] = []
    for lista in columnas:
        for nombre in lista:
            if nombre.lower() not in {n.lower() for n in nombres}:
                nombres.append(nombre)
    partes = []
    for indice, (select, cols) in enumerate(zip(selects, columnas, strict=True)):
        presentes = {columna.lower() for columna in cols}
        elementos = ", ".join(
            n if n.lower() in presentes else f"NULL AS {n}" for n in nombres
        )
        partes.append(f"SELECT {elementos} FROM ({select}) AS _ou_{indice}")
    return " UNION ALL ".join(partes)


def _columnas_del_select(select: str, esquema: Esquema) -> list[str]:
    """Nombres de salida, en orden, de un SELECT simple."""
    if not re.match(r"(?i)SELECT\s", select):
        raise NoSoportado("OUTER UNION CORR entre algo que no es un SELECT")
    cuerpo = select[len("SELECT") :].strip()
    if re.match(r"(?i)DISTINCT\b", cuerpo):
        raise NoSoportado("OUTER UNION CORR con SELECT DISTINCT")
    desde = buscar_fuera_de_parentesis(cuerpo, _FROM)
    if not desde:
        raise NoSoportado("OUTER UNION CORR sin FROM")
    lista = cuerpo[: desde[0].start()]
    nombres: list[str] = []
    for elemento in dividir_fuera_de_parentesis(lista):
        nombres += _nombres_del_elemento(elemento, cuerpo[desde[0].end() :], esquema)
    return nombres


def _nombres_del_elemento(elemento: str, resto_desde: str, esquema: Esquema) -> list[str]:
    if elemento == "*":
        tabla = re.match(r"\s*([A-Za-z_]\w*)", resto_desde)
        columnas = esquema.columnas(tabla.group(1)) if tabla else None
        if columnas is None:
            raise NoSoportado("SELECT * de una tabla que el esquema no conoce")
        return columnas
    if elemento.endswith("*"):
        raise NoSoportado("SELECT tabla.* dentro de OUTER UNION CORR")
    con_alias = _CON_ALIAS.match(elemento)
    if con_alias:
        return [con_alias.group(2)]
    con_tabla = _COLUMNA_CON_TABLA.match(elemento)
    if con_tabla:
        return [con_tabla.group(1)]
    if _COLUMNA.match(elemento):
        return [elemento]
    raise NoSoportado(f"columna sin nombre en OUTER UNION CORR ({elemento[:40]})")
