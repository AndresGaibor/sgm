# Qlik DataFlow Logical Mapping Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Map the demonstrated SAS `PROC SQL` case to a local, traceable Qlik DataFlow logical graph without creating a Qlik artifact.

**Architecture:** Add one `src/sgm/qlik_dataflow.py` module that consumes `sgm.ir.models.Graph` and returns small DataFlow node/edge dataclasses. It maps only `read`, `filter`, `aggregate` and `write`; unknown operations stay visible as pending. It never reads Talend components or changes the input graph.

**Tech Stack:** Python 3.12, standard-library `dataclasses`, existing SGM IR, pytest.

**Spec:** `openspec/changes/mapear-sas-a-qlik-dataflow/specs/qlik-dataflow-mapping/spec.md`; design: `openspec/changes/mapear-sas-a-qlik-dataflow/design.md`.

## Global Constraints

- The system SHALL represent sources, filters, aggregates and targets detected by SAS analysis as linked DataFlow nodes, preserving order, demonstrated parameters and target name.
- The system SHALL mark an operation partial or pending if its compatibility depends on a type or metadata not demonstrated by SAS or local schemas, including the reason and available evidence.
- The system SHALL preserve unmapped operations as pending with reason and evidence, without dropping them or assigning an inferred processor.
- The system SHALL produce a local mapping without creating, importing, running or modifying Qlik resources and SHALL distinguish logical representation from verified generation or execution equivalence.
- No dependencies, CLI, MCP, frontend, database access, Qlik tenant calls, or changes to Talend emitters.

## Review Focus

- Missing schema for `SUM(total)` must leave the aggregate pending; the exact SQL test checks the reason and does not infer a numeric type.
- A Qlik filter processor does not prove SAS predicate equivalence; the test checks the preserved expression and partial status.
- An unknown operator with multiple incoming edges must remain pending and keep every edge; a constructed IR graph test covers this.
- An empty evidence list must not make graph conversion fail; a unit test covers this input.
- Mapping must not mutate the source `Graph`; the sample test compares its operators and edges before and after conversion.

---

### Task 1: Tests and mapper

**Files:**
- Create: `tests/unit/test_qlik_dataflow.py`
- Create: `src/sgm/qlik_dataflow.py`

**Interfaces:**
- Consumes: `sgm.ir.models.Graph`, `Operator`, `Edge`, `Evidence`.
- Produces: `DataFlowNode(id: str, kind: str, params: dict, status: str, notes: list[str], evidence: list[Evidence])`; `DataFlowEdge(src: str, dst: str, dataset: str)`; `DataFlowGraph(nodes: list[DataFlowNode], edges: list[DataFlowEdge])`; `map_graph(graph: Graph) -> DataFlowGraph`.
- Status values: `parcial` when a recognized node's SAS expression is not validated for Qlik; `pendiente` when a Qlik source/target location, required type/metadata, or processor mapping is missing. These statuses never claim execution equivalence.

- [ ] **Step 1: Write failing tests** for the required SAS query, unknown `SUM(total)` type, partial filter expression, an unmapped operator with two inputs, empty evidence, and source-graph immutability.
- [ ] **Step 2: Run `uv run python -m pytest -q tests/unit/test_qlik_dataflow.py`** and confirm the tests fail because the mapper module does not exist.
- [ ] **Step 3: Implement the dataclasses and `map_graph`** in `src/sgm/qlik_dataflow.py`. Map `read/filter/aggregate/write` to `Source/Filter/Aggregate/Target`, copy parameters and evidence, preserve IR edge order and labels, and retain all other operator kinds as pending.
- [ ] **Step 4: Run `uv run python -m pytest -q tests/unit/test_qlik_dataflow.py`** and confirm the tests pass.

### Task 2: Documentation and hito record

**Files:**
- Modify: `PROGRESS.md`

- [ ] **Step 1: Add Hito 296** with the mapper scope, Qlik NO-GO boundary, test results, metrics, and decisions; verify it follows the latest hito and does not overwrite existing entries.

### Task 3: Validation and local commit

**Files:**
- Validate only; no new source files.

- [ ] **Step 1: Run `uv run ruff check .` and `uv run python tools/ci.py`** on the final tree; record failures instead of weakening tests.
- [ ] **Step 2: Check `uv run python tools/validacion.py estado`**, confirm the validated tree is unchanged, then commit the hito locally as `hito 296: mapear SAS a Qlik DataFlow`; do not push or alter other branches.
