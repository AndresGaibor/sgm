"""R1-06 (parte 2): los `NOT BETWEEN ... AND RELACION = 1000` del SAS real a `expressionFilter`.

El `tMap` recibe **texto**. En el Job emitido `RELACION` y `TIPO_CTA` vienen tal cual del CSV, y
`GMF` sale de `as_text(input_left_wd(row1.GMF, 3, 0))`. Por eso:

* El control se compara con el **literal a la izquierda** (`"1000".equals(cuenta.RELACION)`,
  R1-01), sin parsear una columna que puede ser nula.
* El rango se traduce con `filtros_cuenta.fuera_de_rango`, que cortocircuita el faltante de SAS
  (nulo, vacío o texto no numérico) antes de `Double.parseDouble`: un faltante cuenta como menor
  que cualquier número y `NOT BETWEEN 1 AND 10` ya lo incluye.
* La **cascada** del SAS se respeta: el codex solo se evalúa en las filas que no rechazó el tipo de
  cuenta, porque su tabla de entrada es `SABANA_TIPO_CTA_VALIDO_*`. Las filas con otra `RELACION`
  quedan exentas de ambas reglas.

Los motivos no son literales escritos aquí: salen del paso `DATA` que leyó `reglas_cuenta_real`.
`INCONS_CUENTA_*` es la consolidación de los dos `INCONS_PAQ_*` con una `INCONSISTENCIA` ternaria;
el tipo de cuenta manda porque su rechazo ocurre primero en el SAS.
"""

from __future__ import annotations

from sgm.proceso.reglas import ReglaRango
from sgm.proceso.reglas_cuenta_real import INCONSISTENCIA, MODOS, ReglasCuentaReal
from sgm.talend_item.expresiones import null_safe_equals
from sgm.talend_item.filtros_cuenta import fuera_de_rango
from sgm.talend_item.modelo import Columna
from sgm.talend_item.normalizacion import literal_java
from sgm.talend_item.tmap import SalidaMap

ENTRADA = "cuenta"
# Nombres de las conexiones de salida. Se prefijan a propósito: el mismo Job ya tiene una salida
# `valido` (R1-04) y la entrada de este `tMap` se llama `cuenta`. Dos conexiones con el mismo
# `UNIQUE_NAME` en un `.item` son ambiguas para Studio, así que aquí no se repite ninguno.
SALIDAS = {
    "tipo_cta": "cta_tipo_cta",
    "codex": "cta_codex",
    "valido": "cta_valido",
    "cuenta": "cta_incons",
}


def control(reglas: ReglasCuentaReal, fila: str = ENTRADA) -> str:
    """`RELACION = 1000`, con el literal a la izquierda de `equals`."""
    columna, valor = reglas.control
    return null_safe_equals(f"{fila}.{columna}", valor)


def fuera(regla: ReglaRango, fila: str = ENTRADA) -> str:
    """`NOT BETWEEN desde AND hasta`, con el faltante de SAS contado como fuera del rango."""
    if regla.permite:
        raise ValueError(f"La regla de {regla.columna} es `BETWEEN`, no un rechazo: {regla}")
    if regla.control is None:
        raise ValueError(f"La regla de {regla.columna} no trae el control del SAS")
    return fuera_de_rango(regla.columna, regla.desde, regla.hasta, fila)


def rechazo_tipo_cta(reglas: ReglasCuentaReal, fila: str = ENTRADA) -> str:
    """Primera regla: fuera de 1..5 **y** con la relación que la dispara."""
    return f"({control(reglas, fila)} && {fuera(reglas.tipo_cta, fila)})"


def rechazo_codex(reglas: ReglasCuentaReal, fila: str = ENTRADA) -> str:
    """Segunda regla: solo sobre las filas que ya pasaron la primera."""
    return (
        f"(!{rechazo_tipo_cta(reglas, fila)} && {control(reglas, fila)} "
        f"&& {fuera(reglas.codex, fila)})"
    )


def inconsistencia(reglas: ReglasCuentaReal, fila: str = ENTRADA) -> str:
    """Motivo del `OUTER UNION CORR`: primero manda el tipo de cuenta, después el codex."""
    motivos = reglas.motivos
    return (
        f"({rechazo_tipo_cta(reglas, fila)} ? {literal_java(motivos['tipo_cta'])} "
        f": {literal_java(motivos['codex'])})"
    )


def filtros(reglas: ReglasCuentaReal, fila: str = ENTRADA) -> dict[str, str]:
    """Los cuatro `expressionFilter`; `valido` es el complemento y `cuenta` la unión."""
    a = rechazo_tipo_cta(reglas, fila)
    b = rechazo_codex(reglas, fila)
    return {
        "tipo_cta": a,
        "codex": b,
        "valido": f"!({a} || {b})",
        "cuenta": f"({a} || {b})",
    }


def salidas(reglas: ReglasCuentaReal, fila: str = ENTRADA) -> list[SalidaMap]:
    """Cuatro salidas: dos rechazos, los válidos y la consolidación con `INCONSISTENCIA`."""
    if not reglas.columnas:
        raise ValueError("El SAS no proyecta columnas para los flujos de cuenta")
    condiciones = filtros(reglas, fila)
    resultado: list[SalidaMap] = []
    for modo in MODOS:
        columnas = (*reglas.columnas, INCONSISTENCIA) if modo == "cuenta" else reglas.columnas
        expresiones = {c: f"{fila}.{c}" for c in reglas.columnas}
        if modo == "cuenta":
            expresiones[INCONSISTENCIA] = inconsistencia(reglas, fila)
        resultado.append(
            SalidaMap(
                SALIDAS[modo],
                [Columna(c) for c in columnas],
                expresiones,
                filtro=condiciones[modo],
            )
        )
    return resultado


__all__ = [
    "ENTRADA",
    "SALIDAS",
    "control",
    "filtros",
    "fuera",
    "inconsistencia",
    "rechazo_codex",
    "rechazo_tipo_cta",
    "salidas",
]
