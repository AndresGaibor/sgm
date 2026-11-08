# Plan para llevar a producción la automatización SAS → especificación Talend

Estado: **plan de trabajo**. Se basa en `01-automatizacion.md` y `02-mapa-de-flujo.md`, que son la propuesta. El estado actual del repositorio se usa solo para decidir qué quitar, qué cambiar y qué construir encima. Donde el repositorio contradice la propuesta, se cambia el repositorio.

Regla de este plan: **lo que dice la propuesta manda**. Si algo existente contradice la propuesta, se quita o se cambia, y el plan lo dice.

---

## 1. Qué es "producción" para esta herramienta

La herramienta produce guías y especificaciones. Una persona las usa para construir Jobs en Talend Studio. Por eso "producción" tiene cinco condiciones verificables:

1. **Suite verde y sin regresión:** todas las pruebas, `ruff`, y el trinquete de métricas en verde.
2. **Invariantes garantizados** en todo el corpus: trazabilidad, sin invención, determinismo, credenciales enmascaradas, cobertura de líneas.
3. **Robustez:** ningún archivo produce excepción; lo que no se entiende queda como pendiente.
4. **Guías revisadas:** cada programa del cliente tiene su guía revisada por una persona, con un acta corta.
5. **Un programa validado extremo a extremo:** se construye a mano en Studio desde la guía y se compara su salida con SAS con datos de prueba. Sin esto no se llama producción; se llama prototipo.

La condición 5 necesita un ambiente con SAS, Talend y datos. Es un requisito de salida, no de desarrollo, y se marca como dependencia externa.

---

## 2. Estado actual frente a la propuesta

Verificado el 3 de noviembre de 2026 sobre `sgm-v2`:

- Pruebas: **397 pasan, 1 se salta**. `ruff check .` limpio.
- Cambios sin confirmar en el árbol de trabajo: `metrics/baseline.json`, `src/sgm/frontend/sql_normalize.py`, `src/sgm/ir/lower_sql.py`, `tests/unit/test_sql_normalize.py` (sin seguimiento), y `docs/diseno-talend-exogena-depositos.md`. **No los toco aquí.** Hay que decidir si se confirman o se descartan (paso 0.1).

### 2.1 Lo que coincide con la propuesta

| Propuesta | Situación en el repo |
|---|---|
| Lectura por nodos y pasos con evidencia por línea (C1) | Existe (`frontend/`) |
| Expansión de macros solo en lo constante | Existe (`frontend/macros.py`), con marcado de dinámico |
| Operadores con evidencia (IR) | Existe (`ir/models.py`, `Evidence`) |
| Pasadas de fontanería, intrínsecos, particiones, componentes | Existen (`passes/p02` a `p10`) |
| Plan en JSON y guía en Markdown | Existen (`emit/plan_json.py`, `emit/guide_md.py`) |
| Explicar una línea y linaje entre programas | Existen (`explain.py`, `lineage.py`) |
| Huecos por motivo, con dueño | Existen (`rules/routing.yaml`, `sgm gaps list`) |
| Ingesta con redacción de secretos | Existe (`intake.py`, `redaction.py`) |
| Hash de reglas para caché | Existe (`cache.py`, `rules_hash`) |

### 2.2 Lo que contradice la propuesta: se quita o se cambia

