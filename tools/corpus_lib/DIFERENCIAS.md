# Diferencias entre PROC SQL de SAS y SQLite

Este documento acompana a `traduccion_sql.py` (funcion `a_sqlite`) y a `oraculo_sql.py`. Cada
construccion de SAS aparece aqui con lo que hace en SAS, como se trata en el oraculo y el riesgo
que queda. Lo que no esta en la tabla se rechaza con `NoSoportado`, nunca se traduce en silencio.

No hay SAS en este entorno. Todo lo que dice la columna "Supuesto" es una afirmacion sobre SAS que
no se ha comprobado con un SAS real. La corrida real minima del plan (seccion 8) debe verificarla.

## Convenciones de datos

| Tema | Supuesto | Riesgo |
|---|---|---|
| Celda vacia en CSV | Es un faltante: NULL en SQLite. En SAS, el numerico faltante es `.` y el de texto es blanco. Al escribir, NULL vuelve a ser celda vacia. | Medio. Un blanco real en un campo de texto de SAS no es lo mismo que un faltante. El corpus no tiene blancos en el texto. |
| Tipo de columna | Un entero es una cadena sin ceros a la izquierda. Si todos los valores son enteros, INTEGER; si son enteros o decimales, REAL; si no, TEXT. `007` es TEXT (un codigo). | Bajo. PROC IMPORT de SAS puede elegir otro tipo. |
| Fechas ISO | `2026-03-01` se trata como texto. `BETWEEN` compara texto, que en ISO coincide con el orden de fechas. | Alto. Si PROC IMPORT las convierte a fecha de SAS, la comparacion con texto falla en SAS. El corpus lo asume. |
| Nombres de columna | Solo identificadores ASCII (`[A-Za-z_]\w*`). | Bajo. |
| Encabezado de salida | SQLite devuelve el nombre de columna tal como se escribio en el SELECT. SAS usa el nombre de la variable. Los casos escriben las columnas con el mismo nombre que el CSV. | Medio. |
| Expresion sin alias | SAS le da un nombre generado (por ejemplo `_TEMA001`); el oraculo toma el texto de la expresion. Los casos L1 siempre usan alias. | Alto si un caso omite el alias. |
| Orden de filas | Si `orden_relevante` es true, se usa el orden de SQLite (el de `ORDER BY`). Si es false, se ordena por todas las columnas: faltantes primero, luego numeros, luego texto. | Bajo. |

## Construcciones

