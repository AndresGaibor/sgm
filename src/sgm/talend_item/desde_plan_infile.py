"""Construcción del lector delimitado que corresponde a INFILE/INPUT."""

from __future__ import annotations

from sgm.ir.models import Operator
from sgm.talend_item.jobs_diseno import java
from sgm.talend_item.modelo import Columna, Nodo
from sgm.talend_item.plantillas import nodo_desde_plantilla


def nodo_infile_delimitado(
    op: Operator,
    columnas: list[Columna],
    unico: str,
    x: int,
    y: int,
    archivo: str,
    separador: str,
    ruta_java: str | None = None,
) -> Nodo:
    """Emite separador, filas de encabezado y comillas que declara SAS."""
    options = op.params.get("infile_options") or {}
    valores = {
        "FILENAME": java(archivo),
        "FIELDSEPARATOR": java(separador),
        "HEADER": str(int(op.params.get("firstobs", 1)) - 1),
    }
    if options.get("dsd"):
        # La plantilla extraída de Studio ya guarda `"` como enclosure y escape char.
        valores["CSV_OPTION"] = "true"
    return nodo_desde_plantilla(
        "tFileInputDelimited",
        unico,
        x,
        y,
        valores,
        columnas=columnas,
        ruta_java=ruta_java,
    )


__all__ = ["nodo_infile_delimitado"]
