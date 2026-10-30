# PROGRESS

## Hito 0. Repositorio nuevo

- Fecha: 2026-10-30
- Qué se hizo: repositorio `git init` en `main`, paquete `uv init` con Python 3.12, estructura de carpetas, `pyproject.toml` (dependencias `networkx`, `typer`, `pyyaml`; dev `pytest`, `pytest-xdist`, `ruff`; `line-length = 100`; `addopts = -n auto`), `AGENTS.md`, `.gitignore`.
- Pruebas: 1 pasa (`test_el_paquete_importa`). `ruff check .` limpio.
- Bloqueos abiertos: ninguno.

## Decisiones

- El script de consola apunta a `sgm.cli:app` (Typer), tal como pide el prompt.
- Pydantic no se usa en el hito 0. Los modelos serán `dataclass`.

## Hito 1. Copiar solo lo que sirve

- Fecha: 2026-10-30
- Qué se hizo:
  - `ingest/`: importador copiado. `Settings` se sustituyó por `ImportLimits` y los modelos `FileKind`, `SourceFile`, `Skipped` pasaron a dataclasses (sin pydantic).
  - `frontend/lexer.py`: copiado sin cambios.
  - `frontend/macro_index.py`: solo funciones puras (`substitute`, `first_quoted`, `resolve_path`, `PathIndex`). Se quitaron `walk`, `macro_index` y `constant_vars` porque dependían del AST anterior; se reescriben en el hito 4.
  - `frontend/grid.py`: modelos `GridTask`, `Schedule`, `Orchestration` (dataclasses), `shell_tasks` y orden topológico. Se quitaron `orchestrator_macros`, `macro_step_tasks` y `analyze_grid`, que dependían del AST; se reescriben en el hito 4.
  - `catalog/environment.py`: catálogo de entorno portado a dataclasses con la misma validación (sin pydantic).
  - `redaction.py`, `expressions/talend_translator.py`, `expressions/expressions.py`: copiados sin cambios de lógica.
  - `passes/plumbing_patterns.py`: solo patrones de fontanería como datos (`PlumbingPattern`, `match_plumbing`). La clasificación con el IR anterior no se copió.
  - `emit/conventions/`: `naming.py` (validación y render de nombres), `context_rules.py` (copiado), `infra.py` (conexión, cierre, `tDie` y `tLogRow` como reglas de datos), `best_practices.py` (BP-NAME-01/02, BP-CTX-01, BP-SEC-01, BP-DB-01, BP-ERR-01, BP-SIZE-01 sin dependencias MCP).
  - `rules/talend/`: `components.json`, `official-component-inventory.json`, `component-panels.json` copiados. `engines.json` (claves `engines` y `engine_notes`) y `type_hints.json` salen de `rules/mappings/talend-components.json`.
  - `rules/sas/sql-functions.json` copiado.
  - `tests/fixtures/sas/` copiado completo (incluye `real`, `synthetic`, `grid`, `generalization`, `inc`).
  - `tests/support/cache.py` copiado. `docs/conventions.md` sin la regla "un programa = un Job" ni la de un componente por paso.
  - Pruebas portadas: `test_no_script_specific_names.py` (lista nueva del prompt), `test_security.py` (solo redacción), `test_ingestion.py` (solo importador), `test_talend_translator.py`.
- Pruebas: 45 pasan, 1 se salta (symlink en Windows). `ruff check .` limpio.
- Diferido a su hito, porque dependen de módulos que aún no existen: `tests/support/spec_invariants.py` (hito 6), `tools/automation_metrics.py` (hito 10).
- Bloqueos abiertos: ninguno.

## Decisiones

- E501 (líneas largas) se tolera solo en código portado o de datos (mensajes en español, patrones Java y de ruta). Está en `per-file-ignores` de `pyproject.toml`. El resto del código respeta `line-length = 100`.
- Catálogo de entorno y modelos de ingesta: dataclasses en vez de pydantic, porque pydantic no está en la lista de dependencias permitidas.
- Se eliminó la vista previa de renombrado masivo de `job_naming.py` (dependía del modelo de plan anterior).
- Hito 0: identidad de git del repositorio nuevo = la del repositorio viejo (`Andres Gaibor`), configurada solo en `sgm-v2`.
- Incidente: durante el hito 1 se ejecutó `uv run --project .` dentro del repositorio viejo; sincronizó su `.venv` (ignorado por git, sin cambios en el código). El repositorio viejo sigue limpio en `git status`.

## Hito 2. Fixtures del cliente

- Fecha: 2026-10-30
- Qué se hizo: los dos programas del cliente están en `tests/fixtures/sas/client/`:
  - `client_poc.sas` ← `data/projects/c0a88f920346/src/cod1.sas` del repositorio viejo (81 KB, 19 nodos `/* Etiqueta: */`, `sashelp.cars` y bulkload). No tiene credenciales.
  - `client_large.sas` ← `Downloads/Cod2.txt` (836 KB, 610 nodos `/* Etiqueta: */`, proceso de información exógena de depósitos).