| Construccion SAS | Que hace en SAS | Como se trata en el oraculo | Riesgo y supuesto |
|---|---|---|---|
| `WORK.X` | Prefijo de la biblioteca de trabajo | Se quita el prefijo; la tabla se llama `X`. | Ninguno. |
| `IS MISSING` | Verdadero si el valor es faltante | `IS NULL` | Medio: depende de la convencion de celda vacia. |
| `IS NOT MISSING` | Lo contrario | `IS NOT NULL` | Medio: igual. |
| `^=`, `~=` | Distinto (dos formas) | `<>` | Ninguno. |
| `\|\|` (concatenar) | Une textos. Un faltante de texto cuenta como blanco | Se pasa igual. En SQLite, un NULL hace NULL todo el resultado. | Alto con faltantes: el corpus no concatena columnas con faltantes. Un campo de largo fijo en SAS conserva blancos finales; por eso los programas usan `TRIM`. |
| `AS` en alias de tabla | Opcional: `FROM T1 A` | Se pasa igual: SQLite acepta las dos formas. | Ninguno. |
| `LEFT JOIN`, `INNER JOIN ... ON (...)` | Union de tablas | Se pasa igual. Sin casos todavia (nivel L2). | No verificado aun. |
| `CASE WHEN ... END` | Expresion condicional | Se pasa igual. Sin casos todavia. | Bajo. |
| `DISTINCT` | Filas unicas; los faltantes cuentan como un valor | Se pasa igual. | Bajo. |
| `GROUP BY`, `HAVING` | Agregados por grupo | Se pasa igual. Sin casos todavia (nivel L3). | No verificado aun. |
| `COUNT`, `SUM`, `MIN`, `MAX`, `AVG` | Agregados; ignoran faltantes | Se pasan igual. Un agregado sobre vacio da NULL en ambos. | Bajo. No hay casos todavia. |
| `ABS`, `ROUND`, `COALESCE`, `SUBSTR` | Funciones escalares | Se pasan igual. `ROUND` no tiene casos: el redondeo de la mitad difiere entre motores. | Medio en `ROUND`. |
| `UPCASE`, `LOWCASE` | Mayusculas y minusculas | `upper`, `lower` | Bajo. |
| `TRIM` | Quita blancos finales | `RTRIM` (quita solo blancos finales, como SAS) | Bajo. |
| `LIKE` | Coincidencia con `%` y `_` | Se pasa igual, con `PRAGMA case_sensitive_like = ON`. | Medio. Supuesto: LIKE de SAS distingue mayusculas. Si no es asi, el oraculo difiere para textos con mayusculas mezcladas. |
| `IN (lista)` | Pertenencia a una lista | Se pasa igual. | Bajo. |
| `BETWEEN a AND b` | Rango inclusivo | Se pasa igual. | Ver fechas ISO arriba. |
| `NOT`, `AND`, `OR` | Logica | Se pasan igual. | Bajo. |
| `ORDER BY` | Orden; faltantes primero en ascendente | Se pasa igual; faltantes primero en ascendente. Admite posicion (`ORDER BY 2 DESC`) y alias. | Medio: supuesto de que SAS pone los faltantes primero en ascendente, como SQLite (es el comportamiento habitual de SAS; no comprobado aqui). |
| `"texto"` | En SAS, texto entre comillas dobles | Pasa a `'texto'`; las comillas simples dentro se duplican. | Bajo. Un nombre con espacios (`"nombre"n`) no se soporta. |
| `'texto'` | Texto | Se pasa igual. | Ninguno. |
| `/* comentario */` | Comentario | Se quita. | Ninguno. |
| `calculated x` | Reutiliza un alias del mismo SELECT | `NoSoportado` | No soportado. |
| `FORMAT=`, `INFORMAT=`, `LABEL=` | Formato y etiqueta de salida | `NoSoportado` | No soportado. |
| `INTO :macro` | Guarda un valor en una macrovariable | `NoSoportado` | No soportado. |
| `/` (division) | En SAS da decimal | `NoSoportado`. SQLite trunca enteros, y no se debe traducir en silencio. | No soportado. Usar `* 1.0` si hace falta. |
| `**` (potencia) | Potencia | `NoSoportado` | No soportado. |
| `%` | En SQLite es modulo; en SAS es macro | `NoSoportado` | No soportado. |
| `&var` | Macrovariable | `NoSoportado` | No soportado (nivel L5). |
| `'01JAN2026'd`, `'...'t` | Fecha u hora de SAS | `NoSoportado` | No soportado (nivel L4). |
| `"nombre"n` | Nombre SAS entre comillas | `NoSoportado` | No soportado. |
| Otra funcion `nombre(...)` | Funcion de SAS o de SQLite no listada | `NoSoportado` con el nombre | Se amplia cuando un caso la necesite. |
| Sentencia distinta de `CREATE TABLE WORK.X AS` | Por ejemplo `SELECT` suelto, `DROP` | `NoSoportado` | No soportado. |
| `* comentario;` de sentencia | Comentario de SAS al inicio de sentencia | No se quita: SQLite lo rechaza y falla con error. | Bajo: falla en voz alta. |

## Comparaciones con faltantes (fuera del alcance de esta tabla)

En SAS, un faltante numerico en una comparacion fuera de SQL se considera menor que cualquier numero.
No esta verificado si PROC SQL de SAS sigue esa regla o la logica de tres valores de SQL. SQLite
usa la logica de tres valores: `NULL < 5` da NULL, y en WHERE eso es falso. Los casos L1 no comparan
columnas con faltantes en WHERE ni en JOIN. Este punto queda para la capa B (tarea K06) y para la
corrida real del plan.
