# Fase 0: auditoría de reuso para la reescritura del centro

Fecha: 2026-11-04. Alcance: solo lectura de `src/`, `tests/` y `rules/`. Este es el único archivo escrito.

Arquitectura destino: frontend -> grafo de linaje de datasets -> modelo de proceso (fuentes, salidas, etapas, parámetros por producto, validaciones, pendientes) -> emisores (diseño en Markdown, Job Script de Talend, mapa de flujo).

## 0. Cómo se hizo y qué no se pudo verificar

Verificado leyendo código y ejecutando experimentos de solo lectura (sin escribir en el repo):

- Lectura de los módulos pedidos, sus importaciones cruzadas (`grep` de `from sgm...`) y la cabecera de cada pasada.
- `pytest --collect-only`: 636 pruebas en 67 archivos de `tests/unit` (coincide con PROGRESS: 629 pasan, 1 salta, 6 xfail).
- Experimentos con `facts_for_project`, `build_flows`, `match_plumbing` y `sql_tree.build` sobre texto sintético y sobre `client_poc.sas` y `client_large.sas`.

No verificado:

- No corrí la suite completa ni medí cobertura de líneas (no hay `pytest-cov` en el proyecto). "Cobertura" aquí significa qué archivos de prueba importan o ejercitan el módulo, por importaciones y `grep`. Es una aproximación.
- El reparto de pruebas "mixtas" (sección 4) usa una heurística: busca `compile`, `Store` o `invoke` dentro del cuerpo de cada prueba. Puede errar en unas pocas.
- No existe `.codegraph/` en el repo, así que no usé CodeGraph. Todo salió de `grep` y lectura directa.
- No leí línea por línea p05, p06, p07, p08, p09, p10, `ir/lower_*`, `expressions_*` ni `talend_*`. De esos módulos audité cabecera, API y acoplamientos, no cada regla de negocio.
- Durante la auditoría el árbol de trabajo cambió: `src/sgm/flow/*` y `tests/unit/test_flujo_salidas.py` aparecen modificados y hay un `src/sgm/flow/estilo.py` nuevo. No fue obra mía. Mi lectura de `flow/model.py` (sin cambios en `git status`) es consistente, pero `layout`, `page`, `salida` y `seccion` pueden haber cambiado después de que los leí.
- `src/sgm/passes/region.py` tiene cambios sin confirmar (memoización en `grow`). Hay que conservarlos si se reusa.
- `pyproject.toml` declara `sqlglot` y `jsonschema`, que no están en la lista de dependencias permitidas de `AGENTS.md`. No busqué si quedaron anotadas en "Decisiones".

## 1. Tabla resumen

Tamaños en líneas de `src/sgm`. Total del paquete: unas 14.900 líneas.

