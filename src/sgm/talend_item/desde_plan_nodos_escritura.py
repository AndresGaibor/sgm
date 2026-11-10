"""Escritura de salidas de archivo desde operadores lógicos."""

from __future__ import annotations

from sgm.ir.models import Operator
from sgm.java_identificadores import is_java_identifier
from sgm.talend_item.modelo import Columna
from sgm.talend_item.plantillas import disponibles, nodo_desde_plantilla


def nodo_escritura(
    op: Operator,
    columnas: list[Columna],
    unico: str,
    x: int,
    y: int,
    ruta_java: str | None = None,
):
    """`write_file` como `tFileOutputDelimited` o `tFileOutputExcel` si hay plantilla."""
    from sgm.migrar.esquemas import PendienteMigracion
    from sgm.talend_item.desde_plan_nodos import (
        DELIMITADOS,
        EXCEL,
        Resultado,
        _linea,
        ruta,
        separador,
    )
    from sgm.talend_item.jobs_diseno import java

    params = op.params
    dbms = (params.get("dbms") or "").lower()
    resultado = Resultado(columnas=list(columnas))
    archivo = ruta(params.get("outfile"))
    if any(not is_java_identifier(columna.nombre) for columna in columnas):
        resultado.pendientes.append(
            PendienteMigracion(
                "P-ESQUEMA-NO-PORTABLE",
                "la escritura tiene nombres de columna no portables para Java",
                _linea(op),
            )
        )
        return resultado
    if dbms in EXCEL:
        if "tFileOutputExcel" not in disponibles():
            resultado.pendientes.append(
                PendienteMigracion(
                    "P-COMPONENTE-SIN-PLANTILLA",
                    f"{archivo}: falta la plantilla de tFileOutputExcel, extraída de un Job real",
                    _linea(op),
                )
            )
            return resultado
        resultado.nodo = nodo_desde_plantilla(
            "tFileOutputExcel",
            unico,
            x,
            y,
            {"FILENAME": java(archivo)},
            columnas=list(columnas),
            ruta_java=ruta_java,
        )
        return resultado
    separa, motivo = separador(dbms, params.get("delimiter"))
    if dbms not in DELIMITADOS:
        resultado.pendientes.append(
            PendienteMigracion(
                "P-FORMATO-SIN-SOPORTE",
                f"{archivo}: DBMS={dbms or '(sin DBMS)'} no es un archivo delimitado",
                _linea(op),
            )
        )
        return resultado
    if separa is None:
        resultado.pendientes.append(
            PendienteMigracion("P-DELIMITADOR", f"{archivo}: {motivo}", _linea(op))
        )
        separa = ","
    resultado.nodo = nodo_desde_plantilla(
        "tFileOutputDelimited",
        unico,
        x,
        y,
        {
            "FILENAME": java(archivo),
            "FIELDSEPARATOR": java(separa),
            "INCLUDEHEADER": "true",
            "APPEND": "false",
        },
        columnas=list(columnas),
        ruta_java=ruta_java,
    )
    return resultado


__all__ = ["nodo_escritura"]
