"""Jobs del diseño de Talend armados desde la arquitectura declarada y el modelo de proceso.

Por ahora el Job padre (sección 3.1 del diseño): validar el entorno, leer la fecha, correr los
hijos en orden y recorrer los productos. Cada pieza es un componente real con plantilla de
Studio; lo que el SAS no demuestra (la tabla de origen de cada producto) queda vacío y se
informa como pendiente.
"""

from __future__ import annotations

from dataclasses import dataclass

from sgm.talend_item.arquitectura import Arquitectura
from sgm.talend_item.componentes import fixed_flow_input, log_row
from sgm.talend_item.conexiones import al_terminar_componente, al_terminar_subjob, iterar, si
from sgm.talend_item.item import _id
from sgm.talend_item.modelo import Columna, Conexion, Job, Nodo, ParametroContexto
from sgm.talend_item.plantillas import nodo_desde_plantilla

PASO_X = 200  # separación horizontal entre subjobs en el lienzo
PASO_Y = 120


@dataclass(frozen=True)
class ProductoJob:
    """Una fila de la tabla de productos que recorre el padre."""

    producto: str
    ruta_origen: str  # archivo de datos del producto, tal como lo baja el SAS; vacío = pendiente
    sufijo: str
    # Excel de homologación de tipo de documento de ese producto; vacío = sin validación.
    arch_hom_tipo_doc: str = ""


def java(valor: str) -> str:
    """Literal de cadena de Java."""
    return '"' + valor.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def run_job(
    unico: str,
    hijo: str,
    proyecto: str,
    parametros: dict[str, str] | None = None,
    x: int = 0,
    y: int = 0,
    ruta_java: str | None = None,
) -> Nodo:
    """`tRunJob` hacia el Job `hijo` (versión más reciente), transmitiendo el contexto completo.

    `parametros` mapea parámetro de contexto del hijo a una expresión de Java del padre.
    """
    celdas = tuple(
        celda
        for nombre, expresion in (parametros or {}).items()
        for celda in (("PARAM_NAME_COLUMN", nombre), ("PARAM_VALUE_COLUMN", expresion))
    )
    return nodo_desde_plantilla(
        "tRunJob",
        unico,
        x,
        y,
        {
            "PROCESS": hijo,
            "PROCESS:PROCESS_TYPE_PROCESS": f"{proyecto}:{_id(f'{hijo}_0.1:id')}",
            "TRANSMIT_WHOLE_CONTEXT": "true",
        },
        {"CONTEXTPARAMS": celdas},
        ruta_java=ruta_java,
    )


def codigo_validar_entorno(entornos: tuple[str, ...]) -> str:
    """Código del Prejob: marca si `env_nombre` es uno de los entornos declarados."""
    lista = ", ".join(java(e) for e in entornos)
    return (
        f"java.util.List<String> validos = java.util.Arrays.asList({lista});\n"
        'globalMap.put("env_valido", validos.contains(context.env_nombre));'
    )


CONDICION_ENTORNO_INVALIDO = '!((Boolean) globalMap.get("env_valido"))'


