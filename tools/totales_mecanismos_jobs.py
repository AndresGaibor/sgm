"""Jobs mínimos de la prueba R2-01 (hito 97): tres mecanismos para pasar totales entre Jobs.

(a) `tBufferOutput` y `PROPAGATE_CHILD_RESULT`; (b) archivo por producto y Job de totales que los
añade en orden (`tUnite` no compila, ver PROGRESS); (c) `resultado` y `globalMap` del hijo. Nombres
base `mec_<x>_padre`, `mec_<x>_hijo` y `mec_b_totales`; `renombrar` les pone el sufijo del intento.
"""

from __future__ import annotations

from sgm.talend_item.componentes import log_row
from sgm.talend_item.conexiones import al_terminar_subjob
from sgm.talend_item.item import _id
from sgm.talend_item.jobs_diseno import java
from sgm.talend_item.modelo import Columna, Conexion, Job, ParametroContexto
from sgm.talend_item.plantillas import nodo_desde_plantilla
from sgm.talend_item.totalizadores import operaciones, totales

ENTRADA = (Columna("CLAVE"), Columna("saldo", "id_BigDecimal"))
TOTALES = (Columna("registros", "id_Long"), Columna("suma_saldo", "id_BigDecimal"))
OPERACIONES = operaciones(True, "CLAVE", "registros", "suma_saldo")


def _contexto(*nombres: str, valores: dict[str, str] | None = None) -> dict:
    valores = valores or {}
    return {"Default": [ParametroContexto(n, valor=valores.get(n, "")) for n in nombres]}


def _println(expresion: str) -> str:
    return f"System.out.println({expresion});"


def _tjava(unico: str, lineas: list[str], x: int, y: int) -> object:
    return nodo_desde_plantilla("tJava", unico, x, y, {"CODE": "\n".join(lineas)})


def _entrada_producto(unico: str, x: int, y: int) -> object:
    """`tFileInputDelimited` del archivo de origen `CLAVE;saldo`, sin cabecera."""
    return nodo_desde_plantilla(
        "tFileInputDelimited",
        unico,
        x,
        y,
        {
            "FILENAME": "context.ruta_origen",
            "FIELDSEPARATOR": java(";"),
            "HEADER": "0",
            "DIE_ON_ERROR": "true",
        },
        columnas=list(ENTRADA),
    )


def _salida(unico: str, x: int, y: int, nombre: str, append: bool = False) -> object:
    """`tFileOutputDelimited` de `registros;suma_saldo`, con cabecera salvo al añadir."""
    return nodo_desde_plantilla(
        "tFileOutputDelimited",
        unico,
        x,
        y,
        {
            "FILENAME": nombre,
            "FIELDSEPARATOR": java(";"),
            "INCLUDEHEADER": str(not append).lower(),
            "APPEND": str(append).lower(),
        },
        columnas=list(TOTALES),
    )


def _hijo(nombre: str, arranque: list[str], salida: object, extra: tuple[str, ...]) -> Job:
    """Subjob del hijo: tJava -> tFileInputDelimited -> tAggregateRow -> salida."""
    nodos = [
        _tjava("tJava_1", arranque, 0, 0),
        _entrada_producto("tFileInputDelimited_1", 240, 0),
        totales("tAggregateRow_1", list(TOTALES), OPERACIONES, 480, 0, None),
        salida,
    ]
    conexiones = [
        al_terminar_subjob("tJava_1", "tFileInputDelimited_1"),
        Conexion("tFileInputDelimited_1", "tAggregateRow_1", "row1"),
        Conexion("tAggregateRow_1", salida.unico, "row2"),
    ]
    contexto = _contexto(
        "producto", "ruta_origen", "ruta_trabajo", "sufijo", *extra,
        valores={"resultado": "SIN_VALOR"},
    )  # fmt: skip
    return Job(nombre, nodos=nodos, conexiones=conexiones, contextos=contexto)


def hijo_a() -> Job:
    """Hijo (a): el total sale por `tBufferOutput`."""
    buffer = nodo_desde_plantilla(
        "tBufferOutput", "tBufferOutput_1", 720, 0, columnas=list(TOTALES)
    )
    return _hijo(
        "mec_a_hijo", [_println('"mec_a_hijo arranca, sufijo=" + context.sufijo')], buffer, ()
    )