| Módulo | Líneas | Veredicto | Resumen |
|---|---:|---|---|
| `frontend/` (lexer, macros, steps, datastep, sql, sql_normalize, selectors, splitter, program) | 2.117 | CONSERVAR | Es la base. `grid.py` (212) está muerto: TIRAR. |
| `facts/` (model, structural, textual, project, mapa) | 769 | ADAPTAR | Sirven para lo externo (rutas, servidores, credenciales, conexiones). No bastan para el linaje. `mapa.py` se reemplaza por el emisor nuevo. |
| `flow/model.py` + `salida.py` | ~450 | ADAPTAR (semilla del linaje) | Ya es un grafo paso-dataset construido directo del frontend. Tiene huecos concretos. |
| `flow/layout.py`, `page.py`, `seccion.py` | ~430 | CONSERVAR como emisor del mapa de flujo | Hoy leen `FlowModel`; habría que alimentarlos del grafo nuevo. En edición concurrente. |
| `ir/models.py`, `builder.py`, `lower*.py`, `proc_rules.py`, `signature.py` | ~1.200 | TIRAR | Son la IR por operador. |
| `ir/sql_tree.py`, `sql_render.py`, `sql_semantics.py`, `sql_portability.py`, `types_code.py` | ~690 | ADAPTAR (mover) | Piezas puras sin `ir.models`. Útiles para columnas, tipos y SQL de base. Se mueven fuera de `ir/`. |
| `passes/p01_graph` | 86 | TIRAR | Su idea (aristas por dataset con versión `@vN`) pasa al linaje. |
| `passes/p02_plumbing` + `plumbing_patterns` + `rules/sas/plumbing.yaml` | 138+60 | ADAPTAR | Los patrones se conservan. La pasada no: está soldada a `Operator`, `Plan` y `NotMigrated`. |
| `passes/p03_intrinsics` + `region.py` | 135+293 | ADAPTAR (`region.py`), TIRAR p03 | La detección de la región de carga es útil. Está escrita sobre `Operator`. |
| `passes/p04_placement`, `db_push`, `db_sql` | 168+166+136 | TIRAR | Decisión base de datos o flujo sobre operadores. |
| `passes/p05_sql_fusion` | 149 | TIRAR | Fusión de operadores en CTE. |
| `passes/p06_flow_fusion` | 172 | TIRAR | Fusión a `tMap`. |
| `passes/p07_templates` | 299 | TIRAR (la idea migra) | Plantillas por forma de subgrafo. Lo reemplaza la agrupación por producto. |
| `passes/p08_partition` | 171 | TIRAR | Subjobs y materialización sobre el grafo de operadores. |
| `passes/p09_schemas` | 150 | TIRAR | Propagación de esquemas por operador. `types_code` se conserva aparte. |
| `passes/p10_components`, `reglas_mapeo`, `join_match` | 200+158+108 | TIRAR (las 24 reglas YAML se reescriben) | Son la escalera de componentes por operador. |
| `expressions/` | 1.542 | CONSERVAR | Funciones puras de cadena a cadena, sin IR. Hay dos traductores solapados. |
| `ingest/` | 226 | CONSERVAR | Importación segura de carpeta o ZIP. |
| `store/` | 288 | ADAPTAR | `db.py` es genérico. `gaps.py` y `overrides.py` dependen de `Plan`. |
| `catalog/` | 614 | CONSERVAR (con un cambio en `schemas.py`) | Configuración de entorno, esquemas y catálogo de componentes. |
| `emit/guide_md.py`, `emit/plan_json.py` | 488 | TIRAR | Renderizan `Plan` y `Operator`. |
| `emit/conventions/naming.py` | 59 | CONSERVAR | Nombres de Jobs. |
| `emit/conventions/best_practices.py`, `context_rules.py`, `infra.py` | ~400 | TIRAR o rescatar `context_rules` | Nadie los importa y ninguna prueba los ejercita. |
| `redaction.py` | 48 | CONSERVAR | Intacto. |
| `decisions.py` | 48 | ADAPTAR | Agrupa `plan.pending` por firma. |
| `rules_validate.py` + `schemas/rules/` | 136 | CONSERVAR | Valida cualquier YAML de reglas. |
| Cargador de `rules/` (varios) | disperso | Ver sección 2.16 | Cada cargador sigue a su consumidor. |
| `agrupacion.py` | 153 | CONSERVAR | Solo depende de `facts.model`. |
| `generador.py`, `diseno.py` | 309+32 | ADAPTAR | Mitad hechos, mitad operadores del plan. |
| `lineage.py` | 73 | TIRAR | Linaje entre programas calculado desde operadores. Lo cubre el grafo nuevo. |

## 2. Auditoría por módulo

### 2.1 `frontend/` (2.117 líneas) - CONSERVAR

Responsabilidad real: `lexer.split_statements` corta en sentencias respetando comillas y comentarios. `macros*.py` indexa y expande macros con evaluación parcial; lo no constante sale como `MacroDynamic`. `steps.py` y `datastep.py`, `sql.py` agrupan en `DataStep`, `ProcSql`, `Proc`, `MacroDef`, `Libname`, etc. `splitter.py` separa nodos por etiqueta de SAS Studio. `selectors.py` detecta macros de ambiente. `sql_normalize.py` prepara SQL de SAS para `sqlglot`. `program.analyze_program` une todo y devuelve `ProgramAnalysis.items`: cada `ProgramItem` lleva `file`, `label` (nodo), `item` (el paso), `line` y `call` (la invocación de macro más externa, `archivo:línea:nombre`).

API que usaría el modelo nuevo:

- `analyze_program(files, externals)` y `ProgramItem`.
- Tipos de paso de `steps_tipos.py`.
- `DsStatement.fields["sources"]` (con `in=`) para `set` y `merge`.
- `SqlStatement.target`, `.sources`, `.engine`, `.inner_sql`.
- `macro_index.PathIndex` para casar `%include`.

Acoplamientos: ninguno a la IR ni a Talend. El único importador inverso es la propia capa de análisis. Es el módulo mejor aislado del repo.

Problemas reales (verificados):

- `sql.py` extrae fuentes con la regex `\b(?:from|join)\s+([\w.&]+)`. Para `select extract(year from fecha), trim(both from n) from b left join c` devuelve `('fecha','n','b','c')`: dos fuentes falsas. Con `from (select * from b) x, c` devuelve solo `('b',)` y pierde `c`, porque la coma no cuenta como join.
- `sql_tree.build` (en `ir/`) es exacto para consultas planas (`from b x, c` da `b` y `c`) pero lanza `SqlNotSelect("origen que no es una tabla")` ante una subconsulta en `FROM`.
- `datastep.classify_statement` no registra `infile`, `file` ni `put` como lecturas o escrituras externas; solo marca el tipo.
- `grid.py` (212 líneas, `shell_tasks`) no lo importa nada ni lo prueba ninguna prueba (`grep` sobre `src` y `tests`). Código muerto.

Tamaño: ninguno pasa de 300 líneas (el mayor, `sql_normalize.py`, tiene 293).