| # | Qué hay hoy | Qué dice la propuesta | Acción |
|---|---|---|---|
| R1 | `passes/p08_partition.py`, `_materialize`: fija `temp_table` **sin regla**, con `supuesto: "volumen grande"` y lo deja como default | La materialización sale de hechos del linaje (lectores, entregable, frontera). No se elige en silencio | **Quitar** la asignación directa. Sustituir por la regla de materialización (sección 3.5 de este plan). Lo no decidible queda como decisión, no aplicado |
| R2 | `rules/mapping/*.yaml` (24 reglas): se elige la **primera** regla de la escalera que coincide (`p10_components.choose`) | Si dos reglas proponen valores distintos, se crea una decisión; no se elige una | **Cambiar** el motor: evaluar todas las reglas activas; conflicto → decisión. **Quitar** `choose()` como mecanismo de decisión una vez migradas las reglas |
| R3 | `decisions.py` y `plan_json.py` emiten `default` como si fuera la opción aplicada | El default es una sugerencia; no se escribe como elegido | **Cambiar**: el campo pasa a `sugerido` y el JSON marca `aplicado: false` hasta que una persona decida |
| R4 | Formato de regla `id / rung / match / emit / confidence / alternatives / tests` | Formato `cuando / produce / prioridad / casos`, con condiciones sobre hechos | **Cambiar** el formato y el esquema en `schemas/rules/`. Migrar las 24 reglas con sus casos |
| R5 | Pendientes como `Pending(options, default)` y `Gap(reason, ...)`: dos modelos distintos | Un solo modelo de pendiente: `motivo`, `dueno`, `se_cierra_con`, `nota`; valor `null` | **Cambiar**: unificar en un modelo. Los motivos se unifican con `routing.yaml` |
| R6 | Plan docs (`docs/plan-sgm-v2/`): fase 5 reactiva **MCP y web**; el prompt de fase 1 los menciona | La API y la web siguen fuera; el MCP se admite como backend opcional desde el 5 de noviembre de 2026 | **Superado:** fase 5 retirada como producto; el MCP vive en `src/sgm/backend_talend/` (hito 127m). Ver `docs/plan-sgm-v2/05-contratos.md` y `02-fases.md` |
| R7 | Carpeta `docs/plan/` citada en `00-README.md` no coincide con la real `docs/plan-sgm-v2/` | Un solo lugar para el plan | **Cambiar** la referencia o la carpeta, en un commit aparte |
| R8 | `README.md` vacío (0 bytes) | Producción necesita documentación de uso | **Cambiar**: escribir README con instalación, comandos y flujo |
| R9 | Archivos de `src/` por encima de 300 líneas (`AGENTS.md`): `talend_translator.py` 736, `expressions.py` 700, `macros.py` 478, `cli.py` 387, `steps.py` 305 | `AGENTS.md`: si un archivo pasa de 300 líneas, se divide | **Cambiar**: dividir los cinco archivos sin cambiar la salida (golden sin cambios) |

### 2.3 Lo que falta y la propuesta exige

| # | Falta | Por qué |
|---|---|---|
| F1 | Capa de **hechos** (C2) con catálogo cerrado de tipos y extractores | Sin ella, las reglas no tienen contra qué evaluar |
| F2 | **Joblets** como concepto en la IR, el plan y la guía | No aparece en el repo; la propuesta los usa para bloques repetidos |
| F3 | Evaluador de condiciones sobre hechos, con prioridad y conflictos | Reemplaza R2 |
| F4 | Residuo de bloques repetidos (`SEMANTICA_DUDOSA`) | La agrupación actual es por forma; falta explicar lo que no encaja |
| F5 | Campos por valor: `fuente`, `regla`, `confianza`, `hechos` | Requisito de trazabilidad |
| F6 | Emisor de **guía de Jobs** con la estructura de la sección 4 de este plan | Es el entregable que se quiere |
| F7 | Emisor de **mapa de flujo** (`02-mapa-de-flujo.md`) | Entender el SAS sin traducir |
| F8 | Ranking de constructos sin regla sobre el corpus | Decide qué regla escribir después |
| F9 | Pruebas de invariantes de la propuesta (sección 9 de este plan) | Garantizan lo prometido |

---

## 3. Fases

Cada tarea tiene dueño por área (núcleo, lectura SAS, Talend y entorno), criterio de terminado y dependencias. No hay fechas: se fijan al cerrar la fase 1 con el ritmo real. Las fases 1 a 4 corren en paralelo cuando no dependen unas de otras.

### Fase 0. Decisiones y limpieza

