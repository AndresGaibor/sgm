# Referencia SAS 9.4 (documentación oficial)

Descargado el 2026-11-03 desde `documentation.sas.com` (colección `pgmsascdc/9.4_3.5`).
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

Notas:
- Las URL siguen el patrón `https://documentation.sas.com/api/collections/pgmsascdc/9.4_3.5/docsets/<docset>/content/<docset>.pdf?locale=en`.
- Estas guías describen SAS 9.4 (edición 3.5). No se verificó que el código fuente del proyecto
  use esa versión; si una regla depende de un comportamiento específico, confirmarlo en la guía.
- Cada guía tiene además un `.INDEX.md` con sus secciones y páginas, generado desde los marcadores
  del PDF (`tools/referencia/indice.py`).
- **Pendiente (tarea 9):** confirmar con el equipo del cliente la versión exacta de SAS en que corre el
  código. Hasta entonces, todo lo de estas guías se toma como SAS 9.4 y se marca como tal.
- PROC SORT y PROC FORMAT están dentro de `proc.pdf` (la guía de procedimientos), no en una guía propia.
  La guía de formatos (`leforinfref`) devolvió 404 y no se descargó.
