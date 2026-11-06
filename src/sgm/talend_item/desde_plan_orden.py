"""Nodos de orden y de duplicados del plan: `sort` a `tSortRow`, `dedup` a `tUniqRow`.

Los dos pasan el esquema de su entrada sin cambiarlo: lo único que deciden es el orden y qué filas
quedan. Por eso este módulo no necesita el `tMap` ni sus filas con nombre.

* `sort` sale de un `ORDER BY` de `PROC SQL`. El criterio de Studio lleva tres celdas por columna
  (`COLNAME`, `SORT` con `num`, `alpha` o `date`, y `ORDER` con `asc` o `desc`); la forma sale de
  un Job real guardado por Studio, no de la plantilla vacía.
* `dedup` sale de un `SELECT DISTINCT`. Todas las columnas del `SELECT` son la llave, como en SAS,
  y la comparación distingue mayúsculas, porque SAS también las distingue.

Lo que este módulo no demuestra, lo deja pendiente con su motivo: una columna que el esquema de
entrada no tiene, o una entrada de la que no se conoce ni una columna.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sgm.ir.models import Operator
from sgm.migrar.esquemas import PendienteMigracion
from sgm.talend_item.modelo import Columna, Metadata, Nodo
from sgm.talend_item.plantillas import nodo_desde_plantilla

ORDEN_SIN_COLUMNA = "P-ORDEN-COLUMNA-DESCONOCIDA"
ORDEN_SIN_ESQUEMA = "P-ORDEN-SIN-ESQUEMA"

_NUMERICOS = frozenset(
    {"id_Integer", "id_Long", "id_Short", "id_Byte", "id_Double", "id_Float", "id_BigDecimal"}
)


@dataclass
class ResultadoOrden:
    """El nodo (o `None` si no se pudo armar) y lo que quedó pendiente."""

    nodo: Nodo | None = None
    pendientes: list[PendienteMigracion] = field(default_factory=list)


def _tipo_de_orden(columna: Columna) -> str:
    """Cómo compara `tSortRow` esta columna: `num`, `date` o `alpha`."""
    if columna.tipo in _NUMERICOS:
        return "num"
    if columna.tipo == "id_Date":
        return "date"
    return "alpha"


def _resolver(nombre: str, columnas: list[Columna]) -> Columna | None:
    """Columna de entrada que nombra `nombre`: por nombre sin distinguir mayúsculas, o por posición.

    `ORDER BY 2` es la segunda columna del `SELECT` (`sqlproc`), y el esquema de entrada de un
    `sort` es justamente la lista del `SELECT`, en su orden.
    """
    texto = str(nombre).strip()
    if texto.isdigit():
        posicion = int(texto)
        return columnas[posicion - 1] if 1 <= posicion <= len(columnas) else None
    for columna in columnas:
        if columna.nombre.lower() == texto.lower():
            return columna
    return None


def _sin_entrada(op: Operator, linea: int | None, columnas: list[Columna]) -> ResultadoOrden | None:
    if columnas:
        return None
    motivo = f"el operador '{op.kind}' no tiene columnas de entrada demostradas: no se escribe"
    return ResultadoOrden(pendientes=[PendienteMigracion(ORDEN_SIN_ESQUEMA, motivo, linea)])


def nodo_orden(
    op: Operator,
    columnas: list[Columna],
    unico: str,
    x: int,
    linea: int | None,
    ruta_java: str | None = None,
) -> ResultadoOrden:
    """`tSortRow` con un criterio por columna del `ORDER BY`, en el mismo orden."""
    vacio = _sin_entrada(op, linea, columnas)
    if vacio is not None:
        return vacio
    nombres = list(op.params.get("by") or [])
    descendentes = list(op.params.get("descending") or [])
    celdas: list[tuple[str, str]] = []
    pendientes: list[PendienteMigracion] = []
    for posicion, nombre in enumerate(nombres):
        columna = _resolver(nombre, columnas)
        if columna is None:
            motivo = f"ORDER BY {nombre}: la entrada no tiene esa columna ni esa posición"
            pendientes.append(PendienteMigracion(ORDEN_SIN_COLUMNA, motivo, linea))
            continue
        descendente = posicion < len(descendentes) and bool(descendentes[posicion])
        celdas += [
            ("COLNAME", columna.nombre),
            ("SORT", _tipo_de_orden(columna)),
            ("ORDER", "desc" if descendente else "asc"),
        ]
    if pendientes or not celdas:
        # Un orden a medias da un resultado distinto sin avisar: o todo el criterio, o nada.
        return ResultadoOrden(pendientes=pendientes)
    nodo = nodo_desde_plantilla(
        "tSortRow",
        unico,
        x,
        0,
        tablas={"CRITERIA": tuple(celdas)},
        columnas=list(columnas),
        ruta_java=ruta_java,
    )
    return ResultadoOrden(nodo=nodo)


def nodo_unicos(
    op: Operator,
    columnas: list[Columna],
    unico: str,
    entrada: str,
    x: int,
    linea: int | None,
    ruta_java: str | None = None,
) -> ResultadoOrden:
    """`tUniqRow` con llave en las columnas del `DISTINCT`; `entrada` es el nodo que lo alimenta."""
    vacio = _sin_entrada(op, linea, columnas)
    if vacio is not None:
        return vacio
    llaves: set[str] = set()
    pendientes: list[PendienteMigracion] = []
    for nombre in op.params.get("by") or []:
        columna = _resolver(nombre, columnas)
        if columna is None:
            motivo = f"DISTINCT {nombre}: la entrada no tiene esa columna"
            pendientes.append(PendienteMigracion(ORDEN_SIN_COLUMNA, motivo, linea))
        else:
            llaves.add(columna.nombre)
    if pendientes or not llaves:
        return ResultadoOrden(pendientes=pendientes)
    celdas: list[tuple[str, str]] = []
    for columna in columnas:
        es_llave = columna.nombre in llaves
        celdas += [
            ("SCHEMA_COLUMN", columna.nombre),
            ("KEY_ATTRIBUTE", "true" if es_llave else "false"),
            ("CASE_SENSITIVE", "true" if es_llave else "false"),
        ]
    nodo = nodo_desde_plantilla(
        "tUniqRow",
        unico,
        x,
        0,
        tablas={"UNIQUE_KEY": tuple(celdas)},
        columnas=list(columnas),
        ruta_java=ruta_java,
    )
    # Hallazgo de Studio (hito 92): con el bloque FLOW propio vacío, `tUniqRow` saca filas en
    # blanco por UNIQUE y DUPLICATE. El segundo FLOW lleva el nombre del nodo que lo alimenta.
    nodo.metadatas = [
        Metadata("FLOW", unico, tuple(columnas)),
        Metadata("FLOW", entrada, tuple(columnas)),
        Metadata("UNIQUE", "UNIQUE", tuple(columnas)),
        Metadata("DUPLICATE", "DUPLICATE", tuple(columnas)),
    ]
    return ResultadoOrden(nodo=nodo)


__all__ = ["ResultadoOrden", "nodo_orden", "nodo_unicos"]
