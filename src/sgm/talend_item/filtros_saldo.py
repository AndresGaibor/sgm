"""R1-07: el `FIN_SALDO_CTA < 0` del caso v05 como `expressionFilter` del `tMap` de saldo.

El `tMap` recibe texto normalizado por R1-02: `FIN_SALDO_CTA` sale de
`as_text(input_left_wd(row1.FIN_SALDO_CTA, 20, 0))`, así que es `""` cuando el `input()` de SAS da
faltante y un decimal con signo en los demás casos.

Decisiones que sostienen este módulo:

* **Faltante cuenta como menor que cero.** En SAS un valor faltante es menor que cualquier número
  (`tests/corpus/semantica/vectores.yaml`, `cmp-missing-01`), así que `FIN_SALDO_CTA < 0` es
  verdadero con faltante y la fila entra en `INCONS_SALDO_NEG_*`. `faltante` cortocircuita antes
  de `Double.parseDouble`.
* **`-0.00` no es negativo.** `input_left_wd` lo convierte en `BigDecimal` cero, y `0 < 0` es
  falso, igual que en SAS.
* **Sin cascada de codex en el rechazo.** El SAS toma `INCONS_SALDO_NEG_*` de la sábana entera.
  Una fila con codex inválido y saldo negativo sale en las dos tablas. La cascada solo entra en
  `SABANA_VALIDA_*`, que excluye las filas que ya pasaron por la cuenta (`cta_valido`).
* La `SABANA_VALIDA_*` del SAS excluye por **llave** (`NOT IN`). Aquí se excluye por **fila**; la
  equivalencia exige que la llave sea única, y esa salvedad se publica en `reglas_saldo`.
"""

from __future__ import annotations

from sgm.proceso.reglas_cuenta_real import ReglasCuentaReal
from sgm.proceso.reglas_saldo import INCONSISTENCIA, ReglaSaldo
from sgm.talend_item.filtros_cuenta import faltante
from sgm.talend_item.filtros_cuenta_real import filtros as filtros_cuenta
from sgm.talend_item.modelo import Columna
from sgm.talend_item.normalizacion import literal_java
from sgm.talend_item.tmap import SalidaMap

ENTRADA = "saldo_fuente"
# Nombres de las conexiones de salida. Se distinguen de `cta_*` (R1-06) y de `valido` (R1-04).
SALIDAS = {"neg": "saldo_neg", "valida": "saldo_valida"}


def negativo(regla: ReglaSaldo, fila: str = ENTRADA) -> str:
    """`FIN_SALDO_CTA < umbral`, con el faltante de SAS contado como verdadero."""
    expr = f"{fila}.{regla.columna}"
    return (
        f"({faltante(regla.columna, fila)} "
        f"|| java.lang.Double.parseDouble({expr}) < {regla.umbral})"
    )


def valido(regla: ReglaSaldo, cuenta: ReglasCuentaReal, fila: str = ENTRADA) -> str:
    """Sábana válida de R1-07: pasa la cuenta (R1-06) y no es saldo negativo."""
    return f"({filtros_cuenta(cuenta, fila)['valido']} && !{negativo(regla, fila)})"


def salidas(
    regla: ReglaSaldo, cuenta: ReglasCuentaReal, fila: str = ENTRADA
) -> list[SalidaMap]:
    """Dos salidas: el rechazo de saldo con su `INCONSISTENCIA`, y la sábana válida."""
    if not regla.proyeccion_neg or not regla.proyeccion_valida:
        raise ValueError("El SAS no proyecta columnas para los flujos de saldo negativo")
    motivo = literal_java(regla.motivo)
    expresiones_neg = {c: f"{fila}.{c}" for c in regla.proyeccion_neg}
    expresiones_neg[INCONSISTENCIA] = motivo
    neg = SalidaMap(
        SALIDAS["neg"],
        [Columna(c) for c in (*regla.proyeccion_neg, INCONSISTENCIA)],
        expresiones_neg,
        filtro=negativo(regla, fila),
    )
    expresiones_valida = {c: f"{fila}.{c}" for c in regla.proyeccion_valida}
    valida = SalidaMap(
        SALIDAS["valida"],
        [Columna(c) for c in regla.proyeccion_valida],
        expresiones_valida,
        filtro=valido(regla, cuenta, fila),
    )
    return [neg, valida]


__all__ = ["ENTRADA", "SALIDAS", "negativo", "salidas", "valido"]