Cobertura: `test_frontend.py` (18), `test_macros.py` (12), `test_entrada_sas.py` (13, lexer y redacción), `test_selectors.py` (5 de 7 sin compilar), `test_sql_normalize.py` (unas 19 de 21 sin compilar), `test_catalogo_sas.py` (27, sobre lo que el parser reconoce). Alrededor de 95 pruebas, todas independientes del pipeline. `grid.py` sin ninguna.

### 2.2 `facts/` (769 líneas) - ADAPTAR

Responsabilidad real: `facts_for_project` redacta, analiza y devuelve por archivo una lista de `Fact` (21 tipos cerrados). Importante: los pasos salen **del texto sin expandir** (`parse_steps(split_statements(texto))`, incluyendo cuerpos de `%macro`), no de `analysis.items`. Solo los `MacroDynamic` y los selectores vienen del análisis. Cada hecho tiene `nodo` (etiqueta de nodo), líneas y `detalle`.

API útil: `Fact`, `TIPOS`, `alcance_de`, `facts_for_project`. Los hechos `archivo_externo`, `ruta_literal`, `servidor`, `conexion_base`, `credencial`, `biblioteca`, `macro_llamada` (con `args`), `variable_constante` son buenos insumos para fuentes, salidas y parámetros.

Acoplamientos: `facts/project.py` importa `sgm.compile.project_base` (para leer los archivos externos). Es un acoplamiento al módulo del pipeline viejo por una sola función. `facts/mapa.py` produce el Markdown viejo.

Veredicto: conservar `model.py`, `structural.py`, `textual.py`. Mover `project_base` a un módulo de entorno. Retirar `mapa.py` cuando exista el emisor nuevo.

Cobertura: `test_facts.py` (11), `test_mapa_flujo.py` (4), `test_agrupacion.py` (3), `test_generador.py` (parcial). Medición: `client_large.sas` da 9.210 hechos en 2,1 s.

### 2.3 `flow/` (885 líneas) - ADAPTAR `model.py`, CONSERVAR el resto

Responsabilidad real: `build_flow` recorre `analysis.items` en orden y arma `FlowStep` (con `reads`, `writes`, `label`, `macro_call`, `kind`) y `FlowEdge` (productor -> consumidor por dataset). Un dataset leído sin productor anterior es una entrada externa. `salida.indice_datasets` responde "quién escribe y quién lee X". `page.py`, `layout.py`, `seccion.py` dibujan HTML con SVG en línea (hito 43).

Esto **ya es un grafo de linaje de datasets** construido directamente del frontend, sin IR. Es la mejor semilla para el nodo central del pipeline nuevo.

Acoplamientos: `model.py` importa solo `frontend.*` y `redaction`. Los otros tres archivos solo dependen de `flow.model`. Ninguno toca IR ni Talend.

Medición en `client_large.sas`: 2.205 pasos, 1.226 aristas, 6 entradas externas, 0,9 s. En `client_poc.sas`: 310 pasos, 69 aristas.

Huecos verificados (detalle en la sección 3.1): `PROC APPEND base=` no cuenta como escritura (probado: `work.tot` aparecería como entrada externa); `infile`, `proc import datafile=` y `proc export outfile=` no generan lecturas ni escrituras; las fuentes dentro de un pass-through no entran; las fuentes de SQL vienen de la regex mala del frontend.

Cobertura: `test_flujo.py` (11) y `test_flujo_salidas.py` (15, esta última modificada ahora mismo en el árbol de trabajo).

### 2.4 `ir/` (2.000 líneas) - TIRAR el núcleo, rescatar cinco piezas

Tirar: `models.py` (`Operator`, `Edge`, `Graph`, `Plan`, `Job`, `Gap`, `Pending`), `builder.py`, `lower.py`, `lower_data.py`, `lower_procs.py`, `lower_sql.py`, `lower_sql_flow.py`, `proc_rules.py`, `signature.py`. Todo gira en torno a `Operator` por sentencia y a sus 23 tipos. `proc_rules.py` carga `rules/sas/procs/*.yaml`, cuyas reglas emiten operadores de la IR.

Rescatar y mover (no importan `ir.models`; lo comprobé con `grep`):

- `sql_tree.py` (188): `build(sql)` devuelve `SqlTree` con fuentes, uniones (claves del `ON`), filtros, agregados. Es exacto en consultas planas y falla en subconsultas de `FROM`. Útil para el linaje de columnas y para validar uniones.
- `sql_render.py` (65): SQL dialecto Hive para Impala.
- `sql_semantics.py` (72): lee `rules/sas/sql-semantica.yaml`.
- `sql_portability.py` (73): funciones portables de `rules/sas/sql-functions.json`.
- `types_code.py` (190): tipos que el código SAS demuestra; lee `rules/sas/informats.yaml`.

