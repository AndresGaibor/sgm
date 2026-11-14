"""Nodo de unión del plan: `union` a `tUnite`.

Un `SET a b` del DATA step y un `UNION ALL` de `PROC SQL` apilan las filas de varias entradas.
`tUnite` hace lo mismo, pero exige que todas las entradas traigan **las mismas columnas en el mismo
orden**; SAS, en cambio, junta por nombre y rellena con faltante lo que una entrada no tiene.

Lo que no se puede demostrar queda pendiente con su motivo y no se escribe:

* entradas con columnas distintas: habría que rellenar con faltante y alinear antes de unir;
* `UNION` sin `ALL`: quita los duplicados, y eso es un `tUniqRow` detrás que todavía no se arma.
"""

from __future__ import annotations

from sgm.ir.models import Operator
from sgm.migrar.esquemas import PendienteMigracion
from sgm.talend_item.desde_plan_orden import ResultadoOrden
from sgm.talend_item.modelo import Columna
from sgm.talend_item.plantillas import nodo_desde_plantilla

UNION_ESQUEMAS = "P-UNION-ESQUEMAS-DISTINTOS"
UNION_SIN_TODO = "P-UNION-SIN-ALL"
UNION_SIN_ESQUEMA = "P-UNION-SIN-ESQUEMA"
APPEND_COLUMNAS_DISTINTAS = "P-APPEND-COLUMNAS-DISTINTAS"
APPEND_ATRIBUTOS_DISTINTOS = "P-APPEND-ATRIBUTOS-DISTINTOS"


def nodo_union(
    op: Operator,
    entradas: list[list[Columna]],
    unico: str,
    x: int,
    linea: int | None,
    ruta_java: str | None = None,
) -> ResultadoOrden:
    """`tUnite` si todas las entradas traen las mismas columnas, en el mismo orden."""
    if len(entradas) < 2 or not all(entradas):
        motivo = "una entrada de la unión no tiene columnas demostradas: no se escribe"
        return ResultadoOrden(pendientes=[PendienteMigracion(UNION_SIN_ESQUEMA, motivo, linea)])
    if not op.params.get("all", True):
        motivo = "UNION sin ALL quita duplicados y necesita un tUniqRow detrás: no se escribe"
        return ResultadoOrden(pendientes=[PendienteMigracion(UNION_SIN_TODO, motivo, linea)])
    if (op.origin or "").casefold() == "proc_append" and len(entradas) == 2:
        base = {columna.nombre.lower(): columna for columna in entradas[0]}
        fuente = entradas[1]
        adicionales = [
            columna.nombre for columna in fuente if columna.nombre.lower() not in base
        ]
        if adicionales:
            motivo = (
                f"DATA contiene columnas que BASE no tiene ({', '.join(adicionales)}); "
                "SAS requiere FORCE para esa forma y FORCE no está soportado "
                "(proc.pdf, p. 640)"
            )
            return ResultadoOrden(
                pendientes=[PendienteMigracion(APPEND_COLUMNAS_DISTINTAS, motivo, linea)]
            )
        for columna in fuente:
            destino = base[columna.nombre.lower()]
            tipo_distinto = columna.tipo != destino.tipo
            longitud_mayor = (
                destino.longitud >= 0
                and columna.longitud > destino.longitud
            )
            if tipo_distinto or longitud_mayor:
                motivo = (
                    f"DATA tiene atributos incompatibles para {columna.nombre}; SAS requiere "
                    "FORCE cuando el tipo difiere o la variable es más larga "
                    "(proc.pdf, p. 640)"
                )
                return ResultadoOrden(
                    pendientes=[PendienteMigracion(APPEND_ATRIBUTOS_DISTINTOS, motivo, linea)]
                )
    primera = [c.nombre.lower() for c in entradas[0]]
    for otra in entradas[1:]:
        if [c.nombre.lower() for c in otra] != primera:
            motivo = (
                f"las entradas no traen las mismas columnas ({', '.join(primera)} contra "
                f"{', '.join(c.nombre for c in otra)}): SAS las junta por nombre y tUnite no"
            )
            return ResultadoOrden(pendientes=[PendienteMigracion(UNION_ESQUEMAS, motivo, linea)])
    nodo = nodo_desde_plantilla(
        "tUnite", unico, x, 0, columnas=list(entradas[0]), ruta_java=ruta_java
    )
    return ResultadoOrden(nodo=nodo)


__all__ = ["nodo_union"]
