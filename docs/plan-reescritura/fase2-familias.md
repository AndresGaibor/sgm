# Fase 2: familias de regiones en `client_large.sas`

Reproducible con `uv run python tools/familias_regiones.py --sas tests/fixtures/sas/client/client_large.sas --agrupacion decisiones/client_large.agrupacion.yaml`.
Método en `src/sgm/proceso/familias.py`: se quitan comentarios, se pasa a minúsculas, se sustituye el
sufijo de producto (`_CTE`, `_AHO`, `_NEQUI`, declarado en el YAML) por `{P}` y se compara línea a
línea con `difflib`. Umbral 0,85. Mide texto, no semántica. La región 0 incluye el encabezado del
archivo, por eso su tamaño (1.214 líneas) no es comparable con las demás.

## Resultado (4 de noviembre de 2026)

| Familia | Líneas | Peor par | Regiones (producto) |
|---|---|---|---|
| 1 | 361 | 0,997 | 1 (aho), 4 (cte) |
| 2 | 346 | 0,977 | 6 (aho), 11 (cte) |
| 3 | 328 | 0,994 | 7 (aho), 12 (cte) |
| 4 | 202 | 0,874 | 8, 9, 18, 20, 22 (aho); 13, 14, 25, 27 (cte); 23 (sin producto) |
| 5 | 379 | 0,917 | 10 (aho), 15 (cte) |
| 6 | 284 | 0,979 | 19 (aho), 26 (cte) |
| 7 | 461 | 0,893 | 21 (aho), 28 (cte) |

Sin copia: 0 (aho, con encabezado), 2 (aho, grande), 3 (cte), 5 (cte, grande), 16 y 17 (nequi), 24 (cte),
29 (cte, grande).

## Lectura

- Seis familias son pares aho/cte: el mismo proceso con dos productos. Coincide con la corrección de H3.
- **Nequi no tiene copias.** Sus regiones (16 y 17) no se parecen a ninguna otra. La premisa D3/D6 del
  diseño manual (un mismo job de producto para los tres) no la sostiene el texto del SAS para Nequi;
  sigue siendo decisión humana (P6).
- **La familia 4 es la persistencia de una tabla WORK a la base.** Las diferencias entre sus miembros son
  solo el nombre de la tabla (`%let wtabsrc=%scan(work.<tabla>_{P}, -1, '.')`); sus etiquetas son
  `Escritura <TABLA>`. Es la maquinaria que el diseño elimina (D1, sin tablas intermedias). Se
  detecta por parecido, sin nombres del cliente. El parámetro de esa familia no es el producto sino la
  tabla, y por eso hay productos repetidos dentro de ella.
- La familia 4 une por encadenamiento (union-find): el peor par (0,874) es menor que el de las demás.
  Si se quiere subdividirla hay que subir el umbral o comparar contra un representante.
- Las regiones grandes (2, 5, 29) quedan solas: son el proceso completo de un producto (ver
  `fase0-correccion-h3.md`). La relación de contención entre ellas no se mide aquí.

## Límites

- El parecido de texto no demuestra que dos regiones hagan lo mismo; las líneas que difieren fuera del
  sufijo (`diferencias`) hay que revisarlas una por una.
- El producto de una región se decide por el sufijo dominante en su texto; un empate o ausencia deja
  `?` (no se adivina).
