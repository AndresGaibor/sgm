# Proposal

## Why

El usuario decidió el 17 de noviembre de 2026 que `LZ` es una base de datos, sin acceso, y que las
pruebas usan tablas inventadas (`docs/BLOQUEOS.md`, decisiones del dueño, punto 1). Hoy `l2_16` sigue
como pendiente `P-OPERADOR-SIN-SOPORTE` solo porque `env/engines.json` no declara `LZ`. Además, la
tabla de avance (27,8 %) no acredita P6, P11, P12 ni P13 aunque hay hitos que las movieron (APPEND y limpiezas,
carpetas, cobertura por programa, rendimiento, secretos, identificadores hostiles, SBOM), así que subestima el avance real.

## What Changes

- Declarar `LZ` en `libraries` de `env/engines.json` con el motor `impala` (supuesto anotado).
- `l2_16` pasa a un solo componente (`tImpalaRow`) y un solo pendiente de configuración, `P-CONEXION-BASE`
  (como `l0_16`); se actualiza su entrada en `tests/corpus/migrar_pendientes.yaml` y en `test_pendientes_sql_l1_l2.py`.
- Recalcular `docs/plan-reescritura/creditos.yaml` con la evidencia de `PROGRESS.md` y regenerar la
  tabla 11b.

## Historias de usuario

**Como** dueño del producto, **quiero** que una biblioteca declarada como base de datos se migre sin
que el migrador invente su esquema real, **para** cerrar el bloqueo B-7 sin acceso a la base.

Criterios de aceptación:
- Con `LZ` declarada, `l2_16` migra con un solo componente y solo el pendiente de configuración `P-CONEXION-BASE`.
- El esquema inventado vive solo en el caso de prueba, nunca en `src/` ni en `rules/`.
- Sin la declaración, el migrador sigue dejando el pendiente (no se adivina el motor).

**Como** dueño del producto, **quiero** que el porcentaje de avance refleje el trabajo hecho, **para**
decidir con números reales.

Criterios de aceptación:
- Cada cambio de crédito cita el hito que lo respalda.
- `tools/avance_creditos.py --imprimir` coincide con la tabla 11b del plan.

## Capabilities

### New Capabilities
- `lz-base-de-datos`: una biblioteca declarada como base de datos se migra con `read` y `sql` literal
  en su motor (primera historia).

### Modified Capabilities

## Impact

`env/engines.json`, `tests/corpus/L2/l2_16_sql_en_misma_base/caso.yaml`, `tests/corpus/migrar_pendientes.yaml`,
`tests/unit/test_pendientes_sql_l1_l2.py`, `docs/plan-reescritura/creditos.yaml` y la tabla 11b de
`plan-migrador-general.md`. Sin Studio.
