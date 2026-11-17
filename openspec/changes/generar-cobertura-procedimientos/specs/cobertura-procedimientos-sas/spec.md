# Spec Delta

## Purpose
Documento generado que muestra, para cada procedimiento SAS del catálogo que el migrador no reconoce, su página en la guía oficial, su estado y su motivo. Sirve para revisar la cobertura sin leer el YAML y para detectar cuándo el documento ya no coincide con el catálogo.

## ADDED Requirements

### Requirement: Una fila por procedimiento no reconocido
La herramienta de generación SHALL escribir en `docs/cobertura.md` una fila por cada entrada de `rules/sas/catalogo/procs-usados.yaml` cuyo estado sea distinto de `reconocida`, y ninguna fila para las entradas reconocidas.

#### Scenario: Entradas mixtas
- **WHEN** el catálogo tiene entradas `reconocida` y entradas `no_verificada`
- **THEN** el documento tiene una fila por cada `no_verificada` y ninguna fila para las `reconocida`

#### Scenario: Catálogo sin entradas pendientes
- **WHEN** todas las entradas del catálogo están `reconocida`
- **THEN** el documento indica que no hay procedimientos sin tratamiento y no tiene filas

### Requirement: Datos tomados del catálogo sin reclasificar
Cada fila SHALL mostrar el nombre, la página de la fuente, el estado y la nota tal como están en el catálogo. La herramienta MUST NOT cambiar un estado, inventar un motivo ni omitir la página.

#### Scenario: Entrada con nota
- **WHEN** una entrada tiene `nota`
- **THEN** la fila muestra esa nota sin modificarla

#### Scenario: Entrada sin nota
- **WHEN** una entrada no tiene `nota`
- **THEN** la fila muestra el motivo como vacío, sin texto supuesto

### Requirement: Salida determinista
La herramienta SHALL producir el mismo `docs/cobertura.md` byte a byte para el mismo catálogo, con las filas en el mismo orden que el catálogo.

#### Scenario: Dos generaciones seguidas
- **WHEN** se genera el documento dos veces sin cambiar el catálogo
- **THEN** los dos archivos son idénticos

### Requirement: Verificación de documento desactualizado
Con el modo de verificación, la herramienta SHALL terminar con código distinto de cero cuando `docs/cobertura.md` no coincide con lo que generaría ahora, y con código cero cuando coincide. MUST NOT modificar el archivo en modo de verificación.

#### Scenario: Documento al día
- **WHEN** el documento coincide con el catálogo y se ejecuta el modo de verificación
- **THEN** la herramienta termina con código cero y no escribe el archivo

#### Scenario: Documento desactualizado
- **WHEN** el catálogo cambió y no se regeneró el documento
- **THEN** la herramienta termina con código distinto de cero y no escribe el archivo

### Requirement: Página citada válida
Cada fuente que aparezca en el documento SHALL tener el formato `<guía>.pdf, p. N`, como lo exige el esquema del catálogo.

#### Scenario: Fuente con formato correcto
- **WHEN** una entrada tiene la fuente `proc.pdf, p. 837`
- **THEN** la fila muestra `proc.pdf, p. 837`
