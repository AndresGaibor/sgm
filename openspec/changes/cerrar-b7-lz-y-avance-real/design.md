# Design

## Context

`catalog/config.py` ya lee `libraries` (biblioteca → motor). La prueba
`tests/unit/test_pendientes_sql_l1_l2.py` clasifica `l2_16` como `entorno`. No se toca Studio.

## Goals / Non-Goals

**Goals:** cerrar B-7 con datos inventados solo de prueba; avance real en la tabla 11b.

**Non-Goals:** esquema real de `LZ`; validar en Studio; B-12, B-14 y B-20 (siguen como están).

## Decisions

- Motor `impala`: supuesto del agente (el usuario dijo «base de datos»). Se cambia en una línea.
- No hace falta esquema inventado: el SQL pasa literal a la base y no se necesitan columnas.
- Pocos componentes: el `read` más `sql` literal es un solo componente de entrada; no se añade nada.

## Ingeniería

- Descartado: declarar `LZ` solo en la prueba (el producto no la vería); inventar columnas en el
  código (regla 6 de `AGENTS.md`).
- Riesgo: `env/engines.json` es global: declarar `LZ` puede cambiar otros casos que usen `LZ`. El paso 1.6 lo
  comprueba con las pruebas de la lista y manda parar si cambia más de `l2_16`.
- Verificado el 17 de noviembre de 2026 sobre `main` con los hitos de Byron: no hace falta tocar `src/`.
- Frontera con `src/sgm/backend_talend/`: no se toca.

## Pruebas

- `uv run python -m pytest -q tests/unit/test_pendientes_sql_l1_l2.py tests/unit/test_migrar_corpus_aceptacion.py -k "solo_los_casos or la_lista_no_tiene"`.
- Cierre: `uv run ruff check .` y `uv run python tools/ci.py`.

## Risks / Trade-offs

Los créditos son un juicio: cada cambio cita su hito para que sea revisable.