def job_padre(
    arq: Arquitectura,
    productos: list[ProductoJob],
    ruta_java: str | None = None,
    periodo: tuple[list[Nodo], list[Conexion]] = ([], []),
    contextos_periodo: list[ParametroContexto] | None = None,
) -> Job:
    """Job padre: Prejob, periodo, productos en iteración, totales, conciliación y Postjob.

    `periodo` son los nodos que leen la fecha del proceso al contexto (ver `periodo.py`); si vienen
    vacíos el padre arranca directamente en los productos.
    """
    nodos_p, conexiones_p = periodo
    texto = [Columna("producto"), Columna("ruta_origen"), Columna("sufijo")]
    if any(p.arch_hom_tipo_doc for p in productos):
        texto.append(Columna("arch_hom_tipo_doc"))
    filas = [
        [java(p.producto.upper()), java(p.ruta_origen), java(p.sufijo)]
        + ([java(p.arch_hom_tipo_doc)] if len(texto) == 4 else [])
        for p in productos
    ]
    y = 2 * PASO_Y  # el periodo ocupa la fila de y = PASO_Y
    nodos = [
        nodo_desde_plantilla("tPrejob", "tPrejob_1", 0, 0, ruta_java=ruta_java),
        nodo_desde_plantilla(
            "tJava",
            "tJava_1",
            PASO_X,
            0,
            {"CODE": codigo_validar_entorno(arq.entornos)},
            ruta_java=ruta_java,
        ),
        nodo_desde_plantilla(
            "tDie",
            "tDie_1",
            2 * PASO_X,
            0,
            {"MESSAGE": '"env_nombre invalido: " + context.env_nombre', "EXIT_JVM": "true"},
            ruta_java=ruta_java,
        ),
        *nodos_p,
        fixed_flow_input("tFixedFlowInput_1", texto, filas, 0, y, ruta_java or ""),
        nodo_desde_plantilla("tFlowToIterate", "tFlowToIterate_1", PASO_X, y, ruta_java=ruta_java),
        run_job(
            "tRunJob_1",
            arq.producto,
            arq.proyecto,
            {c.nombre: f'(String) globalMap.get("row1.{c.nombre}")' for c in texto},
            2 * PASO_X,
            y,
            ruta_java,
        ),
        run_job("tRunJob_2", arq.totales, arq.proyecto, None, 0, y + PASO_Y, ruta_java),
        run_job("tRunJob_3", arq.conciliacion, arq.proyecto, None, 0, y + 2 * PASO_Y, ruta_java),
        nodo_desde_plantilla("tPostjob", "tPostjob_1", 0, y + 3 * PASO_Y, ruta_java=ruta_java),
        fixed_flow_input(
            "tFixedFlowInput_2",
            [Columna("mensaje")],
            [[java(arq.mensaje_fin)]],
            PASO_X,
            y + 3 * PASO_Y,
            ruta_java or "",
        ),
        log_row("tLogRow_1", [Columna("mensaje")], 2 * PASO_X, y + 3 * PASO_Y, ruta_java or ""),
    ]
    inicio = nodos_p[0].unico if nodos_p else None
    conexiones = [
        al_terminar_componente("tPrejob_1", "tJava_1"),
        si("tJava_1", "tDie_1", CONDICION_ENTORNO_INVALIDO),
        *conexiones_p,
        *([al_terminar_subjob(inicio, "tFixedFlowInput_1", 1)] if inicio else []),
        Conexion("tFixedFlowInput_1", "tFlowToIterate_1", "row1"),
        iterar("tFlowToIterate_1", "tRunJob_1"),
        al_terminar_subjob("tFixedFlowInput_1", "tRunJob_2", 2),
        al_terminar_subjob("tRunJob_2", "tRunJob_3", 3),
        al_terminar_componente("tPostjob_1", "tFixedFlowInput_2", 2),
        Conexion("tFixedFlowInput_2", "tLogRow_1", "row2"),
    ]
    extras = [ParametroContexto("ruta_resultados")] if arq.validaciones else []
    contextos = {"Default": [ParametroContexto("env_nombre"), *extras, *(contextos_periodo or [])]}
    contextos.update({e: [ParametroContexto("env_nombre", valor=e)] for e in arq.entornos})
    return Job(arq.padre, nodos=nodos, conexiones=conexiones, contextos=contextos)


def job_pendiente(
    nombre: str,
    motivo: str,
    parametros: tuple[str, ...] = (),
    ruta_java: str | None = None,
) -> Job:
    """Job hijo todavía sin lógica: un `tJava` que informa el motivo y los parámetros heredados."""
    lineas = [f"System.out.println({java(nombre + ': PENDIENTE, ' + motivo)});"]
    lineas += [f'System.out.println("  {p} = " + context.{p});' for p in parametros]
    nodo = nodo_desde_plantilla(
        "tJava", "tJava_1", 0, 0, {"CODE": "\n".join(lineas)}, ruta_java=ruta_java
    )
    contextos = {"Default": [ParametroContexto(p) for p in parametros]} if parametros else {}
    return Job(nombre, nodos=[nodo], contextos=contextos)


def jobs_hijos(
    arq: Arquitectura,
    variables_periodo: tuple[str, ...] = (),
    lookups: str = "",
    ruta_java: str | None = None,
    producto_real: Job | None = None,
    totales_real: Job | None = None,
) -> list[Job]:
    """Hijos del padre. Mientras no se traduzca su lógica, cada uno dice qué le falta.

    Cada hijo declara las variables del periodo que hereda del padre y las imprime, para que se
    vea que el contexto llega. `lookups` describe los Excel que `job_producto` usará en su `tMap`.
    `totales_real` es el `job_totales` ya emitido (R2-02); sin él queda como pendiente.
    """
    producto = ("producto", "ruta_origen", "sufijo", *variables_periodo)
    return [
        producto_real
        or job_pendiente(
            arq.producto,
            "falta la lectura, la validación y las salidas del producto" + lookups,
            producto,
            ruta_java,
        ),
        totales_real
        or job_pendiente(
            arq.totales,
            "falta unir totales de origen y de salida",
            variables_periodo,
            ruta_java,
        ),
        job_pendiente(
            arq.conciliacion, "falta conciliar origen contra salida", variables_periodo, ruta_java
        ),
    ]
