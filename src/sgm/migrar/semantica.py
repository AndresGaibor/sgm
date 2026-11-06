"""Semántica de SAS para comparar valores: faltantes, blancos finales y números.

Un intérprete que compare con las reglas de Python da resultados distintos de SAS en los tres casos
que importan aquí, y los tres están documentados en `docs/referencia/sas/lrcon.txt` (comparaciones y
valores faltantes):

* **Un faltante es menor que cualquier valor no faltante**, y dos faltantes son iguales entre
  sí. Por eso `saldo < 500` es verdadero cuando `saldo` falta, que es justo lo contrario de lo que
  hace Java con un `null`.
* **Los blancos finales no cuentan al comparar texto**: `'AB'` y `'AB   '` son iguales.
* **Un valor en blanco es faltante**: una cadena vacía o de blancos es un faltante de texto.

Los valores viajan como texto porque el corpus los lee de CSV, y la decisión de comparar como número
o como texto se toma valor por valor, no por columna: si los dos lados se leen como números, se
comparan como números. Es la misma regla que usa el comparador del corpus (`studio_filas.iguales`),
así que el intérprete y la comparación no se contradicen.
"""

from __future__ import annotations

import re

_NUMERO = re.compile(r"[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?$")


def es_faltante(valor: object) -> bool:
    """Un faltante es `None`, la cadena vacía o una cadena de blancos."""
    if valor is None:
        return True
    if isinstance(valor, str):
        return not valor.strip()
    return False


def como_numero(valor: object) -> float | None:
    """El valor como número, o `None` si falta o no se puede leer como número."""
    if isinstance(valor, bool):
        return float(valor)
    if isinstance(valor, (int, float)):
        return float(valor)
    if isinstance(valor, str) and _NUMERO.match(valor.strip()):
        return float(valor.strip())
    return None


def como_texto(valor: object) -> str:
    """El valor como texto, sin blancos finales, que es como lo compara SAS."""
    if valor is None:
        return ""
    if isinstance(valor, bool):
        return "1" if valor else "0"
    if isinstance(valor, float):
        return str(int(valor)) if valor.is_integer() else format(valor, ".12g")
    return str(valor).rstrip()


def comparar(izquierda: object, derecha: object) -> int:
    """-1, 0 o 1 con la regla de SAS: el faltante va antes que todo, y dos faltantes son iguales."""
    falta_izquierda, falta_derecha = es_faltante(izquierda), es_faltante(derecha)
    if falta_izquierda and falta_derecha:
        return 0
    if falta_izquierda:
        return -1
    if falta_derecha:
        return 1
    numero_izquierda, numero_derecha = como_numero(izquierda), como_numero(derecha)
    if numero_izquierda is not None and numero_derecha is not None:
        return (numero_izquierda > numero_derecha) - (numero_izquierda < numero_derecha)
    texto_izquierda, texto_derecha = como_texto(izquierda), como_texto(derecha)
    return (texto_izquierda > texto_derecha) - (texto_izquierda < texto_derecha)


def iguales(izquierda: object, derecha: object) -> bool:
    return comparar(izquierda, derecha) == 0


def distintos(izquierda: object, derecha: object) -> bool:
    return comparar(izquierda, derecha) != 0


def menor(izquierda: object, derecha: object) -> bool:
    return comparar(izquierda, derecha) < 0


def menor_igual(izquierda: object, derecha: object) -> bool:
    return comparar(izquierda, derecha) <= 0


def mayor(izquierda: object, derecha: object) -> bool:
    return comparar(izquierda, derecha) > 0


def mayor_igual(izquierda: object, derecha: object) -> bool:
    return comparar(izquierda, derecha) >= 0


def a_texto(valor: object) -> str | None:
    """El valor para la tabla de salida: `None` si falta, número sin ceros de más si es número."""
    if valor is None:
        return None
    if isinstance(valor, bool):
        return "1" if valor else "0"
    if isinstance(valor, float):
        return str(int(valor)) if valor.is_integer() else format(valor, ".12g")
    if isinstance(valor, int):
        return str(valor)
    return valor if isinstance(valor, str) else str(valor)


__all__ = [
    "a_texto",
    "como_numero",
    "como_texto",
    "comparar",
    "distintos",
    "es_faltante",
    "iguales",
    "mayor",
    "mayor_igual",
    "menor",
    "menor_igual",
]