| Id | Tarea | Criterio |
|---|---|---|
| 0.1 | Decidir qué hacer con los cambios sin confirmar (baseline, `sql_normalize`, `lower_sql`, su prueba, `diseno-talend-exogena-depositos.md`) | Confirmados en commit propio o descartados por decisión explícita. **Decide el usuario** |
| 0.2 | Confirmar la versión objetivo de Talend Studio y el perfil de licencia | Una sola versión en toda la documentación. Hoy hay dos referencias: 8.0 R2026-09 (documentación del migrador) y 8.0.1 (buenas prácticas de sgm). **Decide el usuario** |
| 0.3 | Acuerdo de contratos para los cambios de `05-contratos.md`: campos por valor, hechos, joblets en el plan, modelo de pendiente, motivos | Acta corta firmada por las tres áreas |
| 0.4 | Quitar API y web de la hoja de ruta (R6); el MCP queda como backend opcional fuera del núcleo | El plan no menciona API ni web como trabajo; el MCP no es una fase de producto |
| 0.5 | Aceptar la regla: `default` es sugerencia, no decisión (R3) | Acta corta |

**Salida:** ningún cambio de código depende de una decisión abierta.

### Fase 1. Lectura y hechos (C1 y C2)

| Id | Tarea | Criterio |
|---|---|---|
| 1.1 | Invariante de cobertura: toda línea del SAS está en un nodo, un paso o una lista de líneas en blanco o comentario | Prueba en todos los fixtures; 0 líneas sin clasificar |
| 1.2 | Extractores de hechos por tipo (catálogo de la sección 4.2 de `01-automatizacion.md`), en `src/sgm/facts/` con un archivo por familia (cada uno menos de 300 líneas) | Cada hecho con archivo y líneas válidos |
| 1.3 | Enmascarado de credenciales en la capa de hechos, antes de cualquier salida | Ningún secreto en hechos, plan, guía ni mapa (prueba) |
| 1.4 | Orden estable y determinismo de hechos | Dos ejecuciones dan el mismo JSON |
| 1.5 | Pruebas con archivos hostiles: vacío, truncado, binario, codificación cp1252, CRLF, `%include` circular | 0 excepciones; cada caso sale con pendiente o hueco |

**Salida:** `sgm facts <archivo>` produce el catálogo de hechos con fuente, sin interpretación.

### Fase 2. Motor de reglas por hechos (C3)

| Id | Tarea | Criterio |
|---|---|---|
| 2.1 | Esquema nuevo de regla: `cuando` (tipo de paso, hechos, valores, relaciones del linaje), `produce`, `prioridad`, `casos` | `sgm rules validate` lo acepta; rechaza campos fuera del lenguaje |
| 2.2 | Evaluador de condiciones con lenguaje cerrado: no ejecuta código, no lee texto crudo, no consulta red | Pruebas de cada operador del lenguaje y de rechazo de los prohibidos |
| 2.3 | Conflictos entre reglas activas → decisión con las opciones y las reglas que las propusieron (R2) | Prueba `test_conflictos_de_reglas` |
| 2.4 | Migrar las 24 reglas de `rules/mapping/` al formato nuevo, con sus casos | Golden con cambios explicados regla por regla; ninguna regla sin caso |
| 2.5 | Retirar `choose()` como mecanismo de decisión cuando 2.4 esté completo | Trinquete sin regresión |
| 2.6 | Reglas de patrones de Talend como datos: caché, joblet, parámetro, contexto de ambiente, `tDBRow` para SQL de consumo único | Cada patrón con versión y caso |

**Salida:** cambiar una regla no requiere tocar `src/`; un conflicto nunca se resuelve en silencio.

### Fase 3. Especificación (C4) y joblets

