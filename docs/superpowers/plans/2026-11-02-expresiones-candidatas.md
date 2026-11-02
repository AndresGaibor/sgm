# Expresiones Talend candidatas Implementation Plan

> **For agentic workers:** ejecutar en línea este plan por tareas pequeñas; no se usa delegación.

**Goal:** guardar en el plan JSON las expresiones Java de Talend como candidatas revisables.

**Architecture:** `p10_components` conservará la salida del traductor dentro de los parámetros del operador. Las advertencias y el estado parcial existentes se mantienen.

**Tech Stack:** Python 3.12, pytest, Ruff; sin dependencias nuevas.

**Spec:** [2026-11-02-expresiones-candidatas-design.md](../specs/2026-11-02-expresiones-candidatas-design.md)

## Global Constraints

- Solo librería Python y CLI; nada de MCP, API web, frontend o base de datos.
- No afirmar tipos o equivalencias que el SAS no demuestre.
- Código e identificadores en inglés; mensajes y documentación en español.
- Después de cambios: `uv run pytest -q` y `uv run ruff check .`.

## Review Focus

- Una expresión Talend candidata conserva Java, alias de fila, columnas y advertencias en JSON.
- Expresiones inline ya soportadas no se duplican como traducciones Talend.
- Las traducciones candidatas siguen como `parcial` y requieren revisión.
- El serializador conserva el orden y estructura estable del plan salvo el nuevo campo.
- La desactivación explícita del traductor sigue dejando el hueco existente.

### Task 1: Conservar las expresiones candidatas

**Files:**
- Modify: `src/sgm/passes/p10_components.py`
- Test: `tests/unit/test_components.py`
- Update: `tests/golden/*.plan.json` y `PROGRESS.md`

**Interfaces:**
- `Operator.params["talend_expression_candidates"]` es una lista de objetos con `source`, `java`, `columns`, `warnings` y `row_context`.
- `row_context` indica que el nombre `input_row` es marcador y necesita sustituirse por el enlace Talend real.

- [x] Añadir una prueba que compile `scan(...)` y verifique contenido y advertencia de la candidata JSON.
- [x] Ejecutar la prueba nueva y confirmar el fallo esperado.
- [x] Guardar la candidata devuelta por `translate()` sin alterar el estado parcial/revisable.
- [x] Regenerar solo las referencias golden afectadas y revisar los diffs.
- [x] Ejecutar suite, Ruff, reglas y trinquete; actualizar `PROGRESS.md` y hacer commit `hito 14: conservar expresiones Talend candidatas`.
