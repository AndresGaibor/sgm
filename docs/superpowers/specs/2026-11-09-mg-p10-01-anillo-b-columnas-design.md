# MG-P10-01: comparación de columnas del anillo B

## Intención

El anillo B debe detectar cuando el intérprete produce una columna adicional o deja fuera una
columna que declara `esperado/`. Hoy `_esperado` toma el encabezado esperado para construir la tabla
calculada; por eso una columna adicional en las filas del intérprete no llega al comparador.

## Objetivo y límites

- Comparar, para cada fila disponible, el conjunto de columnas de salida con el encabezado del CSV
  esperado, sin distinguir mayúsculas.
- Mantener la comparación actual de valores, tolerancia y orden de filas.
- No cambiar el comparador común del corpus ni inferir un esquema cuando el intérprete devuelve cero
  filas: el resultado actual no conserva metadatos de columnas para una salida vacía.

## Enfoques considerados

- Validar las claves dentro del arnés B antes de construir la tabla calculada. Es el cambio elegido:
  corrige la brecha identificada y limita el efecto a la verificación del intérprete.
- Cambiar `comparar_con_guardado` o el comparador común del corpus para recibir nombres reales de
  columnas. Se descarta para este hito porque afectaría el oráculo SQL y la comparación de Studio,
  aunque el defecto observado solo está en cómo el anillo B construye su tabla.

## Restricciones y aceptación

El esperado guardado sigue siendo independiente; no se regeneran CSV ni se alteran `xfail`. Se
agregan pruebas de regresión que fallen antes del arreglo para columnas extra en filas posteriores y
faltantes con valor esperado vacío. La prueba de columna extra también comprueba que los nombres que
solo difieren en mayúsculas se traten como iguales; otra prueba cubre salidas vacías. El cierre del
hito requiere `uv run python -m pytest -q` y `uv run ruff check .` en verde.
