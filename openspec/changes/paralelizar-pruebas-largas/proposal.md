# Proposal

## Why

La suite completa tarda 202 s (medido el 17 de noviembre de 2026 con `--durations=25`, 4584 pasan).
Dos pruebas de `tests/unit/test_migrar_corpus_aceptacion.py` recorren el corpus dentro de un `for`:
`test_robustez_sobre_todo_el_repositorio` (89,7 s) y `test_solo_los_casos_listados_tienen_pendientes`
(76,0 s). `xdist` reparte pruebas, no iteraciones de un bucle, así que cada una ocupa un solo worker
y fija el piso del tiempo total. El objetivo del usuario es que cada cierre de hito sea lo más rápido
posible.

## What Changes

- `test_robustez_sobre_todo_el_repositorio` pasa a una prueba parametrizada por programa de
  `tests/fixtures/sas`; la comprobación «hay al menos 190 programas» queda en una prueba propia.
- `test_solo_los_casos_listados_tienen_pendientes` pasa a una prueba parametrizada por caso del corpus.
  La comprobación inversa (la lista no guarda casos resueltos) ya la hace
  `test_la_lista_no_tiene_casos_resueltos`.
- No cambia ninguna aserción ni se relaja ningún umbral (límite de 60 s por programa incluido).

## Historias de usuario

**Como** desarrollador del migrador, **quiero** que las pruebas largas del corpus se repartan entre los
workers, **para** que el cierre de hito (`tools/ci.py`) tarde menos.

Criterios de aceptación:
- Cada programa de `tests/fixtures/sas` es una prueba con id propio; un fallo dice cuál.
- Cada caso del corpus es una prueba con id propio para la lista de pendientes.
- Si desaparecen programas de referencia (menos de 190), una prueba falla.
- La suite completa mide menos de 202 s en este equipo y las mismas aserciones siguen en pie.

## Capabilities

### New Capabilities
- `suite-de-pruebas`: la aceptación del corpus se reparte por caso entre los workers de `xdist`
  (cubre la historia anterior).

### Modified Capabilities

## Impact

Solo `tests/unit/test_migrar_corpus_aceptacion.py`. Sin cambios en `src/`, `rules/` ni backend de Talend.