Cobertura: `test_ir_rules.py` (21) y `test_sql_*` ejercitan el lowering. Las pruebas de `sql_tree`, `sql_render` y `sql_normalize` (`test_sql_render.py` 5, buena parte de `test_sql_normalize.py` y `test_sql_flujo.py`) protegen lo rescatable. `test_tipos_codigo.py` (11) pasa por `compile`, así que hay que reescribirla contra `types_code` directo.

### 2.5 `passes/p01_graph` (86) - TIRAR

Construye aristas entre operadores por nombre de dataset, con versión `@vN` cuando se reescribe, y añade `write` finales. La idea de versionar por reescritura es correcta y falta en `flow/model.py` (que une siempre al último productor, sin nombre de versión). Se reimplementa en el linaje nuevo. Cobertura: `test_passes.py` (11, vía `compile`).

### 2.6 `passes/p02_plumbing` + `plumbing_patterns.py` (138+60) - ADAPTAR

Responsabilidad real: `classify(op)` decide si un operador es fontanería con 19 patrones de `rules/sas/plumbing.yaml` y con `_work_cleanup` (`proc delete` o `proc datasets` sobre WORK). `mark` anota `op.status="reemplazado"` y `plan.not_migrated`. `_report` aplica la política `reports` (`discard`, `log`, `csv`) mutando el operador. `remove_marked` lo quita del grafo. La respuesta a la pregunta 2 está en la sección 3.2.

Cobertura: `test_plumbing_categorias.py` (39), `test_plumbing_yaml.py` (12) ejercitan `plumbing_patterns` sin pipeline. Protegen lo que se conserva.

### 2.7 `passes/p03_intrinsics` + `region.py` (135+293) - ADAPTAR `region.py`, TIRAR p03

Responsabilidad real: reconocer por estructura (no por nombre) la región de carga externa: un paso lanza comandos en segundo plano (`... &"`), otro espera con `until` y `wc -l`, y la región crece hacia atrás y hacia delante por la maquinaria vecina, según qué macro variables y datasets define y usa cada paso. Luego p03 reemplaza el bloque por un `external_load`.

`region.py` es un algoritmo de definiciones y usos (`FactBook`, `Flow.live_users`, `absorbable`, `units`, `grow`) que da el concepto de "región o macro de origen" que el linaje necesita. Su acoplamiento es estrecho pero poco profundo: solo `FactBook._compute(op)` lee `op.params` y `p02_plumbing.op_text(op)`. Si se sustituye `Operator` por un registro de paso con texto, entradas, salidas, `call` y bandera de fontanería, el resto funciona igual.

Cuidado: tiene cambios sin confirmar en el árbol de trabajo (memoización de `back_ok` y `forward_ok`). Conservar.

`rules/sas/intrinsics/external-load.yaml` declara `implementation: sgm.passes.p03_intrinsics._external_load`, y `test_intrinsecos_yaml.py` comprueba que esa función exista. Si se tira p03, esa prueba y ese YAML se rompen y hay que reapuntarlos.

Cobertura: solo `test_carga_externa.py` (6, vía `compile`) y, indirectamente, `test_diseno`/`test_generador`. Es la cobertura más frágil de lo que se quiere conservar: hay que portarla.

### 2.8 `passes/p04_placement`, `db_push`, `db_sql` (168+166+136) - TIRAR

Deciden por operador si va a la base o al flujo, cortan aristas con `read` y `write` de frontera y generan SQL en CTE (`sgm_paso<n>`). Dependen de `Operator.placement`, `Graph.split_edge` y `Builder`. La decisión "empujar a la base" desaparece como etapa y pasa a ser un campo del modelo de proceso. Cobertura: `test_push_db.py` (5), `test_sql_with.py` (15).

### 2.9 `passes/p05_sql_fusion` (149) y `p06_flow_fusion` (172) - TIRAR

Fusionan operadores en `exec_sql` con `WITH` o en un `map` (tMap). Son optimizaciones del grafo de operadores; el Job Script nuevo decide su propia forma. Cobertura: `test_passes.py`, `test_components.py`, `test_sql_with.py`, vía `compile`.

### 2.10 `passes/p07_templates` (299) - TIRAR, rescatar la idea

Agrupa componentes conexos por etiqueta, calcula una forma (hash de tipos y conexiones sin nombres) y crea plantilla más instancias `iterate` con contexto `parametro_k`. Es la versión por operador de lo que el modelo nuevo llama parámetros por producto. `agrupacion.py` ya hace algo parecido con los hechos. Cobertura: `test_joblets.py` (5), `test_guia_joblets.py` (3).

### 2.11 `passes/p08_partition` (171) - TIRAR

Subjobs por componente conexo, tope `max_components_per_job` y decisión de materializar aristas. Es un asunto del emisor de Talend. La política `max_components_per_job` sí vive en `env/project.json` y se conserva. Cobertura: `test_fusion_partition.py` (10), `test_subjobs.py` (5).

### 2.12 `passes/p09_schemas` (150) - TIRAR

