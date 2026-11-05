# Registro de riesgos del oráculo

Cada afirmación sobre SAS que hace `DIFERENCIAS.md` y que no se ha comprobado con un SAS real
aparece aquí con tres cosas: qué tan grave es si está mal, qué caso o vector la ejerce hoy y qué
tarea del plan la cierra. Sin severidad no se puede priorizar; sin caso, nadie se entera de que la
afirmación cambió; sin plan, el riesgo es eterno.

Severidad: **Alta** puede cambiar el resultado de un producto (conteos o sumas); **Media** cambia
un detalle verificable (orden, formato, redondeo de un caso raro); **Baja** afecta solo a datos que
hoy no existen.

Las tareas son de `docs/plan-reescritura/ruta-a-produccion.md`.

| ID | Riesgo (lo que afirma `DIFERENCIAS.md`) | Severidad | Lo ejerce | Plan |
|---|---|---|---|---|
| O-01 | En SAS un faltante numérico es menor que cualquier número: `saldo < 500`, `saldo <= 500` y `saldo <> 500` son verdaderos con faltante; SQLite da NULL y descarta la fila | Alta | `L4/l4_19_cmp_faltantes` (capa B, referencia en Python; su `razonamiento` dice que el resultado no es el de SQL) y vectores `cmp-missing-01` a `cmp-missing-03` | R7-13. Cierra cuando un caso capa A lo ejerza con el oráculo de acuerdo; hoy los casos L2 y L3 lo esquivan |
| O-02 | Un campo de texto de SAS compara sin blancos finales también cuando sale de una expresión (`UPPER(a)`, `a \|\| b`); el oráculo solo pone `COLLATE RTRIM` en columnas | Alta | Ningún caso; el vector `cmp-texto-01` solo cubre columnas | R7-13. Necesita un caso con `WHERE` sobre una expresión y un collar explícito |
| O-03 | El tipo de una columna sale del CSV del caso (`csv_tabla.tipo_sql`), no de lo que haría `PROC IMPORT` | Alta | Los 16 casos de `L8`; es el motivo de `pendiente_revision` en `v01`, `v02`, `v03`, `v05`, `v06`, `v07`, `03`, `06` y `08` | R1-02 (normalización) y R7-02 (`PROC IMPORT`), con `R9-12` como verificación final |
| O-04 | `IS MISSING` se traduce por tipo de columna (texto: `IS NULL OR rtrim(col) = ''`; numérico: `IS NULL`), y una columna con el mismo nombre y tipos distintos en dos tablas cae a la forma de texto | Media | `L8/validaciones/v02`, `L8/totales/03` y `08`; vectores `ismissing-01` a `ismissing-04` | R7-13 |
| O-05 | Una fecha ISO se trata como texto y `BETWEEN` compara texto; si `PROC IMPORT` la convierte a fecha de SAS, la comparación con texto falla | Alta | Ningún caso; `L8/totales/06_periodo_fecha` solo comprueba el formato del nombre, no un rango | R7-02, con un caso nuevo de rango de fechas |
| O-06 | `MERGE ... BY` de un `DATA step` **no** es un `JOIN`: por grupo sale el máximo de filas de los dos conjuntos y el más corto retiene su última observación | Alta | Los 12 casos `L6/l6_*` y la referencia de `referencia_datastep.py` | R7-09, con la regla de máximo de filas por grupo en un caso del oráculo |
| O-07 | `NOT IN ( SELECT ... )` con un NULL en la subconsulta: en SQL ningún valor queda fuera; en SAS no está comprobado | Media | `L2/l2_07`, `L2/l2_15` (sin NULL en la clave de la subconsulta, así que hoy no distingue) | R7-13, con un caso con NULL real en la subconsulta |
| O-08 | El orden de los faltantes en `ORDER BY`, `GROUP BY` y `DISTINCT` es el de SQLite (primero en ascendente, agrupados al final), y `'CC'` agrupa con `'CC '` | Media | `L2/l2_14`, `L3/l3_03`; `DISTINCT` con blancos no tiene caso | R7-13 |
| O-09 | `ROUND(x, u)` usa una tolerancia de 1e-10 para decidir el empate y no se comprobó `u = 0`; SAS usa un fuzz no documentado con precisión | Media | `L4/l4_18_round_multiplo_y_mitad`, vectores `round-01` a `round-06` y `L8/totales/05_conciliacion` | R7-13, con vectores nuevos en los bordes del fuzz y `u = 0` |
| O-10 | `OUTER UNION CORR` entre N `SELECT`: el oráculo no comprueba el orden de las columnas de salida ni el tipo que resulta de mezclar NULL con texto | Media | `L8/totales/02_inconsistencias_correccion` y `L8/totales/08_cadena_completa_macros` | R1-13 y R7-13 |
| O-11 | `tabla (OBS=n)` lee las n primeras observaciones en orden físico; el oráculo usa el orden de inserción | Media | `L8/totales/05_conciliacion` (`(OBS=1)`) | R7-13 |
| O-12 | `SELECT ... INTO :macro` no lo ejecuta el oráculo: las macrovariables las resuelve el cruce en Python antes de correr el SQL | Baja | `L8/totales/05_conciliacion` y `08_cadena_completa_macros` | R2-01 y R2-02 (los valores llegan por contexto al Job); R7-13 solo si el traductor los necesita |
| O-13 | Un agregado sin valores presentes da NULL en SQLite; en SAS, `AVG` da faltante (supuesto) | Baja | `L3/l3_04`, `L3/l3_02` | R7-13 |
| O-14 | `LIKE` de SAS distingue mayúsculas (por eso el oráculo enciende `PRAGMA case_sensitive_like`) | Media | `L1/l1_06_like_con_tildes`, `L1/l1_07_like_guion_bajo`, `L1/l1_14_expresion_compuesta` | R7-13 |
| O-15 | El oráculo no ejecuta pasos `DATA` ni `PROC IMPORT`: los 9 casos capa A de `L8` se omiten con ese motivo y su cruce vive en `tools/corpus_datos/*cruce*.py` | Alta | `tests/corpus/L8/` (capa A) y los cruces de totales y validaciones | R1-02, R7-02 y R7-14 (caso L9 con esperado por construcción) |
| O-16 | El mecanismo `preparacion` evalúa el `DATA step` previo con la referencia de Python (capa B); si esa referencia entiende mal `input(left(x), N.)`, el caso hereda el error | Media | `L3/l3_08`, `L8/validaciones/v01` y `v06` | R7-13 y R1-02, con vectores de `input` y `left` contrastados contra SAS |
| O-17 | Una expresión sin alias toma un nombre generado por SAS (`_TEMA001`); el oráculo usa el texto de la expresión | Baja | Ningún caso: `L1` siempre usa alias | R7-13 |
| O-18 | El orden de las columnas de salida sin `ORDER BY` y los formatos de `PROC EXPORT` (comillas, `BEST`, `3.`, `20.`) no se pueden demostrar sin SAS | Media | `L8/totales/03_sabana_nal_ext` y `06_periodo_fecha`; `L8/validaciones/v07` | R1-14 (salidas con el orden del `SELECT`) y R9-12 |

## Cómo se mantiene

- Un riesgo nuevo entra con el cambio que lo introduce (una fila de `DIFERENCIAS.md` sin fila aquí
  es un hueco).
- Cuando una tarea cierra un riesgo, la fila se queda y se le añade el caso que lo demuestra; no se
  borra: la historia de qué se creía y cuándo se comprobó vale para la auditoría de R9-14.
- La severidad no la baja quien escribe el traductor: la baja quien tiene el SAS o los datos.