def hijo_b() -> Job:
    """Hijo (b): el total se escribe en `totales_origen_<sufijo>.csv` de la carpeta de trabajo."""
    archivo = _salida(
        "tFileOutputDelimited_1",
        720,
        0,
        'context.ruta_trabajo + "totales_origen_" + context.sufijo + ".csv"',  # noqa: E501
    )
    return _hijo(
        "mec_b_hijo", [_println('"mec_b_hijo arranca, sufijo=" + context.sufijo')], archivo, ()
    )


def hijo_c() -> Job:
    """Hijo (c): escribe `resultado` en su contexto y en `globalMap`, y muestra su total."""
    arranque = [
        'context.resultado = "HIJO_" + context.sufijo;',
        'globalMap.put("resultado", context.resultado);',
        _println('"mec_c_hijo fija resultado=" + context.resultado'),
    ]
    return _hijo(
        "mec_c_hijo", arranque, log_row("tLogRow_1", list(TOTALES), 720, 0), ("resultado",)
    )


def totales_b() -> Job:
    """Job de totales de (b): añade los dos totales a `totales_unidos_b.csv`, en orden."""
    nodos = [
        _tjava("tJava_1", [_println('"mec_b_totales arranca"')], 0, 0),
        nodo_desde_plantilla(
            "tFileInputDelimited",
            "tFileInputDelimited_1",
            240,
            0,
            {
                "FILENAME": 'context.ruta_trabajo + "totales_origen_" + context.sufijo_1 + ".csv"',  # noqa: E501
                "FIELDSEPARATOR": java(";"),
                "HEADER": "1",
                "DIE_ON_ERROR": "true",
            },
            columnas=list(TOTALES),
        ),
        _salida("tFileOutputDelimited_1", 480, 0, 'context.ruta_trabajo + "totales_unidos_b.csv"'),
        nodo_desde_plantilla(
            "tFileInputDelimited",
            "tFileInputDelimited_2",
            240,
            120,
            {
                "FILENAME": 'context.ruta_trabajo + "totales_origen_" + context.sufijo_2 + ".csv"',  # noqa: E501
                "FIELDSEPARATOR": java(";"),
                "HEADER": "1",
                "DIE_ON_ERROR": "true",
            },
            columnas=list(TOTALES),
        ),
        _salida(
            "tFileOutputDelimited_2",
            480,
            120,
            'context.ruta_trabajo + "totales_unidos_b.csv"',
            True,
        ),
    ]
    conexiones = [
        al_terminar_subjob("tJava_1", "tFileInputDelimited_1", 1),
        Conexion("tFileInputDelimited_1", "tFileOutputDelimited_1", "row1"),
        al_terminar_subjob("tFileInputDelimited_1", "tFileInputDelimited_2", 2),
        Conexion("tFileInputDelimited_2", "tFileOutputDelimited_2", "row2"),
    ]
    return Job(
        "mec_b_totales",
        nodos=nodos,
        conexiones=conexiones,
        contextos=_contexto("ruta_trabajo", "sufijo_1", "sufijo_2"),
    )


def _run(
    unico: str,
    hijo: str,
    proyecto: str,
    parametros: dict[str, str],
    x: int,
    y: int,
    columnas: list[Columna] | None = None,
    propagar: bool = False,
) -> object:
    """`tRunJob` hacia `hijo`; `propagar` activa `PROPAGATE_CHILD_RESULT`."""
    celdas = tuple(
        celda
        for nombre, expresion in parametros.items()
        for celda in (("PARAM_NAME_COLUMN", nombre), ("PARAM_VALUE_COLUMN", expresion))
    )
    referencia = f"{proyecto}:{_id(f'{hijo}_0.1:id')}"
    return nodo_desde_plantilla(
        "tRunJob",
        unico,
        x,
        y,
        {
            "PROCESS": hijo,
            "PROCESS:PROCESS_TYPE_PROCESS": referencia,
            "TRANSMIT_WHOLE_CONTEXT": "true",
            "PROPAGATE_CHILD_RESULT": str(propagar).lower(),
        },
        {"CONTEXTPARAMS": celdas},
        columnas=columnas,
    )


def _producto(producto: str) -> dict[str, str]:
    """Parámetros del hijo para un producto: su nombre, su archivo y su sufijo de salida."""
    origen = "context.ruta_origen_cte" if producto == "CTE" else "context.ruta_origen_aho"
    return {"producto": f'"{producto}"', "ruta_origen": origen, "sufijo": f'"{producto}"'}


