"""Los tres flujos de R1-04 dentro del `job_producto` **emitido** (hito 87).

El hito 86 probó los `expressionFilter` en un Job mínimo. Aquí la misma terna se cuelga del
`tReplicate_1` del Job real, como una rama más, y cada flujo escribe el CSV de la tabla que el SAS
nombra en su `CREATE TABLE`::

    tReplicate_1 --flujos--> tMap_flujos --tit_cot/fa/valido--> 3 tFileOutputDelimited

La terna, su proyección y el nombre de cada tabla salen de `proceso.reglas_fila.flujos_producto`,
que los lee del `SELECT`/`WHERE` del SAS. No se declaran columnas ni nombres de archivo aquí. El
filtro lo traduce `filtros_fila.py`, ya verificado fila por fila contra `v02` en Studio.

Los filtros comparan `NRO_DOC` como **texto normalizado** (`""`, `"0"` o dígitos). Por eso este
módulo exige que la columna del filtro esté entre las `numericas` que R1-02 convierte: sin esa
normalización el `IS MISSING` de SAS no se puede traducir y no se emite un filtro equivocado.
"""

from __future__ import annotations

from sgm.proceso.reglas_fila import MODOS, ReglaFila
from sgm.talend_item.filtros_fila import salidas_filtro
from sgm.talend_item.jobs_diseno import java
from sgm.talend_item.modelo import Columna, Conexion, Nodo
from sgm.talend_item.plantillas import nodo_desde_plantilla
from sgm.talend_item.tmap import EntradaMap, tmap

ENTRADA = "flujos"
TMAP = "tMap_flujos"
SALIDA = "tFileOutputDelimited_flujos_{n}"


def _validar(flujos: list[ReglaFila], cols: list[Columna], informats: dict[str, tuple[int, int]]):
    """No se emite un flujo si falta algo que el SAS o la normalización no demuestran."""
    if not flujos:
        raise ValueError("Sin reglas de fila no hay flujos R1-04 que emitir")
    if sorted(f.modo for f in flujos) != sorted(MODOS):
        raise ValueError(f"Los flujos R1-04 deben ser exactamente {MODOS}: {flujos}")
    nombres = {c.nombre for c in cols}
    for flujo in flujos:
        if not flujo.tabla or not flujo.columnas:
            raise ValueError(f"El flujo '{flujo.modo}' no trae tabla ni proyección del SAS")
        if flujo.columna not in informats:
            raise ValueError(
                f"El filtro de '{flujo.columna}' exige la normalización de R1-02; "
                f"no está en numericas: {sorted(informats)}"
            )
        fuera = sorted(set(flujo.columnas) - nombres)
        if fuera:
            raise ValueError(f"El flujo '{flujo.modo}' proyecta columnas que no se leen: {fuera}")


def componentes(
    flujos: list[ReglaFila],
    cols: list[Columna],
    informats: dict[str, tuple[int, int]],
    ruta_java: str | None = None,
) -> tuple[list[Nodo], list[Conexion]]:
    """El `tMap` de los tres flujos, sus tres salidas CSV y sus conexiones.

    La conexión de entrada sale de `tReplicate_1`; el llamador la añade a las ramas existentes.
    Cada CSV lleva cabecera (para poder compararlo por nombre de columna) y el sufijo de producto
    de `context.sufijo`, igual que `doc_incorrectos_`.
    """
    _validar(flujos, cols, informats)
    esquemas = {f.modo: [Columna(c) for c in f.columnas] for f in flujos}
    salidas = salidas_filtro(flujos, esquemas, fila=ENTRADA)
    nodos: list[Nodo] = [tmap(TMAP, [EntradaMap(ENTRADA, cols)], salidas, 240, 600, ruta_java)]
    conexiones: list[Conexion] = [Conexion("tReplicate_1", TMAP, ENTRADA)]
    for n, (flujo, salida) in enumerate(zip(flujos, salidas, strict=True), start=1):
        unico = SALIDA.format(n=n)
        nombre = (
            f"context.ruta_resultados + {java(flujo.tabla + '_')} "
            f"+ context.sufijo + {java('.csv')}"
        )
        nodos.append(
            nodo_desde_plantilla(
                "tFileOutputDelimited",
                unico,
                720,
                480 + (n - 1) * 120,
                {
                    "FILENAME": nombre,
                    "FIELDSEPARATOR": '","',
                    "INCLUDEHEADER": "true",
                    "APPEND": "false",
                },
                columnas=list(salida.columnas),
                ruta_java=ruta_java,
            )
        )
        conexiones.append(Conexion(TMAP, unico, salida.nombre))
    return nodos, conexiones


__all__ = ["ENTRADA", "SALIDA", "TMAP", "componentes"]
