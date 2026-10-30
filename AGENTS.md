# AGENTS.md

Instrucciones para agentes de IA que trabajen en `sgm-v2`.

## Prohibido en esta tarea

1. **Nada de MCP.** No uses herramientas MCP, no arranques `talend-mcp`, no copies `mcp/`, `contract/` ni `talend_adapter/`, no agregues dependencias `mcp` ni crees `.mcp.json`. La salida es solo Markdown y JSON.
2. Nada de API web ni frontend. Solo librería Python y CLI.
3. No conectarte a Impala ni a ninguna base. Los esquemas salen de un archivo JSON local (`env/schemas.json`).
4. No modificar el repositorio viejo (`migrador-sasgrid-qlik`). Solo leerlo y copiar.
5. No hacer `git push`. Sí se hacen commits locales, uno por hito, con el mensaje `hito N: <resumen>`.
6. No inventar datos: si el SAS no demuestra un tipo, una columna, un valor o una equivalencia, queda como pendiente con su motivo.
7. No guardar secretos. Nunca copiar una contraseña en claro de `proc pwencode in='...'`; se reemplaza por `'***'`.
8. No borrar ni debilitar pruebas para que pasen. Si una prueba falla, se arregla el código o se anota el bloqueo.
9. No usar nombres de scripts de ejemplo (`cod1`, `cod2`, `cars_poc`, `exogena`, `split2`, `split3`, `executeBulkload`, `waitForBulkLoads`, `bulkload_generic`) dentro de `src/` ni de `rules/`. Las reglas se basan en estructura o comportamiento. `tests/unit/test_no_script_specific_names.py` lo vigila.

## Forma de trabajar

- Lee antes de escribir. Los archivos grandes (`client_large.sas`, unos 800 KB) no se leen enteros: usa búsqueda y lecturas por rango de líneas.
- Archivos pequeños, una responsabilidad. Si un archivo pasa de 300 líneas, divídelo.
- Código e identificadores en inglés. Comentarios, docstrings, mensajes de usuario y documentación en español.
- Después de cada cambio corre `uv run pytest -q` y `uv run ruff check .`. Un hito termina solo con las dos cosas en verde.
- `PROGRESS.md` se actualiza al cerrar cada hito: fecha, qué se hizo, pruebas, métricas, bloqueos y decisiones.
- Si una decisión de diseño no está en el prompt, elige la opción más simple que respete las reglas y anótala en `PROGRESS.md` bajo "Decisiones".
- Dependencias permitidas: `networkx`, `typer`, `pyyaml`, `pydantic` (opcional). Dev: `pytest`, `pytest-xdist`, `ruff`. Cualquier otra se anota en "Decisiones".
