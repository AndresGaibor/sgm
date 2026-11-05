"""R1-12: la rama de duplicados por llave (`PROC SORT NODUPKEY`) como Job de Talend.

Cadena de componentes, con la regla leída de `proceso.reglas_duplicados`::

    <entrada> --row1--> tMap_dup --dup_fila--> tUniqRow_dup --UNIQUE--> CSV de únicos
                                                            --DUPLICATE--> CSV de repetidos

* `tMap_dup` recorta los blancos finales de cada llave (en SAS no cuentan al comparar). Las demás
  columnas pasan tal cual.
* `tUniqRow_dup` compara las llaves sensibles a mayúsculas (`CASE_SENSITIVE`, como el `BY` de SAS).
  Saca la primera fila que llega por cada llave por `UNIQUE` y las siguientes por `DUPLICATE`.
  Sin `tSortRow`: el orden de salida no es parte de la regla. Que `tUniqRow` conserve la primera
  fila que llega se comprueba ejecutando (`tools/prueba_duplicados.py`).
* Los dos CSV llevan cabecera y `context.sufijo`, igual que las demás ramas.

`componentes` cuelga la rama de una entrada existente (en `job_producto`, `tReplicate_1`).
`job_duplicados` la monta en un Job propio con su lectura de CSV, para probarla con datos.
"""

from __future__ import annotations

from sgm.proceso.reglas_duplicados import ReglaDuplicados
from sgm.talend_item.filtros_ubicacion import recortado
from sgm.talend_item.jobs_diseno import java
from sgm.talend_item.modelo import Columna, Conexion, Job, Metadata, Nodo, ParametroContexto
from sgm.talend_item.plantillas import nodo_desde_plantilla
from sgm.talend_item.tmap import EntradaMap, SalidaMap, tmap

ENTRADA = "dup_fuente"  # nombre de la conexión de entrada al tMap
TMAP = "tMap_dup"
UNICOS = "tUniqRow_dup"
FILA = "dup_fila"  # salida del tMap hacia tUniqRow
SALIDA_UNICA = "dup_unica"  # conexión UNIQUE hacia el CSV de únicos
SALIDA_REPETIDA = "dup_repetida"  # conexión DUPLICATE hacia el CSV de repetidos
CSV_UNICO = "tFileOutputDelimited_dup_unicos"
CSV_REPETIDO = "tFileOutputDelimited_dup_repetidos"
SUFIJO_REPETIDOS = "_DUPLICADOS_"


def _validar(regla: ReglaDuplicados, columnas: list[Columna]) -> None:
    """No se emite la rama si falta algo que el SAS demuestra."""
    if not regla.equals:
        raise ValueError("Sin EQUALS el SAS no fija qué fila se conserva: no se emite la rama")
    nombres = {c.nombre for c in columnas}
    fuera = sorted(set(regla.llaves) - nombres)
    if fuera:
        raise ValueError(f"Las llaves {fuera} no están en el esquema de la entrada")


def _llave_recortada(columna: str) -> str:
    """Expresión de la llave ya recortada, para el `tMap` de entrada a `tUniqRow`."""
    return recortado(f"{ENTRADA}.{columna}")


def _tmap(regla: ReglaDuplicados, columnas: list[Columna], ruta_java: str | None) -> Nodo:
    llaves = set(regla.llaves)
    expresiones = {
        c.nombre: _llave_recortada(c.nombre) if c.nombre in llaves else f"{ENTRADA}.{c.nombre}"
        for c in columnas
    }
    return tmap(
        TMAP,
        [EntradaMap(ENTRADA, columnas)],
        [SalidaMap(FILA, columnas, expresiones)],
        240,
        120,
        ruta_java,
    )


