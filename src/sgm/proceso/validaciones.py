"""Detección del patrón de validación por lookup en el SQL del programa SAS.

El programa valida una columna contra un catálogo importado de Excel con una pareja de consultas:

- rechazos: `FROM <sabana> LEFT JOIN <catálogo> ON (<sabana>.<col> = <catálogo>.<col2>)
  WHERE <catálogo>.<col2> IS MISSING` (o `IS NULL`);
- válidos: el mismo `ON` con `INNER JOIN`.

Solo cuenta como validación si el catálogo sale de un `PROC IMPORT`: un `LEFT JOIN` contra otro
dataset de SAS y el mismo filtro es un cruce con descarte de sobrantes, no una homologación.

La columna de la sabana, la columna del catálogo y su dataset salen del SAS. El archivo no se
supone: `ruta_de_dataset` une el dataset con su `PROC IMPORT` para resolverlo después con
`InsumoResuelto`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from sgm.proceso.columnas_fuente import _sentencias as _partir
from sgm.proceso.columnas_fuente import datasets_importados

_RESERVADAS = frozenset({"AS", "CROSS", "FULL", "INNER", "JOIN", "LEFT", "ON", "OUTER", "RIGHT"})

# Las sentencias ya vienen sin comentarios de `_partir`; aquí solo se reconoce el
# `CREATE TABLE ... AS SELECT` y las dos formas de unir el catálogo.
_CREATE = re.compile(r"(?is)\bCREATE\s+TABLE\s+[\w.]+\s+AS\s+(?P<cuerpo>SELECT\b.*)$")
_UNION = re.compile(
    r"(?is)\b(?P<tipo>LEFT|INNER)\s+(?:OUTER\s+)?JOIN\s+(?P<lookup>[\w.]+)"
    r"(?:\s+(?:AS\s+)?(?P<alias>\w+))?\s+ON\b"
)
_COMPARACION = re.compile(
    r"(?i)(?P<ca>[\w$]+)\.(?:'(?P<cb>[^']+)'n|(?P<cc>[\w$]+))\s*=\s*"
    r"(?P<la>[\w$]+)\.(?:'(?P<lb>[^']+)'n|(?P<lc>[\w$]+))"
)
_FILTRO = re.compile(
    r"(?i)(?P<alias>[\w$]+)\.(?:'(?P<col>[^']+)'n|(?P<col2>[\w$]+))\s+IS\s+(?:MISSING|NULL)"
)
_WHERE = re.compile(r"(?i)\bWHERE\b")
_FIN_CUERPO = re.compile(r"(?i)\b(?:GROUP\s+BY|ORDER\s+BY|HAVING|UNION)\s")


@dataclass(frozen=True)
class Validacion:
    """Pareja de consultas que separa los valores del catálogo de los que no están en él."""

    columna: str
    columna_lookup: str
    fuente_lookup: str
    linea: int
    linea_valida: int | None = None

    @property
    def dataset(self) -> str:
        """Nombre del dataset del catálogo sin la biblioteca (`WORK.X` → `X`)."""
        return self.fuente_lookup.rsplit(".", 1)[-1]


@dataclass(frozen=True)
class _Union:
    """Una consulta que une la sabana con el catálogo, ya interpretada."""

    tipo: str
    linea: int
    lookup: str
    columna: str
    columna_lookup: str
    rechaza: bool


def validaciones(texto: str) -> list[Validacion]:
    """Validaciones del programa, cada una con su línea y la de su pareja `INNER JOIN` si existe."""
    importados = {i.dataset.casefold() for i in datasets_importados(texto)}
    uniones: list[_Union] = []
    for desplazamiento, sentencia in _partir(texto)[1]:
        base = texto.count("\n", 0, desplazamiento) + 1
        uniones.extend(_uniones(sentencia, base))
    uniones = [u for u in uniones if _dataset(u.lookup).casefold() in importados]
    resultado: list[Validacion] = []
    for rechazo in (u for u in uniones if u.rechaza):
        pareja = _pareja(uniones, rechazo)
        resultado.append(
            Validacion(
                columna=rechazo.columna,
                columna_lookup=rechazo.columna_lookup,
                fuente_lookup=rechazo.lookup,
                linea=rechazo.linea,
                linea_valida=pareja.linea if pareja else None,
            )
        )
    return resultado


def ruta_de_dataset(texto: str, dataset: str) -> str | None:
    """Ruta del archivo que un `PROC IMPORT` carga en `dataset`, si el SAS la demuestra."""
    nombre = _dataset(dataset).casefold()
    for importacion in datasets_importados(texto):
        if importacion.dataset.casefold() == nombre:
            return importacion.ruta
    return None


def _dataset(nombre: str) -> str:
    """Nombre del dataset sin la biblioteca."""
    return nombre.rsplit(".", 1)[-1]


def _pareja(uniones: list[_Union], rechazo: _Union) -> _Union | None:
    """Consulta `INNER JOIN` con el mismo catálogo y el mismo `ON` que la de rechazos."""
    for union in uniones:
        if (
            union.tipo == "INNER"
            and union.lookup.casefold() == rechazo.lookup.casefold()
            and union.columna.casefold() == rechazo.columna.casefold()
            and union.columna_lookup.casefold() == rechazo.columna_lookup.casefold()
        ):
            return union
    return None


def _uniones(sentencia: str, base: int) -> list[_Union]:
    """Uniones con el catálogo que hay en una sentencia, con su línea absoluta y su filtro."""
    crear = _CREATE.search(sentencia)
    if crear is None:
        return []
    cuerpo = crear.group("cuerpo")
    inicio_cuerpo = crear.start("cuerpo")
    uniones: list[_Union] = []
    for m in _UNION.finditer(cuerpo):
        lookup = m.group("lookup")
        alias = m.group("alias")
        if alias is not None and alias.upper() in _RESERVADAS:
            alias = None
        desde = m.end()
        where = _WHERE.search(cuerpo, desde)
        hasta = where.start() if where else len(cuerpo)
        fin = _FIN_CUERPO.search(cuerpo, desde)
        if fin and fin.start() < hasta:
            hasta = fin.start()
        comparacion = _comparacion(cuerpo[desde:hasta], lookup, alias)
        if comparacion is None:
            continue
        columna, columna_lookup = comparacion
        uniones.append(
            _Union(
                tipo=m.group("tipo").upper(),
                linea=base + sentencia.count("\n", 0, inicio_cuerpo + m.start()),
                lookup=lookup,
                columna=columna,
                columna_lookup=columna_lookup,
                rechaza=where is not None
                and _filtra(cuerpo[where.end() :], lookup, alias, columna_lookup),
            )
        )
    return uniones


def _comparacion(condicion: str, lookup: str, alias: str | None) -> tuple[str, str] | None:
    """Par `(columna de la sabana, columna del catálogo)` del `ON`, en cualquier orden."""
    calificadores = {_dataset(lookup).casefold()}
    if alias:
        calificadores.add(alias.casefold())
    for m in _COMPARACION.finditer(condicion):
        izquierda = m.group("cb") or m.group("cc")
        derecha = m.group("lb") or m.group("lc")
        if izquierda is None or derecha is None:
            continue
        if m.group("la").casefold() in calificadores:
            return izquierda, derecha
        if m.group("ca").casefold() in calificadores:
            return derecha, izquierda
    return None


def _filtra(cola: str, lookup: str, alias: str | None, columna_lookup: str) -> bool:
    """Cierto si el `WHERE` deja fuera los valores que no están en el catálogo."""
    calificadores = {_dataset(lookup).casefold()}
    if alias:
        calificadores.add(alias.casefold())
    for m in _FILTRO.finditer(cola):
        columna = m.group("col") or m.group("col2")
        if m.group("alias").casefold() in calificadores and (
            columna.casefold() == columna_lookup.casefold()
        ):
            return True
    return False
