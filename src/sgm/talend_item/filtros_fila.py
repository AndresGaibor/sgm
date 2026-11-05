"""Reglas de fila de R1-04 traducidas a `expressionFilter` del `tMap` (T13).

El `tMap_normalizacion` de R1-02 entrega `NRO_DOC` como **texto**: `input(left(x), 30.)` produce un
`BigDecimal`, y `as_text` lo convierte con `java.util.Objects.toString(..., "")`. Por eso el
faltante de SAS es `""` y el cero es `"0"`; no se comparan números ni se llama a `.equals` sobre la
columna (R1-01: una columna nula lanzaría `NullPointerException`).

Cada regla se convierte en una salida con su propio filtro. Las tres salidas de `v02` son
disjuntas y cubren la sábana: tit_cot y fa separan el mismo `vacio_o_cero` por `RELACION`, y
`valido` es su negación.
"""

from __future__ import annotations

from sgm.proceso.reglas_fila import ReglaFila
from sgm.talend_item.expresiones import null_safe_equals
from sgm.talend_item.modelo import Columna
from sgm.talend_item.tmap import SalidaMap


def faltante_o_cero(columna: str, fila: str = "row1") -> str:
    """`NRO_DOC = 0 OR NRO_DOC IS MISSING` sobre la columna ya normalizada a texto."""
    expr = f"{fila}.{columna}"
    return f'({expr} == null || "".equals({expr}) || "0".equals({expr}))'


def no_faltante_ni_cero(columna: str, fila: str = "row1") -> str:
    """`NRO_DOC IS NOT MISSING AND NRO_DOC <> 0`."""
    return f"!{faltante_o_cero(columna, fila)}"


def _relacion(regla: ReglaFila, fila: str) -> str:
    igual = null_safe_equals(f"{fila}.{regla.columna_relacion}", regla.valor_relacion)
    return f"!{igual}" if regla.operador_relacion in ("<>", "!=") else igual


def filtro(regla: ReglaFila, fila: str = "row1") -> str:
    """Expresión booleana de Java para el `expressionFilter` de la salida de esa regla."""
    base = (
        faltante_o_cero(regla.columna, fila)
        if regla.vacio_o_cero
        else no_faltante_ni_cero(regla.columna, fila)
    )
    if not regla.columna_relacion:
        return base
    return f"({base} && {_relacion(regla, fila)})"


def salidas_filtro(
    reglas: list[ReglaFila],
    esquemas: dict[str, list[Columna]],
    fila: str = "row1",
) -> list[SalidaMap]:
    """Una salida por regla, con el nombre del modo y las columnas pedidas para ese modo.

    `esquemas` decide la proyección de cada flujo; las expresiones son `fila.<columna>` porque el
    filtro no transforma valores. Un modo sin esquema es un error, no se inventa uno.
    """
    resultado: list[SalidaMap] = []
    for regla in reglas:
        if regla.modo not in esquemas:
            raise ValueError(f"Falta el esquema de la salida '{regla.modo}'")
        columnas = esquemas[regla.modo]
        resultado.append(
            SalidaMap(
                regla.modo,
                columnas,
                {c.nombre: f"{fila}.{c.nombre}" for c in columnas},
                filtro=filtro(regla, fila),
            )
        )
    return resultado


__all__ = ["faltante_o_cero", "filtro", "no_faltante_ni_cero", "salidas_filtro"]