def _tunique(regla: ReglaDuplicados, columnas: list[Columna], ruta_java: str | None) -> Nodo:
    """`tUniqRow` con las llaves de la regla sensibles a mayúsculas, y sus tres bloques."""
    llaves = set(regla.llaves)
    tabla: list[tuple[str, str]] = []
    for c in columnas:
        clave = "true" if c.nombre in llaves else "false"
        tabla += [
            ("SCHEMA_COLUMN", c.nombre),
            ("KEY_ATTRIBUTE", clave),
            ("CASE_SENSITIVE", "true" if c.nombre in llaves else "false"),
        ]
    nodo = nodo_desde_plantilla(
        "tUniqRow",
        UNICOS,
        480,
        120,
        tablas={"UNIQUE_KEY": tuple(tabla)},
        columnas=list(columnas),
        ruta_java=ruta_java,
    )
    # Hallazgo de Studio (hito 92): con el bloque FLOW propio vacío, `tUniqRow` saca filas en
    # blanco por UNIQUE y DUPLICATE. Con el esquema también en el bloque propio, saca los valores.
    # El bloque FLOW lleva el nombre del nodo que lo alimenta (el tMap), como en el Job de Studio.
    nodo.metadatas = [
        Metadata("FLOW", UNICOS, tuple(columnas)),
        Metadata("FLOW", TMAP, tuple(columnas)),
        Metadata("UNIQUE", "UNIQUE", tuple(columnas)),
        Metadata("DUPLICATE", "DUPLICATE", tuple(columnas)),
    ]
    return nodo


def _csv(
    unico: str, nombre: str, columnas: list[Columna], y: int, ruta_java: str | None
) -> Nodo:
    """CSV con cabecera; el nombre es `<tabla>_<sufijo>.csv` en la carpeta de resultados."""
    return nodo_desde_plantilla(
        "tFileOutputDelimited",
        unico,
        720,
        y,
        {
            "FILENAME": (
                f"context.ruta_resultados + {java(nombre)} + context.sufijo + {java('.csv')}"
            ),
            "FIELDSEPARATOR": '","',
            "INCLUDEHEADER": "true",
            "APPEND": "false",
        },
        columnas=list(columnas),
        ruta_java=ruta_java,
    )


def componentes(
    regla: ReglaDuplicados,
    columnas: list[Columna],
    entrada: str,
    ruta_java: str | None = None,
) -> tuple[list[Nodo], list[Conexion]]:
    """Nodos y conexiones de la rama, colgada de la conexión `entrada` (un nodo del Job)."""
    _validar(regla, columnas)
    tmap_nodo = _tmap(regla, columnas, ruta_java)
    unico = _tunique(regla, columnas, ruta_java)
    csv_unico = _csv(CSV_UNICO, regla.salida + "_", columnas, 120, ruta_java)
    csv_repetido = _csv(
        CSV_REPETIDO, regla.salida + SUFIJO_REPETIDOS, columnas, 240, ruta_java
    )
    nodos = [tmap_nodo, unico, csv_unico, csv_repetido]
    conexiones = [
        Conexion(entrada, TMAP, ENTRADA),
        Conexion(TMAP, UNICOS, FILA),
        Conexion(UNICOS, CSV_UNICO, SALIDA_UNICA, conector="UNIQUE"),
        Conexion(UNICOS, CSV_REPETIDO, SALIDA_REPETIDA, conector="DUPLICATE"),
    ]
    return nodos, conexiones


def job_duplicados(
    regla: ReglaDuplicados,
    columnas: list[Columna],
    delimitador: str = ",",
    ruta_java: str | None = None,
) -> Job:
    """Job propio: lee el CSV de `context.ruta_origen` (con cabecera) y aplica la rama."""
    lectura = nodo_desde_plantilla(
        "tFileInputDelimited",
        "tFileInputDelimited_1",
        0,
        120,
        {
            "FILENAME": "context.ruta_origen",
            "FIELDSEPARATOR": java(delimitador),
            "HEADER": "1",
        },
        columnas=list(columnas),
        ruta_java=ruta_java,
    )
    nodos, conexiones = componentes(regla, columnas, "tFileInputDelimited_1", ruta_java)
    contextos = {
        "Default": [
            ParametroContexto("ruta_origen"),
            ParametroContexto("ruta_resultados"),
            ParametroContexto("sufijo"),
        ]
    }
    return Job(
        f"dup_{regla.salida.lower()}",
        nodos=[lectura, *nodos],
        conexiones=conexiones,
        contextos=contextos,
    )


__all__ = ["ENTRADA", "TMAP", "UNICOS", "componentes", "job_duplicados"]
