"""Lectura de la fecha del proceso en el Job padre.

El SAS importa un Excel con el año, el mes y el día y los usa en los nombres de archivo. Aquí el
padre lee ese Excel una sola vez (`tFileInputExcel` y un `tJavaRow`) y deja los valores en variables
de contexto; los hijos las heredan porque el padre transmite el contexto completo. Las columnas son
las que el SAS usa del archivo; su orden dentro del Excel no está en el SAS y queda pendiente.
"""

from __future__ import annotations

import re
import unicodedata

from sgm.java_identificadores import require_context_identifier
from sgm.proceso.insumos import InsumoResuelto, InsumosResueltos
from sgm.talend_item.arquitectura import Arquitectura
from sgm.talend_item.modelo import Columna, Conexion, Nodo, ParametroContexto
from sgm.talend_item.plantillas import nodo_desde_plantilla

HOJA_POR_DEFECTO = "Sheet1"  # el SAS dice SHEET='' (la primera hoja); Talend pide un nombre
VARIABLE_HOJA = "hoja_excel"


def nombre_columna(texto: str, usadas: set[str]) -> str:
    """Nombre de columna válido en Java: sin acentos, sin espacios y sin repetirse."""
    base = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    base = re.sub(r"\W+", "_", base).strip("_") or "col"
    if base[0].isdigit():
        base = "c_" + base
    nombre, n = base, 2
    while nombre.lower() in usadas:
        nombre, n = f"{base}_{n}", n + 1
    usadas.add(nombre.lower())
    return nombre


def columnas_de(insumo: InsumoResuelto) -> list[tuple[str, Columna]]:
    """(nombre en el Excel, columna de Talend) en el orden en que el SAS las usa."""
    usadas: set[str] = set()
    return [(c, Columna(nombre_columna(c, usadas))) for c in insumo.columnas]


def contextos_de_periodo(
    arq: Arquitectura, resueltos: InsumosResueltos
) -> list[ParametroContexto]:
    """Variables de contexto del periodo (grupo Default): el Excel y dónde va la fecha."""
    if arq.periodo is None or arq.periodo.fuente not in resueltos.insumos:
        return []
    insumo = resueltos.insumos[arq.periodo.fuente]
    _validar_contextos(arq, insumo)
    vacias = [ParametroContexto(v) for _, v in arq.periodo.variables]
    return [
        ParametroContexto(VARIABLE_HOJA, valor=HOJA_POR_DEFECTO),
        ParametroContexto(insumo.variable_ruta, valor=insumo.directorio),
        ParametroContexto(insumo.variable_archivo, valor=insumo.archivo),
        *vacias,
    ]


def nodos_periodo(
    arq: Arquitectura, resueltos: InsumosResueltos, ruta_java: str | None = None
) -> tuple[list[Nodo], list[Conexion]]:
    """`tFileInputExcel` y `tJavaRow` que dejan el periodo en el contexto (vacío sin resolver)."""
    if arq.periodo is None or arq.periodo.fuente not in resueltos.insumos:
        return [], []
    insumo = resueltos.insumos[arq.periodo.fuente]
    _validar_contextos(arq, insumo)
    pares = columnas_de(insumo)
    columnas = [c for _, c in pares]
    por_excel = {excel: c.nombre for excel, c in pares}
    asignaciones = [
        f"context.{variable} = String.valueOf(input_row.{por_excel[columna]});"
        for columna, variable in arq.periodo.variables
        if columna in por_excel
    ]
    excel = nodo_desde_plantilla(
        "tFileInputExcel",
        "tFileInputExcel_1",
        0,
        120,
        {
            "FILENAME": f"context.{insumo.variable_ruta} + context.{insumo.variable_archivo}",
            # Vacío o "***" hacen que Studio genere `Optional.ofNullable()` y no compile
            # (verificado). El archivo no tiene clave: Excel ignora este marcador.
            "PASSWORD": '"sgm_ref"',
        },
        {"SHEETLIST": (("SHEETNAME", f"context.{VARIABLE_HOJA}"), ("USE_REGEX", "false"))},
        columnas,
        ruta_java,
    )
    fila = nodo_desde_plantilla(
        "tJavaRow",
        "tJavaRow_1",
        240,
        120,
        {"CODE": "\n".join(asignaciones)},
        columnas=columnas,
        ruta_java=ruta_java,
    )
    return [excel, fila], [Conexion(excel.unico, fila.unico, "row2")]


def _validar_contextos(arq: Arquitectura, insumo: InsumoResuelto) -> None:
    """Valida nombres que se interpolan como campos de `context` en los nodos del periodo."""
    for nombre in (
        VARIABLE_HOJA,
        insumo.variable_ruta,
        insumo.variable_archivo,
        *(variable for _, variable in (arq.periodo.variables if arq.periodo else ())),
    ):
        require_context_identifier(nombre)
