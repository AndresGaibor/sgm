# Spec Delta

## Purpose
Define cómo se migra una biblioteca SAS que el entorno declara como base de datos, sin inventar su esquema de producción.

## ADDED Requirements

### Requirement: Una biblioteca declarada como base se lee y se escribe en su motor
Cuando `env/engines.json` declara una biblioteca en `libraries`, el migrador SHALL emitir el SQL del programa como `sql` literal en un solo componente del motor declarado y dejar la conexión como pendiente de configuración, y MUST NOT inventar columnas ni tipos que el SAS no demuestre.

#### Scenario: l2_16 con LZ declarada
- **WHEN** se migra `l2_16_sql_en_misma_base` con `LZ` declarada como `impala`
- **THEN** el Job tiene un solo componente `tImpalaRow` y el único pendiente es `P-CONEXION-BASE`, el de configuración del host y el puerto

#### Scenario: biblioteca sin declarar
- **WHEN** se migra un programa cuya biblioteca no está en `libraries`
- **THEN** el pendiente `P-OPERADOR-SIN-SOPORTE` se mantiene con su motivo

### Requirement: Los datos de prueba inventados no salen del caso
Los esquemas y filas inventados de una base sin acceso SHALL vivir solo en el caso del corpus que los usa.

#### Scenario: búsqueda de datos inventados fuera del caso
- **WHEN** se revisa `src/` y `rules/`
- **THEN** no aparece el esquema inventado de `LZ.origen`
