"""`job_conciliacion` real (R2-03): compara los totales de origen y de salida de cada producto.

Entrada: los mismos archivos que deja `job_producto` y que une `job_totales` (hito 97):
`totales_origen_<p>.csv` y `totales_salida_<p>.csv`, con cabecera y el esquema
`PRODUCTO;TIPO;NRO_FILAS;NRO_SALDOS_NO_VACIOS;SUMA_SALDO`.

Por cada producto, en orden (`OnSubjobOk`), un `tMap` cruza el origen (fila principal) con la
salida (lookup por `PRODUCTO`) y calcula `DIF_FILAS` y `DIF_SALDO`. Las filas se añaden a
`conciliacion_<anio><mes><dia>.csv` con las columnas de `CONCILIACION_FINAL` del SAS
(`PRODUCTO;DIF_FILAS;DIF_SALDO`).

Después, el mismo archivo se vuelve a leer y un `tJavaRow` marca en `globalMap` cada producto que
no concilia. Un `tDie` con `EXIT_JVM` falla el Job con un código numérico y un mensaje con el
producto y la diferencia. El criterio es el del SAS (L8/05): no concilia si `DIF_FILAS` es distinto
de 0 o si `|DIF_SALDO|` supera la tolerancia. La tolerancia es solo de saldo; las filas no tienen.
La tolerancia de negocio vale 0 por omisión y queda pendiente de confirmar.
"""

from __future__ import annotations

from sgm.java_literals import literal_nombre_archivo
from sgm.talend_item.arquitectura import Arquitectura
from sgm.talend_item.conexiones import al_terminar_subjob, lookup, si
from sgm.talend_item.jobs_diseno import java
from sgm.talend_item.jobs_totales import COLUMNAS_TOTALES, variables_fecha
from sgm.talend_item.modelo import Columna, Conexion, Job, Nodo, ParametroContexto
from sgm.talend_item.plantillas import nodo_desde_plantilla
from sgm.talend_item.tmap import EntradaMap, SalidaMap, tmap

COLUMNAS_CONCILIACION = (Columna("PRODUCTO"), Columna("DIF_FILAS"), Columna("DIF_SALDO"))
ARCHIVO_CONCILIACION = "conciliacion"
MENSAJE = "conc_mensaje"  # clave de `globalMap` con el texto de los productos que no concilian
CODIGO_NO_CONCILIA = 3  # código de salida del tDie cuando algún producto no concilia
TOLERANCIA = "tolerancia_conciliacion"
TOLERANCIA_OMISION = "0"  # valor de negocio pendiente: confirmar con negocio
PASO_X = 240
PASO_Y = 120


def _lector(unico: str, x: int, y: int, archivo: str) -> Nodo:
    """Lee un archivo de totales con cabecera. `DIE_ON_ERROR` hace fallar al Job si no lo lee."""
    return nodo_desde_plantilla(
        "tFileInputDelimited",
        unico,
        x,
        y,
        {
            "FILENAME": archivo,
            "FIELDSEPARATOR": java(";"),
            "HEADER": "1",
            "DIE_ON_ERROR": "true",
        },
        columnas=list(COLUMNAS_TOTALES),
    )


def _expresiones() -> dict[str, str]:
    """Diferencias de filas (exacta) y de saldo (BigDecimal) del origen contra la salida."""
    return {
        "PRODUCTO": "row1.PRODUCTO",
        "DIF_FILAS": (
            "String.valueOf(Long.parseLong(row1.NRO_FILAS.trim())"
            " - Long.parseLong(row2.NRO_FILAS.trim()))"
        ),
        "DIF_SALDO": (
            "new java.math.BigDecimal(row1.SUMA_SALDO.trim())"
            ".subtract(new java.math.BigDecimal(row2.SUMA_SALDO.trim())).toPlainString()"
        ),
    }


def _codigo_chequeo() -> str:
    """Código del `tJavaRow` que marca en `globalMap` los productos que no concilian."""
    tolerancia = f"context.{TOLERANCIA}.trim()"
    return "\n".join(
        [
            f"java.math.BigDecimal tol = new java.math.BigDecimal({tolerancia});",
            "long dif = Long.parseLong(input_row.DIF_FILAS.trim());",
            "java.math.BigDecimal sal = new java.math.BigDecimal(input_row.DIF_SALDO.trim());",
            "if (dif != 0 || sal.abs().compareTo(tol) > 0) {",
            '    String previo = (String) globalMap.get("' + MENSAJE + '");',
            '    String nuevo = "NO CONCILIA " + input_row.PRODUCTO.trim()',
            '        + ": diferencia de filas " + dif',
            '        + ", diferencia de saldo " + sal.toPlainString()',
            '        + " (tolerancia " + tol.toPlainString() + ")";',
            '    globalMap.put("' + MENSAJE + '", previo == null ? nuevo : previo + "; " + nuevo);',
            "}",
        ]
    )


