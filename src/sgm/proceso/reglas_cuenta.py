"""Reglas de cuenta y GMF de R1-06, leídas del SAS (caso `v04_tipo_cta_gmf`).

El caso pequeño y el programa real escriben la misma idea de dos formas:

=============================  ================================  =============================
comprobación                   `v04/programa.sas`                `client_large.sas`
=============================  ================================  =============================
tipo de cuenta                 `TIPO_CTA NOT IN ('1'..'5')`      `TIPO_CTA NOT BETWEEN 1 AND 5`
GMF                            `GMF IS MISSING OR NOT BETWEEN`   `GMF NOT BETWEEN 1 AND 10`
control de relación            no                                `RELACION = 1000`
=============================  ================================  =============================

Aquí **solo se lee el caso pequeño**: es el que tiene esperados construidos de forma independiente
(`tools/corpus_datos/validaciones_esp_cuenta.py`). Las dos formas del rango del programa real se
comprueban aparte con `proceso.reglas.reglas`; no se sustituye una por la otra ni se unifican sus
motivos (en el real, el rango de GMF se llama `CODEX INVALIDO`).

Lo importante de la traducción es el **faltante de SAS**: un valor numérico faltante cuenta como
menor que cualquier número, así que `NOT BETWEEN 1 AND 10` ya lo incluye. `v04` lo escribe además
de forma explícita en el `WHERE` y le da su propio motivo con un `CASE`. Nada de esto se supone:
sale de las expresiones regulares de abajo.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_LISTA = re.compile(
    r"(?is)\b(?P<columna>[A-Z]\w*)\s+NOT\s+IN\s*\((?P<valores>[^)]*)\)"
)
_LITERAL = re.compile(r"'([^']*)'")
_RANGO_FALTANTE = re.compile(
    r"(?is)\b(?P<columna>[A-Z]\w*)\s+IS\s+MISSING\s*\)\s*OR\s*\(\s*"
    r"[\w.&]+\s+NOT\s+BETWEEN\s+(?P<desde>-?\d+)\s+AND\s+(?P<hasta>-?\d+)"
)
_CASO = re.compile(
    r"(?is)WHEN\s+[\w.&]+\s+IS\s+MISSING\s+THEN\s+'(?P<falta>[^']*)'"
    r"\s+ELSE\s+'(?P<rango>[^']*)'"
)
_MOTIVO_LISTA = re.compile(r"(?is)'([^']*)'\s+AS\s+INCONSISTENCIA")
_INFORMAT = re.compile(
    r"(?is)\b(?P<columna>\w+)\s*=\s*INPUT\s*\(\s*LEFT\s*\(\s*(?P<texto>\w+)\s*\)"
    r"\s*,\s*(?P<ancho>\d+)\.(?P<decimales>\d*)"
)
_ALIAS = re.compile(r"\bVAR(\d+)\s+AS\s+(\w+)", re.IGNORECASE)
_CREAR = re.compile(
    r"(?is)\bCREATE\s+TABLE\s+(?:WORK\.)?(?P<tabla>[\w&]+)\s+AS\s+"
    r"SELECT\s+(?P<cuerpo>.*?)\s+FROM\b"
)
_IDENTIFICADOR = re.compile(r"(?i)\b([A-Z_]\w*)\s*$")

# Tablas del SAS cuya proyección usa el Job. Las dos de cuenta deben coincidir.
TABLAS = {
    "tipo_cta": "INCONS_TIPO_CTA_INVALIDO_&SUFIJO",
    "gmf": "INCONS_GMF_INVALIDO_&SUFIJO",
    "valido": "SABANA_VALIDA_&SUFIJO",
    "cuenta": "INCONS_CUENTA_CTE",
}
_CUENTA_AHO = "INCONS_CUENTA_AHO"


@dataclass(frozen=True)
class ReglasCuenta:
    """Lo que el SAS demuestra para separar la sábana de `v04`."""

    columna_lista: str
    valores: tuple[str, ...]
    columna_rango: str
    desde: int
    hasta: int
    con_faltante: bool
    motivos: dict[str, str]
    columna_texto: str
    informat: tuple[int, int]
    alias: dict[str, str]
    proyecciones: dict[str, tuple[str, ...]]


def _partes(cuerpo: str) -> list[str]:
    """Separa la lista del `SELECT` por comas fuera de paréntesis y de literales."""
    resultado: list[str] = []
    actual: list[str] = []
    profundidad = 0
    comilla = ""
    for caracter in cuerpo:
        if comilla:
            actual.append(caracter)
            if caracter == comilla:
                comilla = ""
            continue
        if caracter in "'\"":
            comilla = caracter
            actual.append(caracter)
        elif caracter == "(":
            profundidad += 1
            actual.append(caracter)
        elif caracter == ")":
            profundidad -= 1
            actual.append(caracter)
        elif caracter == "," and profundidad == 0:
            resultado.append("".join(actual).strip())
            actual = []
        else:
            actual.append(caracter)
    resultado.append("".join(actual).strip())
    return [parte for parte in resultado if parte]


def _columna_select(parte: str) -> str:
    """Nombre de salida de un elemento del `SELECT`: su alias o el último identificador."""
    alias = re.search(r"(?is)\s+AS\s+(\w+)\s*$", parte)
    if alias is not None:
        return alias.group(1).upper()
    nombre = _IDENTIFICADOR.search(parte)
    if nombre is None:
        raise ValueError(f"No se puede leer la columna del SELECT: {parte!r}")
    return nombre.group(1).upper()


def proyecciones(texto: str) -> dict[str, tuple[str, ...]]:
    """Proyección de cada `CREATE TABLE ... AS SELECT`, por nombre de tabla en mayúsculas."""
    resultado: dict[str, tuple[str, ...]] = {}
    for crear in _CREAR.finditer(texto):
        columnas = tuple(_columna_select(p) for p in _partes(crear.group("cuerpo")))
        nombre = crear.group("tabla").upper()
        # El mismo nombre aparece una vez por producto (`&sufijo`); la forma debe ser la misma.
        anterior = resultado.get(nombre)
        if anterior is not None and anterior != columnas:
            raise ValueError(
                f"La tabla {nombre} tiene dos proyecciones distintas: {anterior}, {columnas}"
            )
        resultado[nombre] = columnas
    return resultado


def _proyecciones_flujo(texto: str) -> dict[str, tuple[str, ...]]:
    tablas = proyecciones(texto)
    resultado: dict[str, tuple[str, ...]] = {}
    for modo, tabla in TABLAS.items():
        if tabla not in tablas:
            raise ValueError(f"El SAS no declara la tabla {tabla} para el flujo '{modo}'")
        resultado[modo] = tablas[tabla]
    if _CUENTA_AHO in tablas and tablas[_CUENTA_AHO] != resultado["cuenta"]:
        raise ValueError("INCONS_CUENTA_CTE y _AHO no proyectan las mismas columnas")
    return resultado


def reglas_cuenta(texto: str) -> ReglasCuenta:
    """Lee del SAS la lista, el rango, el faltante, los motivos, el informat y las proyecciones.

    Un programa que no declara alguna de estas piezas no produce reglas a medias: se rechaza.
    """
    lista = _LISTA.search(texto)
    rango = _RANGO_FALTANTE.search(texto)
    caso = _CASO.search(texto)
    motivo_lista = _MOTIVO_LISTA.search(texto)
    informat = _INFORMAT.search(texto)
    if lista is None:
        raise ValueError("El SAS no declara `NOT IN (...)` para el tipo de cuenta")
    if rango is None:
        raise ValueError("El SAS no declara `IS MISSING OR NOT BETWEEN` para el GMF")
    if caso is None:
        raise ValueError("El SAS no declara el CASE que distingue el motivo del GMF")
    if motivo_lista is None:
        raise ValueError("El SAS no declara el motivo de los rechazos de tipo de cuenta")
    if informat is None:
        raise ValueError("El SAS no declara `input(left(...), w.d)` para el GMF")
    valores = tuple(_LITERAL.findall(lista.group("valores")))
    if not valores:
        raise ValueError("La lista de tipos de cuenta del SAS está vacía")
    alias = {nombre.upper(): f"VAR{n}" for n, nombre in _ALIAS.findall(texto)}
    if informat.group("texto").upper() not in alias:
        raise ValueError(
            f"El texto {informat.group('texto')} del informat no está entre los alias VARn del SAS"
        )
    return ReglasCuenta(
        columna_lista=lista.group("columna").upper(),
        valores=valores,
        columna_rango=rango.group("columna").upper(),
        desde=int(rango.group("desde")),
        hasta=int(rango.group("hasta")),
        con_faltante=True,
        motivos={
            "lista": motivo_lista.group(1),
            "faltante": caso.group("falta"),
            "rango": caso.group("rango"),
        },
        columna_texto=informat.group("texto").upper(),
        informat=(int(informat.group("ancho")), int(informat.group("decimales") or 0)),
        alias=alias,
        proyecciones=_proyecciones_flujo(texto),
    )


__all__ = ["ReglasCuenta", "TABLAS", "proyecciones", "reglas_cuenta"]
