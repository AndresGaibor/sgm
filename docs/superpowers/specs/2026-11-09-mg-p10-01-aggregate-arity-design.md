# Diseño: aridad de agregados y funciones por fila en PROC SQL

## Intención

El intérprete del anillo B debe distinguir los agregados de PROC SQL de las funciones Base SAS que
tienen el mismo nombre. En PROC SQL, SUM, MIN, MAX y MEAN con un argumento resumen una columna;
con varios argumentos ejecutan la función Base SAS para cada fila. AVG con varios argumentos es
inválido porque Base SAS no tiene una función AVG.

## Evidencia SAS

La sección summary-function Component del índice de sqlproc conduce a las pp. 433 y 435–436. La
p. 433 lista AVG y MEAN como nombres de la media aritmética. La p. 435 establece que un argumento
resume los valores de una columna y varios argumentos se evalúan por fila; si existe una función
Base SAS homónima, PROC SQL la ejecuta, y AVG con varios argumentos da error porque esa función
Base SAS no existe. La p. 436 ejemplifica MIN, MAX y SUM con varios argumentos.

Las entradas MAX Function, MEAN Function, MIN Function y SUM Function de lefunctionsref.INDEX.md
conducen a las pp. 1230, 1233–1234, 1236 y 1580–1581. Describen argumentos numéricos y que MAX,
MEAN, MIN y SUM devuelven faltante cuando todos los argumentos están faltantes; SUM con varios
argumentos suma solo los no faltantes. `lrcon`, p. 124, documenta los faltantes numéricos especiales
`.A`–`.Z` y `._`.

## Alcance

- Preservar en el parser las llamadas de varios argumentos a SUM, MIN, MAX y MEAN sin que sqlglot
  las confunda con agregados SQL de un argumento.
- Traducirlas en la IR como expresiones por fila, restaurando el nombre SAS antes de las pasadas de
  traducción.
- Ejecutarlas en el intérprete con argumentos numéricos, omitiendo faltantes y devolviendo faltante
  cuando todos faltan.
- Mantener SUM(x), MIN(x), MAX(x), AVG(x) y MEAN(x) como agregados SQL de columna; AVG y MEAN
  calculan el mismo promedio.
- No transformar AVG(x, y) en un agregado ni en un promedio por fila; SAS documenta que esa forma
  genera error y se conservará como no traducible.
- Rechazar valores de texto no numérico en los argumentos numéricos en vez de asumir coerción.
- La verificación solo reconoce los faltantes que el intérprete ya representa como `None` o texto
  vacío/blanco. No reinterpretar cadenas como `.A` sin evidencia del tipo numérico de la columna;
  esa codificación queda pendiente.

## Fuera de alcance

- Emisión o ejecución de componentes Talend para estas expresiones.
- Equivalencia de SUM, MIN, MAX o MEAN sobre columnas de texto.
- Cambio de los esperados golden o aumento de horas MG-P10: la aceptación requiere cubrir más
  casos elegibles del anillo B.

## Decisiones

- MEAN se incluye junto con AVG porque la guía de PROC SQL los lista como sinónimos de agregado,
  y la guía muestra MEAN con varios argumentos como cálculo por fila.
- Se protege el nombre solo cuando se detectan al menos dos argumentos; las llamadas escalares de
  un argumento conservan el tratamiento de agregado SQL.
- Los nombres protegidos se guardan por consulta con marcadores internos que no colisionan con los
  identificadores de entrada y se restauran solo en las expresiones que los usaron; así no se cambia
  una columna que casualmente tenga el nombre del marcador base.
- Si la forma no puede conservarse con seguridad por el parser, se deja pendiente en vez de
  traducirla como resumen de tabla.
