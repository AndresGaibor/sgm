# Referencia SAS 9.4 (documentación oficial)

Descargado el 2026-11-03 desde `documentation.sas.com` (colección `pgmsascdc/9.4_3.5`) y completado
el 2026-11-05 con las guías que faltaban del catálogo por capas (`../catalogo-sas.md`).
Son los PDF oficiales de SAS, sin modificar. Cada `.pdf` tiene además un `.txt` con su texto
extraído (una marca `<!-- página N -->` por página) para buscar con `Grep`.

| Archivo | Guía oficial | Páginas | Para qué sirve en sgm-v2 |
|---|---|---|---|
| `sqlproc.pdf` / `.txt` | SAS 9.4 SQL Procedure User's Guide (3.5) | 546 | PROC SQL: SELECT, joins, CREATE TABLE, subconsultas, funciones de agregado |
| `mcrolref.pdf` / `.txt` | SAS 9.4 Macro Language Reference | 602 | Macros (`%macro`, `%let`, `&var`, `%if`, `%do`) |
| `lestmtsref.pdf` / `.txt` | SAS 9.4 Statements Reference | — | Sentencias del DATA step (`MERGE`, `BY`, `RETAIN`, `IF`, `OUTPUT`, `FORMAT`, etc.) |
| `ledsoptsref.pdf` / `.txt` | SAS 9.4 Data Set Options Reference | — | Opciones de dataset (`KEEP=`, `DROP=`, `RENAME=`, `WHERE=`, `FIRSTOBS=`, `OBS=`) |
| `lefunctionsref.pdf` / `.txt` | SAS 9.4 Functions and CALL Routines Reference | 1764 | Funciones de texto, fecha, numéricas y formatos de fecha |
| `proc.pdf` / `.txt` | SAS 9.4 Procedures Guide | 2928 | Procedimientos como PROC SORT, PROC IMPORT/EXPORT, PROC CONTENTS, PROC FORMAT |
| `lepg.pdf` / `.txt` | SAS 9.4 Programmer's Guide: Essentials | 930 | Cómo funciona el paso DATA por dentro (búfer de entrada, PDV, ciclo compilar/ejecutar), grupos `BY` con `FIRST.`/`LAST.`, combinar conjuntos (`MERGE`, `SET`, `UPDATE`), `RETAIN`, arrays, `OUTPUT`, y el apéndice «Understanding How the DATA Step Works» (p. 887) |
| `lrcon.pdf` / `.txt` | SAS 9.4 Language Reference: Concepts (Sixth Edition) | 916 | Las reglas del lenguaje, no la sintaxis: valores perdidos (p. 123), expresiones y comparación con blancos finales (p. 133), fechas e intervalos (p. 155), `BY` en programas (p. 229), `WHERE` (p. 231), combinar y modificar conjuntos (p. 563), arrays (p. 667) |
| `leforinforref.pdf` / `.txt` | SAS 9.4 Formats and Informats: Reference | 766 | Diccionario completo de formats (p. 15) e informats (p. 553): `ANYDTDTE` (p. 617), `B8601DA` (p. 628), `E8601DA` (p. 654), `RMFDUR` (p. 706), `YYMMDD` (p. 755). Es la fuente de `rules/sas/informats.yaml` |
| `lesysoptsref.pdf` / `.txt` | SAS 9.4 System Options: Reference (Fifth Edition) | 514 | Opciones que cambian el resultado sin estar en el código: `MERGENOBY` (p. 265), `MISSING=` (p. 266), `VALIDVARNAME=` (p. 412), `YEARCUTOFF=` (p. 432) |
| `gridref.pdf` / `.txt` | Grid Computing in SAS 9.4 (Fifth Edition) | 374 | La infraestructura que no es transformación: envío con `SASGSUB` (p. 321), colas, nodos y planificación del Grid |
| `hostunx.pdf` / `.txt` | SAS 9.4 Companion for UNIX Environments (Sixth Edition) | 702 | Ejecución en primer o segundo plano (p. 33), `fileref` (p. 129), rutas y archivos del host |
| `connref.pdf` / `.txt` | SAS/CONNECT 9.4 User's Guide (Fourth Edition) | 500 | `SIGNON`/`SIGNOFF` (p. 151), `RSUBMIT` (p. 185) y librerías remotas (p. 31), que sí aparecen en el corpus |

Notas:
- Las URL siguen el patrón `https://documentation.sas.com/api/collections/pgmsascdc/9.4_3.5/docsets/<docset>/content/<docset>.pdf?locale=en`,
  salvo `lrcon`, que no está en esa colección (404) y se baja por
  `https://documentation.sas.com/api/docsets/<docset>/9.4/content/<docset>.pdf`. La diferencia vive
  en el campo `base` de cada `SasDocset` (`tools/referencia/fuentes.py`).
- Estas guías describen SAS 9.4 (edición 3.5). No se verificó que el código fuente del proyecto
  use esa versión; si una regla depende de un comportamiento específico, confirmarlo en la guía.
- Cada guía tiene además un `.INDEX.md` con sus secciones y páginas, generado desde los marcadores
  del PDF (`tools/referencia/indice.py`); el `.txt` sale de `tools/referencia/texto.py`.
- `lepg` no repite a `lestmtsref`: aquella da la sintaxis de cada sentencia y esta la semántica del
  paso DATA (qué queda en el PDV, cuándo se escribe la fila, cómo se agrupa por `BY`). Sirve para
  justificar una equivalencia de Talend cuando la duda es de comportamiento, no de ortografía.
- `lrcon` es la que se cita cuando la duda es una regla y no un caso: qué es un valor perdido, cómo
  se comparan cadenas (los blancos finales no cuentan: `'fox '` es igual a `'fox'`), qué pasa en un
  `MERGE` sin coincidencia, en qué orden se procesan `WHERE` y `BY`. `lepg` muestra cómo se usa;
  `lrcon` dice cómo se comporta.
- **Pendiente (tarea 9):** confirmar con el equipo del cliente la versión exacta de SAS en que corre el
  código. Hasta entonces, todo lo de estas guías se toma como SAS 9.4 y se marca como tal.
- PROC SORT y PROC FORMAT están dentro de `proc.pdf` (la guía de procedimientos), no en una guía propia.
- La guía de formatos y informats se llama `leforinforref` (con `forinfor`). Durante varios hitos se
  la buscó como `leforinfref`, con un solo `for`, y ese docset no existe: de ahí el 404 que quedó
  anotado como pendiente. Ya está descargada; lo que falta es llevar sus definiciones a
  `rules/sas/informats.yaml`.
- El orden por capas (semántica, transformaciones, entorno, Talend), lo que falta y por qué está en
  `../catalogo-sas.md`.
