# MG-P10-01: interpretar agregados PROC SQL

## Intención

El anillo B ya compila el caso `l2_08_case_when_tras_left_join` hasta una operación `aggregate`,
pero el intérprete la rechaza. El objetivo es ejecutar los agregados que el corpus y la guía permiten
demostrar para que el resultado se pueda comparar con el SAS de referencia.

## Alcance

- Admitir `COUNT(*)`, `COUNT(expresión)`, `SUM(expresión)`, `AVG(expresión)`, `MIN(expresión)` y
  `MAX(expresión)` en la operación `aggregate` de la IR.
- Admitir agregados con `GROUP BY` de una o varias columnas simples y agregados globales sin `GROUP BY`.
- La salida del agregado solo contiene las columnas simples seleccionadas del `GROUP BY`, respeta
  sus alias y conserva el orden del `SELECT`; las llaves no seleccionadas siguen agrupando, pero no
  aparecen en la salida.
- Contar todas las filas con `COUNT(*)`, incluidas las que tengan otros campos faltantes; `COUNT(expr)`
  cuenta solo expresiones no faltantes.
- Los agregados numéricos omiten valores faltantes y devuelven faltante cuando no tienen ningún valor
  no faltante. Un `GROUP BY` forma un solo grupo para los faltantes.
- Aplicar agrupación textual solo cuando la clave no sea un texto numérico ambiguo. Si las filas llegan
  como texto numérico sin tipo SAS demostrado, el intérprete informa que no puede ejecutar el grupo;
  no adivina si el campo de origen era numérico o carácter.
- Conservar el orden de primera aparición de grupos para que la ejecución sea determinista; no declarar
  orden SAS en resultados cuyo caso no exige orden.

## Fuera de alcance

- `DISTINCT`, `COUNT(DISTINCT ...)`, agregados distintos de los enumerados, expresiones con varios
  argumentos, `GROUP BY` sin agregados, remezcla de columnas no agrupadas, `SELECT *` con agregados y
  tipos de clave no demostrables. Las columnas no agrupadas o referencias `ORDER BY` no seleccionadas
  que impliquen remezcla quedan pendientes y el intérprete las rechaza.
- No se cambia el emisor Talend ni se conecta una base de datos. El trabajo es del intérprete de
  referencia y reutiliza las expresiones de la IR.

## Enfoques considerados

- Agrupar las filas en Python y evaluar cada expresión por grupo. Elegido: corresponde al rol del anillo
  B, no requiere servicios externos y permite aplicar faltantes de SAS explícitamente.
- Ejecutar SQL generado contra SQLite. Descartado: añade semántica SQL distinta de SAS y requiere una
  capa de traducción de tipos y faltantes que no está en el contrato del intérprete.
- Programar una excepción solo para `COUNT(*)` del caso L2. Descartado: dejaría el intérprete acoplado
  a un programa y no cubriría las funciones que el usuario pidió.

## Evidencia SAS

- `GROUP BY` forma subconjuntos y calcula los agregados por grupo (`sqlproc.pdf`, p. 38).
- `COUNT(*)` incluye todas las filas; `COUNT(columna)` cuenta valores no faltantes (`sqlproc.pdf`,
  p. 82).
- `PROC SQL` agrupa los faltantes en un solo grupo (`sqlproc.pdf`, p. 88).
- `SUM`, `AVG`, `MIN` y `MAX` son agregados documentados; los agregados ignoran faltantes
  (`sqlproc.pdf`, pp. 76 y 83). Las funciones numéricas devuelven faltante cuando todos sus argumentos
  están faltantes (`lefunctionsref.pdf`, pp. 1230, 1234, 1236 y 1580).
- Un agregado sin `GROUP BY` produce una fila resumen (`sqlproc.pdf`, pp. 78-79).
- SAS remezcla cuando el `SELECT` combina agregados con columnas no incluidas en `GROUP BY`, o cuando
  `ORDER BY` usa una columna no seleccionada (`sqlproc.pdf`, p. 79). Como no se implementa esa
  remezcla, esos patrones no se calculan parcialmente.

## Aceptación

- El caso `l2_08_case_when_tras_left_join` calcula sus dos tablas esperadas sin `xfail`, sin modificar
  `esperado/`.
- Pruebas del intérprete cubren cada función, filas faltantes, un grupo con todos sus valores
  agregados faltantes, claves de grupo faltantes, agregación global, proyección/alias/orden de salida
  y patrones que se mantienen explícitamente no soportados.
- La suite completa y Ruff pasan; `MG-P10-01` sigue parcial mientras haya más casos `xfail`.
