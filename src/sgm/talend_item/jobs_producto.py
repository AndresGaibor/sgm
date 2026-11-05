"""`job_producto` del diseño (sección 3.3): lee el origen, totaliza y valida el tipo de documento.

El archivo del producto se lee una vez y se replica: una rama calcula los totales de origen (conteo
y suma del saldo, la base de la conciliación) y otra valida el tipo de documento contra el Excel de
homologación, con el mismo patrón que el SAS (`LEFT JOIN` + `IS MISSING` para el rechazo, `INNER
JOIN` para los válidos). Los válidos se totalizan y los rechazados se escriben con su `motivo`.

Todas las columnas se leen como texto: el SAS convierte después con `input()`. `cli_talend` pasa en
`numericas` las columnas que `esquema_csv` demuestra como numéricas, con el informat `w.d` real; con
eso se inserta un `tMap` de normalización que aplica `input(left(x), w.d)` (expresiones verificadas
en Studio, hito 83) y devuelve el mismo esquema en texto. La comparación del tipo de documento es de
texto contra texto: en el SAS `TIPO_DOC` es numérico (`input(left(VAR9), 8.)`), así que `01` y `1`
no casan igual. Esa diferencia está pendiente (R1-03).

Desde el hito 87 el `tReplicate_1` tiene una tercera rama: los tres flujos de vacíos y ceros de
R1-04 (`talend_item/flujos_fila.py`), con reglas y proyecciones leídas del SAS real. Desde el hito
89 tiene una cuarta: los dos rechazos de cuenta/codex de R1-06 en la **forma del SAS real**
(`NOT BETWEEN` con `RELACION = 1000`), más los válidos y la consolidación con `INCONSISTENCIA`
(`talend_item/flujos_cuenta_real.py`). Los helpers de totales y de homologación viven en
`totalizadores.py` para no pasar de 300 líneas.
"""

from __future__ import annotations

from sgm.proceso.reglas_cuenta_real import ReglasCuentaReal
from sgm.proceso.reglas_fila import ReglaFila
from sgm.talend_item.arquitectura import Arquitectura, ValidacionProducto
from sgm.talend_item.componentes import log_row
from sgm.talend_item.conexiones import al_terminar_subjob, lookup
from sgm.talend_item.flujos_cuenta_real import componentes as componentes_cuenta
from sgm.talend_item.flujos_fila import componentes as componentes_flujos
from sgm.talend_item.jobs_diseno import java
from sgm.talend_item.modelo import Columna, Conexion, Job, ParametroContexto
from sgm.talend_item.normalizacion import as_text, input_left_wd
from sgm.talend_item.periodo import HOJA_POR_DEFECTO
from sgm.talend_item.plantillas import nodo_desde_plantilla
from sgm.talend_item.tmap import EntradaMap, SalidaMap, tmap
from sgm.talend_item.totalizadores import a_decimal, homologacion, operaciones, totales

MOTIVO = "motivo"


