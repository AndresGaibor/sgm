"""Jobs de la prueba R2-02 (hito 97): totales de origen y de salida del caso L8/totales/04.

`job_producto` todavía no escribe `totales_origen_<sufijo>.csv` ni `totales_salida_<sufijo>.csv`
(pendiente, ver PROGRESS). Por eso este productor mínimo los escribe con la misma lógica que
`job_producto` ya calcula: el saldo sale de `input(left(FIN_SALDO_CTA), 20.)` (`a_decimal`,
hito 85), el origen cuenta todas las filas y suma los saldos no faltantes, y la salida toma las
filas con `TIPO_CTA <> '03'`, que es un supuesto del caso y no del SAS.

Los archivos tienen el esquema que lee `job_totales`:
`PRODUCTO;TIPO;NRO_FILAS;NRO_SALDOS_NO_VACIOS;SUMA_SALDO`. En la salida, `NRO_SALDOS_NO_VACIOS`
va vacío: el caso no define ese conteo para la salida.
"""

from __future__ import annotations

from sgm.talend_item.conexiones import al_terminar_subjob
from sgm.talend_item.jobs_diseno import java
from sgm.talend_item.jobs_totales import COLUMNAS_TOTALES
from sgm.talend_item.modelo import Columna, Conexion, Job, ParametroContexto
from sgm.talend_item.plantillas import nodo_desde_plantilla
from sgm.talend_item.tmap import EntradaMap, SalidaMap, tmap
from sgm.talend_item.totalizadores import a_decimal, totales

COLUMNAS_ENTRADA = (
    "ANIO_PROCESO,MES_PROCESO,CODIGO_OFICINA,RELACION,CODIGO_SUCURSAL,TIPO_CTA,NRO_CTA,"
    "LLAVE_NOMBRE,TIPO_DOC,NRO_DOC,GMF,VAL_CRED_MES,NRO_CRED_MES,PROM_CRED_MES,MED_CRED_MES,"
    "VAL_DEB_MES,NRO_DEB_MES,PROM_DEB_MES,MED_SALDO_CTA,PROM_SALDO_CTA,MAX_SALDO_CTA,"
    "MIN_SALDO_CTA,FIN_SALDO_CTA"
).split(",")
# Columnas que el producto necesita después de leer: producto, tipo de cuenta, cuenta y saldo.
NORMALIZADAS = (
    Columna("PRODUCTO"),
    Columna("TIPO_CTA"),
    Columna("NRO_CTA"),
    Columna("saldo", "id_BigDecimal"),
)
OPERACIONES_ORIGEN = (
    ("OUTPUT_COLUMN", "NRO_FILAS"), ("FUNCTION", "count"),
    ("INPUT_COLUMN", "NRO_CTA"), ("IGNORE_NULL", "false"),
    ("OUTPUT_COLUMN", "NRO_SALDOS_NO_VACIOS"), ("FUNCTION", "count"),
    ("INPUT_COLUMN", "saldo"), ("IGNORE_NULL", "true"),
    ("OUTPUT_COLUMN", "SUMA_SALDO"), ("FUNCTION", "sum"),
    ("INPUT_COLUMN", "saldo"), ("IGNORE_NULL", "true"),
)  # fmt: skip
OPERACIONES_SALIDA = (
    ("OUTPUT_COLUMN", "NRO_FILAS"), ("FUNCTION", "count"),
    ("INPUT_COLUMN", "NRO_CTA"), ("IGNORE_NULL", "false"),
    ("OUTPUT_COLUMN", "SUMA_SALDO"), ("FUNCTION", "sum"),
    ("INPUT_COLUMN", "saldo"), ("IGNORE_NULL", "true"),
)  # fmt: skip
AGREGADO_ORIGEN = [
    Columna("NRO_FILAS", "id_Long"),
    Columna("NRO_SALDOS_NO_VACIOS", "id_Long"),
    Columna("SUMA_SALDO", "id_BigDecimal"),
]
AGREGADO_SALIDA = [Columna("NRO_FILAS", "id_Long"), Columna("SUMA_SALDO", "id_BigDecimal")]


def _numero(entrada: str, columna: str) -> str:
    """Texto del conteo, o vacío si es nulo: un valor faltante no se escribe como cero."""
    return f'{entrada}.{columna} == null ? "" : String.valueOf({entrada}.{columna})'


def _formato(
    unico: str,
    entrada: str,
    columnas: list[Columna],
    tipo: str,
    con_saldos: bool,
    x: int,
    y: int,
    ruta_java: str | None,
) -> object:
    """tMap que da al agregado el esquema del archivo de totales, con PRODUCTO y TIPO."""
    suma = f'{entrada}.SUMA_SALDO == null ? "" : {entrada}.SUMA_SALDO.toPlainString()'
    expresiones = {
        "PRODUCTO": "context.producto",
        "TIPO": java(tipo),
        "NRO_FILAS": _numero(entrada, "NRO_FILAS"),
        # La salida no define este conteo en el caso: el archivo lo deja vacío.
        "NRO_SALDOS_NO_VACIOS": (_numero(entrada, "NRO_SALDOS_NO_VACIOS") if con_saldos else '""'),
        "SUMA_SALDO": suma,
    }
    salida = [Columna(c.nombre) for c in COLUMNAS_TOTALES]
    return tmap(
        unico, [EntradaMap(entrada, columnas)], [SalidaMap("out_" + tipo, salida, expresiones)],
        x, y, ruta_java,
    )  # fmt: skip


