# Proposal

## Why

SGM ya analiza `PROC SQL` y conserva un grafo lógico, pero su salida actual se orienta a Talend. Se necesita una primera representación revisable para Qlik Cloud Analytics DataFlow sin duplicar el parser ni afirmar que ya se puede generar un flujo visual.

## What Changes

- Añadir un adaptador aislado que mapee operadores de la IR existente al grafo lógico Qlik DataFlow para el caso `Source → Filter → Aggregate → Target`.
- Conservar parámetros, aristas y evidencia SAS; marcar como parcial o pendiente lo que dependa de tipos o equivalencias no demostrados.
- Añadir pruebas sintéticas del caso obligatorio y de sus pendientes.
- Dejar fuera la creación/importación automática del lienzo y la salida Qlik Script. La primera queda NO-GO mientras no se documente una API pública que defina el grafo visual.

## Historias de usuario

### Historia 1

Como responsable de migración, quiero convertir el caso SAS de `PROC SQL` a un grafo lógico compatible con DataFlow, para revisar la estructura y sus límites antes de una generación visual.

- Criterio de aceptación: dado `CREATE TABLE ventas_resumen AS SELECT ciudad, SUM(total) AS ventas FROM ventas WHERE total > 100 GROUP BY ciudad`, el adaptador emite `Source → Filter → Aggregate → Target`, preserva el filtro, la agrupación, el agregado, su alias y el nombre de salida.
- Criterio de aceptación: cuando la entrada no demuestra el tipo de una columna requerida, el resultado la marca parcial o pendiente con motivo y no inventa el tipo.
- Criterio de aceptación: cuando un operador no tiene mapeo confirmado, se conserva en el resultado como pendiente con evidencia; no se descarta ni se traduce a un procesador supuesto.
- Criterio de aceptación: el adaptador no crea ni importa recursos Qlik y no declara equivalencia de ejecución.

## Capabilities

### New Capabilities

- `qlik-dataflow-mapping`: cubre la Historia 1; traduce el subconjunto lógico demostrado de la IR SAS a nodos, enlaces y estados de compatibilidad para DataFlow.

### Modified Capabilities

- Ninguna.

## Impact

- Un módulo nuevo `src/sgm/qlik_dataflow.py` y pruebas unitarias en `tests/unit/`.
- Reutiliza `compile_project` y los modelos `Graph`, `Operator`, `Edge` y `Evidence`; no cambia el frontend ni los emisores Talend.
- Sin dependencias nuevas, conexiones a Qlik, cambios de CLI, MCP o archivos de configuración.
- La evidencia de producto proviene de la documentación oficial vigente de Qlik DataFlow Analytics y su API pública; no se toma la API de Qlik Talend Data Integration como equivalente.