| Id | Tarea | Criterio |
|---|---|---|
| 3.1 | Campos por valor en el plan: `fuente`, `regla` (id@versión), `confianza`, `hechos` (F5) | Prueba de invariante: todo valor con fuente o pendiente |
| 3.2 | Modelo único de pendiente con `motivo`, `dueno`, `se_cierra_con`, `nota` y valor `null` (R5) | Los motivos coinciden con `routing.yaml`; ningún pendiente sin dueño |
| 3.3 | Quitar la materialización silenciosa de `p08` (R1) y aplicar la regla de la sección 3.5 | Prueba `test_regla_de_materializacion` |
| 3.4 | `default` pasa a `sugerido`, con `aplicado: false` (R3) | Prueba: ninguna decisión sin valor elegido aparece como aplicada |
| 3.5 | Regla de materialización: un lector y no entregable → encadenar; dos o más lectores, entregable o frontera entre etapas → materializar; sin lectores → advertencia | Conteos reproducibles sobre el corpus |
| 3.6 | Bloques repetidos: huella por forma y diff por hechos; parámetros con tipo y valores observados; residuo como `SEMANTICA_DUDOSA` (F4) | Un bloque con residuo no se unifica |
| 3.7 | Joblets en la IR y en el plan (F2): aparecen cuando un bloque de la misma forma se repite en al menos dos sitios con al menos tres operaciones cada uno | Umbrales parametrizados en `rules/`, no en código; ver nota de investigación I.1 |
| 3.8 | Parámetros de joblet: un dataset que cambia es parámetro de tipo tabla; un reemplazo consistente de literales es un solo parámetro | Prueba con un bloque repetido de referencia |
| 3.9 | Contextos de ambiente: rama por valor → grupos `DEV`, `QA`, `PROD` con valores `pendiente` si no están en el archivo | Ningún valor de entorno inventado |
| 3.10 | Dividir los cinco archivos de más de 300 líneas (R9) | Golden sin cambios |

**Salida:** el plan contiene jobs, subjobs, joblets, componentes, contextos y pendientes, cada valor con su fuente.

### Fase 4. Guías y mapa de flujo (C5)

| Id | Tarea | Criterio |
|---|---|---|
| 4.1 | Emisor de guía de Jobs con la estructura de la sección 4 de este plan | Golden de los fixtures; revisión de una guía por una persona |
| 4.2 | Emisor de mapa de flujo (`02-mapa-de-flujo.md`) en Markdown y JSON | Entendible sin conocer Talend; cada frase con fuente |
| 4.3 | Reporte de cobertura por archivo y ranking de constructos sin regla sobre el corpus (F8) | El ranking identifica la siguiente regla a escribir |
| 4.4 | Actas de revisión de guías de los programas del cliente | Una acta por programa, firmada por quien conoce el proceso |

**Salida:** para cada programa, una guía de Jobs y un mapa de flujo revisados.

### Fase 5. Calidad y puesta en producción

| Id | Tarea | Criterio |
|---|---|---|
| 5.1 | Suite de invariantes: trazabilidad, sin invención, determinismo, credenciales, cobertura, sin nombres de cliente en `src/` ni `rules/` | Todas en verde |
| 5.2 | Métricas de la sección 10 de `01-automatizacion.md` en `sgm metrics --check` | El trinquete impide empeorar cualquier métrica |
| 5.3 | Corpus hostil: ningún archivo produce excepción | 0 excepciones |
| 5.4 | Medir tiempo y memoria del archivo más grande y del corpus; fijar límites | Límites escritos en `docs/automatizacion/` y vigilados por prueba |
| 5.5 | README con instalación (`uv sync`), comandos y flujo de un archivo nuevo | Una persona nueva lo sigue sin ayuda |
| 5.6 | Runbook de incorporación de un archivo: intake → hechos → reglas → guía → revisión | Probado con un archivo nuevo |
| 5.7 | Etiqueta de versión con el hash de reglas y de salida | Una guía declara la versión con la que se generó |
| 5.8 | Validación extremo a extremo de un programa: construcción a mano en Studio desde la guía y comparación con SAS con datos de prueba | Conteos, sumas y huellas iguales (dependencia externa, ver sección 6) |

**Salida:** versión etiquetada, con guías revisadas y un programa validado con datos.

---

## 4. Estructura de la guía de Jobs

Esta es la guía que se quiere, con la misma estructura que el documento de diseño de este caso. Se genera del plan, no a mano.

### 4.1 Orden de secciones

1. **Resumen:** programa, versión de reglas, número de jobs, joblets, componentes, pendientes por motivo.
2. **Contextos:** tabla con variable, tipo, `DEV`, `QA`, `PROD`, origen y estado (`pendiente` o valor con fuente).
3. **Jobs:** un job padre y sus hijos, con rol (orquestador, etapa, por producto, conciliación), contextos que usa, orden (`OnSubjobOk`, `OnSubjobError`) y su conteo de componentes frente al tope de 20.
4. **Joblets:** nombre, por qué se propone (apariciones y forma), parámetros, entradas, salidas, componentes, dónde se usa.
5. **Subjobs y componentes:** por subjob, tabla con componente, propósito, regla que lo propone (id@versión), confianza, fuente (líneas) y pendientes.
6. **Cachés y datos intermedios:** qué se pasa en memoria, qué se materializa y por qué (regla de materialización).
7. **Salidas:** archivos y tablas finales, con ruta o nombre, origen y pendientes.
8. **Pendientes:** lista agrupada por motivo, con dueño y `se_cierra_con`.
9. **Evidencia:** índice de archivo y líneas por cada elemento.

