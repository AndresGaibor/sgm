# Diseño: subconsultas no correlacionadas con IN y NOT IN

## Intención

El intérprete del anillo B debe ejecutar los tres casos traducibles del corpus L2 que filtran con
`IN (SELECT ...)` o `NOT IN (SELECT ...)`, para comparar el resultado con el esperado de SAS.
Actualmente rechaza esas expresiones aunque el plan ya conserva el filtro SQL.

## Enfoques considerados

1. **Evaluar la subconsulta como una consulta independiente en el intérprete (elegido).** Usa las
   tablas que el plan ya produjo, ejecuta el `WHERE` de la subconsulta y evalúa su única columna.
   Mantiene la forma de la IR y no afecta al emisor Talend.
2. **Reescribir cada subconsulta como un semi-join en la IR.** Podría servir también al emisor, pero
   cambia la forma del plan y requiere una semántica de unión que el alcance del intérprete no
   necesita.

Se elige el primer enfoque porque `MG-P10-01` mide el intérprete de referencia y los casos L2
demuestran subconsultas independientes de una sola tabla y columna. El emisor seguirá marcando la
subconsulta como parcial hasta que exista su implementación y evidencia Talend.

## Alcance y límites

- Admitir subconsultas independientes de un valor por fila, con una tabla fuente, una columna
  proyectada y un `WHERE` evaluable por el intérprete.
- Evaluar pertenencia con la comparación SAS ya usada por el intérprete; los duplicados de la lista
  no cambian el resultado de `IN`.
- Aceptar `NOT IN` como negación de la pertenencia para los datos no faltantes demostrados por el
  corpus.
- Rechazar de forma explícita valores faltantes, referencias correlacionadas, fuente o columna no
  verificable, varias columnas y cláusulas de subconsulta fuera de este alcance.
- No cambiar el emisor Talend, la clasificación parcial de SQL ni la cobertura MG-P10.

## Fuente y restricciones

`docs/referencia/sas/sqlproc.INDEX.md` remite a `sqlproc.pdf`, pp. 123–124: las subconsultas de
varios valores se usan con `IN`, y `NOT IN` excluye los valores devueltos. La p. 394 define `IN`
como prueba de pertenencia al conjunto de valores devueltos por la consulta; un conjunto sin
coincidencias no contiene ningún valor, por lo que `IN` es falso y `NOT IN` verdadero. Esta última
conclusión se deriva de la definición general de pertenencia. La p. 124 describe las correlacionadas
como dependientes de valores de la consulta externa, que quedan fuera de este alcance. Las pp. 39 y
99 respaldan la selección de todas las columnas y el uso de alias de tabla para calificarlas en
`SELECT alias.*`. No se extiende la equivalencia a faltantes ni se infiere esquema a partir de datos
ausentes.

## Decisiones del constructor

- Si una tabla derivada tiene varias escrituras, la subconsulta usa la última versión creada antes
  de la línea del filtro y mantiene las escrituras posteriores después de ese filtro. Si la evidencia
  no permite ordenar productor y consumidor, el intérprete rechaza el caso.
- Una proyección de todas las columnas sobre un lado vacío del LEFT JOIN se rechaza cuando no existe
  esquema que permita reconstruir sus columnas faltantes.

- El contexto de tablas se pasa al evaluador del filtro; se conserva el uso actual de `_filtrar` sin
  contexto para filtros que no tienen subconsultas. La ejecución usa evidencia de línea para leer la
  versión disponible antes del filtro y mantener las sobrescrituras futuras después de este.
- Las etapas de `L2-15` producen tablas intermedias con `SELECT alias.*`; se conserva el origen de
  cada lado del join y la proyección calificada publica solo las columnas del alias pedido.
- Cuando el lowerer ve una subconsulta en `WHERE`, conserva sus calificadores de tabla: el filtro
  sigue parcial para Talend, pero el intérprete necesita distinguir un alias externo correlacionado
  de una columna local.
- El intérprete prepara la lista de valores una vez por filtro, valida el alcance y luego reutiliza
  el evaluador existente para la comparación.
- El caso se considera cubierto en el anillo B solo cuando L2-06, L2-07 y L2-15 pasan sus archivos
  `esperado/`; eso no completa la traducción Talend.
