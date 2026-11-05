"""`job_totales` real (R2-02): une los totales de origen y de salida de cada producto.

Mecanismo elegido en R2-01 (hito 97): cada `job_producto` deja en la carpeta de resultados un
archivo por producto y por tipo, `totales_origen_<producto>.csv` y `totales_salida_<producto>.csv`,
con una fila y el mismo esquema: `PRODUCTO;TIPO;NRO_FILAS;NRO_SALDOS_NO_VACIOS;SUMA_SALDO`.
Este Job los lee en orden y los añade al archivo final `<archivo_totales>_<anio><mes><dia>.csv`
con
`APPEND`. No se usa `tUnite`: en Studio 8.0.1 no compiló (NPE en `TUniteMainJava.generate`,
ver PROGRESS).

Los nombres de producto son los `sufijo` de `ProductoJob`, que el padre ya conoce. La fecha sale de
las variables de contexto del periodo (`AÑO`, `MES`, `DIA` del Excel de la fecha).
"""

from __future__ import annotations

from sgm.talend_item.arquitectura import Arquitectura
from sgm.talend_item.conexiones import al_terminar_subjob
from sgm.talend_item.jobs_diseno import java
from sgm.talend_item.modelo import Columna, Conexion, Job, Nodo, ParametroContexto
from sgm.talend_item.plantillas import nodo_desde_plantilla

COLUMNAS_TOTALES = (
    Columna("PRODUCTO"),
    Columna("TIPO"),
    Columna("NRO_FILAS"),
    Columna("NRO_SALDOS_NO_VACIOS"),
    Columna("SUMA_SALDO"),
)
TIPOS = ("origen", "salida")
RUTA_RESULTADOS = "ruta_resultados"
PASO_X = 240
PASO_Y = 120
COLUMNAS_PERIODO = {"AÑO": "anio", "MES": "mes", "DIA": "dia"}


def variables_fecha(arq: Arquitectura) -> dict[str, str]:
    """Nombre de la variable de contexto de año, mes y día según la declaración del periodo.

    Falla con el motivo si el periodo no declara `AÑO`, `MES` y `DIA`: sin ellos no hay nombre de
    archivo con fecha.
    """
    if arq.periodo is None:
        raise ValueError("job_totales necesita el periodo declarado (AÑO, MES, DIA)")
    variables: dict[str, str] = {}
    for columna, variable in arq.periodo.variables:
        clave = COLUMNAS_PERIODO.get(columna.strip().upper())
        if clave:
            variables[clave] = variable
    faltan = sorted(set(COLUMNAS_PERIODO.values()) - set(variables))
    if faltan:
        raise ValueError(f"el periodo no declara {faltan} para el nombre del archivo")
    return variables


def _entrada(unico: str, x: int, y: int, archivo: str) -> Nodo:
    """Lee un archivo de totales con cabecera; todas las columnas como texto, sin conversión."""
    return nodo_desde_plantilla(
        "tFileInputDelimited",
        unico,
        x,
        y,
        {
            "FILENAME": archivo,
            "FIELDSEPARATOR": java(";"),
            "HEADER": "1",
            # Un archivo mal formado debe fallar el Job; sin esto Studio solo registra el error.
            "DIE_ON_ERROR": "true",
        },
        columnas=list(COLUMNAS_TOTALES),
    )


def _salida(unico: str, x: int, y: int, archivo: str, primero: bool) -> Nodo:
    """Escribe el archivo de exógena; el primero con cabecera, los demás añaden filas."""
    return nodo_desde_plantilla(
        "tFileOutputDelimited",
        unico,
        x,
        y,
        {
            "FILENAME": archivo,
            "FIELDSEPARATOR": java(";"),
            "INCLUDEHEADER": str(primero).lower(),
            "APPEND": str(not primero).lower(),
        },
        columnas=list(COLUMNAS_TOTALES),
    )


def job_totales(
    arq: Arquitectura,
    productos: tuple[str, ...],
    ruta_java: str | None = None,
) -> Job:
    """Job de totales: una entrada y una salida por archivo, en orden de producto y de tipo.

    Para cada producto se leen primero `totales_origen_<p>.csv` y luego `totales_salida_<p>.csv`.
    Cada par de componentes forma su subjob y arranca cuando termina el anterior (`OnSubjobOk`).
    """
    if not productos:
        raise ValueError("job_totales necesita al menos un producto")
    if not arq.archivo_totales:
        raise ValueError("job_totales necesita archivo_totales en la decisión del programa")
    variables = variables_fecha(arq)
    fecha = f"context.{variables['anio']} + context.{variables['mes']} + context.{variables['dia']}"
    destino = (
        f'context.{RUTA_RESULTADOS} + "{arq.archivo_totales}_" + {fecha} + ".csv"'
    )
    archivos = [(producto, tipo) for producto in productos for tipo in TIPOS]
    mensaje = f"job_totales: une {len(archivos)} archivos de totales"
    nodos: list[Nodo] = [
        nodo_desde_plantilla(
            "tJava",
            "tJava_1",
            0,
            0,
            {"CODE": f"System.out.println({java(mensaje)});"},
            ruta_java=ruta_java,
        )
    ]
    conexiones: list[Conexion] = []
    anterior = "tJava_1"
    for indice, (producto, tipo) in enumerate(archivos, start=1):
        archivo = f'context.{RUTA_RESULTADOS} + "totales_{tipo}_{producto}.csv"'
        entrada = _entrada(f"tFileInputDelimited_{indice}", PASO_X * indice, 0, archivo)
        salida = _salida(
            f"tFileOutputDelimited_{indice}", PASO_X * indice, PASO_Y, destino,
            primero=indice == 1,
        )  # fmt: skip
        nodos += [entrada, salida]
        conexiones.append(Conexion(entrada.unico, salida.unico, "row1"))
        # Cada par es un subjob: arranca cuando termina el anterior (OnSubjobOk, ordinal `indice`).
        conexiones.append(al_terminar_subjob(anterior, entrada.unico, indice))
        anterior = entrada.unico
    parametros = [ParametroContexto(RUTA_RESULTADOS)]
    parametros += [ParametroContexto(variables[k]) for k in ("anio", "mes", "dia")]
    return Job(arq.totales, nodos=nodos, conexiones=conexiones, contextos={"Default": parametros})


__all__ = ["COLUMNAS_TOTALES", "job_totales", "variables_fecha"]
