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
    variables = params.get("variables")
    if variables:
        nombres_entrada = [columna.nombre.casefold() for columna in columnas]
        nombres_put = [str(variable).casefold() for variable in variables]
        if nombres_entrada != nombres_put:
            resultado.pendientes.append(
                PendienteMigracion(
                    "P-FILE-PUT-PROJECTION-SIN-SOPORTE",
                    f"{archivo}: PUT lista {nombres_put}, pero el flujo entrega {nombres_entrada}; "
                    "falta un componente de proyección validado para cambiar el esquema sin "
                    "romper la conexión Talend.",
                    _linea(op),
                )
            )
            return resultado
        if any(
            columna.tipo
            in {"id_Double", "id_Float", "id_Integer", "id_Long", "id_BigDecimal"}
            for columna in columnas
        ):
            resultado.pendientes.append(
                PendienteMigracion(
                    "P-PUT-NUMERIC-FORMAT",
                    f"{archivo}: falta fijar el formato numérico por omisión de PUT en lista "
                    "y comprobar su serialización en Talend.",
                    _linea(op),
                )
            )
            return resultado
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
        if "putnames" in params:
            resultado.pendientes.append(
                PendienteMigracion(
                    "P-PUTNAMES-EXCEL-SIN-SOPORTE",
                    f"{archivo}: PUTNAMES no está documentado para DBMS={dbms.upper()}; "
                    "la referencia de SAS lo limita a exportación delimitada (proc, p. 904 y 910).",
                    _linea(op),
                )
            )
        if "tFileOutputExcel" not in disponibles():
            resultado.pendientes.append(
                PendienteMigracion(
                    "P-COMPONENTE-SIN-PLANTILLA",
                    f"{archivo}: falta la plantilla de tFileOutputExcel, extraída de un Job real",
                    _linea(op),
                )
            )
            return resultado
        resultado.pendientes.append(
            PendienteMigracion(
                "P-EXPORT-EXCEL-CABECERA-SIN-REFERENCIA",
                f"{archivo}: SAS/ACCESS documenta SHEET= (acpcref, sección desde p. 93; detalle "
                "en pp. 97–98), pero no se encontró "
                "una equivalencia documentada para la fila de encabezado del XLSX.",
                _linea(op),
            )
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
    putnames = params.get("putnames", True)
    if not isinstance(putnames, bool):
        resultado.pendientes.append(
            PendienteMigracion(
                "P-PUTNAMES-SIN-LITERAL",
                f"{archivo}: PUTNAMES no es YES/NO literal y no puede resolverse sin ejecutar SAS.",
                _linea(op),
            )
        )
        return resultado
    valores = {
        "FILENAME": java(archivo),
        "FIELDSEPARATOR": java(separa),
        "INCLUDEHEADER": "true" if putnames else "false",
        "APPEND": "false",
    }
    if params.get("dsd"):
        # DSD exige salida CSV: Talend usa comillas dobles y las duplica dentro del campo.
        resultado.pendientes.append(
            PendienteMigracion(
                "P-FILE-DSD-MISSING",
                f"{archivo}: SAS advierte que FILE DSD puede suprimir valores faltantes en PUT; "
                "revisar los registros de ejecución antes de aceptar esta salida.",
                _linea(op),
            )
        )
        valores.update(
            {
                "CSV_OPTION": "true",
                "ESCAPE_CHAR": java('"'),
                "TEXT_ENCLOSURE": java('"'),
            }
        )
    resultado.nodo = nodo_desde_plantilla(
        "tFileOutputDelimited",
        unico,
        x,
        y,
        valores,
        columnas=list(columnas),
        ruta_java=ruta_java,
    )
    return resultado


__all__ = ["nodo_escritura"]
