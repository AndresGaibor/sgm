"""`LAG` y `DIF` del DATA step como `tJavaRow` (B-13; lefunctionsref, pp. 1163-1164 y 663).

Solo se emite la forma que el generador `java_lag` sabe verificar: `x = LAGn(col);` o
`DIFn(col);`, con `col` numérica del paso anterior, y con `IF col OP número THEN` como condición
opcional. Cualquier otra forma devuelve None y el operador sigue como hueco `P-LAG-SIN-EMISOR`
(el Job no se escribe).
"""

from __future__ import annotations

import re

from sgm.ir.models import Operator
from sgm.java_identificadores import is_java_identifier
from sgm.talend_item.desde_plan_orden import _NUMERICOS, ResultadoOrden
from sgm.talend_item.java_lag import codigo_lag
from sgm.talend_item.modelo import Columna
from sgm.talend_item.plantillas import nodo_desde_plantilla

_FORMA = re.compile(r"(?i)^(lag|dif)(\d*)\s*\(\s*([A-Za-z_]\w*)\s*\)$")
_CONDICION = re.compile(r"(?i)^([A-Za-z_]\w*)\s*(>=|<=|>|<|=)\s*(-?\d+(?:\.\d+)?)$")
_OPERADOR_JAVA = {">=": ">=", "<=": "<=", ">": ">", "<": "<", "=": "=="}


def _columna(columnas: list[Columna], nombre: str) -> Columna | None:
    return next((c for c in columnas if c.nombre.lower() == nombre.lower()), None)


def _condicion_java(condicion: str, columnas: list[Columna]) -> str | None:
    """`col OP número` como Java sobre `input_row`; faltante es falso (lrcon, p. 500)."""
    if not condicion:
        return None
    m = _CONDICION.fullmatch(condicion.strip())
    if m is None:
        return None
    col = _columna(columnas, m.group(1))
    if col is None or col.tipo not in _NUMERICOS:
        return None
    op = _OPERADOR_JAVA[m.group(2)]
    return f"input_row.{col.nombre} != null && input_row.{col.nombre} {op} {m.group(3)}"


def nodo_lag(
    op: Operator,
    columnas: list[Columna],
    unico: str,
    x: int,
    linea: int | None,
    ruta_java: str | None,
) -> ResultadoOrden | None:
    """`tJavaRow` con el `LAG`/`DIF` de `op`, o None si la forma no es la que se sabe emitir."""
    forma = _FORMA.fullmatch(str(op.params.get("expression") or "").strip())
    destino = str(op.params.get("target") or "")
    if forma is None or not is_java_identifier(destino) or _columna(columnas, destino):
        return None
    funcion, n_texto, nombre = forma.group(1).lower(), forma.group(2), forma.group(3)
    origen = _columna(columnas, nombre)
    if origen is None or origen.tipo not in _NUMERICOS:
        return None
    condicion = op.params.get("condition")
    condicion_java = _condicion_java(str(condicion), columnas) if condicion else None
    if condicion and condicion_java is None:
        return None
    salida = [*columnas, Columna(destino, "id_Double")]
    # `doubleValue()` sirve para cualquier columna numérica (entero o decimal), no solo `id_Double`.
    valor = f"(input_row.{origen.nombre} == null ? null : input_row.{origen.nombre}.doubleValue())"
    codigo = codigo_lag(
        unico,
        destino,
        valor,
        int(n_texto or 1),
        [c.nombre for c in columnas],
        condicion=condicion_java,
        dif=funcion == "dif",
    )
    nodo = nodo_desde_plantilla(
        "tJavaRow", unico, x, 0, valores={"CODE": codigo}, columnas=salida, ruta_java=ruta_java
    )
    return ResultadoOrden(nodo=nodo, columnas=salida)
