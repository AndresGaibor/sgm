"""R1-06 (parte 2): la cuarta rama del `tReplicate_1` del `job_producto` **emitido**.

El hito 88 ejecutó la forma de `v04` en un Job aislado. Aquí se cuelga del Job real la forma del
`client_large.sas`, que es la que el plan dejó pendiente::

    tReplicate_1 --cuenta--> tMap_cuenta --tipo_cta/codex/valido/cuenta--> 4 tFileOutputDelimited

Las reglas, los motivos, el control, la proyección de 19 columnas y los nombres de las tres tablas
del SAS salen de `proceso.reglas_cuenta_real`. El cuarto CSV (`INCONS_CUENTA_*`) es una
consolidación derivada de los `INCONS_PAQ_*` y su `OUTER UNION CORR`; su columna extra
`INCONSISTENCIA` está anclada a esas tablas, no inventada aquí.

Los filtros comparan `GMF` como texto **normalizado** por R1-02 (`as_text(input_left_wd(...,3.))`).
Por eso este módulo exige que la columna del codex esté en `numericas`: sin esa conversión el
faltante de SAS no se puede traducir y no se emite un filtro equivocado (igual que R1-04).
"""

from __future__ import annotations

from sgm.proceso.reglas_cuenta_real import MODOS, ReglasCuentaReal
from sgm.talend_item.filtros_cuenta_real import ENTRADA
from sgm.talend_item.filtros_cuenta_real import salidas as salidas_cuenta
from sgm.talend_item.jobs_diseno import java
from sgm.talend_item.modelo import Columna, Conexion, Nodo
from sgm.talend_item.plantillas import nodo_desde_plantilla
from sgm.talend_item.tmap import EntradaMap, tmap

TMAP = "tMap_cuenta"
SALIDA = "tFileOutputDelimited_cuenta_{n}"


def _validar(
    reglas: ReglasCuentaReal, cols: list[Columna], informats: dict[str, tuple[int, int]]
) -> None:
    """No se emite un filtro si falta algo que el SAS o la normalización no demuestran."""
    nombres = {c.nombre for c in cols}
    if not reglas.columnas:
        raise ValueError("Sin proyección del SAS no hay flujos de cuenta que emitir")
    fuera = sorted(set(reglas.columnas) - nombres)
    if fuera:
        raise ValueError(f"Los flujos de cuenta proyectan columnas que no se leen: {fuera}")
    columna_control, _ = reglas.control
    for columna in (columna_control, reglas.tipo_cta.columna):
        if columna not in nombres:
            raise ValueError(f"El filtro de cuenta exige la columna '{columna}' del CSV de origen")
    if reglas.codex.columna not in informats:
        raise ValueError(
            f"El filtro de '{reglas.codex.columna}' exige la normalización de R1-02; "
            f"no está en numericas: {sorted(informats)}"
        )
    if sorted(reglas.tablas) != sorted(MODOS):
        raise ValueError(f"Las tablas del SAS deben ser {MODOS}: {reglas.tablas}")


def componentes(
    reglas: ReglasCuentaReal,
    cols: list[Columna],
    informats: dict[str, tuple[int, int]],
    ruta_java: str | None = None,
) -> tuple[list[Nodo], list[Conexion]]:
    """El `tMap` de cuenta, sus cuatro CSV y sus conexiones.

    La conexión de entrada sale de `tReplicate_1`; el llamador la añade a las ramas existentes.
    Cada CSV lleva cabecera (para compararlo por nombre de columna) y `context.sufijo`, igual que
    los flujos de R1-04.
    """
    _validar(reglas, cols, informats)
    flujos = salidas_cuenta(reglas, ENTRADA)
    nodos: list[Nodo] = [tmap(TMAP, [EntradaMap(ENTRADA, cols)], flujos, 240, 840, ruta_java)]
    conexiones: list[Conexion] = [Conexion("tReplicate_1", TMAP, ENTRADA)]
    for n, (modo, salida) in enumerate(zip(MODOS, flujos, strict=True), start=1):
        unico = SALIDA.format(n=n)
        nombre = (
            f"context.ruta_resultados + {java(reglas.tablas[modo] + '_')} "
            f"+ context.sufijo + {java('.csv')}"
        )
        nodos.append(
            nodo_desde_plantilla(
                "tFileOutputDelimited",
                unico,
                720,
                720 + (n - 1) * 120,
                {
                    "FILENAME": nombre,
                    "FIELDSEPARATOR": '","',
                    "INCLUDEHEADER": "true",
                    "APPEND": "false",
                },
                columnas=list(salida.columnas),
                ruta_java=ruta_java,
            )
        )
        conexiones.append(Conexion(TMAP, unico, salida.nombre))
    return nodos, conexiones


__all__ = ["ENTRADA", "SALIDA", "TMAP", "componentes"]