def _contexto_padre() -> dict:
    return _contexto(
        "ruta_origen_cte", "ruta_origen_aho", "ruta_trabajo", "sufijo", "resultado",
        valores={"resultado": "SIN_VALOR"},
    )  # fmt: skip


def padre_a(proyecto: str) -> Job:
    """Padre (a): cada `tRunJob` pasa su total a un archivo con `PROPAGATE_CHILD_RESULT`."""
    nodos = [
        _tjava("tJava_1", [_println('"mec_a_padre arranca"')], 0, 0),
        _run("tRunJob_1", "mec_a_hijo", proyecto, _producto("CTE"), 240, 0, list(TOTALES), True),
        _salida("tFileOutputDelimited_1", 480, 0, 'context.ruta_trabajo + "totales_a_CTE.csv"'),
        _run("tRunJob_2", "mec_a_hijo", proyecto, _producto("AHO"), 240, 120, list(TOTALES), True),
        _salida("tFileOutputDelimited_2", 480, 120, 'context.ruta_trabajo + "totales_a_AHO.csv"'),
    ]
    conexiones = [
        al_terminar_subjob("tJava_1", "tRunJob_1", 1),
        Conexion("tRunJob_1", "tFileOutputDelimited_1", "row1"),
        al_terminar_subjob("tRunJob_1", "tRunJob_2", 2),
        Conexion("tRunJob_2", "tFileOutputDelimited_2", "row1"),
    ]
    return Job("mec_a_padre", nodos=nodos, conexiones=conexiones, contextos=_contexto_padre())


def padre_b(proyecto: str) -> Job:
    """Padre (b): lanza los hijos, que dejan sus archivos, y luego el Job de totales."""
    nodos = [
        _tjava("tJava_1", [_println('"mec_b_padre arranca"')], 0, 0),
        _run("tRunJob_1", "mec_b_hijo", proyecto, _producto("CTE"), 240, 0),
        _run("tRunJob_2", "mec_b_hijo", proyecto, _producto("AHO"), 480, 0),
        _run(
            "tRunJob_3",
            "mec_b_totales",
            proyecto,
            {"sufijo_1": '"CTE"', "sufijo_2": '"AHO"'},
            720,
            0,
        ),
    ]
    conexiones = [
        al_terminar_subjob("tJava_1", "tRunJob_1", 1),
        al_terminar_subjob("tRunJob_1", "tRunJob_2", 2),
        al_terminar_subjob("tRunJob_2", "tRunJob_3", 3),
    ]
    return Job("mec_b_padre", nodos=nodos, conexiones=conexiones, contextos=_contexto_padre())


def padre_c(proyecto: str) -> Job:
    """Padre (c): lee `resultado` antes y después de cada hijo, sin pasar por archivos."""

    def leer(unico: str, x: int, etiqueta: str) -> object:
        linea = (
            f'"mec_c_padre {etiqueta}: resultado=" + context.resultado'
            ' + " globalMap=" + globalMap.get("resultado")'
        )
        return _tjava(unico, [_println(linea)], x, 0)

    nodos = [
        leer("tJava_1", 0, "antes"),
        _run("tRunJob_1", "mec_c_hijo", proyecto, _producto("CTE"), 240, 0),
        leer("tJava_2", 480, "tras CTE"),
        _run("tRunJob_2", "mec_c_hijo", proyecto, _producto("AHO"), 720, 0),
        leer("tJava_3", 960, "tras AHO"),
    ]
    conexiones = [
        al_terminar_subjob("tJava_1", "tRunJob_1", 1),
        al_terminar_subjob("tRunJob_1", "tJava_2", 2),
        al_terminar_subjob("tJava_2", "tRunJob_2", 3),
        al_terminar_subjob("tRunJob_2", "tJava_3", 4),
    ]
    return Job("mec_c_padre", nodos=nodos, conexiones=conexiones, contextos=_contexto_padre())


def jobs_mecanismos(proyecto: str) -> dict[str, list[Job]]:
    """Hijos y padres de los tres mecanismos, por letra de mecanismo."""
    return {
        "a": [hijo_a(), padre_a(proyecto)],
        "b": [hijo_b(), totales_b(), padre_b(proyecto)],
        "c": [hijo_c(), padre_c(proyecto)],
    }