- Enmascarado: en `client_large.sas` hay 1 `proc pwencode in=...` y 26 sentencias `signon ... user=... pass=...` con la contraseña en claro. Todas quedaron como `'***'`. `client_poc.sas` no tiene credenciales.
- Pruebas: `test_pwencode_en_fixtures_y_salidas_solo_con_asteriscos` (en `test_security.py`) falla si un fixture de texto, un miembro de un ZIP de fixtures o un archivo de `out/` trae un `proc pwencode` con un valor distinto de `'***'`. Total: 46 pasan, 1 se salta. `ruff check .` limpio.
- Bloqueos abiertos: ninguno.

## Decisiones (hito 2)

- Además de `pwencode`, se enmascara `pass=` en claro en `client_large.sas` (`signon`). El prompt pedía solo `pwencode`, pero es una credencial del mismo tipo y no debe llegar a fixtures ni salidas.

## Hito 3. Frontend: nodos y pasos

- Fecha: 2026-10-30
- Qué se hizo:
  - `frontend/splitter.py`: nodos por `/* Etiqueta: ... */`, con líneas de inicio y fin; quita U+200B sin mover líneas; nodo sin etiqueta solo si tiene contenido.
  - `frontend/steps.py`: DATA step, PROC SQL, PROC genérico (nombre, `DATA=`, `OUT=`, opciones, cláusulas BY/VAR/CLASS/WHERE), `%macro`/`%mend`, llamadas de macro (con o sin paréntesis), `%let`, `%include`, `libname`, `options`, `x`, y `Global` para lo demás. Un paso que falla devuelve `Unparsed` y sigue.
  - `frontend/sql.py`: `create table ... as select`, `select` (con FROM/JOIN), pass-through `from connection to <motor> (...)`, `execute (...) by <motor>` y la forma `execute by <motor> (...)`, `insert`, `delete`, `drop table`, `connect`, `disconnect`. El SQL del pass-through queda intacto.
  - `frontend/datastep.py`: `set`/`merge` con `in=`, `by`, `where`, `output`, `keep`, `drop`, `rename`, `retain`, `lag`, `first./last.`, `array`, `do`/`end`, `infile`, `input`, `datalines`, `call symput`, `format`/`length`/... como `declare`, asignaciones.
  - Corrección en `frontend/lexer.py`: el resto de la línea de `datalines;` ya no cuenta como una fila vacía.
- Pruebas: 17 nuevas en `tests/unit/test_frontend.py`. Total: 64 pasan, 1 se salta. `ruff check .` limpio.
- Métricas sobre `client_large.sas`: 610 nodos, 610 con etiqueta (coincide con las `/* Etiqueta:` del archivo). Sentencias: 353 DATA step, 359 PROC SQL, 215 PROC genérico, 274 definiciones de macro. 0 `Unparsed`. Tiempo de división más parseo: ~0.5 s.
- Bloqueos abiertos: ninguno.

## Hito 4. Expansor de macros

- Fecha: 2026-10-30
- Qué se hizo:
  - `frontend/macros.py`: índice de `%macro ... %mend` (también anidadas) con huella del cuerpo normalizado; evaluación parcial sobre sentencias crudas: `%let` constante, `&var` conocidas, `%if`/`%else` con condición constante (`=`, `eq`, `ne`, `<`, `>`, etc.), `%do` con límites constantes (`%to`, `%by` negativo incluido), llamadas con parámetros posicionales y por nombre, y `%include` resuelto dentro del proyecto. Lo no constante se marca como `MacroDynamic` con motivo `MACRO_DINAMICA` y su texto.
  - `frontend/program.py`: pipeline por proyecto. Indexa todas las macros antes de expandir, expande archivo a archivo y asigna a cada paso o dinámico la etiqueta de su nodo.
  - `frontend/macro_index.py`: se completó con `resolve_path` y utilidades (sin AST).
- Pruebas: 11 nuevas en `tests/unit/test_macros.py`. Total: 75 pasan, 1 se salta. `ruff check .` limpio.
- Métricas sobre los fixtures del cliente:
  - `client_poc.sas`: 17 macros con nombre único, 40 definiciones duplicadas contadas una vez, 6 nombres con cuerpos distintos, 36 dinámicos, 10 `%include` externos, 0 `Unparsed`.
  - `client_large.sas`: 10 macros con nombre único, 261 definiciones duplicadas contadas una vez, 3 nombres con cuerpos distintos, 610 dinámicos, 30 `%include` externos, 0 `Unparsed`. Los dinámicos son sobre todo `%let` con `%sysfunc`, `TITLE`/`FOOTNOTE` con `%qsysfunc(date())` y `call symput`.
- Bloqueos abiertos: ninguno.

## Decisiones (hito 4)

- Si un mismo nombre de macro tiene cuerpos distintos, gana la primera definición en orden alfabético de archivo. Los casos quedan en `MacroIndex.conflicts`. Es una decisión a revisar con el usuario.
- Un `%include` externo (ruta fuera del proyecto) se conserva como paso `Include` y se registra en `unresolved_includes`. No se adivina su contenido.
- Un `%if` con condición no constante no expande ninguna de sus ramas: se marca completo como `MacroDynamic`.
- Un fragmento dinámico corta el grupo de pasos. Un DATA step que cruza un dinámico queda partido.
