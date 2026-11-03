# INPUT con informat dinámico Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Evitar que `INPUT` con informat no resuelto emita una conversión numérica candidata y mantener la traducción como pendiente con evidencia.

**Architecture:** El módulo público `talend_translator` conservará `translate_to_talend`, `Unsupported` y `Result`. El lexer, parser, tipos/ayudantes y funciones SAS se dividirán por responsabilidad en módulos pequeños; el constructor de `INPUT` rechazará formatos que no sean literales.

**Tech Stack:** Python 3.12, pytest, Ruff; sin dependencias nuevas.

**Spec:** [2026-11-03-input-informat-dinamico-design.md](../specs/2026-11-03-input-informat-dinamico-design.md)

## Global Constraints

- Solo librería Python/CLI y artefactos Markdown/JSON; nada de MCP, API web, frontend ni conexiones a bases.
- Los esquemas se leen del JSON local; no se inventan tipos ni equivalencias.
- Los ejemplos del cliente se analizan en memoria después de redacción; nunca se copian a `src/`, `rules/` o pruebas.
- No se guardan secretos; los literales de `PROC PWENCODE` se sustituyen por `'***'` antes del análisis.
- No se agregan dependencias fuera de `networkx`, `typer`, `pyyaml`, `pydantic` opcional y las herramientas de desarrollo permitidas.
- Cada módulo nuevo queda por debajo de 300 líneas. Tras el cambio se ejecutan `uv run pytest -q` y `uv run ruff check .`.
- El cierre registra fecha, cambios, pruebas, métricas, bloqueos y decisiones en `PROGRESS.md`; el commit usa `hito N: <resumen>`.

## Files

- Create `src/sgm/expressions/talend_core.py`: `Unsupported`, `E`, `Result` y ayudantes de semántica Java comunes.
- Create `src/sgm/expressions/talend_lexer.py`: patrón de tokens y `tokenize(text: str) -> list[tuple[str, str]]`.
- Create `src/sgm/expressions/talend_parser.py`: parser de expresiones `ExpressionParser`, que recibe tokens, nombre de conexión y registro de funciones.
- Create `src/sgm/expressions/talend_functions_strings.py`: constructores de funciones de texto.
- Create `src/sgm/expressions/talend_functions_numeric.py`: constructores aritméticos, agregados y matemáticos.
- Create `src/sgm/expressions/talend_functions_dates.py`: informats/formatos y funciones de fecha, incluido `_input`.
- Create `src/sgm/expressions/talend_functions.py`: registro único que asocia nombres SAS con sus constructores.
- Modify `src/sgm/expressions/talend_translator.py`: fachada compatible con la interfaz actual.
- Create `tests/unit/test_input_informat.py`: regresiones unitarias y de compilación con fuentes SAS sintéticas.
- Modify `PROGRESS.md`; modify `metrics/baseline.json` solo si `metrics --check` exige aceptar la nueva clasificación de candidatos dinámicos como huecos.

## Review Focus

- Informat de macro aún dinámico: `input(value, &informat)` no produce Java y se registra como hueco `FUNCION_NO_MAPEADA` en la línea SAS original. Test: `test_dynamic_macro_informat_is_unsupported` y `test_dynamic_informat_compiles_as_gap_without_candidate`.
- Informat identificado por columna: `input(value, informat)` queda pendiente. Test: `test_column_informat_is_unsupported`.
- Informat calculado: una expresión de texto como `cats('best', '32.')` no se confunde con un literal. Test: `test_computed_informat_is_unsupported`.
- Informat literal de fecha ya reconocido: conserva su candidato actual. Test existente: `test_fechas_usan_talenddate`.
- Informats literales numérico y de carácter: mantienen el resultado actual. Tests: `test_literal_numeric_informat_keeps_current_candidate` y `test_literal_character_informat_keeps_current_result`.
- Macro que se resuelve a un literal antes de traducir: conserva la expresión expandida y el motor inline la traduce con el mapeo de fecha existente, sin crear un hueco `FUNCION_NO_MAPEADA`. Test: `test_macro_informat_resuelto_a_literal_sigue_traduciendose`.

---

### Task 1: Modularizar el traductor y rechazar informats dinámicos

**Files:**
- Create: `src/sgm/expressions/talend_core.py`
- Create: `src/sgm/expressions/talend_lexer.py`
- Create: `src/sgm/expressions/talend_parser.py`
- Create: `src/sgm/expressions/talend_functions_strings.py`
- Create: `src/sgm/expressions/talend_functions_numeric.py`
- Create: `src/sgm/expressions/talend_functions_dates.py`
- Create: `src/sgm/expressions/talend_functions.py`
- Modify: `src/sgm/expressions/talend_translator.py`
- Create: `tests/unit/test_input_informat.py`
- Modify: `PROGRESS.md`
- Modify only if required by the measured reclassification: `metrics/baseline.json`