Propaga `Column` por el grafo de operadores. El catálogo (`env/schemas/`) y los tipos del código (`types_code`) se conservan; la propagación se rehace sobre columnas del linaje. Cobertura: `test_schemas.py` (7, de ellas 5 vía `compile`), `test_tipos_codigo.py` (11).

### 2.13 `passes/p10_components`, `reglas_mapeo`, `join_match` (200+158+108) - TIRAR

La escalera asigna un componente de Talend a cada operador con las 24 reglas de `rules/mapping/*.yaml`, que casan por `kind`, `placement` y `file_format` del operador. `join_match` fija modelo de coincidencia y tipo de unión del `tMap`. Todo está en términos de `Operator.kind`. Las reglas YAML y el catálogo (`rules/talend/*.json`) tienen conocimiento de Talend valioso, pero su clave de entrada desaparece. Cobertura: `test_components.py` (11), `test_casos.py` (39, ejecuta `tests/cases/*` con 39 casos), `test_reglas_conflictos.py` (5), `test_join_match.py` (11).

### 2.14 `expressions/` (1.542 líneas) - CONSERVAR

Responsabilidad real: dos traductores de expresión SAS a Java, ambos de cadena a cadena. El primero (`expressions_*`, ~735 líneas) es en línea y conservador; lee plantillas de `rules/sas/functions/*.yaml`. Si se rinde, `translate` llama al segundo (`talend_*`, ~836 líneas), que usa rutinas de Talend (`StringHandling`, `TalendDate`). Un interruptor `SGM_TALEND_EXPRESSIONS` lo apaga.

API: `expressions.translate(sas) -> Translation` y `talend_translator.translate_to_talend(sas, entrada)`. Ninguno importa `ir`. Solo `p10_components` los llama.

Cobertura desigual: `test_talend_translator.py` (28) cubre el segundo. **El traductor en línea no tiene prueba propia**: ningún archivo de `tests/unit` importa `expressions.expressions`; se ejercita solo a través de `compile` (por ejemplo `test_components`, `test_casos`). Al borrar esas pruebas se pierde su cobertura. Hay que escribir pruebas directas antes de tirar el pipeline viejo.

### 2.15 `ingest/` (226), `store/` (288), `catalog/` (614)

- `ingest/` (CONSERVAR): importación segura de carpeta o ZIP, límites, detección de codificación, sha256. No depende de nada del pipeline. Cobertura: `test_ingestion.py` (15).
- `store/` (ADAPTAR): `db.py` es SQLite genérico. `gaps.py` (inventario de huecos por firma) y `overrides.py` (decisiones por firma y alcance) reciben `Plan`. El concepto de firma como llave de decisión sobrevive solo si el modelo nuevo calcula firmas; hoy las calcula `ir/signature.py`. Cobertura: `test_store.py` (8), `test_routing.py` (5), `test_intake.py` (7), todas pasan por `compile`.
- `catalog/` (CONSERVAR): `config.py` (Env, Project, Externals), `environment.py`, `describe.py`, `talend.py` (nombres de componentes), `schemas.py`. Solo `schemas.py` importa `ir.models.Column`; basta redefinir `Column` en `catalog`. Cobertura: `test_config.py` (unas 15 de 20 sin compilar), `test_describe.py` (8), `test_schemas.py` (2 sin compilar).

### 2.16 `emit/`, `redaction.py`, `decisions.py`, `rules_validate.py` y cargadores de `rules/`

- `emit/guide_md.py` (312) y `emit/plan_json.py` (176): TIRAR. Renderizan `Plan`, `Operator` y `Evidence`. Cobertura: `test_compile_outputs`, `test_golden*`, `test_invariantes_produccion`, `test_plan_valores`.
- `emit/conventions/naming.py` (CONSERVAR): validación y render de nombres de Job.
- `emit/conventions/best_practices.py`, `context_rules.py`, `infra.py` (unos 400): **código muerto**. `grep` en `src`, `tests` y `tools` muestra que solo `best_practices` importa `infra`; nada importa los tres. `context_rules` (variables de contexto desde `%LET`, cadenas de ambiente, credenciales) toca el tema de parámetros por producto: vale como referencia, no como código a conectar tal cual.
- `redaction.py` (CONSERVAR): una función `redact(text, path)` más regex de secretos. Se aplica antes de analizar; cualquier modelo nuevo debe seguir recibiendo texto ya redactado. Cobertura: `test_security.py` (4), `test_redaction_txt.py` (3), `test_entrada_sas.py` (parte).
- `decisions.py` (ADAPTAR): agrupa `plan.pending` por firma. Cobertura: `test_decisiones.py` (3).
- `rules_validate.py` (CONSERVAR): valida cada YAML o JSON contra `schemas/rules/`, comprueba que los componentes de `rules/mapping/` existan y que cada `tests:` apunte a un caso real. Es independiente del pipeline, salvo que valida `rules/mapping` y `rules/sas/procs`, que se reescribirán. Cobertura: `test_rules_validate.py` (7), `test_catalogo_sas.py` (27).
- Cargadores de `rules/`: cada uno sigue a su consumidor.
  - `plumbing_patterns.cargar` (puro): conservar.
  - `catalog/talend.component_names` (puro): conservar.
  - `types_code` + `informats.yaml`, `sql_semantics`, `sql_portability`: conservar.
  - `expressions_base` carga `rules/sas/functions/`: conservar.
  - `motivos` carga `rules/routing.yaml`: conservar.
  - `reglas_mapeo.load_rules` y `proc_rules.declared`: se van con p10 y la IR.

