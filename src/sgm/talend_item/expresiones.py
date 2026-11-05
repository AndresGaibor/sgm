"""Expresiones Java del `tMap` que aguantan columnas nulas.

En un `LEFT JOIN` del `tMap`, las columnas del lookup quedan a `null` cuando la fila principal no
tiene pareja. `row2.tipo.equals("CC")` lanza `NullPointerException` en ese caso; poner el literal a
la izquierda no. El hito 81 comprobó el filtro con texto no nulo y dejó este riesgo anotado como
bloqueo de R1-04 a R1-09; aquí queda la forma que deben usar esas validaciones.
"""

from __future__ import annotations

from sgm.talend_item.jobs_diseno import java


def null_safe_equals(expression: str, value: str) -> str:
    """Comparación de texto que devuelve `false` si `expression` es `null`.

    El literal va a la izquierda para que `equals` se ejecute sobre un objeto que nunca es nulo.
    Se usa tanto en `expressionFilter` de una salida como en expresiones de columna.
    """
    if not expression.strip():
        raise ValueError("La expresión comparada no puede estar vacía")
    return f"{java(value)}.equals({expression})"


__all__ = ["null_safe_equals"]