**Interfaces:**
- `translate_to_talend(sas: str, entrada: str = "input_row") -> Result` remains importable from `sgm.expressions.talend_translator`.
- `Unsupported`, `Result` and `E` remain re-exported from that module for compatibility.
- `ExpressionParser(tokens, entrada, functions)` parses tokens using the supplied `functions` mapping; function modules depend on `talend_core`, not on the facade.
- `_P.raw_format` accepts one literal token of type `fmt` or `str`, or one numeric token matching `\d+\.\d*` for a numeric SAS informat such as `10.`. A macro, column, integer without an informat dot, or multi-token expression raises `Unsupported` before it can be converted into a string literal. `_input` keeps its current mappings for literal informats.
- Static numeric informat behavior and recognized date/character literal behavior remain unchanged in this hito.

- [x] **Step 1: Add failing direct and integration tests** in `tests/unit/test_input_informat.py`.

```python
import pytest

from sgm.compile import compile_project
from sgm.expressions.expressions import translate
from sgm.expressions.talend_translator import Unsupported, translate_to_talend


def test_dynamic_macro_informat_is_unsupported():
    with pytest.raises(Unsupported, match="informat"):
        translate_to_talend("input(value, &informat)")


def test_column_informat_is_unsupported():
    with pytest.raises(Unsupported, match="informat"):
        translate_to_talend("input(value, informat)")


def test_computed_informat_is_unsupported():
    with pytest.raises(Unsupported, match="informat"):
        translate_to_talend("input(value, cats('best', '32.'))")


def test_literal_numeric_informat_keeps_current_candidate():
    result = translate_to_talend("input(value, 10.)")
    assert result.java == (
        "(input_row.value == null ? null : "
        "Mathematical.REAL(StringHandling.TRIM(input_row.value)))"
    )
    assert any("input numérico" in warning for warning in result.warnings)


def test_literal_character_informat_keeps_current_result():
    assert translate_to_talend("input(value, $char10.)").java == "input_row.value"


def test_dynamic_informat_compiles_as_gap_without_candidate():
    plan = _plan("data target; set source; parsed=input(value, &informat); run;")
    operator = _derive_for(plan, "parsed")
    assert "talend_expression_candidates" not in operator.params
    assert any(g.reason == "FUNCION_NO_MAPEADA" for g in plan.gaps)


def test_macro_informat_resuelto_a_literal_sigue_traduciendose():
    plan = _plan(
        "%let fmt = yymmdd10.; data target; set source; parsed=input(value, &fmt); run;"
    )
    operator = _derive_for(plan, "parsed")
    expression = operator.params["assignments"][0]["expression"]
    assert expression == "input(value, yymmdd10.)"
    result = translate(expression)
    assert result.engine == "inline"
    assert "TalendDate.parseDate(" in result.talend
    assert not any(gap.reason == "FUNCION_NO_MAPEADA" for gap in plan.gaps)


def _plan(source):
    compiled, _ = compile_project({"program.sas": source})
    return compiled["program.sas"].plan


def _derive_for(plan, target):
    return next(
        operator
        for operator in plan.graph.operators()
        if operator.kind == "derive"
        and any(assignment["target"] == target for assignment in operator.params["assignments"])
    )


```

- [x] **Step 2: Verify RED** with `uv run pytest -q tests/unit/test_input_informat.py`; the unresolved cases must fail because the current translator emits a numeric `Mathematical.REAL` candidate.
- [x] **Step 3: Move the existing code by responsibility** into the listed core, lexer, parser, function-family and registry modules. Keep existing expressions and output byte-for-byte equivalent. In the parser, make `raw_format` accept one `fmt` or `str` token, or one `num` token matching `\d+\.\d*`; otherwise raise `Unsupported` without including its source value. The facade delegates parsing to `ExpressionParser` with the shared function registry.
- [x] **Step 4: Verify the refactor and behavior** with `uv run pytest -q tests/unit/test_talend_translator.py tests/unit/test_input_informat.py`; all current literal cases and new pending cases must pass.
- [x] **Step 5: Recompile the second supplied example in memory** through `compile_batch` (which redacts before analysis). Verify the four `INPUT` expressions remain literal numeric informats and preserve the baseline of 21 candidates and 21 gaps. Report only these aggregate classifications/counts; do not write source or derived example files.
- [x] **Step 6: Run project verification** with `uv run pytest -q`, `uv run ruff check .`, `uv run sgm rules validate`, and `uv run sgm metrics tests/fixtures/sas --check`. If the intentional reclassification raises `FUNCION_NO_MAPEADA`, update only that baseline count with the reason in `PROGRESS.md`, then rerun the metric check.
- [x] **Step 7: Update `PROGRESS.md`** with the hito date, implementation summary, test/Ruff/rules/metrics results, candidate-to-gap change, blockers, and the decision to keep dynamic informats pending.
- [x] **Step 8: Commit** the completed hito with `git commit -m "hito 20: dejar INPUT con informat dinámico pendiente"`.
