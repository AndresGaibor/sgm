"""`job_producto` del diseño (sección 3.3): lee el archivo de datos del producto.

Por ahora implementa la lectura del archivo de origen con el esquema que el SAS demuestra y el
conteo de registros de origen (la base de los totales de conciliación). Las validaciones, las
correcciones y las salidas siguen pendientes y el Job las lista con lo que el modelo de proceso
midió. Todas las columnas se leen como texto: el SAS las convierte después con `input()` y esa
conversión es una etapa de normalización que aún no se traduce.
"""

from __future__ import annotations

from sgm.talend_item.arquitectura import Arquitectura
from sgm.talend_item.componentes import log_row
from sgm.talend_item.conexiones import al_terminar_subjob
from sgm.talend_item.jobs_diseno import java
from sgm.talend_item.modelo import Columna, Conexion, Job, ParametroContexto
from sgm.talend_item.plantillas import nodo_desde_plantilla


def job_producto(
    arq: Arquitectura,
    columnas: tuple[str, ...],
    variables_periodo: tuple[str, ...] = (),
    pendiente: str = "",
    delimitador: str = ";",
    ruta_java: str | None = None,
) -> Job:
    """Lee `context.ruta_origen`, cuenta los registros y los imprime con el producto."""
    cols = [Columna(c) for c in columnas]
    parametros = ("producto", "ruta_origen", "sufijo", *variables_periodo)
    mensaje = f"{arq.producto}: lee el archivo de origen del producto. Pendiente: {pendiente}"
    lineas = [f"System.out.println({java(mensaje)});"]
    lineas += [f'System.out.println("  {p} = " + context.{p});' for p in parametros]
    conteo = [Columna("registros_origen", "id_Long")]
    nodos = [
        nodo_desde_plantilla(
            "tJava", "tJava_1", 0, 0, {"CODE": "\n".join(lineas)}, ruta_java=ruta_java
        ),
        nodo_desde_plantilla(
            "tFileInputDelimited",
            "tFileInputDelimited_1",
            0,
            120,
            {
                "FILENAME": "context.ruta_origen",
                "FIELDSEPARATOR": java(delimitador),
                "HEADER": "0",
            },
            columnas=cols,
            ruta_java=ruta_java,
        ),
        nodo_desde_plantilla(
            "tAggregateRow",
            "tAggregateRow_1",
            240,
            120,
            tablas={
                "OPERATIONS": (
                    ("OUTPUT_COLUMN", "registros_origen"),
                    ("FUNCTION", "count"),
                    ("INPUT_COLUMN", cols[0].nombre),
                    ("IGNORE_NULL", "false"),
                )
            },
            columnas=conteo,
            ruta_java=ruta_java,
        ),
        log_row("tLogRow_1", conteo, 480, 120, ruta_java or ""),
    ]
    conexiones = [
        al_terminar_subjob("tJava_1", "tFileInputDelimited_1"),
        Conexion("tFileInputDelimited_1", "tAggregateRow_1", "row1"),
        Conexion("tAggregateRow_1", "tLogRow_1", "row2"),
    ]
    contextos = {"Default": [ParametroContexto(p) for p in parametros]}
    return Job(arq.producto, nodos=nodos, conexiones=conexiones, contextos=contextos)
