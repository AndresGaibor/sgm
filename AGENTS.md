# AGENTS.md

Instrucciones para agentes de IA que trabajen en `sgm-v2`.

## Prohibido en esta tarea

1. **Nada de MCP.** No uses herramientas MCP, no arranques `talend-mcp`, no copies `mcp/`, `contract/` ni `talend_adapter/`, no agregues dependencias `mcp` ni crees `.mcp.json`. La salida es solo Markdown y JSON.
2. Nada de API web ni frontend. Solo librería Python y CLI.
   **Excepción aprobada por el usuario (hito 43):** `sgm flujo` escribe un HTML estático de revisión
   (`<programa>.flujo.html`) con CSS y SVG en línea. No tiene scripts, servidor ni recursos externos,
   y no cambia el plan ni la guía. Es una vista de cómo funciona el programa, no una traducción.
3. No conectarte a Impala ni a ninguna base. Los esquemas salen de un archivo JSON local (`env/schemas.json`).
4. No modificar el repositorio viejo (`migrador-sasgrid-qlik`). Solo leerlo y copiar.
5. No hacer `git push`. Sí se hacen commits locales, uno por hito, con el mensaje `hito N: <resumen>`.
6. No inventar datos: si el SAS no demuestra un tipo, una columna, un valor o una equivalencia, queda como pendiente con su motivo.
7. No guardar secretos. Nunca copiar una contraseña en claro de `proc pwencode in='...'`; se reemplaza por `'***'`.
8. No borrar ni debilitar pruebas para que pasen. Si una prueba falla, se arregla el código o se anota el bloqueo.
9. No usar nombres de scripts de ejemplo (`cod1`, `cod2`, `cars_poc`, `exogena`, `split2`, `split3`, `executeBulkload`, `waitForBulkLoads`, `bulkload_generic`) dentro de `src/` ni de `rules/`. Las reglas se basan en estructura o comportamiento. `tests/unit/test_no_script_specific_names.py` lo vigila.

## Documentación de referencia

Las equivalencias no se inventan: cada regla del traductor se apoya en una página de la
documentación de SAS. Está en `docs/referencia/`; el estado y la deuda de cada guía, en
`docs/referencia/README.md` y `docs/referencia/catalogo-sas.md`.

- **13 guías** en `docs/referencia/sas/`, cada una con tres archivos: `<docset>.pdf` (no
  versionado), `<docset>.txt` (texto con marcas `<!-- página N -->`) y `<docset>.INDEX.md`
  (sección → página, sacado de los marcadores del PDF). Las páginas de Talend, por componente, en
  `docs/referencia/talend/`.
- **No leas el PDF ni el `.txt` entero.** Busca la sección en el `.INDEX.md` y luego la página en el
  `.txt`: `grep -n "<!-- página 265 -->" docs/referencia/sas/lesysoptsref.txt`.
- Qué guía para qué: `lrcon` = semántica (qué significa una comparación, un missing); `lestmtsref` =
  sintaxis de cada sentencia; `lefunctionsref` = funciones; `leforinforref` = formats e informats
  (el docset es `leforinforref`, con `forinfor`: `leforinfref` no existe y da 404); `sqlproc` =
  `PROC SQL`; `proc` = los demás procedimientos; `lesysoptsref` = opciones de sistema;
  `ledsoptsref` = opciones de data set; `mcrolref` = macros; `lepg` = uso y ejemplos; `gridref`,
  `hostunx` y `connref` = Grid, UNIX y CONNECT (`SIGNON`, `RSUBMIT`, `PROC UPLOAD`).
- `tools/referencia/`: `fuentes.py` es el catálogo de docsets y sus dos formas de URL; `descargar.py`
  baja; `indice.py` y `texto.py` generan el `.INDEX.md` y el `.txt` (necesitan `pypdf`:
  `uv run --with pypdf`); `verificar.py` cruza `rules/talend/components.json` con las páginas.
- `rules/sas/catalogo/*.yaml` dice qué está cubierto y con qué página. Esquema:
  `schemas/rules/catalogo.schema.json`; cada entrada exige `id`, `nombre`, `fuente` (`<pdf>, p. N`) y
  `estado`. Los estados significan: `reconocida` = el traductor ya lo convierte, venga de una regla
  YAML o de la tabla de `src/sgm/expressions/`; `no_reconocida` = lo conoce y no lo convierte;
  `no_verificada` = existe en la guía y el repo no lo trata; `dentro_de_select` = solo se acepta en
  ese contexto.
- **Si no hay página, no hay equivalencia:** se emite `Pendiente:` con el motivo, nunca un valor
  supuesto. `docs/opciones-de-sistema.md` es una decisión tomada así.
- Lo vigilan `tests/unit/test_catalogo_sas.py` (toda página citada tiene que existir en el índice de
  su guía) y `tests/unit/test_referencia_tools.py`. Un catálogo con página inventada no pasa.
- Los `.pdf` están en `.gitignore` (unos 50 MB): no se commitean, se bajan con `tools/referencia/`.

## Numeración de hitos

- El número de cada hito es único en todo el repositorio: antes de escribir, busca el último
  `## Hito` de `PROGRESS.md` y suma uno.
- Una entrada publicada no se renumera: `docs/` la referencia por número.
- Sesiones en paralelo: cada serie toma una letra detrás del número, que va en el título y en el
  mensaje del commit (`hito 73c: ...`). `c` está tomada por el corpus y los contenedores;
  `b` quedó para el resto de las series viejas. Las letras no se reutilizan ni se quitan.
- El commit del hito lleva el mismo número que la entrada, con el mensaje `hito N: <resumen>`.

## Forma de trabajar

- Lee antes de escribir. Los archivos grandes (`client_large.sas`, unos 800 KB) no se leen enteros: usa búsqueda y lecturas por rango de líneas.
- Archivos pequeños, una responsabilidad. Si un archivo pasa de 300 líneas, divídelo.
- Código e identificadores en inglés. Comentarios, docstrings, mensajes de usuario y documentación en español.
- Después de cada cambio corre `uv run pytest -q` y `uv run ruff check .`. Un hito termina solo con las dos cosas en verde.
- `PROGRESS.md` se actualiza al cerrar cada hito: fecha, qué se hizo, pruebas, métricas, bloqueos y decisiones.
- Si una decisión de diseño no está en el prompt, elige la opción más simple que respete las reglas y anótala en `PROGRESS.md` bajo "Decisiones".
- Dependencias permitidas: `networkx`, `typer`, `pyyaml`, `pydantic` (opcional). Dev: `pytest`, `pytest-xdist`, `ruff`. Cualquier otra se anota en "Decisiones".
