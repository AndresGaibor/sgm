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

## Construcciones de L2 y L3 (JOIN, subconsultas, CASE, agregados)

Estas filas las usan los casos L2 y L3. Todas se pasan igual a SQLite, salvo lo que se indica.

| Construccion SAS | Que hace en SAS | Como se trata en el oraculo | Riesgo y supuesto |
|---|---|---|---|
| `LEFT JOIN` / `INNER JOIN` con `ON ( a.X = b.Y AND a.Z = b.W )` | Une por una o dos claves | Se pasa igual. Un faltante en la clave no empareja (NULL no es igual a nada). | Bajo. Supuesto: SAS tampoco empareja faltantes. |
| Clave repetida en la tabla de la derecha | Cada fila de la izquierda sale una vez por cada coincidencia | Se pasa igual: el cruce multiplica filas. Casos `l2_05` y `l3_09`. | Ninguno: es el comportamiento esperado de SQL y de SAS. |
| Auto-JOIN (`FROM T a INNER JOIN T b`) | Une una tabla consigo misma | Se pasa igual. Caso `l2_12`. | Bajo. |
| Tres tablas con dos `INNER JOIN` encadenados | Une en cadena | Se pasa igual. Caso `l2_11`. | Bajo. |
| `t.*` y `p.*` en SELECT | Todas las columnas de un alias | Se pasa igual. | Bajo. |
| `IN ( SELECT ... )` | Pertenencia a una subconsulta | Se pasa igual. Casos `l2_06`, `l2_07`. | Bajo. |
| `NOT IN ( SELECT ... )` | Lo contrario | Se pasa igual. Casos `l2_07`, `l2_15`. | Medio: si la subconsulta trae un NULL, en SQL ningun valor queda fuera del NOT IN. Los casos no tienen NULL en la clave de la subconsulta. No verificado en SAS. |
| `CASE WHEN ... THEN ... ELSE ... END` | Expresion condicional | Se pasa igual. Casos `l2_08`. | Ver "Comparaciones con faltantes" abajo. |
| `COALESCE(a, b)` | Primer valor no faltante | Se pasa igual. Casos `l2_09`. | Bajo. |
| `COUNT(*)`, `COUNT(col)`, `COUNT(DISTINCT col)` | Cuenta filas, valores presentes o valores distintos | Se pasan igual. Casos `l3_01`, `l3_06`. | Bajo. `COUNT(*)` cuenta las filas faltantes; `COUNT(col)` no. |
| `SUM`, `MIN`, `MAX`, `AVG` con faltantes | Ignoran los faltantes | Se pasan igual. Un agregado sin valores presentes da NULL en SQLite; en SAS, `AVG` da faltante (supuesto, lo muestra `l3_04`). Casos `l3_02`, `l3_04`. | Bajo. `AVG` es coma flotante: los casos usan tolerancia. El caso de `SUM` sin valores no esta cubierto. |
| `GROUP BY` con faltante | El faltante forma su propio grupo, primero al ordenar | Se pasa igual. Caso `l3_03`. | Medio: el orden de los faltantes en GROUP BY no esta verificado en SAS. |
| `HAVING` con agregado | Filtra grupos | Se pasa igual. Casos `l3_05`, `l3_12`. | Bajo. |
| Subconsulta escalar `(SELECT COUNT(*) FROM T)` en SELECT | Valor constante | Se pasa igual. Caso `l3_09`. | Bajo. |
| `ORDER BY` con alias y `DESC` | Orden descendente | Se pasa igual. Un faltante va al final en descendente (SQLite) y al final en SAS (supuesto). Caso `l2_14`. | Medio, supuesto no verificado. |
| `PROC EXPORT`, `PROC IMPORT` | Lectura y escritura de archivos | No se ejecutan: el oraculo lee `entradas/` y no escribe en disco. Son parte del estilo del original. | Ninguno para el oraculo; la lectura real la prueba el Job. |

### Comparaciones con faltantes (riesgo alto, no verificado)

En SAS, un faltante numerico es menor que cualquier numero en una comparacion. Por eso
`saldo < 500`, `saldo <= 500` y `saldo ^= 500` son verdaderos para un faltante, mientras que SQLite
(logica de tres valores) da NULL y el WHERE descarta la fila. Esta diferencia del oraculo no esta
resuelta. Los casos L2 y L3 la evitan: solo comparan con `<`, `<=` o `<>` columnas que nunca son
faltantes (ids, conteos), y con `>=` sobre montos con faltantes (ahi SAS y SQL coinciden: el
faltante no cumple). Si un programa real usa `<` sobre un campo con faltantes, el oraculo puede dar
un resultado distinto al de SAS. Queda para la capa B (tarea K06) y para la corrida real del plan.

### Blancos finales en claves de texto (riesgo alto, no verificado)

En SAS, un campo de texto de largo fijo compara sin sus blancos finales: `'CC '` es igual a `'CC'`.
SQLite no: `'CC '` es distinto de `'CC'`. Los CSV del corpus no traen blancos finales en claves, así
que el oraculo no lo muestra. Un programa real con un lookup sobre texto de ancho fijo puede fallar
en SQLite y pasar en SAS. Mientras no haya un caso con blancos, el riesgo sigue abierto.

### Preparacion con DATA step (caso `l3_08`)

El oraculo SQL no ejecuta pasos DATA. Un caso que mezcla DATA step y PROC SQL declara el DATA step en
`caso.yaml` como `preparacion`: asignaciones `variable = f1(f2(columna))` evaluadas con `evaluar`
de `tools/corpus_semantica_funciones.py` (capa B). El generador escribe el resultado en
`entradas_preparadas/`, y el oraculo comprueba antes de correr el SQL que ese archivo coincide con
la preparacion. Si no coincide, el caso falla con el motivo.

- Un faltante de texto entra al DATA step como blanco, como en SAS. El resultado faltante sale
  como celda vacia.
- La conversion `input(left(x), 20.)` depende de los vectores de la capa B (`input-01` a `input-07`
  y `left`). Si la funcion de referencia entiende mal la documentacion, el caso lo hereda.
- El riesgo de que la preparacion no coincida con el DATA step real queda para la corrida real del
  plan (seccion 8 del plan).
