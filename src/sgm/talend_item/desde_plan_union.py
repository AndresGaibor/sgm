"""Nodo de unión del plan: `union` a `tUnite`.

Un `SET a b` del DATA step y un `UNION ALL` de `PROC SQL` apilan las filas de varias entradas.
`tUnite` exige que todas las entradas traigan las mismas columnas en el mismo orden. SAS, en cambio,
junta por nombre y rellena con faltante lo que una entrada no tiene (lestmtsref, p. 343; lrcon,
p. 579). Por eso cada entrada cuyo esquema no es el de la unión pasa por un `tMap` que lo alinea:
las columnas de la unión, en el orden de la primera aparición, y `null` donde la entrada no trae la
columna. El tipo y la longitud los fija la primera aparición; un tipo distinto para la misma columna
ya se detecta antes, en `esquemas_propagacion` (`P-UNION-TIPO-CONFLICTO`).

Lo que no se puede demostrar queda pendiente con su motivo y no se escribe:

* entradas sin columnas demostradas;
* `UNION` sin `ALL`: quita los duplicados, y eso es un `tUniqRow` detrás que todavía no se arma.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace

from sgm.ir.models import Operator
from sgm.migrar.esquemas import PendienteMigracion
from sgm.talend_item.desde_plan_orden import ResultadoOrden
from sgm.talend_item.modelo import Columna, Nodo
from sgm.talend_item.plantillas import nodo_desde_plantilla
from sgm.talend_item.tmap import EntradaMap, SalidaMap, tmap

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
    nuevo_tmap: Callable[[], str] | None = None,
) -> ResultadoOrden:
    """`tUnite` con sus entradas alineadas por `tMap` si traen columnas distintas."""
    if len(entradas) < 2 or not all(entradas):
        motivo = "una entrada de la unión no tiene columnas demostradas: no se escribe"
        return ResultadoOrden(pendientes=[PendienteMigracion(UNION_SIN_ESQUEMA, motivo, linea)])
    if not op.params.get("all", True):
        motivo = "UNION sin ALL quita duplicados y necesita un tUniqRow detrás: no se escribe"
        return ResultadoOrden(pendientes=[PendienteMigracion(UNION_SIN_TODO, motivo, linea)])
    if str(getattr(op, "origin", "") or "").casefold() == "proc_append" and len(entradas) == 2:
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
    union = _union_de(entradas)
    if nuevo_tmap is None:
        contador = 0

        def nombre_tmap() -> str:
            nonlocal contador
            contador += 1
            return f"tMap_{unico}_{contador}"

        nuevo_tmap = nombre_tmap
    alineados = {
        i: _alinear(entrada, union, nuevo_tmap(), f"{unico}_in{i + 1}", x - 96, 96 * i, ruta_java)
        for i, entrada in enumerate(entradas)
        if _nombres(entrada) != _nombres(union)
    }
    columnas = list(entradas[0] if not alineados else union)
    nodo = nodo_desde_plantilla("tUnite", unico, x, 0, columnas=columnas, ruta_java=ruta_java)
    return ResultadoOrden(nodo=nodo, alineados=alineados, columnas=columnas)


def _nombres(columnas: list[Columna]) -> list[str]:
    return [c.nombre.lower() for c in columnas]


def _union_de(entradas: list[list[Columna]]) -> list[Columna]:
    """Columnas de todas las entradas por nombre, en el orden de la primera aparición. Nulables."""
    union: dict[str, Columna] = {}
    for entrada in entradas:
        for columna in entrada:
            union.setdefault(columna.nombre.lower(), replace(columna, nulable=True))
    return list(union.values())


def _alinear(
    entrada: list[Columna],
    union: list[Columna],
    unico_tmap: str,
    nombre_salida: str,
    x: int,
    y: int,
    ruta_java: str | None,
) -> Nodo:
    """`tMap` que toma la entrada como `row1` y emite el esquema de la unión (`null` si falta)."""
    presentes = {c.nombre.lower(): c.nombre for c in entrada}
    expresiones = {
        c.nombre: f"row1.{presentes[c.nombre.lower()]}" if c.nombre.lower() in presentes else "null"
        for c in union
    }
    return tmap(
        unico_tmap,
        [EntradaMap(conexion="row1", columnas=list(entrada))],
        [SalidaMap(nombre=nombre_salida, columnas=list(union), expresiones=expresiones)],
        x=x,
        y=y,
        ruta_java=ruta_java,
    )


__all__ = ["nodo_union"]