### 2.17 Módulos de agrupación y diseño (fuera de la lista, pero en el camino)

- `agrupacion.py` (153): solo importa `facts.model`. Agrupa regiones por similitud de Jaccard del vocabulario de datasets. No usa nombres de producto. CONSERVAR. Cobertura: `test_agrupacion.py` (3). Su "región" es una definición de macro detectada por regex sobre líneas de texto, no el `call` del frontend; conviene unificar.
- `generador.py` (309): la mitad usa hechos (regiones, datasets por región, variables de contexto). `joblets_por_grupo`, `operadores_de_contexto` y `diseno_del_job` reciben `plan_ops` (operadores con `component`, `signature`, `evidence`). ADAPTAR: separar la parte de hechos. Cobertura: `test_generador.py` (6, 4 vía `compile`).
- `diseno.py` (32): compone `facts_for_project` con `diseno_del_job`. ADAPTAR junto con `generador.py`.
- `lineage.py` (73): linaje entre programas por operadores (`op.params["outputs"]`). TIRAR; lo absorbe el grafo.

## 3. Respuestas específicas

### 3.1 ¿Qué hechos del frontend/facts bastan para construir el grafo de linaje y qué falta?

**Lo que ya basta** (verificado):

- Quién escribe: `DataStep.outputs` y `output <ds>`; `SqlStatement.target` en `create table`, `create like`, `insert`; `Proc.options["out"]`. Quién lee: `set`/`merge` con `in=`; `SqlStatement.sources`; `Proc.options["data"]`.
- Región o macro de origen: `ProgramItem.call` (invocación más externa, con archivo y línea) y `ProgramItem.label` (nodo de SAS Studio). El `Fact` solo trae el nodo, no la invocación.
- Orden de ejecución y versiones: `analysis.items` va en el orden del programa tras expandir macros constantes.
- Alcance: `facts.model.alcance_de` (work, permanente, externo) con `libref_externos`.
- Prueba de que alcanza: `flow/model.py` ya construye el grafo con esos datos (2.205 pasos y 1.226 aristas en `client_large.sas`, 0,9 s).

**Qué hay que construir sobre `analysis.items` y no sobre `Fact`.** Los hechos salen del texto sin expandir, sin identidad de paso (solo `nodo` y líneas) y sin `call`. El `PROC SQL` se puede reasociar escritura-lectura por línea idéntica; un `DATA` no (la escritura está en la cabecera y la lectura en el `set`). Además, un nombre armado con parámetros de macro queda marcado `dinamico` en los hechos, mientras que el análisis expandido resuelve los constantes. Por eso el linaje debe leer `ProgramItem`, como ya hace `flow/model.py`, y usar los `Fact` solo para lo externo.

**Qué falta** (cada punto probado salvo que se indique):

1. `PROC APPEND base=... data=...`: no se registra `base` como escrito ni leído. Con el ejemplo probado, `work.tot` aparece como entrada externa sin productor. Existe `rules/sas/procs/proc-append.yaml` en la IR, pero no el equivalente en `flow`.
2. E/S de archivos: `infile "ruta"`, `proc import datafile=`, `proc export outfile=`, `filename`. El flujo no genera nodos de archivo externo (`PROC IMPORT` da `reads=[]`, `writes=['work.raw']`). Los hechos sí tienen `archivo_externo` para `proc import/export/download/upload`, pero no para `infile` de un DATA step.
3. Fuentes de SQL fiables: la regex del frontend añade tablas falsas (`extract(year from fecha)`) y pierde uniones con coma. `sql_tree` es exacto en consultas planas y se rinde ante subconsultas en `FROM`. Hace falta un extractor con `sqlglot` (recorrer `exp.Table`, descontar CTE y alias) y la regex como respaldo.
4. Fuentes dentro del pass-through (`inner_sql`): los hechos las ven (`_LEE_EN_MOTOR`, alcance externo), el modelo de flujo no.
5. Nombres con macro variable sin resolver: en `client_large.sas`, 210 de 2.315 referencias (9 %) y 24 de 148 en `client_poc.sas` conservan `&`. El grafo debe marcarlas "sin resolver" con su motivo, no descartarlas.
6. Pasos dinámicos: 790 de 2.205 pasos de `client_large.sas` (36 %) son `MacroDynamic`. De ellos, 630 empiezan con `%` (control de macro: `%let` con `%sysfunc`, `%do` con límites no constantes, `call symput`) y 160 son otras sentencias (por ejemplo `footnote`). Ninguno aporta lecturas ni escrituras. Es probable que esto pierda poco linaje, pero lo que haya dentro de los `%do` no constantes no se ve: no lo verifiqué.
7. Versión de dataset: `flow/model.py` une cada lectura al último productor, sin nombre de versión. Falta el `@vN` de p01 para distinguir reescrituras. También faltan los procs que reescriben en su lugar con otras formas (`PROC SORT` sin `OUT=` sí se trata).
8. Modo de escritura (crear, insertar, agregar, reemplazar): `insert` y `create` producen el mismo `tabla_escrita`. No se distingue.
9. Condicionales: un `%if` con condición constante elige rama al expandir; con condición no constante expande ambas ramas. El grafo no puede decir cuál corre.
10. Nivel de columna: los hechos no llevan columnas, claves ni filtros. Para validaciones y para el `tMap` hay que apoyarse en `sql_tree` y `DsStatement` (`by`, `where`, `keep`, `rename`). Es trabajo aparte.
11. Parámetros por producto: `macro_llamada` trae `args` como texto crudo; hay que parsearlos y relacionarlos con los parámetros de `MacroDef` (`macro_params` en `compile`).

