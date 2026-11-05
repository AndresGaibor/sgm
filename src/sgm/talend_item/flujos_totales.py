"""Ramas de totales de `job_producto` (R2-02, parte 2): los archivos que lee `job_totales`.

Cada `job_producto` escribe en la carpeta de resultados dos archivos de una fila con el esquema
`PRODUCTO;TIPO;NRO_FILAS;NRO_SALDOS_NO_VACIOS;SUMA_SALDO` (el de `jobs_totales.COLUMNAS_TOTALES`):

* `totales_origen_<sufijo>.csv`: todas las filas que lee el Job. Conteo de filas, conteo de saldos
  no faltantes y suma de esos saldos. Usa el `tAggregateRow_1` de `jobs_producto`; aquí solo se
  da formato y se escribe.
* `totales_salida_<sufijo>.csv`: las filas de la rama `validos` (tipo de documento homologado, el
  `tAggregateRow_2`). Es la definición "saldos validados" de la sección 1.2 del manual de diseño
  (`docs/diseno-talend-*-depositos.md`). El conteo de saldos no vacíos queda vacío: el caso
  `L8/totales/04` no lo define para la salida.

Este módulo existe porque `jobs_producto.py` ya estaba en el límite de 300 líneas.

Un faltante numérico no suma (`sum` ignora nulos) y el conteo de saldos no vacíos no cuenta los
faltantes. Si una suma queda nula (todos los saldos faltan) se escribe cadena vacía, nunca cero.
"""

from __future__ import annotations

from sgm.talend_item.arquitectura import ValidacionProducto
from sgm.talend_item.componentes import log_row
from sgm.talend_item.jobs_diseno import java
from sgm.talend_item.jobs_totales import COLUMNAS_TOTALES
from sgm.talend_item.modelo import Columna, Conexion, Nodo
from sgm.talend_item.plantillas import nodo_desde_plantilla
from sgm.talend_item.tmap import EntradaMap, SalidaMap, tmap

ENTRADA_ORIGEN = "row_tot_o"  # conexión del agregado de origen hacia su formato
ENTRADA_SALIDA = "row_tot_s"  # conexión del agregado de validos hacia su formato
COLUMNAS_SALIDA = [
    Columna("registros_validos", "id_Long"),
    Columna("suma_saldo_valido", "id_BigDecimal"),
]


def columnas_origen(con_saldo: bool) -> list[Columna]:
    """Columnas del agregado de origen: filas, saldos no vacíos y suma (con saldo)."""
    columnas = [Columna("registros_origen", "id_Long")]
    if con_saldo:
        columnas += [
            Columna("saldos_origen", "id_Long"),
            Columna("suma_saldo_origen", "id_BigDecimal"),
        ]
    return columnas


def operaciones_origen(con_saldo: bool, llave: str) -> tuple[tuple[str, str], ...]:
    """Operaciones del `tAggregateRow_1`: filas por la llave; con saldo, saldos no nulos y suma."""
    resultado = [
        ("OUTPUT_COLUMN", "registros_origen"),
        ("FUNCTION", "count"),
        ("INPUT_COLUMN", llave),
        ("IGNORE_NULL", "false"),
    ]
    if con_saldo:
        resultado += [
            ("OUTPUT_COLUMN", "saldos_origen"),
            ("FUNCTION", "count"),
            ("INPUT_COLUMN", "saldo"),
            ("IGNORE_NULL", "true"),
            ("OUTPUT_COLUMN", "suma_saldo_origen"),
            ("FUNCTION", "sum"),
            ("INPUT_COLUMN", "saldo"),
            ("IGNORE_NULL", "true"),
        ]
    return tuple(resultado)


def _numero(entrada: str, columna: str) -> str:
    """Texto del conteo; un nulo se escribe vacío, nunca como cero."""
    return f'{entrada}.{columna} == null ? "" : String.valueOf({entrada}.{columna})'


def _suma(entrada: str, columna: str) -> str:
    """Texto de la suma BigDecimal; nula (todos los saldos faltan) se escribe vacía."""
    return f'{entrada}.{columna} == null ? "" : {entrada}.{columna}.toPlainString()'


