"""Emisión de lecturas Excel para Jobs Talend."""

from __future__ import annotations

from sgm.ir.models import Column, Operator
from sgm.migrar.esquemas import PendienteMigracion
from sgm.talend_item.jobs_diseno import java
from sgm.talend_item.modelo import Columna, Nodo
from sgm.talend_item.plantillas import nodo_desde_plantilla


def nodo_lectura_excel(
    op: Operator,
    esquema: list[Column],
    columnas: list[Columna],
    archivo: str,
    dbms: str,
    header: str,
    unico: str,
    x: int,
    y: int,
    ruta_java: str | None = None,
) -> tuple[Nodo, list[PendienteMigracion]]:
    """Construye el nodo Excel y sus pendientes, conservando la semántica existente."""
    params = op.params
    pendientes: list[PendienteMigracion] = []
    linea = op.evidence[0].line_start if op.evidence else None
    guessingrows = params.get("guessingrows")
    if guessingrows is not None:
        pendientes.append(
            PendienteMigracion(
                "P-GUESSINGROWS",
                f"{archivo}: GUESSINGROWS={guessingrows} se limita a archivos delimitados "
                "según la referencia SAS; no se aplica a este Excel.",
                linea,
            )
        )
    for columna in esquema:
        if columna.type is None:
            pendientes.append(
                PendienteMigracion(
                    "P-TIPO-EXCEL",
                    f"{archivo}: no se demostró el tipo de la columna Excel '{columna.name}'; "
                    "se conserva como texto hasta validar el esquema SAS.",
                    linea,
                )
            )
    celdas: tuple[tuple[str, str], ...] = (("USE_REGEX", "false"),)
    if params.get("sheet") is not None:
        celdas = (("SHEETNAME", java(str(params["sheet"]))), *celdas)
    valores = {
        "FILENAME": java(archivo),
        "VERSION_2007": "true" if dbms == "xlsx" else "false",
        "HEADER": header,
    }
    if dbms == "xlsx":
        valores["PASSWORD"] = '"sgm_ref"'
    nodo = nodo_desde_plantilla(
        "tFileInputExcel",
        unico,
        x,
        y,
        valores,
        {"SHEETLIST": celdas},
        columnas,
        ruta_java,
    )
    return nodo, pendientes