### 3.2 ¿`p02_plumbing` puede clasificar fontanería sin depender del resto de pasadas?

**Parcialmente: la clasificación sí, el módulo no.**

Lo que sí es independiente (verificado leyendo `p02` y `plumbing_patterns`):

- `match_plumbing(texto)` es puro: recibe una cadena y devuelve la categoría. Depende solo de `rules/sas/plumbing.yaml`.
- `_work_cleanup(statement)` también es puro (regex sobre `proc delete` y `proc datasets`).
- `p02.mark` no necesita p01 ni ninguna otra pasada anterior. Solo requiere que los operadores existan (lowering) y que el contexto traiga `project.reports`.

Lo que impide usar el módulo tal cual:

- `classify` y `mark` esperan `Operator` (leen `op.params["statement"|"sql"|"text"|"untranslated"|"assignments"]`) y mutan `op.status`, `op.params["plumbing"]`, `plan.not_migrated`.
- `_report` cambia `op.kind` y `op.params` según una política del proyecto.
- p03 y `region.py` dependen de que p02 haya marcado (`"plumbing" in op.params`) y llaman a `p02.op_text` y `p02.remove_marked`. Es una dependencia de p03 hacia p02, no al revés.

Riesgo si se aplica sobre texto de paso completo (verificado con cadenas sintéticas):

- `match_plumbing("data a; set b; do while (x<3); x+1; end; run")` devuelve `espera`, porque el patrón `\b(sleep|until|wait|ps\s+-|while)\b` no está anclado.
- `data a; x=datetime(); run` devuelve `medicion`.
- Hoy el IR evita esto en parte porque clasifica por sentencia y cada asignación es un operador con su texto. Con un paso entero habría falsos positivos.
- No medí cuántos ocurren en `client_large.sas`; el riesgo está demostrado con ejemplos, no cuantificado.

Recomendación: conservar `plumbing_patterns.py` y el YAML. Llamar `match_plumbing` por sentencia (cada `Stmt`, `DsStatement` o `SqlStatement`) o por paso con los patrones anclados. Reimplementar el efecto (registrar y omitir) en el modelo nuevo.

### 3.3 Pruebas que se van y pruebas que protegen lo conservado

Base: 636 pruebas en 67 archivos. Las clasifiqué por importaciones; las mixtas con la heurística descrita en la sección 0.

**A. Se van con la IR, las pasadas y los emisores viejos: 22 archivos, 195 pruebas.**

`test_carga_externa` (6), `test_casos` (39), `test_compile_outputs` (8), `test_components` (11), `test_fronteras` (2), `test_fusion_partition` (10), `test_golden` (4), `test_golden_equivalencia` (7), `test_guia_joblets` (3), `test_invariantes_produccion` (5), `test_ir_rules` (21), `test_joblets` (5), `test_join_match` (11), `test_objetivo_diseno` (6), `test_passes` (11), `test_plan_valores` (2), `test_programa_independiente` (7), `test_push_db` (5), `test_reglas_conflictos` (5), `test_reportes` (7), `test_sql_with` (15), `test_subjobs` (5).

Todas llaman a `compile_project` o a `ir.*` y comprueban operadores, componentes o `plan.json`. Mucho de lo que verifican (determinismo, ningún secreto en la salida, políticas de reportes, tamaño máximo de Job) son comportamientos que el modelo nuevo debe volver a demostrar. No se descartan los casos; se reescriben contra la API nueva. En particular, `tests/cases/*` (39 casos con `expected.yaml`) y los `tests/golden/*.plan.json` son datos reutilizables.

**B. Mixtas: 11 archivos, 120 pruebas, de las cuales unas 56 se van.**

