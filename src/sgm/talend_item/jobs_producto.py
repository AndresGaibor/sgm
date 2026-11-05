"""`job_producto` del diseño (sección 3.3): lee el archivo de datos del producto.

Por ahora implementa la lectura del archivo de origen con el esquema que el SAS demuestra y los
totales de origen (conteo de registros y suma de la columna de saldo), la base de la conciliación.
Las validaciones, las correcciones y las salidas siguen pendientes y el Job las lista. Todas las
columnas se leen como texto: el SAS las convierte después con `input()`; aquí solo se convierte la
del saldo, dentro del `tMap` que alimenta la suma.
"""

from __future__ import annotations

from sgm.talend_item.arquitectura import Arquitectura
from sgm.talend_item.componentes import log_row
from sgm.talend_item.conexiones import al_terminar_subjob
from sgm.talend_item.jobs_diseno import java
from sgm.talend_item.modelo import Columna, Conexion, Job, ParametroContexto
from sgm.talend_item.plantillas import nodo_desde_plantilla
from sgm.talend_item.tmap import EntradaMap, SalidaMap, tmap


def _a_decimal(columna: str) -> str:
    """Expresión de Java equivalente a `input(left(col), 20.)`: vacío es nulo, el resto decimal."""
    valor = f"row1.{columna}"
    vacio = f"{valor} == null || {valor}.trim().isEmpty()"
    return f"{vacio} ? null : new java.math.BigDecimal({valor}.trim())"


def job_producto(
    arq: Arquitectura,
    columnas: tuple[str, ...],
    variables_periodo: tuple[str, ...] = (),
    pendiente: str = "",
    delimitador: str = ";",
    ruta_java: str | None = None,
) -> Job:
    """Lee `context.ruta_origen`, cuenta los registros, suma el saldo y los imprime."""
    cols = [Columna(c) for c in columnas]
    parametros = ("producto", "ruta_origen", "sufijo", *variables_periodo)
    mensaje = f"{arq.producto}: lee el archivo de origen del producto. Pendiente: {pendiente}"
    lineas = [f"System.out.println({java(mensaje)});"]
    lineas += [f'System.out.println("  {p} = " + context.{p});' for p in parametros]
    con_saldo = arq.columna_saldo in columnas
    llave = cols[0]
    suma = [Columna("saldo", "id_BigDecimal")]
    salida_map = [llave, *suma] if con_saldo else [llave]
    totales = [Columna("registros_origen", "id_Long")]
    operaciones = [
        ("OUTPUT_COLUMN", "registros_origen"),
        ("FUNCTION", "count"),
        ("INPUT_COLUMN", llave.nombre),
        ("IGNORE_NULL", "false"),
    ]
    if con_saldo:
        totales.append(Columna("suma_saldo_origen", "id_BigDecimal"))
        operaciones += [
            ("OUTPUT_COLUMN", "suma_saldo_origen"),
            ("FUNCTION", "sum"),
            ("INPUT_COLUMN", "saldo"),
            ("IGNORE_NULL", "true"),
        ]
    expresiones = {llave.nombre: f"row1.{llave.nombre}"}
    if con_saldo:
        expresiones["saldo"] = _a_decimal(arq.columna_saldo)
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
        tmap(
            "tMap_1",
            [EntradaMap("row1", cols)],
            [SalidaMap("out1", salida_map, expresiones)],
            240,
            120,
            ruta_java,
        ),
        nodo_desde_plantilla(
            "tAggregateRow",
            "tAggregateRow_1",
            480,
            120,
            tablas={"OPERATIONS": tuple(operaciones)},
            columnas=totales,
            ruta_java=ruta_java,
        ),
        log_row("tLogRow_1", totales, 720, 120, ruta_java or ""),
    ]
    conexiones = [
        al_terminar_subjob("tJava_1", "tFileInputDelimited_1"),
        Conexion("tFileInputDelimited_1", "tMap_1", "row1"),
        Conexion("tMap_1", "tAggregateRow_1", "out1"),
        Conexion("tAggregateRow_1", "tLogRow_1", "row2"),
    ]
    contextos = {"Default": [ParametroContexto(p) for p in parametros]}
    return Job(arq.producto, nodos=nodos, conexiones=conexiones, contextos=contextos)
