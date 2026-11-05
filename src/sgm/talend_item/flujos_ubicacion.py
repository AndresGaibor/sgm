"""R1-05: la rama de ubicación del `job_producto` emitido.

Cuelga una rama de `tReplicate_1`, paralela a las de R1-04, R1-06 y R1-07::

    tReplicate_1 --ubic_fuente--> tMap_ubicacion --ubic_rechazo/ubic_valida--> 2 CSV
    tFileInputExcel_ubic_pais --ubic_pais (LEFT)--^
    tFileInputExcel_ubic_dane --ubic_dane (LEFT)--^

Los dos lookups son Excel de homologación (`Cod_pais.xlsx` y `CODIGOS_DANE.xlsx`), sin `INNER JOIN`
porque el SAS une con `LEFT JOIN`: una fila sin pareja sigue, con el lookup en nulo. El nombre del
archivo de cada Excel es un contexto (`arch_hom_pais`, `arch_hom_dane`) con el valor del SAS.

La sábana de entrada debe traer `PAIS`, `CODIGO_UBICACION` y `DIRECCION`: el SAS las lee de la
tabla `UBICACION` unida por `LLAVE_NOMBRE`, y esa unión no está en el Job (ver `reglas_ubicacion`).
"""

from __future__ import annotations

from sgm.proceso.reglas_ubicacion import INCONSISTENCIA, ReglaUbicacion
from sgm.talend_item.conexiones import lookup
from sgm.talend_item.filtros_ubicacion import (
    ENTRADA,
    LOOKUP_DANE,
    LOOKUP_PAIS,
    SALIDAS,
    clave_dane,
    clave_pais,
    salidas,
)
from sgm.talend_item.jobs_diseno import java
from sgm.talend_item.modelo import Columna, Conexion, Nodo
from sgm.talend_item.plantillas import nodo_desde_plantilla
from sgm.talend_item.tmap import EntradaMap, tmap

TMAP = "tMap_ubicacion"
EXCEL = {"pais": "tFileInputExcel_ubic_pais", "dane": "tFileInputExcel_ubic_dane"}
VARIABLE = {"pais": "arch_hom_pais", "dane": "arch_hom_dane"}
SALIDA = "tFileOutputDelimited_ubic_{n}"
ARCHIVO = {"rechazo": "INCONS_UBICACION", "valida": "UBIC_VALIDA"}
ORDEN = ("rechazo", "valida")
REQUERIDAS = (
    "PAIS", "CODIGO_UBICACION", "DIRECCION", "LLAVE_NOMBRE", "RELACION", "TIPO_DOC", "NRO_DOC",
)  # fmt: skip


def _validar(regla: ReglaUbicacion, cols: list[Columna]) -> None:
    """No se emite la rama si la sábana no trae las columnas que la regla lee o proyecta."""
    nombres = {c.nombre for c in cols}
    necesarias = set(REQUERIDAS) | set(regla.proyeccion_rechazo) | set(regla.proyeccion_valida)
    faltan = sorted(necesarias - {INCONSISTENCIA} - nombres)
    if faltan:
        raise ValueError(f"La ubicación necesita las columnas {faltan} en la sábana del producto")


def _excel(unico: str, clave: str, columna: str, x: int, ruta_java: str | None) -> Nodo:
    """`tFileInputExcel` de un lookup: el archivo lo elige el padre por su contexto."""
    return nodo_desde_plantilla(
        "tFileInputExcel",
        unico,
        x,
        1440,
        {
            "FILENAME": f"context.ruta_insumos + context.{VARIABLE[clave]}",
            # Vacío o "***" hacen que Studio no compile; el archivo no tiene clave.
            "PASSWORD": '"sgm_ref"',
        },
        {"SHEETLIST": (("SHEETNAME", "context.hoja_excel"), ("USE_REGEX", "false"))},
        [Columna(columna)],
        ruta_java,
    )


def componentes(
    regla: ReglaUbicacion,
    cols: list[Columna],
    ruta_java: str | None = None,
) -> tuple[list[Nodo], list[Conexion]]:
    """El `tMap` de ubicación, sus dos lookups, sus dos CSV y sus conexiones."""
    _validar(regla, cols)
    flujos = salidas(regla, ENTRADA)
    nodos: list[Nodo] = [
        _excel(EXCEL["pais"], "pais", regla.columna_pais, 0, ruta_java),
        _excel(EXCEL["dane"], "dane", regla.columna_dane, 240, ruta_java),
        tmap(
            TMAP,
            [
                EntradaMap(ENTRADA, cols),
                EntradaMap(
                    LOOKUP_PAIS,
                    [Columna(regla.columna_pais)],
                    expresiones_union={regla.columna_pais: clave_pais(ENTRADA)},
                ),
                EntradaMap(
                    LOOKUP_DANE,
                    [Columna(regla.columna_dane)],
                    expresiones_union={regla.columna_dane: clave_dane(ENTRADA)},
                ),
            ],
            flujos,
            480,
            1440,
            ruta_java,
        ),
    ]
    conexiones: list[Conexion] = [
        lookup(EXCEL["pais"], TMAP, LOOKUP_PAIS),
        lookup(EXCEL["dane"], TMAP, LOOKUP_DANE),
        Conexion("tReplicate_1", TMAP, ENTRADA),
    ]
    for n, (modo, salida) in enumerate(zip(ORDEN, flujos, strict=True), start=1):
        unico = SALIDA.format(n=n)
        nombre = (
            f"context.ruta_resultados + {java(ARCHIVO[modo] + '_')} "
            f"+ context.sufijo + {java('.csv')}"
        )
        nodos.append(
            nodo_desde_plantilla(
                "tFileOutputDelimited",
                unico,
                720,
                1440 + (n - 1) * 120,
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
        conexiones.append(Conexion(TMAP, unico, SALIDAS[modo]))
    return nodos, conexiones


__all__ = ["EXCEL", "SALIDA", "TMAP", "VARIABLE", "componentes"]