def _formato(
    unico: str,
    entrada: str,
    columnas: list[Columna],
    tipo: str,
    expresiones_tipo: dict[str, str],
    x: int,
    y: int,
    ruta_java: str | None,
) -> Nodo:
    """tMap que da al agregado el esquema del archivo de totales, con PRODUCTO y TIPO.

    Dos salidas con las mismas expresiones: `out_<tipo>` al archivo y `log_<tipo>` al `tLogRow`.
    El agregado no puede tener dos conexiones principales: en Studio la segunda llegaba sin
    valores (v100a, v100b), así que el log cuelga del formato.
    """
    expresiones = {"PRODUCTO": "context.producto", "TIPO": java(tipo), **expresiones_tipo}
    columnas_salida = list(COLUMNAS_TOTALES)
    return tmap(
        unico,
        [EntradaMap(entrada, columnas)],
        [
            SalidaMap("out_" + tipo, columnas_salida, expresiones),
            SalidaMap("log_" + tipo, columnas_salida, dict(expresiones)),
        ],
        x,
        y,
        ruta_java,
    )


def _escritura(unico: str, archivo: str, x: int, y: int, ruta_java: str | None) -> Nodo:
    """Escribe `<archivo>_<sufijo>.csv` en la carpeta de resultados, con cabecera."""
    return nodo_desde_plantilla(
        "tFileOutputDelimited",
        unico,
        x,
        y,
        {
            "FILENAME": f'context.ruta_resultados + "{archivo}_" + context.sufijo + ".csv"',
            "FIELDSEPARATOR": java(";"),
            "INCLUDEHEADER": "true",
            "APPEND": "false",
        },
        columnas=list(COLUMNAS_TOTALES),
        ruta_java=ruta_java,
    )


def componentes(
    con_saldo: bool, validacion: ValidacionProducto | None, ruta_java: str | None
) -> tuple[list[Nodo], list[Conexion]]:
    """Formatos y escrituras de los dos archivos de totales, conectados a sus agregados.

    Exige lo que el archivo necesita: un saldo que sumar y la rama `validos` que es la salida.
    """
    if not con_saldo:
        raise ValueError("los totales de origen y de salida necesitan la columna de saldo")
    if validacion is None:
        raise ValueError("la salida de totales son los válidos de la validación de producto")
    origen = columnas_origen(True)
    nodos = [
        _formato(
            "tMap_tot_origen",
            ENTRADA_ORIGEN,
            origen,
            "origen",
            {
                "NRO_FILAS": _numero(ENTRADA_ORIGEN, "registros_origen"),
                "NRO_SALDOS_NO_VACIOS": _numero(ENTRADA_ORIGEN, "saldos_origen"),
                "SUMA_SALDO": _suma(ENTRADA_ORIGEN, "suma_saldo_origen"),
            },
            960,
            120,
            ruta_java,
        ),
        _escritura("tFileOutputDelimited_tot_origen", "totales_origen", 1200, 60, ruta_java),
        log_row("tLogRow_1", list(COLUMNAS_TOTALES), 1200, 180, ruta_java or ""),
        _formato(
            "tMap_tot_salida",
            ENTRADA_SALIDA,
            COLUMNAS_SALIDA,
            "salida",
            {
                "NRO_FILAS": _numero(ENTRADA_SALIDA, "registros_validos"),
                # La salida no define este conteo en el caso: el archivo lo deja vacío.
                "NRO_SALDOS_NO_VACIOS": '""',
                "SUMA_SALDO": _suma(ENTRADA_SALIDA, "suma_saldo_valido"),
            },
            960,
            420,
            ruta_java,
        ),
        _escritura("tFileOutputDelimited_tot_salida", "totales_salida", 1200, 300, ruta_java),
        log_row("tLogRow_2", list(COLUMNAS_TOTALES), 1200, 420, ruta_java or ""),
    ]
    conexiones = [
        Conexion("tAggregateRow_1", "tMap_tot_origen", ENTRADA_ORIGEN),
        Conexion("tMap_tot_origen", "tFileOutputDelimited_tot_origen", "out_origen"),
        Conexion("tMap_tot_origen", "tLogRow_1", "log_origen"),
        Conexion("tAggregateRow_2", "tMap_tot_salida", ENTRADA_SALIDA),
        Conexion("tMap_tot_salida", "tFileOutputDelimited_tot_salida", "out_salida"),
        Conexion("tMap_tot_salida", "tLogRow_2", "log_salida"),
    ]
    return nodos, conexiones


__all__ = ["columnas_origen", "componentes", "operaciones_origen"]