`test_tipos_codigo` (11, casi todas vía `compile`), `test_sql_flujo` (20, unas 9), `test_sql_semantica` (14, unas 8), `test_schemas` (7, unas 5), `test_config` (20, unas 5), `test_selectors` (7, 2), `test_sql_normalize` (21, 2), `test_motivos` (6, 4), `test_routing` (5, 3), `test_generador` (6, 4), `test_diseno` (3).

**C. Cableado sobre `Plan` y `compile` que se reescribe o adapta: 7 archivos, 53 pruebas.**

`test_batch` (10), `test_trinquete` (9), `test_store` (8), `test_intake` (7), `test_generadores` (11), `test_explain` (5), `test_decisiones` (3). Prueban la infraestructura (lotes, trinquete de métricas, almacén, intake, explain), no la traducción. Se van o se adaptan según se reescriban `batch`, `intake`, `explain`, `store` y `trinquete`.

**Total aproximado que se va o se reescribe: unas 300 de 636.**

**D. Protegen lo que se conserva: 25 archivos, 253 pruebas, más 15 de CLI y reglas.**

| Módulo conservado | Pruebas que lo protegen |
|---|---|
| Frontend y macros | `test_frontend` (18), `test_macros` (12), `test_entrada_sas` (13), `test_catalogo_sas` (27), parte de `test_selectors` y `test_sql_normalize` |
| Hechos y agrupación | `test_facts` (11), `test_mapa_flujo` (4), `test_agrupacion` (3) |
| Modelo de flujo | `test_flujo` (11), `test_flujo_salidas` (15) |
| Fontanería | `test_plumbing_categorias` (39), `test_plumbing_yaml` (12), `test_intrinsecos_yaml` (1, depende de p03) |
| SQL rescatable | `test_sql_render` (5), parte de `test_sql_normalize` y `test_sql_flujo` |
| Ingesta | `test_ingestion` (15) |
| Seguridad | `test_security` (4), `test_redaction_txt` (3) |
| Reglas y catálogo | `test_rules_validate` (7), `test_describe` (8), parte de `test_config`, `test_informats_yaml` (3), `test_proc_rules` (3), `test_talend_referencia` (10), `test_referencia_tools` (7), `test_routing_motivos` (2), `test_no_script_specific_names` (2), `test_smoke` (1) |
| Expresiones | `test_talend_translator` (28) |
| Verificación de salidas | `test_comparar_salidas` (4) |

Huecos de protección (conservado sin prueba directa):

- Traductor de expresiones en línea: sin pruebas propias, solo vía `compile`.
- `region.py` y detección de carga externa: solo `test_carga_externa` (en el grupo A).
- `types_code`: solo vía `compile` (`test_tipos_codigo`). `test_informats_yaml` valida el YAML, no el código.
- `facts/project.py`: ninguna prueba del acoplamiento con `compile.project_base`.
- `frontend/grid.py`: ninguna, y nada lo usa.
- `emit/conventions/best_practices`, `context_rules`, `infra`: ninguna, y nada los usa.

## 4. Hallazgos que cambian el plan

1. `flow/model.py` ya es un grafo de linaje de datasets construido del frontend, sin IR. El plan debe partir de él y no de cero, con los huecos de la sección 3.1.
2. El linaje se arma sobre `analysis.items`, no sobre `facts`. Los hechos no traen identidad de paso ni la invocación de macro y están calculados sobre texto sin expandir.
3. Hay que reescribir la extracción de fuentes de SQL. La regex del frontend da fuentes falsas y pierde las uniones con coma; `sql_tree` no admite subconsultas en `FROM`.
4. `plumbing_patterns` y el YAML se conservan. La pasada p02 no, y los patrones no se pueden aplicar a pasos enteros sin falsos positivos (`do while` -> `espera`).
5. `region.py` es el único trozo de p03 que aporta al concepto de región. Se porta sobre un registro de paso en vez de `Operator`, con el cambio sin confirmar que ya tiene.
6. Antes de borrar las pruebas del grupo A, hay que escribir pruebas directas para el traductor de expresiones en línea, `types_code` y `region`. Hoy solo pasan por `compile`.
7. Hay código muerto: `frontend/grid.py` (212 líneas) y `emit/conventions/{best_practices,context_rules,infra}.py` (unas 400). Se pueden borrar ya, sin riesgo para el pipeline.
8. `rules/sas/intrinsics/external-load.yaml` apunta a `sgm.passes.p03_intrinsics._external_load` y una prueba lo comprueba. Hay que reapuntarlo al borrar p03.
9. Las 24 reglas de `rules/mapping/*.yaml` y `rules/sas/procs/*.yaml` se indexan por `Operator.kind`. El conocimiento de Talend que contienen vale, pero hay que reescribir su clave de entrada.
10. `sqlglot` y `jsonschema` figuran en `pyproject.toml` fuera de la lista de `AGENTS.md`. Conviene confirmar que están anotadas en "Decisiones".
