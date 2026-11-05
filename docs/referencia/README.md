# Referencia de documentación oficial

Copias locales de la documentación oficial de SAS y Talend que usa el proyecto, para consultarla sin
internet. Cada carpeta dice qué se descargó, de dónde y cuándo.

| Carpeta | Contenido | Fuente | Descargado |
|---|---|---|---|
| [`sas/`](sas/README.md) | 13 guías en PDF, con texto extraído (`.txt`) e índice por sección (`.INDEX.md`) | documentation.sas.com, colección `pgmsascdc/9.4_3.5` y `/api/docsets/` | 2026-11-03, completado el 2026-11-05 |
| [`catalogo-sas.md`](catalogo-sas.md) | Las guías ordenadas por capa (semántica, transformaciones, entorno, Talend), con lo que falta y por qué | — | 2026-11-05 |
| [`talend/`](talend/README.md) | Páginas de 41 componentes de Talend Studio 8.0 y la guía de diseño de Jobs y contextos (R2026-09) | help.qlik.com | 2026-11-03 |

## Cómo se regenera

Las herramientas están en `tools/referencia/`. Solo usan la biblioteca estándar, salvo el texto y el
índice de los PDF:

```
uv run python tools/referencia/descargar.py sas                 # PDF de SAS (no repite los existentes)
uv run python tools/referencia/descargar.py sas --forzar        # vuelve a bajar los PDF
uv run python tools/referencia/descargar.py talend              # componentes y guía de Studio
uv run python tools/referencia/descargar.py talend --componentes tmap tsqltemplate
```

El índice `.INDEX.md` de cada guía sale de los marcadores del PDF y requiere `pypdf`, que no es una
dependencia de `sgm`. Se instala solo para esa tarea. Ver `tools/referencia/indice.py`.

El `.txt` de cada guía sale de `tools/referencia/texto.py`, que también necesita `pypdf`:

```
uv run --with pypdf python tools/referencia/texto.py docs/referencia/sas/lepg.pdf
```

Las pruebas de `tests/unit/test_referencia_tools.py` revisan que las listas de la herramienta
coincidan con los archivos que hay en esta carpeta.

## Qué no está aquí

- La guía de soporte de idioma nacional (`nlsref`, 7.7 MB) responde, pero no se descargó: todavía no
  hay una regla que dependa de la codificación. Si aparece un archivo con encoding declarado, se
  agrega a `SAS_DOCSETS`.
- La guía de logging no tiene docset en la colección (`logref` da 404); el catálogo la manda al SAS
  Help Center. Si hace falta, se busca ahí y se anota la URL exacta.
- La versión exacta de SAS del cliente no está confirmada. Las guías son 9.4 (edición 3.5); ver
  `sas/README.md`.
- Las páginas de Talend que el sitio no publica en Markdown se listan como no descargadas dentro del
  archivo de cada tema, con su URL.

## Revisiones hechas sobre esta documentación

- `talend/catalogo/VERIFICACION.md`: el catálogo de componentes contra sus páginas.
- `talend/cruce-con-el-codigo.md`: lo que dice la documentación frente al código, con las brechas.
- `sas/*.INDEX.md`: índices por sección de las trece guías de SAS.
