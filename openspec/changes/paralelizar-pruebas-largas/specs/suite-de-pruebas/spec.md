# Spec Delta

## Purpose
Define cómo se reparte la aceptación del corpus entre los workers de la suite de pruebas, para que el cierre de un hito no dependa de una sola prueba larga.

## ADDED Requirements

### Requirement: La robustez del corpus es una prueba por programa
El sistema de pruebas SHALL ejecutar la migración de cada programa de `tests/fixtures/sas` como una prueba independiente con el nombre del programa en su id, y SHALL mantener el límite de 60 s por programa y las aserciones sobre `pendientes.md` y los archivos escritos.

#### Scenario: un programa falla
- **WHEN** la migración de un programa lanza una excepción o supera 60 s
- **THEN** falla solo la prueba de ese programa y su id lo nombra

#### Scenario: faltan programas de referencia
- **WHEN** `tests/fixtures/sas` trae menos de 190 programas
- **THEN** una prueba dedicada falla con el mensaje de que los programas desaparecieron

### Requirement: Los pendientes del corpus se verifican por caso
El sistema de pruebas SHALL comprobar, para cada caso del corpus, que sus pendientes reales están en `tests/corpus/migrar_pendientes.yaml` con el mismo código, como una prueba independiente por caso.

#### Scenario: un caso con pendiente no listado
- **WHEN** un caso migra con un pendiente real y su nombre no está en la lista
- **THEN** falla la prueba de ese caso

#### Scenario: la lista guarda un caso resuelto
- **WHEN** la lista nombra un caso que ya no tiene pendientes reales
- **THEN** sigue fallando `test_la_lista_no_tiene_casos_resueltos`
