# Spec Delta

## Purpose

Permite representar el subconjunto SAS demostrado como un grafo lógico revisable para Qlik Cloud Analytics DataFlow, con trazabilidad y pendientes explícitos antes de disponer de una vía oficial de generación visual.

## ADDED Requirements

### Requirement: Mapear la estructura lógica SQL a nodos DataFlow

El sistema SHALL representar fuentes, filtros, agregados y destinos detectados por el análisis SAS como nodos DataFlow enlazados, preservando el orden, los parámetros demostrados y el nombre del destino.

#### Scenario: Consulta con filtro y agrupación
- **WHEN** se analiza `CREATE TABLE ventas_resumen AS SELECT ciudad, SUM(total) AS ventas FROM ventas WHERE total > 100 GROUP BY ciudad`
- **THEN** el resultado contiene `Source → Filter → Aggregate → Target` con la fuente `ventas`, el filtro `total > 100`, la agrupación `ciudad`, el agregado `SUM(total) AS ventas` y el destino `ventas_resumen`

### Requirement: Conservar las dudas de esquema como pendientes

El sistema SHALL marcar como parcial o pendiente cualquier operación cuya compatibilidad dependa de un tipo o metadato que el SAS y los esquemas locales no demuestren, indicando el motivo y la evidencia disponible.

#### Scenario: Tipo de columna sin demostrar
- **WHEN** una consulta usa `SUM(total)` y no hay tipo demostrado para `total`
- **THEN** el resultado conserva el agregado y registra que su tipo de entrada debe validarse, sin asignar uno por suposición

### Requirement: Preservar operaciones sin equivalencia confirmada

El sistema SHALL conservar las operaciones para las que no exista un mapeo DataFlow confirmado como pendientes con motivo y evidencia, sin omitirlas ni asignarles un procesador por inferencia.

#### Scenario: Operador sin mapeo conocido
- **WHEN** el grafo SAS contiene una operación sin equivalencia confirmada en el catálogo DataFlow
- **THEN** el grafo lógico conserva la operación como pendiente y describe qué equivalencia falta demostrar

### Requirement: No declarar una generación visual no verificada

El sistema SHALL producir el mapeo local sin crear, importar, ejecutar ni modificar recursos Qlik y SHALL distinguir la representación lógica de una generación o equivalencia de ejecución validada.

#### Scenario: Mapeo local sin tenant Qlik
- **WHEN** se genera el grafo lógico de un programa SAS
- **THEN** no se realizan llamadas a Qlik y el resultado no se presenta como un DataFlow importado ni ejecutado
