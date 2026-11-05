# Catálogo de documentación SAS 9.4 por capas

Este archivo ordena la documentación oficial de SAS según para qué la usa el traductor, y dice qué
hay descargado en `sas/` y qué no. Nació de un catálogo de referencia del equipo (2026-11-05) que
recomendaba cubrir sintaxis, funciones, macros, SQL, datasets, procedimientos, formatos, ejecución por
lotes y SAS Grid; acá queda con el estado real de cada guía.

La regla del proyecto es una: **ninguna equivalencia se escribe sin fuente**. Cada regla de
`rules/sas/` que dependa de un comportamiento debería poder citar la guía y la página, y tener una
prueba de equivalencia. Si no hay equivalencia segura, la decisión queda como pendiente con su motivo.

## Capa A — Semántica del lenguaje

Fundamenta el parser, el análisis semántico y las reglas de equivalencia.

| Guía | Docset | Páginas | Estado |
|---|---|---|---|
| Language Reference: Concepts | `lrcon` | 916 | descargada |
| Programmer's Guide: Essentials | `lepg` | 930 | descargada |
| Functions and CALL Routines: Reference | `lefunctionsref` | 1764 | descargada |
| Formats and Informats: Reference | `leforinforref` | 766 | descargada |
| Data Set Options: Reference | `ledsoptsref` | — | descargada |
| DATA Step Statements: Reference | `lestmtsref` | — | descargada |
| System Options: Reference | `lesysoptsref` | 514 | descargada |

`lesysoptsref` importa por opciones que cambian el resultado de un programa sin que se vean en el
código: `MERGENOBY` (p. 265) decide si un `MERGE` sin `BY` avisa o falla, `MISSING=` (p. 266) cambia
qué caracteres cuentan como valor perdido, `VALIDVARNAME=` (p. 412) qué nombres son válidos y
`YEARCUTOFF=` (p. 432) en qué siglo cae un año de dos dígitos.

## Capa B — Transformaciones

Identifica operaciones, dependencias, orden de ejecución y lo que no se traduce automáticamente.

| Guía | Docset | Páginas | Estado |
|---|---|---|---|
| Macro Language: Reference | `mcrolref` | 602 | descargada |
| SQL Procedure User's Guide | `sqlproc` | 546 | descargada |
| Procedures Guide | `proc` | 2928 | descargada |

De `proc` solo se consultan los procedimientos que el corpus usa de verdad (`SORT`, `SUMMARY`,
`MEANS`, `TRANSPOSE`, `FREQ`, `DATASETS`, `IMPORT`, `EXPORT`, `APPEND`, `FORMAT`). El índice
`proc.INDEX.md` sirve para llegar a cada uno sin leer las 2928 páginas.

## Capa C — Entorno y ejecución

Reconstruye dependencias externas, parámetros, ejecución remota y condiciones de despliegue.

| Guía | Docset | Páginas | Estado |
|---|---|---|---|
| Grid Computing in SAS 9.4 | `gridref` | 374 | descargada |
| Companion for UNIX Environments | `hostunx` | 702 | descargada |
| SAS/CONNECT User's Guide | `connref` | 500 | descargada |
| System Options: Reference | `lesysoptsref` | 514 | descargada |

Estas tres no son teoría: el programa grande se generó en `sasgrid.bancolombia.corp` /
`SASGRIDCOMP1.APPS.BANCOLOMBIA.CORP`, los casos de `tests/corpus/L8/validaciones/` traen `signon` y
`RSUBMIT`, y `rules/sas/plumbing.yaml` ya separa los comandos de shell (`x`, `%sysexec`, `systask`)
del trabajo de datos. En `gridref` el comando de envío está en «SASGSUB Command» (p. 321); en
`connref`, `SIGNON`/`SIGNOFF` en la p. 151 y `RSUBMIT` en la p. 185; en `hostunx`, la ejecución en
primer o segundo plano (p. 33) y los `fileref` (p. 129).

## Capa D — Construcción en Talend

| Documento | Dónde | Estado |
|---|---|---|
| Páginas de 41 componentes de Talend Studio 8.0 | `talend/` | descargadas |
| Guía de Studio: Jobs, joblets, contextos y conexiones (R2026-09) | `talend/studio-guia-jobs-contextos.md` | descargada |
| Catálogo de componentes contra sus páginas | `talend/catalogo/VERIFICACION.md` | revisado |

Esta capa es la que produce instrucciones verificables: componente, nombre, propiedades, esquema,
conexión, expresión y prueba. La versión de Studio del cliente manda sobre la guía: si una propiedad
no aparece en la página descargada, no se inventa, se marca como pendiente.

## Lo que no está descargado y por qué

- **NLS** (`nlsref`, 7.7 MB): responde, pero todavía no hay una regla que dependa de la codificación.
  El día que aparezca un archivo con encoding declarado, se agrega a `SAS_DOCSETS`.
- **Logging**: no hay docset con ese nombre en la colección (`logref` da 404). El catálogo lo manda al
  SAS Help Center; si hace falta, se busca ahí y se anota la URL exacta.
- **SAS/STAT, SAS/ACCESS, ODS, DS2**: solo si el corpus los usa. Hoy `client_large.sas` y los casos
  de `tests/corpus/` no los tienen; se comprueba con una búsqueda antes de bajarlos, no por si acaso.
- **Language Reference: Dictionary**: es la edición impresa que reúne sentencias, opciones de dataset,
  opciones de sistema y funciones. En docsets son `lestmtsref`, `ledsoptsref`, `lesysoptsref` y
  `lefunctionsref`, que ya están.

## Orden de descarga que se siguió

1. `leforinforref` — formatos e informats.
2. `lefunctionsref` — funciones.
3. `lestmtsref` — sentencias del paso DATA.
4. `ledsoptsref` — opciones de dataset.
5. `mcrolref` — macros.
6. `sqlproc` — SQL.
7. `lesysoptsref` — opciones globales.
8. `proc` — procedimientos.
9. `gridref`, `hostunx` y `connref` — entorno Grid, UNIX y sesiones remotas.
10. Documentación de Talend de los componentes objetivo.

Las nueve primeras están en `sas/`; la décima, en `talend/`.
