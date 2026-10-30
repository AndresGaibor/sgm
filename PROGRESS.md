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
