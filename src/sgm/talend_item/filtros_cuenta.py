"""R1-06: reglas de lista/rango de `v04` traducidas a `expressionFilter` del `tMap`.

El `tMap` recibe columnas **de texto**. `TIPO_CTA` viene tal cual del CSV; `GMF` sale de
`as_text(input_left_wd(row1.GMF_TXT, 3, 0))`, así que es `""` cuando `input()` da faltante de SAS
(por ejemplo el `XX` plantado) y un número escrito como texto en los demás casos.

De ahí las dos reglas de este módulo:

* La lista se compara con el **literal a la izquierda** (`"1".equals(row1.TIPO_CTA)`), igual que en
  R1-01: una columna nula no lanza `NullPointerException`.
* El **faltante de SAS cuenta como menor que cualquier número**. Por eso `fuera_de_rango` empieza
  con el cortocircuito del faltante y solo después parsea: `GMF NOT BETWEEN 1 AND 10` incluye al
  faltante, y el `CASE` del SAS le da el motivo `GMF NO NUMERICO` en vez de `GMF FUERA DE RANGO`.

Las cuatro salidas son disjuntas salvo `cuenta`, que es la unión de los dos rechazos (el
`OUTER UNION CORR` del SAS) con el motivo elegido por una expresión ternaria, no por un segundo
componente. La comparación fila por fila contra `esperado/` es la que decide si esa traducción es
correcta.
"""

from __future__ import annotations

from sgm.proceso.reglas_cuenta import ReglasCuenta
from sgm.talend_item.expresiones import null_safe_equals
from sgm.talend_item.modelo import Columna
from sgm.talend_item.normalizacion import literal_java, numero_valido
from sgm.talend_item.tmap import SalidaMap

MODOS = ("tipo_cta", "gmf", "valido", "cuenta")


def faltante(columna: str, fila: str = "row1") -> str:
    """Faltante de SAS sobre una columna de texto normalizada: nulo, vacío o no numérico."""
    expr = f"{fila}.{columna}"
    return f'({expr} == null || "".equals({expr}) || !{numero_valido(expr)})'


def en_lista(columna: str, valores: tuple[str, ...], fila: str = "row1") -> str:
    """`TIPO_CTA IN ('1'..'5')`, con el literal a la izquierda de cada `equals`."""
    if not valores:
        raise ValueError("La lista de valores permitidos no puede estar vacía")
    expr = f"{fila}.{columna}"
    uniones = " || ".join(null_safe_equals(expr, valor) for valor in valores)
    return f"({uniones})"


def fuera_de_rango(
    columna: str,
    desde: int,
    hasta: int,
    fila: str = "row1",
) -> str:
    """`GMF IS MISSING OR GMF NOT BETWEEN desde AND hasta`. El faltante sale primero.

    `Double.parseDouble` solo se evalúa si la columna no es faltante (cortocircuito de `||`),
    porque el patrón numérico ya se comprobó. Los límites son enteros del propio SAS.
    """
    if desde > hasta:
        raise ValueError(f"El rango del SAS está invertido: {desde}..{hasta}")
    expr = f"{fila}.{columna}"
    fuera = (
        f"(java.lang.Double.parseDouble({expr}) < {desde} "
        f"|| java.lang.Double.parseDouble({expr}) > {hasta})"
    )
    return f"({faltante(columna, fila)} || {fuera})"


def motivo_gmf(reglas: ReglasCuenta, fila: str = "row1") -> str:
    """El `CASE WHEN GMF IS MISSING THEN ... ELSE ... END AS MOTIVO` del SAS."""
    return (
        f"({faltante(reglas.columna_rango, fila)} "
        f"? {literal_java(reglas.motivos['faltante'])} "
        f": {literal_java(reglas.motivos['rango'])})"
    )


def inconsistencia(reglas: ReglasCuenta, fila: str = "row1") -> str:
    """Motivo del `OUTER UNION CORR`: primero manda el tipo de cuenta, después el GMF."""
    dentro = en_lista(reglas.columna_lista, reglas.valores, fila)
    return (
        f"(!{dentro} ? {literal_java(reglas.motivos['lista'])} "
        f": {motivo_gmf(reglas, fila)})"
    )


def _expresiones(reglas: ReglasCuenta, modo: str, fila: str) -> dict[str, str]:
    columnas = reglas.proyecciones[modo]
    base = {c: f"{fila}.{c}" for c in columnas if c not in ("MOTIVO", "INCONSISTENCIA")}
    if "MOTIVO" in columnas:
        base["MOTIVO"] = motivo_gmf(reglas, fila)
    if "INCONSISTENCIA" in columnas:
        base["INCONSISTENCIA"] = inconsistencia(reglas, fila)
    return base


def salidas(reglas: ReglasCuenta, fila: str = "row1") -> list[SalidaMap]:
    """Las cuatro salidas del `tMap`: dos rechazos, los válidos y la cuenta consolidada."""
    if sorted(reglas.proyecciones) != sorted(MODOS):
        raise ValueError(f"Las proyecciones del SAS deben ser {MODOS}: {reglas.proyecciones}")
    dentro = en_lista(reglas.columna_lista, reglas.valores, fila)
    fuera = fuera_de_rango(reglas.columna_rango, reglas.desde, reglas.hasta, fila)
    filtros = {
        "tipo_cta": f"!{dentro}",
        "gmf": f"({dentro} && {fuera})",
        "valido": f"({dentro} && !{fuera})",
        "cuenta": f"(!{dentro} || {fuera})",
    }
    return [
        SalidaMap(
            modo,
            [Columna(c) for c in reglas.proyecciones[modo]],
            _expresiones(reglas, modo, fila),
            filtro=filtros[modo],
        )
        for modo in MODOS
    ]


__all__ = [
    "MODOS",
    "en_lista",
    "faltante",
    "fuera_de_rango",
    "inconsistencia",
    "motivo_gmf",
    "salidas",
]