def job_conciliacion(
    arq: Arquitectura,
    productos: tuple[str, ...],
    ruta_java: str | None = None,
    nombre: str | None = None,
) -> Job:
    """Job de conciliación: un subjob por producto, luego el chequeo y el `tDie` si no concilia.

    `nombre` permite emitir el mismo Job con otro nombre (las pruebas de Studio lo usan).
    """
    if not productos:
        raise ValueError("job_conciliacion necesita al menos un producto")
    if not arq.archivo_totales:
        raise ValueError("job_conciliacion necesita archivo_totales en la decisión del programa")
    variables = variables_fecha(arq)
    fecha = f"context.{variables['anio']} + context.{variables['mes']} + context.{variables['dia']}"
    destino = (
        f"context.ruta_resultados + "
        f"{literal_nombre_archivo(ARCHIVO_CONCILIACION + '_')} + {fecha} + "
        f"{literal_nombre_archivo('.csv')}"
    )
    salida_cols = list(COLUMNAS_CONCILIACION)
    nodos: list[Nodo] = [
        nodo_desde_plantilla(
            "tJava",
            "tJava_1",
            0,
            0,
            {"CODE": f"System.out.println({java('job_conciliacion: ' + ', '.join(productos))});"},
            ruta_java=ruta_java,
        )
    ]
    conexiones: list[Conexion] = []
    anterior = "tJava_1"
    for indice, producto in enumerate(productos, start=1):
        x = PASO_X * indice
        origen = _lector(
            f"tFileInputDelimited_o{indice}",
            x,
            0,
            f"context.ruta_resultados + "
            f"{literal_nombre_archivo(f'totales_origen_{producto}.csv')}",
        )
        salida = _lector(
            f"tFileInputDelimited_s{indice}",
            x,
            PASO_Y,
            f"context.ruta_resultados + "
            f"{literal_nombre_archivo(f'totales_salida_{producto}.csv')}",
        )
        cruce = tmap(
            f"tMap_{indice}",
            [
                EntradaMap("row1", list(COLUMNAS_TOTALES)),
                EntradaMap(
                    "row2",
                    list(COLUMNAS_TOTALES),
                    expresiones_union={"PRODUCTO": "row1.PRODUCTO"},
                ),
            ],
            [SalidaMap("out1", salida_cols, _expresiones())],
            x,
            2 * PASO_Y,
            ruta_java,
        )
        escritura = nodo_desde_plantilla(
            "tFileOutputDelimited",
            f"tFileOutputDelimited_{indice}",
            x,
            3 * PASO_Y,
            {
                "FILENAME": destino,
                "FIELDSEPARATOR": java(";"),
                "INCLUDEHEADER": str(indice == 1).lower(),
                "APPEND": str(indice != 1).lower(),
            },
            columnas=salida_cols,
            ruta_java=ruta_java,
        )
        nodos += [origen, salida, cruce, escritura]
        conexiones += [
            Conexion(origen.unico, cruce.unico, "row1"),
            lookup(salida.unico, cruce.unico, "row2"),
            Conexion(cruce.unico, escritura.unico, "out1"),
            al_terminar_subjob(anterior, origen.unico, indice),
        ]
        anterior = origen.unico
    n = len(productos) + 1
    # Relee el archivo que acaba de escribir: el chequeo mira lo que queda registrado.
    chequeo = nodo_desde_plantilla(
        "tFileInputDelimited",
        "tFileInputDelimited_chk",
        PASO_X,
        4 * PASO_Y,
        {"FILENAME": destino, "FIELDSEPARATOR": java(";"), "HEADER": "1", "DIE_ON_ERROR": "true"},
        columnas=salida_cols,
        ruta_java=ruta_java,
    )
    marca = nodo_desde_plantilla(
        "tJavaRow",
        "tJavaRow_chk",
        2 * PASO_X,
        4 * PASO_Y,
        {"CODE": _codigo_chequeo()},
        columnas=salida_cols,
        ruta_java=ruta_java,
    )
    fallo = nodo_desde_plantilla(
        "tDie",
        "tDie_conc",
        3 * PASO_X,
        4 * PASO_Y,
        {
            "MESSAGE": f'(String) globalMap.get("{MENSAJE}")',
            "CODE": str(CODIGO_NO_CONCILIA),
            "EXIT_JVM": "true",
        },
        ruta_java=ruta_java,
    )
    nodos += [chequeo, marca, fallo]
    conexiones += [
        al_terminar_subjob(anterior, chequeo.unico, n),
        Conexion(chequeo.unico, marca.unico, "row1"),
        si(marca.unico, fallo.unico, f'((String) globalMap.get("{MENSAJE}")) != null'),
    ]
    parametros = [ParametroContexto("ruta_resultados")]
    parametros += [ParametroContexto(variables[k]) for k in ("anio", "mes", "dia")]
    parametros.append(
        ParametroContexto(
            TOLERANCIA,
            valor=TOLERANCIA_OMISION,
            comentario="Tolerancia de saldo. Valor por omisión; confirmar con negocio.",
        )
    )
    return Job(
        nombre or arq.conciliacion,
        nodos=nodos,
        conexiones=conexiones,
        contextos={"Default": parametros},
    )


__all__ = ["COLUMNAS_CONCILIACION", "CODIGO_NO_CONCILIA", "MENSAJE", "job_conciliacion"]
