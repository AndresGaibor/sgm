"""`job_producto` del diseño (sección 3.3): lee el origen, totaliza y valida el tipo de documento.

El archivo del producto se lee una vez y se replica: una rama calcula los totales de origen (conteo
y suma del saldo, la base de la conciliación) y otra valida el tipo de documento contra el Excel de
homologación, con el mismo patrón que el SAS (`LEFT JOIN` + `IS MISSING` para el rechazo, `INNER
JOIN` para los válidos). Los válidos se totalizan y los rechazados se escriben con su `motivo`.

Todas las columnas se leen como texto: el SAS convierte después con `input()`. La comparación del
tipo de documento es, por tanto, de texto contra texto: en el SAS `TIPO_DOC` es numérico
(`input(left(VAR9), 8.)`), así que `01` y `1` no casan igual. Esa diferencia está pendiente.
"""

from __future__ import annotations

from sgm.talend_item.arquitectura import Arquitectura, ValidacionProducto
from sgm.talend_item.componentes import log_row
from sgm.talend_item.conexiones import al_terminar_subjob, lookup
from sgm.talend_item.jobs_diseno import java
from sgm.talend_item.modelo import Columna, Conexion, Job, Nodo, ParametroContexto
from sgm.talend_item.periodo import HOJA_POR_DEFECTO
from sgm.talend_item.plantillas import nodo_desde_plantilla
from sgm.talend_item.tmap import EntradaMap, SalidaMap, tmap

MOTIVO = "motivo"


def _a_decimal(columna: str, entrada: str = "row1") -> str:
    """Expresión de Java equivalente a `input(left(col), 20.)`: vacío es nulo, el resto decimal."""
    valor = f"{entrada}.{columna}"
    vacio = f"{valor} == null || {valor}.trim().isEmpty()"
    return f"{vacio} ? null : new java.math.BigDecimal({valor}.trim())"


def _operaciones(
    con_saldo: bool, llave: str, conteo: str, suma: str
) -> tuple[tuple[str, str], ...]:
    """Operaciones del `tAggregateRow`: conteo por la llave y, si hay saldo, su suma."""
    operaciones = [
        ("OUTPUT_COLUMN", conteo),
        ("FUNCTION", "count"),
        ("INPUT_COLUMN", llave),
        ("IGNORE_NULL", "false"),
    ]
    if con_saldo:
        operaciones += [
            ("OUTPUT_COLUMN", suma),
            ("FUNCTION", "sum"),
            ("INPUT_COLUMN", "saldo"),
            ("IGNORE_NULL", "true"),
        ]
    return tuple(operaciones)


def _totales(
    unico: str,
    columnas: list[Columna],
    operaciones: tuple[tuple[str, str], ...],
    x: int,
    y: int,
    ruta_java: str | None,
) -> Nodo:
    return nodo_desde_plantilla(
        "tAggregateRow",
        unico,
        x,
        y,
        tablas={"OPERATIONS": operaciones},
        columnas=columnas,
        ruta_java=ruta_java,
    )


def _homologacion(
    validacion: ValidacionProducto, x: int, y: int, ruta_java: str | None
) -> Nodo:
    """`tFileInputExcel` con la columna de homologación.

    El archivo lo elige el padre, producto a producto.
    """
    return nodo_desde_plantilla(
        "tFileInputExcel",
        "tFileInputExcel_1",
        x,
        y,
        {
            "FILENAME": "context.ruta_insumos + context.arch_hom_tipo_doc",
            # Vacío o "***" hacen que Studio no compile; el archivo no tiene clave.
            "PASSWORD": '"sgm_ref"',
        },
        {"SHEETLIST": (("SHEETNAME", "context.hoja_excel"), ("USE_REGEX", "false"))},
        [Columna(validacion.columna_lookup)],
        ruta_java,
    )


def job_producto(
    arq: Arquitectura,
    columnas: tuple[str, ...],
    variables_periodo: tuple[str, ...] = (),
    pendiente: str = "",
    delimitador: str = ";",
    ruta_java: str | None = None,
    validacion: ValidacionProducto | None = None,
) -> Job:
    """Lee `context.ruta_origen`, totaliza el origen y, si hay validación,
    separa los válidos de los rechazos.
    """
    cols = [Columna(c) for c in columnas]
    parametros = ["producto", "ruta_origen", "sufijo", *variables_periodo]
    if validacion is not None:
        parametros += ["arch_hom_tipo_doc", "ruta_insumos", "ruta_resultados", "hoja_excel"]
    mensaje = f"{arq.producto}: lee el archivo de origen del producto. Pendiente: {pendiente}"
    lineas = [f"System.out.println({java(mensaje)});"]
    lineas += [f'System.out.println("  {p} = " + context.{p});' for p in parametros]
    con_saldo = arq.columna_saldo in columnas
    llave = cols[0]
    saldo = Columna("saldo", "id_BigDecimal")
    salida_map = [llave, saldo] if con_saldo else [llave]
    expresiones = {llave.nombre: f"row1.{llave.nombre}"}
    if con_saldo:
        expresiones["saldo"] = _a_decimal(arq.columna_saldo)
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
        nodo_desde_plantilla(
            "tReplicate", "tReplicate_1", 240, 120, columnas=cols, ruta_java=ruta_java
        ),
        tmap("tMap_1", [EntradaMap("row1", cols)], [SalidaMap("out1", salida_map, expresiones)],
             480, 60, ruta_java),
        _totales(
            "tAggregateRow_1",
            totales_origen,
            _operaciones(con_saldo, llave.nombre, "registros_origen", "suma_saldo_origen"),
            720,
            60,
            ruta_java,
        ),
        log_row("tLogRow_1", totales_origen, 960, 60, ruta_java or ""),
    ]
    conexiones = [
        al_terminar_subjob("tJava_1", "tFileInputDelimited_1"),
        Conexion("tFileInputDelimited_1", "tReplicate_1", "row1"),
        Conexion("tReplicate_1", "tMap_1", "row1"),
        Conexion("tMap_1", "tAggregateRow_1", "out1"),
        Conexion("tAggregateRow_1", "tLogRow_1", "row2"),
    ]
    if validacion is not None:
        motivo = Columna(MOTIVO)
        valido = [llave, *([saldo] if con_saldo else [])]
        expresiones_validos = {llave.nombre: f"copy2.{llave.nombre}"}
        if con_saldo:
            expresiones_validos["saldo"] = _a_decimal(arq.columna_saldo, "copy2")
        nodos += [
            _homologacion(validacion, 240, 360, ruta_java),
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
            _totales(
                "tAggregateRow_2",
                [Columna("registros_validos", "id_Long")]
                + ([Columna("suma_saldo_valido", "id_BigDecimal")] if con_saldo else []),
                _operaciones(con_saldo, llave.nombre, "registros_validos", "suma_saldo_valido"),
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
    valores = {"hoja_excel": HOJA_POR_DEFECTO}
    contextos = {
        "Default": [ParametroContexto(p, valor=valores.get(p, "")) for p in parametros]
    }
    return Job(arq.producto, nodos=nodos, conexiones=conexiones, contextos=contextos)


__all__ = ["HOJA_POR_DEFECTO", "job_producto"]