### 4.2 Forma de un joblet en la guía

```markdown
### jl_<nombre_propuesto>

- **Por qué se propone:** el mismo bloque de N operaciones aparece en M sitios; cambian K valores.
- **Usado en:** <job>, <job>.
- **Parámetros:** `<nombre>` (tabla de entrada), `<nombre>` (literal, valores observados: …).
- **Entradas / salidas:** …
- **Componentes:** tMap (regla X@1), tAggregateRow (regla Y@2).
- **Pendientes:** …
- **Evidencia:** archivo.sas:120-131, archivo.sas:480-491.
```

### 4.3 Reglas de redacción de la guía

- Sin datos de cliente en la plantilla; los nombres vienen del archivo fuente.
- Cada componente lleva su regla y su confianza. Nada aparece sin fuente.
- Lo que no tiene valor elegido se muestra como `pendiente`, nunca como valor probable.
- Un joblet se muestra solo si pasa el umbral; los bloques que no pasan se muestran como repetición sin joblet, con su motivo.

---

## 5. Investigación pendiente

Estas tareas no bloquean las fases 1 y 2, pero sí bloquean marcar una regla como `soportado`.

| Id | Tema | Fuente a consultar | Qué se decide |
|---|---|---|---|
| I.1 | Semántica de joblets en Talend Studio 8: diseño reutilizable en el repositorio, no Job hijo en ejecución; si se compila dentro del Job padre | Documentación oficial de joblets y de `tRunJob` en Talend Studio 8; documentación del migrador en `docs/reference/talend/tRunJob.md` y `docs/joblets.md` (antecedente, a contrastar) | Si el joblet se representa como diseño del repositorio o como Job hijo. Hoy la propuesta usa diseño del repositorio |
| I.2 | Componentes usados por las reglas: que estén activos en el perfil objetivo | `docs/reference/talend/` del migrador (fichas oficiales) y su lista de instalación opcional | Cada componente de una regla queda marcado como activo, opcional o archivado. Un componente archivado no entra en una regla soportada. Ejemplo verificado: `tUniqRow`, `tImpalaInput`, `tImpalaOutput`, `tImpalaRow`, `tImpalaLoad`, `tImpalaCreateTable`, `tImpalaConnection` son de instalación opcional |
| I.3 | Semántica SAS de cada construcción que una regla interpreta: `%if` con macro variables, `%do %to`, `PROC SQL` con pass-through (`CONNECT TO`, `EXECUTE BY`), `MERGE` con `IN=`, `PROC SORT NODUPKEY` (conserva la primera fila por clave), `PROC IMPORT` con `DBMS=EXCELCS` | Documentación oficial de SAS para lenguaje de macros y procedimientos (versión del cliente) | Cada regla de SAS cita la sección que la define. Lo que no se pueda citar queda como regla `parcial` |
| I.4 | Dialecto de Impala para lo que se empuja a la base: `WITH`, funciones de ventana (`ROW_NUMBER`), `CREATE TABLE AS SELECT`, tablas externas | Documentación de Impala de la versión del cliente | Qué SQL se puede empujar. Lo que no, queda en el flujo |
| I.5 | Orden de los `OnSubjobOk` y propagación de contextos a `tRunJob` hijos; si `tCacheOut` / `tCacheIn` ven datos de un hijo | Documentación de Talend y prueba en Studio | Si las cachés entre hijos son válidas. Si no, los insumos se cargan por hijo y la guía lo dice |
| I.6 | Comportamiento exacto de `tMap` con salida `reject` y de la "unique match" (un reporte de la comunidad dice que devuelve la última coincidencia) | Documentación de `tMap` y pruebas en Studio | Si el deduplicado se hace en la base (recomendado) o en `tMap` |