def job_producto(
    arq: Arquitectura,
    columnas: tuple[str, ...],
    variables_periodo: tuple[str, ...] = (),
    pendiente: str = "",
    delimitador: str = ";",
    ruta_java: str | None = None,
    validacion: ValidacionProducto | None = None,
    numericas: dict[str, tuple[int, int]] | None = None,
    flujos: list[ReglaFila] | None = None,
    cuenta: ReglasCuentaReal | None = None,
) -> Job:
    """Lee `context.ruta_origen`, normaliza, totaliza el origen y separa válidos de rechazos.

    `numericas` es columna -> (w, d) del informat que el SAS demuestra. Sin él no se emite el
    `tMap` de normalización, para no inventar conversiones que el programa no declara. `flujos` es
    la terna canónica de R1-04 que `reglas_fila.flujos_producto` leyó del SAS; `cuenta` es la
    pareja de reglas de R1-06 que `reglas_cuenta_real` leyó del programa real. Sin ellos el Job
    queda como en el hito 84.
    """
    cols = [Columna(c) for c in columnas]
    informats = dict(numericas or {})
    parametros = ["producto", "ruta_origen", "sufijo", *variables_periodo]
    if validacion is not None:
        parametros += ["arch_hom_tipo_doc", "ruta_insumos", "hoja_excel"]
    if validacion is not None or flujos or cuenta is not None:
        parametros.append("ruta_resultados")
    mensaje = f"{arq.producto}: lee el archivo de origen del producto. Pendiente: {pendiente}"
    lineas = [f"System.out.println({java(mensaje)});"]
    lineas += [f'System.out.println("  {p} = " + context.{p});' for p in parametros]
    con_saldo = arq.columna_saldo in columnas
    w_saldo, d_saldo = informats.get(arq.columna_saldo, (20, 0))
    llave = cols[0]
    saldo = Columna("saldo", "id_BigDecimal")
    salida_map = [llave, saldo] if con_saldo else [llave]
    expresiones = {llave.nombre: f"row1.{llave.nombre}"}
    if con_saldo:
        expresiones["saldo"] = a_decimal(arq.columna_saldo, ancho=w_saldo, decimales=d_saldo)
    totales_origen = [Columna("registros_origen", "id_Long")]
    if con_saldo:
        totales_origen.append(Columna("suma_saldo_origen", "id_BigDecimal"))
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
    ]
    if informats:
        normalizadas = {
            c.nombre: (
                as_text(input_left_wd(f"row1.{c.nombre}", *informats[c.nombre]))
                if c.nombre in informats
                else f"row1.{c.nombre}"
            )
            for c in cols
        }
        nodos.append(
            tmap(
                "tMap_normalizacion",
                [EntradaMap("row1", cols)],
                [SalidaMap("normalizados", cols, normalizadas)],
                120,
                120,
                ruta_java,
            )
        )
    nodos += [
        nodo_desde_plantilla(
            "tReplicate", "tReplicate_1", 240, 120, columnas=cols, ruta_java=ruta_java
        ),
        tmap("tMap_1", [EntradaMap("row1", cols)], [SalidaMap("out1", salida_map, expresiones)],
             480, 60, ruta_java),
        totales(
            "tAggregateRow_1",
            totales_origen,
            operaciones(con_saldo, llave.nombre, "registros_origen", "suma_saldo_origen"),
            720,
            60,
            ruta_java,
        ),
        log_row("tLogRow_1", totales_origen, 960, 60, ruta_java or ""),
    ]
    conexiones = [al_terminar_subjob("tJava_1", "tFileInputDelimited_1")]
    if informats:
        conexiones += [
            Conexion("tFileInputDelimited_1", "tMap_normalizacion", "row1"),
            Conexion("tMap_normalizacion", "tReplicate_1", "normalizados"),
        ]
    else:
        conexiones.append(Conexion("tFileInputDelimited_1", "tReplicate_1", "row1"))
    conexiones += [
        Conexion("tReplicate_1", "tMap_1", "row1"),
        Conexion("tMap_1", "tAggregateRow_1", "out1"),
        Conexion("tAggregateRow_1", "tLogRow_1", "row2"),
    ]
    if validacion is not None:
        motivo = Columna(MOTIVO)
        valido = [llave, *([saldo] if con_saldo else [])]
        expresiones_validos = {llave.nombre: f"copy2.{llave.nombre}"}
        if con_saldo:
            expresiones_validos["saldo"] = a_decimal(
                arq.columna_saldo, "copy2", w_saldo, d_saldo
            )
        nodos += [
            homologacion(validacion, 240, 360, ruta_java),
            tmap(
                "tMap_2",
                [
                    EntradaMap("copy2", cols),
                    EntradaMap(
                        "row2",
                        [Columna(validacion.columna_lookup)],
                        expresiones_union={
                            validacion.columna_lookup: f"copy2.{validacion.columna}"
                        },
                        union_interna=True,
                    ),
                ],
                [
                    SalidaMap(
                        "validos",
                        valido,
                        {
                            **expresiones_validos,
                        },
                    ),
                    SalidaMap(
                        "rechazados",
                        [llave, motivo],
                        {llave.nombre: f"copy2.{llave.nombre}", MOTIVO: java(validacion.motivo)},
                        rechazo_union=True,
                    ),
                ],
                480,
                360,
                ruta_java,
            ),
            totales(
                "tAggregateRow_2",
                [Columna("registros_validos", "id_Long")]
                + ([Columna("suma_saldo_valido", "id_BigDecimal")] if con_saldo else []),
                operaciones(con_saldo, llave.nombre, "registros_validos", "suma_saldo_valido"),
                720,
                300,
                ruta_java,
            ),
            nodo_desde_plantilla(
                "tFileOutputDelimited",
                "tFileOutputDelimited_1",
                720,
                420,
                {
                    "FILENAME": 'context.ruta_resultados + "doc_incorrectos_" + context.sufijo'
                    ' + ".csv"',
                    "FIELDSEPARATOR": '"|"',
                    "INCLUDEHEADER": "true",
                    "APPEND": "false",
                },
                columnas=[llave, motivo],
                ruta_java=ruta_java,
            ),
        ]
        conexiones += [
            lookup("tFileInputExcel_1", "tMap_2", "row2"),
            Conexion("tReplicate_1", "tMap_2", "copy2"),
            Conexion("tMap_2", "tAggregateRow_2", "validos"),
            Conexion(
                "tAggregateRow_2",
                "tLogRow_2",
                "row3",
            ),
            Conexion("tMap_2", "tFileOutputDelimited_1", "rechazados", "REJECT"),
        ]
        nodos.append(
            log_row(
                "tLogRow_2",
                [Columna("registros_validos", "id_Long")]
                + ([Columna("suma_saldo_valido", "id_BigDecimal")] if con_saldo else []),
                960,
                300,
                ruta_java or "",
            )
        )
    if flujos:
        nuevos, nuevas = componentes_flujos(flujos, cols, informats, ruta_java)
        nodos += nuevos
        conexiones += nuevas
    if cuenta is not None:
        nuevos, nuevas = componentes_cuenta(cuenta, cols, informats, ruta_java)
        nodos += nuevos
        conexiones += nuevas
    valores = {"hoja_excel": HOJA_POR_DEFECTO}
    contextos = {
        "Default": [ParametroContexto(p, valor=valores.get(p, "")) for p in parametros]
    }
    return Job(arq.producto, nodos=nodos, conexiones=conexiones, contextos=contextos)


__all__ = ["HOJA_POR_DEFECTO", "job_producto"]
