# Fase 0: corrección de la hipótesis H3

La medición de `fase0-mediciones.md` dio H3 como refutada: la mediana de similitud entre los 435
pares de regiones bajaba de 0,75 a 0,20 al quitar la fontanería. Esa conclusión era demasiado gruesa.
La mediana sobre todos los pares mezcla tipos de región que no tienen por qué parecerse. La pregunta
correcta es si cada región tiene una copia, no si todas se parecen entre sí.

## Lo que se encontró al mirar el texto (4 de noviembre de 2026)

Cada región va de un `%macro ambiente;` al siguiente. Contiene primero la fontanería (definición de
macros y cargas masivas) y después el proceso de negocio. Comparando las líneas de las regiones
después de reemplazar el sufijo de producto (`_CTE`, `_AHO`, `_NEQUI`) por un marcador:

| Par de regiones | Líneas | Parecido (SequenceMatcher por línea) |
|---|---|---|
| 0 y 3 | 534 | 0,949 |
| 1 y 4 | 565 | 0,989 |
| 6 y 11 | 515 y 514 | 0,952 |
| 7 y 12 | 580 | 0,934 |
| 8 y 13 | 313 | 0,997 |
| 9 y 14 | 366 | 0,997 |
| 18 y 25 | 328 | 0,997 |
| 19 y 26 | 424 | 0,983 |
| 8 y 20 | 313 | 0,984 |
| 2 y 5 (grandes, producto distinto) | 1.417 y 4.265 | 0,458 |
| 17 y 29 (grandes) | 1.324 y 3.614 | 0,244 |

Numeración de regiones desde 0, por el orden de `%macro ambiente`.

Lectura:

- Las regiones pequeñas y medianas (313 a 725 líneas) vienen en copias casi exactas que solo cambian
  el sufijo de producto. Hay unos 15 tipos de región repetidos por producto.
- Las regiones grandes (2, 5, 17 y 29) son el proceso completo de un producto. La 2 (ahorros) tiene 58
  etiquetas y la 5 (corriente) 173. Comparando las etiquetas normalizadas, el 84 % de las de la 2
  aparecen en la 5 en el mismo orden: el proceso de ahorros es un subconjunto del de corriente. Las
  regiones 17 y 29 se parecen menos (23 %).
- Por eso el conteo anterior de "30 regiones sin parecido" mezclaba tipos distintos. La unidad de
  comparación debe ser la familia de clones con el producto como parámetro.

## Qué cambia

- Se confirma una parte de la premisa del diseño manual (D3): hay copias por producto que difieren
  solo en el sufijo. No se confirma que las 30 regiones sean copias del mismo proceso (P6 sigue
  abierto): son unas 15 familias, más cuatro regiones grandes con procesos propios.
- La Fase 2 se plantea como detección de clones parametrizados: normalizar el producto y los literales,
  agrupar regiones por parecido normalizado y emitir una plantilla por familia con una instancia por
  producto. El resto del parecido no se mide con tipos de operador sino con el texto normalizado.
- Las cifras de `fase0-mediciones.md` siguen siendo válidas como medición de fontanería (H1) y de
  tablas WORK (H2). Solo H3 se reemplaza por este documento.

## Límites

- El parecido por líneas con `difflib` es una medida de texto, no de semántica. Un 0,95 no demuestra
  que las dos regiones hagan lo mismo; muestra que difieren en pocas líneas y esas líneas hay que
  revisarlas.
- No revisé las diferencias de cada par. Las diferencias fuera del sufijo son justo lo que la
  parametrización tiene que listar.
- El informe de etiquetas por región (`fase0-etiquetas.md`) usa otra división (la primera región incluye
  el encabezado) y asigna producto por el sufijo dominante; sus cifras por producto no coinciden con
  las de este documento y no deben mezclarse.
