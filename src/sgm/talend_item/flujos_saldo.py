"""R1-07: la rama de saldo negativo del `job_producto` emitido.

Cuelga una quinta rama de `tReplicate_1`, paralela a las de R1-04 y R1-06::

    tReplicate_1 --saldo_fuente--> tMap_saldo --saldo_neg/saldo_valida--> 2 tFileOutputDelimited

La regla y las proyecciones salen de `proceso.reglas_saldo`, leídas del caso v05. Los dos CSV
llevan cabecera (para compararlos por nombre de columna) y `context.sufijo`, igual que las demás
ramas. Sus nombres de archivo son las tablas del SAS (`INCONS_SALDO_NEG_*`, `SABANA_VALIDA_*`),
y las conexiones usan nombres propios (`saldo_*`) para no repetir ninguna de R1-04 o R1-06.

Esta rama necesita la cascada de R1-06: `SABANA_VALIDA_*` se calcula sobre la cuenta válida. Sin
esa pareja no se emite, porque no habría con qué excluir el codex.
"""

from __future__ import annotations

from sgm.proceso.reglas_cuenta_real import ReglasCuentaReal
from sgm.proceso.reglas_saldo import ReglaSaldo
from sgm.talend_item.filtros_saldo import ENTRADA, SALIDAS, salidas
from sgm.talend_item.jobs_diseno import java
from sgm.talend_item.modelo import Columna, Conexion, Nodo
from sgm.talend_item.plantillas import nodo_desde_plantilla
from sgm.talend_item.tmap import EntradaMap, tmap

TMAP = "tMap_saldo"
SALIDA = "tFileOutputDelimited_saldo_{n}"
ORDEN = ("neg", "valida")


def _validar(
    regla: ReglaSaldo,
    cuenta: ReglasCuentaReal | None,
    cols: list[Columna],
    informats: dict[str, tuple[int, int]],
) -> None:
    """No se emite un filtro si falta algo que el SAS o la normalización no demuestran."""
    if cuenta is None:
        raise ValueError("Sin la cascada de codex de R1-06 no hay SABANA_VALIDA_* que calcular")
    nombres = {c.nombre for c in cols}
    proyectadas = set(regla.proyeccion_neg) | set(regla.proyeccion_valida)
    fuera = sorted(proyectadas - nombres)
    if fuera:
        raise ValueError(f"Los flujos de saldo proyectan columnas que no se leen: {fuera}")
    if regla.columna not in informats:
        raise ValueError(
            f"El filtro de {regla.columna} exige la normalización de R1-02; "
            f"no está en numericas: {sorted(informats)}"
        )
    if sorted(regla.tablas) != sorted(ORDEN):
        raise ValueError(f"Las tablas del SAS deben ser {ORDEN}: {regla.tablas}")


def componentes(
    regla: ReglaSaldo,
    cuenta: ReglasCuentaReal | None,
    cols: list[Columna],
    informats: dict[str, tuple[int, int]],
    ruta_java: str | None = None,
) -> tuple[list[Nodo], list[Conexion]]:
    """El `tMap` de saldo, sus dos CSV y sus conexiones. Ver el docstring del módulo."""
    _validar(regla, cuenta, cols, informats)
    assert cuenta is not None
    flujos = salidas(regla, cuenta, ENTRADA)
    nodos: list[Nodo] = [
        tmap(TMAP, [EntradaMap(ENTRADA, cols)], flujos, 240, 1200, ruta_java)
    ]
    conexiones: list[Conexion] = [Conexion("tReplicate_1", TMAP, ENTRADA)]
    for n, (modo, salida) in enumerate(zip(ORDEN, flujos, strict=True), start=1):
        unico = SALIDA.format(n=n)
        nombre = (
            f"context.ruta_resultados + {java(regla.tablas[modo] + '_')} "
            f"+ context.sufijo + {java('.csv')}"
        )
        nodos.append(
            nodo_desde_plantilla(
                "tFileOutputDelimited",
                unico,
                720,
                1200 + (n - 1) * 120,
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
        conexiones.append(Conexion(TMAP, unico, SALIDAS[modo]))
    return nodos, conexiones


__all__ = ["ENTRADA", "SALIDA", "TMAP", "componentes"]