def _escritura(unico: str, nombre: str, x: int, y: int) -> object:
    return nodo_desde_plantilla(
        "tFileOutputDelimited",
        unico,
        x,
        y,
        {
            "FILENAME": f'context.ruta_resultados + "{nombre}_" + context.sufijo + ".csv"',
            "FIELDSEPARATOR": java(";"),
            "INCLUDEHEADER": "true",
            "APPEND": "false",
        },
        columnas=[Columna(c.nombre) for c in COLUMNAS_TOTALES],
    )


def producto_caso(ruta_java: str | None = None) -> Job:
    """Productor mínimo: origen y salida de un producto, con su archivo de totales por tipo."""
    entrada = [Columna(c) for c in COLUMNAS_ENTRADA]
    expresiones = {
        "PRODUCTO": "context.producto",
        "TIPO_CTA": "row1.TIPO_CTA",
        "NRO_CTA": "row1.NRO_CTA",
        "saldo": a_decimal("FIN_SALDO_CTA", "row1", 20, 0),
    }
    nodos = [
        nodo_desde_plantilla(
            "tJava",
            "tJava_1",
            0,
            0,
            {"CODE": f"System.out.println({java('caso_totales: origen y salida del producto')});"},
            ruta_java=ruta_java,
        ),  # fmt: skip
        nodo_desde_plantilla(
            "tFileInputDelimited",
            "tFileInputDelimited_1",
            240,
            0,
            {
                "FILENAME": "context.ruta_origen",
                "FIELDSEPARATOR": java(";"),
                "HEADER": "0",
                "DIE_ON_ERROR": "true",
            },  # fmt: skip
            columnas=entrada,
            ruta_java=ruta_java,
        ),
        tmap(
            "tMap_1",
            [EntradaMap("row1", entrada)],
            [SalidaMap("out1", NORMALIZADAS, expresiones)],
            480,
            0,
            ruta_java,
        ),  # fmt: skip
        nodo_desde_plantilla(
            "tReplicate", "tReplicate_1", 720, 0, columnas=list(NORMALIZADAS), ruta_java=ruta_java
        ),
    ]
    conexiones = [
        al_terminar_subjob("tJava_1", "tFileInputDelimited_1"),
        Conexion("tFileInputDelimited_1", "tMap_1", "row1"),
        Conexion("tMap_1", "tReplicate_1", "out1"),
    ]
    # Rama de origen: todas las filas.
    nodos += [
        totales("tAggregateRow_1", AGREGADO_ORIGEN, OPERACIONES_ORIGEN, 960, 0, ruta_java),
        _formato("tMap_origen", "row2", AGREGADO_ORIGEN, "origen", True, 1200, 0, ruta_java),
        _escritura("tFileOutputDelimited_1", "totales_origen", 1440, 0),
    ]
    conexiones += [
        Conexion("tReplicate_1", "tAggregateRow_1", "row1"),
        Conexion("tAggregateRow_1", "tMap_origen", "row2"),
        Conexion("tMap_origen", "tFileOutputDelimited_1", "out_origen"),
    ]
    # Rama de salida: TIPO_CTA distinto de 03 (supuesto del caso).
    nodos += [
        tmap(
            "tMap_salida",
            [EntradaMap("copy2", list(NORMALIZADAS))],
            [
                SalidaMap(
                    "salida",
                    list(NORMALIZADAS),
                    {c.nombre: f"copy2.{c.nombre}" for c in NORMALIZADAS},
                    filtro='!"03".equals(copy2.TIPO_CTA.trim())',
                )
            ],  # fmt: skip
            960,
            200,
            ruta_java,
        ),
        totales("tAggregateRow_2", AGREGADO_SALIDA, OPERACIONES_SALIDA, 1200, 200, ruta_java),
        _formato("tMap_salida_fmt", "row3", AGREGADO_SALIDA, "salida", False, 1440, 200, ruta_java),
        _escritura("tFileOutputDelimited_2", "totales_salida", 1680, 200),
    ]
    conexiones += [
        Conexion("tReplicate_1", "tMap_salida", "copy2"),
        Conexion("tMap_salida", "tAggregateRow_2", "salida"),
        Conexion("tAggregateRow_2", "tMap_salida_fmt", "row3"),
        Conexion("tMap_salida_fmt", "tFileOutputDelimited_2", "out_salida"),
    ]
    contexto = [
        ParametroContexto(n) for n in ("producto", "ruta_origen", "ruta_resultados", "sufijo")
    ]
    return Job("caso_producto", nodos=nodos, conexiones=conexiones, contextos={"Default": contexto})


__all__ = ["COLUMNAS_ENTRADA", "producto_caso"]
