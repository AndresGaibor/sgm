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