Cada investigación deja una nota en `docs/automatizacion/investigacion/` con fuente, fecha y conclusión. Una regla no pasa a `soportado` sin su nota.

---

## 6. Dependencias externas

- **Ambiente con SAS y Talend con datos de prueba** para la validación 5.8. Sin esto el resultado es prototipo.
- **Programas del cliente** con su revisión humana (tarea 4.4).
- **Decisiones de negocio** que el plan marca como `DECISION_HUMANA`; no las toma la herramienta.

---

## 7. Preguntas que necesito que decidas

1. **Versión de Talend Studio objetivo** (0.2): 8.0 R2026-09 o 8.0.1.
2. **Los cambios sin confirmar** (0.1): confirmar o descartar.
3. **Contratos** (0.3): aprobar los cambios de la sección 2.3 (F1 a F8) y R5, que tocan `05-contratos.md`.
4. **Umbrales de joblet** (3.7): propuesta de dos apariciones y tres operaciones, tomada del antecedente del migrador. ¿Se mantiene?
5. **Política de pendiente:** ¿un pendiente bloquea la guía o solo la marca? Propuesta: la guía se genera siempre; un pendiente de motivo `SECRETO`, `DECISION_HUMANA` o `LOGICA_SIN_REGLA` marca la guía como no lista para construir.

---

## 8. Riesgos

| Riesgo | Mitigación |
|---|---|
| El cambio de formato de reglas rompe las 24 existentes | Migración con casos y golden; cambios explicados regla por regla |
| Joblets que no se pueden construir en Studio como se describen | Investigación I.1 antes de la fase 3; la guía lo marca como pendiente hasta confirmarlo |
| Guías que se leen como verdad | Cada elemento lleva fuente y regla; revisión humana obligatoria antes de producción |
| Crecimiento de reglas sin control | Versión, estado, caso y hash del conjunto de reglas |
| Regresiones silenciosas al quitar `choose()` y `temp_table` | Trinquete y golden antes de cada quita |
| Archivos muy grandes lentos | Medición 5.4; límites y pruebas de rendimiento |

---

## 9. Pruebas de la propuesta

| Prueba | Garantiza |
|---|---|
| Trazabilidad de hechos | Cada hecho apunta a líneas que existen |
| Sin invención | Cada valor del plan tiene fuente o pendiente |
| Determinismo | Dos compilaciones de la misma entrada dan el mismo JSON y hash |
| Credenciales | Ningún secreto en ninguna salida |
| Sin nombres de cliente | Vigilado en `src/` y `rules/` (prueba existente, ampliada) |
| Conflictos de reglas | Dos reglas que chocan producen decisión |
| Materialización | Conteos esperados con un linaje de referencia |
| Residuo de bloques | Un bloque con diferencias no explicadas no se unifica |
| Joblets | Umbrales y parámetros con un bloque repetido de referencia |
| Golden de guías y mapas | Salida completa revisada cuando cambia |
| Robustez | Corpus hostil sin excepciones |

---

## 10. Lo que este plan no hace

- No promete equivalencia semántica; eso lo prueba la validación 5.8 con datos.
- No toma decisiones de negocio.
- No usa API ni web. El MCP es opcional y vive en `src/sgm/backend_talend/`, no en el núcleo.
- No genera Jobs dentro de Studio; genera la guía que una persona usa para construirlos.

## Estado (actualizado el 3 de noviembre de 2026)

- Fases 0 a 4: hechas. Ver `PROGRESS.md`, hitos 20 a 32.
- 3.5: hecha. La regla de materialización está en `p08_partition.sugerir_materializacion`. La frontera entre etapas se calcula entre programas (`sgm.lineage.fronteras`), se expone en el plan (`fronteras`) y en la guía. Un conjunto de frontera ya está persistido, así que no hace falta tabla temporal.
- Fase 5: hecha, salvo 5.8.
- 5.8: el procedimiento está en `05-validacion-extremo-a-extremo.md`. La comparación es `sgm comparar` (filas, sumas por columna y huella, sin depender del orden). La ejecución en SAS y Talend requiere un ambiente externo: queda pendiente hasta que se haga allí.
