# Design

## Context

See `proposal.md` for motivation and `specs/qlik-dataflow-mapping/spec.md` for required behavior. `compile_project` currently produces an IR graph with `read`, `filter`, `aggregate` and `write` for the sample query. The current `Operator.status` and `Operator.component` belong to the Talend flow, so they cannot certify Qlik compatibility. No official public contract for creating the Analytics DataFlow processor graph was found in the reviewed Qlik API references.

## Goals / Non-Goals

**Goals:**

- Add a library-only adapter from the existing IR graph to a Qlik DataFlow logical graph.
- Preserve node order, connections, parameters, and source evidence.
- Keep target compatibility independent from Talend component selection and status.

**Non-Goals:**

- Create or import a Qlik app or visual flow, edit `.dfw`, call a tenant, or use UI automation.
- Translate SAS expressions beyond what the existing IR proves.
- Add a CLI, MCP server, dependencies, schemas, frontend, or a Qlik Script emitter.

## Decisions

1. **Consume `compile_project` IR.** Map `read` to `Source`, `filter` to `Filter`, `aggregate` to `Aggregate`, and `write` to `Target`. Keep IR operator IDs for this in-memory result and convert IR edges without reordering, preserving their dataset labels. Do not propagate `Edge.materialize`, which is a backend placement choice. Other operator kinds remain visible as pending nodes. A separate SAS parser or an adapter over Talend `.item` components would duplicate logic or bind the new target to Talend.
2. **Return target-specific status and reasons.** Do not copy `Operator.status` or inspect `Operator.component`; those are Talend-specific. A mapped filter is partial while its SAS expression remains unvalidated; source/target are pending while a Qlik connection or target location is unknown; aggregate is pending when an input type is unknown. Preserve `Evidence` on mapped and pending nodes.
3. **Use small standard-library data classes.** Keep the mapping data in the form provided by the IR and avoid Pydantic or other new dependencies. The adapter must not modify the input graph.
4. **Treat logical mapping and artifact generation as separate capabilities.** Qlik help documents the visual source/processor/target model and `.dfw` export/upload, while the public Apps API only documents app operations and the `DATAFLOW_PREP` usage value. That does not document how to create or validate the processor graph. Qlik Talend Data Integration project APIs are a separate product and are not used as a substitute.

## Risks / Trade-offs

- [IR changes for Talend] → Isolate mapping code in `src/sgm/qlik_dataflow.py` and test it against operator kinds and parameters, not Talend components.
- [Unknown source types] → Preserve the logical operation but mark numeric aggregate compatibility pending with its evidence; never infer a type from synthetic test values.
- [No public graph API] → Keep the result as a reviewable local graph and do not expose it as an importable Qlik artifact.
- [SAS filter syntax differs from Qlik expressions] → Preserve the SAS/IR expression and mark it partial until a documented equivalence is established.

## Migration Plan

No deployment or data migration is needed. The adapter is additive and does not alter the Talend compiler. Rollback consists of removing the new package and its tests.

## Ingeniería

- **Alternativas:** crear un parser paralelo se descartó porque `compile_project` ya conserva el grafo y la evidencia; emitir `.dfw` o usar endpoints observados en la interfaz se descartó porque falta un contrato oficial para el grafo; Qlik Script se excluyó según la decisión del usuario.
- **Dependencias:** solo la IR existente y la biblioteca estándar. No se añade cliente HTTP ni SDK de Qlik.
- **Frontera Talend:** el módulo nuevo no importa `sgm.talend_item` ni `sgm.backend_talend`; no lee `Operator.component` ni emite `.item`.
- **Riesgos:** los tipos desconocidos y las expresiones no demostradas quedan parciales o pendientes; el resultado lógico no certifica importación ni equivalencia de ejecución.

## Pruebas

- Una prueba unitaria con `compile_project` sobre el SAS obligatorio verificará cuatro nodos y tres enlaces en orden, el predicado, grupo, agregado/alias y destino.
- Pruebas unitarias comprobarán que un tipo de columna ausente genera estado pendiente con evidencia, que un operador sin mapeo se conserva y que el grafo de entrada no se modifica.
- Verificación del cambio: `uv run python -m pytest -q tests/unit/test_qlik_dataflow.py` y `uv run ruff check .`.
- Cierre del hito: `uv run python tools/ci.py`, según `AGENTS.md`; el resultado se registra en `PROGRESS.md` antes del commit local.
