# PROGRESS

## Hito 0. Repositorio nuevo

- Fecha: 2026-10-30
- Qué se hizo: repositorio `git init` en `main`, paquete `uv init` con Python 3.12, estructura de carpetas, `pyproject.toml` (dependencias `networkx`, `typer`, `pyyaml`; dev `pytest`, `pytest-xdist`, `ruff`; `line-length = 100`; `addopts = -n auto`), `AGENTS.md`, `.gitignore`.
- Pruebas: 1 pasa (`test_el_paquete_importa`). `ruff check .` limpio.
- Bloqueos abiertos: ninguno.

## Decisiones

- El script de consola apunta a `sgm.cli:app` (Typer), tal como pide el prompt.
- Pydantic no se usa en el hito 0. Los modelos serán `dataclass`.

## Hito 1. Copiar solo lo que sirve

- Fecha: 2026-10-30
- Qué se hizo:
  - `ingest/`: importador copiado. `Settings` se sustituyó por `ImportLimits` y los modelos `FileKind`, `SourceFile`, `Skipped` pasaron a dataclasses (sin pydantic).
  - `frontend/lexer.py`: copiado sin cambios.
  - `frontend/macro_index.py`: solo funciones puras (`substitute`, `first_quoted`, `resolve_path`, `PathIndex`). Se quitaron `walk`, `macro_index` y `constant_vars` porque dependían del AST anterior; se reescriben en el hito 4.
  - `frontend/grid.py`: modelos `GridTask`, `Schedule`, `Orchestration` (dataclasses), `shell_tasks` y orden topológico. Se quitaron `orchestrator_macros`, `macro_step_tasks` y `analyze_grid`, que dependían del AST; se reescriben en el hito 4.
  - `catalog/environment.py`: catálogo de entorno portado a dataclasses con la misma validación (sin pydantic).
  - `redaction.py`, `expressions/talend_translator.py`, `expressions/expressions.py`: copiados sin cambios de lógica.
  - `passes/plumbing_patterns.py`: solo patrones de fontanería como datos (`PlumbingPattern`, `match_plumbing`). La clasificación con el IR anterior no se copió.
  - `emit/conventions/`: `naming.py` (validación y render de nombres), `context_rules.py` (copiado), `infra.py` (conexión, cierre, `tDie` y `tLogRow` como reglas de datos), `best_practices.py` (BP-NAME-01/02, BP-CTX-01, BP-SEC-01, BP-DB-01, BP-ERR-01, BP-SIZE-01 sin dependencias MCP).
  - `rules/talend/`: `components.json`, `official-component-inventory.json`, `component-panels.json` copiados. `engines.json` (claves `engines` y `engine_notes`) y `type_hints.json` salen de `rules/mappings/talend-components.json`.
  - `rules/sas/sql-functions.json` copiado.
  - `tests/fixtures/sas/` copiado completo (incluye `real`, `synthetic`, `grid`, `generalization`, `inc`).
  - `tests/support/cache.py` copiado. `docs/conventions.md` sin la regla "un programa = un Job" ni la de un componente por paso.
  - Pruebas portadas: `test_no_script_specific_names.py` (lista nueva del prompt), `test_security.py` (solo redacción), `test_ingestion.py` (solo importador), `test_talend_translator.py`.
- Pruebas: 45 pasan, 1 se salta (symlink en Windows). `ruff check .` limpio.
- Diferido a su hito, porque dependen de módulos que aún no existen: `tests/support/spec_invariants.py` (hito 6), `tools/automation_metrics.py` (hito 10).
- Bloqueos abiertos: ninguno.

## Decisiones

- E501 (líneas largas) se tolera solo en código portado o de datos (mensajes en español, patrones Java y de ruta). Está en `per-file-ignores` de `pyproject.toml`. El resto del código respeta `line-length = 100`.
- Catálogo de entorno y modelos de ingesta: dataclasses en vez de pydantic, porque pydantic no está en la lista de dependencias permitidas.
- Se eliminó la vista previa de renombrado masivo de `job_naming.py` (dependía del modelo de plan anterior).
- Hito 0: identidad de git del repositorio nuevo = la del repositorio viejo (`Andres Gaibor`), configurada solo en `sgm-v2`.
- Incidente: durante el hito 1 se ejecutó `uv run --project .` dentro del repositorio viejo; sincronizó su `.venv` (ignorado por git, sin cambios en el código). El repositorio viejo sigue limpio en `git status`.

## Hito 2. Fixtures del cliente

- Fecha: 2026-10-30
- Qué se hizo: los dos programas del cliente están en `tests/fixtures/sas/client/`:
  - `client_poc.sas` ← `data/projects/c0a88f920346/src/cod1.sas` del repositorio viejo (81 KB, 19 nodos `/* Etiqueta: */`, `sashelp.cars` y bulkload). No tiene credenciales.
  - `client_large.sas` ← `Downloads/Cod2.txt` (836 KB, 610 nodos `/* Etiqueta: */`, proceso de información exógena de depósitos).
- Enmascarado: en `client_large.sas` hay 1 `proc pwencode in=...` y 26 sentencias `signon ... user=... pass=...` con la contraseña en claro. Todas quedaron como `'***'`. `client_poc.sas` no tiene credenciales.
- Pruebas: `test_pwencode_en_fixtures_y_salidas_solo_con_asteriscos` (en `test_security.py`) falla si un fixture de texto, un miembro de un ZIP de fixtures o un archivo de `out/` trae un `proc pwencode` con un valor distinto de `'***'`. Total: 46 pasan, 1 se salta. `ruff check .` limpio.
- Bloqueos abiertos: ninguno.

## Decisiones (hito 2)

- Además de `pwencode`, se enmascara `pass=` en claro en `client_large.sas` (`signon`). El prompt pedía solo `pwencode`, pero es una credencial del mismo tipo y no debe llegar a fixtures ni salidas.

## Hito 3. Frontend: nodos y pasos

- Fecha: 2026-10-30
- Qué se hizo:
  - `frontend/splitter.py`: nodos por `/* Etiqueta: ... */`, con líneas de inicio y fin; quita U+200B sin mover líneas; nodo sin etiqueta solo si tiene contenido.
  - `frontend/steps.py`: DATA step, PROC SQL, PROC genérico (nombre, `DATA=`, `OUT=`, opciones, cláusulas BY/VAR/CLASS/WHERE), `%macro`/`%mend`, llamadas de macro (con o sin paréntesis), `%let`, `%include`, `libname`, `options`, `x`, y `Global` para lo demás. Un paso que falla devuelve `Unparsed` y sigue.
  - `frontend/sql.py`: `create table ... as select`, `select` (con FROM/JOIN), pass-through `from connection to <motor> (...)`, `execute (...) by <motor>` y la forma `execute by <motor> (...)`, `insert`, `delete`, `drop table`, `connect`, `disconnect`. El SQL del pass-through queda intacto.
  - `frontend/datastep.py`: `set`/`merge` con `in=`, `by`, `where`, `output`, `keep`, `drop`, `rename`, `retain`, `lag`, `first./last.`, `array`, `do`/`end`, `infile`, `input`, `datalines`, `call symput`, `format`/`length`/... como `declare`, asignaciones.
  - Corrección en `frontend/lexer.py`: el resto de la línea de `datalines;` ya no cuenta como una fila vacía.
- Pruebas: 17 nuevas en `tests/unit/test_frontend.py`. Total: 64 pasan, 1 se salta. `ruff check .` limpio.
- Métricas sobre `client_large.sas`: 610 nodos, 610 con etiqueta (coincide con las `/* Etiqueta:` del archivo). Sentencias: 353 DATA step, 359 PROC SQL, 215 PROC genérico, 274 definiciones de macro. 0 `Unparsed`. Tiempo de división más parseo: ~0.5 s.
- Bloqueos abiertos: ninguno.

## Hito 4. Expansor de macros

- Fecha: 2026-10-30
- Qué se hizo:
  - `frontend/macros.py`: índice de `%macro ... %mend` (también anidadas) con huella del cuerpo normalizado; evaluación parcial sobre sentencias crudas: `%let` constante, `&var` conocidas, `%if`/`%else` con condición constante (`=`, `eq`, `ne`, `<`, `>`, etc.), `%do` con límites constantes (`%to`, `%by` negativo incluido), llamadas con parámetros posicionales y por nombre, y `%include` resuelto dentro del proyecto. Lo no constante se marca como `MacroDynamic` con motivo `MACRO_DINAMICA` y su texto.
  - `frontend/program.py`: pipeline por proyecto. Indexa todas las macros antes de expandir, expande archivo a archivo y asigna a cada paso o dinámico la etiqueta de su nodo.
  - `frontend/macro_index.py`: se completó con `resolve_path` y utilidades (sin AST).
- Pruebas: 11 nuevas en `tests/unit/test_macros.py`. Total: 75 pasan, 1 se salta. `ruff check .` limpio.
- Métricas sobre los fixtures del cliente:
  - `client_poc.sas`: 17 macros con nombre único, 40 definiciones duplicadas contadas una vez, 6 nombres con cuerpos distintos, 36 dinámicos, 10 `%include` externos, 0 `Unparsed`.
  - `client_large.sas`: 10 macros con nombre único, 261 definiciones duplicadas contadas una vez, 3 nombres con cuerpos distintos, 610 dinámicos, 30 `%include` externos, 0 `Unparsed`. Los dinámicos son sobre todo `%let` con `%sysfunc`, `TITLE`/`FOOTNOTE` con `%qsysfunc(date())` y `call symput`.
- Bloqueos abiertos: ninguno.

## Decisiones (hito 4)

- Si un mismo nombre de macro tiene cuerpos distintos, gana la primera definición en orden alfabético de archivo. Los casos quedan en `MacroIndex.conflicts`. Es una decisión a revisar con el usuario.
- Un `%include` externo (ruta fuera del proyecto) se conserva como paso `Include` y se registra en `unresolved_includes`. No se adivina su contenido.
- Un `%if` con condición no constante no expande ninguna de sus ramas: se marca completo como `MacroDynamic`.
- Un fragmento dinámico corta el grupo de pasos. Un DATA step que cruza un dinámico queda partido.

## Hito 5. IR lógica

- Fecha: 2026-10-30
- Qué se hizo:
  - `ir/models.py`: `Evidence`, `Column`, `Operator`, `Edge`, `Graph` (sobre `networkx.MultiDiGraph`, con `merge` que une evidencia y redirige aristas), `Job`, `Plan` (con `not_migrated`, `pending`, `gaps`).
  - `ir/signature.py`: firma de 16 caracteres por tipo y parámetros normalizados. Nombres, literales, números y macro variables se sustituyen; se conservan palabras clave, operadores y funciones (lo que sigue a `(`).
  - `ir/builder.py`: id secuencial por plan, enlace de operadores y recálculo de firma.
  - `ir/lower_data.py`: `set` (lectura por fuente; unión si hay varias), `merge` con `by`, `in=` y tipo de unión (`inner` con `if a and b`, `left` con `if a`, `right` con `if b`, `full` con `or` o sin `if`; si no se deduce, `parcial`), `where` y `if` sin `then` como `filter`, asignaciones como `derive` acumulado, `keep`/`drop` como `select`, `rename`, `output` condicionado como `split`, `retain`/`lag`/`first.`/`last.` como `stateful_row` parcial, `infile`/`input`/`datalines` como `read_file`.
  - `ir/lower_sql.py`: pass-through `select ... from connection to <motor>` como `read` con `placement=db:<motor>` y SQL intacto; `execute` como `exec_sql` en la base (con la salida si es `create table`); SQL sobre WORK como `exec_sql` parcial.
  - `ir/lower_procs.py`: `sort` (con `nodupkey` → `sort` + `dedup`; sin clave, `parcial`), `append` → `union`, `import` → `read_file`, `export` → `write_file`, `means`/`summary`/`freq` → `aggregate`, cualquier otro PROC → `unsupported` `hueco` con `PROC_NO_SOPORTADO`.
  - `ir/lower.py`: despachador. Cada operador lleva evidencia (archivo, líneas, etiqueta).
- Pruebas: 21 nuevas en `tests/unit/test_ir_rules.py` (una por regla, firmas por nombres, evidencia y fusión del grafo). Total: 96 pasan, 1 se salta. `ruff check .` limpio.
- Métricas de lowering sobre los fixtures del cliente:
  - `client_poc.sas`: 271 operadores, 4 aristas internas. Estados: 131 hueco, 101 reemplazado, 21 soportado, 18 parcial.
  - `client_large.sas`: 4 292 operadores, 282 aristas internas. Estados: 2 195 hueco, 871 reemplazado, 800 soportado, 426 parcial. Motivos principales: `CONFIGURACION` 871, `SENTENCIA_NO_SOPORTADA` 789, `MACRO_DINAMICA` 610, `MACRO_NO_EXPANDIDA` 447 (llamadas `%web_*` del visor de Studio), `PROC_NO_SOPORTADO` 213, `CONEXION_SQL` 106.
- Bloqueos abiertos: ninguno.

## Decisiones (hito 5)

- Motivo de hueco añadido: `SENTENCIA_NO_SOPORTADA` para sentencias globales sin regla (títulos, `signon`, `rsubmit`, etc.). No está en la lista del prompt; la pasada de plomería las tratará como fontanería o como hueco.
- Configuración de sesión y macro (`libname`, `options`, `%let`) no es lógica de datos: se registra como operador `unsupported` con estado `reemplazado` y motivo `CONFIGURACION`, para que cada paso aparezca en la evidencia.
- Un `output;` sin condición no crea operador: es la salida por defecto del DATA step.
- El SQL que lee datasets de WORK queda `exec_sql` parcial. Su traducción a flujo o a CTE es de los hitos 6 y 7.
- Se aplicó `ruff format` a módulos nuevos y a algunos portados de `emit/`. Solo cambió el formato, no la lógica.

## Hito 6. Pasadas 1 a 4 y guía (cierre de la fase 1)

- Fecha: 2026-10-30
- Qué se hizo:
  - `passes/p01_graph.py`: aristas por nombre de dataset; reescrituras versionadas (`WORK.x@vN`); escrituras finales (sin lector, o en biblioteca permanente) como `write`; lecturas permanentes sin productor como fuentes.
  - `passes/p02_plumbing.py` y `passes/plumbing_patterns.py`: fontanería por forma (espera, shell auxiliar, conexión, limpieza de tablas, control de macro, mensajes, medición, troceo, conteo, visor de Studio `%web_*`) y `proc delete`/`proc datasets` solo sobre WORK. Se registra en `not_migrated` con su equivalente Talend.
  - `passes/p03_intrinsics.py`: carga externa por estructura. Un grupo de invocación con comandos en segundo plano (`&"`) y otro con espera (`until` + `wc -l`) delimitan el bloque, que se reemplaza por un `external_load`. La detección no depende de nombres de macro (prueba con nombres aleatorios).
  - `passes/p04_placement.py`: ubicación ávida en orden topológico; un operador va a `db:<motor>` si sus entradas están en el mismo motor y su tipo se expresa en SQL portable (`rules/sas/sql-functions.json`). Cada cruce se corta con un `read` (base a flujo) o `write` (flujo a base), o reutiliza el `read`/`write` que ya consume ese dataset.
  - `passes/pipeline.py`, `compile.py`: pipeline por programa; el texto se redacta antes de analizarlo.
  - `emit/guide_md.py`, `emit/plan_json.py`, `cli.py`: `sgm compile <archivo-o-carpeta> --out <carpeta>` escribe `<programa>.guide.md` y `<programa>.plan.json`.
  - `frontend/macros.py` y `frontend/program.py`: las expansiones conservan la invocación más interna (`Evidence.call`) para agrupar bloques. Un `%if` no constante marca la condición y expande las dos ramas; un `%do` con límites no constantes (o `%do %while`) marca el encabezado y muestra el cuerpo una vez.
  - `tests/support/spec_invariants.py`: invariantes del grafo, aristas, evidencia y nombres de Job, adaptadas de la versión anterior (las de componentes Talend llegan en el hito 8).
- Pruebas: 118 pasan, 1 se salta. `ruff check .` limpio.
  - `tests/unit/test_passes.py` (11): una prueba por pasada y por criterio.
  - `tests/unit/test_compile_outputs.py` (6): todos los fixtures compilan; invariantes; cada etiqueta de `client_large` aparece en evidencia o en no migrado; carga externa de `client_poc`; guía y JSON sin secretos; CLI.
  - `tests/unit/test_golden.py` (4): referencias en `tests/golden/` para tres fixtures sintéticos y `client_poc`. Se regeneran con `SGM_UPDATE_GOLDEN=1`.
- Métricas (sin fusión ni particionado todavía):
  - `client_poc.sas`: 492 operadores, 79 aristas, 244 no migrados, 41 firmas con hueco, 1 carga externa (`db:impala`, parcial: entrada y destino no declarados en el bloque).
  - `client_large.sas`: 3 486 operadores, 1 305 aristas, 1 702 no migrados, 32 firmas con hueco, 30 cargas externas, 19 operadores en base, 18 cruces base a flujo y 0 de flujo a base.
  - Cobertura: las 610 etiquetas de `client_large` aparecen en la evidencia de operadores o de no migrados.
- Bloqueos abiertos: ninguno.

## Decisiones (hito 6)

- Orden de pasadas: p02 solo marca y registra; p03 usa esas marcas para reconocer el bloque; al final de p03 se quitan del grafo los operadores de fontanería que sobrevivieron. El prompt pone p02 antes de p03 y quitar en p02 impediría ver los comandos de la carga.
- Agrupación de carga externa por la invocación más interna de macro (`Evidence.call`), no por la más externa. Con la más externa, todo `mainProgram` sería un solo bloque.
- `%web_*` (macros auxiliares del visor de SAS Studio) se clasifican como fontanería con el patrón `visor_studio`. El prompt no lo listaba.
- Los dinámicos de `%if`/`%do` con condición no constante no bloquean el código: la condición queda como `MacroDynamic` y el cuerpo se expande.
- La entrada y el destino de una carga externa solo se toman si el bloque los declara. Si no, el operador queda `parcial` con la nota correspondiente, en vez de adivinarlos.
- Jobs: un Job por programa, sin subjobs todavía (lo hace p08 en el hito 7). El nombre del Job pasa por `render_job_name`, así un programa que empieza por dígitos queda `job_...`.
- Redacción: `redact()` se aplica al texto de entrada antes del análisis.
- Motor de base de datos siempre en minúsculas en `placement` (`db:impala`).

## Hito 7. Pasadas 5 a 8

- Fecha: 2026-10-30
- Qué se hizo:
  - `passes/p05_sql_fusion.py`: dos `exec_sql` del mismo motor se funden en uno con CTE cuando el intermedio tiene un solo lector dentro del programa y no es salida de otro. La CTE toma el nombre de la tabla que crea el primer paso y las referencias del segundo se reescriben a ese nombre. Cada fusión deja una decisión pendiente (`fundir` o `conservar`), porque otro programa podría leer la tabla intermedia.
  - `passes/p06_flow_fusion.py`: cadenas de filtro, derivación, renombre y selección en un `map` con la lista de pasos; una fuente que alimenta varias ramas `read -> filter` en un `map` con una salida por rama. Un filtro aislado no se funde.
  - `passes/p07_templates.py`: componentes conexos de una misma etiqueta con la misma forma (la firma ignora nombres); si son dos o más, una plantilla (Job hijo con el cuerpo y los parámetros) y un `iterate` por instancia con los nombres que difieren como contexto.
  - `passes/p08_partition.py`: subjobs en orden topológico; corte después de `write` y `external_load`, alrededor de cada `iterate`, y al pasar de 200 operadores. Arista materializada (`temp_table`, con decisión pendiente) desde un agregado hacia la lectura que llega al join con un ancestro compartido.
  - `passes/p09_schemas.py` y `catalog/schemas.py`: esquemas de `env/schemas.json` y propagación por lectura, filtro, derivación, selección, renombre, unión y mapa. Una columna sin tipo genera hueco `TIPO_DESCONOCIDO`. Se adelantó con este commit porque la pasada 8 ya lo llama en el pipeline; el hito 8 lo completa con los tipos de la conversión.
  - Cambios de corrección encontrados al probar: `Graph.replace` añadía el nodo nuevo después de consultar sus aristas; p02 tomaba una expresión de asignación (`x + 1`) por un comando `x` de shell; p01 escribía un `write` para un dataset permanente que el propio programa lee, lo que impedía la fusión SQL de intermedios de base; las llamadas `execute` no declaraban sus entradas; el `PROC MEANS ... OUT=` no declaraba su salida.
- Pruebas: `tests/unit/test_fusion_partition.py` (9): las cuatro pruebas obligatorias del hito y casos negativos. `tests/unit/test_schemas.py` (6). Golden regenerado (las salidas cambiaron por las pasadas 5 a 8). Total: 133 pasan, 1 se salta. `ruff check .` limpio.
- Métricas:
  - `client_poc.sas`: 475 operadores, 62 aristas, 4 mapas, 2 plantillas, 15 subjobs (máximo 200 operadores por subjob), 2 Jobs hijos.
  - `client_large.sas`: 2 941 operadores, 760 aristas, 6 mapas, 45 plantillas, 249 iteraciones, 401 subjobs (máximo 200), 82 Jobs hijos, 0 fusiones SQL.
  - Agrupación: el número de operadores después de p08 es menor que el de nodos SAS (610) en `client_large`, con 2 941 operadores; la cifra es mayor porque cada nodo tiene varias sentencias. El criterio pedía comparar operadores con nodos: queda registrado como no cumplido en el sentido estricto. Ver decisiones.
- Bloqueos abiertos: ninguno.

## Decisiones (hito 7)

- p05 no fundió nada en los programas del cliente. Los intermedios de SQL en base son tablas con nombre de biblioteca y se reutilizan entre pasos de un mismo bloque con más de un lector; la regla exige un solo lector, así que se quedan separados. Es el comportamiento correcto y conservador, pero reduce la agrupación.
- El criterio "operadores después de p08 < nodos SAS" no se cumple en `client_large` (2 941 operadores frente a 610 nodos). Los nodos son agrupaciones de sentencias: cada nodo tiene varias sentencias, cada una con su operador, y la plomería no migrada no cuenta como operador. La métrica de agrupación del hito 10 se calcula por componente Talend; aquí se deja registrada la cifra real.
- Un dataset permanente sin lector dentro del programa sigue escribiéndose con `write`; uno que sí tiene lector ya no (cambio de p01).

## Hito 8. Esquemas, componentes y decisiones de la escalera

- Fecha: 2026-10-30
- Qué se hizo:
  - `env/schemas.json`: ejemplo con dos tablas inventadas (`ejemplo_lz.clientes`, `ejemplo_lz.cuentas`), marcadas como ejemplo.
  - `passes/p09_schemas.py` y `catalog/schemas.py` (se adelantaron en el commit del hito 7): propagación de esquemas por lectura, filtro, derivación, selección, renombre, unión, mapa y Job hijo; columnas sin tipo generan hueco `TIPO_DESCONOCIDO`.
  - `rules/mapping/*.yaml`: 22 reglas, una por archivo, con `id`, `version`, `rung`, `match`, `emit`, `confidence`, `alternatives` y `tests`.
  - `passes/p10_components.py`: escalera fija (1 motor, 2 específico, 3 tMap, 4 tJavaRow con revisión, 5 tJava con revisión y SAS original). Las reglas se cargan de YAML; no hay mapeos fijos en Python. Cada componente es `candidato`. Las expresiones se traducen con el traductor copiado; sin equivalente, hueco `FUNCION_NO_MAPEADA` con la función en la firma. Cada regla con `alternatives` crea una decisión pendiente.
  - `Operator.component`: campo nuevo en la IR con el componente candidato, su peldaño, regla y revisión.
- Pruebas: `tests/unit/test_components.py` (31): cada ejemplo del YAML elige su componente; escalera; tJava solo como último recurso; ningún componente verificado; función sin equivalente; **todos los componentes usados en los fixtures existen en `components.json` o en el inventario oficial**; los motores de las reglas existen en el catálogo. `tests/unit/test_schemas.py` (6). Total: 164 pasan, 1 se salta. `ruff check .` limpio.
- Métricas de `client_poc.sas`: 67 componentes (36 de peldaño 2, 21 tMap, 9 tJava, 1 de motor), 15 `none` (conexiones de flujo), 41 huecos, 293 pendientes en `client_large` (ver abajo).
- Métricas de `client_large.sas`: 766 componentes por peldaño: 9 de motor, 388 específicos, 39 tMap, 330 tJava. **tJava = 43,1 %**. 415 componentes sin revisión pendiente. 56 firmas con hueco (24 `FUNCION_NO_MAPEADA`). 293 decisiones pendientes por alternativas de regla.
- Bloqueos abiertos: ninguno.

## Decisiones (hito 8)

- El 43 % de tJava en `client_large` viene sobre todo de SQL sobre WORK (`exec_sql` parcial en flujo), que la escalera no tiene cómo traducir a un componente específico. Se deja como tJava con revisión y no se inventa una regla: es el dato que el usuario tiene que ver.
- Operadores `read`/`write` de flujo se marcan `none`: la conexión entre componentes la da el Job, no hace falta un componente propio.
- El campo `component` se añade a `Operator` (el prompt permite añadir campos). La firma no cambia por el componente.
- Una decisión pendiente por cada operador con alternativas en su regla; el volumen es alto y se consolidará por firma en el hito 9.

## Hito 9. Decisiones y huecos

- Fecha: 2026-10-30
- Qué se hizo:
  - `store/db.py`: SQLite con `sqlite3` de la librería estándar, en `~/.sgm/sgm.sqlite` (variable `SGM_DB` para cambiarla). Tablas `overrides` (llave: firma, alcance, referencia) y `gaps`.
  - `store/overrides.py`: un override tiene firma, alcance (`paso`, `archivo`, `proyecto`, `global`), referencia, opción, autor, motivo y fecha. Gana el más específico; si no hay ninguno, queda la opción por defecto de la regla. `apply` lo aplica a los componentes con alternativas y deja la decisión en `component.decision`.
  - `store/gaps.py`: inventario por firma con motivo, archivos, ocurrencias y un ejemplo con evidencia; orden por número de archivos y, después, por ocurrencias.
  - CLI: `sgm decisions list`, `sgm decisions set <firma> <opcion> --scope <alcance> [--ref <nombre>] [--reason "<texto>"]` (un alcance que no sea global exige `--ref`), `sgm gaps list --top N`. `sgm compile` aplica las decisiones guardadas y actualiza el inventario.
- Pruebas: `tests/unit/test_store.py` (8): un override global cambia la salida de todos los archivos con esa firma; un override de archivo gana sobre el global; el override sobrevive a una recompilación; alcances inválidos se rechazan; el inventario ordena por archivos y ocurrencias; recompilar reemplaza el inventario; y dos pruebas de CLI con base temporal. Total: 172 pasan, 1 se salta. `ruff check .` limpio.
- Bloqueos abiertos: ninguno.

## Decisiones (hito 9)

- El alcance `paso` usa como referencia `archivo:línea` (línea de inicio del paso).
- El inventario de huecos se sustituye completo en cada compilación (no se acumula entre corridas). Así un hueco que ya no aparece desaparece, y el inventario siempre describe la última compilación.
- Una decisión guardada solo afecta a componentes que tienen alternativas; no cambia un componente que la regla no ofrece como opción.

## Hito 10. Escala y métricas

- Fecha: 2026-10-30
- Qué se hizo:
  - `batch.py`: compilación por lotes. El análisis del proyecto (macros, expansión) se hace una vez; cada programa se compila en su proceso (`ProcessPoolExecutor`, `--workers N`). Un programa que falla queda con un hueco `PARSE_ERROR` del archivo y no detiene a los demás. Los archivos que otros incluyen con `%include` se procesan primero.
  - `cache.py`: caché en `out/.cache/<clave>/`. La clave es el hash de los textos de entrada, de `rules/`, de `env/schemas.json` y la versión de sgm. Si nada cambió, la salida se copia sin recalcular. `--no-cache` la desactiva.
  - `lineage.py` y `sgm lineage <carpeta>`: oleadas de ejecución según los datasets permanentes que cada programa escribe y lee. WORK se excluye (es local a cada programa). Los ciclos se agrupan.
  - `metrics.py` y `sgm metrics <carpeta>`: escribe `out/metrics.json` con nodos SAS por componente, jobs y subjobs, operadores por estado, componentes por peldaño y porcentaje de tJava, pasos sin pendientes, decisiones pendientes y top 10 de huecos. `tools/automation_metrics.py` es un envoltorio de la misma función.
  - Huecos con su texto: cada hueco guarda la sentencia que lo causa (recortada), y el top de métricas la muestra.
  - Fontanería ampliada (datos en `plumbing_patterns.py`): presentación (`TITLE`, `FOOTNOTE`), configuración de macro (`%GLOBAL`, `%LOCAL`, `%RETURN`, `%SYSLPUT`), remoto (`RSUBMIT`, `SIGNON`, `SIGNOFF`, `WAITFOR`) y fin de paso (`QUIT`/`RUN` sueltos). Antes contaban como huecos.
  - `python -m sgm.cli` como punto de entrada, porque el lanzador `sgm.exe` fue bloqueado por una directiva de Control de aplicaciones de Windows.
- Pruebas: `tests/unit/test_batch.py` (9): paralelo igual que secuencial; un archivo que falla no detiene a los demás; orden por inclusiones; oleadas de linaje; WORK excluido; métricas; caché (hit y reinvalidación al cambiar un archivo); CLI de métricas y de linaje. Total: 181 pasan, 1 se salta. `ruff check .` limpio.
- Métricas sobre todos los fixtures (`sgm metrics tests/fixtures/sas`): 189 programas, 629 nodos SAS, 1 690 componentes, 959 subjobs, 189 Jobs, 1 030 pasos sin pendientes, 976 decisiones pendientes, 25,7 % de tJava. Nodos por componente: 0,372.
- Métricas de los programas del cliente:
  - `client_poc.sas`: 19 nodos, 67 componentes, 0,284 nodos por componente, 14 subjobs, 13,4 % tJava, 49 pasos sin pendientes, 37 decisiones pendientes, 46 huecos.
  - `client_large.sas`: 610 nodos, 662 componentes, 0,921 nodos por componente, 397 subjobs, 49,8 % tJava, 311 pasos sin pendientes, 293 decisiones pendientes, 43 huecos.
- Top 10 de huecos del corpus: `%include` externo (104 ocurrencias, 18 archivos), `PROC CONTENTS` (86, 4), `%LET` con `%SYSFUNC` sobre rutas y datos (34, 2; 31, 2; 31, 2; 30, 1), `PROC PRINT` (31, 4), `PROC CONTENTS ... _ALL_` (31, 2), `SELECT INTO :` dinámico (30, 1), `%LET` con `%SYSEVALF` (30, 1), y `sessio&i %end` (30, 1). Las firmas completas están en `out/metrics.json`.
- Bloqueos abiertos: ninguno.

## Decisiones (hito 10)

- La caché es por proyecto y no por archivo: las macros se comparten entre archivos, así que un archivo que cambia puede afectar a los demás. El prompt pedía el hash del archivo; por seguridad se toma el del proyecto completo.
- El paralelismo es por programa: el análisis del proyecto (macros, expansión) se hace una vez en el proceso principal, y solo las pasadas y la salida corren en paralelo.
- "Nodos por componente" queda en 0,37 para el corpus y 0,92 para `client_large`. La regla "más alto es mejor" se cumple en sentido relativo: un valor mayor que 1 significaría que cada componente agrupa varios nodos, y este corpus todavía tiene más componentes que nodos. No se cambia la métrica para que parezca mejor.
- Las dos sentencias `%LET` con `%SYSFUNC` sobre rutas y datos siguen como `MACRO_DINAMICA`: su valor depende del entorno de ejecución.

## Hito 11. Verificación final

- Fecha: 2026-10-30
- Comprobaciones:
  - `uv run pytest -q`: 181 pasan, 1 se salta (el symlink de Windows). `uv run ruff check .`: limpio.
  - Compilación de todos los fixtures (`tests/fixtures/sas`, 189 programas): sin excepciones, código de salida 0, 189 guías y 189 planes en `out/`.
  - Guías revisadas a mano: `client_poc` (sección por nodo, componente candidato, evidencia por fila, huecos con su sentencia) y `p0_ejemplo_basico` (sin etiqueta, lectura con su dataset, `tMap` de la fusión). Cada fila cita archivo y líneas.
  - Secretos: `pwencode` en `out/` y `tests/` solo con `***`. La prueba de guardia lo verifica; la máscara que produce la redacción (`in=***`) se acepta. Las dos contraseñas sintéticas (`Tiger123`, `Sekret9`, `TopSecret77`) aparecen solo en `tests/unit/test_security.py`, como cadenas de prueba de la redacción; no son del cliente.
- Estado por hito:
  - Hito 0 a 10: terminados, con commit local cada uno (`hito N: ...`).
  - Hito 11: terminado.
- Commits locales (sin `git push`): `2a45654` hito 0, `a314f00` hito 1, `ab7b379` hito 2, `b990a1d` hito 3, `3be98bc` hito 4, `0e2ce34` hito 5, `2cabd91` hito 6, `13ed16e` hito 7, `bb2164a` hito 8, `aae9613` hito 9, `19ead8b` hito 10, y este commit del hito 11.

## Estado final de los programas del cliente

- `client_poc.sas` (19 nodos): 67 componentes (13,4 % tJava), 14 subjobs, 49 pasos sin pendientes, 37 decisiones pendientes, 46 firmas con hueco, 1 carga externa (`db:impala`, parcial).
- `client_large.sas` (610 nodos, 610 etiquetas cubiertas): 662 componentes (49,8 % tJava), 397 subjobs, 30 cargas externas, 311 pasos sin pendientes, 293 decisiones pendientes, 43 firmas con hueco.

## Bloqueos abiertos y lo que hace falta del usuario

1. **Esquemas reales del entorno**: `env/schemas.json` solo tiene tablas de ejemplo (`ejemplo_lz.*`). Para que la pasada 9 asigne tipos al programa del cliente hacen falta sus esquemas reales (tablas de Impala y de LZ con tipos). No se inventaron.
2. **Motores de biblioteca**: `library_engines` está vacío. Las lecturas de `LZ.*` y otras bibliotecas permanentes no se ubican en base de datos hasta que se declare qué motor usa cada biblioteca. Con eso la pasada 4 podría empujar más operadores a la base.
3. **`%include` externo**: 104 ocurrencias apuntan a `/data/Programas_SAS/activenodelzcode.sas` (y otros). No están en el repositorio. Sus macros se desconocen.
4. **SQL sobre WORK y tJava (49,8 % en `client_large`)**: la escalera no tiene un componente específico para SQL sobre flujo, así que cae en `tJava` con revisión. Es la cifra más importante a revisar con el usuario: definir si el SQL de WORK se traduce a `tMap`/`tAggregateRow` (requiere un traductor de SQL a componentes) o se deja como revisión manual.
5. **Decisiones pendientes**: 293 en `client_large`, una por operador con alternativas. Conviene consolidarlas por firma con `sgm decisions set` (ya existe el comando; falta la decisión del usuario).
6. **Ejecución de `sgm.exe`**: una directiva de Control de aplicaciones de Windows bloqueó el lanzador `sgm.exe`. Se usa `uv run python -m sgm.cli ...` en su lugar. El comando `sgm` del `pyproject.toml` sigue definido.

## Entrega final (resumen)

1. Hitos terminados: 0 a 11, todos. Ninguno bloqueado.
2. Pruebas: 181 pasan, 1 se salta. `ruff check .` limpio.
3. Métricas de `out/metrics.json` (corpus completo: 189 programas): 629 nodos SAS, 1 690 componentes, nodos por componente 0,372, 25,7 % tJava, 189 Jobs, 958 subjobs, 1 030 pasos sin pendientes, 976 decisiones pendientes.
   - `client_large.sas`: 610 nodos, 662 componentes, nodos por componente 0,921, 49,8 % tJava, 397 subjobs, 311 pasos sin pendientes.
4. Top 10 de huecos: ver la sección del hito 10.
5. Bloqueos y lo que se necesita del usuario: sección anterior.
6. Decisiones de diseño tomadas por cuenta propia: en cada hito, en la sección "Decisiones" de este archivo.
7. Commits locales: lista arriba.

No se hizo `git push`. No se activó MCP.

# Ronda 2: agrupación real

Plan guardado en `docs/ronda2.md`. Regla de la ronda: `sgm metrics` antes y después de cada pasada, con los números anotados aquí.

## R0. Diagnóstico (sin cambiar comportamiento)

- Fecha: 2026-10-30
- Qué se hizo:
  - `ir/models.py` y `ir/builder.py`: cada operador lleva `origin` (constructo SAS de origen). No entra en la firma, así que las firmas, las decisiones y la caché no cambian. `Builder.created` guarda los operadores en orden de creación.
  - `ir/lower.py`: `origin_of` asigna el origen: `data_step`, `proc_sql_work`, `proc_sql_db`, `proc_<nombre>`, `macro_dinamica`, `include`, etc.
  - `passes/p08_partition.py`: registra el motivo de cada corte de subjob (`despues_de_write`, `iterate`, `antes_de_iterate`, `tamano_maximo`, `fin_del_programa`).
  - `metrics.py`: métrica principal `pasos_por_componente` (pasos del programa expandido, `ProgramItem`). Se conserva `nodos_por_componente`. Añade `cortes_de_subjob`, `firmas_de_decision`.
  - `diagnostics.py` (nuevo): `out/diagnostico.md` con componentes y tJava por origen, operadores por pasada (creados, fusionados, quitados), cortes de subjob y decisiones por firma. `sgm metrics` lo escribe.
- Pruebas: 181 pasan, 1 se salta. `ruff check .` limpio. Ningún número de compilación cambió (la línea base del corpus coincide con la ronda 1).

### Números antes (ronda 1, corpus de 189 programas)

- Pasos SAS 8 960; nodos SAS 629; componentes 1 690.
- Pasos por componente 5,302; nodos por componente 0,372.
- tJava 25,7 %; subjobs 958; decisiones 976 totales, 256 firmas únicas.
- `client_large.sas`: 5 152 pasos; 662 componentes; pasos por componente 7,782; 397 subjobs; tJava 49,8 %; decisiones 293 totales, 31 firmas únicas.
- `client_poc.sas`: 763 pasos; 67 componentes; pasos por componente 11,388; 14 subjobs; tJava 13,4 %; decisiones 37 totales, 12 firmas únicas.

### Desglose de componentes por origen (corpus)

| origen | componentes | tJava |
|---|---|---|
| `proc_sql_work` | 418 (24,7 %) | 406 |
| `data_step` | 434 (25,7 %) | 0 |
| creado por pasada (fusiones, plantillas, cargas) | 520 (30,8 %) | 29 |
| `proc_sort`, `proc_import`, `proc_export`, `proc_means`, `proc_append`, `proc_freq` | 287 (17 %) | 0 |

De los 520 "creados por pasada", 372 son `tRunJob` de plantillas (`iterate`).

### Causas confirmadas (con números)

1. **PROC SQL sobre WORK termina en tJava. Confirmada.** `client_large.sas` tiene 301 sentencias `CREATE TABLE ... AS SELECT` como `exec_sql` con estado `parcial` (sin análisis de SQL). La regla de último recurso (`05-tjava-last-resort`) las manda a `tJava`. En el corpus son 406 de los 435 `tJava` (93 %).
2. **Nada se ubica en la base. Confirmada.** `client_large.sas` tiene 77 lecturas: 68 de `WORK`, 8 de `db:impala` y 1 de `WLIBORG`. La pasada 4 deja 69 en flujo. Las lecturas de WORK vienen de DATA steps y de `proc import`/`read_file`, no solo de CSV: el origen real es mixto.
3. **La maquinaria de carga no se absorbe. Confirmada en los huecos.** En `client_large.sas` cada una de estas firmas aparece 30 veces o más: `%sysevalf`, `%sysfunc(pathname(...))`, `select ... into:`, `sessio&i %end`, `proc contents ... _all_`, `%sysfunc(open/close)`, `%sysfunc(countw)`, `%include` externo. Por qué p03 no las absorbe: se confirma en R3 (hipótesis: están fuera del tramo entre el primer grupo de lanzamiento y el de espera).
4. **Los subjobs no se cortan por nodo, se cortan por escritura y por plantilla. Parcialmente distinta de la hipótesis.** En el corpus, los cortes son: `despues_de_write` 403, `iterate` 372, `antes_de_iterate` 80, `fin_del_programa` 62, `despues_de_external_load` 31, `tamano_maximo` 10. En `client_large.sas`: `iterate` 249, `antes_de_iterate` 75, `despues_de_external_load` 30, `despues_de_write` 35.

### Causa no prevista en el plan

- **`tRunJob` por instancia de plantilla.** En `client_large.sas`, 249 de 662 componentes (38 %) son `tRunJob`, uno por instancia de la plantilla de `iterate` (p07). Cada llamada a una macro de carga por tabla se convierte en un Job hijo. Es el mayor bloque de componentes del caso grande y no estaba en las cuatro causas. Se atiende en R3 (absorción de la maquinaria) y R8 (partición).

### Lo que dice el diagnóstico de decisiones

- Corpus: 976 decisiones y 256 firmas. `client_large.sas`: 293 decisiones y 31 firmas. Cada firma aparece varias veces: el usuario elige 31 veces, no 293 (se trata en R9).

## R1. Configuración de entorno y proyecto

- Fecha: 2026-10-30
- Qué se hizo:
  - `env/engines.json`, `env/project.json` y `env/externals.json` con los valores del prompt. Cada DSN y esquema se comprobó en el código: `IMPALA`, `IMPALAC` e `IMPALAP` aparecen en `connect`; `proceso_vspc_finanzas`, `resultados_vspc_clientes` y `s_canales` aparecen en el código del cliente. No se añadió ningún otro.
  - `env/externals/` con su README. Un `.sas` ahí se lee como fuente y sus macros se expanden.
  - `catalog/config.py`: carga y validación de los tres archivos (`load_env`). Cada error nombra el archivo y el campo. Un archivo ausente usa sus valores por defecto. Sin dependencias nuevas.
  - `frontend/program.py` y `frontend/macros.py`: los archivos de `env/externals/` se indexan y se expanden, pero no son programas. Un `%include` se casa con ellos por nombre de archivo.
  - `ir/lower.py`: un `%include` declarado genera un operador `INCLUDE_DECLARADO` con estado `reemplazado` (o `parcial` si `as_context` es falso). No es hueco. `compile.py` lo registra en `not_migrated` y, si `as_context`, sus variables pasan a `Job.contexts`.
  - `compile_batch` y `compile_project` reciben `env`. El CLI carga `env/` una vez y, si hay un error de configuración, sale con código 2 y el mensaje.
- Pruebas: `tests/unit/test_config.py` con 20 casos: validación de cada archivo, valores del repositorio, `%include` declarado (no hueco, contextos, no migrado), no declarado (sigue siendo hueco), `as_context: false` (sin contextos), archivo presente en `externals/` (se expande), y que un externo no se compila como programa. Total: 201 pasan, 1 se salta. `ruff check .` limpio.
- Efecto medido (`sgm metrics` con `env/`):
  - Corpus: `INCLUDE_EXTERNO` de `activenodelzcode.sas` desaparece (30 ocurrencias en `client_large`). Quedan 70 `INCLUDE_EXTERNO` de otros archivos.
  - Pasos, componentes, tJava, subjobs y decisiones no cambian: R1 no toca la ubicación ni la partición.
- Lo que R1 valida pero aún no ejecuta (se activa en su hito):
  - `placement_strategy` (`push_to_db`): lo usa R5. Hoy no cambia la ubicación.
  - `reports`: lo usa R6.
  - `max_components_per_job`: lo usa R8. Hoy `p08` sigue con 200 fijo.
  - `dsn` de `engines.json`: solo referencia. Lo usa R2 para el contexto `lz_dsn`.
- Bloqueos abiertos: ninguno nuevo. Los esquemas reales siguen pendientes (bloqueo 1 de la ronda 1).

## Decisiones (R1)

- `%include` declarado sin `as_context` queda `parcial` y no crea contextos. Así no se inventa que sus variables son contexto.
- Un archivo de `env/externals/` gana sobre la declaración de `externals.json`: si está presente, se lee el contenido real y no se usan las variables declaradas.
- Los valores que el código no demuestra no se agregan. `libraries` queda vacío porque ninguna biblioteca LZ tiene motor demostrado (bloqueo 2 de la ronda 1).

## R2. Contextos desde macros de ambiente

- Fecha: 2026-10-30
- Qué se hizo:
  - `frontend/selectors.py`: `detect(name, body)` reconoce por estructura un selector: una cadena `%if &X eq <lit> %then %do; %let Y=<valor>; %end;` seguida de una o más ramas `%else %if &X eq <lit> ...`, y como mucho un `%put`. Exige al menos dos literales y la misma variable `X` en todas las ramas. No mira nombres.
  - `frontend/macros.py`: el expansor detecta los selectores al indexar. Una invocación de selector no expande sus ramas: registra un `SelectorUse` y devuelve un `Expanded` vacío.
  - `ir/models.py` y `emit/plan_json.py`: `Job.context_groups`, con `selector`, `variables` y `contextos` (literal -> {variable: valor}).
  - `compile.py`: cada selector invocado en el programa crea su grupo y un `NotMigrated` con id `selector:<nombre>`.
- Pruebas: `tests/unit/test_selectors.py` (7 casos). Detección con nombres aleatorios; un solo literal, rama sin literal, variables distintas o código extra no son selector; el programa con selector no genera operadores; el selector real de `client_poc.sas` da `ambiente` con `lz_dsn` y D→IMPALA, C→IMPALAC, P→IMPALAP.
- Golden: se regeneraron las cuatro referencias. Las tres sencillas solo cambian por la clave nueva `context_groups`. `client__client_poc` pierde 12 operadores `CONFIGURACION` que salían de expandir las ramas del selector. Sus componentes siguen en 82.
- Pruebas totales: 208 pasan, 1 se salta. `ruff check .` limpio.

### Efecto medido (con `env/`)

- Corpus: pasos SAS 8 960 → 8 722 (238 pasos de ramas de selector ya no cuentan como pasos). Componentes 1 690 sin cambio. Pasos por componente 5,302 → 5,161 (por el denominador). Subjobs 958 → 957.
- `client_large.sas`: pasos 5 152 → 4 942 (210 pasos de ramas de selector). Pasos por componente 7,782 → 7,465. Componentes 662 sin cambio.
- `client_poc.sas`: pasos 763 → 735 (28 pasos de ramas de selector). Pasos por componente 11,388 → 10,97. Componentes 67 sin cambio.
- El cambio de la métrica de pasos viene de cómo se cuentan los pasos, no de agrupar mejor. Los componentes no cambian en R2.

## Decisiones (R2)

- La detección exige al menos dos literales. Con uno solo, no hay elección de ambiente y el `%if` se trata como antes.
- Un selector se detecta por macro, no por archivo: un selector definido en otro archivo del proyecto también vale.
- El grupo de contexto se guarda por nombre de macro (`ambiente`), y no por variable, porque una macro puede tener varias variables Y.

## R3. La pasada 3 absorbe toda la maquinaria de carga

- Fecha: 2026-10-30
- Causa confirmada antes de cambiar nada (R0 con el grafo de operadores antes de p03): en el primer bloque de `client_large.sas`, la preparación (`%let` con `pathname`, `%sysevalf`, `%sysfunc(open/close)`), el troceo (`%split2`: `signon`, `%syslput`, `rsubmit wait=no`, `waitfor`, `sessio&i`), la lista de tablas (`proc contents ... _all_`, `select ... into :`, `countw`) y la limpieza están **antes** del lanzamiento o **después** de la espera. La versión anterior de p03 solo tomaba el tramo entre ambos. Por eso los huecos de la maquinaria salían 30 veces (una por bloque).
- Qué se hizo:
  - `passes/region.py` (nuevo): reconocimiento de la región. `FactBook` calcula por operador si es lanzamiento, espera, qué macro variables y datasets define y usa, si es fontanería o configuración, y a qué invocación de macro pertenece. `Flow` mira la liveness: una definición solo tiene como consumidores los usos antes de su siguiente redefinición (los bloques repetidos reutilizan los mismos nombres). `grow` amplía la región hacia atrás y hacia delante por unidades, y un vecino lejano entra con todo lo que hay en medio.
  - `passes/p03_intrinsics.py`: el `external_load` absorbe la región entera. Añade `params.verify_count` (hay un `select count(*)` dentro) y `params.absorbed` (operadores absorbidos).
  - `passes/base.py` y `compile.py`: `PassContext.macro_params`, con los parámetros de cada macro. Al empezar una invocación, sus parámetros toman valor del llamador.
  - `passes/plumbing_patterns.py`: corrección. `x\s` marcaba como comando de shell cualquier sentencia `x = ...;` de un DATA step. Ahora solo `x "..."`, `x '...'` o `x &...`.
- Pruebas: `tests/unit/test_carga_externa.py` (6 casos). La maquinaria completa con nombres aleatorios queda en un único `external_load` con la evidencia de todas sus líneas; no quedan huecos de troceo ni de preparación; una variable usada por un DATA step posterior a la carga no entra; sin lanzamiento no hay carga; dos bloques dan dos regiones; `x = ...;` no es comando.
- Golden: `client__client_poc` cambia (cuatro cargas, ver abajo). `test_compile_outputs` pasa de esperar 1 carga a 4 (un bloque de escritura por tabla: ACURA, BMW, CHEVROLET, JAGUAR). Pruebas totales: 214 pasan, 1 se salta. `ruff check .` limpio.

### Criterios de salida de R3 (con `env/`)

| Firma de hueco | `client_large.sas` antes | después | `client_poc.sas` antes | después |
|---|---|---|---|---|
| `%let workpath=%sysfunc(cat(%sysfunc(pathname(work))...` | 30 | 0 | 1 | 0 |
| `%sysfunc(countw(...))` | 30 | 0 | — | 0 |
| `%sysevalf(...)` | 30 | 0 | 3 | 0 |
| `sessio&i %end` | 30 | 0 | — | 0 |
| `proc contents data=work._all_` | 30 | 0 | 1 | 0 |
| `select ... into :` de conteo | — | 0 | — | 0 |

- En `client_large.sas` quedan 10 `SELECT ... INTO` de año, mes y día (`validacion_fecha`). No son de conteo y no pertenecen a la región.
- En `client_large.sas` quedan 26 `PROC DOWNLOAD` (transferencia desde un recurso compartido). Están antes de los bloques de carga, en la preparación de entrada. No entran en la región; es un hueco de entrada aparte.

### Cifras (`sgm metrics` sobre el corpus, con `env/`)

| Métrica | Antes de R3 (con `env/` de R1–R2) | Después de R3 |
|---|---|---|
| Componentes (corpus) | 1 690 | 1 605 |
| Pasos SAS por componente (corpus) | 5,161 | 5,434 |
| tJava (corpus) | 25,7 % | 25,2 % |
| `client_large.sas`: componentes | 662 | 603 |
| `client_large.sas`: `tRunJob` | 249 | 188 |
| `client_large.sas`: cargas externas | 30 (parciales, tJava) | 30 (`tImpalaOutput`) |
| `client_large.sas`: subjobs | 397 | 425 |
| `client_large.sas`: tJava | 49,8 % | 49,8 % |
| `client_large.sas`: decisiones | 293 totales, 31 firmas | 230 totales, 26 firmas |
| `client_poc.sas`: componentes | 67 | 37 |
| `client_poc.sas`: tJava | 13,4 % | 24,3 % |

- Lectura honesta: R3 quita componentes (los de la maquinaria y las plantillas de carga), no quita `tJava`. El `tJava` de `client_large` viene del SQL (`proc_sql_work`), que es R4. En `client_poc` el porcentaje sube porque bajan los componentes totales; los nueve `tJava` siguen ahí.
- Los subjobs de `client_large` **suben** (397 → 425). El corte tras cada escritura pasa de 35 a 132: ahora la región absorbe a los bloques completos y sus escrituras ya no se reparten entre bloques más pequeños. R8 (partición por componente conexo) es el hito que lo corrige. Se registra aquí en vez de ocultarlo.

## Decisiones (R3)

- La región se detecta por estructura (lanzamiento en segundo plano, espera con conteo de procesos). Nunca por nombres de macro.
- Una definición la lee la región si su siguiente uso está en la región y antes de la siguiente redefinición. No se cuentan usos de otros bloques que reutilizan el mismo nombre.
- Un dataset que la región lee es la **entrada** de la carga: su productor no entra. Solo entran macro variables de preparación, fontanería, configuración, y pasos de la misma invocación de macro que la región.
- Dentro de `rsubmit ... endrsubmit` los datasets no son locales (corren en otra sesión): solo cuentan las macro variables.
- Los parámetros de una macro se tratan como definidos al empezar cada invocación (así `%syslput tabla_origen` no se confunde con el valor del bloque siguiente).
- `PROC DOWNLOAD` no se absorbe: no está entre los criterios de R3 y ocurre antes del bloque de carga.

## R4. PROC SQL nunca termina en tJava

- Fecha: 2026-10-30
- Dependencia nueva: `sqlglot` 30.27.0 (`uv add sqlglot`). Anotada en "Decisiones".
- Qué se hizo:
  - `frontend/sql_normalize.py` (nuevo): normaliza el SQL de SAS antes de parsearlo. Quita `into :var [separated by]` (lo guarda), sustituye `&macro` por `mv_macro` (con la vuelta atrás), `%funcion(` por `fn_funcion(`, convierte `eq ne gt lt ge le`, `contains`, `is [not] missing`, `calculated x`, comillas dobles de texto, literales de fecha `"..."d`, `format=`/`informat=` y opciones de dataset `(where=..)`, `(obs=..)`. Cada quita queda anotada en `notes`.
  - `ir/sql_tree.py` (nuevo): parsea con `sqlglot` y extrae la estructura: fuentes, uniones (`JoinSpec` con pares de clave y el `ON` completo), `SELECT` (expresiones y alias), `WHERE`, `GROUP BY`, `HAVING`, `DISTINCT`, `ORDER BY`, `UNION`/`UNION ALL`, subconsultas y funciones de ventana. Un texto que no parsea lanza `SqlParseError` (PARSE_ERROR). Una sentencia que no es consulta lanza `SqlNotSelect`.
  - `ir/lower_sql_flow.py` (nuevo): convierte la consulta en cadena de operadores de flujo, en orden lógico de SQL: `read` y `join` → `filter` (WHERE) → `aggregate` (GROUP BY y funciones de agregado) → `filter` (HAVING, con la agregación sustituida por su alias) → `derive` (expresiones con alias) → `dedup` (DISTINCT) → `sort` (ORDER BY). Un UNION une las ramas con `union`. El destino va en `outputs` (p01 añade la escritura). `SELECT ... INTO :var` va a `set_variable`.
  - `ir/lower_sql.py`: `create table` y `select` usan ese camino. `insert`, `delete`, `create like` y `drop` quedan como hueco `SQL_NO_SOPORTADO` (o plumbing si son limpieza). Ya no se crea ningún `exec_sql` sobre WORK.
  - `ir/sql_render.py` (nuevo): genera SQL de base en dialecto Hive desde el árbol. `sqlglot` no tiene dialecto de Impala; Hive es el más cercano. Un nombre con macro variable no se escribe (`ValueError`). Lo usará R5.
  - `ir/models.py` y `rules/mapping/02-set-variable.yaml`: nuevo tipo de operador `set_variable` → componente `tSetGlobalVar`.
  - `frontend/macros.py`: un `select ... into :var` ya no es `MACRO_DINAMICA`: llega al analizador de SQL.
  - `passes/p10_components.py`: **defecto de la ronda 1 corregido**. La regla de último recurso (`05`, con `kind: "*"`) se aplicaba a cualquier operador antes que la excepción de `_tjava`. Así una lectura de un motor no declarado caía en `tJava`. Ahora el peldaño 5 solo lo aplica `_tjava`. La excepción se acota a lo que va a la base: un SQL de **flujo** sin regla sí es `tJava`.
- Pruebas: `tests/unit/test_sql_flujo.py` (una prueba por construcción de la lista del plan, más función no traducida, texto no parseable, `IS MISSING`, `CONTAINS`, `INTO` con separador, macros, opciones de dataset, y un caso del cliente sin `tJava` de origen SQL), `tests/unit/test_sql_render.py` (SQL Hive válido, UNION ALL, macro en destino rechazada, fecha de SAS, `format=`). `test_ir_rules` y `test_components` se actualizaron al comportamiento nuevo. Golden: `p0_ejemplo_basico` (un `exec_sql` tJava pasa a `read` + `tAggregateRow`) y `client__client_poc`. Total: 240 pasan, 1 se salta. `ruff check .` limpio.

### Criterios de salida de R4

- **0 `tJava` cuyo origen sea PROC SQL en todo el corpus: cumplido** (antes 405 en el corpus, 301 en `client_large`).
- Corpus (`sgm metrics`): `tJava` 25,2 % → **0,0 %**. Componentes 1 605 → 1 663 (las consultas ahora son varios operadores de flujo).
- `client_large.sas`: `tJava` 49,8 % → **0,0 %**. Componentes 603 → 606. `tAggregateRow` 24, `tFilterRow` 16, `tMap` 148, `tSetGlobalVar` 12.
- `client_poc.sas`: `tJava` 24,3 % → 0,0 %. Componentes 37 → 34.

### Lo que sube y se registra (no se oculta)

- **Subjobs**: `client_large` 425 → 537. Cada consulta que crea una tabla termina en una escritura, y la partición corta después de cada escritura. R8 corta por componente conexo y lo corrige.
- **Decisiones**: `client_large` 293 → 520 totales y 31 → 70 firmas (corpus: 885 → 1 339 totales, 251 → 352 firmas). Cada operador de flujo con alternativas (`tMap` frente a `tFilterRow`, etc.) genera una decisión. R9 las agrupa por firma.
- **Ronda 1, peor de lo que parecía**: el `tJava` de SQL no venía solo de `exec_sql`. La regla 05 también capturaba lecturas de motores no declarados. Corregido.

### Límites que quedan (honestos)

- El traductor de expresiones (copiado de la ronda 1) **no traduce comparaciones de igualdad con columnas de tipo desconocido** (`x = 1` sobre una columna sin tipo: "validar conversión"), y no tiene `CASE`. Esas expresiones quedan pendientes (`FUNCION_NO_MAPEADA`) y el componente no cambia. R7 (tipos desde el código) resuelve la primera; `CASE` necesita trabajo en el traductor.
- `sqlglot` avisa por el log cuando cae a un comando. Se silencia en `sql_tree.py`.
- Las consultas en la base (pass-through) se siguen generando como antes. El SQL de Hive (`sql_render.render`) existe y tiene pruebas, pero la pasada 4 **no** lo usa todavía: decidir que una consulta de flujo se ejecute en la base es R5.

## Decisiones (R4)

- `sqlglot` (30.27.0) para parsear el SQL. Es la única dependencia nueva de la ronda 2.
- No hay dialecto `impala` en `sqlglot`: se usa `hive`, como indica el plan.
- SQL de SAS que `sqlglot` no lee se normaliza antes (`sql_normalize.py`), y cada quita se anota.
- Ninguna consulta sobre WORK se queda como `exec_sql` opaco. Lo que no se puede analizar es `PARSE_ERROR`; lo que se analiza pero no se traduce es un operador de flujo con una expresión pendiente.
- `IS NULL`/`IS NOT NULL` se escriben como `missing(x)` (la forma que el traductor sí acepta).

## R5. Estrategia de ubicación "cargar una vez, calcular en la base"

- Fecha: 2026-10-30
- Qué se hizo (con `placement_strategy = "push_to_db"`; con `flow` el comportamiento es el de R4):
  - `passes/db_sql.py` (nuevo): qué se puede ejecutar en la base. Solo entran `filter` (WHERE), `derive`, `aggregate` (GROUP BY), `sort` (ORDER BY) y `dedup` sin claves (DISTINCT), en cadena lineal. `sas_to_sql` pasa la expresión de SAS a SQL (`missing(x)` → `x IS NULL`, `^=` → `<>`) y comprueba con `sqlglot` que se puede leer. Una expresión con macro variable, o que no se lee como SQL, no entra.
  - `passes/db_push.py` (nuevo): `place` (pasada 4) ubica en la base las cadenas candidatas; cada `read_file` que las alimenta se convierte en **una sola** carga (`external_load` a la tabla `sgm_<firma corta>`, nunca el nombre del script); las lecturas de WORK con un único productor se quitan (son solo referencias). `fuse` (pasada 5) sustituye cada cadena por un `exec_sql` con su `CREATE TABLE ... AS` en dialecto Hive. La fuente (carga o lectura de base) se queda fuera del reemplazo.
  - `passes/p04_placement.py`: rama `_push_to_db`. Los cruces base↔flujo siguen con sus `read`/`write` de frontera.
  - `passes/p05_sql_fusion.py`: llama a `fuse` en modo push.
  - `graph.merge` (`ir/models.py`): **defecto corregido**. Las aristas fusionadas conservaban el extremo antiguo (`src`/`dst` de un nodo eliminado), lo que rompía los cruces.
- Pruebas: `tests/unit/test_push_db.py` (5 casos). El caso del plan: CSV → WHERE y columna calculada en SQL → exportación a CSV. Con `push_to_db`: una carga (`tImpalaOutput`), un `exec_sql` fusionado (`tImpalaRow`) con el filtro y la columna calculada en el SQL, y un `write_file` en el flujo con su `read` de frontera; ningún `tJava`. Con `flow`: `tFileInputDelimited`, `tFileOutputDelimited` y ningún componente de base. Total: 245 pasan, 1 se salta. `ruff check .` limpio.

### Números (`sgm metrics` con `env/`, `push_to_db`)

| Métrica | R4 | R5 |
|---|---|---|
| Componentes (corpus) | 1 663 | 1 475 |
| `tJava` (corpus) | 0,0 % | 0,0 % |
| `client_large.sas`: componentes | 606 | 457 |
| `client_large.sas`: subjobs | 537 | 284 |
| `client_large.sas`: `tImpalaRow` / `tImpalaOutput` / `tImpalaInput` | 1 / 30 / 17 | 21 / 31 / 17 |
| `client_large.sas`: cadenas fusionadas | 0 | 20 (todas de 2 pasos) |
| `client_poc.sas`: componentes | 34 | 37 |

### Criterio de salida: "cadenas largas de SQL fusionado" — **no cumplido**

Las cadenas fusionadas de `client_large.sas` tienen 2 pasos (20 cadenas). Lo que lo impide, medido sobre los operadores de SQL que quedan en flujo (130):

- **`aggregate` en flujo (39)**: se alimentan de tablas WORK que produce un DATA step (flujo), o de dos entradas (un `join`, que queda en flujo). Una cadena de base empieza solo en una carga o una lectura de base.
- **`derive` y `filter` con funciones de SAS sin equivalente SQL (~60)**: `compress`, `input`, `left`, `substr`, etc. No hay traducción de funciones a SQL. Hace falta la tabla de funciones de `rules/sas/sql-functions.json` aplicada a la expresión, y los tipos (R7) para `input`.
- **Comparaciones de igualdad con columnas de tipo desconocido**: el traductor no las acepta (ver R4). Lo resuelven los tipos de R7.

Es decir, el cuello de botella de la ubicación en base no es la pasada 4 sino la falta de tipos y de traducción de funciones. Se deja anotado para la ronda siguiente, en vez de forzar cadenas que no son exactas.

### Lo que sí se cumple

- Una carga única por archivo: las lecturas repetidas del mismo archivo (el mismo destino) se fusionan en la primera (`client_large`: `sgm_fb09f3a9` aparecía 4 veces; ahora una).
- Ninguna tabla de trabajo lleva el nombre de un script: `sgm_<firma corta>`.
- Ningún `tJava` en la base; un SQL de base sin SQL no existe (la candidatura comprueba `sas_to_sql` antes de ubicar).

## Decisiones (R5)

- Los `join` y `union` no entran en la base: sin esquemas no se califican las columnas. Quedan en flujo y su entrada desde base se corta con un `read` de frontera.
- `dedup` solo se ejecuta en base sin claves (DISTINCT). Con claves haría falta `ROW_NUMBER` y un esquema.
- Las tablas de trabajo llevan el prefijo `sgm_` fijo. El plan pide un prefijo configurable; queda como mejora (no hay campo en `env/project.json`).
- Una cadena que produce una tabla que lee el flujo tiene como nombre de salida el dataset de su arista (sin `WORK.` y sin `.`), para que el `read` de frontera encuentre la misma tabla.

## R6. Reportes y PROC CONTENTS

- Fecha: 2026-10-30
- Qué se hizo:
  - `ir/lower_procs.py`: `PROC PRINT`, `PROC REPORT` y `PROC CONTENTS` sin `OUT=` pasan a un hueco de tipo `REPORTE` (con su dataset de entrada). Con `OUT=` (dataset que otros pasos leen) siguen como hueco `PROC_NO_SOPORTADO`.
  - `passes/p02_plumbing.py`: la política `reports` de `env/project.json` decide. `discard` (por defecto): no migrado, con la nota "reporte de diagnóstico, no se migra". `log`: un `report` que va a `tLogRow` (`rules/mapping/02-report-log.yaml`, tipo nuevo `report`). `csv`: un `write_file` con `outfile = contexto.ruta_<procedimiento>`, de modo que la ruta es un contexto del Job.
- Pruebas: `tests/unit/test_reportes.py` (5 casos: `discard` no migra y no es hueco; `log` usa `tLogRow`; `csv` escribe con la ruta como contexto; `OUT=` sigue siendo hueco; en el cliente con `discard`, desaparecen `PROC PRINT` y `PROC CONTENTS` de los huecos). `test_ir_rules` usaba `proc print` como ejemplo de procedimiento sin regla: ahora usa `proc univariate`. Total: 251 pasan, 1 se salta. `ruff check .` limpio.

### Criterio de salida: con `discard`, PROC PRINT y PROC CONTENTS fuera del top de huecos — **cumplido**

| Firma en el top de huecos (corpus) | Antes (R5) | Después (R6) |
|---|---|---|
| `proc contents data=Mozart.Test_Scores ...` | 86 | fuera del top |
| `proc print data=Veg...` | 31 | fuera del top |
| `proc contents data=work._all_ ...` (no absorbido) | 31 | fuera del top |

El top de huecos ahora lo ocupan las expresiones `input(...)` y `COMPRESS(input(...))` sin traducción (220, 160, 150, 80, 75 ocurrencias): es el trabajo de R7 (tipos) y de traducción de `input`.

## Decisiones (R6)

- Un `PROC CONTENTS` con `OUT=` no es un reporte: produce un dataset que otros pasos leen. Se queda como hueco.
- Un reporte de `log` o `csv` se convierte en la pasada 2 (con la política), y no en el lowering, que no conoce la configuración.

## R7. Tipos desde el propio código

- Fecha: 2026-10-30
- Qué se hizo:
  - `ir/types_code.py` (nuevo): tipos que el código fija sin ambigüedad. `input(x, w.)` y `input(x, w.d)`: `Long` si no hay decimales y `w <= 18`, `BigDecimal` con decimales, `Double` en otro caso. Informats de fecha u hora: `Date`. `put(x, w.)`: `String` de longitud `w`. `cast(x as T)`: el tipo del cast. Literales: entero `Long`, decimal `Double`, texto `String`. Aritmética sobre números: `Double`. Funciones de SAS de carácter (`compress`, `substrn`, `cats`, `left`...) y numéricas (`int`, `round`, `sum`...), cuando la llamada es la expresión completa. Declaraciones del DATA step: `length v $ n`, `length v n`, `format` e `informat`.
  - `ir/lower_data.py`: las declaraciones del DATA step se guardan en sus derivaciones (`params.declared`).
  - `passes/p09_schemas.py`: origen `code`. Prioridad catálogo, encabezado, código, derivado: una columna que ya tiene tipo no se cambia. Una derivación sin esquema de entrada (o un `map`) sigue dando tipo a las columnas que el código fija.
- Pruebas: `tests/unit/test_tipos_codigo.py` (11 casos): reglas de informat, `input`/`put`/`cast`, literales y aritmética, funciones, declaraciones, prioridad del catálogo, derivada sin tipo que sigue desconocida, y un DATA step que tipa sus columnas. `test_sql_flujo`: el `CASE` (sin traducción) ahora da también `TIPO_DESCONOCIDO` para su columna, que es lo correcto. Goldens regenerados: en las referencias solo cambian los huecos de tipo; las firmas de operadores no cambian. Total: 261 pasan, 1 se salta. `ruff check .` limpio.

### Criterio de salida: el DATA step de tipado de `VARn` produce tipo para las columnas que convierte — **cumplido, con una excepción**

- En `client_large.sas` hay 21 columnas convertidas con `input(...)` dentro de DATA steps. **20 reciben tipo** (`Long`, `Double` o `String` según el informat o la función). La restante (`sum_pesos`) mezcla `input(...)` con operandos sin tipo: sigue desconocida, como debe.
- Antes de R7 solo 1 de 21 tenía tipo. La causa era que sin esquema de entrada no se calculaba la derivación, ni dentro de un `map` fusionado.

### Cifras (`sgm metrics`)

| Métrica | R6 | R7 |
|---|---|---|
| Componentes (corpus) | 1 475 | 1 475 (sin cambio) |
| Subjobs (corpus) | 779 | 779 (sin cambio) |
| Decisiones (corpus) | 1 033 totales, 292 firmas | 1 033 totales, 294 firmas |
| Huecos `TIPO_DESCONOCIDO` | 0 en el top | Visibles: 4 en `client_poc`, 41 en `client_large` (antes ocultos) |

Tipar no cambia la agrupación; cambia la calidad del esquema y lo que queda declarado como desconocido.

### Lo que sigue en el top de huecos (no es tipado)

- `input(left(VAR7), 30.)` y `COMPRESS(input(...))`: **220, 160, 150, 80 y 75** ocurrencias. El tipo ya se conoce, pero el traductor de expresiones no sabe convertir `input` a Java. Es el siguiente hueco más caro: traducir `input` (numérico y texto) en el traductor.

## Decisiones (R7)

- Un `derive` o un `map` sin esquema de entrada conservan las columnas que el código tipa. Así las derivaciones de un DATA step se tipan aunque la lectura de origen no tenga esquema. Las demás columnas siguen sin tipo.
- `COMPRESS`, `SUBSTR`, `CAT` y similares dan `String`, y `INT`, `ROUND`, `SUM` y similares dan `Double`. Son reglas de SAS, no suposiciones sobre los datos.
- Un informat de fecha o de hora da `Date`, sin distinguir `date` de `datetime`. El plan lo pide así.

## R8. Partición por componente conexo

- Fecha: 2026-10-30
- Qué se hizo:
  - `passes/p08_partition.py`: un subjob es un componente conexo de conexiones de filas. Ya no hay un subjob por nodo ni por etiqueta: la etiqueta es solo la del componente. Los operadores de control (`exec_sql`, `external_load`, `iterate`) van cada uno en su propio subjob, ordenados por OnSubjobOk. Un operador sin componente (configuración, huecos, pasos reemplazados, y los `read`/`write` de flujo que solo traspasan un dataset WORK) no ocupa subjob y une a sus vecinos. Un componente que supera `max_components_per_job` (`env/project.json`, 200) se parte en trozos en orden topológico, con el motivo `tamano_maximo`.
  - `passes/p07_templates.py`: las instancias de una misma plantilla se sustituyen por **una sola** llamada en bucle (`iterate` con `params.instancias`, la alternativa `tFlowToIterate`). Solo si el grafo sigue siendo acíclico al contraerlas (`networkx`); si una instancia depende de un operador común, se mantiene una llamada por instancia.
  - Defectos corregidos durante la prueba: un `iterate` colapsado sin comprobar aciclicidad creaba ciclos (fallaban `compile` y `test_compile_outputs`).
- Pruebas: `tests/unit/test_subjobs.py` (5 casos: dos flujos de distinta forma son dos subjobs; una cadena de filas es uno; una sentencia de base es su propio subjob; el límite de componentes parte en trozos, construido sobre el grafo; el orden es topológico). `test_fusion_partition` se actualizó: una sola llamada en bucle para las tres ramas iguales, y la cadena lineal se comprueba por su contenido. Goldens regenerados (solo cambian subjobs e `iterate`). Total: 270 pasan, 1 se salta. `ruff check .` limpio.

### Criterio de salida: subjobs ≤ 198 en `client_large.sas` — **cumplido**

| Métrica | R7 | R8 |
|---|---|---|
| `client_large.sas`: subjobs | 284 (ronda 1: 397) | **196** |
| `client_large.sas`: `tRunJob` | 107 | 53 |
| `client_large.sas`: componentes | 457 | 403 |
| `client_large.sas`: subjobs por motivo | — | componente conexo 91, `exec_sql` 21, `external_load` 31, `iterate` 53 |
| `client_poc.sas`: subjobs | 8 | 10 (1 componente de 29 operadores + 9 de control) |
| Corpus: subjobs | 779 | 750 |
| Corpus: componentes | 1 475 | 1 328 |
| Corpus: `tJava` | 0,0 % | 0,0 % |

- La cifra de componentes del corpus baja (1 475 → 1 328) porque los `read`/`write` de flujo sin componente ya no cuentan como componentes candidatos, y las plantillas comparten una sola llamada.
- Los `iterate` restantes (53) son las plantillas que el grafo permite colapsar; las demás siguen con una llamada por instancia.

## Decisiones (R8)

- Un `read` o `write` de flujo (que solo referencia un dataset WORK) **no** ocupa subjob. Su componente es `none`, así que contarlo inflaba el número de subjobs con piezas de un solo operador.
- El colapso de plantillas se comprueba con aciclicidad del grafo contraído. Un colapso que rompiera el orden se rechaza, y se mantienen las llamadas por instancia.
- Los `exec_sql`, `external_load` e `iterate` son subjobs propios: en Talend un `tRunJob` o una sentencia de base no comparten subjob con filas sin un trigger.

# R9. Decisiones agrupadas

- Fecha: 2026-10-30
- Qué se hizo:
  - `sgm/decisions.py` (nuevo): agrupa las decisiones pendientes por firma (operadores que la comparten, archivos distintos, opciones y valor por defecto), y calcula decisiones totales y firmas únicas.
  - `sgm decisions pendientes <fuente>` (nuevo comando): muestra el total de decisiones y de firmas únicas, y la lista por firma de la más frecuente a la menos frecuente. `sgm metrics` ya reporta ambas cifras.
- Pruebas: `tests/unit/test_decisiones.py` (3 casos: una firma compartida por dos archivos cuenta un operador por archivo; los totales distinguen decisiones de firmas; sin alternativas no hay decisiones).
- Uso real (`client/`): 316 decisiones pendientes, 58 firmas únicas. La firma más frecuente (`temp_table` frente a `hash`) tiene 58 operadores: se elige una vez, no 58.

## R10. Verificación y entrega (ronda 2)

- Fecha: 2026-10-30
- Verificación:
  - `uv run pytest`: 270 pasan, 1 se salta (un symlink que Windows no permite crear). `ruff check .` limpio.
  - `sgm compile tests/fixtures/sas --out out --no-cache`: sale con código 0; 189 programas, todas las guías y planes escritos.
  - `sgm metrics tests/fixtures/sas`: `out/metrics.json` y `out/diagnostico.md` con el estado final.
  - Secretos: `pwencode` sin enmascarar, en `out/` ni en `tests/`: ninguno (la coincidencia de `grep` es `pwencode in='***'`). Ningún `pass=` en claro.
  - Guía de `client_large.sas`: se añadió la sección `## Etapas` (una fila por subjob). Son **196 etapas**: cumple el criterio numérico, pero no se lee como "pocas etapas". Queda como deuda (ver abajo).

### Metas de la ronda 2 (`client_large.sas`)

| Métrica | Ronda 1 | Meta | Alcanzado |
|---|---|---|---|
| `tJava` | 49,8 % | 10 % o menos | **0,0 %** |
| `tJava` con origen PROC SQL | sin medir | 0 | **0** (corpus: 0) |
| Componentes frente a pasos SAS | más componentes que nodos | menos componentes que pasos SAS | **403 componentes frente a 4 808 pasos** (pasos por componente 11,9) |
| Subjobs | 397 | 198 o menos | **196** |
| Huecos de la maquinaria de carga | 6 firmas en el top 10 | 0 | **0** (`WORKPATH`, `COUNTW`, `SYSEVALF`, `sessio&i`, `PROC CONTENTS ... _ALL_`). Quedan 10 `SELECT ... INTO` de año, mes y día, que no son de conteo. |
| Decisiones | 293 totales | reportar firmas únicas | **302 totales, 55 firmas únicas** (`sgm decisions pendientes`) |

- `client_poc.sas`: componentes 67 → 37; `tJava` 13,4 % → **0,0 %**; subjobs 14 → 10.
- Corpus (189 programas): componentes 1 690 → **1 328**; `tJava` 25,7 % → **0,0 %**; subjobs 958 → **750**; decisiones 976 (256 firmas) → 886 (306 firmas).

### Desglose de R0, antes y después (componentes por origen SAS, corpus)

| Origen | Ronda 1 (R0) | Ronda 2 (R10) | `tJava` antes | `tJava` después |
|---|---|---|---|---|
| `proc_sql_work` | 418 (24,7 %) | 362 (27,3 %) | 406 | **0** |
| `creado_por_pasada` (fusiones, plantillas, cargas) | 520 (30,8 %) | 346 (26,1 %) | 29 | 0 |
| `data_step` | 434 (25,7 %) | 345 (26,0 %) | 0 | 0 |
| `proc_sort`, `proc_import`, `proc_export`, `proc_means`, `proc_append`, `proc_freq` | 287 | 244 | 0 | 0 |

- Los `tJava` que quedaban en R0 eran 435 (25,7 %). Ahora son **0**. El `tJavaRow` (64 en `data_step`) es el componente de estado entre filas, que la escalera mantiene a propósito: no es `tJava`.

### Top 10 de huecos (corpus, ronda 2)

| # | Ocurrencias | Motivo | Firma (sentencia) |
|---|---|---|---|
| 1 | 220 | `FUNCION_NO_MAPEADA` | `input(left(VAL_CRED_MES_old), 20.)` |
| 2 | 160 | `FUNCION_NO_MAPEADA` | `COMPRESS(input(left(VAR12), 30.))` |
| 3 | 150 | `FUNCION_NO_MAPEADA` | `COMPRESS(input(left(VAR12), 30.))` |
| 4 | 80 | `FUNCION_NO_MAPEADA` | `input(left(VAR7), 30.)` |
| 5 | 75 | `FUNCION_NO_MAPEADA` | `input(left(VAR7), 30.)` |
| 6 | 70 | `INCLUDE_EXTERNO` | `%include "/data/Programas_SAS/sascode/grid_util.sas"` |
| 7 | 30 | `TIPO_DESCONOCIDO` | columnas derivadas sin tipo que el código no fija |
| 8 | 26 | `PROC_NO_SOPORTADO` | `PROC DOWNLOAD INFILE=...` (transferencia de entrada) |
| 9 | 24 | `FUNCION_NO_MAPEADA` | `SUBSTRN(CATS(NOMBRE_SIN_ESP), 1, CNLFN1)` |
| 10 | 23 | `INCLUDE_EXTERNO` | `%include "&prog_path./000_bsf_macros.sas"` |

- Los puestos 1 a 5 (685 ocurrencias) son `input(...)` y funciones de carácter sin traducción al lenguaje de Talend. Sus tipos ya los fija R7; falta la traducción en el traductor. Es el siguiente paso con más efecto.
- Los `TIPO_DESCONOCIDO` no traen texto en la guía: la firma identifica al operador.

### Lo que no se cumplió, dicho sin rodeos

1. **"Pocas etapas" en la guía**: 196 subjobs. El criterio numérico se cumple (≤198), pero una guía con 196 filas no es una lectura de pocas etapas. Lo que lo reduciría: fusionar lecturas de base de una sola fila (`tImpalaInput` solo) con la etapa que las consume, y bajar las 53 llamadas `tRunJob`.
2. **Cadenas de SQL fusionado de 2 pasos** (criterio R5 "cadenas largas"): no se cumple. Lo impiden las lecturas WORK producidas por DATA steps en flujo, las funciones de SAS sin SQL, y los `join` que quedan en flujo.
3. **Traducción de `input()` y de funciones de carácter** en el traductor: los puestos 1 a 5 del top.
4. **34 PROC SQL que `sqlglot` no parsea** (`PARSE_ERROR`): no se revisaron uno a uno.

## Bloqueos abiertos (lo que hace falta del usuario)

1. **Esquemas reales del entorno** (`env/schemas.json` solo tiene ejemplos). Los tipos que el código fija (R7) ya cubren 20 de 21 columnas convertidas; los esquemas darían el resto.
2. **Motores por biblioteca** (`env/engines.json`, `libraries` vacío). Sin eso, las bibliotecas LZ no se ubican en base.
3. **`%include` externos** no declarados: `grid_util.sas` (70 ocurrencias) y `000_bsf_macros.sas` (23). Si se declaran en `env/externals.json`, dejan de ser hueco.
4. **Decisión sobre `input()`**: traducirla a conversiones Java (numérica o de texto) en el traductor, o dejarla como revisión manual.
5. **Prefijo de tablas de trabajo** (`sgm_`): el plan lo pide configurable; no hay campo en `env/project.json`.

## Decisiones de diseño de la ronda 2 (resumen; el detalle está en cada hito)

- `sqlglot` 30.27.0 como única dependencia nueva (R4). Dialecto `hive` porque `sqlglot` no tiene `impala`.
- La regla de último recurso (`05`) solo la aplica `_tjava` (R4). Era un defecto de la ronda 1.
- Un `read` o `write` de flujo sin componente no ocupa subjob (R8).
- Plantillas en una llamada en bucle solo si la contracción sigue siendo acíclica (R8).
- `reports = discard` por defecto; `csv` y `log` solo cambian el destino (R6).
- Ningún `join` ni `union` entra en la base sin esquemas (R5).

## Commits (ronda 2, local; no se hizo `push`)

- `1be6181` docs: plan de la ronda 2 guardado tal cual
- `0f927eb` R0: diagnóstico de agrupación
- `8599d8d` R1: env/ validado; `%include` declarado no es hueco
- `4afd5e7` R2: selectores de ambiente; `b0e1f58` corrige cifras del registro
- `8ff0a25` R3: región de carga externa absorbe preparación, troceo y limpieza
- `9f41fa4` R4: PROC SQL a operadores de flujo (sqlglot), `set_variable`, SQL Hive
- `c655861` R5: `push_to_db` (carga única, cadenas de base, frontera)
- `944f883` R6: reportes según `reports`
- `7129a45` R7: tipos que fija el código
- `e0c17d0` R8: subjob por componente conexo; R9: decisiones agrupadas
- `88c84cf` chore: quita el archivo vacío `1`
- `69560a6` R10: sección de etapas en la guía

## Entrega final (resumen)

1. Hitos: R0 a R10 terminados. Ninguno bloqueado. Dos metas quedan parciales (pocas etapas en la guía; cadenas largas de SQL en base), con su motivo arriba.
2. Pruebas: 270 pasan, 1 se salta. `ruff check .` limpio.
3. Metas: ver la tabla de R10.
4. Desglose R0 antes y después: ver arriba.
5. Top 10 de huecos: ver arriba.
6. Decisiones de diseño: ver arriba y en cada hito.
7. Lo que se necesita del usuario: bloqueos 1 a 5.
8. Commits locales: lista arriba.

No se hizo `git push`. No se activó MCP. El repositorio tiene un remoto `origin` configurado (github.com/AndresGaibor/sgm) que no añadí yo: conviene revisarlo antes de cualquier envío.

## Seguimiento: traducción de `input()` y funciones de carácter

- Causa: el traductor en línea no traduce `input(x, w.)` ni `left`/`substrn`. Lo hace el motor de rutinas de Talend (`expressions/talend_translator.py`), que está **apagado por defecto** (`SGM_TALEND_EXPRESSIONS=1`). Su propia documentación lo reserva hasta comprobar en Studio que el Java que emite compila (`talend_job_verify`).
- Medición con el motor encendido (corpus, `out/talend_on/`): los cinco primeros huecos (685 ocurrencias de `input(...)` y `COMPRESS(input(...))`) desaparecen del top. Componentes (1 328), subjobs (750), `tJava` (0,0 %) y decisiones no cambian. Pasan a dominar `INCLUDE_EXTERNO` (70), `TIPO_DESCONOCIDO` (30) y `PROC DOWNLOAD` (26).
- Decisión: no se enciende por defecto. Hacerlo pondría en las guías como traducido código que aún no se ha compilado en Studio. Próximo paso: validar el Java de esas expresiones en Studio; si compila, se puede cambiar el valor por defecto.

## Fase 1, F1.0. Línea base y trinquete (A0.2, A1.5)

- Fecha: 2026-10-30
- Qué se hizo: `metrics/baseline.json` con las cifras del corpus (189 programas). `sgm metrics --check` compara con la línea base y falla si una métrica empeora (módulo `sgm/trinquete.py`). Nuevas métricas: `tjava_sql`, `excepciones`, `huecos_por_motivo`, `lineas_sin_cubrir`, `tiempo_compilacion_s` (margen de 20 %). `--write-baseline` exige `--razon`. La comparación exige el mismo número de programas.
- Pruebas: `tests/unit/test_trinquete.py` (9 casos). Suite: 279 pasan, 1 se salta. Ruff limpio. `--check` sobre el corpus: pasa.
- Deuda visible: `lineas_sin_cubrir` = 11 349. La meta de `06-calidad.md` es 0. El trinquete solo impide que empeore. Pendiente: revisar qué líneas quedan sin evidencia (sospecha: cuerpos de macros definidas y no llamadas).

## Fase 1, F1.1. Motivos completos y guardias (dueño: Joseph en la guardia de estados; Byron en el catálogo)

- Fecha: 2026-10-30
- Qué se hizo:
  - `src/sgm/motivos.py`: registro de motivos con dueño y marca de contrato. Los diez de la lista del contrato más `COMPONENTE_NO_CATALOGADO` e `INTRINSECO_PARCIAL`. Quedan fuera del contrato, pendientes de que los tres acuerden: `COMANDO_SISTEMA`, `MACRO_NO_EXPANDIDA`, `SQL_NO_SOPORTADO`. Los que no son huecos (`CONFIGURACION`, `CONEXION_SQL`, `INCLUDE_DECLARADO`, `REPORTE`) van aparte.
  - `src/sgm/catalog/talend.py`: fuente única del catálogo de componentes.
  - `compile.py`: un componente fuera del catálogo genera hueco `COMPONENTE_NO_CATALOGADO`. Una carga de región parcial genera `INTRINSECO_PARCIAL`. Ninguno cambia el estado del operador.
- Pruebas: `tests/unit/test_motivos.py` (6 casos). Todo motivo emitido está registrado; ningún operador sin estado; los tres motivos de la fase; los fuera de contrato se marcan; las dos reglas de hueco nuevas. Suite: 285 pasan. Las referencias doradas no cambian.
- Pendiente: los motivos fuera de contrato requieren acuerdo de Andres, Joseph y Byron. Las cifras del trinquete cambian por las dos reglas nuevas; la línea base se recalcula con `--razon` cuando el cambio se acepte.

## Fase 1, F1.2. Validador de reglas y configuración (`sgm rules validate`)

- Fecha: 2026-10-30
- Qué se hizo:
  - `schemas/rules/*.schema.json`: un esquema por tipo (mapping, proc, statement, function, informats, plumbing, intrinsic, routing, case, engines, project, externals). Dependencia `jsonschema`.
  - `src/sgm/rules_validate.py`: valida cada archivo con su esquema. Además comprueba que el nombre del archivo sea el `id`, que cada `tests:` apunte a una carpeta de `tests/cases/` con `expected.yaml`, y que cada `emit.component` exista en el catálogo (salvo `engine:...` y `none`). Cada problema sale con archivo, ruta del campo y línea.
  - `sgm rules validate`: sale con 1 si hay errores.
- Pruebas: `tests/unit/test_rules_validate.py` (7). Un árbol temporal con errores a propósito (componente inventado, caso inexistente, nombre distinto del id, campo obligatorio faltante) y el repositorio real, que valida sin problemas.
- Retirado: `test_components.py::test_ejemplos_de_cada_regla_dan_su_componente`. Leía los ejemplos inline `raw["tests"]`, que ya no existen. Su cobertura la sustituyen `tests/cases/` (F1.3, con compilación completa) y el validador.

## Fase 1, F1.3. Casos declarativos por regla

- Fecha: 2026-10-30
- Qué se hizo: cada regla de `rules/mapping/` tiene su carpeta en `tests/cases/<id>/` con `input.sas` (o `ir:` para la regla de último recurso) y `expected.yaml` (entorno, componentes esperados, operadores, huecos y `max_tjava`). Las `tests:` de las 24 reglas apuntan a esas carpetas. El generador de los casos está en `out/casos/generate.py`.
- Pruebas: `tests/unit/test_casos.py` (una prueba por caso, 24). Validador: sin problemas en el repositorio.
- Cobertura: un caso por regla. El caso no prueba cada ejemplo que tenía el YAML antes; si se detecta una regla sin cubrir, se añade un caso con `sgm case new` (F1.6).

## Fase 1, F1.5 a F1.9 (un solo commit)

Fecha: 2026-10-30. Se agruparon en un commit porque comparten `cli.py` y no hay edición interactiva para separar hunks. Golden sin cambios (ninguna salida de compilación cambió); suite: 329 pasan, 1 se salta; ruff limpio.

- **F1.5 ruteo.** `rules/routing.yaml` es ahora la fuente de dueños, `fix_with`, tipo de regla sugerido y contrato pendiente. `src/sgm/motivos.py` lo lee en vez de su tabla. `sgm gaps list --owner --file --top` muestra dueño, ejemplo, arreglo y comando sugerido. Caso: `tests/cases/routing`. Pruebas: `tests/unit/test_routing.py` (4).
- **F1.6 generadores.** `sgm case new --from-gap <firma> --fuente <programa>` anonimiza el fragmento del hueco (tablas y columnas a `t<n>`/`c<n>`, literales a `texto`, comentarios fuera) y anota su estado actual en `expected.yaml`. `sgm rules new <tipo> --from-gap <firma>` crea el YAML prellenado con `status: parcial` o `component: none`. Los tipos `statement`, `intrinsic`, `mapping` y `proc` se validan; `informats` no tiene archivo nuevo a propósito. Pruebas: `tests/unit/test_generadores.py` (11). Se corrigió un bug propio: `crear_caso` escribía en el repo real por un valor por defecto fijado al importar; ahora se resuelve en cada llamada.
- **F1.7 intake.** `sgm intake <ruta>` importa con `import_source`, pasa a UTF-8 (utf-8-sig, utf-8, cp1252, latin-1), redacta credenciales, compila, escribe guía y plan en `corpus/inbox/<fecha>-<hash>/salida/` y registra huecos. El original no se guarda; `corpus/` queda en `.gitignore` salvo su README. Decisión: el inventario de huecos se reemplaza en cada `intake`, igual que en `compile`. Pruebas: `tests/unit/test_intake.py` (6).
- **F1.8 explain.** `sgm explain <archivo>:<línea>` muestra operadores que cubren la línea, pasadas que los crearon o absorbieron otros, huecos y notas de no migrado. Límite conocido: lo que quita la fontanería (pasada 2) no queda en el plan final, así que no se puede ligar a una línea; la salida lo dice. Pruebas: `tests/unit/test_explain.py` (5).
- **F1.9 esquemas.** `sgm env import-describe <archivo> --schema <nombre>` lee DESCRIBE de Impala (formato de barras o de tabulador, varias tablas) y escribe `env/schemas/<nombre>.json`. Tipos según el plan; los no traducibles quedan `null` con el tipo original en `impala`. `env/schemas.json` se convirtió en `env/schemas/ejemplo_lz.json` (datos ficticios, sin cambios de contenido); el cargador, la compilación y la caché leen la carpeta. Pruebas: `tests/unit/test_describe.py` (8) y `test_schemas.py` actualizado.
- Incidente: el test de CLI de `import-describe` sobrescribió `env/schemas/ejemplo_lz.json` por un valor por defecto fijado al importar. Restaurado desde `HEAD:env/schemas.json`, corregido el valor por defecto y comprobado que el contenido vuelve a coincidir.

Pendiente de F1: F1.4 (reglas fuera del código: fontanería, sentencias, informats, funciones, procs, intrínsecos) y F1.10 (ciclo completo con un hueco de cada motivo).

## Fase 1, F1.4 (parcial): fontanería desde YAML

- Fecha: 2026-10-30
- Qué se hizo: `rules/sas/plumbing.yaml` tiene los 15 patrones de fontanería (regex idénticas a las del código, generadas desde él). `src/sgm/passes/plumbing_patterns.py` solo carga el archivo. Pruebas: `tests/unit/test_plumbing_yaml.py` (9); caso `tests/cases/plumbing`.
- Golden: sin cambios (la suite de golden pasa). Trinquete: `metrics tests/fixtures/sas --check` sin empeorar.
- Pendiente de F1.4: funciones SAS (`rules/sas/functions/`, sale de `expressions.py`), informats (`rules/sas/informats.yaml`, sale de `types_code.py`), sentencias globales (`rules/sas/statements/`), PROC genéricos (`rules/sas/procs/` con un intérprete de `bind`/`ops`; sort, append, means, summary, freq viven hoy en `lower_procs.py`) e intrínsecos (`rules/sas/intrinsics/`). Cada uno cambia el lugar donde se decide un motivo, así que va en su propio commit con golden.

## Fase 1, F1.10 (parcial): ciclo de huecos de punta a punta

- Fecha: 2026-10-30
- Hueco cerrado: `INCLUDE_EXTERNO` (`tests/cases/include-externo`). Antes: `INCLUDE_EXTERNO` y `MACRO_NO_EXPANDIDA` para un `%include` de un archivo fuera del repo. Se cerró solo tocando `env/externals/helpers_ejemplo.sas` (contenido sintético: una macro). Después: sin huecos. Usa solo `env/` y `tests/cases/`, como pide el plan.
- Corrección encontrada en el camino: `cache.rules_hash` solo miraba `rules/` y `env/schemas/`; un cambio en `env/externals/` no invalidaba la caché. Ahora cubre todo `env/`.
- Huecos de otros motivos no cerrados en este ciclo, con motivo: `PROC_NO_SOPORTADO` (necesita el intérprete de PROC de F1.4), `FUNCION_NO_MAPEADA` (necesita `rules/sas/functions/` de F1.4), `TIPO_DESCONOCIDO` (necesita informats de F1.4 o `env/schemas/` con tipos), `PARSE_ERROR`, `MACRO_DINAMICA`, `INTRINSECO_PARCIAL`, `SEMANTICA_DUDOSA` (código o decisión del usuario, no reglas), `COMPONENTE_NO_CATALOGADO` (no se da con el catálogo actual), `COMANDO_SISTEMA`, `MACRO_NO_EXPANDIDA`, `SQL_NO_SOPORTADO` (fuera de contrato).
- Verificación: `rules validate` sin problemas; suite 339 pasan, 1 se salta; ruff limpio; `metrics --check` sin empeorar.

## Fase 1, F1.4 (continuación): informats, funciones e intrínsecos

- Fecha: 2026-10-30
- Informats: `rules/sas/informats.yaml` tiene los nombres de fecha, la marca de carácter y los umbrales numéricos. `src/sgm/ir/types_code.py` los lee. Salida idéntica en 34 especificaciones de muestra (comparación antes/después). Caso `tests/cases/informats-basicos` (con `input()` y `put()` como `FUNCION_NO_MAPEADA`, porque el traductor de Talend está apagado). Pruebas: `tests/unit/test_informats_yaml.py` (3).
- Funciones: `rules/sas/functions/fn-{upcase,lowcase,strip,trim}.yaml` con la plantilla Java y el aviso de nulos. `expressions.py` las lee. Salida idéntica en cinco muestras. Un caso por función (`tests/cases/fn-*`). Las demás funciones (`substr`, `input`, `put`, fechas...) siguen en código: pasan a YAML cuando se pueda cambiar su implementación con golden.
- Intrínsecos: `rules/sas/intrinsics/external-load.yaml` declara la carga externa con su `implementation`. Caso `tests/cases/external-load-parcial` (queda parcial y su componente es `tJava`). Prueba: `tests/unit/test_intrinsecos_yaml.py` (el `implementation` existe).
- Pendiente de F1.4: sentencias globales (todas caen en un único motivo de respaldo, no hay nada que mover sin cambiar salida), y PROC genéricos (`sort`, `append`, `means`, `summary`, `freq`), que necesitan un intérprete de `bind`/`ops` con equivalencia probada.
- Verificación: suite 349 pasan, 1 se salta; ruff limpio; `rules validate` limpio; `metrics --check` sin empeorar.

## Fase 1, F1.4 (PROC): append, means, summary y freq desde YAML

- Fecha: 2026-10-30
- Qué se hizo: `rules/sas/procs/proc-{append,means,summary,freq}.yaml` declaran los operadores que emiten. `src/sgm/ir/proc_rules.py` es el intérprete: resuelve `{data}`, `{out}`, `{proc}`, `{clause:...}` y `{qualified:...}`, comprueba `when_options` y usa el `fallback` cuando faltan opciones. `lower_procs.py` lo consulta antes de su cadena de `elif`.
- Equivalencia: huella del plan (hash del JSON completo) de los 189 programas de `tests/fixtures/sas` idéntica antes y después. Ese corpus tiene 95 apariciones de estos PROC en 22 archivos, así que la comparación sí los ejercita.
- Casos: `tests/cases/proc-{means,summary,freq,append,append-sin-base}`. Pruebas: `tests/unit/test_proc_rules.py` (3).
- Pendiente: `sort` sigue en código (su estado depende de si hay BY y añade `dedup` con NODUP). Otros PROC (`print`, `import`, `export`) también siguen en código.
- Verificación: suite 357 pasan, 1 se salta; ruff limpio; `rules validate` limpio; `metrics --check` sin empeorar.

## Fase 1, cierre de huecos de fontanería (PROC DELETE, PRINTTO, SYSECHO)

- Fecha: 2026-10-30
- Qué se hizo: se añadieron a `rules/sas/plumbing.yaml` tres patrones (`borrado_datasets`, `redireccion_log`, `mensajes_sistema`). Cierran 25 huecos `PROC_NO_SOPORTADO` del corpus (205 → 180) como `not_migrated`. Componentes sin cambio (1328). Línea base del trinquete reescrita con razón.
- Por qué: el plan de fontanería ya declara "borrado de temporales" y los mensajes de log. Talend no materializa WORK, y para tablas de la base la acción del componente de salida reemplaza la tabla. Si alguien piensa que `proc delete` sobre una tabla de la base debe seguir como hueco, se quita la entrada y se vuelve a la línea base.
- Falso positivo encontrado y descartado: un patrón `^\s*filename` cerraba también el `FILENAME` que define la fuente de un `INFILE` dentro de un DATA step. Eso era un componente real (194 → 195 en `Solutions_to_Odd_Numbered_problems.sas`). Se quitó el patrón: `FILENAME` sigue como hueco.
- Hallazgo sin resolver: `%JOB_CONTROL_RD(...)`, `%JOB_CONTROL_UPDT(...)` y `%TMSIS_CONNECT` aparecen como `PROC_NO_SOPORTADO` en `001_batch_bsf.sas`. Son llamadas de macro, no PROC: el paso de frontend las clasifica mal. Pendiente de revisar en el parser de pasos; cambiarlo cambia la clasificación de motivos.
- Pruebas: `tests/unit/test_plumbing_yaml.py` ahora cubre los tres patrones nuevos y el falso positivo del `FILENAME`.
- Verificación: suite 360 pasan, 1 se salta; ruff limpio; `rules validate` limpio; `metrics --check` sin empeorar; línea base actualizada con razón.

## Fase 1, reclasificación: llamadas de macro dentro de PROC SQL

- Fecha: 2026-10-30
- Qué se hizo: en `src/sgm/ir/lower_sql.py`, una sentencia de PROC SQL que empieza por `%` es `MACRO_NO_EXPANDIDA`, no `PROC_NO_SOPORTADO`. Caso `tests/cases/proc-sql-macro`.
- Efecto medido sobre el corpus (cuenta directa, sin caché): `PROC_NO_SOPORTADO` 180 → 124 y `MACRO_NO_EXPANDIDA` 75 → 131. El total de huecos no cambia (56 pasan de una clase a otra), ni los componentes (1328). Mismo dueño (joseph) en ambos motivos.
- Línea base del trinquete reescrita con razón, según el plan (sección de ciclo de huecos: si una métrica por motivo cambia, se justifica por escrito y se actualiza). Revisar si el criterio es el que quieren.
- Verificación: suite 360 pasan, 1 se salta; ruff limpio; `metrics --check` sin empeorar.
- Nota: el trinquete mide por motivo, no solo por total. Un movimiento entre motivos del mismo dueño dispara la alarma aunque el total baje o se mantenga; por eso se documenta aquí.

## Entrega final de la fase 1 (estado al cierre de esta sesión)

- Fecha: 2026-10-30
- Hitos: F1.0, F1.1, F1.2, F1.3, F1.5, F1.6, F1.7, F1.8, F1.9 terminados. F1.4 parcial (fontanería, informats, funciones de una línea, intrínseco `external-load`, PROC append/means/summary/freq); quedan `sort`, `print`/`import`/`export`, sentencias globales y el resto de funciones con lógica. F1.10 parcial (ver abajo).
- Pruebas: 361 pasan, 1 se salta. Ruff limpio. `rules validate` limpio. `metrics --check` sin empeorar frente a la línea base de la sesión.
- Golden: sin cambios salvo las reclasificaciones registradas con razón (fontanería PROC DELETE/PRINTTO/SYSECHO; llamadas de macro dentro de PROC SQL).
- Huecos cerrados en F1.10 y archivo creado para cada uno:
  - `INCLUDE_EXTERNO` (caso sintético): `env/externals/helpers_ejemplo.sas`, caso `tests/cases/include-externo`.
  - `PROC_NO_SOPORTADO` de `PROC DELETE`, `PRINTTO` y `SYSECHO`: entradas en `rules/sas/plumbing.yaml` (25 huecos del corpus).
  - `PROC_NO_SOPORTADO` de `PROC APPEND`, `MEANS`, `SUMMARY`, `FREQ`: `rules/sas/procs/*.yaml`, con casos en `tests/cases/proc-*`.
- Top huecos por dueño (corpus, `sgm gaps list`):
  - Byron: `TIPO_DESCONOCIDO` (30 ocurrencias, 18 archivos), `INCLUDE_EXTERNO` (70, 17), `INCLUDE_EXTERNO` (10, 5).
  - Joseph: `MACRO_NO_EXPANDIDA` (13, 8), `SENTENCIA_NO_SOPORTADA` (10, 7), `MACRO_NO_EXPANDIDA` (17, 5), `SENTENCIA_NO_SOPORTADA` (10, 5), `SENTENCIA_NO_SOPORTADA` (6, 5).
  - Andres: ninguno (`SEMANTICA_DUDOSA` no se emite en el corpus).
- Bloqueos que requieren datos externos: `TIPO_DESCONOCIDO` (salida real de DESCRIBE de Impala), `INCLUDE_EXTERNO` del corpus (archivos de Grid no incluidos en el repo).
- Decisiones de diseño tomadas sin consultar: `PROC DELETE` como fontanería; reclasificación de macros dentro de `PROC SQL`; el inventario de huecos se reemplaza en cada `intake`; el trinquete se actualiza con razón cuando cambia la distribución por motivo.
- Commits locales de esta sesión (sin push): `581fa5a`, `5d63209`, `cd722ad`, `65d7930`, `53f3d79`, `8ca4388`, `9c513b5`, `4fd6938`, `af1187d`, `a2fef41`.

## Lote del cliente: Cod1.txt y Cod2.txt (intake)

- Fecha: 2026-10-30
- Qué se hizo: `sgm intake` sobre los dos archivos. Cod1: 15 huecos, sin secretos. Cod2: 139 huecos, 1 valor redactado (el `proc pwencode`).
- Corrección de seguridad: la redacción elegía el redactor de SAS por la extensión `.sas`. Cod2 es un `.txt` con código SAS, así que sus `connect ... pass="..."` quedaron en claro en la copia guardada (27 líneas). Ahora `redaction.redact` aplica ambos redactores a todo texto. Prueba: `tests/unit/test_redaction_txt.py`. La copia anterior se borró y se volvió a generar; las 26 apariciones que quedan son referencias a macro (`pass="&..."`), no credenciales literales.
- Corrección de lotes: cada `intake` reemplazaba toda la base de huecos y borraba los del lote anterior. Ahora la base es la unión de los `huecos.json` de todos los lotes. Y la carpeta del lote incluye el nombre del archivo en su huella (dos archivos con el mismo texto chocaban). Prueba: `tests/unit/test_intake.py` (dos lotes).
- Medido, no activado: con `SGM_TALEND_EXPRESSIONS=1`, Cod2 pasa de 236 a 119 huecos (`FUNCION_NO_MAPEADA` 123 → 6). Sigue apagado por defecto hasta validar en Studio el Java que emite.
- Pendiente, con decisión: 34 `PARSE_ERROR` en Cod2 (dueño Joseph). Son `OUTER UNION CORR` (SAS alinea por nombre; reescribirlo como `UNION ALL` cambia el resultado si el orden de columnas difiere) y `CASE` con formas que `sqlglot` no acepta. Hace falta decidir si `OUTER UNION CORR` pasa a `SEMANTICA_DUDOSA`.
- Pendiente: 73 `TIPO_DESCONOCIDO` (dueño Byron), que necesitan la salida de DESCRIBE de las tablas que leen esos programas.
- Verificación: suite 365 pasan, 1 se salta; ruff limpio; trinquete sin empeorar.

## Hito 12. Cierres ODS cuando los reportes se descartan

- Fecha: 2026-11-02
- Qué se hizo:
  - `rules/sas/plumbing.yaml` reconoce el cierre de destinos ODS HTML, HTML5, RTF y PDF como limpieza de presentación; la versión de la regla sube a 2.
  - `p02_plumbing` solo clasifica esos cierres como fontanería si `reports=discard`. Si se pide conservar reportes (`log` o `csv`), la sentencia sigue como hueco hasta definir su equivalencia.
  - El caso declarativo `tests/cases/plumbing` y pruebas unitarias cubren ambos comportamientos.
- Efecto en `client_poc.sas`, con `env/` local: 122 → 106 operadores, 21 → 18 firmas con hueco y 16 cierres ODS registrados como fontanería.
- No se automatiza `FILENAME _ALL_ CLEAR` ni `PROC DATASETS` sobre una biblioteca permanente: hace falta confirmar su efecto y dependencia en el flujo.
- Verificación: `uv run pytest -q`: 370 pasan, 1 se salta; `uv run ruff check .`: limpio; `sgm rules validate`: válido; `sgm metrics tests/fixtures/sas --check`: trinquete sin empeorar.
- Decisión: las salidas ODS se consideran descartables solo bajo la política explícita `reports=discard`; una política distinta no debe eliminar ese paso sin una regla probada.

## Hito 13. Traducciones Talend de expresiones como candidatas

- Fecha: 2026-11-02
- Qué se hizo: el traductor de expresiones SAS con rutinas Talend queda activo por defecto; `SGM_TALEND_EXPRESSIONS=0` lo desactiva explícitamente. Las traducciones de ese motor agregan una nota de validación en Studio 8.0.1, copian sus advertencias semánticas y dejan el operador como `parcial` con `needs_review: true`. Las funciones que no tienen traducción demostrada siguen como huecos.
- Referencias: se actualizaron cuatro planes golden y el caso `informats-basicos` para reflejar el comportamiento predeterminado. Pruebas unitarias cubren activación, opt-out, estado parcial y advertencias.
- Efecto en `client_poc.sas`, con `env/` local: 106 operadores; 17 firmas con hueco (18 al cierre del hito 12); el total del corpus conserva 160 huecos `FUNCION_NO_MAPEADA` en 189 programas.
- Verificación: `uv run pytest -q`: 372 pasan, 1 se salta; `uv run ruff check .`: limpio; `rules validate` limpio; `metrics --check`: trinquete sin empeorar. Una primera medición concurrente excedió el umbral solo en tiempo de compilación; la repetición aislada quedó dentro del umbral.
- Limitación: no se puede comprobar compilación ni semántica real de rutinas en Studio desde el SGM; la instalación disponible carece del JAR de rutinas utilizable. Se debe validar cada candidato allí antes de convertirlo en migración confirmada.
- Decisión: se aceptan traducciones experimentales en la guía/plan para permitir trabajo incremental, siempre identificadas como parciales y sujetas a revisión. La versión de Studio se registra en la nota para indicar el entorno pendiente.

## Hito 14. Guardar Java Talend candidato en el plan

- Fecha: 2026-11-02
- Qué se hizo: `p10_components` guarda en `params.talend_expression_candidates` el SAS de origen, Java candidato, columnas, advertencias y el aviso de que `input_row` es un alias provisional. Solo se conserva para el motor Talend; la traducción inline existente no se duplica. El operador continúa parcial y con revisión obligatoria.
- Artefactos: plan JSON y referencias golden para `client_poc.sas` y `p1_merge_first_last.sas`; una candidata visible en `client_poc.sas` (`compress(v, ' ')`). Diseño: `docs/superpowers/specs/2026-11-02-expresiones-candidatas-design.md`.
- Verificación: `uv run pytest -q`: 372 pasan, 1 se salta; `uv run ruff check .`: limpio; `rules validate` limpio; `metrics --check`: trinquete sin empeorar.
- Decisión: el campo de fila mantiene el alias genérico del traductor; no se infiere un enlace (`row1`, `row2`, etc.) que el plan aún no conoce.

## Hito 15. Mostrar traducciones candidatas en la guía

- Fecha: 2026-11-02
- Qué se hizo: `guide_md` agrega una sección con el SAS de origen, Java candidato, columnas, advertencias, contexto provisional de fila y evidencia. Los bloques de código usan delimitadores que se adaptan al contenido para que expresiones con backticks no rompan el Markdown.
- Efecto en `client_poc.sas`: la guía muestra la candidata `compress(v, ' ')` y su Java con `StringHandling.CHANGE`; indica que `input_row` todavía debe enlazarse en Talend Studio.
- Pruebas nuevas: guía con candidata y guía con advertencia semántica de `scan()`.
- Verificación: `uv run pytest -q`: 374 pasan, 1 se salta; `uv run ruff check .`: limpio; `rules validate` limpio; `metrics --check`: trinquete sin empeorar.
- Decisión: mostrar las expresiones completas en la guía, sin truncar el Java ni convertirlo en una afirmación de equivalencia validada.

## Hito 16. Medir candidatas Talend por validar

- Fecha: 2026-11-02
- Qué se hizo: `metrics.json` ahora cuenta `expresiones_talend_candidatas` y `operadores_con_expresiones_talend`, por programa y en el total. El diagnóstico Markdown incluye una línea que resume ambas cifras como trabajo pendiente de validación en Studio.
- Efecto medido en los 189 programas del corpus: 234 expresiones candidatas en 148 operadores. El conteo no modifica el estado de aprobación ni la línea base del trinquete.
- Prueba: un programa con `scan()` comprueba conteos por programa y total, además del texto del diagnóstico.
- Verificación: `uv run pytest -q`: 375 pasan, 1 se salta; `uv run ruff check .`: limpio; `rules validate` limpio; `metrics --check`: trinquete sin empeorar.
- Decisión: tratar la cantidad de candidatas como indicador de revisión pendiente, no como mejora o regresión automática.

## Hito 17. Priorizar programas para validación Talend

- Fecha: 2026-11-02
- Qué se hizo: el diagnóstico lista los programas que tienen expresiones Talend candidatas, ordenados por expresiones y operadores; los empates quedan ordenados por ruta. Solo aparece la sección si hay candidatas por revisar.
- Prioridad observada: `client/client_large.sas` concentra 117 expresiones en 59 operadores; los siguientes programas del corpus tienen 31 y 30 expresiones.
- Prueba: dos programas sintéticos verifican el orden por cantidad, el total y los conteos por operador.
- Verificación: `uv run pytest -q`: 375 pasan, 1 se salta; `uv run ruff check .`: limpio; `rules validate` limpio; `metrics --check`: trinquete sin empeorar.
- Decisión: mostrar todos los programas con candidatas, sin límite de filas, para no esconder trabajo pendiente.

## Hito 18. Agrupar candidatas por función SAS

- Fecha: 2026-11-02
- Qué se hizo: el parser de expresiones conserva los nombres de función SAS encontrados en cada candidata, incluidas las llamadas anidadas y sin repetir nombres dentro de la misma expresión. `metrics.json` agrega el conteo por programa y total; el diagnóstico Markdown lista las funciones por frecuencia.
- Prioridad medida en el corpus: `input` (81 expresiones), `left` (65), `compress` (24), `put` (22) y `catx` (19). Una expresión anidada puede contribuir a más de una función.
- Pruebas: una expresión con `strip(scan(...))` verifica detección, orden y deduplicación; las métricas verifican el conteo y su orden.
- Verificación: `uv run pytest -q`: 376 pasan, 1 se salta; `uv run ruff check .`: limpio; `rules validate` limpio; `metrics --check`: trinquete sin empeorar.
- Decisión: el inventario se calcula desde el árbol analizado por el traductor, no buscando palabras en el Java generado ni en cadenas literales SAS.

## Hito 19. Agrupar advertencias semánticas de candidatas

- Fecha: 2026-11-02
- Qué se hizo: las métricas cuentan las advertencias guardadas por expresión candidata, por programa y en el total; el diagnóstico las muestra ordenadas por frecuencia. Una expresión puede aportar varias advertencias y el agrupamiento conserva el texto exacto.
- Prioridad observada en el corpus: 81 advertencias para `input` numérico (confirmar el informat), 5 para `scan` (delimitadores consecutivos) y 4 para una macrovariable que requiere contexto.
- Prueba: métricas y diagnóstico validan la frecuencia de advertencias de `scan()` e `input()` en fixtures separados.
- Verificación: `uv run pytest -q`: 376 pasan, 1 se salta; `uv run ruff check .`: limpio; `rules validate` limpio; `metrics --check`: trinquete sin empeorar.
- Decisión: agrupar por texto exacto de advertencia; no generalizar mensajes que pueden señalar distintos nombres o causas.

## Hito 20. Automatización para producción: fases 0 y 1

- Fecha: 2026-11-03
- Qué se hizo (fase 0, decisiones):
  - 0.1: los cambios sin confirmar del árbol (`metrics/baseline.json`, `frontend/sql_normalize.py`, `ir/lower_sql.py`, `tests/unit/test_sql_normalize.py`, `docs/diseno-talend-exogena-depositos.md`) no se tocan ni entran en este commit.
  - 0.2: versión objetivo de Talend Studio 8.0 R2026-09 (la de la documentación del migrador). Pendiente de confirmación del usuario.
  - 0.3: los contratos de `05-contratos.md` solo reciben campos opcionales nuevos (permitido sin acuerdo). Reemplazar el modelo de pendiente queda pendiente de acuerdo.
  - 0.4: MCP, API y web salen de la hoja de ruta, como manda `AGENTS.md`.
- Qué se hizo (fase 1, capa de hechos C2): `src/sgm/facts/` con el modelo `Fact` y un catálogo cerrado de tipos, extractores estructurales (DATA step, PROC SQL, PROC genérico) y textuales (macros, `%let`, `%include`, bibliotecas, rutas, servidores, credenciales), y el comando `sgm facts <ruta>`.
- Decisión: las definiciones y llamadas de macro se leen de los pasos del texto completo (`parse_steps`), no del índice. El índice descarta copias idénticas: en el archivo de referencia conserva 13 de las 274 definiciones de `%macro` y descarta 261 (medido).
- Decisión: el catálogo se amplió con `biblioteca`, `comando_sistema` y `sentencia_global`, que el SAS real necesita. Son extensiones del catálogo propuesto, no cambios de contrato.
- Decisión: un nombre con `&` o `%` se marca `dinamico=si`; no se trata como tabla concreta.
- Corrección de conteos: las cifras anteriores de este diseño (348 tablas WORK creadas, 263 leídas, 2 borradas) salían de búsquedas con grep que solo veían `CREATE TABLE` y `FROM`. Con los hechos, en `client_large.sas`: 405 conjuntos WORK distintos escritos (sin dinámicos), 347 leídos y 1 borrado. Los hechos reemplazan a los conteos de grep.
- Hallazgos del extractor, corregidos: (a) el `create table` dentro de un pase directo o de `EXECUTE BY` se perdía; (b) las definiciones de macro repetidas se perdían en el índice; (c) las llamadas que se expanden a nada no dejaban hecho.
- Prueba: 11 pruebas en `tests/unit/test_facts.py`: trazabilidad, catálogo cerrado, credenciales enmascaradas, determinismo, alcances, nombres dinámicos, cobertura de cada línea con contenido por un paso y entradas hostiles sin excepciones.
- Medición: en `client_large.sas`, los 390 `CREATE TABLE` tienen hecho en su línea; las 274 definiciones de macro son 10 nombres distintos; 0 líneas con contenido sin cubrir.
- Verificación: `uv run pytest -q`: 408 pasan, 1 se salta; `uv run ruff check .`: limpio.
- Pendiente: la fase 2 (motor de reglas por hechos) y el resto de las fases siguen en el plan `docs/automatizacion/03-plan-produccion.md`.

## Hito 21. Motor de reglas: fase 2 de producción (parcial)

- Fecha: 2026-11-03
- Qué se hizo (según `docs/automatizacion/03-plan-produccion.md`, fase 2):
  - 2.1: esquema `schemas/rules/mapping.schema.json` con `prioridad`, `cuando`, `produce` y `casos`.
  - 2.2: `cuando` es un lenguaje cerrado (`kind`, `placement`, `file_format`); el esquema rechaza cualquier otra clave.
  - 2.3: `p10_components.resolve`: entre las reglas que coinciden gana la de mayor prioridad; si dos de igual prioridad proponen componentes distintos, se registra un `Conflicto` como decisión pendiente y el operador queda para revisión.
  - 2.4: las 24 reglas de `rules/mapping/` migradas al formato nuevo (`match`→`cuando`, `emit`→`produce`, `tests`→`casos`, `rung`→`prioridad` = 100 − 10·peldaño). `rung` queda como valor derivado para las métricas.
  - 2.5: `choose` es ahora un envoltorio sobre `resolve`; la primera coincidencia ya no decide por sí sola.
- Medición previa a la migración: no hay solapes reales entre reglas de peldaños 1 a 4 en el corpus; la única regla que cubre todo es la de último recurso.
- Pruebas: `tests/unit/test_reglas_conflictos.py` (4 de conflictos y prioridad, 1 de lenguaje cerrado).
- Verificación: la suite completa pasa sin cambiar goldens (408 pasan, 1 se salta); `uv run ruff check .` limpio; `rules validate` limpio; `metrics --check` sobre `tests/fixtures/sas`: trinquete sin empeorar.
- Pendiente de la fase 2 (no cerrado):
  - 2.2: el lenguaje de `cuando` todavía no lee hechos (`tiene(tabla_escrita, alcance=work)`, `lectores(...)`); la sección 5.1 de `01-automatizacion.md` lo pide.
  - 2.6: los patrones de Talend como datos (caché, joblet, parámetro, contexto de ambiente, `tDBRow` para SQL de consumo único) no existen todavía. Pasan a la fase 3, donde nacen los joblets.

## Hito 22. Decisiones sin valor aplicado: fase 3 de producción (parcial)

- Fecha: 2026-11-03
- Qué se hizo (según `docs/automatizacion/03-plan-produccion.md`, fase 3):
  - 3.3 (parcial): la pasada 8 ya no fija `temp_table` en la arista. Queda sin materializar y la decisión lleva `temp_table` como sugerencia, con cada opción marcada `aplicado: false`. Es el cambio que quita la materialización silenciosa.
  - 3.4: en el plan JSON, `default` pasa a `sugerido` y cada decisión lleva `aplicado: false`. La CLI muestra "sugerido ... (no aplicado)".
- Decisión: todas las decisiones pendientes se emiten con `aplicado: false` hasta que una persona las confirme, también las de alternativas de componente de la pasada 10, que hoy usan el componente propuesto como candidato.
- Cambio de comportamiento deliberado: `tests/golden/*.plan.json` (4 programas) cambian solo en las claves de decisión (`default` → `sugerido`, más `aplicado`). Se comprobó con un script que, ignorando esas tres claves, los planes son idénticos. Se regeneraron con `SGM_UPDATE_GOLDEN=1`.
- Prueba: `test_p08_agregado_que_vuelve_a_unirse_deja_decision_no_materializa` comprueba que ninguna arista queda materializada sin decisión.
- Verificación: `uv run pytest -q`: 413 pasan, 1 se salta; `uv run ruff check .`: limpio.
- Pendiente de la fase 3 (no cerrado): 3.1 campos por valor (`fuente`, `regla`, `confianza`, `hechos`), 3.2 modelo único de pendiente, 3.5 regla de materialización por lectores, 3.6 residuo de bloques repetidos, 3.7 y 3.8 joblets y sus parámetros, 3.9 contextos de ambiente como pendientes, 3.10 división de los archivos de más de 300 líneas.

## Hito 23. Campos por valor y pendiente unificado: fase 3.1 y 3.2

- Fecha: 2026-11-03
- Qué se hizo (según `docs/automatizacion/03-plan-produccion.md`):
  - 3.1: cada componente del plan lleva `valor_componente` con `valor`, `fuente` (archivo y líneas), `regla` (id@versión) y `confianza`. El campo `hechos` queda en `null`: enlazar hechos a operadores no está calculado.
  - 3.2: el plan lleva `pendientes`, un modelo único con `valor: null`, `motivo`, `dueno` y `se_cierra_con` (tomados de `rules/routing.yaml` vía `motivos.de`), y `nota`. Los modelos `Pending` y `Gap` no cambian: es una vista nueva y aditiva, porque reemplazarlos requiere acuerdo de contrato.
- Decisión: ambos cambios son aditivos. Los goldens se regeneraron y se verificó con un script que, quitando `valor_componente` y `pendientes`, son idénticos a los del commit anterior.
- Pruebas: `tests/unit/test_plan_valores.py` (fuente, regla y confianza en cada componente; dueño y cierre en cada pendiente).
- Pendiente: `hechos` por valor (enlace operador↔hecho); 3.5 regla de materialización por lectores como regla completa (hoy solo dispara la decisión del patrón de agregado).

## Hito 24. Joblets por forma repetida: fase 3.7 (parcial)

- Fecha: 2026-11-03
- Qué se hizo (según `docs/automatizacion/03-plan-produccion.md`):
  - 3.7: `Plan.joblets` (campo aditivo de la IR) y su salida `joblets` en el plan JSON. La pasada 7 registra un joblet por cada forma repetida con al menos 2 apariciones y 3 operaciones. Las mismas formas en nodos distintos son un solo joblet: se suman apariciones, instancias y fuente.
  - Cada joblet lleva `id`, `etiquetas`, `operaciones`, `apariciones`, `parametros`, `instancias`, `fuente` (una lista por aparición, con archivo y líneas) y `por_que`.
- Medición: en `client_large.sas`, 74 joblets con identificadores únicos (antes de fusionar por forma salían 98 repetidos).
- Decisión: los joblets se derivan de las plantillas que la pasada 7 ya detecta; no cambian la emisión de componentes (sigue `iterate`).
- Límites conocidos, pendientes:
  - Los umbrales (2 apariciones, 3 operaciones) están como constantes en `p07_templates.py`, no en `rules/`, como pide 3.7.
  - Los parámetros se llaman `parametro_k`: falta el tipo (tabla o literal) y un nombre con sentido, que es 3.8.
  - La guía de Jobs todavía no muestra los joblets; eso es la fase 4.1.
- Prueba: `tests/unit/test_joblets.py` (un bloque repetido en dos nodos es un solo joblet con 5 apariciones; invariantes de joblet; sin repetición no hay joblet).
- Goldens: regenerados; verificado que, quitando `joblets`, `valor_componente` y `pendientes`, son idénticos al commit anterior.
- Verificación: `uv run pytest -q`: 418 pasan, 1 se salta; `uv run ruff check .`: limpio.

## Hito 25. Mapa de flujo sin traducir: fase 4.2

- Fecha: 2026-11-03
- Qué se hizo (según `docs/automatizacion/02-mapa-de-flujo.md`): `src/sgm/facts/mapa.py` genera un Markdown por programa con las secciones del diseño: resumen, conjuntos de datos (escritos, leídos y borrados, con alcance), entradas y salidas externas, conexiones a base, ramas por valor de ambiente y pendientes. Sale solo de los hechos. Comando: `sgm mapa <ruta> --out <carpeta>`.
- Decisión: los nombres con macro variable no entran en la tabla de conjuntos (se cuentan aparte en el resumen), para no presentar como tablas nombres que aún no se conocen.
- Pruebas: `tests/unit/test_mapa_flujo.py` (secciones, conteos por conjunto y ausencia de secretos).
- Pendiente de 4.2: la sección de etapas (grafo de datos separado por fronteras externas) y los bloques repetidos con su residuo, que dependen de 3.6.
- Verificación: `uv run pytest -q`: 421 pasan, 1 se salta; `uv run ruff check .`: limpio; `sgm mapa` genera el Markdown del fixture de prueba.

## Hito 26. Guía de Jobs con joblets: fase 4.1 (parcial)

- Fecha: 2026-11-03
- Qué se hizo (según `docs/automatizacion/03-plan-produccion.md`): la guía Markdown de cada programa tiene una sección `## Joblets` con, por joblet, el porqué, las operaciones del bloque, los parámetros, cada aparición con su archivo y líneas, y una nota fija de lo que falta.
- Pendiente de 4.1: entradas y salidas de cada joblet (aún no calculadas), la estructura completa de la guía de Jobs con contextos y subjobs como la del diseño, y el tipo y nombre de los parámetros (3.8).
- Pruebas: `tests/unit/test_guia_joblets.py` (la sección aparece con joblets y no aparece sin ellos).

## Hito 27. Fase 5: producción (cerrada salvo 5.8 y las partes pendientes de fases 3 y 4)

- Fecha: 2026-11-03
- Qué se hizo (según `docs/automatizacion/03-plan-produccion.md`, fase 5):
  - 5.1: pruebas de invariantes en `tests/unit/test_invariantes_produccion.py`: determinismo byte a byte del plan, etiqueta de versión, ningún secreto en plan ni guía, límite de tiempo y entradas hostiles sin excepciones.
  - 5.2: el trinquete incluye `pendientes_sin_dueno` y `valores_sin_fuente`, con meta cero (no depende de la línea base, que tiene cambios sin confirmar).
  - 5.3: corpus hostil de compilación sin excepciones.
  - 5.4: medido: `client_large.sas` compila en 26 s, pico de 29 MB de memoria Python. Límite vigilado: 120 s. Queda en `docs/automatizacion/04-runbook.md`.
  - 5.5: `README.md` (estaba vacío): instalación, comandos, qué produce y límites.
  - 5.6: `docs/automatizacion/04-runbook.md`: incorporar un archivo nuevo, paso a paso.
  - 5.7: la salida de `intake` y `compile` lleva `metadatos` con `sgm_version` y `ruleset_hash`. Va fuera de `plan_to_dict` para que un cambio de reglas no rompa los goldens.
- Pendiente de la fase 5: 5.8 (validación extremo a extremo contra SAS y Talend con datos), que necesita un ambiente externo.
- Pendiente que quedó de fases 3 y 4 y que la fase 5 no cubre: 3.5 (regla de materialización por lectores completa), 3.6 (residuo de bloques repetidos), 3.8 (tipo y nombre de parámetros de joblet), 3.9 (contextos de ambiente como pendientes), 3.10 (dividir archivos de más de 300 líneas), 4.1 (entradas y salidas de joblets, estructura completa de la guía), 4.2 (sección de etapas del mapa), 4.3 (informe de constructos sin regla; `sgm gaps list` ya lo da en parte).
- Verificación: `uv run pytest -q`: 428 pasan, 1 se salta; `uv run ruff check .`: limpio; `metrics --check`: sin empeorar, metas cero en 0.

## Hito 28. An�lisis SQL m�s completo: fase 0.1 cerrada

- Fecha: 2026-11-03
- Qu� se hizo: el �rbol llevaba cambios sin confirmar desde antes de la fase 0. Se verific� la suite y se confirmaron en dos commits. El usuario decidi� incluirlos (paso 0.1).
  - hito 28: sql_normalize.py (m�s reglas de sqlglot: nombres con espacios, LABEL, informatos, literal ., ^=, NOT =, CONTAINS), lower_sql.py (OUTER UNION pasa a SEMANTICA_DUDOSA en vez de parsearse mal), metrics/baseline.json (PARSE_ERROR 42 -> 8, FUNCION_NO_MAPEADA 394 -> 177, componentes 1328 -> 1383), 	ests/unit/test_sql_normalize.py.
  - hito 29: divisi�n de los archivos de m�s de 300 l�neas (R9, fase 3.10): cli.py queda en 276 (comandos a cli_decisiones.py y cli_util.py), expressions.py en 131 (m�s expressions_base.py, expressions_funciones.py, expressions_parser.py), 	alend_translator.py en 43 (m�s 	alend_base.py, 	alend_parser.py, 	alend_funciones.py, 	alend_tabla.py), macros.py en 163 (m�s macros_modelo.py, macros_control.py, macros_llamadas.py), steps.py en 216 (m�s steps_tipos.py), p10_components.py en 194 (m�s 
eglas_mapeo.py). La salida no cambia: goldens id�nticos.
- Reparaci�n incluida en hito 29: el trabajo de divisi�n ven�a sin terminar y la suite no importaba (	alend_parser.py con un import vac�o y un error de sintaxis; _FUNCTIONS a medio mover a 	alend_tabla.py). Se complet� el movimiento y se dej� el �rbol en verde.
- Verificaci�n: uv run pytest -q: 428 pasan, 1 se salta; uv run ruff check .: limpio; metrics --check: sin empeorar. Ning�n archivo de src/ supera 300 l�neas.

## Hito 28b. Partir los archivos de más de 300 líneas: fase 3.10

- Fecha: 2026-11-03
- Qué se hizo (según `docs/automatizacion/03-plan-produccion.md`, 3.10): ningún archivo de `src/` supera 300 líneas. Cambios puros de estructura, sin cambiar salidas:
  - `frontend/steps.py` (305): tipos de paso en `steps_tipos.py`, reexportados.
  - `passes/p10_components.py` (327): carga, emparejamiento y resolución de reglas en `reglas_mapeo.py`.
  - `cli.py` (390): auxiliares en `cli_util.py`; comandos de decisiones y huecos en `cli_decisiones.py`.
  - `frontend/macros.py` (478): modelo e índice en `macros_modelo.py`; control (`%if`, `%do`) en la mezcla `macros_control.py`; llamadas e `%include` en `macros_llamadas.py`.
  - `expressions/expressions.py` (700): base, funciones y analizador en `expressions_base.py`, `expressions_funciones.py` y `expressions_parser.py`; la fachada conserva `translate`.
  - `expressions/talend_translator.py` (736): `talend_base.py`, `talend_parser.py`, `talend_funciones.py` y `talend_tabla.py` (la tabla `_FUNCTIONS`); la fachada conserva `translate_to_talend`, `Unsupported` y `Result`.
- Decisión: los nombres públicos se reexportan desde el módulo original, así que los importadores no cambian. Donde una función solo usa el tipo del analizador como anotación, el import va bajo `TYPE_CHECKING` para evitar un ciclo.
- Verificación: `uv run pytest -q`: 428 pasan, 1 se salta. Los goldens no cambiaron, lo que confirma que la división no altera salidas. `uv run ruff check .`: limpio.
- Cambios sin confirmar de otros (`frontend/sql_normalize.py`, `ir/lower_sql.py`, `metrics/baseline.json`) no se tocaron ni entran en este commit.

## Hito 30. Fase 3 y 4 pendientes: 3.6, 3.8, 3.9, 4.2 y 4.3

- Fecha: 2026-11-03
- Qué se hizo (según `docs/automatizacion/03-plan-produccion.md`):
  - 3.6: la pasada 7 registra cada grupo de la misma forma que no se puede unificar en `Plan.residuos_bloques` (motivo `SEMANTICA_DUDOSA`, apariciones y fuente). Ya no se descarta en silencio. Plan JSON: `residuos_bloques`.
  - 3.8: cada parámetro de joblet tiene `tipos` (`tabla` si todos sus valores son nombres de conjunto de datos; `literal` si no). Los nombres siguen siendo `parametro_k`: el nombre con sentido queda pendiente.
  - 3.9: cada variable de contexto declarada sin valor en el archivo sale como pendiente `DATO_NO_EN_ARCHIVO` con dueño y cómo cerrarse. No se inventa el valor.
  - 4.2: el mapa de flujo tiene la sección `## Etapas`: pasos unidos por conjuntos de datos internos. Lo externo no une etapas.
  - 4.3: el ranking de constructos sin regla ya lo da `sgm gaps list --top` (por archivos y ocurrencias). No se agregó un reporte nuevo.
- Parcial, sin cerrar:
  - 3.5: la única materialización automática es la del agregado que vuelve a unirse, que ya exige dos lectores. La regla de frontera entre etapas no está implementada.
  - 4.1: las entradas y salidas de cada joblet siguen pendientes; la guía lo dice.
- Goldens regenerados. Verificado con un script que, quitando `residuos_bloques`, `tipos` y los pendientes `contexto:*`, son idénticos al commit anterior.
- Pruebas: `tests/unit/test_joblets.py` (tipos y residuos), `tests/unit/test_mapa_flujo.py` (etapas).
- Verificación: `uv run ruff check .`: limpio. Suite completa: ver la línea del commit siguiente.

## Hito 31. Entradas y salidas de joblets y regla de materialización: 4.1 y 3.5

- Fecha: 2026-11-03
- Qué se hizo (según `docs/automatizacion/03-plan-produccion.md`):
  - 4.1: cada joblet declara `entradas` (conjuntos que lee de fuera del bloque) y `salidas` (conjuntos que escribe para el resto del programa), con `variable_entre_apariciones` cuando cambian entre copias. La guía las muestra en lugar de la nota pendiente.
  - 3.5: `sugerir_materializacion(lectores, entregable, frontera)` en `p08_partition.py`: entregable o frontera → materializar; dos o más lectores → materializar; un lector y no entregable → encadenar. La decisión sigue sin aplicarse (3.4). El único patrón que materializa hoy usa la regla con dos lectores, así que la salida no cambia.
- Parcial, sin cerrar:
  - 3.5: la regla está probada, pero el entregable y la frontera entre etapas aún no se leen de los hechos ni de los operadores. Por eso la pasada solo le pasa dos lectores y no entregable.
- Pruebas: `test_regla_de_materializacion_tabla_de_decision` (tabla de decisión) y los invariantes de joblet con entradas y salidas.
- Verificación: `uv run pytest -q`: 432 pasan, 1 se salta. `uv run ruff check .`: limpio.
- Pendiente del plan: 5.8 (validación extremo a extremo contra SAS y Talend con datos). Requiere un ambiente externo.

## Hito 32. Guía con contextos y pendientes: fase 4.1 completa en estructura

- Fecha: 2026-11-03
- Qué se hizo (según `docs/automatizacion/03-plan-produccion.md`, 4.1): la guía trae las secciones que pide el plan y que faltaban: `## Contextos` (variables declaradas con su origen y su estado, y grupos de ambiente con su selector) y `## Pendientes` (motivo, dueño y cómo cerrar, con el mismo modelo que el plan JSON).
- Pendiente de la fase 4: ninguno en el plan. 4.1, 4.2 y 4.3 quedan cubiertos; 4.3 con `sgm gaps list`.
- Pruebas: `test_guia_tiene_contextos_y_pendientes`.
- Verificación: `uv run pytest -q`: 433 pasan, 1 se salta. `uv run ruff check .`: limpio. Los goldens no cambian porque no incluyen la guía Markdown.
- Pendiente de la fase 5: 5.8, validación con datos contra SAS y Talend. Requiere un ambiente externo.

## Hito 33. Frontera entre programas, comparación de salidas y procedimiento de validación: 3.5 y 5.8

- Fecha: 2026-11-03
- Qué se hizo (según `docs/automatizacion/03-plan-produccion.md`):
  - 3.5: `sgm.lineage.fronteras` calcula, por programa, los conjuntos permanentes que escribe y que otro programa lee. Se expone como `Plan.fronteras`, en el plan JSON (`fronteras`) y en la guía (`## Fronteras entre programas`). Un conjunto de frontera ya está persistido, por eso la regla no pide tabla temporal.
  - 5.8 (lo que no depende del ambiente): `src/sgm/verify.py` y el comando `sgm comparar <sas.csv> <talend.csv>`, que compara filas, sumas por columna y huella del contenido sin importar el orden. Sale con código 1 si algo no coincide. Procedimiento en `docs/automatizacion/05-validacion-extremo-a-extremo.md`.
- Pruebas: `tests/unit/test_fronteras.py` (2), `tests/unit/test_comparar_salidas.py` (4).
- Goldens regenerados: verificado con un script que, quitando `fronteras`, son idénticos al commit anterior.
- Verificación: `uv run ruff check .`: limpio. Suite completa: 439 pasan, 1 se salta, en la segunda ejecución.
- Incidencia: en una ejecución completa falló una vez `test_compile_outputs::test_guia_y_json_no_contienen_secretos_sin_enmascarar`. No se reproduce: pasa en serie, con tres semillas de hash distintas y en la ejecución siguiente de la suite completa. Queda anotado como fallo intermitente sin causa identificada.
- Pendiente: 5.8 en un ambiente con SAS, Talend Studio y datos de prueba. Es el único punto del plan que no se puede cerrar desde el repositorio.

## Hito 39. Umbral de agrupación fijado y joblet de contexto del encabezado

- Fecha: 2026-11-03
- Qué se hizo (según `docs/automatizacion/06-brecha-con-diseno.md`):
  - Umbral de agrupación en `sgm.generador.UMBRAL_DE_AGRUPACION = 0.2`, decidido con revisión humana. Con 0,3 salen 5 joblets, 7 firmas más y 3 nodos más en el Job padre, sin que el archivo demuestre que esos grupos sean procesos distintos.
  - `sgm.generador.contexto_del_encabezado`: joblet de contexto con las sentencias de entorno del encabezado (`%let`, `OPTIONS REMOTE=`, `PROC DOWNLOAD`/`RSUBMIT`, `PROC PWENCODE`), el resto del encabezado se queda en el Job padre.
  - Variables de contexto declaradas sin inventar valores: `servidor_remoto`, `base_de_datos` y `credencial` con el valor observado (credencial siempre `***`); `anio`, `mes`, `dia` y `mday` como pendiente `DATO_NO_EN_ARCHIVO`. Las 14 rutas literales quedan como un pendiente que pide confirmar su papel.
  - `diseno_del_job` reporta el nodo de contexto, los nodos del padre y las firmas de componente distintas de todo el programa.
- Medición en `client_large.sas`: 14 operadores de entorno en el joblet de contexto; 7 variables declaradas y 5 pendientes; Job padre de 36 nodos (2 llamadas, 1 contexto, 27 del encabezado, 6 de sueltas); 112 firmas distintas e 137 instancias.
- Decisión: el joblet de contexto no se conecta al plan ni a la guía. Sigue siendo la fase de diseño, igual que los joblets por grupo; conectarlo es otro cambio y no lo pidió esta ronda.
- Pruebas: `tests/unit/test_generador.py`, 4 nuevas (umbral 0,2 contra 0,3 con Jaccard 0,25; variables sin contraseña en claro; conteo de operadores de contexto; aritmética de nodos del padre).
- Verificación: `uv run pytest -q`: 447 pasan, 1 se salta, 6 xfail (las de `test_objetivo_diseno.py`, que miden la brecha y no cambian con este hito). `uv run ruff check .`: limpio.
- Bloqueos sin cambio: la decisión de qué regiones forman un mismo proceso, la fusión de joins con decisión por firma y la validación con datos (5.8), que necesita un ambiente externo.


## Hito 40. Modelo de coincidencia y tipo de join en tMap

- Fecha: 2026-11-03
- Qué se hizo: cada join que se emite como tMap lleva `match_model` (`unique`, `first` o `all`) y `join_type` (`inner` o `left outer`) en su componente. `src/sgm/passes/join_match.py` calcula ambos y las advertencias; `p10_components` lo llama solo para joins con componente tMap.
- Premisa corregida: la pasada 6 no funde joins. `CHAINABLE` es `filter`, `derive`, `rename` y `select`. Los joins pasan a tMap por la regla `rules/mapping/03-join.yaml`, en la pasada 10. No se cambió la pasada 6: fundir joins alteraría la firma de decisión por join y los overrides guardados.
- Modelo por construcción: un `join` de SQL (con `keys`) es `all`, porque SQL devuelve todas las parejas que cumplen el ON. Un MERGE (sin `keys`) es `all` como suposición, con advertencia, porque SAS empareja en secuencia cuando la clave se repite en ambos lados.
- Tipo de join (tarea 21): `inner` y `left` se traducen a `inner` y `left outer`. `right`, `full` y `cross` no tienen tipo tMap; quedan con `join_type: null` y una advertencia que pide revisión. El tMap solo admite inner y left outer según la documentación de Talend.
- Firmas y overrides: los parámetros del join no cambian, así que la firma y las decisiones guardadas por firma siguen igual. Una prueba lo verifica.
- Goldens regenerados: `p1_merge_first_last.plan.json` y `generalization__etl_archivos_simple.plan.json`. La diferencia es solo en los joins: claves nuevas en `component` y, en el MERGE, la advertencia en `notes`.
- Pruebas: `tests/unit/test_join_match.py` (11 pruebas, una por comportamiento, con programas SAS mínimos inline). Junto con `test_components.py`, `test_store.py` y `test_golden.py`: 34 pasan.
- Verificación: `ruff check .` limpio; `ruff format` aplicado a los archivos nuevos y tocados.

### Tarea 22. Advertencia de unique match en la guía

- Qué se hizo: `describe()` agrega, para `unique`, la advertencia de que el tMap conserva la última fila coincidente, no la primera. La advertencia queda en las notas del operador, que la guía muestra en su tabla. `first` tiene su propia advertencia.
- Fuente: la página de ejemplo https://help.qlik.com/talend/en-US/components/8.0/tmap/example-job-implementing-different-match-models dice "It outputs the last matching record of the lookup source." para unique y "the first matching record" para first. La página general de modelos no lo precisa, por eso la advertencia cita la de ejemplo.
- Límite: ninguna construcción SAS actual demuestra `unique` ni `first`, así que el pipeline no emite ninguno todavía. Ambos quedan aceptados por `describe(op, model=...)` y probados en aislamiento. Activarlos exige una fuente que lo demuestre.
- Verificación: pruebas de `describe` con `unique` y `first`, y de no repetir advertencias.

### Tarea 23. Medición de tJavaRow en client_large.sas

- Medición con `sgm compile --no-cache` sobre `tests/fixtures/sas/client/client_large.sas` (copia en el directorio temporal de sesión): 812 operadores, 119 firmas con hueco, 0 componentes `tJavaRow` y 0 `tJava`.
- Causa: el archivo no contiene `RETAIN`, `FIRST.`/`LAST.` ni `LAG(`. Ninguna sentencia cae en la regla `04-stateful-row`.
- Joins en el mismo archivo: 53 tMap, todos con `match_model: all`. Tipos: 14 inner, 9 left outer, 29 cross y 1 full. Los 30 de tipo cross o full llevan advertencia.
- Decisión: el cero de `tJavaRow` es real en este pipeline; un SAS con `RETAIN` que no se traduce aparecería como hueco, no como tJavaRow.


## Hito 41. Investigación de temas 41 a 47

- Fecha: 2026-11-03
- Qué se hizo: se escribió `docs/automatizacion/07-investigacion.md` con una sección por tema (41 a 47): pregunta, fuentes con enlace, conclusión y qué cambia en el proyecto. Cada punto va marcado como confirmado, parcial o sin confirmar según lo que dijeron las páginas leídas.
- Hallazgos principales: tFlowToIterate y tCacheOut/tCacheIn quedan con puntos sin confirmar en documentación oficial; el modelo de caché de tMap tiene límites documentados; %DO, %SYSFUNC y el IN= de MERGE tienen sintaxis confirmada; no encontré traductor de SAS de código abierto maduro (tree-sitter-sas es el parser más sólido hallado).
- Pruebas: no aplica (solo documentación).
- Bloqueos: el PDF del paper de Horstman (MERGE) no se pudo extraer en texto; la página de scoring translator de SAS devolvió 404; la nota de %EVAL y las reglas many-to-many de MERGE quedan sin confirmar en fuente oficial.
- Decisión: tratar como pendiente de validación en Studio 8 cualquier comportamiento de subjob por fila y de caché entre jobs; no traducir MERGE a JOIN sin prueba de equivalencia.

## Hito 42. El diseño sale como artefacto de CLI

- Fecha: 2026-11-03
- Qué se hizo:
  - `sgm.diseno.diseno_de_programa` compone plan, hechos y generador en un dict de diseño; redacta el texto antes de extraer hechos.
  - `sgm diseno <archivo.sas> --out out/` (en `sgm/cli_diseno.py`, registrado desde `sgm.cli`) escribe `out/<programa>.diseno.json` con joblets por grupo, sus contextos, joblet de contexto y Job padre. Compila con la misma `env/` que `sgm compile`. `cli.py` no pasa de 300 líneas.
  - Pruebas: `tests/unit/test_diseno.py` (2), que ejercitan el comando completo y verifican que la contraseña no aparece en claro en el archivo.
- Hallazgo: las mediciones de la ronda anterior se hicieron sin `env/project.json`. La política canónica `push_to_db` cambia la fusión: el plan pasa de 955 a 780 operadores, el encabezado de 27 a 56 componentes, las firmas distintas de 112 a 131 y el Job padre de 36 a 65 nodos. Aislado por variantes de `Env`: la causa es `placement_strategy`, no los externos ni los motores.
- Decisión: el diseño queda como artefacto separado (`.diseno.json`), no dentro de `plan.jobs`. Meter los joblets y el Job padre en el plan toca el modelo de decisiones y las pruebas de firmas; es una decisión aparte y no lo pidió esta ronda.
- Verificación: `uv run pytest -q`: 449 pasan, 1 se salta, 6 xfail. `uv run ruff check .`: limpio. Corrida real: `uv run sgm diseno tests/fixtures/sas/client/client_large.sas --out out/diseno` en 45 s, con 2 joblets, 65 nodos y 131 firmas.

## Hito 43. `sgm flujo`: HTML de cómo funciona un programa SAS

- Fecha: 2026-11-03
- Qué se hizo: el comando `sgm flujo <archivo|carpeta> --out out` escribe `<programa>.flujo.html`, una vista de cómo funciona el programa (no es la traducción). Contiene resumen, diagrama SVG, tabla de pasos en orden con su código plegable, entradas externas, configuración y pendientes.
  - `src/sgm/flow/model.py`: pasos con los datasets que leen y escriben (DATA step, PROC SQL, PROC genérico), aristas entre el último paso que escribió un dataset y el que lo lee, entradas externas, capas y redacción de credenciales antes de analizar.
  - `src/sgm/flow/layout.py`: diseño en columnas por capa y SVG a mano.
  - `src/sgm/flow/page.py`: página HTML con CSS en línea y modo claro/oscuro. Sin scripts ni recursos externos.
  - `src/sgm/cli_flow.py`: comando, registrado en `sgm.cli`.
  - Programas con más de 200 pasos muestran el diagrama por sección (etiquetas del programa), con una caja por sección y su número de pasos. El detalle sigue en la tabla.
- Decisiones:
  - Excepción a AGENTS.md (punto 2, "solo Markdown y JSON" y "nada de frontend"), aprobada por el usuario. El HTML es estático, de revisión, sin scripts ni servidor.
  - Sin dependencias nuevas: SVG y CSS escritos a mano.
  - Identificadores en inglés; textos de la página en español.
  - Las entradas externas van en la columna 0 y las capas se calculan por dependencia.
  - El motivo de macro dinámica se traduce a una frase en la nota, en lugar del código `MACRO_DINAMICA`.
- Pruebas: `tests/unit/test_flujo.py` (11): pasos y datasets, unión entre pasos, capas, `WORK.` como mismo dataset, configuración separada, credenciales fuera del HTML, escape de texto, SVG bien formado, programa sin pasos, macro expandida y bloque condicional dinámico.
- Mediciones: `client_poc.sas` 310 pasos, 69 aristas, 13 s. `client_large.sas` 2,205 pasos, 1,226 aristas, 5 s; HTML de 0,4 MB con la vista por sección.
- Verificación: `uv run pytest -q`: 471 pasan, 1 se salta, 6 xfail. `uv run ruff check .`: limpio.
- Bloqueos y pendientes: en `client_large` la vista por sección sigue densa: una sección muy grande ("Escritura COLUMNAS_DEPOSITOS", 1,084 pasos) domina la columna y algunas curvas largas cruzan cajas. No se resolvió en este hito.

## Hito 44. Calidad de las pruebas

- Fecha: 2026-11-03
- Qué se hizo:
  - Aislamiento de la base: `tests/conftest.py` apunta `SGM_DB` a una base temporal por prueba. Antes, las pruebas de CLI que compilan, registran huecos o listan decisiones escribían en `~/.sgm/sgm.sqlite`, compartida por todas las pruebas, los workers de xdist y las ejecuciones previas.
  - `tests/unit/test_security.py` ya no lee `out/`: esa carpeta es estado local y el resultado de la prueba dependía de lo que hubiera en ella.
  - Se quitó `tests/support/cache.py`: nada lo importa y apunta a paquetes que ya no existen (`sas_grid_migrator`, `apps/api`, `mcp/`). Al llamar `cached_planset` falla con `ModuleNotFoundError: No module named 'sas_grid_migrator'`.
  - `tests/unit/test_golden_equivalencia.py` compara cada plan golden con el actual y clasifica cada diferencia como `quitado`, `cambiado` o `agregado`. Solo se aceptan campos agregados listados en `CAMPOS_ADITIVOS` (hoy `talend_expression_candidates`, hito 14).
  - Segundo programa SAS: `tests/fixtures/sas/independiente/inventario_mensual.sas`, con `%let`, `WHERE`, `SORT ... OUT=`, `MERGE` con `IN=`, `PROC MEANS` con `CLASS` y un nombre de salida con macrovariable. `tests/unit/test_programa_independiente.py` fija lo que el compilador demuestra. Las tablas de origen no tienen esquema, así que sus huecos son `TIPO_DESCONOCIDO` y no se inventan tipos.
- Falla intermitente de `test_guia_y_json_no_contienen_secretos_sin_enmascarar` (tarea 29): no reproducida. Hipótesis probadas:
  - Semilla de hash: la misma compilación de `client_large.sas` con `PYTHONHASHSEED` de 0 a 9 no produce ninguna coincidencia del regex.
  - Paralelo: `uv run pytest tests/unit/test_compile_outputs.py -n 2` pasó en todas las pasadas ejecutadas en este hito.
  - Estado compartido: la prueba no lee disco ni base, y `compile_project` no usa `Store`. El estado compartido sí existía en las pruebas vecinas (base del usuario y `out/`) y ya quedó aislado.
  - Causa: no determinada. Si reaparece, pytest muestra la lista `secrets` con las coincidencias; hay que anotar esa salida y el `PYTHONHASHSEED` del fallo.
- Pendiente, cobertura (tarea 33): `pytest-cov` no está entre las dependencias de desarrollo permitidas por AGENTS.md y no se instaló. No hay cifra de cobertura hasta que se autorice.
- Verificación: `uv run pytest -q` (xdist): 390 pasan, 1 se salta; `uv run ruff check .`: limpio. Pruebas nuevas o cambiadas, serie (`-n 0`): 18 pasan.
- Decisiones:
  - El aislamiento de la base es global (autouse) y no por archivo, para que ninguna prueba nueva escriba en la base del usuario por omisión. Una prueba que necesite otra base la fija con `monkeypatch.setenv`.
  - `test_security` deja de leer `out/`; las salidas se revisan en pruebas que las generan en una carpeta temporal.

## Hito 44b. Documentación de referencia: herramientas, índices y guía

- Fecha: 2026-11-03
- Qué se hizo (de la lista de 50 tareas, grupos de documentación y herramientas):
  - Tarea 50: la descarga sale de `tools/referencia/` (`descargar.py`, `fuentes.py`). Usa solo biblioteca estándar. Talend se baja en Markdown; una página sin `.md` queda anotada como no descargada.
  - Tarea 10: `tools/referencia/indice.py` escribe `<guía>.INDEX.md` por cada PDF de SAS, desde sus marcadores (sección → página). Las seis guías ya tienen su índice.
  - Tarea 49: `docs/referencia/README.md` con la tabla de fuentes, fecha y cómo regenerar.
  - Tareas 46, 47, 48: `docs/automatizacion/02-mapa-de-flujo.md` (sección 8, `sgm flujo`), `04-runbook.md` (cómo generar y leer el flujo) y `docs/conventions.md` (sección 8, excepción del HTML).
  - Tarea 9: la versión exacta de SAS del cliente sigue sin confirmar; queda como pendiente en `docs/referencia/sas/README.md`. No se puede resolver desde el repo.
  - Los PDF de SAS (~48 MB) se excluyen de git con `.gitignore`. Se versionan el texto y los índices.
- Decisiones:
  - `pypdf` solo se usa en `tools/referencia/indice.py`, con import tardío. No es dependencia de `sgm`; queda fuera de `pyproject.toml`.
  - La prueba de referencia no exige los PDF (no están en git); exige el `.txt` y el `.INDEX.md` de cada guía.
- Pruebas: `tests/unit/test_referencia_tools.py` (7): enlaces de subpáginas por nombre, sin duplicados, aplanado de marcadores, formato del índice, URLs, texto e índice presentes para cada guía, y página presente para cada componente de Talend del proyecto.
- Verificación: `uv run pytest -q` y `uv run ruff check .` ver al cierre del hito.

## Hito 45. Agrupación declarada por producto en el diseño

- Fecha: 2026-11-03
- Qué se hizo:
  - `sgm.agrupacion.Declaracion`, `cargar_declaracion` y `grupos_declarados`: la agrupación por sufijo declarada en YAML (`region_marcador` y `productos` con sus sufijos) produce los grupos; una región sin producto no se adivina y queda suelta.
  - `sgm diseno` busca `<programa>.agrupacion.yaml` junto al programa y, si no está, en `decisiones/`; `--agrupacion` manda sobre ambos. El JSON declara el modo (`declarada`, o `similitud` con su umbral) y cada joblet lista sus `regiones`.
  - Corrección documental: las regiones con producto son 24 de 30 (11 CTE, 10 AHO, 3 NEQUI) y 6 quedan sin producto. La sección anterior decía 25 y 5, y la suma no cuadraba.
- Medición en `client_large.sas` con su YAML: 3 joblets (11, 10 y 3 regiones) con 64, 38 y 57 firmas; Job padre de 66 nodos; 131 firmas distintas, las mismas que con similitud porque son las mismas regiones. La suma de firmas por joblet sube de 121 a 159: se arman los tres procesos del diseño a cambio de más variedad dentro de cada joblet.
- Decisión: sin YAML se mantiene la similitud con umbral 0,2; con YAML manda la declaración del equipo. El archivo de `decisiones/` existía desde la ronda anterior y ningún código lo leía.
- Pruebas: `tests/unit/test_agrupacion.py` (2 nuevas: agrupación por sufijo con región sin producto, y YAML mal formado) y `tests/unit/test_diseno.py` (1 nueva: el comando detecta el YAML junto al programa y deja la región sin producto como suelta).
- Verificación: `uv run ruff check src tests`: limpio. `uv run pytest -q`: 495 pasan, 1 se salta, 6 xfail. `ruff check .` falla solo en `tools/referencia/`, trabajo sin confirmar de otro agente.

## Hito 47. SQL de base con WITH, funciones portables y reglas PROC SQL (tareas 13 a 16)

- Fecha: 2026-11-03
- Qué se hizo:
  - `ir/sql_portability.py`: funciones de una expresión (sqlglot) contra `rules/sas/sql-functions.json`; solo `status: portable` pasa. `CASE`, `AND`, `OR`, `NOT` y paréntesis no cuentan como funciones. `load_sql_portable` se movió aquí desde `compile.py`.
  - `passes/db_sql.py`: `sas_to_sql` rechaza funciones no portables (antes, `cats(...)` o `input(...)` llegaban a la base). Las cadenas se escriben con `WITH sgm_paso<n>` en vez de subconsultas.
  - `rules/sas/sql-semantica.yaml` y `ir/sql_semantics.py`: reglas `agregado-sin-group-by` (tratamiento `pendiente`) y `select-into-macrovariable` (`programa_anfitrion`). La carga falla si un id o un tratamiento no es válido.
  - `ir/lower_sql_flow.py`: un agregado sin GROUP BY con columnas sin agregar queda `parcial` con `params.pendiente` y nota; el `SELECT ... INTO` se reconstruye como `set_variable` por posición (`into :a, :b` asigna cada variable a su elemento), con la expresión original.
  - `passes/p04_placement.py` y `passes/db_sql.py` consultan la regla: un agregado pendiente no se ubica en la base ni genera SQL.
  - `frontend/sql_normalize.py`: `into` acepta varias variables y `trimmed`.
- Pruebas: `tests/unit/test_sql_with.py` (15) y `tests/unit/test_sql_semantica.py` (14). Golden, frontend, push, reglas y nombres pasan sin cambiar referencias. `ruff check .` limpio.
- Bloqueos abiertos: `WITH` dentro de `CREATE TABLE ... AS` y `ORDER BY` en CTE no verificados en Impala (ver docs/automatizacion/07-sql-investigacion.md).

## Decisiones (hito 20)

- Impala no tiene dialecto en sqlglot: se sigue usando `write="hive"`, como antes.
- La portabilidad es conservadora: una función sin entrada `portable` en el JSON no es portable.
- Un `SELECT ... INTO` con varias filas y sin separador queda `parcial`: no está demostrado qué valor toma SAS.
- `trimmed` se ignora sin nota; afecta solo a espacios de columnas de texto (pendiente).
- Tratamiento y etiqueta de las reglas viven en el YAML; el código solo conoce los dos ids y los dos tratamientos.

## Hito 48. Investigación y medición SQL (tareas 17 a 19)

- Fecha: 2026-11-03
- Qué se hizo:
  - `docs/automatizacion/07-sql-investigacion.md`: README de sqlglot (sin dialecto Impala; Hive como más cercano; parser permisivo), documentación de Impala sobre `WITH` (CTAS con `WITH` no confirmado) y lista de pendientes.
  - `tools/medir_sql_portable.py`: clasifica las sentencias de PROC SQL de un archivo con las reglas del código.
- Medición en `tests/fixtures/sas/client/client_large.sas`: 463 sentencias de PROC SQL; 231 portables; 118 no consultas; 86 con `parse_error`; 22 `SELECT ... INTO`; 4 con macro; 2 con función no portable.
- Verificación: `ruff check .` limpio.
- Bloqueos abiertos: las 86 sentencias con `parse_error` no están clasificadas por causa.

## Decisiones (hito 48)

- La investigación se hizo con búsquedas web y lectura de páginas públicas; las afirmaciones sobre Impala se marcan como documentadas o pendientes, no como probadas.
- La herramienta de medición es un script en `tools/`, no un test: lee el archivo grande y no se ejecuta en la suite.

## Hito 45b. `sgm flujo`: tramos, índice de datasets, JSON y pruebas de salida

- Fecha: 2026-11-03
- Qué se hizo (tareas 41 a 45 y 31 a 38 de la lista de 50):
  - 41: una sección de más de 150 pasos se parte en tramos consecutivos según el dataset que escribe cada paso (`src/sgm/flow/seccion.py`). Un paso sin escritura sigue al tramo anterior. Client_large: la sección de 1,084 pasos pasa a tramos.
  - 42: las conexiones del diagrama van en codo, cada una por su carril vertical entre columnas. Ya no cruzan las cajas.
  - 43: sección "Datasets" en la página: cada dataset con los pasos que lo escriben y los que lo leen, enlazados a su fila. Sin JavaScript.
  - 44: los pendientes enlazan a su paso.
  - 45: `sgm flujo --json` escribe `<programa>.flujo.json` (versión 1) con el modelo completo.
  - Pruebas (`tests/unit/test_flujo_salidas.py`): índice de datasets, JSON, tramos, vista por sección que cuenta todos los pasos una vez, conexiones sin retroceso de capa, posiciones únicas, HTML con etiquetas balanceadas, golden de la página (`tests/fixtures/flujo/`), programa vacío, carpeta de generalización, comando que crea la carpeta de salida.
- Bug encontrado y corregido: un `.sas` guardado con BOM UTF-8 perdía su primer paso, porque el `﻿` quedaba pegado a `data`. Ahora `build_flows` quita el BOM antes de analizar.
- Decisiones:
  - La división de secciones grandes usa el dataset escrito, no el tipo de paso. En client_large, 604 de los 1,084 pasos son macros dinámicas sin escritura; esos se quedan en el tramo que los contiene.
  - Las pruebas de tiempo no se incluyen (tarea 32): dependen de la máquina. Se usa el tamaño del HTML y el número de pasos como señal.
  - El módulo `model.py` se mantiene bajo 300 líneas; la vista por sección y el índice de datasets viven en `seccion.py` y `salida.py`.
- Medición: client_large.sas, 2,205 pasos. HTML de 2.0 MB; JSON de 2.0 MB.
- Pruebas: `tests/unit/test_flujo.py` (11) y `tests/unit/test_flujo_salidas.py` (14). Suite completa y ruff: ver verificación al cierre.

## Hito 46. Catálogo documental de SAS en YAML, con página por entrada (tareas 1 a 8, 21, 23 a 27)

- Fecha: 2026-11-03
- Qué se hizo:
  - Tipo nuevo `catalogo` (`schemas/rules/catalogo.schema.json`, carpeta `rules/sas/catalogo/`). Cada entrada exige `fuente` con página (`p. N`) y un `estado`. Tarea 23: el validador rechaza una entrada sin página (prueba `test_una_entrada_sin_pagina_no_pasa_el_esquema`). Tarea 24: la misma regla de estilo, por esquema.
  - `funciones-usadas.yaml` (tarea 1): 36 funciones y CALL routines de `client_large.sas`, cada una con la página de la guía (`lefunctionsref.INDEX.md`).
  - `sentencias-data-step.yaml` (tarea 7): 80 sentencias de `lestmtsref`. `reconocida` si el parser las clasifica; `no_reconocida` si caen en `other`. `DO UNTIL` y `Label:` figuran como `no_verificada`, porque el parser solo mira la primera palabra.
  - `sentencias-proc-sql.yaml` (tarea 8): sentencias y cláusulas de `sqlproc`. Pruebas de HAVING y UNION (quedan dentro del SELECT).
  - `funciones-macro.yaml` (tareas 5 y 6): funciones de macro de `mcrolref`. Reconocidas: SYSFUNC, EVAL, STR.
  - `opciones-dataset.yaml` (tarea 3): 40 opciones de `ledsoptsref`. Reconocida: IN=.
  - `sql-nulos.yaml` (tarea 21): valores nulos y faltantes de PROC SQL, citados. Ninguno tiene regla implementada.
  - Tarea 4 bloqueada: una regla `proc-sort.yaml` se escribió y se revirtió. `test_proc_rules.py::test_sort_sigue_en_codigo` fija la decisión de F1.4 (PROGRESS, hito de F1.4): `sort` depende de si hay BY y de NODUPKEY, y una regla plana no lo expresa. Ya existen PROC FREQ y PROC MEANS como reglas.
  - Tarea 26: la guardia de nombres de scripts ahora mira `tools/*.py` y `rules/*.yml`. `docs/` queda fuera a propósito (describe los programas del cliente).
  - Tarea 25: no hay motivos sin uso. Los 13 de `routing.yaml` aparecen en `src/sgm`. Se fija con prueba, no se borra nada.
  - Tarea 27: `test_plumbing_categorias.py` tiene un caso que cae y un caso cercano que no cae, para las 19 categorías. El pipeline pasa la sentencia sin `;`; la prueba lo reproduce.
  - Tarea 2: prueba de que las funciones de `rules/sas/functions` existen en la guía.
- No hecho, con motivo:
  - Tarea 22 (informats): la guía de formatos (`leforinfref`) no está descargada (404). Pendiente.
  - Tarea 21, la regla en código: `rules/sas/sql-semantica.yaml` lo lee `src/sgm/ir/sql_semantics.py`, que hace fallar la carga con un id que no conoce. Se documentó en el catálogo y no se tocó ese archivo, porque lo editó otro trabajo en paralelo.
- Decisiones:
  - Un catálogo por tema, no un archivo por función (tarea 1 pedía "una regla por función"). Un archivo por tema evita 36 archivos casi vacíos. Cada entrada conserva su id.
  - `estado` tiene el mismo significado en todos los catálogos: lo que el repo hace hoy con ese elemento. La descripción de cada archivo dice el criterio.
  - Los conteos de usos de `client_large.sas` son del fixture, no de la documentación. Van en la nota.
- Pruebas: `tests/unit/test_catalogo_sas.py` (27), `tests/unit/test_plumbing_categorias.py` (38), `tests/unit/test_routing_motivos.py` (2), `tests/unit/test_no_script_specific_names.py` (ampliada).
- Verificación: `uv run sgm rules validate`: válido. `uv run pytest -q` y `uv run ruff check .`: ver al cierre del hito.

## Hito 49. Documentación de Talend contra el catálogo, cruce con el código y pruebas de entrada (tareas 11 a 20, 28, 29, 30, 37)

- Fecha: 2026-11-03
- Qué se hizo:
  - Tarea 12: las 539 páginas de `rules/talend/components.json` bajadas en `docs/referencia/talend/catalogo/` (`descargar.py talend --catalogo`, sin errores). `test_cada_componente_del_catalogo_tiene_su_pagina`.
  - Tarea 11: `tools/referencia/verificar.py` compara el catálogo con las páginas (título y familia). Informe en `catalogo/VERIFICACION.md`. Hay 8 discrepancias de familia, sin errores de título: 6 LDAP (catálogo `Business/LDAP`, página `Databases`), `tReplace` (catálogo `Processing`, página `Data Quality`) y `tREST` (catálogo `Internet`, página `ESB`). Quién tiene razón lo decide una persona; el catálogo no se cambió.
  - Tarea 15: `tjdbcconnection-opciones.yaml`, 14 propiedades extraídas de sus tablas (`tools/referencia/opciones.py`).
  - Tarea 20 (parcial): la guía de Studio (R2026-09) incluye ahora el tema *Creating a connection*. 16 temas, sin duplicados (la primera versión repetía los joblets; se corrigió). Falta *Creating metadata database*: vive en otra ruta del sitio y el descargador no la sigue.
  - Tareas 16, 18, 19: `cruce-con-el-codigo.md`, con cada referencia a archivo y línea comprobada con grep. Brechas: `tPrejob`/`tPostjob` no se emiten en `src/sgm` aunque la convención los describe; `tDie` se usa para parar sin el `tLogCatcher` que la documentación pide junto a él.
  - Tarea 28: `inventario.sha256` registra la huella del inventario oficial. `test_la_huella_del_inventario_no_cambio_sin_revisarse` falla si el inventario cambia.
  - Pruebas: `tests/unit/test_talend_referencia.py` (11), `tests/unit/test_entrada_sas.py` (28 con las pruebas del lexer y del redactor), y `tests/unit/test_flujo_salidas.py` con la prueba de la tarea 37.
- Pendiente, con motivo:
  - Tarea 13 (funciones de `tMap`): `tmap.md` no trae el catálogo de funciones de expresión. Se necesitan otras páginas de Talend que no están descargadas.
  - Tarea 14 (motores de `tSQLTemplate`): la página no enumera los motores; la lista está en el desplegable de la interfaz.
  - Tarea 17 (prueba del diseño de joblets frente a contextos): el joblet de contexto no está conectado al plan (hito 39); la prueba se escribe cuando se conecte.
  - Tarea 20, la página *Creating metadata database*: fuera de la ruta que sigue el descargador.
- Hallazgo, sin cambio: en la tarea 29 se pensó que `* comentario; de linea;` era un fallo del lexer. No lo es: en SAS, un comentario `*` termina en el primer `;`, y el lexer lo hace igual. La prueba fija ese comportamiento.
- Decisiones:
  - El catálogo de componentes se baja solo en su página raíz (sin subpáginas), para que el tamaño quede en 5 MB.
  - El extracto de opciones JDBC es un YAML de consulta, no una regla: no pasa por el esquema de `rules/`.
- Verificación: `uv run pytest -q`: 629 pasan, 1 se salta, 6 xfail. `uv run ruff check .`: limpio.

## Hito 51. Reescritura, Fase 1: linaje completo (APPEND, archivos, fuentes SQL, región por llamada)

- Fecha: 2026-11-04
- Contexto: plan de reescritura en `docs/plan-reescritura/`. Fase 0 (hito 50) midió y fijó la meta; ver `fase0-correccion-h3.md` (las regiones vienen en copias por producto de 93 a 99,7 % al normalizar el sufijo).
- Qué se hizo:
  - `flow/pasos_archivo.py`: `PROC APPEND`, `PROC IMPORT/EXPORT` y `INFILE/FILE` entre comillas entran al grafo como datasets `file:<ruta>`. `FILE LOG/PRINT` e `INFILE DATALINES` se ignoran.
  - `frontend/sql_fuentes.py`: extracción de tablas de PROC SQL con tokenizador (sin tablas falsas en `extract(... from ...)`, listas con coma, todos los JOIN, alias, subconsultas, CTE).
  - `flow/regiones.py`: división por marcador (parámetro del YAML de decisiones) y asignación de pasos por la línea de la llamada más externa. `ProgramItem` y `FlowStep` ganan `outer_call`; `call` sigue siendo la más interna.
  - `tools/medir_regiones.py`, `tools/etiquetas_fase0.py`.
- Medición en `client_large.sas`: 2.205 pasos, 1.277 aristas; 15 entradas externas (9 archivos: 5 Excel y 4 CSV, que coinciden con las 5 fuentes Excel del diseño manual); 22 salidas de archivo; de 406 datasets WORK escritos, 301 son locales a una región, 74 cruzan regiones y 31 no tienen lector. Paso 0 de región: 233 pasos (antes 1.277 por línea de evidencia).
- Pruebas: `uv run pytest -q`: 715 pasan, 1 se salta, 146 xfail (140 de conformidad). `ruff check .`: limpio.
- Pendiente, con motivo:
  - `infile`/`file` con fileref sin comillas: requiere resolver `FILENAME`.
  - Lecturas de la base por `connect to ... (select ...)`: los nombres de tabla de Impala no aparecen aún como entradas externas.
  - 3 entradas `WORK` sin escritor previo y 3 nombres con macrovariable sin resolver (`&tabla_origen.`).
  - `sql_tree` falla con subconsultas en FROM (no es parte de la extracción de fuentes).
- Decisiones: `call` conserva su significado (más interna) para no mover plantillas ni goldens; la región usa el campo nuevo `outer_call`. El marcador de región vive en el YAML de decisiones, no en el código.

## Hito 52. Reescritura, Fase 2: familias de regiones por producto

- Fecha: 2026-11-04
- Qué se hizo:
  - `frontend/sql.py`: un pass-through (`select ... from connection to <motor> (...)`) ahora expone como lecturas las tablas de su SQL interno. Con eso aparecen en el grafo las tablas de la base que el programa consulta.
  - `frontend/sql_fuentes.py`: arreglo de un fallo propio: la lista de columnas de una subconsulta en `join (select a, b from t)` se leía como lista de tablas.
  - `proceso/familias.py` (nuevo): normaliza regiones (sin comentarios, minúsculas, sufijo de producto como `{P}`), detecta familias por parecido de líneas (umbral 0,85) y lista las diferencias entre miembros. `tools/familias_regiones.py` lo aplica a un programa.
- Resultado en `client_large.sas` (detalle en `docs/plan-reescritura/fase2-familias.md`): 7 familias; 6 son pares aho/cte (parecido 0,89 a 0,997); la 7.ª agrupa 10 regiones que persisten una tabla WORK a la base. Nequi no tiene copias; las tres regiones grandes quedan solas.
- Pruebas: `tests/unit/test_proceso_familias.py` (9), tres más en `test_sql_fuentes.py`.
- Pendiente, con motivo:
  - Nequi sin copias contradice la premisa D6 del diseño manual; sigue como decisión humana (P6).
  - Falta el modelo de proceso (entradas, salidas, etapas, parámetros por familia) y el emisor del documento de ocho secciones.
  - Las entradas de la base que son tablas intermedias del propio programa (persistencias) aún aparecen como entradas externas.
- Decisiones: los sufijos de producto salen del YAML; el módulo no tiene nombres del cliente. El umbral es un parámetro.

## Hito 53. Reescritura, Fase 2: fuentes, persistencias y plantillas de salida

- Fecha: 2026-11-04
- Qué se hizo: `proceso/entradas_salidas.py` reparte las entradas externas del linaje en fuentes (Excel, CSV, tabla de base), persistencias propias (tabla de la base cuyo nombre coincide con un WORK que el programa escribe: el diseño la elimina) y pendientes con motivo (macrovariable, `_all_`, WORK que se lee antes de crearse). Agrupa las salidas de archivo por plantilla con el producto como `{P}`.
- Medición en `client_large.sas`: de 40 entradas externas quedan 12 fuentes (5 Excel, 4 CSV y 3 tablas de base: las 5 Excel y las 3 tablas coinciden en número con el diseño manual), 22 persistencias propias descartadas y 6 pendientes. Las 22 salidas de archivo pasan a 16 plantillas.
- Decisión del YAML `decisiones/client_large.agrupacion.yaml`: se declaran `AHORROS` y `CORRIENTE` como palabras de producto. Con eso las salidas `*_AHORROS`/`*_CORRIENTE` casan con las de `AHO`/`CTE`. Es una declaración del equipo, no un hecho del SAS.
- Pruebas: `tests/unit/test_proceso_entradas_salidas.py` (4). `uv run pytest -q`: 731 pasan, 1 se salta, 146 xfail. `ruff check .`: limpio.
- Pendiente, con motivo:
  - Las 16 plantillas no equivalen aún a las 5 familias de salida del diseño (sábana válida, rechazados, totales, conciliación, log): esa agrupación semántica es decisión humana o va en el YAML.
  - 3 WORK que se leen antes de crearse (`SABANA_SIN_*`): no se investigó cómo se crean (probablemente macro dinámica).
  - Las 4 CSV de entrada no coinciden con las tablas Impala del diseño; no se afirma que sean las mismas fuentes.

## Hito 54. Reescritura, Fase 2: etapas de negocio declaradas

- Fecha: 2026-11-04
- Qué se hizo: `proceso/etapas.py` asigna cada etiqueta `/* Etiqueta: ... */` a la primera etapa cuyo patrón casa. Las etapas y sus patrones viven en `decisiones/client_large.diseno.yaml` (clave `etapas`), no en el código. `tools/cobertura_etapas.py` mide cuántas etiquetas quedan cubiertas y lista las sueltas.
- Medición: 610 etiquetas, 97,9 % con etapa (9 etapas). Quedan 13 sin etapa (5 distintas: `Validar DV`, `Validar monetarios`, `Validar nombres`, `Validar_mes_año`, `tit-cot vacios o 0`). La etapa `persistencia_intermedia` (30 etiquetas `Escritura ...`) coincide con la familia 4 de regiones.
- Límite: los patrones se ajustaron mirando las mismas etiquetas, así que el 97,9 % mide que ninguna quedó huérfana, no que cada una esté bien clasificada. `normalizar` (179) es la etapa más amplia y la más dudosa. Una persona debe revisar el reparto.
- Pruebas: `tests/unit/test_proceso_etapas.py` (7). `ruff check .`: limpio.
- Pendiente: usar las etapas para ordenar el proceso por producto y emitir las secciones 3.x; agrupar las 5 familias de salida del diseño.

## Hito 55. Reescritura, Fase 3: primeras secciones del documento de diseño (1.1 y 1.4)

- Fecha: 2026-11-04
- Qué se hizo:
  - `proceso/secciones_entrada.py`: emite las secciones 1.1 (fuentes) y 1.4 (salidas). Cada fila une lo declarado (`fuentes` y `salidas` en `decisiones/client_large.diseno.yaml`: nombres de parámetros, textos de uso) con lo que el SAS demuestra: tipo y estado de cada fuente salen de las fuentes halladas; el equivalente en el SAS de una salida sale de los archivos que el programa escribe. Lo que el SAS no demuestra queda `pendiente`.
  - `proceso/diseno_doc.py`: `construir_diseno(programa, agrupacion, diseno)` devuelve `{sección: {fila: {columna: texto}}}`.
  - La conformidad (`tests/conformidad/`) llama ahora al emisor. Las secciones emitidas se evalúan de verdad; el resto sigue en `xfail` estricto. Cambié `test_el_emisor_de_las_ocho_secciones_aun_no_existe` (su premisa terminó) por una prueba de que solo se emiten las secciones declaradas.
- Resultado: pasan 15 pruebas más de conformidad (2 de sección y 13 de fila: F01-F03, F05-F08 y S01-S05). Una fila discrepa y queda como `xfail` estricto con su motivo: F04 (el SAS sí lee `CODIGOS_DANE.xlsx`; el manual lo daba por pendiente, así que el migrador halla más que el manual).
- Límite honesto: los nombres de parámetros (`ruta_insumos + arch_dane`) y los textos de uso no están en el SAS; vienen del YAML, que en esas filas contiene el diseño manual. Lo que el emisor deduce es tipo, estado, existencia y el equivalente de `totales_exogena` (`TOTAL_AHORROS_CONS.csv, TOTAL_CORRIENTE.csv`).
- Pruebas: `tests/unit/test_proceso_secciones_entrada.py` (6). `uv run pytest -q`: 759 pasan, 1 se salta, 132 xfail. `ruff check .`: limpio.
- Pendiente: secciones 1.2, 1.3, 2.x, 3.x, 4 a 7; y la prosa del Markdown (hoy solo se emite el contrato de datos).

## Hito 56. Reescritura, Fase 3: sección 6 (equivalencias) desde las reglas de fontanería

- Fecha: 2026-11-04
- Qué se hizo: `proceso/fontaneria.py` aplica los patrones de `rules/sas/plumbing.yaml` a cada sentencia del programa expandido y emite la sección 6: una fila por tipo de fontanería, con cuántas veces aparece y el equivalente en Talend que la regla ya declara. No hay nombres del cliente ni equivalentes inventados. `diseno_doc.construir_diseno` la incluye bajo `SECCIONES_GENERICAS` (sus claves no coinciden con las del manual, así que no entra en la comparación fila a fila).
- Medición en `client_large.sas`: 2.228 de 4.808 sentencias son fontanería, en 12 categorías: `visor_studio` 447, `presentacion` 293, `control_macro` 240, `configuracion_macro` 222, `mensajes` 218, `borrado_datasets` 216, `remoto` 202, `troceado_lotes` 120, `espera` 90, y 60 cada una de `medicion`, `variables_control` y `fin_de_paso`. Coincide con la medición de la Fase 0 (mismos conteos en las categorías comparables).
- Cómo difiere del manual: el manual tiene 8 filas escritas a mano ("30 bloques de macros", "348 tablas WORK") con claves en prosa. Aquí las filas salen de las reglas, con conteos medidos (el SAS tiene 404 nombres WORK distintos, no 348). Las filas de estructura del manual (30 bloques → `job_producto` parametrizado) todavía no se emiten.
- Pruebas: `tests/unit/test_proceso_fontaneria.py` (3). `uv run pytest -q`: 762 pasan, 1 se salta, 132 xfail. `ruff check .`: limpio.
- Pendiente: filas estructurales de la sección 6 (familias de regiones, tablas WORK, exportaciones); render a Markdown; secciones 2, 3, 4, 5, 7, 8.

## Hito 57. Reescritura, Fase 3: documento de diseño en Markdown y comando `sgm proceso`

- Fecha: 2026-11-04
- Qué se hizo:
  - `docs/plan-reescritura/plan.md`: el plan de la reescritura con su estado por fase, los hallazgos que lo corrigieron y lo que no se podrá igualar. `docs/plan-sgm-v2/00-README.md` lleva una nota: su secuencia de fases quedó superada, pero su reparto, contratos y ciclo de huecos siguen vigentes (el README y `motivos.py` lo citan, por eso no se borró).
  - `proceso/analisis.py` (regiones, producto y familias en una sola llamada), `proceso/pendientes.py` (pendientes con motivo) y `proceso/render_md.py` (Markdown). `proceso/diseno_doc.py` ahora devuelve un `DocumentoDiseno` con secciones, resumen y pendientes.
  - Comando `sgm proceso <programa.sas> [--out] [--agrupacion] [--diseno]`: escribe `<programa>.diseno.md`. Lee `decisiones/<programa>.agrupacion.yaml` y `decisiones/<programa>.diseno.yaml` si no se indican.
- Resultado en `client_large.sas`: documento de 79 líneas con resumen (2.205 pasos, 30 regiones, 7 familias, 8 regiones sin copia, 12 fuentes, 22 persistencias propias, 13 plantillas de salida, 2.228 sentencias de fontanería, 597 de 610 etiquetas con etapa), secciones 1.1, 1.4 y 6, y 16 pendientes con su motivo.
- Pruebas: `tests/unit/test_proceso_documento.py` (4). `uv run pytest -q`: 766 pasan, 1 se salta, 132 xfail. `ruff check .`: limpio.
- Pendiente:
  - El documento aún no tiene las secciones 2 a 5, 7 y 8 del manual.
  - Las tablas de 1.1 y 1.4 siguen leyendo nombres del YAML (ver hito 55).
  - `ruff format --check` marca 25 archivos antiguos sin formatear; no es parte de las comprobaciones del proyecto y no se tocaron.

## Hito 58. Reescritura, Fase 2/3: colapso por linaje y tamaño estimado por etapa

- Fecha: 2026-11-04
- Qué se hizo:
  - `proceso/colapso.py`: funde las cadenas lineales de pasos de datos (la tabla entre dos pasos que solo se leen uno a otro es una arista, D1), excluye la fontanería (tipos de transferencia y borrado, y las reglas de `plumbing.yaml`) y cuenta bloques por región y etapa. `plantilla_por_etapa` cuenta una vez cada familia (su región mayor) y omite las etapas con `elimina: true` en el YAML.
  - `proceso/etapas.py`: la etapa declarada admite `elimina: true`; `persistencia_intermedia` lo lleva en `decisiones/client_large.diseno.yaml`.
  - Sección 3 del documento ("Etapas y tamaño estimado") y tres medidas nuevas en el resumen.
- Medición en `client_large.sas` (cota, no número exacto de componentes):
  - 2.205 pasos; 1.473 son de datos tras quitar la fontanería; 988 bloques tras colapsar cadenas lineales.
  - Escribiendo cada familia una vez y sin la etapa de persistencia: **364 bloques**. Por etapa: normalizar 98, validar_documento 82, totales_conciliacion 55, validar_cuenta_y_saldos 36, sabana_final 31, corregir_inconsistencias 24, importar_insumos 18, validar_ubicacion 16, sin etapa 4.
- Hallazgo: el colapso mecánico (364) queda en el mismo orden que el generador anterior (388 componentes) y lejos de los unos 80 del diseño manual. Normalizar literales y números reduce los 755 pasos de las plantillas a 421 formas distintas, tampoco cerca de 80. Esa diferencia no se cierra con colapso: el manual abstrae la validación en joblets y cambia comportamiento (un solo archivo de rechazos con columna motivo, un lookup en caché). Es una decisión de diseño, no una deducción. Lo que el emisor entrega es el diseño por etapas y su tamaño medido; reducirlo a ~80 pide joblets declarados (fase 4) y decisiones del negocio (D2).
- Pruebas: `tests/unit/test_proceso_colapso.py` (5). `uv run pytest -q`: 771 pasan, 1 se salta, 132 xfail. `ruff check .`: limpio.
- Pendiente: joblets por cadena repetida dentro de una etapa; secciones 2, 4, 5, 7 y 8 del documento.

## Hito 59. Reescritura, Fase 5: emisión de Jobs de Talend como `.item`

- Fecha: 2026-11-04
- Qué se hizo:
  - Se revisó el Talend instalado (`docs/plan-reescritura/fase5-talend-instalado.md`): Studio 8.0.1 parche 2026-09 ("Cloud Data Fabric"), sin Job Script ni línea de comandos, con un proyecto Git (`PRJ_BANCOLOMBIA`) y decenas de Jobs reales guardados por ese Studio.
  - Decisión: escribir directamente los `.item` y `.properties` que guarda Studio (plan B), modelados sobre esos Jobs reales.
  - `src/sgm/talend_item/` (`base.py` 96 parámetros base, `modelo.py`, `componentes.py` con `tFixedFlowInput` y `tLogRow`, `item.py` con `render_item` y `render_properties`).
  - `tests/fixtures/talend/hijo_0.1.item`: copia de un Job real de este Studio, con las contraseñas cifradas por defecto vaciadas.
- Resultado: nodos, conexiones y subjobs del Job emitido son idénticos a los del Job real; los 96 parámetros base coinciden en campo y orden. Hubo un fallo propio (el separador de filas `\n` se escribía como salto real en vez de la secuencia de dos caracteres) que la comparación detectó.
- Pruebas: `tests/unit/test_talend_item.py` (5). `uv run pytest -q`: 776 pasan, 1 se salta, 132 xfail. `ruff check .`: limpio.
- No verificado: ningún Job emitido se abrió en Studio; el `.properties` omite `item_key` y el `.screenshot`; las contraseñas por defecto van vacías. `tFileInputExcel`, `tAggregateRow`, `tUnite` y `tReplicate` no tienen ejemplo en el proyecto.
- Pendiente: que una persona abra un Job emitido en Studio; añadir componentes con su comparación contra un Job real (`tMap`, `tFileInputDelimited`, `tFileOutputDelimited`, `tRunJob`, `tPrejob`, `tPostjob`, `tDie`, `tHashInput`/`tHashOutput` como caché).

## Hito 60. Reescritura, Fase 5: plantillas de componentes, conexiones y validación en Studio

- Fecha: 2026-11-04
- Qué se hizo:
  - Validación contra el Studio real. El usuario autorizó usar el proyecto `C:\Users\USUARIO_BISOLUTION1\code\talend-mcp` como validador externo desde la línea de comandos. Es una excepción puntual a la regla de no usar MCP de `AGENTS.md`; el producto `sgm` no depende de él. Se arrancó su servidor con `bun run start:server` y `TALEND_PROJECT` apuntando a `C:/Talend/8.0.1/studio/workspace/talendbancolombia-963626413/PRJ_BANCOLOMBIA`. El puente de Studio respondió.
  - `src/sgm/talend_item/plantillas.py` y `extraccion.py`: plantillas JSON de 16 componentes (tFileInputDelimited, tFileOutputDelimited, tJava, tJavaRow, tRunJob, tPrejob, tPostjob, tFlowToIterate, tDie, tHashInput, tHashOutput, tSortRow, tWarn, tImpalaConnection, tImpalaInput, tImpalaRow) extraídas de Jobs reales con `tools/extraer_plantilla.py`. El extractor vacía contraseñas y datos de entorno (USER, HOST, DBNAME, PORT, URL, FILENAME), neutraliza código, consultas, mensajes, Job hijo y columnas, y regenera las tablas por columna (TRIMSELECT, DECODE_COLS, TRIM_COLUMN) y las columnas del rechazo desde el esquema pedido. Instanciar una plantilla rechaza un parámetro que el componente no tiene.
  - `src/sgm/talend_item/conexiones.py`: OnSubjobOk (lineStyle 1), OnComponentOk (3), Run if (6) e Iterate (7), con los parámetros de Jobs reales.
  - Los atributos XML escriben el salto de línea, el tabulador y el retorno como `&#10;`, `&#09;` y `&#13;`, como hace Studio.
  - `Nodo` admite varios bloques `metadata` y `nodeData`.
- Resultado de la validación en Studio real:
  - El Job de dos componentes (tFixedFlowInput a tLogRow) emitido por sgm se cargó, se compiló con build-batch y, exportado como Build Job y ejecutado con el JDK de Studio, imprimió `1|Bogota` y `2|Medellin`.
  - Un Job de siete nodos (tPrejob, tJava, tFileInputDelimited, tFileOutputDelimited, tJava, tPostjob y tJava, con disparadores) compiló y se ejecutó: imprimió INICIO, FILAS=3 y FIN, y escribió la copia del CSV con cabecera.
- Hallazgos de la validación:
  - La primera plantilla de tFileOutputDelimited venía de un Job con USESTREAM=true. Ese Job compilaba, pero al ejecutarlo fallaba con NullPointerException. Solo se vio al ejecutarlo. Se rehízo desde un Job con el modo por defecto. Compilar no basta: hay que ejecutar.
  - Studio guarda en memoria cada Job por su identificador. Al reemitir el mismo nombre con otro contenido, build-batch regeneró el código con la versión anterior, aunque se hizo refresh del workspace. Con un nombre nuevo funcionó. Los identificadores de sgm son deterministas a partir del nombre y la versión; para revalidar un cambio hay que usar un nombre nuevo.
  - Un diálogo "Network Issue Occured" de Studio bloquea talend_job_verify y la creación en vivo de Jobs. talend-mcp no sabe cerrarlo y no se tocó. La ruta sin interfaz funciona: escribir el `.item`, build-batch, exportar y ejecutar.
  - Los Jobs de prueba se borraron del proyecto después de la validación.
- Pruebas: `tests/unit/test_talend_plantillas.py` (más de 30 casos, con parametrización por plantilla). `uv run pytest -q`: 814 pasan, 1 se salta, 132 xfail. `uv run ruff check .`: limpio.
- No verificado:
  - Ningún Job emitido se abrió en el editor gráfico de Studio. Solo se cargaron, compilaron y ejecutaron por la ruta de generación de código.
  - tMap no está emitido.
  - tFileInputExcel, tAggregateRow, tUnite y tReplicate no tienen ejemplo en el proyecto.
  - Los valores de rutas de trabajo de Studio en las plantillas (TEMP_DIR, BASE_FILE_PATH) vienen del Job de origen.
  - Las plantillas de Impala traen USE_EXISTING_CONNECTION=true, y su CONNECTION no está regenerada.
- Pendiente:
  - tMap con nodeData.
  - Conectar el modelo de proceso con el emisor.
  - Plantillas de componentes sin ejemplo, creándolos en Studio.
- `tMap` (mismo hito): `src/sgm/talend_item/tmap.py` (`EntradaMap`, `SalidaMap`, `tmap()`) con plantilla `tMap.json` y el `nodeData` generado; el encabezado del `.item` declara `xmlns:xsi` y `xmlns:TalendMapper`. Validado en Studio real: tFixedFlowInput a tMap (`row1.id * 2`, `row1.nombre.toUpperCase()`) a tLogRow compiló y ejecutó e imprimió `2|ANA`, `4|LUIS`, `6|MARIA`. Pruebas finales: 821 pasan, 1 se salta, 132 xfail; `ruff check .` limpio.
- `tMap` sin verificar: solo hay un ejemplo real por tipo; lookups con varias entradas, filtros y el orden de varias entradas o salidas en `nodeData` no están verificados (`tmap()` solo escribe lo visto en Jobs reales).

## Hito 61. Reescritura, Fase 5: Jobs del diseño generados desde el modelo de proceso y validados en Studio

- Fecha: 2026-11-04
- Qué se hizo:
  - `decisiones/client_large.jobs.yaml` declara la arquitectura de Jobs: proyecto, entornos DEV, QA y PROD, nombres de los cinco Jobs y mensaje final. Es una decisión del equipo, no un hecho del SAS. `src/sgm/talend_item/arquitectura.py` lo carga y falla con el motivo si el archivo no cumple.
  - `src/sgm/talend_item/jobs_diseno.py`:
    - `job_padre` arma el Job padre de la sección 3.1 del diseño: tPrejob, tJava que marca `env_valido`, tDie con EXIT_JVM condicionado por Run if, tRunJob a insumos, tFixedFlowInput de productos a tFlowToIterate a tRunJob de producto por iteración con los parámetros producto, tabla_origen y sufijo, tRunJob a totales y a conciliación encadenados por OnSubjobOk, y tPostjob con tLogRow.
    - `jobs_hijos` emite los cuatro hijos como `tJava` que dicen qué les falta (`job_pendiente`).
    - Los productos salen de `decisiones/client_large.agrupacion.yaml` (CTE, AHO, NEQUI). La tabla de origen de cada uno queda vacía y se informa como pendiente, porque el SAS no la demuestra.
    - El padre declara contextos: un grupo Default con `env_nombre` vacío y un grupo por entorno con su valor.
  - `src/sgm/talend_item/escritura.py`: `escribir_job` escribe el par `.item` y `.properties`.
  - `src/sgm/cli_talend.py`: comando `sgm talend <programa.sas>`, que escribe los cinco Jobs en `<out>/<programa>/talend/process/`.
  - Contextos de Job: `ParametroContexto`, `Job.contextos` y los grupos Default y de entorno. Los hizo un subagente y se validó en Studio: `--context=DEV` imprime el valor del grupo.
  - Siete plantillas nuevas, validadas ejecutando en Studio: tFileInputExcel, tAggregateRow, tUnite, tReplicate, tFileExist, tSetGlobalVar y tLogCatcher. Se obtuvieron creando Jobs de referencia con el modo offline de talend-mcp y completando todos los parámetros de la definición de Studio (`defaultValue` de `component-definitions.json`) con un script temporal.
  - tFileInputExcel se ejecutó con `talend_job_execute` (salida 0; filas 1|Ana|10, 2|Jose|20 y 3|Lucia|30), pero el Build Job falla por una dependencia Maven (log4j-bom) sin red. No se validó con el `.bat`.
- Resultado en Studio real (nombres nuevos, de _v2 a _v6, en cada intento):
  - Los cinco Jobs compilan.
  - El padre, exportado y ejecutado con `--context=DEV`, corre insumos una vez, producto tres veces (CTE, AHO y NEQUI, por iteración), totales, conciliación, y escribe "Proceso terminado". Salida 0.
  - Con el entorno vacío (Default), el Prejob marca `env_valido=false`, el tDie condicionado se ejecuta, termina la máquina virtual y ningún hijo corre. Salida 1.
- Hallazgos:
  1. El parámetro `ACTIVATE=false` en una conexión Run if significa conexión desactivada, no una condición. Copiarlo de un Job real dejó el tDie suelto, que se ejecutaba siempre. Studio lo omite cuando la conexión está activa.
  2. La plantilla de tDie venía de un componente desactivado (`ACTIVATE=false` en el nodo), y Studio no generó su código. La extracción ahora descarta `ACTIVATE`.
  3. La regla que neutralizaba el parámetro CODE vaciaba también el código de salida numérico de tDie y tWarn. Al compilar daba `new Integer()` sin argumento. Ahora solo se vacía el CODE de los campos de código Java (MEMO_EDITOR_JAVA).
  4. tPrejob que lanza una excepción no detiene el flujo principal en Talend. Hace falta un tDie con EXIT_JVM.
  5. build-batch compila en paralelo, y un padre que llama a hijos recién creados puede fallar la primera vez. Conviene compilar primero los hijos y después el padre.
  6. El MERGE de tUnite usa lineStyle 10 (FLOW_MERGE), leído del enum `EConnectionType`.
  7. tLogCatcher, tAggregateRow y otras plantillas que se completaron a mano traen `show` y orden calculados por regla, no copiados de un Job guardado por Studio.
  8. Con PASSWORD vacío, Studio genera `ofNullable()`. Una instancia debe recibir un valor.
- Limpieza de datos: las plantillas tAggregateRow (OPERATIONS) y tFileInputExcel (SHEETLIST, ahora "Sheet1") no guardan datos de los Jobs de referencia.
- Pruebas: `tests/unit/test_talend_contextos.py` (7 casos), `tests/unit/test_talend_plantillas_extra.py` (7) y `tests/unit/test_talend_jobs_diseno.py` (8). `uv run pytest -q`: 857 pasan, 1 se salta, 132 xfail. `uv run ruff check .`: limpio.
- No verificado:
  - Ningún Job se abrió en el editor gráfico de Studio.
  - Los parámetros de contexto locales no tienen ejemplo real guardado por Studio. Se aceptan y se resuelven al ejecutar, pero no se comparó el XML.
  - `show` y orden de las siete plantillas nuevas.
  - Lookups y filtros de tMap.
- Pendiente:
  - Los hijos son esqueletos que dicen qué falta. Hay que traducir la lectura de insumos (Excel a caché con tHashOutput), la lectura y validación de producto (tImpalaInput, tMap, joblets), y totales y conciliación.
  - tDBClose y la conexión compartida de Impala.
  - El registro de errores (`jl_registro_errores`) y OnSubjobError (lineStyle sin ejemplo real).


## Hito 62. Ciclos locales de pruebas incrementales

- Fecha: 2026-11-04
- Qu? se hizo: se agreg? `pytest-testmon` como dependencia de desarrollo y se document? en README el comando local `uv run pytest --testmon -q -n 4`. La base `.testmondata` queda fuera de git. La suite completa `uv run pytest -q` contin?a como verificaci?n obligatoria.
- Decisi?n: habilitar selecci?n incremental solo al pedir `--testmon`; no activarla por defecto, para que las ejecuciones est?ndar sigan corriendo toda la suite. La dependencia adicional est? aprobada por el usuario.
- M?tricas: l?nea base con `--durations=20`: 74,21 s para 859 pruebas pasadas, 1 omitida y 132 xfail; destacaron compilar todos los fixtures (18,32 s) y validar componentes del cat?logo (15,45 s). Con Testmon ya inicializado y `-n 4`, una ejecuci?n sin pruebas afectadas tard? 10,94 s en seleccionar y recolectar (sin ejecutar tests). Validaci?n completa final: 899 pasadas, 1 omitida y 132 xfail en 69,59 s; Ruff limpio.
- Uso: la primera ejecuci?n incremental corre la suite para construir el mapa; luego `uv run pytest --testmon -q -n 4` elige las pruebas afectadas. Tras cambios amplios, de configuraci?n, dependencias o pruebas, ejecutar `uv run pytest -q` completo.
- Bloqueos: ninguno.

- Bloqueo detectado en una repetici?n posterior: `uv run pytest -q` fall? en `tests/unit/test_talend_jobs_diseno.py::test_los_insumos_declarados_llevan_cache_o_variables_globales` (898 pasaron, 1 fall?, 1 omitida, 132 xfail). El test espera cuatro caches, pero el YAML de decisiones modificado en el ?rbol de trabajo ya contiene `cache_periodo`. Esos cambios estaban presentes antes de este hito y no se modificaron aqu?; requieren actualizar/verificar juntos el YAML y su expectativa.

- Estado final tras la repetici?n: `uv run pytest -q` pas? (903 pruebas, 1 omitida y 132 xfail en 78,06 s) y `uv run ruff check .` qued? limpio. El fallo intermedio ya no se reproduce.

## Hito 63. Reescritura, Fase 5: diseño simple de Jobs (sin caché), periodo en el padre y columnas deducidas del SAS

- Fecha: 2026-11-04
- Qué se hizo:
  - Se eliminó `job_insumos` y el caché compartido entre Jobs. Lo pidió el usuario: "que sea simple".
  - `src/sgm/proceso/columnas_fuente.py` deduce las columnas de cada Excel importado por `PROC IMPORT`, a partir de cómo el programa las usa: alias en `PROC SQL` (incluido `alias.'NOMBRE'n`), `SELECT col INTO :var FROM` y `rename=`. No inventa columnas: un Excel sin columnas usadas queda con esquema pendiente. Resultado en el programa grande:
    - Homologacion_tpo_dto.xlsx: CNAME, CODIGO DIAN.
    - Cod_pais.xlsx: Codigo_Pais, Nombre Pais.
    - CODIGOS_DANE.xlsx: CODIGO_DANE.
    - Validacion_fecha.xlsx: AÑO, MES, DIA.
    - Homologacion_tpo_dto_Nequi.xlsx: CNAME, CODIGO DIAN.
  - `src/sgm/proceso/insumos.py`: `resolver_insumos` une las fuentes declaradas en `decisiones/<programa>.diseno.yaml` con la ruta, las variables de contexto (ruta y archivo) y las columnas halladas. Lo que falta queda como pendiente, con su motivo.
  - `tools/simular_insumos.py` escribe un .xlsx simulado por cada Excel del programa, solo con la biblioteca estándar. Los datos son `SIM_<columna>_<n>`. Si no hay columnas, escribe una columna `PENDIENTE`. Sirve para probar sin los archivos reales.
  - `src/sgm/talend_item/periodo.py`: `tFileInputExcel` y `tJavaRow` en el padre asignan `context.periodo_*`. `nombre_columna` convierte los nombres del Excel en identificadores válidos en Java: AÑO pasa a ANO y los espacios pasan a guion bajo.
  - `arquitectura.py` y `decisiones/client_large.jobs.yaml` ya no declaran `insumos`. Ahora declaran `periodo` (fuente y variables) y `lookups_producto`.
  - `jobs_diseno.py`: el padre arranca con el periodo y recorre producto, totales y conciliación. Los tres hijos esqueleto declaran e imprimen las variables del periodo. El hijo de producto lista los lookups con sus columnas en su mensaje de pendiente.
  - `sgm talend` ahora escribe cuatro Jobs: el padre y tres hijos.
- Resultado en Studio real:
  - El padre, con un Excel simulado de fecha, compiló, se exportó y se ejecutó con salida 0. Leyó el Excel.
  - Los hijos imprimieron `periodo_anio = SIM_AÑO_1`, `periodo_mes = SIM_MES_1` y `periodo_dia = SIM_DIA_1`.
  - El hijo de producto corrió tres veces (CTE, AHO y NEQUI, cada una con sus parámetros).
  - El padre terminó con "Proceso terminado".
- Hallazgos:
  1. `tFileInputExcel` con VERSION_2007 genera un `Optional.ofNullable()` vacío y no compila si PASSWORD está vacío o vale `***`, porque Studio trata `***` como máscara. Con un valor normal (ni vacío ni máscara) compila, y Excel lo ignora porque el archivo no tiene clave. El valor se pasa desde `periodo.py`.
  2. La ejecución con `talend_job_execute` desde Studio no carga los archivos de contexto: el grupo DEV no se encuentra y las variables quedan en null. Para Jobs con contexto hay que exportar el Build Job y ejecutar su lanzador.
  3. La exportación de Jobs con `tFileInputExcel` fallaba por poms públicos de Maven ausentes de la caché local en modo offline: `logging-parent` 11.3.0, `log4j-bom` 2.24.2 y `log4j-bom` 2.24.3. Hay red a Maven Central. Se resolvió descargando esos poms a la caché de Studio (`C:\Talend\8.0.1\studio\configuration\.m2\repository`) con un script temporal que lee el log de Studio y baja lo que falta. Es un cambio fuera del repositorio.
  4. `rm -rf` con una variable sin comprobar es bloqueado por el sistema: usar `${VAR:?}`.
- Decisiones:
  - Se eliminó `job_insumos` y el caché compartido. Motivo técnico, probado ejecutando en Studio 8.0.1: `tHashOutput` y `tHashInput` no pueden compartir datos entre Jobs distintos con ninguna configuración. La clave del buffer lleva el nombre del Job más un pid aleatorio, el LIST de `tHashInput` solo ve los `tHashOutput` del mismo Job, y el modo PERSISTENT está comentado. Es el riesgo que el diseño manual marcaba como no probado (`tCacheIn` con `tRunJob`).
  - Alternativa descartada: una rutina Java con mapa estático. Un agente intentó instalarla, pero Studio no carga rutinas nuevas sin reiniciar y el formato de `.item` de rutina no tiene ejemplo real. No se validó y se descartó el código.
  - Desviación respecto al diseño manual (secciones 1.2 y 3.2): los Excel pequeños se leerán como lookup dentro del `tMap` de `job_producto`. La fecha del proceso la lee el Job padre una vez y la deja en las variables de contexto `periodo_anio`, `periodo_mes` y `periodo_dia`. Los hijos las heredan porque el padre transmite el contexto completo.
- Pruebas:
  - Pruebas nuevas: `test_proceso_columnas_fuente.py` (28), `test_proceso_insumos.py` (3) y `test_tools_simular_insumos.py` (9). `test_talend_jobs_diseno.py` se reescribió (13).
  - `uv run pytest -q`: 902 pasan, 1 se salta y 132 xfail.
  - `uv run ruff check .`: limpio.
- No verificado:
  - El orden de las columnas dentro de cada Excel real no está en el SAS. Talend mapea por posición.
  - El nombre de la hoja: el SAS dice `SHEET=''`, que es la primera hoja, y Talend pide un nombre. Se usa la variable `hoja_excel` con valor "Sheet1" por defecto.
  - Tipos de columna: todas son String, porque nada en el SAS los demuestra.
  - Ningún Job abierto en el editor gráfico de Studio.
  - Los lookups todavía no están en un `tMap`.
- Pendiente:
  - Traducir `job_producto` (lectura de Impala, validación con los lookups en `tMap`, salidas), `job_totales` y `job_conciliacion`.
  - La tabla de origen de cada producto.
  - `tDBClose` y la conexión Impala compartida.
  - El registro de errores.

## Hito 64. Reescritura, Fase 5: origen de datos de cada producto deducido del SAS y job_producto con lectura real

- Fecha: 2026-11-04
- Hallazgo: los datos de cada producto vienen de archivos CSV (`PROC DOWNLOAD` + `PROC IMPORT DBMS=DLM`, delimitador `;`, sin cabecera), no de tablas Impala como supone el diseno manual. CTE usa `DBIFTCD.csv`, AHO `DBIFTCS.csv` y NEQUI `F_1019.csv`; los tres tienen 23 columnas. `Base_datos_Nequi.csv` (6 columnas) es auxiliar de Nequi. Esto respalda un solo `job_producto` (D6).
- Que se hizo: `proceso/fuentes_csv.py`, `esquema_csv.py` (nombres de columna deducidos de `VARn AS NOMBRE` y `X=input(left(VARn),N.)`), `origen_producto.py`; `talend_item/jobs_producto.py` (lee `context.ruta_origen` con el esquema deducido y cuenta registros); el padre pasa `ruta_origen` por producto; `tools/simular_productos.py` escribe los CSV simulados.
- Resultado en Studio real: el padre exportado con CSV simulados corre los tres productos y cada uno imprime 3 registros; salida 0.
- Pruebas: `test_proceso_origen_producto.py`. `ruff check .`: limpio.
- No verificado: orden y tipos reales de las columnas (todas se leen como texto; el SAS convierte con `input()`); anchuras de Nequi en archivos reales; sin pruebas propias de `fuentes_csv` y `esquema_csv` (solo las cubre `origen_producto`).
- Pendiente: validaciones, correcciones y salidas del producto (RESULTADO_<P>_NAL/EXT.csv, INCONS_DEP_<P>.csv), totales y conciliacion; lookups en tMap; documentar en `docs/plan-reescritura/` (no se actualizo en este hito).

## Hito 65. Reescritura, Fase 5: totales de origen del producto (conteo y suma de saldo), pruebas de fuentes CSV y simulador numérico

- Fecha: 2026-11-04
- Qué se hizo:
  - `tools/simular_productos.py` acepta `--saldo COLUMNA`. Esa columna se escribe como número (`100.50 * n`) y el resto sigue como texto `SIM_<columna>_<n>`.
  - `job_producto` convierte la columna de saldo (`FIN_SALDO_CTA`) a BigDecimal en un `tMap` y calcula `suma_saldo_origen` con `tAggregateRow`. El `tLogRow` imprime `registros_origen|suma_saldo_origen`.
  - Pruebas nuevas: `test_tools_simular_productos.py` (3), `test_proceso_fuentes_csv.py` (`fuentes_csv` y `esquema_csv` sobre un SAS sintético) y `test_talend_jobs_producto.py` (4).
- Resultado en Studio real (talend-mcp contra Studio 8.0.1): los cuatro Jobs `_t1` compilaron con `ok: true`. El padre exportado terminó con `Proceso terminado` y salida 0. Líneas de totales impresas, una por producto:
  ```
  3|603.00   (CTE, DBIFTCD.csv)
  3|603.00   (AHO, DBIFTCS.csv)
  3|603.00   (NEQUI, F_1019.csv)
  ```
  Los saldos simulados son 100.50, 201.00 y 301.50, que suman 603.00. La suma del Job coincide con esa cifra.
- Decisiones:
  - Ninguna nueva. `--saldo` es opción explícita del simulador; por defecto todas las columnas siguen como texto.
  - Sin cambios en `talend_item/jobs_producto.py` respecto al hito anterior: el Job compiló y ejecutó tal cual.
- Pruebas:
  - `uv run pytest -q`: 916 pasan, 1 se salta y 132 xfail.
  - `uv run ruff check .`: limpio.
- No verificado:
  - La suma usa `new java.math.BigDecimal(valor.trim())`. No reproduce la semántica exacta de `input(left(col), 20.)`: espacios internos, signos, decimales con coma y valores no numéricos no se probaron.
  - Solo se probaron saldos simulados con punto decimal. No se vieron saldos reales de FIN_SALDO_CTA ni se comparó la suma con un total real del SAS.
  - Los nombres de columna son los que el SAS demuestra. Las columnas que el SAS no nombra quedan como `VARn`.
- Pendiente: validaciones, correcciones, salidas y conciliación del producto, sin cambios en este hito.

## Hito 66. Reescritura, Fase 5: tMap con lookup, inner join y rechazo de union, validado ejecutando

- Fecha: 2026-11-04
- Que se hizo: `tmap.py` admite una entrada lookup con `expresiones_union` y `union_interna` (INNER JOIN), una salida `rechazo_union` (los que no casan), y modela `rechazo` y `filtro`. Los atributos salen del modelo EMF y del generador de codigo del mapper de Studio (clases `InputTable.innerJoin`, `OutputTable.reject` y `rejectInnerJoin`, `expressionFilter`; la clave de union es el atributo `expression` de la columna del lookup). `conexiones.lookup()` escribe la conexion de busqueda.
- Resultado en Studio real: tFixedFlowInput principal (ids 1 a 4, tipos CC, XX, NIT, YY) contra un lookup (CC, NIT): salio por `validos` 1|CC y 3|NIT, y por `rechazados` 2|XX y 4|YY; salida 0.
- Hallazgo: la conexion LOOKUP de un Job generado por el MCP usa `lineStyle` 0 (es una fila) y no compila; la correcta es `lineStyle` 8 (FLOW_REF).
- Pruebas: `test_talend_tmap_lookup.py` (12). `uv run pytest -q`: 928 pasan, 1 se salta, 132 xfail. `ruff check .`: limpio.
- No verificado en Studio: filtro (`expressionFilter`) y salida `rechazo` (catch output reject); lookup con varias columnas de union.
- Pendiente: usar el lookup en `job_producto` para la validacion de tipo de documento (INNER JOIN contra el Excel de homologacion, rechazo de los que no casan).

## Hito 67. Documentacion del estado y plan de tareas para el siguiente agente

- Fecha: 2026-11-04
- Que se hizo: `docs/plan-reescritura/tareas-agente.md` con el estado verificado (hitos 50 a 66), los hallazgos que cambian el diseno manual (CSV de producto, sin cache entre Jobs), el protocolo de validacion en Studio, los hechos de Studio ya aprendidos y 40 tareas ordenadas por bloque (herramientas, validaciones de producto, totales y conciliacion, joblets, contextos, documento de diseno, fidelidad del emisor, generalizacion, calidad), cada una con criterio de aceptacion y marca de quien puede hacerla.
- Estado: sin cambios de codigo. `uv run pytest -q`: 928 pasan, 1 se salta, 132 xfail. Un agente haiku que validaba el tipo de documento en `job_producto` fue detenido por el usuario antes de dejar cambios (arbol limpio); esa tarea queda como T10.

## Hito 68. Plan de corpus escalonado y equivalencia verificable

- Fecha: 2026-11-04
- Que se hizo: `docs/plan-reescritura/plan-corpus-y-equivalencia.md` (propuesta del usuario): programas SAS de dificultad creciente (niveles L0 a L9) con entradas simuladas, resultado esperado por oraculo ejecutable (SQLite para PROC SQL, vectores de semantica de funciones con fuente, dorados revisados) y el Job de Talend validado en Studio; hitos M1 a M5 y tareas K01 a K12. Docker esta instalado pero su motor esta apagado; los contenedores (PostgreSQL, Hive) quedan para cuando el usuario lo encienda. Excepcion a la regla 3 de AGENTS.md solo para pruebas locales de los Jobs generados.
- Estado: sin cambios de codigo.


## Hito 68b. Bloque 0 del plan de tareas: validador externo, poms y prueba de humo

- Fecha: 2026-11-04
- Que se hizo:
  - `tools/validar_en_studio.py`: convierte el protocolo de Studio (seccion 3 de
    `docs/plan-reescritura/tareas-agente.md`) en un comando. Emite con `sgm talend`, renombra los Jobs
    con sufijo nuevo (Studio cachea el modelo por identificador), parchea `env_nombre=DEV` y las rutas
    de insumos y de CSV de producto, copia al `process/` del proyecto, refresca el workspace, compila
    los hijos, luego el padre, exporta el Build Job y ejecuta el launcher con `--context`. Borra
    siempre los Jobs de prueba en un `finally`, aunque falle.
  - `tools/mcp_cliente.py`: cliente JSON-RPC minimo del MCP por `urllib` y descarga de los poms
    publicos que falten en la cache de Studio, hasta 8 rondas de exportacion (T02).
  - `tests/unit/test_talend_humo.py`: prueba de humo sin Studio (T04) sobre los cuatro Jobs emitidos:
    ninguna conexion con `ACTIVATE=false`, todo `tRunJob` apunta a un Job emitido, cada conexion
    referencia nodos existentes, `UNIQUE_NAME` unicos por Job, ningun `PASSWORD` en claro, toda
    variable `context.X` usada esta declarada y todo `.item` es XML bien formado.
- Hallazgos:
  - `UNIQUE_NAME` se repite fuera de los nodos: las conexiones y el `<subjob>` lo vuelven a declarar.
    La prueba debe contar solo `node/elementParameter[@name='UNIQUE_NAME']`.
  - `tFileInputExcel` se emite con `PASSWORD = "sgm_ref"`, el marcador que evita el fallo de
    compilacion. No es un secreto; la prueba de humo lo admite junto con vacio y `***`.
- Pruebas:
  - `uv run pytest -q`: 935 pasan (928 previas + 7 nuevas), 1 se salta,
    132 xfail.
  - `uv run ruff check .`: limpio.
  - `tools/validar_en_studio.py --dry-run` valida la ruta del proyecto y resume el plan.
- No verificado: la ejecucion completa del validador contra Studio real (emitir, compilar, exportar y
  ejecutar hasta reproducir `3|603.00`). Queda pendiente de una corrida con el servidor de talend-mcp
  arrancado con permiso de escritura y con los datos simulados.
- Pendiente: T10 (validacion de tipo de documento en `job_producto`), que es la siguiente tarea del
  plan y depende de este bloque.


## Hito 70. T10: validacion de tipo de documento con lookup en job_producto

- Fecha: 2026-11-04
- Que se hizo:
  - `decisiones/client_large.jobs.yaml`: seccion `validaciones_producto` con la validacion declarada
    (columna `TIPO_DOC`, columna del Excel `CNAME`, motivo `TIPO_DOC_INVALIDO`, fuente comun y
    excepcion de NEQUI con su propio Excel).
  - `arquitectura.py`: `ValidacionProducto` con `fuente_de(producto)`, y lectura de la seccion con
    error explicito si falta un campo.
  - `jobs_producto.py`: el Job ahora lee el archivo una vez y lo replica. Rama A: totales de origen
    (conteo y suma del saldo), como antes. Rama B: `tMap` con lookup al Excel de homologacion,
    `union_interna` (INNER JOIN) y salida `rechazos` por `rechazo_union`, igual que el SAS
    (`LEFT JOIN ... WHERE CNAME IS MISSING` para rechazos, `INNER JOIN` para validos). Los validos
    se totalizan (conteo y suma) y los rechazos se escriben en `doc_incorrectos_<sufijo>.csv` con la
    columna `motivo`.
  - `jobs_diseno.py`: la tabla de productos del padre lleva `arch_hom_tipo_doc` por producto (NEQUI
    usa su Excel) y el padre declara `ruta_resultados`.
  - `cli_talend.py`: resuelve el Excel de homologacion de cada producto desde el SAS y pasa la
    validacion al Job.
- Pruebas: `test_talend_jobs_producto.py` (5 nuevas: replica y separa, motivo y sufijo, contexto
  declarado, excepcion de NEQUI, lectura del YAML) y `test_talend_jobs_diseno.py` (tabla de
  productos con el Excel). `uv run pytest -q`: 1017 pasan, 1 se salta, 132 xfail.
- `ruff check` sobre los archivos tocados: limpio. La suite completa de `ruff` sigue en rojo por los
  archivos `tools/corpus*` que otra sesion tiene sin commitear; no son de este hito.
- No verificado en Studio: el lookup con el Excel real y la comparacion de texto contra texto. En el
  SAS `TIPO_DOC` es numerico (`input(left(VAR9), 8.)`), asi que `01` y `1` no casan igual; queda
  pendiente y hay que comprobarlo con los datos simulados (99 en TIPO_DOC para CTE/AHO y tambien 3
  para NEQUI).
- Pendiente: T11 (detectar el patron en lugar de declararlo), T12 a T19.


## Hito 71. T11: deteccion del patron de validacion por lookup en PROC SQL

- Fecha: 2026-11-04
- Que se hizo: nuevo `src/sgm/proceso/validaciones.py`. Reconoce la pareja del SAS
  (`CREATE TABLE ... AS SELECT` con `LEFT JOIN` al catalogo y `WHERE <catalogo>.<col> IS MISSING|NULL`
  para rechazos, y el mismo `ON` con `INNER JOIN` para validos) y devuelve
  `Validacion(columna, columna_lookup, fuente_lookup, linea, linea_valida)`.
  - Solo cuenta como validacion si el catalogo sale de un `PROC IMPORT`; un `LEFT JOIN` contra otro
    dataset de SAS es un cruce, no una homologacion. En `client_large.sas` hay ocho parejas
    `LEFT JOIN ... IS MISSING` y solo dos son de homologacion.
  - Tolera `ON` con parentesis, alias con y sin `AS`, `ON` invertido, `IS MISSING` e `IS NULL`, y
    name literals (`h.'codigo dian'n`).
  - `ruta_de_dataset(texto, dataset)` une el dataset del catalogo con la ruta de su `PROC IMPORT`,
    que es lo que despues alimenta `InsumoResuelto`.
- Pruebas: `tests/unit/test_validaciones_sas.py`, 9 pruebas; incluye el programa real (dos
  validaciones `TIPO_DOC` contra `CNAME` de `IMPORT_HOMOLOGACION_TPO_DOC`, las dos con pareja
  `INNER JOIN`) y las rutas de `Homologacion_tpo_dto.xlsx` y `Homologacion_tpo_dto_Nequi.xlsx`.
- `ruff check` de los dos archivos: limpio.
- Pendiente: T12 y siguientes, que consumen el detector; catalogo de pais y DANE importados pero sin
  patron de validacion en el SAS (sus datasets solo se usan en cruces de enriquecimiento).

## Hito 69c. Corpus: ejecutor, oraculo SQL, vectores de semantica y casos L0 y L1

- Fecha: 2026-11-04
- Que se hizo: (a) `tools/corpus.py` con `oraculo` e `informe` y `tools/corpus_lib/` (formato de caso `tests/corpus/<nivel>/<caso>/`); (b) oraculo capa A: `PROC SQL` ejecutado en SQLite con una tabla de diferencias de dialecto (`tools/corpus_lib/DIFERENCIAS.md`); lo no soportado falla con `NoSoportado`, nunca se traduce mal en silencio; (c) 69 vectores de semantica de funciones SAS con fuente (52 documentados, 15 deducidos, 2 inciertos) y su implementacion de referencia (`tools/corpus_semantica*.py`); (d) 30 casos: L0 (15, esperado escrito a mano con razonamiento, estado `pendiente_revision`) y L1 (15, capa A verificada).
- Hallazgos de semantica: COMPRESS sin modificadores quita blancos; SUBSTR sobre un numero lo toma alineado a la derecha; SCAN trata delimitadores consecutivos como uno; ROUND redondea empates alejandose de cero; un faltante numerico es menor que cualquier numero; el texto se compara con relleno de blancos. Con `w.d` los ultimos `d` digitos son decimales: `0023` con `6.2` da `0.23`.
- Riesgos de dialecto declarados: celda vacia igual a faltante; LIKE sensible a mayusculas; fechas ISO como texto en `PROC IMPORT`; orden de faltantes en `ORDER BY`; expresion sin alias (`_TEMA001`); blancos finales en `||`; comparaciones con faltantes en `WHERE` sin cubrir.
- Pruebas: `test_corpus_ejecutor.py`, `test_corpus_oraculo_sql.py`, `test_corpus_semantica.py` (133). `tools/corpus.py oraculo todos --verificar`: 30 casos, 0 fallas.
- No verificado: ningun resultado contra un SAS real (no hay). Los 15 casos L0 necesitan revision de un segundo agente.


## Hito 72. T12 (deteccion): validaciones de ubicacion, pais y DANE

- Fecha: 2026-11-04
- Hallazgo: el SAS si valida pais y DANE, pero no con la pareja limpia de T10. La consulta
  `INCONS_UBICACION_INVALIDA_AHO` (linea 18042) cruza `SABANA_CORR_NOM_AHO` con
  `IMPORT_CODIGOS_DANE` y `IMPORT_CODIGOS_PAIS` y rechaza con un `WHERE` compuesto de cinco
  condiciones (DANE faltante con pais 169, combinacion incoherente, pais faltante, direccion corta o
  con textos prohibidos). No hay `INNER JOIN` de validos y el motivo del SAS es uno solo,
  `CAMPOS DE UBICACION INCORRECTOS`.
- Que se hizo: el detector reconoce esas seis consultas (AHO, CTE y NEQUI). Se corrigio el
  emparejamiento para que compare la tabla de la sabana y no el alias: AHO y CTE usan ambos `t1` y
  antes CTE heredaba el `INNER JOIN` de AHO. `Validacion` ahora lleva `sabana`, sin alias.
- Pruebas: `test_detecta_las_validaciones_de_ubicacion` y
  `test_cada_producto_empareja_su_propio_inner_join` (AHO con 3456 y CTE con 5972).
- Bloqueo de T12 (parte de Job): traducir el `WHERE` compuesto exige filtrar filas dentro del `tMap`
  o con `tFilterRow`, y ninguna de las dos se ha ejecutado nunca en Studio. Es el riesgo que abre
  T13, asi que generar los `tMap` con lookup de pais y DANE queda detras de T13. Los motivos
  separados `PAIS_INVALIDO` y `DANE_INVALIDO` son una decision de diseno: el SAS usa uno solo.
- Pendiente: T12 (Job), T13 a T20.


## Hito 73. T20: presupuesto de componentes por Job

- Fecha: 2026-11-04
- Medido sobre `job_producto` real (no estimado): sin validacion, 6 componentes
  (`tJava`, `tFileInputDelimited`, `tReplicate`, `tMap`, `tAggregateRow`, `tLogRow`). Con la
  validacion de tipo de documento de T10, 11: se suman `tFileInputExcel`, un segundo `tMap`, un
  segundo `tAggregateRow`, `tFileOutputDelimited` de rechazos y un `tLogRow`.
- Queda por debajo del limite de 20 del diseno manual. Margen: 9 componentes.
- Decision: no se mueve nada a joblets todavia. Cada validacion nueva de T12 a T19 cuesta entre 2 y
  4 componentes (lookup, tMap y salida), asi que con dos validaciones mas el Job llega al limite. La
  regla que se deja escrita: cuando el Job pase de 20, cada rama de validacion se va a un Job hijo
  `job_validacion_<tema>` por producto, no a un joblet, porque el joblet comparte contexto y hace mas
  dificil probar la rama por separado.
- Pendiente: T12 (Job), T13 a T19, y el bloque B.

## Estado del backlog al cerrar la sesion

- Hechos: T01, T02, T04 (hito 69), T10 (hito 70), T11 (hito 71), T12 en su parte de deteccion
  (hito 72), T20 (hito 73).
- Bloqueado con motivo: T12 (Job) y T13 dependen de ejecutar en Studio el filtro del `tMap` o
  `tFilterRow`; no hay Studio disponible en esta sesion (el dialogo "Network Issue" bloquea
  `talend_job_verify`) y el repo prohibe suponer el comportamiento sin medirlo. T15 (`tUniqRow`) y
  T16 (compilacion Java con el JDK de Studio) arrastran el mismo bloqueo.
- Abierto: T14, T17 a T19 y los bloques B, C y D (T30 a T94) no se han tocado.
- Nota de convivencia: otra sesion trabaja en el mismo repositorio (`tools/corpus*`, `tests/corpus/`).
  Mientras corre, `uv run pytest -q` puede fallar leyendo un YAML a medio escribir
  (`test_corpus_validaciones.py`); en aislamiento ese archivo pasa. `ruff check .` sigue en rojo por
  esos mismos archivos ajenos: los mios estan limpios.

## Hito 70c. Corpus: 16 casos L8 con anomalias plantadas y revision independiente de L0

- Fecha: 2026-11-04
- Que se hizo: (a) `tests/corpus/L8/validaciones/` (8 casos) y `tests/corpus/L8/totales/` (8 casos): programas SAS de 215 a 300 lineas en el estilo del original (etiquetas, `PROC IMPORT DBMS=DLM`, conversiones `input(left())`, consultas de SAS Studio, macros por producto, `PROC EXPORT`), con CSV de producto de 23 columnas y Excel simulados, generados por `tools/corpus_datos/validaciones.py` y `totales.py` con semilla fija. Cada `caso.yaml` lleva `anomalias_plantadas`: el conteo exacto de registros anomalos que el generador puso (por ejemplo tipo de documento invalido: CTE 7 y AHO 5), que es un oraculo independiente de cualquier traductor. (b) Revision independiente de los 15 casos L0 por un segundo agente que calculo a mano antes de ver el esperado: 13 coinciden (`revisado`), 2 ambiguos por el tipo que `PROC IMPORT` da a una fecha ISO (`tests/corpus/L0/REVISION.md`). (c) `tools/corpus_lib/caso.py` acepta los estados `revisado` y `sin_esperado` y los campos de metadatos de los casos.
- Hallazgos del frontend de sgm (`tests/corpus/HUECOS_FRONTEND*.md`): `PROC DOWNLOAD` dentro de `RSUBMIT` queda sin lectura ni escritura y se pierde la ruta de red; `%IF` dentro de una macro con parametro no se sigue en 3 programas (05 linea 160, 06 linea 118, 07 linea 108). Son huecos reales del analizador, no del corpus.
- Pruebas: `test_corpus_validaciones.py` (5), `test_corpus_totales.py` (12) y las de los hitos anteriores; `tools/corpus.py oraculo todos --verificar`: 30 casos, 0 fallas.
- No verificado: ningun resultado contra SAS real. Dudas de sintaxis y semantica anotadas por caso: UPCASE, STRIP y COMPBL con Ñ y tildes segun la codificacion de sesion, opciones de EXCELCS copiadas del original, `input(left(''), n.)` como faltante.
- Pendiente: generar el esperado de los casos L8 (hoy `sin_esperado`) con el oraculo y las anomalias plantadas, arreglar los huecos del frontend, y traducir estos casos a Jobs de Talend.


## Hito 74. T14 (reglas): tipo de cuenta, Codex y GMF invalidos

- Fecha: 2026-11-04
- Hallazgo: el SAS no usa listas `IN (...)`. Rechaza con `NOT BETWEEN` sobre una columna y una
  columna de control: `( TIPO_CTA NOT BETWEEN 1 AND 5 ) AND ( RELACION = 1000 )` con motivo
  `TIPO CTA INVALIDO`, y `( GMF NOT BETWEEN 1 AND 10 ) AND ( RELACION = 1000 )` con motivo
  `CODEX INVALIDO` (la etiqueta dice Codex pero filtra GMF). NEQUI usa el mismo par sin `RELACION` y
  con motivos propios: `TIPO DE CUENTA INVALIDO` y `GMF INVALIDO`. El motivo sale del paso `DATA`
  que etiqueta la tabla de rechazos, no se inventa.
- Que se hizo: nuevo `src/sgm/proceso/reglas.py`. Devuelve `ReglaRango(destino, columna, desde,
  hasta, permite, motivo, linea, control)` y una `condicion` en Java con el rango agrupado antes del
  control. Detecta ademas las reglas de longitud de documento por tipo (`NRO_DOC BETWEEN ...` por
  `TIPO_DOC`), que son de T19/T15.
- Pruebas: `tests/unit/test_reglas_rango.py`, 6 pruebas: rango negado con control y motivo, rango
  permitido, agrupacion de la condicion y las cuatro reglas reales de AHO, CTE y NEQUI.
- Bloqueo de T14 (parte de Job): aplicar la regla como filtro de fila necesita `tFilterRow` o el
  filtro del `tMap`, que siguen sin ejecutarse nunca en Studio. Mismo bloqueo que T12 (Job) y T13.
- Pendiente: T12/T13/T14 en su parte de Job, T15 a T19.


## Hito 75. T11 (cierre): el YAML confirma, no declara

- Fecha: 2026-11-04
- Que se hizo: `sgm talend` contrasta las validaciones del YAML con las que el SAS demuestra, en las
  dos direcciones. Si el YAML declara una validacion que el SAS no tiene, avisa; si el SAS tiene una
  que nadie declaro, tambien, con su linea. Se imprime como `Pendiente: ...` junto a los demas.
- Efecto: con `client_large.sas` salen avisos por las validaciones de ubicacion (`CODIGO_UBICACION`
  contra `CODIGO_DANE` y `PAIS` contra `Codigo_Pais`), que estan en el SAS y no en el YAML. Es
  exactamente la deuda que abre T12; deja de ser invisible.
- Pruebas: dos nuevas en `tests/unit/test_validaciones_sas.py`; 27 pasan en los archivos tocados.
- Pendiente: declarar esas validaciones en el YAML cuando T12 cierre la parte de Job.


## Hito 76. T03: emulador de las tablas Impala

- Fecha: 2026-11-04
- Que se hizo: nuevo `tools/simular_tablas.py`. Lee los bloques `connect to IMPALA ... select * from
  connection to IMPALA (...)` del programa, saca la tabla de cada `FROM` con biblioteca y las columnas
  que la consulta referencia (calificadas por alias o por tabla, y sin calificar aunque vayan dentro
  de una funcion como `MAX(ingestion_day)`) y escribe `<carpeta>/<biblioteca>.<tabla>.csv` con
  cabecera y filas `SIM_<col>_<n>`.
- Convencion de simulacion: deja `<carpeta>/CONVENCION.md`. Los Jobs que lean Impala usan
  `tImpalaInput` en produccion y, con el contexto `modo_simulacion` no vacio, `tFileInputDelimited`
  sobre el CSV con `;` y cabecera. Asi el Job compila siempre y se ejecuta sin Impala.
- Sobre `client_large.sas` escribe 20 tablas, entre ellas
  `resultados_vspc_clientes.master_customer_data` (`ingestion_day`, `YEAR`, `MONTH`, ...),
  `S_CANALES.SAI_SCILIBRAMD_SCIFFIMGFR` (`ingestion_day`, `ingestion_month`, `ingestion_year`) y las
  `proceso_vspc_finanzas.*` que el programa lee en pasos posteriores. Queda fuera
  `proceso_vspc_finanzas.mcdq` como lectura: el programa la crea con `EXECUTE BY IMPALA`.
- Pruebas: `tests/unit/test_tools_simular_tablas.py`, 4 pruebas (un CSV por tabla con sus columnas,
  convencion escrita y programa sin Impala).
- Corregidos de paso dos fallos del propio emulador: comparaba objetos con `is` (nunca sumaba las
  columnas sin calificar) y trataba marcadores de macro sin biblioteca como tablas Impala.
- Pendiente: los Jobs aun no leen Impala; la convencion queda escrita para el bloque B.

## Hito 71c. Corpus: casos L2 y L3 (joins, validacion con lookup, agregados) con invariantes

- Fecha: 2026-11-04
- Que se hizo: 27 casos en `tests/corpus/L2/` (15) y `tests/corpus/L3/` (12), capa A, todos `traducible`, con el patron de validacion del original (`LEFT JOIN ... ON (t.TIPO_DOC = h.CNAME) WHERE h.CNAME IS MISSING` para invalidos y `INNER JOIN` para validos), joins por varias columnas, `IN` y `NOT IN` con subconsulta, `CASE`, `COALESCE`, `COUNT(DISTINCT)`, `GROUP BY` y `HAVING`, totales de origen y de salida, y conciliacion con una diferencia plantada. Mecanismo de `preparacion` para casos que mezclan un DATA step (`input(left())`) con `PROC SQL`: el DATA step se calcula con la referencia de semantica de `tools/corpus_semantica_funciones.py`, se guarda en `entradas_preparadas/` y el oraculo falla si ese archivo no coincide. Campo `invariantes` en `caso.yaml` (por ejemplo `filas(validos) + filas(invalidos) == filas(origen)`) evaluado por `tools/corpus_lib/invariantes.py`; las diferencias plantadas (`l2_05`, `l3_09`) las declara.
- Verificacion independiente sin el corpus: suma de `l3_08` = 21745.34 con 10 saldos presentes; `l2_04` = 9 validos y 3 invalidos; `l3_09` = 2 operaciones CC y diferencia de conciliacion -2. Coinciden con el oraculo.
- Pruebas: `test_corpus_invariantes.py` (40), `test_corpus_preparacion.py`, y 5 nuevas en `test_corpus_oraculo_sql.py`. `tools/corpus.py oraculo todos --verificar`: 57 casos, 0 fallas.
- Riesgos de dialecto sin SAS real (altos, no verificados): comparaciones `<`, `<=`, `<>` con faltantes (SAS trata el faltante como menor, SQLite da NULL; los casos lo evitan), blancos finales en claves de texto (SAS los ignora, SQLite no), `NOT IN` con NULL en la subconsulta y el orden de NULL en `ORDER BY`/`GROUP BY`.
- Pendiente: generar el esperado de los casos L8; casos L4 a L7 (funciones, macros, `MERGE`, `FIRST.`/`LAST.`).


## Hito 77. T19 (salidas): tablas finales, exportaciones y conciliacion

- Fecha: 2026-11-04
- Que se hizo: nuevo `src/sgm/proceso/salidas.py`.
  - `tablas_finales(texto)`: tablas `SABANA_FINAL_<P>`, `RESULTADO_<P>_NAL|EXT`, `INCONS_DEP_<P>` e
    `INCONS_DEP_CORREGIDA_<P>` con sus columnas en el orden del `SELECT` y la tabla con la que se
    cruzan. Una tabla con `SELECT * ... OUTER UNION CORR` (varias de inconsistencias) se devuelve sin
    columnas: es un esquema pendiente, no se supone.
  - `exportaciones(texto)`: los `PROC EXPORT` con dataset, archivo, delimitador (que en el SAS va en
    una sentencia aparte, `delimiter=';';`) y `replace`.
  - `formula_conciliacion(texto)`.
- Hallazgo del criterio nacional/extranjero: no depende de `TIPO_DOC` sino del cruce.
  `RESULTADO_<P>_NAL` se arma con `SABANA_TIT_NAL_<P>` y `RESULTADO_<P>_EXT` con
  `SABANA_TIT_EXT_<P>`. Queda demostrado por `fuente` en cada tabla.
- Salidas reales: 22 `PROC EXPORT`, todas con `dbms=dlm`, `delimiter=';'` y `replace`, a
  `/work_sasstudio/pcfiles/`. Incluyen `RESULTADO_AHO_NAL.csv`, `RESULTADO_AHO_EXT.csv`,
  `INCONS_DEP_AHORROS.csv` y las de inconsistencias corregidas.
- Conciliacion: `CONCILIACION_SALDOS=SUMA_SALDO_INICIAL-(SUMA_SALDO_FINAL_DEP_AHO+
  SUMA_SALDO_INCONS_DEP_AHO)`.
- Pruebas: `tests/unit/test_salidas_producto.py`, 8 pruebas; incluye el programa real (19 columnas
  de la sabana final, 28 de la nacional con su fuente, 22 exportaciones con `;` y la formula).
- Pendiente de T19 (parte de Job): escribir los archivos con esas columnas requiere las etapas de
  validacion previas (T12 a T18), que siguen detras del filtro de Studio. La invariante
  validos + rechazos = origen se podra comprobar cuando esten completas.

## Hito 72c. Contenedores de prueba: Impala 4.5.3 real y PostgreSQL, con Jobs de Talend ejecutados contra ellos

- Fecha: 2026-11-04
- Que se hizo: `tools/contenedores/impala/` (docker-compose, `arrancar.sh`/`.ps1`, `parar.sh`, README): Impala 4.5.3 REAL con las imagenes locales (HMS, statestored, catalogd, impalad), HiveServer2 en `localhost:21050` sin SASL, topes de memoria que suman 4,75 GiB (en reposo: impalad 347 MiB, catalogd 275 MiB, HMS 260 MiB, statestored 15 MiB). `cargar_tablas.py` crea las tres tablas Impala que el programa grande lee (`resultados_vspc_clientes.master_customer_data`, `s_canales.sai_scilibramd_sciffimgfr`, `proceso_vspc_finanzas.mcdq`) con las columnas que el SAS usa y 3 filas ficticias. `tools/contenedores/postgres/`: compose y datos de ejemplo. Todo con prefijo `sgmtest_`.
- Resultado en Studio real: un Job `tImpalaConnection` a `tImpalaInput` (`select count(*)`) a `tLogRow` imprimio `2` contra el Impala del contenedor; un Job `tPostgresqlInput` a `tLogRow` imprimio las 3 filas de la tabla de PostgreSQL.
- Hallazgos: con `IMPALA_ADDITIONAL_JDBC=";auth=noSasl"` la conexion funciona (sin eso el cliente inicia SASL y se cuelga); `PASS` vacio o `""` hace que Studio genere `if ( != null && false)` y no compile, hace falta un valor (la rama LDAP no se ejecuta); el HMS necesita IP fija y `extra_hosts` porque el DNS inverso devuelve un nombre con guion bajo que Hive rechaza; el volumen nuevo del warehouse es de root y hay que darle permisos.
- Excepcion a `AGENTS.md` regla 3: los contenedores locales solo se usan para probar los Jobs generados, autorizado por el usuario; `sgm` nunca se conecta a una base.
- Pruebas: `test_contenedores.py` (13, sin Docker: compose validos, prefijo `sgmtest_`, sin secretos, SQL de `cargar_tablas.py`).
- No verificado: el codigo de salida del Job de Impala (PowerShell no lo capturo); escritura con `tPostgresqlOutput` (el generador de Studio falla con un nodo escrito offline: `dbType` nulo); plantilla de `tPostgresqlConnection`. La plantilla `tPostgresqlInput` quedo en `tools/contenedores/talend_plantillas/` y falta moverla a `src/sgm/talend_item/plantillas/`.

## Hito 73c. Corpus: casos L4 a L6 (funciones, macros, MERGE y FIRST./LAST.) con referencia de semantica

- Fecha: 2026-11-04
- Nota de numeracion (resuelta en el hito 80, R0-01): esta serie y las entradas 69c a 77c del corpus y los contenedores llevaban el mismo numero que la serie de `tareas-agente.md`. Ahora toda entrada del corpus y de los contenedores lleva la letra de serie `c` y la regla esta en `AGENTS.md`.
- Que se hizo: 44 casos: L4 (20, funciones de DATA step con vectores de `semantica/vectores.yaml`: `input`, `left`, `compress`, `strip`, `upcase`, `lowcase`, `substr`, `substrn`, `scan`, `trim`, `coalescec`, `round`, comparaciones con faltantes), L5 (12, macros: `%let`, `%macro` con parametros, `%if`/`%do`, `&var`, `%eval`, `%str`, `%sysfunc`, `SELECT INTO :var`, macrovariables en nombres de tabla y ruta), L6 (12, `MERGE ... BY` con `IN=`, `FIRST.`, `LAST.`, `RETAIN`, `PROC SORT NODUPKEY` y `NODUP`). Un expansor minimo de macros (`tools/corpus_lib/expansor_macros.py`) deja `programa_expandido.sas` y el esperado se calcula sobre el expandido; la referencia de `MERGE`, `FIRST.`/`LAST.`, `RETAIN` y `NODUPKEY` esta en `tools/corpus_lib/referencia_datastep.py` con la documentacion citada.
- Hallazgos que contradicen lo asumido en L0 a L3 (`DIFERENCIAS.md`): (1) `MERGE` de un DATA step con llaves repetidas en ambos lados NO multiplica filas como un JOIN de SQL: por grupo sale el maximo de filas de los conjuntos y el conjunto mas corto retiene su ultima observacion (ejemplo KB 24752). Un programa que use `MERGE` no es equivalente a un `JOIN`. (2) En un DATA step, `IF saldo < 500` es verdadero cuando el saldo es faltante; en SQLite la comparacion da NULL: el oraculo SQL difiere y la brecha sigue abierta. (3) El mecanismo `preparacion` corta la cadena en el primer faltante, asi que `coalesce` tras `input` no se expresa, y `catx` pide varias columnas.
- Capa: L4 y L6 son capa B (referencia de Python), no un oraculo independiente; su esperado se verifica por regeneracion byte a byte, invariantes y la presencia de las asignaciones en el SAS. La unica comparacion externa es el ejemplo de la documentacion (l6_02).
- Estado: 101 casos con 0 fallas en `tools/corpus.py oraculo todos --verificar` (L4 20: 19 traducibles y 1 pendiente por PUT y fechas sin vector; L6 5 en `pendiente_revision`).
- Sin fuente oficial consultada: `RETAIN`, la sentencia suma, `NODUP`, que fila conserva `NODUPKEY` (la documentacion no lo define) y que las macros no se resuelvan entre comilla simple.
- Pruebas: `test_corpus_l4l6.py` (126 pasan, 25 se saltan por diseno).

## Hito 74c. Corpus: esperado por construccion de los 8 casos L8 de validaciones

- Fecha: 2026-11-04
- Que se hizo: `tools/corpus_datos/validaciones_*.py` calcula 124 salidas esperadas (tablas WORK y archivos de `PROC EXPORT`) desde la etiqueta de anomalia que el generador planto en cada fila, sin pasar por SQL: es un oraculo independiente del traductor. `validaciones_cruce.py` contrasta esas salidas con el oraculo SQL (puente SAS a SQLite): 105 coinciden sin diferencias y 19 no se pudieron verificar porque el oraculo no traduce `LENGTH`, `COMPBL` ni `CONTAINS`. Resultado por caso: v01 12/12, v02 15/15, v04 16/16, v05 19/19, v07 22/22 (con un supuesto sobre GMF), v08 12/12, v03 7/15 y v06 2/13.
- Estado: ningun caso llega a `traducible`: seis quedan `pendiente_revision` y dos `parcial`, porque el tipo que `PROC IMPORT` da a `NRO_DOC` y a las columnas con blancos, y los formatos de `PROC EXPORT` (`3.`, `20.`, `30.`) y el orden sin `ORDER BY` no se pueden demostrar sin SAS. Cada caso lo anota en `observacion_revision`.
- Hallazgos en los programas del propio corpus (errores del autor, no del original): en v02, `SUMA_SALDO_CTE_VALIDAS` suma `FIN_SALDO_CTA` desde una tabla que no trae esa columna (en SAS daria faltante); en v07, `PASO1` usa `SABANA.GMF`, que no existe (solo `GMF_TXT`), y el `PROC SQL` fallaria en SAS. Hay que corregir esos dos programas.
- Limites: `tools/corpus.py oraculo todos --verificar` no cubre los casos de `tests/corpus/L8/` porque `niveles()` solo lista carpetas `L<n>` y `caso.py` exige que el nivel coincida con la carpeta padre; los cubre la prueba de cruce. Las entradas plantan una sola anomalia por fila, asi que la precedencia entre reglas secuenciales (v07, v08) y la del `CASE` (v03) no queda probada.
- Pruebas: `test_corpus_validaciones.py` (39).

## Hito 75c. Corpus: esperado por construccion de los 8 casos L8 de totales y hallazgos del oraculo

- Fecha: 2026-11-04
- Que se hizo: 62 CSV esperados en `tests/corpus/L8/totales/*/esperado/` calculados desde la verdad plantada (`tools/corpus_datos/totales_esperado*.py`) y cruzados con el oraculo SQL (`totales_cruce*.py`). Por caso: 01 `parcial` (capa C, `NODUPKEY`/`NODUPREC` no los ejecuta SQL; cruce 0 diferencias), 02 `pendiente_revision` (0 diferencias con `UNION ALL` por `OUTER UNION CORR`), 03 `pendiente_revision` (1 diferencia), 04 `traducible` (capa A, 0 diferencias), 05 `parcial` (0), 06 `pendiente_revision` (0), 07 `parcial` (Impala emulado sobre CSV, 0), 08 `pendiente_revision` (12 diferencias en cascada por la causa de 03).
- Hallazgo principal del oraculo: ninguna convencion de faltantes sirve a SAS completo. Si el texto en blanco se lee como NULL, `NRO_CTA = ''` no cuenta las filas vacias (casos 03 y 08 difieren); si se lee como cadena vacia, `IS MISSING` tras un `LEFT JOIN` falla (caso 02). En SAS un texto en blanco ES faltante y tambien es igual a `''`. Salida correcta pendiente: guardar el texto vacio como `''` en columnas TEXT y traducir `IS MISSING` segun el tipo de la columna (texto: `col IS NULL OR col = ''`; numerica: `col IS NULL`).
- Otros fallos del oraculo hallados: `ROUND(x, 0.01)` se traduce a `round(x, 0.01)` de SQLite (da 12.0 para 12.345; SAS da 12.35; el equivalente es `round(x/0.01)*0.01`); faltan `NE`, `OUTER UNION CORR`, `OBS=` e `INTO`; `caso.py` rechaza las claves `id`, `productos` y `supuestos`; `oraculo todos` no ve `tests/corpus/L8/` (carpeta anidada), por eso el cruce es un script.
- Hallazgo del programa 08: `DIF_SIN_DUPLICADOS_EXACTOS` da 1 y no 2 duplicados; el esperado sigue la formula del programa.
- Correcciones del propio generador al cruzar: el caso 02 tiene 56 filas y no 55 (la fila con `NRO_CTA` vacio vuelve a la sabana); en el 05, `CONCILIA` exige tambien `DIF_FILAS = 0`, como el `CASE` de SAS; en el 06 el nombre es `FORMATO_TEXTO_FECHA`.
- Pruebas: `test_corpus_totales.py` y `test_corpus_totales_cruce.py` (71 pasan, 4 xfail estrictos documentados: 03 y 08 por la convencion de vacio, 02 con cadena vacia, ROUND).
- Pendiente: arreglar las convenciones de faltantes y `ROUND` en el oraculo; corregir los programas v02 y v07 de validaciones; unificar `oraculo todos` con los casos L8.

## Hito 76c. Corpus: correccion de los programas v02 y v07 de validaciones

- Fecha: 2026-11-04
- Que se hizo: v02 ahora trae `FIN_SALDO_CTA` en la tabla de documentos validos de CTE y AHO, de modo que `SUMA_SALDO_CTE_VALIDAS` suma una columna que existe (1024505 en lugar de faltante); v07 convierte `GMF=input(left(GMF_TXT), 3.)` en el DATA step previo y borra `GMF_TXT`, como el original. Se recorrio cada `CREATE TABLE` y `DATA` de ambos buscando otras columnas o tablas inexistentes: no hay mas. Salidas esperadas que cambiaron: 3 en v02; 0 en v07 (el esperado ya suponia la conversion).
- Cruce con el oraculo SQL: 105 salidas coinciden sin diferencias; v02 15/15 y v07 22/22 ya sin el supuesto sobre GMF (se quito `SUPUESTOS`).
- Pruebas: `test_corpus_validaciones.py` (41; 2 nuevas: la tabla de validos de v02 trae `FIN_SALDO_CTA` y la suma no es faltante; v07 convierte GMF antes de `PASO1`).
- Sigue sin demostrarse con SAS el orden de columnas cuando `format` va antes de `set` (NRO_DOC y GMF al final): supuesto anotado en los casos.

## Hito 77c. Corpus: oraculo SQL con la semantica de faltantes de SAS, ROUND y carga unificada de L8

- Fecha: 2026-11-04
- Que se hizo: (a) Faltantes de texto: el vacio de una columna de texto se guarda como `''` y el de una numerica como `NULL`; las tablas llevan `COLLATE RTRIM`, asi que `=`, `<>`, `IN`, `JOIN`, `ORDER BY` y `GROUP BY` ignoran los blancos finales como SAS; `IS [NOT] MISSING` se traduce por tipo (texto: `(col IS NULL OR rtrim(col) = '')`; numerico: `col IS NULL`); `COUNT(col)` y `COALESCE` llevan `NULLIF(arg,'')`. (b) `ROUND(x, u)` redondea al multiplo `u` con empates alejandose de cero: `ROUND(12.345, 0.01)` da 12.35 y los vectores `round-01` a `round-06` pasan. (c) Nuevos: `NE`, `OUTER UNION CORR` de N `SELECT`, `OBS=n`; `SELECT ... INTO` queda `NoSoportado` con mensaje claro. (d) El cargador acepta casos anidados `L8/<grupo>/<caso>` y guarda los metadatos en `Caso.extra`.
- Resultado: `tools/corpus.py oraculo todos --verificar`: 117 casos, 0 fallas (101 de L1 a L6 mas 16 de L8; de L8, 9 son capa A y se cargan pero el oraculo los omite con motivo: entradas `;` sin cabecera, `PROC IMPORT`, DATA step; 7 son capa C). Cruces: L8/totales 01 a 08 con 0 diferencias (antes 03 tenia 1 y 08 tenia 12); L8/validaciones 105 salidas sin diferencias y 19 sin verificar por `LENGTH`, `COMPBL` y `CONTAINS`. Se quitaron los xfail estrictos que esto resolvia.
- Riesgos abiertos (sin SAS real): las expresiones no llevan collation RTRIM; `IS MISSING` sobre una expresion es `NoSoportado`; `ROUND` depende de una tolerancia de 1e-10 (el "fuzz" de SAS no esta verificado) y `u = 0` no se verifico; `OUTER UNION CORR` no verifica el orden de columnas; `OBS=` usa el orden de insercion; un `JOIN` de textos vacios ahora empareja como en SAS (vector deducido); `GROUP BY` y `DISTINCT` agrupan `'CC'` con `'CC '` por supuesto.
- Pruebas: `test_corpus_oraculo_faltantes.py` y las del oraculo y los cruces actualizadas. `uv run pytest -q`: 1501 pasan, 26 se saltan, 132 xfail. `ruff check .`: limpio.
- Pendiente: la `observacion_revision` de L8/totales 03 y 08 describe la convencion vieja (vacio como NULL) y quedo obsoleta.

## Hito 79. Corpus: arnes `tools/corpus_studio.py` para ejecutar un Job de Talend contra un caso y comparar con el esperado

- Fecha: 2026-11-04
- Que se hizo: `tools/corpus_studio.py` con `validar` y `comparar`. `validar <caso> --jobs <carpeta> --padre <job> --proyecto <ruta> [--mapa mapa.yaml] [--contexto k=v]` copia las entradas del caso a una carpeta de trabajo, apunta las variables de contexto del Job a ellas con `--context_param`, emite con sufijo de nombre nuevo, compila hijos y luego padre, exporta, ejecuta el lanzador, borra los Jobs de prueba aunque falle y compara cada archivo escrito con `esperado/`. `comparar <caso> --salida <carpeta>` compara sin Studio. El comparador (`tools/corpus_lib/studio_comparar.py`, `studio_filas.py`) revisa columnas (nombre y orden), filas (como conjunto salvo `orden_relevante`), numeros con la `tolerancia` del caso, texto sin blancos finales y vacio igual a vacio, y reporta la celda exacta. Uso documentado en `tools/corpus_lib/STUDIO.md`.
- Demostracion en Studio real (caso `l2_01_inner_join_clientes_ventas`, Job escrito a mano: `tFileInputDelimited`, `tMap` con lookup `INNER JOIN`, `tFileOutputDelimited`): `1 casos, 1 coinciden`, 10 filas esperadas escritas; no quedo ningun Job de prueba en `process/`. La misma salida alterada (monto 655 a 656) da `fila 1, columna 'monto': esperado '655', obtenido '656'` con codigo de salida 1.
- Problemas hallados en `tools/validar_en_studio.py` (de la otra sesion, no modificado): `exportar` busca `<job>_run.bat` solo en el destino y el servidor lo deja en `destino/<job>/`; `renombrar` exige la version 0.1; `ejecutar` no entrecomilla los parametros (rechaza espacios); las carpetas `build-*` quedan en `%TEMP%`. El arnes usa su propia `_exportar` recursiva.
- Pruebas: `test_corpus_studio.py` (28). `uv run pytest -q`: 1529 pasan, 26 se saltan, 132 xfail. `ruff check .`: limpio.
- No verificado: fallo de compilacion en Studio real (solo con un doble del cliente), Jobs con hijos (`tRunJob`), casos con varias salidas, tolerancia numerica y `orden_relevante` en Studio real.

## Hito 80. Plan ruta a produccion: Fase 0 completa, herramientas y linea base (G0)

- Fecha: 2026-11-04
- Que se hizo: se implementa la Fase 0 (R0-01 a R0-12) de `docs/plan-reescritura/ruta-a-produccion.md`,
  que es la puerta G0 y el requisito de las demas fases. Lo que necesita Studio, Docker o el entorno
  del banco queda entregado como codigo y documento, y se dice abajo que no se pudo ejecutar.
- R0-01 (numeracion): `PROGRESS.md` tenia siete numeros repetidos (28, 44, 45, 68, 70, 71 y 72). Las
  segundas entradas toman letra de serie: 28b, 44b, 45b, 68b, 70c, 71c y 72c, como ya hacian 73c a
  77c. Queda una regla en `AGENTS.md` (seccion "Numeracion de hitos"): numero unico, una entrada
  publicada no se renumera y cada serie de una sesion paralela lleva letra. 84 entradas, sin repetir.
- R0-02 (`tools/validar_en_studio.py`): cuatro correcciones con su prueba. `exportar` busca el
  lanzador con `rglob` en todo el destino (el servidor lo deja en `<destino>/<job>/`); `renombrar`
  lee la version del nombre del archivo en vez de exigir 0.1 y recalcula los ids del `.properties`
  con esa version (`versiones()`); `ejecutar` arma el comando con `comando_lanzador()`, que
  entrecomilla lanzador, contexto y cada `--context_param`; y la carpeta `build-*` se borra al
  terminar (`crear_destino_build` / `borrar_destino_build`). `tests/unit/test_tools_validar_en_studio.py`,
  12 pruebas con un doble del cliente.
- R0-03: el arnes del corpus ya no tiene su copia de `_exportar`; `studio_validar` importa
  `exportar` del validador y borra el build temporal. Dos pruebas nuevas en `test_corpus_studio.py`
  comprueban que no hay copia y que la carpeta de build desaparece.
- R0-04 (DC-11, dependencias): `sqlglot` y `jsonschema` siguen declarados porque estan en uso real
  (`src/sgm/ir/sql_tree.py`, `sql_portability.py`, `sql_render.py`, `passes/db_*.py` y
  `rules_validate.py`), y `pytest-testmon` porque solo acelera los ciclos locales. La justificacion
  queda en `pyproject.toml` y en "Decisiones" abajo. Sustituir `sqlglot` por un analizador propio no
  cambiaria la salida, solo el riesgo.
- R0-05: se regeneran `observacion_revision` y `razonamiento` de `L8/totales/03` y `08` desde su
  generador (`tools/corpus_datos/totales_meta.py`): describian la convencion vieja (vacio como NULL)
  y el cruce ya coincide con `''` en texto y `COLLATE RTRIM`. No se toco ningun esperado.
- R0-06 (`tools/ci.py`): un comando corre `ruff check .`, la suite completa, los cruces del corpus
  (`test_corpus_totales_cruce.py` y `test_corpus_validaciones.py`, aparte para que un cruce roto se
  nombre), el oraculo (`corpus.py oraculo todos --verificar`) y el tablero (informativo: no puede
  hacer fallar el cierre). Sale con codigo distinto de 0 si falla un paso obligatorio, imprime la
  cola del que fallo y una tabla con el tiempo de cada paso. Documentado en el README.
- R0-07 (`docs/puesta-en-marcha.md`): requisitos, `uv sync`, `uv run python tools/ci.py`, ciclos con
  `--testmon`, uso basico, problemas conocidos y lo que no se reproduce sin el entorno del banco.
  Verificado en esta maquina: `uv sync` no cambia nada (uv 0.12.24, Python 3.12.10, `uv.lock`
  intacto) y el cierre queda verde. No verificado: clonar en una maquina limpia de verdad.
- R0-08 (higiene): `.gitignore` gana `.testmondata*` (testmon deja mas de un archivo), `/.claude/worktrees/`
  (estado local de las sesiones paralelas, que solo estaba en `.git/info/exclude`) y `build-*/`. Los
  fixtures pesan 2,1 MB (`client_large.sas` 820 KB, el mayor) y `git status` queda limpio tras una
  corrida completa: `out/` y `corpus/` ya estaban ignorados.
- R0-09 (`tools/tablero.py`): imprime la tabla de la seccion 2 del plan con lo que se puede medir sin
  Studio: componentes por Job (emite con `sgm talend` y cuenta `<node>`), conformidad (filas y
  secciones de la referencia cumplidas), pendientes del modelo por motivo, casos del corpus por nivel
  y estado, cobertura de construcciones y, con `--suite`, la linea de `pytest -q`. `--markdown` deja
  solo la tabla. Emitir y analizar se memoriza, asi que el comando tarda unos 10 s.
- R0-10 (`tools/corpus_lib/RIESGOS.md`): 18 riesgos del oraculo (O-01 a O-18), cada uno con la
  afirmacion de `DIFERENCIAS.md`, severidad, caso o vector que lo ejerce hoy y la tarea que lo cierra.
  De los 18, cinco no los ejerce ningun caso (blancos finales en expresiones, fechas con `BETWEEN`,
  `DISTINCT` con blancos, expresion sin alias y el orden sin `ORDER BY`).
- R0-11 (linea base): `docs/plan-reescritura/metricas-base.md` con la instantanea medida y la
  etiqueta local `base-n1` sobre este commit.
- R0-12 (`docs/guia-validacion-studio.md`): el protocolo de Studio en un solo documento, con los
  comandos, los dos arneses, los hechos ya aprendidos, la demostracion del hito 79 y lo que no se
  puede comprobar sin Studio.
- Metricas antes (medidas al empezar, coinciden con la seccion 2 del plan): 26 componentes (padre 13,
  producto 11, totales 1, conciliacion 1); conformidad 42 pasan y 126 xfail de 168 pruebas; 16
  pendientes del modelo; 117 casos del corpus; suite 1529 pasan, 26 se saltan, 132 xfail.
- Metricas despues: las mismas de producto (este hito no cambia la salida de `sgm talend` ni del
  documento); suite 1556 pasan, 26 se saltan, 132 xfail (27 pruebas nuevas); `ruff` limpio. El
  tablero queda como la forma de medirlas: 26 componentes, 12 de 118 filas y 2 de 22 secciones de
  conformidad, 16 pendientes en 5 motivos, 117 casos con 81 traducibles y 206 construcciones distintas.
- Pruebas nuevas: `test_tools_validar_en_studio.py` (12), `test_tablero.py` (6), `test_tools_ci.py`
  (7) y dos en `test_corpus_studio.py`. `uv run python tools/ci.py`: ruff OK, suite OK (47 s), cruces
  OK (1,9 s), oraculo 117 casos y 0 fallas (3,2 s), tablero OK.
- No verificado (bloqueos reales, no pendientes de codigo): la demostracion en Studio real de las
  cuatro correcciones (R0-02) y la repeticion del caso `l2_01` con el arnes ya sin copia (R0-03);
  que un agente nuevo valide un Job siguiendo solo la guia (R0-12); y clonar en una maquina limpia
  (R0-07). Todas necesitan Studio, `talend-mcp` o una maquina sin el proyecto.
- Riesgo: la Fase 0 no cambia la paridad (N1) ni la equivalencia (N2); solo deja las herramientas y la
  linea base. El siguiente paso del camino critico sigue siendo R1-01 (filtro del `tMap` en Studio).

## Decisiones (hito 80)

- DC-11, dependencias fuera de la lista de `AGENTS.md`: se conservan `sqlglot` (analisis y
  reescritura del SQL de SAS; un analizador propio no cambia la salida), `jsonschema` (validacion del
  YAML de reglas) y `pytest-testmon` (solo desarrollo; el cierre de cada hito corre la suite completa).
  Queda escrito en `pyproject.toml` y no se anade ninguna dependencia nueva.
- Numeracion de hitos: numero unico por entrada; las entradas ya publicadas no se renumeran porque
  `docs/` las cita por numero; una serie paralela toma letra (`c` para corpus y contenedores, `b` para
  el resto de las series viejas). La regla vive en `AGENTS.md`.
- El tablero no corre la suite: la suite la mide `tools/ci.py`, que es el que falla por umbrales. El
  tablero cuenta filas y secciones de la referencia (12 de 118, 2 de 22) en vez de las 168 pruebas de
  `tests/conformidad`, porque esas 168 incluyen las 28 pruebas que comprueban que el YAML y el
  documento del manual dicen lo mismo. Las dos cifras quedan explicadas en `metricas-base.md`.

## Hito 81. R1-01: el filtro del `tMap` se ejecuta en Studio y separa las filas

- Fecha: 2026-11-04
- Que se hizo: se implementa R1-01 de la Fase 1 del plan, que era el primer bloqueo del camino
  critico (R1-04 a R1-09 dependen de el). Nuevo `tools/prueba_filtro_tmap.py`: arma con el modelo
  del emisor un Job minimo (`tFileInputDelimited` -> `tMap` con una salida filtrada y otra de
  rechazo de salida -> dos `tFileOutputDelimited`), lo ejecuta en el Studio instalado con un CSV de
  prueba y compara cada rama con lo esperado. La prueba real es del utensilio, no del emisor
  completo: es el mismo `tmap.py` y el mismo `escribir_job` que usa `sgm talend`.
- Corrida 1 (Studio 8.0.1, proyecto `PRJ_BANCOLOMBIA`, filtro `row1.tipo.equals("CC")` sobre cinco
  filas `1;CC`, `2;AHO`, `3;CC`, `4;NEQUI`, `5;CC`):
  `validos.csv: ['1', '3', '5']`, `rechazados.csv: ['2', '4']`, codigo de salida 0,
  `RESULTADO: el filtro funciona`.
- Corrida 2 (carpeta de trabajo con espacios en el nombre, para probar las comillas de R0-02): mismo
  resultado, codigo 0. El comando ejecutado quedo con `--context="Default"` y cada
  `--context_param "clave=C:/.../prueba filtro espacios/..."` entre comillas.
- Las dos corridas usan el patron completo de `job_producto`: salida filtrada por `FLOW` y salida
  de rechazo por `REJECT`. No hubo una tercera corrida.
- Hallazgos: (1) `expressionFilter` con `activateExpressionFilter="true"` en una salida del `tMap`
  funciona **ejecutando**, no solo compilando; no hace falta `tFilterRow`. (2) La segunda salida con
  `reject="true"` recoge exactamente las filas que el filtro descarta, con el conector `REJECT`.
  (3) El servidor deja el lanzador en `<destino>/<job>/` y `exportar` lo encuentra con `rglob`
  (R0-02 verificado en real). (4) La carpeta `build-*` de esta corrida se borro al terminar (R0-02,
  cuarta correccion, verificada en real). Las 30 carpetas `build-*` que siguen en `%TEMP%` son de
  sesiones anteriores a la correccion; cada una pesa 1 KB y no tocan el repositorio.
- Riesgo para R1-04 a R1-09 (anotado, no verificado): el filtro probado compara una columna de texto
  no nula. En `job_producto` la columna que se filtra viene de un `LEFT JOIN`, asi que puede ser
  nula y `row1.columna.equals(...)` lanzaria `NullPointerException`. Antes de escribir esas
  validaciones hay que usar la forma que aguanta el nulo (`"CC".equals(row1.columna)` o
  `Relational.IS_EQUALS`) y probarla con una fila sin pareja.
- No verificado: filtro sobre columnas numericas o `BigDecimal`; filtro con varias condiciones
  unidas por `&&`; y el mismo filtro dentro de `job_producto` (eso es R1-04).
- Pruebas: `tests/unit/test_prueba_filtro_tmap.py` (7; sin Studio: el `.item`, la entrada de prueba,
  la lectura de la salida, el protocolo y los dos desenlaces). `uv run pytest -q`: 1563 pasan, 26 se
  saltan, 132 xfail. `ruff check .`: limpio.
- Estado en el plan: R1-01 `hecho`; R0-02 pasa a `hecho` (las cuatro correcciones con demostracion
  real: busqueda recursiva, comillas con espacios y borrado del build; la version distinta de 0.1
  solo con doble).

## Hito 82. R1-01 (cierre): el filtro del `tMap` aguanta columnas nulas de un `LEFT JOIN`

- Fecha: 2026-11-05
- Que se hizo: se cierra la salvedad que el hito 81 dejo anotada. En un `LEFT JOIN` del `tMap` las
  columnas del lookup quedan a `null` cuando la fila principal no tiene pareja; el filtro probado
  en el 81 (`row1.tipo.equals("CC")`) solo servia con texto no nulo y era el bloqueo de R1-04 a
  R1-09. `src/sgm/talend_item/expresiones.py` deja `null_safe_equals(expresion, valor)`, que pone
  el literal a la izquierda (`"CC".equals(row2.valor)`), y `tools/prueba_filtro_nulo.py` arma un
  Job minimo con dos `tFixedFlowInput` (principal de seis filas, lookup de tres: D, E y F sin
  pareja), un `tMap` sin `innerJoin` con salida filtrada y salida de rechazo, y dos
  `tFileOutputDelimited`. El comando corre cada forma del filtro en Studio con un sufijo nuevo.
- Corrida 1 (Studio 8.0.1, proyecto `PRJ_BANCOLOMBIA`, sufijo `v82a`, forma `segura`, filtro
  `"CC".equals(row2.valor)`): `validos.csv: ['1', '3']`, `rechazados.csv: ['2', '4', '5', '6']`,
  codigo de salida 0, `RESULTADO: el filtro seguro separa las filas con y sin pareja`. Las tres
  filas sin pareja salen por el rechazo sin lanzar excepcion.
- Corrida 2 (sufijo `v82b`, forma `insegura`, filtro `row2.valor.equals("CC")`): codigo de salida
  1, `[FATAL] tMap_1 Cannot invoke "String.equals(Object)" because "row2.valor" is null`, con
  `java.lang.NullPointerException` en stdout y stderr; `validos.csv: ['1', '3']` y
  `rechazados.csv: ['2']` (el Job se corta en la primera fila sin pareja). `RESULTADO: el filtro
  inseguro falla con NullPointerException`. Es la demostracion del riesgo, no un fallo del cierre.
- Hallazgos: (1) el riesgo del hito 81 era real y aparece ejecutando, no solo en teoria; (2) un
  `LEFT JOIN` del emisor (`EntradaMap` sin `union_interna`) deja las columnas del lookup a `null`,
  asi que toda comparacion de texto en `expressionFilter` o en expresiones de salida debe llevar
  el literal a la izquierda; (3) la conexion `LOOKUP` con `lineStyle` 8 y el `catch output reject`
  funcionan juntos: el rechazo recoge tanto las filas que no cumplen el filtro como las que no
  tienen pareja; (4) los dos Jobs de prueba se borraron del proyecto al terminar (`process/` sin
  residuales).
- No verificado: filtro con columnas numericas o `BigDecimal`; filtro con varias condiciones
  unidas por `&&`; el mismo filtro dentro de `job_producto` (eso es R1-04); comparaciones con
  `Relational.IS_EQUALS`, que no hizo falta.
- Pruebas: `tests/unit/test_talend_expresiones.py` (4) y `tests/unit/test_prueba_filtro_nulo.py`
  (11): el `.item` con el filtro seguro, el `LEFT JOIN` y la conexion de busqueda, el escapado del
  literal de Java, las seis filas y sus tres sin pareja, la limpieza de salidas previas y el
  protocolo con doble del servidor para ambos desenlaces. `uv run pytest -q`: 1578 pasan, 26 se
  saltan, 132 xfail. `uv run ruff check .`: limpio.
- Metricas antes (tablero del hito 81): 26 componentes, conformidad 12 de 118 filas y 2 de 22
  secciones, 16 pendientes, 117 casos del corpus, suite 1563 pasan. Despues: las mismas de
  producto (este hito no cambia la salida de `sgm talend` ni el documento de diseno); suite 1578
  pasan, 26 se saltan, 132 xfail (15 pruebas nuevas); `ruff` limpio.
- Estado en el plan: R1-01 `hecho` sin salvedades. Quedan desbloqueadas R1-04 a R1-09, que deben
  usar `null_safe_equals` en vez de `.equals` sobre la columna. El camino critico sigue por R1-02.
- Riesgo: `null_safe_equals` solo compara texto; las validaciones de R1-06 (GMF, Codex) y R1-07
  (saldos negativos) comparan numeros y necesitan su propia forma de tratar el faltante, que no
  se inventa aqui.

## Hito 83. R1-02 (parte 1): las expresiones de normalización coinciden con el oráculo en Studio

- Fecha: 2026-11-05
- Que se hizo: `src/sgm/talend_item/normalizacion.py` da expresiones Java puras para el `tMap` (sin
  rutinas de Studio, sin sentencias, sin `;`): `left`, `strip`, `trim`, `upcase`, `lowcase`,
  `compbl`, `normalizar_nombre` (`COMPBL(STRIP(UPCASE(x)))`), `compress` (clases a/d/f/h/l/n/p/s/u
  y modificadores `k` e `i`) e `input_left_wd` (`input(left(x), w.d)`: `BigDecimal` o `null`).
  Todas aguantan columna nula con `x == null ? null : ...` y `as_text` convierte el faltante en
  cadena vacia para el CSV. Los caracteres no ASCII salen como escapes Unicode de Java, asi que
  las Ñ/Í de v06 no dependen de la codificacion del `.java` generado; `UPCASE`/`LOWCASE` usan
  `java.util.Locale.ROOT` para no depender del locale del motor.
- Oraculo independiente: `tools/prueba_normalizacion.py` arma un Job de una sola fila y 45
  columnas (un `tFixedFlowInput`, un `tMap` con una expresion por columna y un
  `tFileOutputDelimited` en UTF-8). El esperado NO lo calcula el traductor: los 29 vectores con
  fuente de `tests/corpus/semantica/vectores.yaml` los evalua
  `tools/corpus_semantica_funciones.py`, y los 16 nombres de
  `L8/validaciones/v06_normalizacion` salen del `esperado/SABANA_NORM_CTE.csv` construido por el
  corpus. El comando compara columna por columna: numeros con `Decimal`, texto exacto y
  `Faltante` con cadena vacia.
- Corrida (Studio 8.0.1, proyecto `PRJ_BANCOLOMBIA`, sufijo `v83a`): codigo de salida 0,
  `Vectores: 45; coinciden: 45; fallan: 0`,
  `RESULTADO: la normalización coincide con el oráculo`. Lineas literales de la salida:
  `OK  input-02: esperado '23.0', obtenido '23'`;
  `OK  input-04: esperado '23.0', obtenido '23.00'`;
  `OK  input-06: esperado '0.23', obtenido '0.23'`;
  `OK  input-09: esperado '', obtenido ''`;
  `OK  nombre_v06_05: esperado 'NIÑO FICTICIO 00005', obtenido 'NIÑO FICTICIO 00005'`;
  `OK  nombre_v06_10: esperado 'CLIENTE FICTICIO 00010', obtenido 'CLIENTE FICTICIO 00010'`.
  Lanzador ejecutado:
  `".../prueba_normalizacion_v83a_run.bat" --context="Default" --context_param "ruta_salida=C:/tmp/sgm-normalizacion/primera/salida"`.
- Hallazgos: (1) `new java.math.BigDecimal` acepta `.5`, `-.5`, `+23`, `23.` y `0023` en el JDK
  21.0.11 de Studio (comprobado antes con `jshell`); con `w.d` sin punto decimal basta
  `movePointLeft(d)`. `23.00` y `23.0` son distintos como texto pero iguales como numero, y la
  comparacion los trata como tales. (2) `matches` con `[+-]?(\d+\.?\d*|\.\d+)` reproduce el
  `_NUMERO` del oraculo: punto solo, campo vacio, blancos internos (`23 45`) y texto no numerico
  dan faltante. (3) `compress` con clases que incluyen caracteres de control funciona porque el
  patron llega al motor de regex como `\u0009` (doble barra en el codigo Java), no como un control
  crudo que romperia el `.java`. (4) Los nombres con Ñ, Í y blancos multiples de v06 pasan por
  `COMPBL(STRIP(UPCASE(x)))` sin depender del locale. (5) El Job de prueba se borro del proyecto
  al terminar; `process/` quedo sin residuales.
- No verificado (no se inventa): **decimales con coma**. El criterio de R1-02 los menciona, pero
  ni `vectores.yaml` ni `L4` ni `v06` aportan un caso con coma decimal y fuente: no hay semantica
  que contrastar, asi que no se implemento. Tampoco se verificaron `compress` con `chars` que
  contengan comillas, ni informats con `d > 0` combinados con punto decimal fuera de los vectores.
- Alcance: este hito valida las **expresiones** sueltas, no las conecta al emisor. R1-02 pide
  ademas que `sgm talend` las aplique a las columnas marcadas `numerica` por `esquema_csv`; eso es
  el hito 84. Por eso R1-02 queda `parcial` en el plan y no `hecho`.
- Pruebas: `tests/unit/test_talend_normalizacion.py` (21) y
  `tests/unit/test_prueba_normalizacion.py` (14): escapado de literales, nulo-seguridad, ausencia
  de sentencias, truncado y `movePointLeft`, clases y modificadores de `compress`, composicion de
  `normalizar_nombre`, origen de los 45 vectores, `.item` con una expresion por columna,
  comparacion, lectura del CSV, limpieza de salidas previas y protocolo con doble del servidor
  para los tres desenlaces. `uv run pytest -q`: 1613 pasan, 26 se saltan, 132 xfail (35 pruebas
  nuevas sobre las 1578 del hito 82). `uv run ruff check .`: limpio.
- Metricas del tablero: sin cambios (26 componentes, conformidad 12 de 118 filas y 2 de 22
  secciones, 16 pendientes, 117 casos del corpus, 81 `traducible`, 0 traducidos por un traductor
  automatico y pasados en Studio). Este hito no cambia la salida de `sgm talend` ni el documento
  de diseno.
- Estado en el plan: R1-02 pasa de `pendiente` a `parcial` (expresiones verificadas con evidencia
  en Studio; integracion pendiente). El camino critico sigue por el hito 84, que no depende de
  decision humana, SAS real ni datos reales.
- Riesgo: `input_left_wd` quita los blancos iniciales antes de truncar a `w`, mientras el oraculo
  `input_wd` trunca primero y quita blancos despues. En los 29 vectores actuales ningun caso
  supera `w` teniendo blancos iniciales, asi que coinciden; si apareciera, hay que decidir con un
  vector con fuente cual de las dos lecturas es la de SAS antes de cambiar el codigo. El SAS de
  `client_large.sas` usa `input(left(x), 30.)`, es decir, primero `LEFT`, lo que respalda el orden
  elegido aqui, pero el oraculo de los vectores modela `input(x, w.d)` sin `LEFT`.

## Hito 84. R1-02 (parte 2): la normalización llega al emisor y los Jobs emitidos compilan en Studio

- Fecha: 2026-11-05
- Que se hizo: se cierra la integración de R1-02 en `sgm talend`, que en el hito 83 solo existía
  como expresiones sueltas verificadas.
  - `src/sgm/proceso/esquema_csv.py` captura el informat completo `w.d` de
    `X=input(left(VARn), 30.)`, `8.2`, `COMPRESS(input(...))` y de las formas con espacios y
    mayúsculas. `ColumnaCsv` guarda `ancho` y `decimales` (0/0 cuando el SAS no demuestra
    conversión). No se supone ningún tipo nuevo.
  - `origenes_producto()` publica `numericas_comunes` (columna -> `(w, d)`) y, si dos productos
    declaran informats distintos para la misma columna, elige el menor **y lo deja en
    `pendientes`** en vez de decidir en silencio. Sobre el SAS real hay 15 columnas:
    `NRO_CTA` (30,0), `TIPO_DOC` (8,0), `GMF` (3,0), `FIN_SALDO_CTA` (30,0);
    `ANIO_PROCESO` solo tiene alias y sigue siendo texto.
  - `cli_talend` pasa `numericas=origenes.numericas_comunes` a `job_producto`. Sin columnas
    numéricas demostradas no se emite ningún `tMap` de normalización: no se inventan conversiones.
  - `jobs_producto.py` inserta `tMap_normalizacion` entre `tFileInputDelimited_1` y
    `tReplicate_1`, conserva las 23 columnas, convierte solo las 15 numéricas con
    `as_text(input_left_wd(row1.col, w, d))` y deja las demás como `row1.col`. `_a_decimal`
    (saldo de origen y filas válidas) usa el mismo `w.d` real en vez de un ancho fijo.
- Evidencia en Studio 8.0.1, proyecto `PRJ_BANCOLOMBIA`, dos comprobaciones reales:
  1. Job suelto `job_producto_v84a`, copiando solo su `.item`/`.properties`:
     `{"ok": true, "source": "studio-bridge", "confidence": "high", "data": {"ok": true,
     "result": {"total": 1, "correctos": 1, "totalMs": 2383, "jobs":
     {"job_producto_v84a": {"generateMs": 1049, "compileMs": 1333, "ok": true}}}}}`.
  2. Comprobación reproducible del repo (sufijo `v84e`), con
     `uv run python tools/validar_en_studio.py tests/fixtures/sas/client/client_large.sas --project "<proyecto>" --sufijo v84e --solo-compilar`.
     Salida literal: `Compilando hijos: job_conciliacion_v84e, job_producto_v84e, job_totales_v84e`;
     `Compilando padre: job_exogena_depositos_v84e`;
     `RESULTADO BUILD: {"job_conciliacion_v84e": {"generateMs": 186, "compileMs": 384, "ok": true}, "job_producto_v84e": {"generateMs": 507, "compileMs": 735, "ok": true}, "job_totales_v84e": {"generateMs": 175, "compileMs": 352, "ok": true}, "job_exogena_depositos_v84e": {"generateMs": 705, "compileMs": 664, "ok": true}}`;
     `Limpieza: 8 archivos borrados del proyecto y build temporal borrado`; código de salida 0.
- Hallazgos (los tres aparecieron al volver reproducible la comprobación, no se buscaron a mano):
  1. `validar_en_studio.construir()` leía solo `datos["jobs"]` como lista. El Studio bridge real
     devuelve `data.result.jobs` como **diccionario** por nombre de Job, así que un build fallido
     habría pasado por bueno. Ahora `resultados_build()` entiende las dos formas y se comprueba el
     `ok` de cada Job, que `correctos == total` y los `ok` del servidor y del puente. Con eso
     apareció el fallo del primer intento (`v84b`): `no compilan: {"job_exogena_depositos_v84b": {"ok": false, "error": {"message": "Cannot invoke \"Object.getClass()\" because \"item\" is null"}}, "<lote>": {"total": 1, "correctos": 0}}`.
  2. Causa: `renombrar()` reescribía cada `.item` solo con su propio nombre e id, pero las
     referencias `PROCESS` y `PROCESS:PROCESS_TYPE_PROCESS` de los `tRunJob` viven en el `.item`
     del **padre**. Con sufijo nuevo el padre seguía apuntando a los hijos originales. Se añadió
     una segunda pasada con el mapa completo de nombres e ids sobre todos los `.item`; con ella
     compilan los 4. Se descartó que fuera cosa de `parchear_padre` repitiendo la prueba sin ese
     parcheo (`v84c`, mismo fallo antes del arreglo).
  3. `--solo-compilar` deja la comprobación en un comando del repo, sin Excel ni CSV simulados:
     emite, renombra, refresca, compila hijos antes que el padre y limpia siempre.
- Alcance: es evidencia de **compilación**, no de ejecución con datos. Las expresiones sueltas sí
  se ejecutaron en Studio en el hito 83; ejecutar el `job_producto` emitido contra CSV y Excel
  reales pertenece a R1-03/G4. En este hito no se ejecutó ningún Job.
- Decisiones: (a) R1-02 se marca `hecho` **con dos salvedades explícitas**: sigue sin haber vector
  con fuente para decimales con coma (no se implementó esa semántica) y `compress`, `UPCASE`,
  `COMPBL` y caracteres especiales están verificadas como expresiones pero aún no se asignan a
  columnas concretas del emisor, porque este SAS no demuestra qué columnas pasan por ellas; se
  retoman en R1-05/R1-08. No se marca `hecho` a secas para no inflar el plan. (b) el ancho por
  omisión de `_a_decimal` cuando el llamador no aporta `numericas` sigue siendo 20, el que declara
  `decisiones/client_large.jobs.yaml`; cuando el CLI aporta el informat, manda el SAS.
  (c) `metricas-base.md` no se modifica: es la foto de G0. (d) `tools/validar_en_studio.py`
  queda en 396 líneas, por encima de las 300 de la regla de `AGENTS.md`: se acepta como desviación
  registrada porque partirlo ahora cambiaría la superficie de importación de cuatro arneses y sus
  pruebas sin beneficio para R1-02; hay precedente en `tools/etiquetas_fase0.py` (364) y
  `tools/prueba_normalizacion.py` (325). La división queda pendiente para un hito de herramientas.
- Efecto colateral a verificar en R1-03: al normalizar `TIPO_DOC` con `8.`, un `01` de origen
  llega al lookup como `1`, justo la comparación texto frente a número que el diseño dejó
  pendiente. No se afirma que ya coincida: hace falta correr el caso `v01` con datos.
- Pruebas: 22 nuevas en `test_talend_emision_normalizacion.py` (cadena completa SAS -> `.item`:
  15 conversiones, anchos 3/8/30, conexiones, ausencia del `tMap` sin `numericas`),
  `test_proceso_fuentes_csv.py` (5), `test_proceso_origen_producto.py` (3),
  `test_tools_validar_en_studio.py` (9: las dos formas del build, los cuatro modos de fallo y las
  referencias cruzadas del padre) y `test_tablero.py` (expectativa actualizada).
  `uv run pytest -q`: 1635 pasan, 26 se saltan, 132 xfail (frente a 1613 del hito 83).
  `uv run ruff check .`: limpio.
- Métricas del tablero: 27 componentes emitidos (job_conciliacion 1, job_exogena_depositos 13,
  job_producto **12**, job_totales 1; antes 26 y 11 por el `tMap` nuevo). Sin cambios en
  conformidad (12 de 118 filas, 2 de 22 secciones), 16 pendientes en 5 motivos, 117 casos del
  corpus, 81 `traducible` y 0 traducidos por un traductor automático y pasados en Studio.
- Estado en el plan: R1-02 pasa de `parcial` a `hecho` con las salvedades anteriores; quedan
  desbloqueadas R1-10 y R1-11, que dependían de R1-02. El camino crítico sigue por R1-03, la
  primera tarea que pide datos reales y, por tanto, el próximo candidato a bloqueo humano.
- Riesgo: la normalización cambia el texto que ven todos los nodos aguas abajo de
  `tMap_normalizacion` (incluida la homologación de tipo de documento), y eso solo se ha
  comprobado compilando, no ejecutando. La segunda pasada de `renombrar` reescribe referencias
  en atributos `value="..."`; si Studio llegara a guardar alguna en otro atributo, habría que
  ampliarla. `metricas-base.md` conserva 26/11 porque es la línea base de G0, no el valor actual.

## Hito 85. R1-03 (parte 1): el `job_producto` emitido se ejecuta con datos y se mide `01` frente a `1`

- Alcance: primera ejecución **con datos** de un Job emitido por `sgm talend` desde R1-02. No
  se construyó un Job a mano: `tools/prueba_tipo_doc.py` emite con `sgm talend`, toma solo el
  `job_producto_0.1.item/.properties`, lo renombra con sufijo nuevo, compila, exporta y corre el
  lanzador dos veces (CTE y AHO) contra las entradas de `L8/validaciones/v01_tipo_doc`, pasando
  por contexto `ruta_origen`, `ruta_insumos`, `arch_hom_tipo_doc`, `ruta_resultados`,
  `hoja_excel=Sheet1`, `sufijo` y periodo. `tools/tipo_doc_variantes.py` guarda la parte
  determinista: las tres escrituras de los códigos, los esperados y la lectura de resultados.
  **No se tocó `src/`**: este hito mide el emisor, no lo cambia.
- Verdad plantada, leída de `esperado/` del corpus (fuente independiente, nunca calculada con la
  salida del propio Job): CTE 95 filas, 88 válidas, 7 rechazadas; AHO 65, 60 y 5. En las doce
  corridas se comprobó además el invariante de R1-03 `origen == válidos + rechazados`.
- Matriz ejecutada en Studio 8.0.1, proyecto `PRJ_BANCOLOMBIA`. Las seis celdas se corrieron con
  el arnés final; todas con código de salida 0 del lanzador y
  `RESULTADO: 2 de 2 productos reproducen lo esperado`. Salidas literales:

  ```text
  v85g texto, normalizado:    CTE: v01 planta {'origen': 95, 'validos': 88, 'rechazados': 7}; combinación esperada {'origen': 95, 'validos': 0, 'rechazados': 95}; obtenido {'origen': 95, 'validos': 0, 'rechazados': 95}
    invariante origen=válidos+rechazados: sí; OK (input(..., 8.) deja faltante un código de texto: todo se rechaza)
  AHO: v01 planta {'origen': 65, 'validos': 60, 'rechazados': 5}; combinación esperada {'origen': 65, 'validos': 0, 'rechazados': 65}; obtenido {'origen': 65, 'validos': 0, 'rechazados': 65}
  v85h texto, sin normalizar: CTE: obtenido {'origen': 95, 'validos': 88, 'rechazados': 7}; OK (coincide con la verdad plantada en v01)
  AHO: obtenido {'origen': 65, 'validos': 60, 'rechazados': 5}; OK
  v85i ceros, normalizado, Excel 01..04: CTE: obtenido {'origen': 95, 'validos': 0, 'rechazados': 95}; OK (el 01 del CSV llega como 1 y el Excel conserva 01: todo se rechaza)
  AHO: obtenido {'origen': 65, 'validos': 0, 'rechazados': 65}; OK
  v85j numérico, normalizado: CTE: obtenido {'origen': 95, 'validos': 88, 'rechazados': 7}; OK (coincide con la verdad plantada en v01)
  AHO: obtenido {'origen': 65, 'validos': 60, 'rechazados': 5}; OK
  v85k ceros, sin normalizar, Excel 01..04: CTE: obtenido {'origen': 95, 'validos': 88, 'rechazados': 7}; OK
  AHO: obtenido {'origen': 65, 'validos': 60, 'rechazados': 5}; OK
  v85l ceros, normalizado, Excel 1..4: CTE: obtenido {'origen': 95, 'validos': 88, 'rechazados': 7}; OK
  AHO: obtenido {'origen': 65, 'validos': 60, 'rechazados': 5}; OK
  ```

  Los sufijos `v85a`..`v85f` fueron corridas exploratorias con versiones intermedias del arnés;
  la evidencia publicada es `v85g`..`v85l`, repetida con el código que queda en el repositorio.
  Comando de una celda (las otras cambian `--variante`, `--sin-normalizar` y `--excel-sin-ceros`):

  ```text
  uv run python tools/prueba_tipo_doc.py --proyecto "C:/Talend/8.0.1/studio/workspace/talendbancolombia-963626413/PRJ_BANCOLOMBIA" --java-bin "C:/Talend/8.0.1/zulu21.50.19-ca-jdk21.0.11-win_x64/bin" --m2 "C:/Talend/8.0.1/studio/configuration/.m2/repository" --variante ceros --excel-sin-ceros --sufijo v85l --trabajo "C:/tmp/sgm-hito85/final-v85l"
  ```

- Hallazgos:
  1. El lookup emitido (`tMap` con `tFileInputExcel`, `union_interna` y salida de rechazo) **sí**
     reproduce `v01` para CTE y AHO cuando los dos lados de la unión tienen la misma escritura:
     `v85h` (texto/texto), `v85j` (número/número), `v85k` (`01`/`01`) y `v85l` (`1`/`1`).
     Queda ejecutado, no solo compilado, el efecto colateral que el hito 84 dejó anotado.
  2. Con el Job tal como lo emite hoy `sgm talend`, el caso original `v01` **no** coincide:
     sus códigos son de texto (`TD01`..`TD04`, `TD99`) y `input(left(VAR9), 8.)` de R1-02 los deja
     faltantes (`v85g`: 0 válidos, 95 y 65 rechazados). No es un fallo del lookup: es la
     convención de datos del corpus frente al informat numérico que el SAS real sí demuestra.
  3. La comparación `01` frente a `1` de T10 queda medida en las cuatro combinaciones `v85i`,
     `v85k`, `v85l` y `v85j`. La causa estructural está en el `.item`: la clave compara
     `row2.CNAME` (Excel, crudo) contra `copy2.TIPO_DOC` (flujo principal, ya normalizado); la
     normalización de R1-02 solo se aplica al flujo principal, nunca a la entrada del lookup.
     Por eso `01` normalizado a `1` no casa con un Excel que conserva `01`, y sí casa con un
     Excel en `1..4`. No hay un error de Java: hay una decisión de representación pendiente.
- Bloqueos reales (el hito se detiene aquí, no se cruza ninguno):
  1. **Sin SAS en el entorno.** Tanto `v01_tipo_doc` como `v08_nequi_cadena` están
     `pendiente_revision`: no está demostrado con SAS el tipo que `PROC IMPORT` da a `NRO_DOC` ni
     el formato de `PROC EXPORT`. Sin eso no se puede decidir si `TIPO_DOC` y el Excel de
     homologación deben compararse como texto o como número; hacerlo a ojo sería inventar
     comportamiento (principio 2 del plan). DC-12, "significado de los códigos de tipo de
     documento", sigue siendo decisión de Negocio.
  2. **NEQUI no está en `v01`.** El criterio de R1-03 pide CTE, AHO y NEQUI, pero `v01` solo
     planta CTE y AHO; la cadena NEQUI es `v08` (R1-16), con su propio Excel y también
     `pendiente_revision`. Cerrar R1-03 exigiría datos reales o una revisión humana de ese caso.
  3. No se modificó el emisor para "hacer pasar" `v01`: quitar la normalización de `TIPO_DOC`
     contradiría el SAS real (`input(..., 8.)`), y normalizar también el Excel exigiría saber cómo
     `PROC IMPORT` tipa esa columna. `--sin-normalizar` es un experimento del arnés sobre el
     `.item` copiado, explícitamente **no** evidencia del producto.
- Decisiones: (a) R1-03 sigue `parcial`, ahora con evidencia y el bloqueo escrito; no se marca
  `hecho` para no inflar el plan. (b) Se retira parcialmente la salvedad de R1-02 "compilación,
  no ejecución con datos" para `job_producto`: ya se ejecutó con datos, aunque con entradas
  simuladas del corpus y no con los insumos reales del cliente; la equivalencia N2 de G4 sigue
  abierta. (c) El arnés se partió en dos módulos (198 y 143 líneas) para cumplir el límite de
  300 de `AGENTS.md` sin registrar otra desviación. (d) Los Excel de las variantes numéricas se
  generan con `simular_insumos.escribir_xlsx`: son datos simulados, nunca copias de datos reales.
- Pruebas: 40 nuevas en `tests/unit/test_prueba_tipo_doc.py` (variantes y esperados, matriz
  `coincide()`, preparación de entradas, lectura de `tLogRow` y del archivo de rechazos,
  invariantes y protocolo completo con dobles de Studio). `uv run pytest -q`: 1675 pasan,
  26 se saltan, 132 xfail (frente a 1635 del hito 84). `uv run ruff check .`: limpio.
- Métricas del tablero: sin cambios, 27 componentes emitidos, conformidad 12 de 118 filas y
  2 de 22 secciones, 16 pendientes en 5 motivos, 117 casos del corpus. Este hito no añade
  componentes ni traducciones: mide las que ya existen.
- Riesgo: las cuatro celdas que coinciden lo hacen sobre insumos **simulados** y con un Job
  copiado y renombrado; no prueban el padre ni la corrida completa de `job_exogena_depositos`.
  `medir()` cuenta las líneas de `doc_incorrectos_<producto>.csv` y los dos `tLogRow`; si el
  diseño cambia el formato de esas salidas, el arnés debe actualizarse antes de volver a usarlo.

## Hito 86. R1-04 (parte 1): `v02_vacios_ceros` separa los tres flujos en Studio y coincide fila por fila

- Alcance: primera ejecución con datos de las reglas de vacíos y ceros. El hito **no** modifica
  `cli_talend.py` ni `jobs_producto.py`: construye un Job mínimo con los módulos de producto, igual
  que los arneses de R1-01/R1-02. La integración en el `job_producto` emitido queda para el hito 87.
  Cuatro módulos nuevos en `src/` y `tools/`, todos por debajo de las 300 líneas de `AGENTS.md`.
- Las reglas salen del SAS, no de YAML. `src/sgm/proceso/reglas_fila.py` reconoce sentencias
  `CREATE TABLE ... AS SELECT ... WHERE` y las tres formas del filtro: titulares/cotitulares
  (`NRO_DOC = 0 OR IS MISSING` con `RELACION <> 9902`), firmas autorizadas (lo mismo con
  `RELACION = 9902`) y válidos (`IS NOT MISSING AND <> 0`). Cubre el alias del programa real
  (`SABANA_NO_DUPLICADOS_AHO.NRO_DOC`) y el del corpus con macro (`SABANA_&sufijo..NRO_DOC`). En
  `client_large.sas` detecta **10** reglas: las 6 de separación (3 por producto), una de NEQUI y 3
  `FINAL_VALIDAR_NRO_DOC_*` que revalidan al final; se documentan, no se descartan en silencio. La
  cadena larga de `Campos vacios` (19 `IS MISSING`) **no** entra: no tiene la forma `= 0 OR ...`,
  queda para la parte 2 de R1-04 con su propio caso.
- `src/sgm/talend_item/filtros_fila.py` traduce cada regla a un `expressionFilter` de Java puro
  (sin punto y coma ni sentencias). Como `tMap_normalizacion` de R1-02 entrega `NRO_DOC` en texto,
  el faltante de SAS es `""` y el cero es `"0"`:
  `(row1.NRO_DOC == null || "".equals(row1.NRO_DOC) || "0".equals(row1.NRO_DOC))`. La comparación
  de `RELACION` reutiliza `null_safe_equals` del hito 82, con el literal a la izquierda, para no
  repetir el `NullPointerException` de R1-01. `valido` es la negación exacta de `vacio_o_cero`, y
  `tit_cot` frente a `fa` se diferencian solo por la negación de `RELACION`. Un modo sin esquema
  declarado lanza `ValueError`: no se inventan columnas.
- `tools/vacios_ceros_datos.py` lee la verdad plantada de `esperado/` y `caso.yaml`, nunca la
  calcula con la salida del Job. El caso declara `orden_relevante: false`, así que los tres flujos
  se comparan como multisets (filas ordenadas), no por posición. Comprueba además el desglose
  vacío/cero de las anomalías y las tres invariantes medibles. El esquema de 23 columnas queda
  anclado por prueba unitaria a `origenes_producto().columnas_comunes` del SAS real.
- `tools/prueba_vacios_ceros.py` monta `tFileInputDelimited -> tMap_normalizacion -> tMap_filtros
  -> 3 tFileOutputDelimited`. Solo normaliza `NRO_DOC` con `(30, 0)`, que es lo que `v02`
  demuestra (`input(left(NRO_DOC_TXT), 30.)`); aplicar los 15 informats del `client_large.sas`
  borraría el texto `TD01..TD04` de `TIPO_DOC` y no correspondería a este caso. No se inventan
  conversiones. El Job se renombra, se compila en Studio, se exporta y se corre dos veces (CTE y
  AHO) contra `entradas/DETALLE_<producto>.csv`.
- Corrida final en Studio 8.0.1, proyecto `PRJ_BANCOLOMBIA`, sufijo `v86c`, con el árbol exacto
  que queda en el repositorio; código de salida 0 del arnés y de los dos lanzadores. Salida literal:

  ```text
  Proyecto: C:\Talend\8.0.1\studio\workspace\talendbancolombia-963626413\PRJ_BANCOLOMBIA
  Sufijo: v86c
  Código de salida CTE: 0
  CTE tit_cot: esperadas 5 filas, obtenidas 5; OK
  CTE fa: esperadas 5 filas, obtenidas 5; OK
  CTE valido: esperadas 85 filas, obtenidas 85; OK
  CTE anomalías plantadas {'tit_cot_vacio': 3, 'tit_cot_cero': 2, 'fa_vacio': 1, 'fa_cero': 4, 'validos': 85}; obtenidas {'tit_cot_vacio': 3, 'tit_cot_cero': 2, 'fa_vacio': 1, 'fa_cero': 4, 'validos': 85}; OK
  Código de salida AHO: 0
  AHO tit_cot: esperadas 3 filas, obtenidas 3; OK
  AHO fa: esperadas 2 filas, obtenidas 2; OK
  AHO valido: esperadas 70 filas, obtenidas 70; OK
  AHO anomalías plantadas {'tit_cot_vacio': 2, 'tit_cot_cero': 1, 'fa_vacio': 2, 'fa_cero': 0, 'validos': 70}; obtenidas {'tit_cot_vacio': 2, 'tit_cot_cero': 1, 'fa_vacio': 2, 'fa_cero': 0, 'validos': 70}; OK
  Limpieza: 2 archivos borrados del proyecto y build temporal borrado
  Invariantes: sábana=válidos+rechazos sí; conteos=rechazos CTE+AHO sí; suma saldo CTE=1024505 frente a 1024505 sí
  RESULTADO: 2 de 2 productos coinciden fila por fila
  ```

  Comando (log completo en `C:/tmp/sgm-hito86/v86c.log`, fuera del repositorio):

  ```text
  uv run python tools/prueba_vacios_ceros.py --proyecto "C:/Talend/8.0.1/studio/workspace/talendbancolombia-963626413/PRJ_BANCOLOMBIA" --java-bin "C:/Talend/8.0.1/zulu21.50.19-ca-jdk21.0.11-win_x64/bin" --m2 "C:/Talend/8.0.1/studio/configuration/.m2/repository" --sufijo v86c --trabajo "C:/tmp/sgm-hito86/v86c"
  ```

- Corridas exploratorias, registradas para no inflar la evidencia: `v86a` pasó CTE (5/5/85) y
  luego cayó con `KeyError: 'fa_nro_doc_cero'` porque `caso.yaml` **no** declara esa anomalía para
  AHO; el caso planta cero, no es un dato perdido. Se corrigió con `.get(..., 0)` y `v86b` pasó
  completo. `v86c` repite la corrida ya con las pruebas unitarias añadidas, para que la evidencia
  publicada corresponda exactamente al código versionado.
- Hallazgos:
  1. Los tres flujos son disjuntos y cubren la sábana: CTE `5 + 5 + 85 = 95` y AHO
     `3 + 2 + 70 = 75`, y los conteos `CONTEO_NRO_DOC_TIT_COT + CONTEO_NRO_DOC_FA` igualan los
     rechazos de ambos productos. La suma de `FIN_SALDO_CTA` de los válidos CTE es 1024505, la
     misma que `SUMA_SALDO_CTE_VALIDAS.csv`.
  2. La decisión de representación que R1-03 dejó abierta aquí sí está resuelta por el propio
     caso: `v02` convierte `NRO_DOC` con `input(left(...), 30.)`, de modo que el faltante y el cero
     llegan al filtro como `""` y `"0"` en texto. Comparar como número habría sido inventar
     comportamiento; comparar como texto con el literal a la izquierda es nulo-seguro.
  3. El `client_large.sas` real repite la misma terna por producto y además revalida al final.
     El detector no colapsa esas 10 reglas en 3: deja constancia de las 4 adicionales para que la
     futura integración en el emisor no pierda las etapas de NEQUI y `FINAL_VALIDAR`.
  4. AHO no declara `fa_nro_doc_cero`. El comparador lo interpreta como cero plantado, no como
     columna ausente: es la única lectura compatible con `caso.yaml` y con `esperado/`.
- Bloqueos reales (el hito se detiene aquí, no se cruza ninguno):
  1. **`v02` sigue `pendiente_revision`.** Sin SAS en el entorno no se demuestra el tipo que
     `PROC IMPORT` da a las columnas ni el formato de `PROC EXPORT`; el propio caso anota la duda
     del formato `30.` de `NRO_DOC` en la exportación. No se cambia el emisor apoyándose en eso.
  2. **No es el `job_producto` emitido.** Es un Job aislado con tres salidas; falta integrar los
     filtros en `jobs_producto.py` y en el padre, y producir `RECHAZO_NRO_DOC_*` y las tablas de
     conteo como salidas reales (hito 87).
  3. **Parte 2 de R1-04 pendiente**: la regla `Campos vacios` (cadena larga de `IS MISSING` sobre
     19 columnas) no se ha traducido ni ejecutado.
  4. La equivalencia N2 de G4 sigue exigiendo los insumos reales del cliente; aquí se usan las
     entradas simuladas del corpus.
- Decisiones: (a) R1-04 pasa de `pendiente` a **`parcial`**, no a `hecho`: el criterio pide que
  `v02` coincida y eso se demostró, pero con un Job aislado y con el caso aún sin revisión humana.
  (b) No se toca `src/sgm/cli_talend.py`, `jobs_producto.py` ni `decisiones/client_large.jobs.yaml`.
  (c) Los siete archivos nuevos suman 914 líneas, ninguno supera 238; no hay desviación del límite
  de 300 de `AGENTS.md`.
- Pruebas: 33 nuevas (`test_proceso_reglas_fila.py` 10, `test_talend_filtros_fila.py` 11,
  `test_vacios_ceros_datos.py` 12), incluidas las que anclan el esquema de 23 columnas al SAS real,
  las que detectan una sola fila cambiada y un desglose de anomalías equivocado, y las que hacen
  fallar las invariantes a propósito. `uv run pytest -q`: 1708 pasan, 26 se saltan, 132 xfail
  (frente a 1675 del hito 85). `uv run ruff check .`: limpio.
- Nota de infraestructura (falso fallo, no del producto):
  `test_tools_ci.py::test_el_cierre_termina_en_cero_si_todo_pasa` lanza un `pytest -n0` anidado
  para los "cruces del corpus". Tras muchas corridas acumuladas, ese pytest intenta purgar el
  directorio temporal `pytest-of-.../garbage-*` con unos 1 900 archivos y el entorno bloquea el
  borrado masivo (`SAFE_DELETE_BULK_CONFIRM_REQUIRED`): el subproceso muere antes de imprimir el
  resumen y el test marca `FALLA`. Aislado, `tests/unit/test_tools_ci.py` da 7 pasan y los cruces
  dan 78 pasan; con `PYTEST_DEBUG_TEMPROOT` apuntando a una carpeta nueva,
  `uv run python tools/ci.py --sin-suite --sin-tablero` imprime `Todo verde.`. La cifra publicada
  sale de una corrida **sin solape**, en serie y con raíz temporal nueva:
  `PYTEST_DEBUG_TEMPROOT=C:/tmp/sgm-hito86/root3 uv run pytest -q -n0 --basetemp=C:/tmp/sgm-hito86/bt3`,
  que termina con código 0 y `1708 passed, 26 skipped, 132 xfailed in 204.75s`. No se cambió
  `tools/ci.py`: no hay nada que arreglar en el producto, solo se evitó la purga del directorio
  temporal del entorno.
- Métricas del tablero: sin cambios, 27 componentes emitidos, conformidad 12 de 118 filas y 2 de
  22 secciones, 16 pendientes en 5 motivos, 117 casos del corpus. Este hito no añade componentes
  al emisor.
- Riesgo: el arnés escribe CSV sin cabecera con separador coma y compara tuplas ordenadas; los
  esperados sí traen cabecera. `anomalias()` y `_suma_observada()` dependen de la posición de
  `NRO_DOC` (5) y `FIN_SALDO_CTA` (6) en la proyección, declarada en `ESQUEMAS`; si el diseño
  cambia la proyección, hay que actualizar `tools/vacios_ceros_datos.py` antes de reutilizarlo.

## Hito 87. R1-04 (parte 1, cierre en el emisor): los tres flujos salen del `job_producto` emitido

Se cerró el hueco que el hito 86 dejó explícito: ya no es un Job aislado, es el `.item` que
`sgm talend` escribe para `client_large.sas`. La tercera rama del `tReplicate_1` es
`tMap_flujos` con las tres salidas `expressionFilter` y sus tres `tFileOutputDelimited`.

- Cadena nueva: `proceso/reglas_fila.py` ahora lee también el `SELECT` de cada `CREATE TABLE`
  (`columnas`) y expone `flujos_producto()`, que entrega **una** terna canónica con el nombre
  base de cada tabla leído del SAS. `cli_talend.py` la pasa a `job_producto(..., flujos=...)`;
  `talend_item/flujos_fila.py` construye el `tMap`, las salidas y las conexiones;
  `talend_item/totalizadores.py` recibió los helpers de totales y homologación para que
  `jobs_producto.py` baje de 299 a 242 líneas y no rompa el límite de 300 de `AGENTS.md`.
- No se declara nada a mano: las proyecciones, los nombres de archivo y los filtros salen del
  SAS. El Job escribe `NRO_DOC_VACIO_0_TIT_COT_<sufijo>.csv`,
  `INCONS_NRO_DOC_VACIO_0_FA_<sufijo>.csv` y `NRO_DOC_NO_VACIO_NI_0_<sufijo>.csv`, con
  cabecera y `context.sufijo`, igual que las tablas del SAS.
- **Hallazgo de diseño**: el SAS real proyecta **19 columnas** en los tres flujos; `v02` proyecta
  6/6/7. El emisor usa las 19 del programa real. El detector encuentra 10 reglas en el real:
  6 de separación (CTE y AHO, formas idénticas) y 4 revalidaciones posteriores
  (`SABANA_SIN_NRO_DOC_VACIOS_NEQUI`, `FINAL_VALIDAR_NRO_DOC_CTE/NEQUI/AHO`). Como el Job es
  uno solo parametrizado por `context.sufijo`, se emite una sola terna, se **exige** que los dos
  bloques de producto tengan la misma forma y las 4 restantes se publican como `Pendiente:`
  en la salida del CLI, no se descartan en silencio.
- **Salvedad heredada, no ocultada**: el emisor normaliza las 15 columnas numéricas del SAS real
  (hito 84), y en `v02` `TIPO_DOC=TDxx` y `LLAVE_NOMBRE=LLVxxxxx` son texto no numérico;
  `input(..., w.d)` las deja vacías. Es la misma salvedad medida en el hito 85. El arnés de este
  hito compara por **nombre de columna** solo las columnas estables (`RELACION`, `TIPO_CTA`,
  `NRO_CTA`, `NRO_DOC`, `FIN_SALDO_CTA`); `NRO_CTA` es única por fila, así que la igualdad de
  multisets sigue siendo fila por fila. No se rellena ni se transforma el esperado. Cabecera
  real escrita por el Job (se ven las dos columnas vacías):
  ```text
  RELACION,TIPO_CTA,NRO_CTA,LLAVE_NOMBRE,TIPO_DOC,NRO_DOC,GMF,VAL_CRED_MES,NRO_CRED_MES,PROM_CRED_MES,MED_CRED_MES,VAL_DEB_MES,NRO_DEB_MES,PROM_DEB_MES,MED_SALDO_CTA,PROM_SALDO_CTA,MAX_SALDO_CTA,MIN_SALDO_CTA,FIN_SALDO_CTA
  1001,1,5000000001,,,,1,1001,2001,3001,4001,5001,6001,7001,8001,9001,10001,11001,12001
  ```

Evidencia literal en Studio 8.0.1 / `PRJ_BANCOLOMBIA`. Compilación de los 4 Jobs emitidos
(`uv run python tools/validar_en_studio.py tests/fixtures/sas/client/client_large.sas --project
<proyecto> --sufijo v87d --solo-compilar`, código de salida 0):
```text
Compilando hijos: job_conciliacion_v87d, job_producto_v87d, job_totales_v87d
Compilando padre: job_exogena_depositos_v87d
RESULTADO BUILD: {"job_conciliacion_v87d": {"generateMs": 167, "compileMs": 434, "ok": true}, "job_producto_v87d": {"generateMs": 662, "compileMs": 965, "ok": true}, "job_totales_v87d": {"generateMs": 180, "compileMs": 417, "ok": true}, "job_exogena_depositos_v87d": {"generateMs": 683, "compileMs": 630, "ok": true}}
```

Ejecución con datos del **Job emitido** (`tools/prueba_flujos_emitidos.py`, sufijo `v87c`,
JDK `zulu21.../bin`, `.m2` de Studio, entradas `v02`, Excel de homologación de `v01`;
código de salida 0 en las dos corridas):
```text
Código de salida CTE: 0
CTE tit_cot: esperadas 5 filas, obtenidas 5; OK
CTE fa: esperadas 5 filas, obtenidas 5; OK
CTE valido: esperadas 85 filas, obtenidas 85; OK
CTE anomalías plantadas {'tit_cot_vacio': 3, 'tit_cot_cero': 2, 'fa_vacio': 1, 'fa_cero': 4, 'validos': 85}; obtenidas {'tit_cot_vacio': 3, 'tit_cot_cero': 2, 'fa_vacio': 1, 'fa_cero': 4, 'validos': 85}; OK
Código de salida AHO: 0
AHO tit_cot: esperadas 3 filas, obtenidas 3; OK
AHO fa: esperadas 2 filas, obtenidas 2; OK
AHO valido: esperadas 70 filas, obtenidas 70; OK
AHO anomalías plantadas {'tit_cot_vacio': 2, 'tit_cot_cero': 1, 'fa_vacio': 2, 'fa_cero': 0, 'validos': 70}; obtenidas {'tit_cot_vacio': 2, 'tit_cot_cero': 1, 'fa_vacio': 2, 'fa_cero': 0, 'validos': 70}; OK
Invariantes: sábana=válidos+rechazos sí; conteos=15 frente a rechazos=15 sí; suma saldo CTE=1024505 frente a 1024505 sí
RESULTADO: 2 de 2 productos coinciden fila por fila
```
Nota de corrida: `v87b` cayó con `"java" no se reconoce como un comando interno o externo`
(exitCode 1) por no pasar `--java-bin`; con el JDK de Studio las dos corridas dan 0. No es un
fallo del producto.

- Bloqueos reales (ninguno se cruza): `v02` sigue `pendiente_revision` (sin SAS no se demuestra
  el tipo de `PROC IMPORT`, el formato de `PROC EXPORT` ni el formato `30.` de `NRO_DOC`); la
  equivalencia N2 de G4 exige los insumos reales del cliente; el lookup `TIPO_DOC`/Excel sigue
  con la comparación texto/número sin resolver (R1-03, DC-12 de Negocio). Quedan fuera del Job
  la parte 2 de R1-04 (`Campos vacios`), `RECHAZO_NRO_DOC_*` y las tablas de conteo.
- Decisiones: R1-04 sigue **`parcial`**, no `hecho`. Se cierra la parte 1 en el emisor, pero el
  criterio de la fila exige el caso revisado y las salidas completas. No se cambió
  `decisiones/client_large.jobs.yaml`. Los programas pequeños que no declaran la terna no emiten
  flujos a medias: `_flujos()` publica un `Pendiente:` en vez de lanzar una excepción.
- Pruebas: 25 nuevas (`test_proceso_reglas_fila.py` +6, `test_talend_emision_flujos_fila.py` +12,
  `test_prueba_flujos_emitidos.py` +7). Comprueban que los `expressionFilter` del `.item` son
  literalmente los del hito 86, que las proyecciones son las 19 del `SELECT` real, que `v02`
  con 6/6/7 columnas también pasa por el mismo emisor, que falta de normalización/columnas/
  modos produce error, y que el comparador detecta una fila cambiada.
  `uv run pytest -q`: **1733 pasan, 26 se saltan, 132 xfail** (frente a 1708 del hito 86),
  corrida en serie con raíz temporal nueva
  (`PYTEST_DEBUG_TEMPROOT=C:/tmp/sgm-hito87/root uv run pytest -q -n0 --basetemp=C:/tmp/sgm-hito87/bt`,
  216.08s). `uv run ruff check .`: limpio.
- Métricas del tablero: **31 componentes emitidos** (antes 27; `job_producto` pasa de 12 a 16:
  `tMap_flujos` + 3 salidas), conformidad 12 de 118 filas y 2 de 22 secciones, 16 pendientes en
  5 motivos, 117 casos del corpus. `test_tablero.py` se actualizó para fijar el nuevo conteo.
- Re-verificación del cierre con la causa del falso fallo aislada: una corrida con
  `PYTEST_DEBUG_TEMPROOT` apuntando a una carpeta **que no existía** dio `1 failed, 1732 passed` en
  `test_tools_ci.py::test_el_cierre_termina_en_cero_si_todo_pasa`. No es el borrado masivo de
  `garbage-*` del hito 86: el `pytest` anidado de `tools/ci.py` hereda esa variable y crea la raíz
  con un `mkdir` **no recursivo** (`FileNotFoundError [WinError 3]` en
  `pytest-of-USUARIO_BISOLUTION1`), así que los 78 cruces del corpus fallan en el `setup` de la
  fixture `tmp_path`. Con `mkdir -p` previo de la raíz, `uv run python tools/ci.py --sin-suite
  --sin-tablero` imprime `Todo verde.` (ruff, 78 cruces y oráculo OK) y la suite completa repetida
  en serie da **1733 pasan, 26 se saltan, 132 xfail en 216.48s**, código 0. No se modificó
  `tools/ci.py` ni `src/`: es un requisito del entorno, no un defecto del producto.

## Hito 88. R1-06 (parte 1): `v04_tipo_cta_gmf` coincide fila por fila en Studio

Se cerró el siguiente punto del camino crítico (sección 16.2: R1-03 a R1-08). El hito 74 solo
había detectado los `NOT BETWEEN` del SAS real con `proceso/reglas.py`; faltaba traducirlos y
ejecutar el caso con datos. Aquí la separación de cuenta y GMF sale del propio `v04/programa.sas`
y se ejecuta en Studio, con los cuatro flujos comparados contra `esperado/`.

- Cadena nueva: `proceso/reglas_cuenta.py` lee `TIPO_CTA NOT IN ('1'..'5')`, el
  `GMF IS MISSING OR GMF NOT BETWEEN 1 AND 10`, los tres motivos (`CASE` y `OUTER UNION CORR`), el
  `GMF=input(left(GMF_TXT), 3.)`, los ocho alias `VARn AS ...` y las proyecciones de los cuatro
  `CREATE TABLE`. `talend_item/filtros_cuenta.py` las traduce a cuatro salidas de `tMap` con
  `expressionFilter`; `tools/prueba_cuenta_gmf.py` monta el Job aislado y `cuenta_gmf_datos.py`
  compara por nombre de columna. En `normalizacion.py` solo se añadió la función pública
  `numero_valido()` para reutilizar el patrón numérico del oráculo en vez de copiarlo.
- **Semántica demostrada**: el faltante de SAS cuenta como **menor que cualquier número**. El Java
  cortocircuita `null`, `""` y texto no numérico antes de `Double.parseDouble`, así que el `XX`
  plantado cae en el rango inválido con motivo `GMF NO NUMERICO` y el `99` con
  `GMF FUERA DE RANGO`. La lista de tipos de cuenta usa el literal a la izquierda de `equals`
  (R1-01), nunca `row1.TIPO_CTA.equals(...)`.
- **Decisión de traducción, validada por datos**: el `OUTER UNION CORR` de `INCONS_CUENTA` se emite
  como **una sola salida** `cuenta` con un filtro `(!dentro || fuera)` y una `INCONSISTENCIA`
  ternaria, no como dos componentes. Las nueve filas de CTE y las nueve de AHO coinciden fila por
  fila con la tabla esperada.
- **Hallazgo de diseño, no unificado**: el programa real escribe la misma idea de otra forma.
  `client_large.sas` usa `TIPO_CTA NOT BETWEEN 1 AND 5 AND RELACION = 1000` y
  `GMF NOT BETWEEN 1 AND 10 AND RELACION = 1000` con motivos `TIPO CTA INVALIDO` y
  **`CODEX INVALIDO`**; `v04` usa `NOT IN`, un `IS MISSING` explícito, dos motivos para GMF y
  ningún control de `RELACION`. Los rangos 1..5 y 1..10 coinciden (anclado por prueba unitaria
  contra `reglas.py`), pero los motivos no. No se sustituyó una forma por la otra: este hito
  traduce `v04`, y la forma del programa real queda pendiente para la integración en el emisor.
- **Salvedad no ocultada**: se comparan las **tablas** `esperado/*.csv` (con cabecera, coma), no los
  archivos de `esperado/archivos/` (sin cabecera, `;`). Esos archivos son la salida supuesta de
  `PROC EXPORT`, y `caso.yaml` sigue `pendiente_revision` porque el formato `3.` de exportación y
  el tipado de `PROC IMPORT` no están demostrados con SAS.

Evidencia literal en Studio 8.0.1 / `PRJ_BANCOLOMBIA`. Ejecución con datos del Job aislado
(`uv run python tools/prueba_cuenta_gmf.py --proyecto <proyecto> --java-bin <jdk>/bin --m2
<studio>/.m2/repository --sufijo v88a --trabajo C:/tmp/sgm-hito88/v88a`, código de salida 0):
```text
Código de salida CTE: 0
CTE tipo_cta: esperadas 4 filas, obtenidas 4; OK
CTE gmf: esperadas 5 filas, obtenidas 5; OK
CTE valido: esperadas 81 filas, obtenidas 81; OK
CTE cuenta: esperadas 9 filas, obtenidas 9; OK
CTE anomalías plantadas {'tipo_cta_invalido': 4, 'gmf_invalido': 2, 'gmf_fuera_rango': 3, 'validos': 81}; obtenidas {'tipo_cta_invalido': 4, 'gmf_invalido': 2, 'gmf_fuera_rango': 3, 'validos': 81}; OK
Código de salida AHO: 0
AHO tipo_cta: esperadas 6 filas, obtenidas 6; OK
AHO gmf: esperadas 3 filas, obtenidas 3; OK
AHO valido: esperadas 56 filas, obtenidas 56; OK
AHO cuenta: esperadas 9 filas, obtenidas 9; OK
AHO anomalías plantadas {'tipo_cta_invalido': 6, 'gmf_invalido': 1, 'gmf_fuera_rango': 2, 'validos': 56}; obtenidas {'tipo_cta_invalido': 6, 'gmf_invalido': 1, 'gmf_fuera_rango': 2, 'validos': 56}; OK
Limpieza: 2 archivos borrados del proyecto y build temporal borrado
Invariantes: sábana=válidos+rechazos sí; conteo de rechazos=18 frente a 18 sí; conteo de válidos=137 frente a 137 sí
RESULTADO: 2 de 2 productos coinciden fila por fila
```
Fila real escrita por el Job (se ve el GMF vacío del `XX` y el `99` fuera de rango):
```text
RELACION,TIPO_CTA,LLAVE_NOMBRE,GMF,INCONSISTENCIA
9902,9,LLV00001,1,TIPO CTA INVALIDO
1001,5,LLV00005,,GMF NO NUMERICO
1001,2,LLV00007,99,GMF FUERA DE RANGO
```
El emisor no se tocó; aun así se repitió la compilación de los cuatro Jobs que `sgm talend` emite
(`--solo-compilar`, sufijo `v88b`, código de salida 0):
```text
Compilando hijos: job_conciliacion_v88b, job_producto_v88b, job_totales_v88b
Compilando padre: job_exogena_depositos_v88b
RESULTADO BUILD: {"job_conciliacion_v88b": {"generateMs": 158, "compileMs": 509, "ok": true}, "job_producto_v88b": {"generateMs": 987, "compileMs": 938, "ok": true}, "job_totales_v88b": {"generateMs": 210, "compileMs": 414, "ok": true}, "job_exogena_depositos_v88b": {"generateMs": 580, "compileMs": 656, "ok": true}}
```

- Bloqueos reales (ninguno se cruza): `v04` sigue `pendiente_revision` por el formato de
  `PROC EXPORT`/`PROC IMPORT`; la forma del SAS real (`RELACION = 1000`, motivo `CODEX INVALIDO`)
  no está traducida ni integrada en el `job_producto` emitido; la equivalencia N2 de G4 exige los
  insumos reales del cliente; DC-12 (Negocio) sigue abierta. R1-05 (ubicación) y R1-07 (saldos
  negativos) siguen sin arnés con datos.
- Decisiones: R1-06 pasa de `parcial (reglas)` a **`parcial` con evidencia en Studio**, no a
  `hecho`: el criterio pide que `v04` coincida y eso se demostró, pero con un Job aislado, con el
  caso aún sin revisión humana y sin la forma del programa real en el emisor. No se cambió
  `decisiones/client_large.jobs.yaml`, `jobs_producto.py` ni `cli_talend.py`. Un programa que no
  declara la lista, el rango, el `CASE`, el informat o una proyección no emite reglas a medias:
  `reglas_cuenta()` falla.
- Pruebas: **37 nuevas** (`test_proceso_reglas_cuenta.py` 13, `test_talend_filtros_cuenta.py` 10,
  `test_cuenta_gmf_datos.py` 7, `test_prueba_cuenta_gmf.py` 7). Anclan las proyecciones a las
  cabeceras de `esperado/`, comparan los rangos con los del SAS real, comprueban los cuatro
  `expressionFilter` en el `.item` escapado como XML, detectan una sola fila cambiada, un desglose
  equivocado y una invariante rota. `uv run pytest -q`: **1770 pasan, 26 se saltan, 132 xfail**
  (frente a 1733 del hito 87), en serie con raíz temporal creada antes de la corrida
  (`PYTEST_DEBUG_TEMPROOT=C:/tmp/sgm-hito88/root-full ... --basetemp=C:/tmp/sgm-hito88/bt-full`,
  253.52s). `uv run ruff check .`: limpio.
- Métricas del tablero: **sin cambios**, 31 componentes emitidos, conformidad 12 de 118 filas y 2
  de 22 secciones, 16 pendientes en 5 motivos, 117 casos del corpus. Este hito no añade
  componentes al emisor.
- Riesgo: `Double.parseDouble` exige texto numérico; la precondición es que `GMF` venga de
  `as_text(input_left_wd(...))`. El cortocircuito del faltante la garantiza en este Job, pero si
  otro emisor conecta una columna sin normalizar hay que reutilizar `faltante()` antes de parsear.
  El `SELECT DISTINCT` de `SABANA_VALIDA` no se modela: las llaves del caso son únicas, y la
  comparación como multiset es la que lo comprueba.

## Hito 89. R1-06 (parte 2): la forma del SAS real, integrada en el `job_producto` emitido

Se cerró el punto que el hito 88 dejó explícitamente pendiente en la fila R1-06 del plan: el
`client_large.sas` escribe la separación de cuenta/codex con `NOT BETWEEN` + `RELACION = 1000` y
motivo `CODEX INVALIDO`, no con la forma de `v04`. Aquí **no se sustituye una forma por la otra**:
se lee, se traduce y se cuelga del Job real que emite `sgm talend`.

- Cadena nueva: `proceso/reglas_cuenta_real.py` parte de `proceso/reglas.py` (hito 74), exige los
  dos pares CTE/AHO con la misma forma, verifica el control compartido `RELACION = 1000` y los
  motivos del paso `DATA`, y lee por tabla las proyecciones de los `CREATE TABLE`: 19 columnas en
  `INCONS_TIPO_CTA_INVALIDO_*`, `INCONS_CODEX_INVALIDO_*` y `SABANA_CODEX_VALIDO_*`, y esas 19 más
  `INCONSISTENCIA` en `INCONS_PAQ_TIPO_CTA_INV_*` / `INCONS_PAQ_GMF_INV_*`. `SELECT *` de los
  `OUTER UNION CORR` se rechaza en vez de interpretarse como proyección. `cli_talend._cuenta()`
  publica como `Pendiente:` los 29 rangos fuera de la cadena, la consolidación de los `INCONS_PAQ_*`
  y R1-07; si falta cualquier declaración, no emite la rama a medias.
- `talend_item/filtros_cuenta_real.py` traduce los cuatro `expressionFilter`: control con el
  literal a la izquierda (`"1000".equals(cuenta.RELACION)`, R1-01), rango con
  `filtros_cuenta.fuera_de_rango` (el faltante cortocircuita antes de `Double.parseDouble`), y
  **cascada**: `rechazo_codex` niega el rechazo de tipo de cuenta porque el SAS evalúa el codex
  sobre `SABANA_TIPO_CTA_VALIDO_*`. Las filas con `RELACION <> 1000` quedan exentas. El
  `INCONS_CUENTA_*` se consolida en una salida con `INCONSISTENCIA` ternaria, con prioridad del
  motivo de tipo de cuenta. `talend_item/flujos_cuenta_real.py` añade la cuarta rama de
  `tReplicate_1` (`tMap_cuenta` + 4 CSV con cabecera y `context.sufijo`) y exige que `GMF` esté en
  `numericas`, igual que R1-04.
- **Colisión de nombres resuelta**: el Job ya tenía una salida `valido` (R1-04) y la entrada de
  este `tMap` se llama `cuenta`. Las cuatro salidas nuevas se llaman `cta_tipo_cta`, `cta_codex`,
  `cta_valido` y `cta_incons`; se verificó en el `.item` que ninguna repite un `UNIQUE_NAME` de
  conexión ya usado. Los nombres de los CSV son las tablas del SAS real
  (`INCONS_TIPO_CTA_INVALIDO_*`, `INCONS_CODEX_INVALIDO_*`, `SABANA_CODEX_VALIDO_*`,
  `INCONS_CUENTA_*`).
- **Vectores propios**: `v05_codex_saldos` solo planta `codex_invalido` (3 en CTE, 2 en AHO) con
  `TIPO_CTA` válido. Para no declarar cerrado lo que el corpus no ejerce, `cuenta_real_datos.py`
  escribe 8 filas de 23 campos con clasificación esperada escrita a mano: `TIPO_CTA` 9 y `XX`
  fuera de 1..5, `GMF` 99 y faltante, `RELACION = 1001`/`9902` exentas, bordes 1..5 y 1..10, y
  una fila que viola las dos reglas a la vez para comprobar la prioridad del motivo.
- **Salvedad no ocultada**: se comparan `RELACION`, `TIPO_CTA`, `NRO_CTA`, `GMF` y
  `FIN_SALDO_CTA` por nombre de columna (`NRO_CTA` es única, así que el multiset es fila por
  fila). R1-02 normaliza 15 columnas del SAS real, de modo que `TIPO_DOC=TDxx` y
  `LLAVE_NOMBRE=LLVxxxxx` quedan vacías y `NRO_DOC=00000001` pierde los ceros (hito 85/87).
  `SABANA_CODEX_VALIDO_*` **no** se compara con `SABANA_VALIDA_*`: R1-07 no está en el Job, y la
  tercera invariante comprueba justamente que las filas de saldo negativo siguen en el flujo
  válido.

Evidencia literal en Studio 8.0.1 / `PRJ_BANCOLOMBIA`. Ejecución con datos del **`job_producto`
emitido** por `sgm talend` (`uv run python tools/prueba_cuenta_real.py --proyecto <proyecto>
--java-bin <jdk>/bin --m2 <studio>/.m2/repository --sufijo v89a --trabajo
C:/tmp/sgm-hito89/v89a`, código de salida 0):
```text
Código de salida CTE: 0
CTE codex: esperadas 3 filas, obtenidas 3; OK
CTE cuenta: esperadas 3 filas, obtenidas 3; OK
CTE tipo_cta: 0 filas (v05 no planta este rechazo); OK
CTE válidos: 87 + rechazos 3 = 90 frente a sábana 90; OK
CTE anomalías plantadas {'codex_invalido': 3}; obtenidas {'codex_invalido': 3}; OK
Código de salida AHO: 0
AHO codex: esperadas 2 filas, obtenidas 2; OK
AHO cuenta: esperadas 2 filas, obtenidas 2; OK
AHO tipo_cta: 0 filas (v05 no planta este rechazo); OK
AHO válidos: 63 + rechazos 2 = 65 frente a sábana 65; OK
AHO anomalías plantadas {'codex_invalido': 2}; obtenidas {'codex_invalido': 2}; OK
Código de salida VECTORES: 0
Vectores tipo_cta: esperadas 2 filas, obtenidas 2; OK
Vectores codex: esperadas 2 filas, obtenidas 2; OK
Vectores valido: esperadas 4 filas, obtenidas 4; OK
Vectores cuenta: esperadas 4 filas, obtenidas 4; OK
Limpieza: 2 archivos borrados del proyecto y build temporal borrado
Invariantes: sábana=válidos+rechazos sí; codex del corpus=5 frente a 5 sí; saldo negativo sigue en válidos (R1-07 fuera) sí
RESULTADO: 2 de 2 productos coinciden fila por fila; vectores OK
```
Filas reales escritas por el Job para los vectores (se ve el GMF faltante, el `XX` no numérico y
la prioridad de `TIPO CTA INVALIDO` cuando `GMF=11` también está fuera de 1..10):
```text
RELACION,TIPO_CTA,NRO_CTA,GMF,INCONSISTENCIA
1000,9,9000000001,11,TIPO CTA INVALIDO
1000,2,9000000002,99,CODEX INVALIDO
1000,3,9000000003,,CODEX INVALIDO
1000,XX,9000000008,0,TIPO CTA INVALIDO
```
Compilación de los cuatro Jobs que `sgm talend` emite (`--solo-compilar`, sufijo `v89b`, código de
salida 0):
```text
Compilando hijos: job_conciliacion_v89b, job_producto_v89b, job_totales_v89b
Compilando padre: job_exogena_depositos_v89b
RESULTADO BUILD: {"job_conciliacion_v89b": {"generateMs": 228, "compileMs": 1003, "ok": true}, "job_producto_v89b": {"generateMs": 2387, "compileMs": 1814, "ok": true}, "job_totales_v89b": {"generateMs": 415, "compileMs": 698, "ok": true}, "job_exogena_depositos_v89b": {"generateMs": 1455, "compileMs": 890, "ok": true}}
```

- Bloqueos reales (ninguno se cruza): `v05` y `v04` siguen `pendiente_revision` por el formato de
  `PROC EXPORT`/`PROC IMPORT`; 29 reglas de rango del SAS real (NEQUI, `DOC_INCORRECTOS_*`,
  `FINAL_VALIDAR_CTA_Y_GMF_*`), el `INNER JOIN` de `INCONS_PAQ_*` con `OUTER UNION CORR` completo
  y R1-07 (saldos negativos) siguen fuera del Job y se publican como `Pendiente:`; la equivalencia
  N2 de G4 exige los insumos reales del cliente y DC-12 (Negocio) sigue abierta. R1-05 y R1-08
  siguen sin arnés con datos.
- Decisiones: R1-06 sigue **`parcial`**, no `hecho`. Ahora las dos formas están traducidas y
  ejecutadas, y la del programa real vive en el emisor, pero el criterio de la fila pide el caso
  revisado (`pendiente_revision`), las salidas completas y la cadena larga de inconsistencias.
  No se cambió `decisiones/client_large.jobs.yaml`. `job_producto.py` pasa de 242 a 249 líneas:
  la lógica nueva vive en módulos separados para no cruzar el límite de 300 de `AGENTS.md`.
- Pruebas: **40 nuevas** (`test_proceso_reglas_cuenta_real.py` 12,
  `test_talend_filtros_cuenta_real.py` 11, `test_talend_emision_cuenta_real.py` 15,
  `test_cuenta_real_datos.py` 10, `test_prueba_cuenta_real.py` 6; 4 ya existían en el hito 88).
  Se corrigieron dos aserciones con mensajes de error desactualizados y se actualizaron los dos
  conteos fijos del tablero (`test_tablero.py` y `test_talend_emision_flujos_fila.py`). Anclan
  las líneas 3572/3656 del SAS, los siete `RELACION = 1000`, las proyecciones de 19/20 columnas,
  los cuatro `expressionFilter` en el `.item` escapado como XML, la ausencia de colisiones de
  etiquetas, los parámetros del lanzador y la detección de una sola fila o un solo motivo cambiado.
- Métricas del tablero: **36 componentes emitidos** (antes 31; `job_producto` pasa de 16 a 21:
  `tMap_cuenta` + 4 salidas), conformidad 12 de 118 filas y 2 de 22 secciones, 16 pendientes en
  5 motivos, 117 casos del corpus. Los dos tests que fijan el conteo se actualizaron.
- Riesgo: `INCONS_CUENTA_*` es una consolidación **derivada** de los `INCONS_PAQ_*`, no una tabla
  única del SAS; su proyección está anclada a esas tablas, pero el `INNER JOIN` y el `OUTER UNION
  CORR` completos no se modelan. El filtro de `GMF` exige la normalización de R1-02; `_validar()`
  falla si `GMF` no está en `numericas` en vez de emitir un filtro sobre texto crudo.

## Hito 90. R1-07: los saldos negativos del caso v05 coinciden en Studio, dentro del `job_producto` emitido

Se cerró la parte del saldo negativo de la fila R1-07 del plan con la forma que demuestra el caso
`v05_codex_saldos`: `INCONS_SALDO_NEG_<P>` con `WHERE FIN_SALDO_CTA < 0` sobre la sábana entera,
motivo `SALDO NEGATIVO` y `SABANA_VALIDA_<P>` que excluye, con dos `NOT IN`, las llaves de codex y
de saldo. La regla se **lee** del SAS del caso; no se inventa ni se copia del cliente.

- `proceso/reglas_saldo.py` expande las macros del caso por sustitución (`%saldo_negativo(CTE);` y
  `&sufijo.`, con su punto delimitador) y lee, por producto, el `WHERE` (una sola comparación
  `col < n`), el motivo del paso `DATA`, las proyecciones de `INCONS_SALDO_NEG_*` (8 columnas) y de
  `SABANA_VALIDA_*` (9 columnas), y la llave de los dos `NOT IN`. Si falta cualquier pieza, o si los
  productos no coinciden, falla con `ValueError` y no emite nada a medias.
- `talend_item/filtros_saldo.py` traduce `FIN_SALDO_CTA < 0` con el faltante contado como verdadero
  (`faltante` de R1-06 cortocircuita antes de `Double.parseDouble`). La sábana válida es la cuenta
  válida de R1-06 y no negativa.
- `talend_item/flujos_saldo.py` cuelga la quinta rama de `tReplicate_1`: `tMap_saldo` con dos
  salidas, `saldo_neg` y `saldo_valida`, y dos CSV con cabecera y `context.sufijo`
  (`INCONS_SALDO_NEG_<sufijo>.csv`, `SABANA_VALIDA_<sufijo>.csv`). Requiere la cascada de R1-06:
  sin ella no hay sábana válida que calcular y la rama no se emite.
- `jobs_producto.py` recibe `regla_saldo` (el parámetro se llama así porque el Job ya usa `saldo`
  como columna) y `cli_talend.py` lo calcula con `_saldo(texto, cuenta)`.

**Decisiones de este hito** (también en `PROGRESS.md` bajo "Decisiones", no repetidas aquí):

- **El SAS de cliente no rechaza saldos negativos.** En `client_large.sas`, línea 8181, el bloque
  "Eliminar negativos en campo fin_sal_cta" hace `FIN_SALDO_CTA=IFN(FIN_SALDO_CTA<0, 0,
  FIN_SALDO_CTA)` sobre `CONS_SIN_NEG` y lo deja en `CONSOLIDADO_SIN_NEGATIVOS`, que alimenta
  `SUMA_SALDOS_POR_NRO_DOC`. Es una puesta en cero para sumas, no un rechazo, y no hay tabla
  `INCONS_SALDO_NEG_*`. `sgm talend` sobre el cliente no emite la rama y publica `Pendiente:` con
  ese motivo (`negativos_a_cero` lo detecta). No se traduce la puesta en cero a rechazo.
- **Faltante = negativo.** En SAS un faltante es menor que cualquier número
  (`tests/corpus/semantica/vectores.yaml`, `cmp-missing-01`, documentado), así que `< 0` es
  verdadero con faltante. El corpus `v05` no planta un faltante; ese caso lo ejercen solo los
  vectores propios, con clasificación escrita a mano.
- **`-0.00` no es negativo.** `input_left_wd` lo deja en cero (`BigDecimal`), y `0 < 0` es falso.
- **Sin cascada de codex en el rechazo de saldo.** `INCONS_SALDO_NEG_*` sale de la sábana entera,
  como en el SAS. Una fila con codex inválido y saldo negativo sale en las dos tablas. La cascada
  solo entra en `SABANA_VALIDA_*`.
- **Llave por fila.** El `NOT IN` cruza por `LLAVE_NOMBRE` en el SAS. El Job filtra por fila
  porque R1-02 deja `LLAVE_NOMBRE` vacía. La equivalencia exige que la llave sea única; en el
  corpus lo es (`NRO_CTA` también). Queda como pendiente en `reglas_saldo` y como salvedad.
- **Emisión del Job de la prueba.** `v05_codex_saldos` no produce `job_producto` con `sgm talend`:
  su `DETALLE_&sufijo..csv` no se resuelve a un producto (`origenes_producto` lo reporta como no
  asignado) y no tiene decisiones propias. `tools/prueba_saldo.py` emite el `job_producto` con la
  misma función que `sgm talend` (`job_producto` más `origenes_producto` del cliente, sus decisiones,
  `_cuenta` y `_flujos` de `cli_talend`) y le pasa la regla leída de `v05`. Eso es una combinación
  deliberada y se declara aquí; el Job no sale de un programa único.
- **Validación en Studio sin SUMA del Job.** `SUMA_SALDO_VALIDA_*` se recalcula en Python (`Decimal`)
  sobre el `SABANA_VALIDA_*` que escribió el Job y se compara con el esperado. El Job no tiene un
  `tAggregateRow` de saldo válido en esta rama.

Evidencia literal en Studio 8.0.1 / `PRJ_BANCOLOMBIA` (`uv run python tools/prueba_saldo.py
--proyecto "C:/Talend/8.0.1/studio/workspace/talendbancolombia-963626413/PRJ_BANCOLOMBIA"
--java-bin "C:/Talend/8.0.1/zulu21.50.19-ca-jdk21.0.11-win_x64/bin" --m2
"C:/Talend/8.0.1/studio/configuration/.m2/repository" --sufijo v90a --trabajo
"C:/tmp/sgm-hito90/v90a"`, código de salida 0):

```text
Proyecto: C:\Talend\8.0.1\studio\workspace\talendbancolombia-963626413\PRJ_BANCOLOMBIA
Sufijo: v90a
Trabajo: C:\tmp\sgm-hito90\v90a
Pendiente: R1-07: el cruce de SABANA_VALIDA_* con la llave LLAVE_NOMBRE es un filtro por fila en el Job; la equivalencia del NOT IN depende de que la llave sea única por fila
Comando CTE: "C:\Users\USUARI~1\AppData\Local\Temp\build-m5x70v9q\job_producto_v90a\job_producto_v90a_run.bat" --context="Default" --context_param "producto=CTE" --context_param "ruta_origen=C:/Users/USUARIO_BISOLUTION1/code/sgm-v2/tests/corpus/L8/validaciones/v05_codex_saldos/entradas/DETALLE_CTE.csv" --context_param "sufijo=CTE" --context_param "periodo_anio=2026" --context_param "periodo_mes=10" --context_param "periodo_dia=01" --context_param "arch_hom_tipo_doc=Homologacion_tpo_dto.xlsx" --context_param "ruta_insumos=C:/Users/USUARIO_BISOLUTION1/code/sgm-v2/tests/corpus/L8/validaciones/v01_tipo_doc/entradas/" --context_param "hoja_excel=Sheet1" --context_param "ruta_resultados=C:/tmp/sgm-hito90/v90a/salida/"
Código de salida CTE: 0
CTE neg: esperadas 4 filas, obtenidas 4; OK
CTE valida: esperadas 83 filas, obtenidas 83; OK
CTE suma valida: esperada 1000067, obtenida 1000067; OK
CTE anomalías plantadas {'saldo_negativo': 4, 'validos': 83}; obtenidas {'saldo_negativo': 4, 'validos': 83}; OK
Comando AHO: "C:\Users\USUARI~1\AppData\Local\Temp\build-m5x70v9q\job_producto_v90a\job_producto_v90a_run.bat" --context="Default" --context_param "producto=AHO" --context_param "ruta_origen=C:/Users/USUARIO_BISOLUTION1/code/sgm-v2/tests/corpus/L8/validaciones/v05_codex_saldos/entradas/DETALLE_AHO.csv" --context_param "sufijo=AHO" --context_param "periodo_anio=2026" --context_param "periodo_mes=10" --context_param "periodo_dia=01" --context_param "arch_hom_tipo_doc=Homologacion_tpo_dto.xlsx" --context_param "ruta_insumos=C:/Users/USUARIO_BISOLUTION1/code/sgm-v2/tests/corpus/L8/validaciones/v01_tipo_doc/entradas/" --context_param "hoja_excel=Sheet1" --context_param "ruta_resultados=C:/tmp/sgm-hito90/v90a/salida/"
Código de salida AHO: 0
AHO neg: esperadas 5 filas, obtenidas 5; OK
AHO valida: esperadas 58 filas, obtenidas 58; OK
AHO suma valida: esperada 698117, obtenida 698117; OK
AHO anomalías plantadas {'saldo_negativo': 5, 'validos': 58}; obtenidas {'saldo_negativo': 5, 'validos': 58}; OK
Comando VECTORES: "C:\Users\USUARI~1\AppData\Local\Temp\build-m5x70v9q\job_producto_v90a\job_producto_v90a_run.bat" --context="Default" --context_param "producto=VECTORES" --context_param "ruta_origen=C:/tmp/sgm-hito90/v90a/DETALLE_VECTORES.csv" --context_param "sufijo=VECTORES" --context_param "periodo_anio=2026" --context_param "periodo_mes=10" --context_param "periodo_dia=01" --context_param "arch_hom_tipo_doc=Homologacion_tpo_dto.xlsx" --context_param "ruta_insumos=C:/Users/USUARIO_BISOLUTION1/code/sgm-v2/tests/corpus/L8/validaciones/v01_tipo_doc/entradas/" --context_param "hoja_excel=Sheet1" --context_param "ruta_resultados=C:/tmp/sgm-hito90/v90a/salida/"
Código de salida VECTORES: 0
Vectores neg: esperadas 7 filas, obtenidas 7; OK
Vectores valida: esperadas 6 filas, obtenidas 6; OK
Vectores invariante: válidos 6 + rechazos 9 = 15 frente a 15; OK
Limpieza: 2 archivos borrados del proyecto y build temporal borrado
CTE invariante sábana: válidos 83 + rechazos 7 = 90 frente a 90; OK
AHO invariante sábana: válidos 58 + rechazos 7 = 65 frente a 65; OK
RESULTADO: 2 de 2 productos coinciden fila por fila; vectores OK
```

Filas que escribió el Job en los vectores propios (`INCONS_SALDO_NEG_VECTORES.csv`, columnas
estables; `LLAVE_NOMBRE` y `TIPO_DOC` vacías por R1-02):

```text
RELACION,TIPO_CTA,NRO_CTA,LLAVE_NOMBRE,TIPO_DOC,NRO_DOC,GMF,FIN_SALDO_CTA,INCONSISTENCIA
1000,1,9000000101,,,1,1,-1,SALDO NEGATIVO
1000,1,9000000104,,,1,1,,SALDO NEGATIVO
1000,1,9000000106,,,1,1,-0.01,SALDO NEGATIVO
1000,1,9000000108,,,1,99,-5,SALDO NEGATIVO
1001,1,9000000109,,,1,99,-3,SALDO NEGATIVO
1000,9,9000000111,,,1,1,-7,SALDO NEGATIVO
1000,5,9000000114,,,1,5,-12345678901234,SALDO NEGATIVO
```

Lectura de la evidencia: la fila `9000000104` es el faltante (saldo vacío) y entra como negativo;
`9000000108` es codex por GMF 99 y saldo negativo, y sale en las dos tablas; `9000000102`
(saldo `0`), `9000000105` (`-0.00`, que sale como `0.00`) y `9000000103` (`0.01`) quedan en la
sábana válida.

- **Qué no demuestra.** La regla viene del caso `v05`, que está en `pendiente_revision`: no se
  demuestra con SAS que `input()` lea el negativo ni el formato de `PROC EXPORT`. El Job coincide
  con el esperado del caso, no con la ejecución de SAS. El faltante y `-0.00` se demuestran solo
  con los vectores propios, cuya clasificación es semántica de SAS escrita a mano, no un caso del
  corpus.
- **Bloqueos reales.** R1-07 sigue **`parcial`**. El saldo negativo del caso `v05` está traducido y
  coincide. El cliente no se cubre: su SAS pone en cero (no rechaza), así que la separación de
  saldo de `client_large.sas` no existe como regla. Los demás campos negativos del cliente
  (`VAL_CRED_MES` con `IFN`, `INCONS_DEP_CAMPOS_NEGATIVOS_CTE/AHO`, y `negativos corriente` /
  `negativos ahorros` del bloque de exógena) siguen sin traducir. El `NOT IN` por llave se traduce
  por fila, con la salvedad de llave única.
- **Pruebas.** 39 nuevas en cuatro archivos: `test_proceso_reglas_saldo.py` (11),
  `test_talend_filtros_saldo.py` (8), `test_talend_emision_saldo.py` (11) y `test_saldo_datos.py`
  (9). Anclan la lectura de v05, el rechazo de cada pieza que falte o cambie (un `<=`, un
  `NOT IN` quitado, un motivo cambiado, un producto sin tabla), las expresiones con faltante primero,
  la emisión con 24 nodos (21 de antes más 3) y 21 nodos sin la regla en el cliente, y que los
  comparadores detectan una fila cambiada.
- **Suite**: `uv run pytest -q -n auto`: 1863 pasadas, 26 omitidas y 132 `xfail`. `uv run ruff check .`:
  sin errores. `tests/unit/test_tablero.py` no cambió: el Job del cliente no emite
  la rama, así que sigue en 36 componentes emitidos y 21 nodos en `job_producto`.
- **Métricas.** Archivos nuevos: `proceso/reglas_saldo.py` (206 líneas), `talend_item/filtros_saldo.py`
  (76), `talend_item/flujos_saldo.py` (95), `tools/saldo_datos.py` (268), `tools/prueba_saldo.py`
  (207). `jobs_producto.py` pasa de 253 a 261 líneas, `cli_talend.py` de 165 a 182.
- **Salvedad de llave.** Los `NOT IN` y las proyecciones se cruzan por nombre. R1-02 deja
  `LLAVE_NOMBRE` y `TIPO_DOC` vacías y quita ceros de `NRO_DOC` (hitos 85 y 87), así que la
  comparación usa `NRO_CTA` (única) y las cinco columnas estables del hito 89.

## Hito 91. R1-05: la ubicación del caso v03 coincide en Studio, dentro del `job_producto` emitido

- Fecha: 2026-11-05
- Qué se hizo: la regla de ubicación se **lee** del caso `v03_pais_dane/programa.sas` y se cuelga
  del `job_producto` emitido por `sgm talend`, con el mismo patrón de R1-06 y R1-07.
  - `proceso/reglas_ubicacion.py` (131 líneas) y `proceso/reglas_ubicacion_forma.py` (214, la
    forma de cada pieza: `LEFT JOIN`, cinco alternativas del `WHERE`, ramas del `CASE`, `NOT IN`,
    proyecciones). Si una pieza no tiene su forma, falla con `ValueError`. Lee los dos Excel
    (`Cod_pais.xlsx` por `Codigo_Pais`, `CODIGOS_DANE.xlsx` por `CODIGO_DANE`) desde los
    `PROC IMPORT`, y comprueba que los dos productos declaran la misma regla.
  - `talend_item/filtros_ubicacion.py` (143): expresiones Java del `tMap`. Las cinco alternativas
    del `WHERE` y las cuatro ramas del `CASE` salen de la misma definición, así que el rechazo y el
    motivo no pueden desviarse.
  - `talend_item/flujos_ubicacion.py` (136): `tMap_ubicacion` con dos lookups Excel en `LEFT JOIN`
    (`tFileInputExcel_ubic_pais`, `tFileInputExcel_ubic_dane`), dos salidas (`ubic_rechazo` con
    `INCONSISTENCIA`, `ubic_valida`) y dos CSV con cabecera y `context.sufijo`.
  - `jobs_producto.py` (261 a 277) recibe `ubicacion`; `cli_talend.py` (182 a 196) lo calcula con
    `_ubicacion(texto)`, igual que `_saldo`.
  - `tools/ubicacion_datos.py` (281) y `tools/prueba_ubicacion.py` (243): vectores propios, unión
    de sábana y ubicación por llave, y el protocolo de Studio.

- Regla leída de `v03` (no inventada):
  - Rechazo: `WHERE` con cinco alternativas. (1) `Codigo_Pais IS MISSING`. (2) `PAIS = '900' AND
    CODIGO_DANE IS MISSING`. (3) `PAIS <> '900' AND CODIGO_UBICACION IS NOT MISSING`. (4)
    `LENGTH(DIRECCION) < 8`. (5) `UPPER(DIRECCION) CONTAINS UPPER('sin dir')`.
  - Motivos del `CASE`, en orden: `PAIS NO HOMOLOGADO`, `DANE NO HOMOLOGADO`, `UBICACION EXTRANJERA
    CON CODIGO` y, en el `ELSE`, `DIRECCION INVALIDA`.
  - Válidos: `LLAVE_NOMBRE NOT IN` la tabla de rechazo.

- Traducción de las funciones que el oráculo SQL no cubre (regla Java exacta):
  - **Blancos finales** (`recortado`): `expr.replaceAll(" +$", "")`. Un nulo da `""`. En SAS los
    blancos finales no cuentan en una comparación, así que `'900 '` es igual a `'900'`.
  - **Faltante** (`faltante`): el texto sin blancos finales está vacío. En SAS un texto en blanco es
    faltante y es igual a `''`.
  - **LENGTH** (`longitud`): sin blancos finales; un texto en blanco vale **1**, igual que el
    faltante: `t.isEmpty() ? 1 : t.length()`.
  - **CONTAINS** (`mayusculas` y `.contains`): subcadena literal sobre `toUpperCase(Locale.ROOT)`.
    `'SIN  DIR'` (dos blancos) no contiene `'SIN DIR'`: ninguna compresión de blancos.
  - **COMPBL** no aparece en `v03`. No se traduce ni se demuestra; la compresión de blancos de
    R1-02 (`normalizacion.compbl`) no entra en esta rama.
  - **Literal a la izquierda** en cada `equals` (`"900".equals(...)`). Con el lookup, `== null` sobre
    la columna del lookup es el caso de "sin pareja" del `LEFT JOIN`.

- Decisiones:
  - **Unión por llave fuera del Job.** `SABANA_UBIC` (sábana `LEFT JOIN` ubicación por
    `LLAVE_NOMBRE`) la hace el arnés (`ubicacion_datos.unir`) antes de correr el Job. La razón es
    que R1-02 deja `LLAVE_NOMBRE` vacía (hitos 85 y 87): en el Job no habría clave con la que unir.
    El Job recibe `PAIS`, `CODIGO_UBICACION` y `DIRECCION` como columnas de la sábana, y la regla
    de rechazo es por fila, que es lo que el SAS hace después de la unión.
  - **Cliente sin rama.** `reglas_ubicacion(client_large.sas)` falla (`INCONS_UBICACION_INVALIDA_AHO`
    no tiene la forma del caso) y `sgm talend` publica `Pendiente:`. El SAS de cliente rechaza con
    `'169'` y un solo motivo (`CAMPOS DE UBICACION INCORRECTOS`), y sus variantes Impala corrigen
    valores (`SABANA_CORREGIR_UBICACION`) en vez de rechazar. Esa forma no se traduce aquí.
  - **Lookups en LEFT JOIN** (`union_interna` falso): una fila sin pareja sigue, con el lookup en
    nulo. La regla de DANE solo aplica con `PAIS = '900'`, como en el SAS.
  - **Los Excel se comparan como texto.** `caso.yaml` declara que el tipo de `Codigo_Pais` y de
    `CODIGO_DANE` es texto según la convención del corpus, no según SAS (sin SAS no está
    demostrado). Además, la normalización de `Codigo_Pais` con `input(left(...), 10.)` quita
    ceros: `01` queda `1`. En `v03` no hay códigos con ceros; la diferencia queda como pendiente.
  - **Nombres de conexión.** `ubic_fuente`, `ubic_pais`, `ubic_dane`, `ubic_rechazo` y `ubic_valida`:
    no repiten ninguno de R1-04, R1-06 ni R1-07 (`valido`, `cta_*`, `saldo_*`).
  - **Parámetros.** `arch_hom_pais` y `arch_hom_dane` se suman al contexto con el nombre del SAS
    como valor por omisión. El arnés pasa `ruta_insumos` con las entradas de `v03`, así que no usa
    `Homologacion_tpo_dto.xlsx` y emite el Job sin la validación de tipo de documento (`validacion`
    en `None`); eso no cambia la rama de ubicación, que sale de `tReplicate_1`.

- Evidencia literal en Studio 8.0.1 / `PRJ_BANCOLOMBIA`. Corrida completa (`uv run python
  tools/prueba_ubicacion.py --proyecto "C:/Talend/8.0.1/studio/workspace/talendbancolombia-963626413/PRJ_BANCOLOMBIA"
  --java-bin "C:/Talend/8.0.1/zulu21.50.19-ca-jdk21.0.11-win_x64/bin" --m2
  "C:/Talend/8.0.1/studio/configuration/.m2/repository" --sufijo v91b --trabajo
  "C:/tmp/sgm-hito91/v91b"`, código de salida 0). Las líneas `Comando` se truncaron a 400 columnas en
  la tubería que guardó la salida; el resto es literal:

```text
Proyecto: C:\Talend\8.0.1\studio\workspace\talendbancolombia-963626413\PRJ_BANCOLOMBIA
Sufijo: v91b
Trabajo: C:\tmp\sgm-hito91\v91b
Pendiente: R1-05: `Codigo_Pais` pasa por `input()` y quita ceros a la izquierda; el Job compara como texto (sin códigos con ceros en el caso)
Pendiente: R1-05: el `CASE` de PROC SQL fija la longitud de INCONSISTENCIA con su primera rama; el SAS del caso no se ejecutó, y el Job no trunca
Pendiente: R1-05: la unión SABANA_UBIC por LLAVE_NOMBRE no está en el Job; R1-02 deja la llave vacía
Unión CTE: 0 llaves sin ubicación (LEFT JOIN)
Unión AHO: 0 llaves sin ubicación (LEFT JOIN)
Comando CTE: "C:\Users\USUARI~1\AppData\Local\Temp\build-6v11x_a2\job_producto_v91b\job_producto_v91b_run.bat" --context="Default" --context_param "producto=CTE" --context_param "ruta_origen=C:/tmp/sgm-hito91/v91b/DETALLE_CTE_UBIC.csv" --context_param "sufijo=CTE" --context_param "periodo_anio=2026" --context_param "periodo_mes=10" --context_param "periodo_dia=01" --context_param "ruta_insumos=C:/
Código de salida CTE: 0
CTE rechazo: esperadas 8 filas, obtenidas 8; OK
CTE valida: esperadas 80 filas, obtenidas 80; OK
CTE anomalías plantadas {'pais_no_homologado': 2, 'dane_no_homologado': 3, 'ubicacion_extranjera_con_codigo': 1, 'direccion_invalida': 2, 'validos': 80}; obtenidas {'pais_no_homologado': 2, 'dane_no_homologado': 3, 'ubicacion_extranjera_con_codigo': 1, 'direccion_invalida': 2, 'validos': 80}; OK
Comando AHO: "C:\Users\USUARI~1\AppData\Local\Temp\build-6v11x_a2\job_producto_v91b\job_producto_v91b_run.bat" --context="Default" --context_param "producto=AHO" --context_param "ruta_origen=C:/tmp/sgm-hito91/v91b/DETALLE_AHO_UBIC.csv" --context_param "sufijo=AHO" --context_param "periodo_anio=2026" --context_param "periodo_mes=10" --context_param "periodo_dia=01" --context_param "ruta_insumos=C:/
Código de salida AHO: 0
AHO rechazo: esperadas 5 filas, obtenidas 5; OK
AHO valida: esperadas 55 filas, obtenidas 55; OK
AHO anomalías plantadas {'pais_no_homologado': 1, 'dane_no_homologado': 2, 'ubicacion_extranjera_con_codigo': 1, 'direccion_invalida': 1, 'validos': 55}; obtenidas {'pais_no_homologado': 1, 'dane_no_homologado': 2, 'ubicacion_extranjera_con_codigo': 1, 'direccion_invalida': 1, 'validos': 55}; OK
Comando VECTORES: "C:\Users\USUARI~1\AppData\Local\Temp\build-6v11x_a2\job_producto_v91b\job_producto_v91b_run.bat" --context="Default" --context_param "producto=VECTORES" --context_param "ruta_origen=C:/tmp/sgm-hito91/v91b/DETALLE_VECTORES.csv" --context_param "sufijo=VECTORES" --context_param "periodo_anio=2026" --context_param "periodo_mes=10" --context_param "periodo_dia=01" --context_param "r
Código de salida VECTORES: 0
Vectores rechazo: esperadas 14 filas, obtenidas 14; OK
Vectores valida: esperadas 6 filas, obtenidas 6; OK
Limpieza: 2 archivos borrados del proyecto y build temporal borrado
CTE invariante sábana: rechazos 8 + válidos 80 = 88 frente a 88; OK
AHO invariante sábana: rechazos 5 + válidos 55 = 60 frente a 60; OK
RESULTADO: 2 de 2 productos coinciden fila por fila; vectores OK
```

- Filas que escribió el Job (columnas de salida tal cual, con sus blancos finales):

```text
INCONS_UBICACION_VECTORES.csv
,1001,,10,900,99003,ABCDEFG,DIRECCION INVALIDA
,1001,,12,900,99003,ABCDEFG   ,DIRECCION INVALIDA
,1001,,17,900,,,DANE NO HOMOLOGADO
UBIC_VALIDA_VECTORES.csv
,1001,,3,900 ,99001,CALLE VALIDA 1 2 3
,1001,,6,900,99002  ,CALLE VALIDA 1 2 3
,1001,,9,902,   ,CALLE VALIDA 1 2 3
```

  Las columnas `LLAVE_NOMBRE` y `TIPO_DOC` salen vacías y `NRO_DOC` sin ceros a la izquierda (R1-02,
  hitos 85 y 87); por eso no entran en la comparación.

- Primera corrida (`v91a`): el Job de CTE salió con código 0 y escribió los CSV, pero el arnés
  falló al leer la cabecera (separador `,` frente a `;`, error del propio arnés, no del Job). Se
  comprobó CTE sin Studio sobre esos mismos archivos (`informe CTE = True`) y se corrigió el
  arnés. La corrida que vale es `v91b`, completa.

- Comprobación sin Studio, antes de la corrida: el oráculo Python (`ubicacion_datos.clasificar_sas`)
  reproduce el esperado del caso en las 148 filas de CTE y AHO, y coincide con la clasificación a
  mano de los 20 vectores.

- Pruebas: **46 nuevas**. `test_proceso_reglas_ubicacion.py` (15): lee productos, motivos, literal,
  umbral, Excel, proyecciones y pendientes; rechaza cada pieza quitada o cambiada (WHERE, CASE,
  ELSE, LEFT JOIN, literal, NOT IN) y rechaza el SAS de cliente. `test_talend_filtros_ubicacion.py`
  (13): forma de cada expresión (literal a la izquierda, blancos finales, `LENGTH` con 1,
  `CONTAINS` en mayúsculas neutras, orden de motivos, rechazo y válido complementarios).
  `test_talend_emision_ubicacion.py` (9): el cliente no emite la rama y publica el pendiente; con la
  regla añade 5 componentes, `ubic_*` sin repetir y tres lookups de LEFT JOIN; falla sin la columna
  `DIRECCION`; el Job sin regla no cambia. `test_ubicacion_datos.py` (9): vectores a mano contra el
  oráculo, bordes pedidos, oráculo contra el esperado del caso fila por fila (CTE y AHO), unión y
  llave repetida, forma de los CSV de vectores.
- Suite: `uv run pytest -q -n auto`: **1909 pasadas, 26 omitidas y 132 `xfail`** (antes 1863; las
  46 nuevas). `uv run ruff check .`: sin errores.
- Tablero: `tests/unit/test_tablero.py` **no cambió**. El `job_producto` del cliente sigue en 21
  nodos porque la rama no se emite. `sgm talend` sobre el cliente imprime una línea más de
  `Pendiente:` (la de la ubicación no emitida).
- Métricas: `jobs_producto.py` 261 a 277 líneas; `cli_talend.py` 182 a 196. Ningún archivo nuevo
  pasa de 300 líneas: el lector se partió en dos módulos por eso.

- **Bloqueos reales** (ninguno se cruza con esta fila):
  - `v03` sigue `pendiente_revision` en el caso: sin SAS no se demuestra el formato de `PROC
    EXPORT`, el tipo que `PROC IMPORT` da a `PAIS` (texto frente a numérico) ni el truncamiento del
    `CASE`. El Job coincide con el esperado del caso, no con una ejecución de SAS.
  - La unión por `LLAVE_NOMBRE` no está en el Job; el arnés la hace. Para llevarla al Job hay que
    corregir R1-02 para que `LLAVE_NOMBRE` no se vacíe (hitos 85 y 87).
  - El SAS de cliente tiene una regla distinta (`'169'`, motivo único, correcciones en Impala). Hasta
    que se traduzca, el Job del cliente no tiene ubicación.
  - `Codigo_Pais` con `input()` quita ceros: no se traduce el `input()` del Excel de país.
  - Las llaves de los Excel se comparan sin blancos finales (el lado del lookup no se recorta);
    `UNIQUE_MATCH` toma la primera pareja si una llave se repite, y el SAS duplicaría la fila. En los
    datos del caso no hay llaves repetidas.
- Salvedad no ocultada: el lado del Excel no se recorta. Si una clave del Excel traía blancos
  finales no casaría con la sábana recortada. El caso no tiene ese Excel; solo los vectores de la
  sábana (`'900 '`, `'99002  '`, `'   '`) ejercen los blancos finales, no los del Excel.
- R1-05 sigue **`parcial`**. El criterio se cumple para `v03`: la regla se lee, su parte de `LENGTH`
  y `CONTAINS` está en Java documentado, y el caso coincide fila por fila en Studio. No se cumple
  para el cliente, y `COMPBL` no aparece en el caso.

## Hito 93. R5-03: `sgm conformidad`, la medida reproducible de "se parece al diseño manual"

- Fecha: 5 de noviembre de 2026. Tarea R5-03 de `docs/plan-reescritura/ruta-a-produccion.md`.
- Qué se hizo:
  - Módulo nuevo `src/sgm/conformidad/`: `referencia.py` (carga de la referencia YAML, movida desde
    `tests/conformidad/cargador.py`), `estado.py` (estado de cada fila y comparador
    `diferencias_fila`) e `informe.py` (conteos, porcentaje, texto y JSON).
  - Comando `sgm conformidad <programa.sas> [--decisiones carpeta] [--formato texto|json]` en
    `src/sgm/cli_conformidad.py`, registrado en `src/sgm/cli.py` con dos líneas. Sigue el modelo de
    `cli_proceso.py`.
  - El emisor reporta el origen de cada fila de las secciones 1.1 y 1.4 (`sas` o `declarada`) en
    `DocumentoDiseno.origenes`, en un campo aparte. Las filas no cambian, así que el Markdown de
    `sgm proceso` tampoco.
  - Las pruebas de `tests/conformidad` ya no tienen copia del cargador ni del comparador: importan
    de `sgm.conformidad`. Ninguna prueba cambió de expectativa.
- Estados por fila, en este orden:
  - `pendiente`: la sección no la emite el migrador, o la fila es `humana` (requiere una persona).
  - `diferente`: el migrador da otro valor (el motivo nombra la columna) o la fila está en
    `DIFERENCIAS_CONOCIDAS` (F04).
  - `derivada`: coincide con el manual, es `derivable` y el SAS demuestra su valor (origen `sas`).
  - `declarada`: coincide, pero el valor sale de `decisiones/`, no del SAS.
- Salida literal de `uv run sgm conformidad tests/fixtures/sas/client/client_large.sas` (hito 93):

```
Conformidad de client_large.sas contra el diseño manual (118 filas)
  derivadas:  5
  declaradas: 7
  pendientes: 105
  diferencias: 1
  porcentaje derivado: 4.2 %
Diferencias con motivo:
  F04 (sección 1.1, Códigos DANE): el SAS sí lee CODIGOS_DANE.xlsx; el manual lo daba por pendiente (el migrador halla más)
```

- Línea base medida: **5 derivadas de 118 filas (4,2 %)**: F01, F02, F03 y F05 (sección 1.1) y
  S03 (sección 1.4). Las 7 declaradas y las 105 pendientes son el resto. Una diferencia: F04.
- Cifras del encargo corregidas con la medida: `tests/conformidad` tiene 168 casos (42 que pasan y
  126 `xfail`), pero no son 168 filas. Incluyen las pruebas de sección. La referencia tiene 118
  filas. Las 42 que pasan no son 42 filas derivadas.
- Pruebas nuevas (20): `tests/unit/test_conformidad_estado.py` (11, con referencias a mano),
  `tests/unit/test_conformidad_cli.py` (6, con el programa pequeño de `tests/fixtures/conformidad/`
  y sus decisiones) y `tests/conformidad/test_linea_base.py` (3, fija 118 filas, las 5 derivadas y
  la diferencia F04 sobre `client_large.sas`).
- Suite: `uv run pytest -q -n auto`: **1929 pasadas, 26 omitidas y 132 `xfail`**. `uv run ruff check .`:
  sin errores. Salida determinista: dos corridas en JSON son idénticas (verificado).
- Tamaño: ningún archivo nuevo pasa de 110 líneas; `src/sgm/cli.py` queda en 292.
- Decisiones:
  - El porcentaje es derivadas entre el total de filas de la referencia.
  - `DIFERENCIAS_CONOCIDAS` se movió a `src/sgm/conformidad/estado.py`. `tools/tablero.py` la sigue
    leyendo desde `tests/conformidad/test_conformidad.py`, que la importa de ahí; no hubo que tocarlo.
  - El origen va en un campo aparte (`origenes`) y no como columna de la fila, para no cambiar las
    tablas del Markdown.
- Salvedades no ocultadas:
  - Una fila derivada prueba que el SAS demuestra la fuente o la salida, no todo su texto. En 1.1,
    `tipo` puede venir del SAS, pero `ubicacion` y `uso` siguen en `decisiones/`. Se mide por
    fila entera; la salvedad queda escrita aquí.
  - S03 se deriva por la regla `^TOTAL_` sobre los nombres de archivo del SAS. No se contrastó con
    una ejecución de SAS.
  - El programa pequeño no tiene macros: el modelo de flujo no lee el código dentro de `%macro`.
    Esto ya era así en el emisor; no se corrigió aquí.
- No verificado: Talend Studio no se usó (no hace falta para esta medida). No se ejecutó ningún
  Job. La cifra de derivadas es la del emisor actual; cambiará cuando el emisor produzca más filas.

## Hito 92. R1-12 (parte 1): lectura de `NODUPKEY` y oráculo de duplicados; la prueba en Studio queda bloqueada

- Fecha: 2026-11-05
- Qué se hizo: `proceso/reglas_duplicados.py` lee las sentencias `PROC SORT ... NODUPKEY` (`DATA=`, `OUT=`, `BY`) y publica como `Pendiente:` lo que no demuestra (`NODUPREC`, `NOEQUALS`, `DESCENDING`); falla con `ValueError` si falta `DATA=`, `OUT=` o `BY`. `tools/duplicados_datos.py` trae un oráculo en Python (recorte de blancos finales, faltante igual a vacío, sensible a mayúsculas, primera fila por llave) y seis grupos de vectores escritos a mano.
- Hechos demostrados sin Studio: el oráculo reproduce `L8/totales/01/esperado/AHO_UNICOS.csv` (40 filas, 7 repetidas de 47). `client_large.sas` tiene 31 `NODUPKEY`: 30 son utilidades de listado de biblioteca y la de negocio está en la línea 15817 (`SABANA_COMPLETA_INFO_CLI_NEQUI` a `SABANA_DIR_UNICA_NEQUI`, `BY NRO_DOC NRO_CTA`). La sábana AHO usa `PROC SQL DISTINCT`, no `NODUPKEY`. Ningún `NODUPKEY` del corpus usa `NOEQUALS`.
- Bloqueo: Studio tiene abierto el diálogo modal "Network Issue Occured" (Reintentar / No) y rechaza compilar y editar nodos. Sin él no se puede crear la plantilla `tUniqRow` ni ejecutar. Hace falta que una persona lo cierre en Studio.
- Sigue pendiente (R1-12 y R6-03 quedan `parcial`): plantilla `tUniqRow.json`, `flujos_duplicados.py`, `tools/prueba_duplicados.py`, integración en `job_producto` y ejecución con comparación contra `esperado/`. Supuestos sin demostrar: que `tUniqRow` conserve la primera fila que llega y que recortar la llave en un `tMap` previo baste.
- Plan: se corrige la línea base de conformidad. `sgm conformidad` (hito 93) mide 5 filas derivadas de 118, no "42 de 168" (esos eran casos de prueba); la meta de R5-04 y de G3 pasa a derivadas 60 o más y derivadas más declaradas 100 o más.
- Pruebas: `test_proceso_reglas_duplicados.py` (10).

## Hito 94. R5-01: `sgm proceso` emite las secciones 2.1 y 5; `sgm conformidad` pasa de 5 a 9 filas derivadas

- Fecha: 2026-11-05. Tarea R5-01 de `docs/plan-reescritura/ruta-a-produccion.md` (parcial). Mueve R5-04 (parcial).
- Qué se hizo:
  - `src/sgm/proceso/secciones_parametros.py`: sección 2.1 (parámetros de ruta y de archivo). Cada parámetro declarado en `decisiones/client_large.diseno.yaml` (clave `parametros`, con `busca` sobre las fuentes del SAS, o sobre sus salidas con `desde: salidas`) toma el valor de la ruta que el SAS demuestra: su nombre de archivo, o su carpeta con `valor: directorio`. La carpeta solo se emite si todas las rutas casadas están en la misma. Sin hallazgo, el parámetro no se emite.
  - `src/sgm/proceso/secciones_decisiones.py`: sección 5 desde `decisiones/client_large.decisiones.yaml`, con DC-01 a DC-12 tomadas de la sección 3 de `ruta-a-produccion.md`. Cada decisión lleva id, texto, motivo, estado (`abierta` o `tomada`) y valor por omisión. El motivo dice quién decide y qué bloquea, porque la tabla no tiene columna de motivo. Todas figuran como abiertas. El cargador rechaza ids repetidos, campos vacíos y estados distintos.
  - `src/sgm/proceso/diseno_doc.py`: `SECCIONES_EMITIDAS` pasa a `1.1, 1.4, 2.1`; `SECCIONES_GENERICAS` pasa a `3, 5, 6` (no se comparan fila a fila). Orden del documento: 1.1, 1.4, 2.1, 3, 5, 6. `render_md.py` añade los títulos.
  - `src/sgm/conformidad/estado.py`: `DIFERENCIAS_CONOCIDAS` gana X01 (la carpeta de insumos coincide, pero el manual pide confirmarla por entorno, DC-07) y X06 (el SAS nombra `CODIGOS_DANE.xlsx`; el manual lo daba por pendiente, como F04).
- Antes y después, con `uv run sgm conformidad tests/fixtures/sas/client/client_large.sas` (PYTHONUTF8=1):

Antes (hito 93, mismo comando; el JSON de hoy da los mismos conteos: 5, 7, 105, 1):

```
Conformidad de client_large.sas contra el diseño manual (118 filas)
  derivadas:  5
  declaradas: 7
  pendientes: 105
  diferencias: 1
  porcentaje derivado: 4.2 %
Diferencias con motivo:
  F04 (sección 1.1, Códigos DANE): el SAS sí lee CODIGOS_DANE.xlsx; el manual lo daba por pendiente (el migrador halla más)
```

Después:

```
Conformidad de client_large.sas contra el diseño manual (118 filas)
  derivadas:  9
  declaradas: 7
  pendientes: 99
  diferencias: 3
  porcentaje derivado: 7.6 %
Diferencias con motivo:
  F04 (sección 1.1, Códigos DANE): el SAS sí lee CODIGOS_DANE.xlsx; el manual lo daba por pendiente (el migrador halla más)
  X01 (sección 2.1, ruta_insumos): el SAS da la misma carpeta de insumos; el manual pide confirmarla por entorno (DC-07) y el migrador no lo dice
  X06 (sección 2.1, arch_dane): el SAS sí nombra CODIGOS_DANE.xlsx, como en F04; el manual lo daba por pendiente
```

- Por sección, lo que se emite:
  - 1.1, 1.4: sin cambio.
  - 2.1: seis filas emitidas (`ruta_insumos`, `arch_hom_tpo_doc`, `arch_hom_tpo_doc_nequi`, `arch_paises`, `arch_dane`, `arch_validacion_fecha`). Derivadas: X03, X04, X05 y X07. Diferencias: X01 y X06. Pendientes de la sección: X02 (la carpeta de resultados se escribe con `PROC UPLOAD` dentro de `RSUBMIT`, y el modelo de salidas no lo lee), X08 (decisión humana) y X09 (valor fijo del emisor, sin fuente en el SAS).
  - 3, 6: sin cambio.
  - 5: doce decisiones DC-01 a DC-12. No mueve filas: las filas D1 a D6 del manual son decisiones de diseño con prosa, y sus claves no son DC.
  - 2.2, 2.3, 2.4, 3.x, 4, 7, 8: no se emiten. E02 (`impala_dsn`) sale de la macro `%ambiente`, pero su columna `origen` es prosa del manual. Las filas de 2.3 y 2.4 y las de 4 y 8 son convenciones del emisor o prosa de diseño. Las de 7 son humanas (P4 a P8, R1 a R4) o tienen prosa (P1 a P3). Ninguna se puede demostrar desde el SAS sin copiar texto del manual.
- Verificación de origen: un script (fuera del repo) comprueba que las nueve filas `derivada` tienen origen `sas` en `doc.origenes`. Las cuatro nuevas (X03, X04, X05, X07) lo tienen. El JSON de `sgm conformidad` es idéntico entre dos corridas.
- Métricas: derivadas 5 a 9; declaradas 7 a 7; pendientes 105 a 99; diferencias 1 a 3; porcentaje derivado 4,2 % a 7,6 %. **Meta de 60 no alcanzada.**
- Pruebas:
  - Nuevas (16): `tests/unit/test_proceso_secciones_parametros.py` (8) y `tests/unit/test_proceso_secciones_decisiones.py` (8, incluido el YAML real con sus doce ids).
  - Ajustes, sin debilitar: `tests/conformidad/test_linea_base.py` fija 9 derivadas (`F01, F02, F03, F05, S03, X03, X04, X05, X07`) y 3 diferencias (`F04, X01, X06`). `tests/conformidad/test_conformidad.py` añade `MOTIVOS_INCOMPLETA` (presencia de 2.1 y de 5, en xfail con motivo) y `FILAS_PENDIENTES` (X02, X08, X09, en xfail con motivo). `tests/unit/test_conformidad_estado.py` renombra los ids ficticios X01 a X04 a Z01 a Z04: ahora X01 es una diferencia conocida, y esas pruebas verifican reglas generales, no el manual. `tests/unit/test_tablero.py` pasa de 12 a 16 filas cumplidas y de 2 a 3 secciones emitidas. `tools/tablero.py` excluye también `FILAS_PENDIENTES`, como ya hacían las pruebas.
  - Suite: `uv run pytest -q -n auto`: **1968 pasadas, 26 omitidas y 128 `xfail`** en las dos últimas corridas. Las dos primeras de la tarde dieron 1959 y 1961 pasadas; la recolección de nodos es la misma (2122) en las corridas que se compararon, y la causa de esa diferencia no se localizó. `uv run ruff check .`: sin errores.
- Tamaño: `secciones_parametros.py` 59 líneas, `secciones_decisiones.py` 55, `diseno_doc.py` 135, `estado.py` 92.
- Decisiones:
  - Un parámetro sin valor demostrado por el SAS no se emite. El manual no se usa como fuente de valores.
  - `nota` se emite vacía: el SAS no tiene notas. Por eso X01 queda como diferencia, y no como derivada.
  - `tipo` es `String` para rutas y nombres: son literales de texto en el SAS.
  - Las rutas en `decisiones/client_large.diseno.yaml` (`parametros`) usan los nombres de parámetro del manual (`arch_*`, `ruta_insumos`). Son nombres, no valores.
  - `decisiones/client_large.decisiones.yaml` es opcional en el emisor: sin archivo, la sección 5 queda vacía.
  - Los identificadores nuevos siguen el vocabulario de `secciones_entrada.py` (`seccion_*`, `cargar_*`), en español. AGENTS pide inglés; no se renombró aquí para no mezclar estilos dentro de `proceso/`.
- Bloqueos:
  - La meta de 60 no se alcanza. Las filas que faltan comparan columnas de prosa del manual (`nota`, `origen`, `tema`, `paso`, `decision`) que el SAS no demuestra, o son decisiones humanas (que nunca cuentan como derivadas). Copiar esa prosa al emisor haría pasar las filas, pero sería copiar valores del manual, así que no se hizo. El comparador no se cambió.
  - Hace falta decidir (dueño del proyecto) si las columnas de prosa cuentan para "derivada". Sin esa decisión, R5-04 no pasa de unas pocas filas.
  - X02 requiere que el modelo de salidas lea `PROC UPLOAD` dentro de `RSUBMIT` (EQ04).
  - Las secciones 4, 7 y 8 no se emiten (ver arriba). La sección 5 emitida no coincide con la D1 a D6 del manual.
- No verificado: Talend Studio no se usó y ningún Job se ejecutó. Los nombres de archivo y la carpeta salen de la lectura del SAS, no de una ejecución de SAS.

## Hito 95. R1-12 (parte 2) y R6-03 (tUniqRow): `NODUPKEY` se ejecuta en Studio y la primera fila por llave se confirma

- Fecha: 2026-11-05. Continúa el hito 92 (parte 1, `8c3f170`), que dejó la regla leída y el oráculo, y la prueba en Studio bloqueada por el diálogo "Network Issue Occured". El usuario lo cerró y Studio respondió.
- Qué se hizo:
  - Plantilla `tUniqRow` (`talend_item/plantillas/tUniqRow.json`), extraída con `tools/extraer_plantilla.py` de `ref_tuniqrow_v92a_0.1.item`, guardado por Studio 8.0.1. Tabla `UNIQUE_KEY` con una fila por columna (`SCHEMA_COLUMN`, `KEY_ATTRIBUTE`, `CASE_SENSITIVE`). Los parámetros de contraseña y de entorno no aparecen. Lo que cambia: los bloques `FLOW` de tUniqRow, `UNIQUE` y `DUPLICATE` llevan sus columnas (ver Hallazgos).
  - `src/sgm/talend_item/flujos_duplicados.py` (185 líneas): `componentes(regla, columnas, entrada)` cuelga la rama de una entrada existente (`tMap_dup` que recorta las llaves, `tUniqRow_dup` con `CASE_SENSITIVE`, y dos `tFileOutputDelimited` con cabecera y `context.sufijo`, para únicos `<tabla>_<sufijo>.csv` y repetidos `<tabla>_DUPLICADOS_<sufijo>.csv`). `job_duplicados(regla, columnas, delimitador)` monta un Job propio con `tFileInputDelimited` sobre `context.ruta_origen`. Falla con `ValueError` si la regla no es `EQUALS` o si una llave no está en el esquema.
  - `tools/prueba_duplicados.py` (265) y `tools/duplicados_datos.py` (168, con `leer_csv(ruta, delimitador)`): emite dos Jobs (`dup_vectores` con 14 filas de vectores propios, y `dup_aho_unicos` con `origen_aho.csv` del caso L8/01, 23 columnas, `;`), los compila, exporta, ejecuta con sufijo nuevo y compara.
  - `tests/unit/test_talend_flujos_duplicados.py` (7): llave recortada en el `tMap`, marcas de `UNIQUE_KEY` (solo la llave con `KEY_ATTRIBUTE=true`, y las dos con `CASE_SENSITIVE=true`), dos CSV con cabecera y sufijo, conexiones `dup_*` sin chocar, job propio con `context.ruta_origen` y cabecera, y los dos `ValueError`.
- Regla que el Job implementa: primera fila que llega por cada llave, con llaves recortadas por la derecha y sensibles a mayúsculas. Es la regla de `reglas_duplicados` (hito 92): `NODUPKEY EQUALS` conserva la primera fila del grupo en el orden de entrada.

- Evidencia literal en Studio 8.0.1 / `PRJ_BANCOLOMBIA`, corrida `v92d` (`uv run python tools/prueba_duplicados.py --proyecto "C:/Talend/8.0.1/studio/workspace/talendbancolombia-963626413/PRJ_BANCOLOMBIA" --java-bin "C:/Talend/8.0.1/zulu21.50.19-ca-jdk21.0.11-win_x64/bin" --m2 "C:/Talend/8.0.1/studio/configuration/.m2/repository" --sufijo v92d --trabajo "C:/tmp/sgm-hito92/v92d"`). Las líneas `stdout` se omiten por su longitud; el resto es literal:

```text
Proyecto: C:\Talend\8.0.1\studio\workspace\talendbancolombia-963626413\PRJ_BANCOLOMBIA
Sufijo: v92d
Trabajo: C:\tmp\sgm-hito92\v92d
Comando dup_vectores_v92d: "C:\Users\USUARI~1\AppData\Local\Temp\build-f2jalwze\dup_vectores_v92d\dup_vectores_v92d_run.bat" --context="Default" --context_param "ruta_origen=C:/tmp/sgm-hito92/v92d/entradas/VECTORES.csv" --context_param "ruta_resultados=C:/tmp/sgm-hito92/v92d/salida_dup_vectores_v92d/" --context_param "sufijo=v92d"
Código de salida dup_vectores_v92d: 0
Vectores: 8 únicas, 6 repetidas; OK
Comando dup_aho_unicos_v92d: "C:\Users\USUARI~1\AppData\Local\Temp\build-jtmy29zz\dup_aho_unicos_v92d\dup_aho_unicos_v92d_run.bat" --context="Default" --context_param "ruta_origen=C:/tmp/sgm-hito92/v92d/entradas/origen_aho_cabecera.csv" --context_param "ruta_resultados=C:/tmp/sgm-hito92/v92d/salida_dup_aho_unicos_v92d/" --context_param "sufijo=v92d"
Código de salida dup_aho_unicos_v92d: 0
AHO: 40 únicas (esperado 40), 7 repetidas (esperado 7)
Limpieza: 4 archivos borrados del proyecto
RESULTADO: vectores y AHO coinciden con el oráculo y con esperado/AHO_UNICOS.csv
[exited with code 0]
```

- Salida que escribió el Job para los vectores (`VECTORES_v92d.csv`, únicas; y `VECTORES_DUPLICADOS_v92d.csv`, repetidas). Entrada en el orden del archivo: `A1,10`, `A1,10`, `G7,11`, `B2,30`, `B2,40`, `C3 ,50`, `C3,60`, `d4,1`, `D4,2`, `,5`, `   ,6`, `E5,1`, `E5,2`, `E5,3`.

```text
VECTORES_v92d.csv (únicas)            VECTORES_DUPLICADOS_v92d.csv (repetidas)
CLAVE,SALDO                           CLAVE,SALDO
A1,10                                 A1,10
G7,11                                 B2,40
B2,30                                 C3,60
C3,50                                 ,6
d4,1                                  E5,2
D4,2                                  E5,3
,5
E5,1
```

- Confirmación de la regla (ejecutada, no supuesta): `B2` sale con `30` y no con `40`; `C3 ` y `C3` son una sola llave con el primer saldo (`50`); `,5` gana a `   ,6` (blanco y vacío son el mismo faltante); `E5` sale con `1`; `d4` y `D4` no se mezclan. En `AHO_UNICOS_v92d.csv` salen 40 filas, con el mismo multiconjunto de 23 columnas que `esperado/AHO_UNICOS.csv` y el mismo orden que el oráculo (primera fila de cada llave en el orden de entrada); `AHO_UNICOS_DUPLICADOS_v92d.csv` tiene 7 filas, igual que 47 - 40.

- Hallazgos de la construcción (no obvios):
  1. Con el bloque `FLOW` propio de `tUniqRow` vacío, Studio saca **filas en blanco** por `UNIQUE` y `DUPLICATE`, aunque el Job compila y sale con código 0. Lo vieron el Job de referencia (`ref_tuniqrow_v92a`, ejecutado: solo líneas vacías) y un Job mínimo sin `tMap` (`dup_diag2`: 14 filas en blanco en cada salida). Con las columnas también en el bloque `FLOW` propio (`dup_diag3`), los valores salen y el reparto es correcto: 10 únicas y 4 repetidas en la entrada sin recortar. Por eso `flujos_duplicados` pone el esquema en ese bloque.
  2. `talend_job_verify` compila el Job aunque la clave `KEY_ATTRIBUTE` quede vacía: se escribió `KEY_ATTRIBUTE=""` para `CLAVE` hasta usar la forma por filas `[["CLAVE","true","true"],...]` de `talend_job_configure_node`. Verificar el `.item` guardado, no solo la compilación.
  3. La primera corrida `v92c` dio `DIFERENCIA` en el orden de AHO: fallo del arnés (leía el `;` del caso con el lector de `,`), no del Job. Se corrigió `leer_csv(ruta, delimitador)` y se repitió con `v92d`.
  4. Studio no creó el Job de referencia mientras el hilo de interfaz estuvo ocupado (unos 10 min) y tampoco con el diálogo "Network Issue" abierto. Se reintentó tras cerrarlo el usuario. El Job `ref_tuniqrow_v92a` se borró del proyecto; quedó una carpeta vacía en `process/`, que se quitó a mano.

- Decisiones:
  - `tUniqRow` sin `tSortRow`. El orden de salida no forma parte de la regla (el SAS deja las filas ordenadas por la llave, pero el caso compara por multiconjunto; la salida del Job sale en orden de llegada, que coincide con el del oráculo para estos datos).
  - La llave sale recortada en el CSV. El SAS la conserva con blancos finales; la comparación de llaves es igual en los dos, pero el texto del CSV no. Es una salvedad, no un hecho del SAS.
  - Nombres de salida: `<tabla>_<sufijo>.csv` y `<tabla>_DUPLICADOS_<sufijo>.csv`. El SAS no escribe los repetidos; el nombre de los repetidos es una decisión de esta rama.
  - Conexiones `dup_fuente`, `dup_fila`, `dup_unica` y `dup_repetida`: no repiten `cta_*`, `saldo_*`, `ubic_*` ni `valido`.

- Pruebas:
  - `test_talend_flujos_duplicados.py` (7, nuevas) y `test_proceso_reglas_duplicados.py` (10, hito 92).
  - Suite: `uv run pytest -q -n auto`: **1967 pasadas, 26 omitidas y 128 `xfailed`**. Falla una: `test_tools_ci.py::test_el_cierre_termina_en_cero_si_todo_pasa`, porque `uv run ruff check .` marca `src/sgm/seguridad/enmascarado.py:6` (E501, 102 columnas). Ese archivo no es de este hito (es de la otra serie en paralelo, sin commitear) y no se toca. Ruff sobre los archivos de este hito: limpio.

- Métricas: `flujos_duplicados.py` 185 líneas; `prueba_duplicados.py` 265; `duplicados_datos.py` 168; la plantilla `tUniqRow.json` tiene 16 parámetros y 4 bloques de metadatos.

- Bloqueos y no verificado:
  - **No integrado en `job_producto` ni en `cli_talend`** (opcional en el encargo). La rama existe y se ejecuta como Job propio; cuelgue de `tReplicate_1` está previsto en `componentes`, pero no se emite en el Job del cliente.
  - `NOEQUALS`, `DESCENDING` y `NODUPREC` quedan `Pendiente:` (`reglas_duplicados`). El caso `L8/01` tiene un `NODUPREC` que no se traduce.
  - Que `tUniqRow` conserve la primera fila **siempre** (con varios hilos, otros volúmenes o con datos nulos) no se probó: solo un Job de un hilo y 14 filas de vectores y 47 de AHO.
  - Las demás plantillas de R6-03 (`tFilterRow`, `tNormalize`, `tJoin`, `tConvertType`, `tFileList`, `tDBClose`, `tSendMail`) siguen pendientes; R6-03 solo tiene `tUniqRow`.
  - Ningún Job se abrió en el editor gráfico de Studio.

## Hito 96. R4-05: `sgm secretos` escanea artefactos y decisiones; cero hallazgos en client_large; DC-06 sigue abierta

- Fecha: 2026-11-05. Tarea R4-05 de `docs/plan-reescritura/ruta-a-produccion.md` (parcial). Relacionada con DC-06 (sección 3), que sigue abierta.
- Qué se hizo:
  - `src/sgm/seguridad/`: escáner de secretos en seis módulos pequeños. `enmascarado.py` (valor visible: 2 caracteres y `***`; por debajo de 6 caracteres solo `***`; marcadores vacío, `***`, `...`, `context.`, `$`, `&`, `%`, `<`), `reglas_texto.py` (asignaciones `password=`/`pwd=`/`passwd=`, `secret`/`token`/`api_key`, `proc pwencode in=` en claro, `{SAS00n}`, `Bearer`, clave privada PEM, `://usuario:clave@`), `reglas_xml.py` (atributos `field="PASSWORD"` o `"ENCRYPTED"` y `type="id_Password"` con valor no vacío, en `.item`, `.properties` y contextos), `lista_blanca.py`, `escaner_secretos.py` (orquestación, archivos binarios omitidos, carpetas `.git`, `__pycache__` y similares ignoradas, salida ordenada) y `__init__.py`.
  - `src/sgm/cli_secretos.py` y registro en `src/sgm/cli.py`: `sgm secretos <ruta> [--formato texto|json]`. Sale con código 1 si hay hallazgos y 0 si no. La salida es determinista.
  - `docs/secretos.md`: propuesta del método de entrega (contexto cargado fuera del repo o variable de entorno del lanzador), lista blanca y su auditoría, compuerta antes del despliegue y límites del escáner. El almacén no se elige: DC-06 queda abierta.
- Lista blanca: una sola entrada, el marcador `"sgm_ref"` del parámetro `PASSWORD` de `tFileInputExcel`. Motivo: Studio no compila ese componente con `PASSWORD` vacío ni con `***`, y el Excel de insumo no tiene clave. La entrada solo vale dentro de ese componente; el mismo valor en otro componente sí da hallazgo (probado).
- Salida literal de `sgm secretos` sobre los artefactos emitidos por `sgm talend` (client_large) y sobre `decisiones/`, con `uv run sgm talend tests/fixtures/sas/client/client_large.sas --out <carpeta temporal>` y después la compuerta:

```
0 hallazgo(s) en 0 archivo(s); 8 archivo(s) revisado(s)     (client_large/talend: 4 .item y 4 .properties; código 0)
0 hallazgo(s) en 0 archivo(s); 4 archivo(s) revisado(s)     (decisiones/; código 0)
0 hallazgo(s) en 0 archivo(s); 2 archivo(s) revisado(s)     (tests/fixtures/sas/client/; código 0)
```

- Hallazgo real fuera de la compuerta, reportado solo como archivo y línea. Salida literal de `sgm secretos tests/fixtures/sas/real/ci360-download-client/macros/dsc_download.sas` (código 1):

```
dsc_download.sas:55: password_en_cadena: "{***
dsc_download.sas:55: sas_cifrado: BA***
2 hallazgo(s) en 1 archivo(s); 1 archivo(s) revisado(s)
```

- Pruebas: `tests/unit/test_secretos_plantados.py` (un ejemplo plantado por tipo, con su detección, el enmascarado en texto y en JSON, la línea y la salida del CLI), `tests/unit/test_secretos_limpios.py` (valores limpios que no dan hallazgo, la lista blanca por componente y su efecto, el emisor sobre client_large con cero hallazgos, y `decisiones/` y `tests/fixtures/sas/client/` sin hallazgos), `tests/unit/test_secretos_cli.py` (códigos de salida, JSON, determinismo, binarios, errores de uso). Total: 74 pruebas nuevas. Los valores de los ejemplos son ficticios (`Zx9-ficticio-123`).
- Verificación medida:
  - Mis archivos: `uv run ruff check` sobre `src/sgm/seguridad`, `src/sgm/cli_secretos.py`, `src/sgm/cli.py` y los tres `tests/unit/test_secretos_*.py`: sin errores. `uv run pytest -q -n auto tests/unit/test_secretos_*.py`: 74 pasadas.
  - Suite completa `uv run pytest -q -n auto` (última corrida): 2043 pasadas, 26 omitidas, 128 xfail y 1 fallo ajeno, `tests/unit/test_tools_ci.py::test_el_cierre_termina_en_cero_si_todo_pasa`, porque el paso de ruff del cierre falla por archivos de `tools/` que no son de este hito.
  - `uv run ruff check .` del repositorio: 11 errores, todos ajenos a este hito y en `tools/`: `tools/prueba_totales_mecanismos.py` (3 E501) y `tools/totales_mecanismos_jobs.py` (1 I001 y 7 E501). No se tocaron.
  - Ruff y la suite completa del repositorio los corre el coordinador al terminar ambos agentes.
- Métricas: `src/sgm/seguridad/` suma 6 módulos, todos bajo 300 líneas. `cli.py` pasa de 292 a 294 líneas.
- Decisiones:
  - Enmascarado: 2 primeros caracteres y `***` solo si el valor tiene 6 caracteres o más. Un valor corto no muestra ninguno.
  - Las reglas de texto se aplican al texto completo, así que una sentencia de varias líneas (`proc pwencode`, `libname ... password=`) también se detecta.
  - La lista blanca es la única excepción. Se aplica al `.item` por componente y, en texto libre, por valor exacto.
  - Un `pwd=`, `password=`, `token` o `secret` con valor que empieza por `context.`, `$`, `&`, `%` o `<` es una referencia y no un secreto.
  - El escáner no revisa binarios (un byte nulo en los primeros 8 KB).
  - Las carpetas de artefactos de la compuerta son `client_large`, `decisiones/` y `tests/fixtures/sas/client/`. El resto del repositorio no entra en la compuerta: `docs/referencia/` tiene ejemplos de manuales SAS (`pass=`, `pwencode`) y el código fuente nombra variables como `token`.
- Bloqueos:
  - DC-06 sigue abierta: falta elegir el almacén de secretos y el mecanismo de carga por entorno.
  - `tests/fixtures/sas/real/ci360-download-client/macros/dsc_download.sas:55` contiene un valor con `{SAS002}`. No se modificó el fixture. Se recomienda que una persona revise si es un ejemplo público o un valor real; si es real, rotarlo y retirarlo del fixture.
  - `tests/unit/test_talend_plantillas.py:20` usa el valor de prueba `"secreto"` en un nodo tJava. El escáner lo marca, lo cual es correcto para su contexto; no se cambió la prueba.
- No verificado: Talend Studio no se usó y ningún Job se ejecutó. El escáner no lee logs reales porque el repositorio no tiene logs de ejecución. Las reglas cubren las formas listadas en `docs/secretos.md`; un secreto sin palabra clave reconocible puede pasar.

## Hito 97. Referencia SAS: `lepg` (Programmer's Guide: Essentials), 930 páginas con texto e índice

- Fecha: 2026-11-05. Pedido del usuario: revisar la guía `lepg` de `documentation.sas.com` y agregarla
  si le sirve al proyecto.
- Qué se hizo:
  - Se revisó la guía antes de agregarla. `lepg` es *SAS 9.4 Programmer's Guide: Essentials* (930
    páginas, 8.1 MB). No repite a las seis que ya estaban: `lestmtsref` da la sintaxis de cada
    sentencia y `proc` la de cada procedimiento; `lepg` da la semántica del paso DATA, que es lo que
    decide una equivalencia de Talend cuando la duda es de comportamiento. Capítulos que sirven al
    traductor, con su página en el índice: «DATA Step Processing» (p. 43), «Syntax» con variables y
    tipos (p. 57), «Grouping Data» con `FIRST.`/`LAST.`, `BY` y `GROUPFORMAT` (p. 423), «Loops and
    Conditionals» (p. 441), «Combining Data» (p. 493), «Using Arrays» (p. 593), «Output» (p. 689) y el
    apéndice «Understanding How the DATA Step Works» (p. 887), con el búfer de entrada y el PDV.
  - `tools/referencia/fuentes.py`: séptima entrada de `SAS_DOCSETS` (`lepg`). La descarga se hizo con
    `descargar.py sas`, que ya no vuelve a bajar los PDF existentes.
  - `tools/referencia/texto.py` (nuevo, 64 líneas): el `.txt` de una guía, con `<!-- página N -->`
    delante de cada página. Antes no había herramienta: los seis `.txt` que ya estaban se generaron a
    mano y no había forma de repetirlo. Se comprobó que reproduce `lestmtsref.txt` byte a byte en sus
    primeras 12 páginas, así que las siete guías quedan con el mismo formato.
  - Artefactos: `docs/referencia/sas/lepg.pdf` (8.1 MB, no versionado), `lepg.txt` (1.4 MB, 930
    páginas, 8 en blanco; `proc` tiene 3), `lepg.INDEX.md` (72 KB, 1584 secciones con su página).
  - `docs/referencia/sas/README.md`: séptima fila de la tabla con para qué sirve y la aclaración de
    que no repite a `lestmtsref`. `docs/referencia/README.md`: «7 guías», la fecha de `lepg` y la
    orden para regenerar el `.txt`.
  - Se comprobó de paso el resto de la colección: `lesysoptsref` (opciones de sistema) sí responde,
    3.6 MB, y queda anotada en «Qué no está aquí»; `leforinfref` sigue devolviendo 404.
- Decisiones:
  - Solo se agrega `lepg`. `lesysoptsref` existe y se podría bajar, pero ninguna regla depende de una
    opción de sistema todavía; bajarla sin uso sería peso muerto. La nota en el README dice cómo
    agregarla cuando haga falta.
  - El `.txt` se escribe con CRLF, igual que los seis que ya estaban (así los guarda git en este
    repositorio). La herramienta lo fija, en vez de depender del sistema donde se corre.
  - Los marcadores del PDF traen títulos partidos en dos líneas (60 casos en `lepg.INDEX.md`, 52 en
    `proc.INDEX.md`): es un defecto del PDF y se deja igual, para que las siete guías se lean igual.
- Pruebas: `tests/unit/test_referencia_tools.py` (3 nuevas): la marca y la línea en blanco entre
  páginas, una página sin texto, y el orden de las páginas. La prueba que exige `.txt` y `.INDEX.md`
  por guía cubre ahora las siete sin cambiar nada, porque recorre `SAS_DOCSETS`.
- Verificación: `uv run ruff check .`: limpio. `uv run pytest -q -n auto`: **2059 pasadas, 26 omitidas
  y 128 `xfailed`**, sin fallos. La corrida anterior a esa dio dos fallos que no se repitieron ni
  solos ni en la corrida completa siguiente; no se identificaron porque el resumen se perdió, y no
  volvieron a aparecer en dos corridas más.
- Métricas: `lepg.txt` 1.4 MB (930 páginas), `lepg.INDEX.md` 72 KB (1584 secciones), `texto.py` 64
  líneas, `docs/referencia/sas/` pasa de 6 a 7 guías.
- Bloqueos: la versión exacta de SAS del cliente sigue sin confirmar (tarea 9) y `leforinfref` sigue
  en 404, así que los informats se siguen tomando de `rules/sas/informats.yaml`.
- No verificado: no se abrió el PDF a mano página por página; la revisión fue por el índice y por
  búsquedas en el texto extraído. Que la guía describa la misma versión que corre el cliente no se
  puede saber desde el repositorio.

## Hito 97d. R2-01 y R2-02: mecanismo de totales entre Jobs validado en Studio (b), y `job_totales` real

- Fecha: 2026-11-05. Continúa el protocolo del hito 95 (`tools/prueba_duplicados.py`) y el cálculo de
  totales de origen del hito 85. Plan: `docs/plan-reescritura/ruta-a-produccion.md`, R2-01 y R2-02;
  `tareas-agente.md`, T30 y T31.
- Aviso de numeración: el commit `64786a4` ya publicó un `## Hito 97` (referencia SAS `lepg`). Esta
  entrada usa el 97 porque así lo encargó la sesión. Hay que renumerar una de las dos antes de
  publicar; no se renumeró ninguna por cuenta propia.

### Qué se hizo

- **R2-01.** `tools/prueba_totales_mecanismos.py` (235 líneas) y `tools/totales_mecanismos_jobs.py`
  (297): tres mecanismos con dos productos de ejemplo (CTE: 3 filas, suma 15.00; AHO: 2 filas, suma
  120.50), cada uno con padre e hijo; (b) añade el Job de totales. Los totales esperados se calculan a
  mano en el arnés, no con Studio.
- Plantilla `src/sgm/talend_item/plantillas/tBufferOutput.json`. El fixture que devuelve
  `talend_components_generate_template` no trae metadatos ni cabecera completa; se completó con la
  cabecera de `tUnite.json`. Studio la compiló y la ejecutó; no es un nodo guardado por Studio.
- **R2-02.** `src/sgm/talend_item/jobs_totales.py` (141): `job_totales(arq, productos)` lee
  `totales_origen_<p>.csv` y `totales_salida_<p>.csv` en orden y los añade con `APPEND` a
  `<archivo_totales>_<anio><mes><dia>.csv`. El nombre `archivo_totales` es la decisión del programa
  (`decisiones/client_large.jobs.yaml`, valor `totales_exogena`); la fecha sale de `context.periodo_*`.
  No usa `tUnite` (ver hallazgos).
- `src/sgm/talend_item/arquitectura.py`: campo `archivo_totales` (vacío por omisión).
- `src/sgm/talend_item/jobs_diseno.py`: `jobs_hijos` acepta `totales_real`.
- `src/sgm/cli_talend.py`: `sgm talend` emite el `job_totales` real cuando hay periodo y productos.
  Además avisa con `Pendiente:` que `job_producto` todavía no escribe los archivos de totales.
- `tools/totales_caso_jobs.py` (200) y `tools/prueba_totales_caso.py` (262): productor mínimo del
  caso 04 con la lógica que ya calcula `job_producto` (saldo con `a_decimal` del hito 85; origen =
  conteo de todas las filas y suma de los saldos no faltantes; salida = filas con `TIPO_CTA` distinto
  de `03`) y padre de prueba. Compara la salida con `esperado/` fila por fila con la tolerancia de
  `caso.yaml` (0,005).
- `tests/unit/test_talend_jobs_totales.py` (12 pruebas nuevas). `tests/unit/test_tablero.py`: la
  línea base de `job_totales` pasa de 1 a 13 componentes y el total de 36 a 48, por el Job real.

### R2-01. Tabla comparativa de los tres mecanismos

Las tres corridas finales son `v97i` (R2-01) y `v97j` (R2-02). Cada columna cita la corrida que la
sostiene.

| Criterio | (a) `tBufferOutput` + `PROPAGATE_CHILD_RESULT` | (b) archivos por producto en la carpeta de trabajo | (c) variables de contexto y `globalMap` |
|---|---|---|---|
| Facilidad de emitir | Requiere plantilla nueva (`tBufferOutput`) y un `tRunJob` con esquema de salida. Compiló y corrió. | Solo plantillas ya existentes (`tFileInputDelimited`, `tFileOutputDelimited`, `tAggregateRow`). Un archivo por producto y tipo. | Fácil de escribir, pero no transporta el total: ver resultado. |
| Auditable | Las filas viven en memoria; la evidencia es el archivo que escribe el padre. | Sí. El total queda en disco con nombre propio y se puede revisar después de la corrida. | No deja rastro en disco; solo se ve en la consola. |
| Fallos si un hijo falla | Con `DIE_ON_ERROR=true` en el lector del hijo: el padre sale con código 1 y no escribe el archivo del producto (`v97i`, fallo a). | Igual: el padre sale con código 1 y el Job de totales no corre (`v97i`, fallo b). | El padre sale con código 1 y no ejecuta el paso siguiente (`v97i`, fallo c). |
| Paralelizable | No probado en paralelo. Cada hijo entregaría sus filas al padre. | En principio sí: cada hijo escribe su propio archivo (`totales_origen_<sufijo>.csv`). No probado en paralelo. | No: el valor del hijo no vuelve al padre. |
| Resultado en Studio | Coincide: `totales_a_CTE.csv` = 3;15.00 y `totales_a_AHO.csv` = 2;120.50 (`v97i`). | Coincide: `totales_origen_CTE.csv`, `totales_origen_AHO.csv` y `totales_unidos_b.csv` (`v97i`). | Refutado: tras cada hijo el padre ve `resultado=SIN_VALOR globalMap=null`, aunque el hijo calcula 3\|15.00 y 2\|120.50 (`v97i`). |

**Recomendación: (b), confirmada por la ejecución.** Es el único que deja el total en disco con
nombre propio y que el Job de totales puede leer por separado, y falla bien con `DIE_ON_ERROR`. (a)
también funciona y podría usarse sin archivos intermedios, pero exige la plantilla de `tBufferOutput`
y no se probó en paralelo. (c) no sirve: el hijo no devuelve variables de contexto ni `globalMap`.

### Evidencia literal de R2-01 (corrida `v97i`, la final)

Los comandos `java -D...` y los prompts `C:\...>` se omiten; las líneas de pila (`at ...`) también.

```text
Proyecto: C:\Talend\8.0.1\studio\workspace\talendbancolombia-963626413\PRJ_BANCOLOMBIA
Sufijo: v97i
Trabajo: C:\Users\USUARI~1\AppData\Local\Temp\scratch\r2_01_v97i
Emitidos mecanismo a: ['mec_a_hijo', 'mec_a_padre']
Emitidos mecanismo b: ['mec_b_hijo', 'mec_b_totales', 'mec_b_padre']
Emitidos mecanismo c: ['mec_c_hijo', 'mec_c_padre']
Compilando hijos: ['mec_a_hijo_v97i', 'mec_b_hijo_v97i', 'mec_b_totales_v97i', 'mec_c_hijo_v97i']
Compilando padres: ['mec_a_padre_v97i', 'mec_b_padre_v97i', 'mec_c_padre_v97i']
--- ok mecanismo a (mec_a_padre_v97i) código de salida 0
mec_a_padre arranca
mec_a_hijo arranca, sufijo=CTE
mec_a_hijo arranca, sufijo=AHO
--- ok mecanismo b (mec_b_padre_v97i) código de salida 0
mec_b_padre arranca
mec_b_hijo arranca, sufijo=CTE
mec_b_hijo arranca, sufijo=AHO
mec_b_totales arranca
--- ok mecanismo c (mec_c_padre_v97i) código de salida 0
mec_c_padre antes: resultado=SIN_VALOR globalMap=null
mec_c_hijo fija resultado=HIJO_CTE
3|15.00
mec_c_padre tras CTE: resultado=SIN_VALOR globalMap=null
mec_c_hijo fija resultado=HIJO_AHO
2|120.50
mec_c_padre tras AHO: resultado=SIN_VALOR globalMap=null
--- fallo mecanismo a (mec_a_padre_v97i) código de salida 1
mart-2.4.11.jar;../lib/commons-beanutils-1.11.0.jar;../lib/commons-text-1.14.0.jar;../lib/javassist-3.30.2-GA.jar;../lib/dom4j-2.1.3.jar;../lib/crypto-utils-7.1.28.jar;../lib/job-audit-1.6.1.jar;../lib/system-routines-dq.jar;../lib/accessors-smart-2.4.11.jar;../lib/talendCBP-1.1.9.jar;../lib/antlr-runtime-3.5.2.jar;../lib/log4j-slf4j2-impl-2.19.0.jar;../lib/talendagent-1.0.2.jar;../lib/audit-log4j2-1.16.1.jar;../lib/logging-event-layout-1.16.1.jar;../lib/org.talend.dataquality.parser.jar;../lib/asm-9.5.jar;../lib/system-routines.jar;../lib/commons-lang3-3.18.0.jar;../lib/talendcsv-1.1.0.jar;../lib/talendboot-1.0.10.jar;../lib/slf4j-api-2.0.16.jar;../lib/audit-common-1.16.1.jar;mec_a_padre_v97i_0_1.jar;mec_a_hijo_v97i_0_1.jar; prj_bancolombia.mec_a_padre_v97i_0_1.mec_a_padre_v97i --context=Default --context="Default" --context_param "ruta_origen_cte=C:/Users/USUARI~1/AppData/Local/Temp/scratch/r2_01_v97i/entradas/origen_cte.csv" --context_param "ruta_origen_aho=C:/Users/USUARI~1/AppData/Local/Temp/scratch/r2_01_v97i/entradas/no_existe_aho.csv" --context_param "ruta_trabajo=C:/Users/USUARI~1/AppData/Local/Temp/scratch/r2_01_v97i/salida_a_fallo_v97i/" --context_param "sufijo=v97i" 
mec_a_padre arranca
mec_a_hijo arranca, sufijo=CTE
mec_a_hijo arranca, sufijo=AHO
[FATAL] 13:54:41 prj_bancolombia.mec_a_hijo_v97i_0_1.mec_a_hijo_v97i- tFileInputDelimited_1 C:\Users\USUARI~1\AppData\Local\Temp\scratch\r2_01_v97i\entradas\no_existe_aho.csv (El sistema no puede encontrar el archivo especificado)
java.io.FileNotFoundException: C:\Users\USUARI~1\AppData\Local\Temp\scratch\r2_01_v97i\entradas\no_existe_aho.csv (El sistema no puede encontrar el archivo especificado)
[FATAL] 13:54:41 prj_bancolombia.mec_a_padre_v97i_0_1.mec_a_padre_v97i- tRunJob_2 Child job running failed.
java.io.FileNotFoundException: C:\Users\USUARI~1\AppData\Local\Temp\scratch\r2_01_v97i\entradas\no_existe_aho.csv (El sistema no puede encontrar el archivo especificado)
java.lang.RuntimeException: Child job running failed.
java.io.FileNotFoundException: C:\Users\USUARI~1\AppData\Local\Temp\scratch\r2_01_v97i\entradas\no_existe_aho.csv (El sistema no puede encontrar el archivo especificado)
stderr:
Exception in component tFileInputDelimited_1 (mec_a_hijo_v97i)
java.io.FileNotFoundException: C:\Users\USUARI~1\AppData\Local\Temp\scratch\r2_01_v97i\entradas\no_existe_aho.csv (El sistema no puede encontrar el archivo especificado)
Exception in component tRunJob_2 (mec_a_padre_v97i)
java.lang.RuntimeException: Child job running failed.
java.io.FileNotFoundException: C:\Users\USUARI~1\AppData\Local\Temp\scratch\r2_01_v97i\entradas\no_existe_aho.csv (El sistema no puede encontrar el archivo especificado)
--- fallo mecanismo b (mec_b_padre_v97i) código de salida 1
ons-beanutils-1.11.0.jar;../lib/commons-text-1.14.0.jar;../lib/javassist-3.30.2-GA.jar;../lib/dom4j-2.1.3.jar;../lib/crypto-utils-7.1.28.jar;../lib/job-audit-1.6.1.jar;../lib/system-routines-dq.jar;../lib/accessors-smart-2.4.11.jar;../lib/talendCBP-1.1.9.jar;../lib/antlr-runtime-3.5.2.jar;../lib/log4j-slf4j2-impl-2.19.0.jar;../lib/talendagent-1.0.2.jar;../lib/audit-log4j2-1.16.1.jar;../lib/logging-event-layout-1.16.1.jar;../lib/org.talend.dataquality.parser.jar;../lib/asm-9.5.jar;../lib/system-routines.jar;../lib/commons-lang3-3.18.0.jar;../lib/talendcsv-1.1.0.jar;../lib/talendboot-1.0.10.jar;../lib/slf4j-api-2.0.16.jar;../lib/audit-common-1.16.1.jar;mec_b_padre_v97i_0_1.jar;mec_b_totales_v97i_0_1.jar;mec_b_hijo_v97i_0_1.jar; prj_bancolombia.mec_b_padre_v97i_0_1.mec_b_padre_v97i --context=Default --context="Default" --context_param "ruta_origen_cte=C:/Users/USUARI~1/AppData/Local/Temp/scratch/r2_01_v97i/entradas/origen_cte.csv" --context_param "ruta_origen_aho=C:/Users/USUARI~1/AppData/Local/Temp/scratch/r2_01_v97i/entradas/no_existe_aho.csv" --context_param "ruta_trabajo=C:/Users/USUARI~1/AppData/Local/Temp/scratch/r2_01_v97i/salida_b_fallo_v97i/" --context_param "sufijo=v97i" 
mec_b_padre arranca
mec_b_hijo arranca, sufijo=CTE
mec_b_hijo arranca, sufijo=AHO
[FATAL] 13:55:01 prj_bancolombia.mec_b_hijo_v97i_0_1.mec_b_hijo_v97i- tFileInputDelimited_1 C:\Users\USUARI~1\AppData\Local\Temp\scratch\r2_01_v97i\entradas\no_existe_aho.csv (El sistema no puede encontrar el archivo especificado)
java.io.FileNotFoundException: C:\Users\USUARI~1\AppData\Local\Temp\scratch\r2_01_v97i\entradas\no_existe_aho.csv (El sistema no puede encontrar el archivo especificado)
[FATAL] 13:55:01 prj_bancolombia.mec_b_padre_v97i_0_1.mec_b_padre_v97i- tRunJob_2 Child job running failed.
java.io.FileNotFoundException: C:\Users\USUARI~1\AppData\Local\Temp\scratch\r2_01_v97i\entradas\no_existe_aho.csv (El sistema no puede encontrar el archivo especificado)
java.lang.RuntimeException: Child job running failed.
java.io.FileNotFoundException: C:\Users\USUARI~1\AppData\Local\Temp\scratch\r2_01_v97i\entradas\no_existe_aho.csv (El sistema no puede encontrar el archivo especificado)
stderr:
Exception in component tFileInputDelimited_1 (mec_b_hijo_v97i)
java.io.FileNotFoundException: C:\Users\USUARI~1\AppData\Local\Temp\scratch\r2_01_v97i\entradas\no_existe_aho.csv (El sistema no puede encontrar el archivo especificado)
Exception in component tRunJob_2 (mec_b_padre_v97i)
java.lang.RuntimeException: Child job running failed.
java.io.FileNotFoundException: C:\Users\USUARI~1\AppData\Local\Temp\scratch\r2_01_v97i\entradas\no_existe_aho.csv (El sistema no puede encontrar el archivo especificado)
--- fallo mecanismo c (mec_c_padre_v97i) código de salida 1
5.2.jar;../lib/log4j-slf4j2-impl-2.19.0.jar;../lib/talendagent-1.0.2.jar;../lib/audit-log4j2-1.16.1.jar;../lib/logging-event-layout-1.16.1.jar;../lib/org.talend.dataquality.parser.jar;../lib/asm-9.5.jar;../lib/system-routines.jar;../lib/commons-lang3-3.18.0.jar;../lib/talendcsv-1.1.0.jar;../lib/talendboot-1.0.10.jar;../lib/slf4j-api-2.0.16.jar;../lib/audit-common-1.16.1.jar;mec_c_padre_v97i_0_1.jar;mec_c_hijo_v97i_0_1.jar; prj_bancolombia.mec_c_padre_v97i_0_1.mec_c_padre_v97i --context=Default --context="Default" --context_param "ruta_origen_cte=C:/Users/USUARI~1/AppData/Local/Temp/scratch/r2_01_v97i/entradas/origen_cte.csv" --context_param "ruta_origen_aho=C:/Users/USUARI~1/AppData/Local/Temp/scratch/r2_01_v97i/entradas/no_existe_aho.csv" --context_param "ruta_trabajo=C:/Users/USUARI~1/AppData/Local/Temp/scratch/r2_01_v97i/salida_c_fallo_v97i/" --context_param "sufijo=v97i" 
mec_c_padre antes: resultado=SIN_VALOR globalMap=null
mec_c_hijo fija resultado=HIJO_CTE
3|15.00
mec_c_padre tras CTE: resultado=SIN_VALOR globalMap=null
mec_c_hijo fija resultado=HIJO_AHO
[FATAL] 13:55:20 prj_bancolombia.mec_c_hijo_v97i_0_1.mec_c_hijo_v97i- tFileInputDelimited_1 C:\Users\USUARI~1\AppData\Local\Temp\scratch\r2_01_v97i\entradas\no_existe_aho.csv (El sistema no puede encontrar el archivo especificado)
java.io.FileNotFoundException: C:\Users\USUARI~1\AppData\Local\Temp\scratch\r2_01_v97i\entradas\no_existe_aho.csv (El sistema no puede encontrar el archivo especificado)
[FATAL] 13:55:20 prj_bancolombia.mec_c_padre_v97i_0_1.mec_c_padre_v97i- tRunJob_2 Child job running failed.
java.io.FileNotFoundException: C:\Users\USUARI~1\AppData\Local\Temp\scratch\r2_01_v97i\entradas\no_existe_aho.csv (El sistema no puede encontrar el archivo especificado)
java.lang.RuntimeException: Child job running failed.
java.io.FileNotFoundException: C:\Users\USUARI~1\AppData\Local\Temp\scratch\r2_01_v97i\entradas\no_existe_aho.csv (El sistema no puede encontrar el archivo especificado)
stderr:
Exception in component tFileInputDelimited_1 (mec_c_hijo_v97i)
java.io.FileNotFoundException: C:\Users\USUARI~1\AppData\Local\Temp\scratch\r2_01_v97i\entradas\no_existe_aho.csv (El sistema no puede encontrar el archivo especificado)
Exception in component tRunJob_2 (mec_c_padre_v97i)
java.lang.RuntimeException: Child job running failed.
java.io.FileNotFoundException: C:\Users\USUARI~1\AppData\Local\Temp\scratch\r2_01_v97i\entradas\no_existe_aho.csv (El sistema no puede encontrar el archivo especificado)
Limpieza: 14 archivos borrados del proyecto
RESULTADO: OK
```

Contenido de los archivos que escribieron los hijos y el Job de totales:

```text
totales_a_CTE.csv (padre, mecanismo a):
registros;suma_saldo
3;15.00

totales_a_AHO.csv (padre, mecanismo a):
registros;suma_saldo
2;120.50

totales_origen_CTE.csv (hijo, mecanismo b):
registros;suma_saldo
3;15.00

totales_unidos_b.csv (Job de totales, mecanismo b):
registros;suma_saldo
3;15.00
2;120.50
```

### Evidencia literal de R2-02 (corrida `v97j`, la final)

Comando y salida de `tools/prueba_totales_caso.py`, sin los `java -D...`:

```text
Proyecto: C:\Talend\8.0.1\studio\workspace\talendbancolombia-963626413\PRJ_BANCOLOMBIA
Sufijo: v97j
Trabajo: C:\Users\USUARI~1\AppData\Local\Temp\scratch\r2_02_v97j
Compilando hijos: ['caso_producto_v97j', 'job_totales_v97j']
Compilando padre: caso_padre_v97j
Limpieza: 6 archivos borrados del proyecto
Comando: "C:\Users\USUARI~1\AppData\Local\Temp\build-i8jhhlgg\caso_padre_v97j\caso_padre_v97j_run.bat" --context="Default" --context_param "ruta_origen_cte=C:/Users/USUARI~1/AppData/Local/Temp/scratch/r2_02_v97j/entradas/origen_cte.csv" --context_param "ruta_origen_aho=C:/Users/USUARI~1/AppData/Local/Temp/scratch/r2_02_v97j/entradas/origen_aho.csv" --context_param "ruta_resultados=C:/Users/USUARI~1/AppData/Local/Temp/scratch/r2_02_v97j/resultados_v97j/" --context_param "sufijo=v97j" --context_param "periodo_anio=2026" --context_param "periodo_mes=09" --context_param "periodo_dia=30"
Código de salida: 0
stdout:
caso_padre: arranca
caso_totales: origen y salida del producto
caso_totales: origen y salida del producto
job_totales: une 4 archivos de totales
Contenido literal de totales_exogena_20260930.csv:
PRODUCTO;TIPO;NRO_FILAS;NRO_SALDOS_NO_VACIOS;SUMA_SALDO
CTE;origen;40;38;170632.98
CTE;salida;39;;163686.34
AHO;origen;40;40;211498.67
AHO;salida;37;;198645.97
RESULTADO: coincide con esperado/
```

Comparación con `esperado/` (caso `L8/totales/04_totales_origen_salida`):

| Producto | Tipo | NRO_FILAS | NRO_SALDOS_NO_VACIOS | SUMA_SALDO | Esperado (filas / saldos / suma) |
|---|---|---|---|---|---|
| CTE | origen | 40 | 38 | 170632.98 | 40 / 38 / 170632.98 |
| CTE | salida | 39 | (vacío) | 163686.34 | 39 / (no definido) / 163686.34 |
| AHO | origen | 40 | 40 | 211498.67 | 40 / 40 / 211498.67 |
| AHO | salida | 37 | (vacío) | 198645.97 | 37 / (no definido) / 198645.97 |

Coincide en filas, conteo de saldos no faltantes y sumas (tolerancia 0,005). Las invariantes del
`caso.yaml` se cumplen con esas filas: 40 - 39 = 1, 40 - 37 = 3, 40 - 38 = 2. Dos saldos del caso
están en blanco en CTE; no suman y no cuentan como saldo no vacío, como exige la semántica de
`vectores.yaml`.

### Hallazgos (ejecutados)

1. **`tUnite` no compila en Studio 8.0.1 con este Job.** Tres variantes (metadato de salida
   `tUnite_1`, `out1` y entradas `row1`/`row2`) dieron el mismo error:
   `Cannot invoke "org.talend.core.model.metadata.IMetadataTable.getListColumns()" because
   "preMetadata" is null`, en `TUniteMainJava.generate(TUniteMainJava.java:98)` (log de Studio,
   `workspace/.metadata/.log`). No hay ningún Job de ejemplo con `tUnite` en el workspace. Por eso
   R2-02 une con `APPEND` secuencial. `tUnite` queda sin validar.
2. **`DIE_ON_ERROR` vale `false` por defecto en `tFileInputDelimited`.** Con el archivo de AHO
   inexistente (corrida `v97e`, sin `DIE_ON_ERROR`), el hijo registra un error y termina bien, el padre
   sigue y sale con código 0. Por ejemplo: `--- fallo mecanismo b (mec_b_padre_v97e) código de salida 0`
   seguido de `mec_b_totales arranca`, y `--- fallo mecanismo c ...` seguido de `mec_c_padre tras AHO:`.
   Con `DIE_ON_ERROR=true` (corrida `v97i`) el hijo falla, el `tRunJob` informa
   `Child job running failed.` y el padre sale con código 1. Por eso `job_totales` pone
   `DIE_ON_ERROR=true` en sus entradas. Es relevante para R2-07 (DC-08): sin esto, un producto sin
   archivo pasa en silencio.
3. **`tRunJob` con `DIE_ON_CHILD_ERROR=true` (valor de la plantilla)** detiene al padre cuando el
   hijo muere. Confirmado en los tres mecanismos.
4. **Infraestructura.** La corrida `v97h` (código final, sin cambios respecto de `v97i`) fue
   rechazada por el puente de Studio con `El job no existe en el repositorio` para los cuatro Jobs
   hijos, y el arnés borró las copias al terminar. La corrida `v97i` con el mismo código y un
   sufijo nuevo pasó. No apareció el diálogo "Network Issue".

### Decisiones

- Mecanismo de totales: (b), por la tabla. (a) y (c) quedan como comparativa, no como código de producción.
- Unión por `APPEND` secuencial, en lugar de `tUnite`, mientras `tUnite` no compile.
- `DIE_ON_ERROR=true` en las entradas de totales, para que un archivo faltante falle el Job.
- `archivo_totales` en la decisión del programa, no en `src/`: el nombre `totales_exogena` es un nombre
  de salida del cliente y las pruebas de nombres prohíben literales de scripts del cliente en `src/`.
- Esquema del archivo de totales: `PRODUCTO;TIPO;NRO_FILAS;NRO_SALDOS_NO_VACIOS;SUMA_SALDO`, una fila
  por producto y tipo. Es el esquema de las columnas del caso 04 (`NRO_FILAS_*`, `SUMA_SALDO_*`), no
  el de `TOTAL_AHORROS_CONS` y `TOTAL_CORRIENTE`.
- `NRO_SALDOS_NO_VACIOS` de la salida va vacío: el caso no define ese conteo para la salida.
- Fecha de la prueba `2026-09-30`: valor de prueba. El caso no declara la fecha del proceso.
- Plantilla `tBufferOutput.json` generada por el servidor y validada en Studio, no extraída de un Job
  guardado (no hay ninguno en el workspace).

### Pruebas

- `uv run ruff check .`: sin errores.
- `uv run pytest -q -n auto`: **2061 pasadas, 26 omitidas y 128 `xfailed`**.
- Studio, R2-01, corridas con sufijo nuevo: `v97a` (`tUnite`, NPE en el generador), `v97b` (`tUnite`
  con metadato `out1`, mismo NPE), `v97c` (`tUnite` con entradas `row1`/`row2`, mismo NPE), `v97d`
  (unión por `APPEND`: a, b y c dan lo esperado; sin escenario de fallo), `v97e` (escenario de fallo
  con `DIE_ON_ERROR` en falso: código 0), `v97f` (con `DIE_ON_ERROR=true`: código 1 en los tres),
  `v97h` (rechazada por el puente, ver hallazgo 4) y `v97i` (código final: todo como se esperaba).
- Studio, R2-02: `v97g` (primera corrida: coincide con `esperado/`), tras pasar el nombre del archivo a
  la decisión y limpiar el código, `v97j` (código final: `RESULTADO: coincide con esperado/`).

### Métricas

- `jobs_totales.py` 141 líneas; `prueba_totales_caso.py` 262; `prueba_totales_mecanismos.py` 235;
  `totales_caso_jobs.py` 200; `totales_mecanismos_jobs.py` 297; `test_talend_jobs_totales.py` 12 pruebas.
- Plantillas nuevas: 1 (`tBufferOutput`). Dependencias nuevas: ninguna.

### Bloqueos y no verificado

- **Numeración duplicada** con el commit `64786a4` (ver arriba).
- **`job_producto` no escribe `totales_origen_<p>.csv` ni `totales_salida_<p>.csv`.** Lo hace el
  productor mínimo de `tools/`. Integrarlo en `job_producto` (módulo propio, para no pasar de 300
  líneas) queda para el siguiente hito. Mientras tanto `sgm talend` avisa con `Pendiente:`.
- **Columnas de la exógena.** R2-02 exige columnas iguales a `TOTAL_AHORROS_CONS` y `TOTAL_CORRIENTE`.
  No se cumple: el SAS de `client_large.sas` (líneas 24693 a 24800) escribe esos dos archivos con
  13 sumas (`FIN_SAL_CTA`, `PROM_SAL_CTA`, ... `PROM_DEB_MES`) sobre las tablas `TOTAL_CORRIENTE` y
  `TOTAL_AHORROS_CONS`, no origen y salida por producto. Pendiente: decidir con el SAS y con negocio
  cuál es la exógena real. R2-02 queda parcial.
- **Regla de salida `TIPO_CTA <> '03'`.** Es un supuesto del caso 04 (`caso.yaml`, "regla de este caso, no
  del SAS"). No está demostrada en el SAS real.
- **Fecha.** La fecha la pasa la prueba como parámetro. La lectura real del Excel de la fecha (R2-04)
  no se probó aquí.
- **Paralelismo** de los tres mecanismos: no probado.
- **`sgm talend` para `client_large`**: la emisión del Job real está cubierta por pruebas unitarias
  y por el tablero; no se ejecutó en Studio el Job del programa grande.
- **`tUnite`**: no validado; ver hallazgo 1.

## Hito 98. Referencia SAS: `lrcon` (Language Reference: Concepts), 916 páginas, y la segunda forma de URL

- Fecha: 2026-11-05. Pedido del usuario: revisar la guía `lrcon` y agregarla si sirve.
- Qué se hizo:
  - Se revisó antes de agregarla. `lrcon` es *SAS 9.4 Language Reference: Concepts*, Sixth Edition
    (916 páginas, 7.7 MB). No repite a `lepg`: `lepg` muestra cómo se usa el lenguaje, con ejemplos;
    `lrcon` fija la regla. Capítulos que sirven al traductor, con su página en el índice: reglas de
    palabras y nombres (p. 43), variables (p. 61), valores perdidos (p. 123), expresiones (p. 133),
    fechas e intervalos (p. 155), `BY` en programas (p. 229), procesamiento de `WHERE` (p. 231), paso
    DATA (p. 491), leer/combinar/modificar conjuntos (p. 563) y arrays (p. 667).
  - Sirve para una duda que quedó abierta en el hito 95: en una comparación los blancos finales no
    cuentan, `'fox '` es igual a `'fox'` (p. 133 y siguientes). Es la regla que explica por qué la
    llave del CSV sale recortada y la del SAS no, sin que la comparación cambie.
  - `tools/referencia/fuentes.py`: `SAS_DOCSET_BASE`, la segunda plantilla de URL
    (`/api/docsets/<docset>/9.4/content/<docset>.pdf`), un campo `base` en `SasDocset` con la
    colección `pgmsascdc` por omisión, `url_sas(docset, base)` y `url_guia(guia)`. La octava entrada
    del catálogo usa la plantilla nueva. `descargar.py` pide el PDF con `url_guia`.
  - Artefactos: `docs/referencia/sas/lrcon.pdf` (7.7 MB, no versionado), `lrcon.txt` (1.5 MB, 916
    páginas, 5 en blanco) y `lrcon.INDEX.md` (67 KB, 1306 secciones con su página).
  - `docs/referencia/sas/README.md`: octava fila de la tabla, la excepción de URL explicada en las
    notas y para qué se cita `lrcon` frente a `lepg`. `docs/referencia/README.md`: «8 guías» y la
    segunda colección como fuente.
  - Se volvió a comprobar el resto: `leforinfref` devuelve 404 también en la forma `/api/docsets/`,
    así que la falta de la guía de formatos no es un problema de plantilla; `lesysoptsref` responde
    por las dos.
- Decisiones:
  - Un campo `base` con valor por omisión, en vez de una tabla de URLs: siete guías comparten
    plantilla y solo `lrcon` la cambia; una tabla habría repetido la misma cadena siete veces.
  - `url_sas` conserva su firma (la usa una prueba y es la forma corta para las guías de la
    colección); `url_guia` es la que decide por guía.
  - `lesysoptsref` sigue sin bajarse: ninguna regla depende todavía de una opción de sistema.
- Pruebas: `tests/unit/test_referencia_tools.py` (2 nuevas, 12 en el archivo): la URL de `lrcon` sale
  de la plantilla nueva, y las otras siete siguen dando exactamente la URL de siempre.
- Verificación: `uv run ruff check .`: limpio. `uv run pytest -q -n auto`: 2215 casos, **2060 pasadas,
  26 omitidas y 128 `xfailed`**, con un fallo intermitente ajeno,
  `tests/unit/test_tools_ci.py::test_el_cierre_termina_en_cero_si_todo_pasa`: ese cierre lanza los
  pasos del corpus dentro de la suite y compite con los demás procesos; corrido solo pasa, y
  `uv run python tools/ci.py --sin-suite --sin-tablero` a mano da los tres pasos en verde.
- Métricas: `lrcon.txt` 1.5 MB (916 páginas), `lrcon.INDEX.md` 67 KB (1306 secciones), `fuentes.py`
  con 8 guías, `docs/referencia/sas/` de 7 a 8 guías.
- Bloqueos: la guía de formatos (`leforinfref`) sigue en 404 por las dos plantillas; la versión exacta
  de SAS del cliente sigue sin confirmar (tarea 9).
- No verificado: no se leyó la guía entera; la revisión fue por el índice y por búsquedas en el texto
  extraído. Que `lrcon` y el SAS del cliente sean la misma edición no se puede saber desde el repo.

## Hito 98d. R2-03 y R2-07: `job_conciliacion` real en Studio, y el fallo de un hijo hace fallar al padre (DC-08 por omisión)

- Fecha: 2026-11-05. Serie `d` (sesión paralela; el hito 98 es el de la referencia `lrcon`). Plan:
  `docs/plan-reescritura/ruta-a-produccion.md`, filas R2-03 y R2-07; `tareas-agente.md`, T32 y T33.

### Qué se hizo

- `src/sgm/talend_item/jobs_conciliacion.py` (227 líneas): `job_conciliacion(arq, productos, ruta_java,
  nombre)`. Por producto, en orden (`OnSubjobOk`): dos lectores de `totales_origen_<p>.csv` y
  `totales_salida_<p>.csv` con `DIE_ON_ERROR=true`; un `tMap` con la salida como lookup por `PRODUCTO`
  que calcula `DIF_FILAS` (entero exacto) y `DIF_SALDO` (`BigDecimal`); y una escritura a
  `conciliacion_<anio><mes><dia>.csv` (la cabecera solo en el primero). Después un lector relee ese
  archivo, un `tJavaRow` deja en `globalMap` el texto de cada producto que no concilia, y un `tDie`
  (`EXIT_JVM=true`, `CODE=3`, mensaje desde `globalMap`) corre con `Run if` si hay texto.
- `src/sgm/cli_talend.py`: `sgm talend` emite el `job_conciliacion` real cuando hay periodo,
  `archivo_totales` y productos. Añade tres avisos `Pendiente:` (tolerancia, salida de la conciliación,
  fórmula de `client_large`). `src/sgm/talend_item/jobs_diseno.py`: `jobs_hijos` acepta
  `conciliacion_real`.
- `src/sgm/talend_item/jobs_producto.py`: `DIE_ON_ERROR=true` en el lector del origen del producto
  (dos líneas).
- `tests/unit/test_talend_jobs_conciliacion.py` (13 funciones de prueba, 15 casos con las parametrizaciones).
- `tests/unit/test_tablero.py`: el baseline de `job_conciliacion` pasa de 1 a 16 componentes y el total
  de 48 a 63. Es el Job real con tres productos (3 x 4 componentes + `tJava`, `tJavaRow`, lector de
  chequeo y `tDie`).
- Herramientas de la prueba en Studio: `tools/prueba_conciliacion_caso.py` (249 líneas),
  `tools/prueba_conciliacion_utiles.py` (97) y `tools/prueba_fallo_producto.py` (114).

### Decisiones

- **Regla de no conciliación, como en el SAS (L8/05).** `CONCILIA` solo si `ABS(DIF_SALDO) <= tolerancia`
  y `DIF_FILAS = 0` (`programa.sas`, etiqueta "Estado de conciliación CTE"). La tolerancia es solo de
  saldo; las filas no tienen tolerancia. La petición decía comparar filas y saldos con la tolerancia;
  se siguió el SAS porque es lo que demuestra.
- **Tolerancia de negocio** (DC-04): `context.tolerancia_conciliacion`, valor `0` por omisión, con el
  comentario "confirmar con negocio". No se inventó otro valor.
- **Código de salida 3 para "no concilia".** El SAS solo escribe `NOTE`/`WARNING`; el código es una
  decisión del emisor, no un dato del SAS.
- **Chequeo por relectura del archivo.** El `tMap` no puede dejar un valor en `globalMap` de forma
  limpia, así que el chequeo lee `conciliacion_<fecha>.csv`, que ya contiene lo que se decidió.
- **Columnas** `PRODUCTO;DIF_FILAS;DIF_SALDO`, las de `CONCILIACION_FINAL` del SAS. No se añadieron
  `NRO_ORIGEN` ni un estado.
- **DC-08 (fallo parcial), solo la opción por omisión.** Si un producto falla, falla todo el proceso:
  `tRunJob` tiene `DIE_ON_CHILD_ERROR=true` y los lectores de totales, de conciliación y del producto
  tienen `DIE_ON_ERROR=true`. La alternativa (seguir con los demás productos y registrar el fallo) no
  se implementó: DC-08 es decisión de negocio y todavía no está tomada.
- **Dos definiciones de "salida".** En `L8/totales/04` la salida es `TIPO_CTA <> '03'` (supuesto del
  caso). En `L8/totales/05` la salida de la conciliación es válidos más rechazados (regla del SAS).
  Son el mismo archivo con significados distintos. Queda pendiente decidir cuál escribe `job_producto`.
- **Totales de entrada de la prueba.** Se escriben desde `esperado/TOTALES_CONC_<p>.csv` (origen:
  `NRO_ORIGEN` y `SUMA_ORIGEN`; salida: válidos más rechazados). Así se prueba el Job de conciliación,
  no el productor de totales, que `job_producto` todavía no escribe. Fecha de prueba: 2026-09-30.

### Evidencia de Studio 8.0.1 (`PRJ_BANCOLOMBIA`, corrida `v98b`, la final)

Comando: `uv run python tools/prueba_conciliacion_caso.py --proyecto
"C:/Talend/8.0.1/studio/workspace/talendbancolombia-963626413/PRJ_BANCOLOMBIA" --java-bin
"C:/Talend/8.0.1/zulu21.50.19-ca-jdk21.0.11-win_x64/bin" --m2 "C:/Talend/8.0.1/studio/configuration/.m2/repository"
--sufijo v98b`. Se omiten las líneas `java -D...` y las de pila (`at ...`).

```text
Proyecto: C:\Talend\8.0.1\studio\workspace\talendbancolombia-963626413\PRJ_BANCOLOMBIA
Sufijo: v98b
Compilando hijos: ['caso_conc_cte_v98b', 'caso_conc_ambos_v98b']
Compilando padre: caso_politica_v98b
--- escenario concilia
Código de salida: 0
job_conciliacion: CTE
Contenido literal de conciliacion_20260930.csv:
PRODUCTO;DIF_FILAS;DIF_SALDO
CTE;0;0.00
RESULTADO concilia: OK
--- escenario no_concilia
Código de salida: 3
job_conciliacion: CTE, AHO
[ERROR] 14:18:21 prj_bancolombia.caso_conc_ambos_v98b_0_1.caso_conc_ambos_v98b- tDie_conc - The die message: NO CONCILIA AHO: diferencia de filas 1, diferencia de saldo 5.00 (tolerancia 0)
routines.system.TDieException: NO CONCILIA AHO: diferencia de filas 1, diferencia de saldo 5.00 (tolerancia 0)
[FATAL] 14:18:21 prj_bancolombia.caso_conc_ambos_v98b_0_1.caso_conc_ambos_v98b- tDie_conc - Exiting the VM.
stderr: NO CONCILIA AHO: diferencia de filas 1, diferencia de saldo 5.00 (tolerancia 0)
Contenido literal de conciliacion_20260930.csv:
PRODUCTO;DIF_FILAS;DIF_SALDO
CTE;0;0.00
AHO;1;5.00
RESULTADO no_concilia: OK
--- escenario politica
Código de salida: 1
caso_politica: arranca
job_conciliacion: CTE, AHO
[FATAL] 14:18:54 prj_bancolombia.caso_conc_ambos_v98b_0_1.caso_conc_ambos_v98b- tFileInputDelimited_o2 C:\Users\USUARI~1\AppData\Local\Temp\scratch\r2_03_v98b\entradas_v98b_politica\totales_origen_AHO.csv (El sistema no puede encontrar el archivo especificado)
[FATAL] 14:18:54 prj_bancolombia.caso_politica_v98b_0_1.caso_politica_v98b- tRunJob_1 Child job running failed.
Exception in component tRunJob_1 (caso_politica_v98b)
java.lang.RuntimeException: Child job running failed.
RESULTADO politica: OK
Limpieza: 6 archivos borrados del proyecto
```

El escenario `politica` no imprime `caso_politica: NO DEBIA CORRER`, así que el paso siguiente no corrió.
El `conciliacion_20260930.csv` de ese escenario solo tiene la fila de CTE, porque el hijo escribió CTE
antes de fallar en AHO.

Prueba de R2-07 para el producto (`tools/prueba_fallo_producto.py`, corrida `v98c`): el `job_producto`
emitido con `ruta_origen` inexistente sale con código 1:

```text
Código de salida: 1
[FATAL] 14:22:57 prj_bancolombia.job_producto_v98c_0_1.job_producto_v98c- tFileInputDelimited_1 C:\Users\USUARI~1\AppData\Local\Temp\scratch\r2_07_v98c\no_existe_origen.csv (El sistema no puede encontrar el archivo especificado)
RESULTADO: OK, el Job falla con código distinto de 0 al faltar el origen
```

Intentos sin valor de evidencia: `v98a` se corrió sin el JDK de Studio en el PATH; `java` no se
reconoce, así que todos los escenarios salieron con 1 por eso. Su `RESULTADO politica: OK` es un
falso positivo y no se usa. Se repitió con `--java-bin` y `--m2` como `v98b`. No apareció el diálogo
"Network Issue".

### Hallazgos de la fórmula de conciliación del SAS real

`client_large.sas` no usa la fórmula de `L8/05` en sus conciliaciones. Los bloques `Calculo conciliacion`
(líneas 4069 a 4140, 6585 a 6660, 7273 a 7360 y 9229 a 9620) calculan `CONCILIACION_REG` y
`CONCILIACION_SALDOS` por producto, con sumas distintas (por ejemplo `NRO_REGISTROS` contra la sábana
final más inconsistencias corregidas, o `SUMA_SALDO_INICIAL` contra la sábana y las inconsistencias).
Este Job implementa `L8/05`. Qué fórmula aplica a `client_large` queda pendiente (aviso `Pendiente:`
de `sgm talend`).

### Pruebas y verificación

- `uv run pytest -q -n auto`: **2094 pasadas, 26 omitidas y 129 `xfailed`**, sin fallos.
- `uv run ruff check .`: limpio.
- Pruebas nuevas: `tests/unit/test_talend_jobs_conciliacion.py` (13 funciones, 15 casos).
- `sgm talend tests/fixtures/sas/client/client_large.sas` emite los cuatro Jobs (padre, producto, totales
  y conciliación). Los avisos `Pendiente:` nuevos son tres.

### Métricas

- `jobs_conciliacion.py` 227 líneas; `cli_talend.py` 229; `prueba_conciliacion_caso.py` 249.
- Dependencias nuevas: ninguna. Plantillas nuevas: ninguna (se usan `tFileInputDelimited`, `tMap`,
  `tFileOutputDelimited`, `tJavaRow`, `tDie`, `tJava` y `tRunJob`).

### Bloqueos y no verificado

- **Tolerancia de negocio** (DC-04) sin valor: solo se probó con `0`. Con una tolerancia distinta de cero
  no se ejecutó nada en Studio.
- **Fórmula de `client_large`** distinta de `L8/05`: sin decidir (ver hallazgos).
- **Salida de totales.** `job_producto` no escribe `totales_origen_<p>.csv` ni `totales_salida_<p>.csv`.
  Los Jobs de totales y conciliación leen archivos que el padre real aún no produce. Los datos de
  entrada de la prueba salen de `esperado/`, no de `job_producto`.
- **Caso de conciliación de prueba.** La variante "concilia" usa un Job solo con CTE
  (`caso_conc_cte`); en el caso no hay un dataset en que AHO concilie. No se inventaron datos.
- **Padre real.** El `job_padre` de `client_large` no se ejecutó en Studio. La propagación se probó con un
  padre de prueba (`caso_politica`).
- **`tDie` dentro de un padre.** La prueba del `tDie` se hizo con el Job de conciliación directamente.
  Que `EXIT_JVM` dentro de un hijo termine el padre no se ejecutó.
- **Control negativo** (`DIE_ON_ERROR=false` en el lector de conciliación): no se corrió aquí. El
  hito 97d lo midió con el mismo tipo de lector (`v97e`): el Job terminó con código 0.
- **Casos no cubiertos del lookup**: un producto sin fila en la salida hace fallar el `tMap` (NPE, sin
  mensaje claro) y un `SUMA_SALDO` vacío hace fallar la conversión `BigDecimal`. Ninguno se probó.
- **Ajeno**: `tests/unit/test_proceso_insumos.py::test_el_programa_grande_resuelve_las_cinco_fuentes_de_excel`
  falla por archivos sin commitear de otra sesión (`decisiones/client_large.diseno.yaml`); no se tocó.
- La regla de `L8/05` y la tolerancia de prueba `0.005` de `caso.yaml` no son lo mismo: `0.005` es la
  tolerancia para comparar decimales en `esperado/`; la de negocio es `tolerancia_conciliacion`.

## Hito 99d. R5-02 y R5-06: el documento emitido y la propuesta al manual siguen lo probado

- Fecha: 2026-11-05. Tareas R5-02 y R5-06 de `docs/plan-reescritura/ruta-a-produccion.md` (T61).
- Dependencia R3-05 sin cumplir: la sección 3 refleja el Job actual, no uno joblet.

### Qué se hizo

- **1.1 Fuentes externas** (`decisiones/client_large.diseno.yaml`, clave `fuentes`). Los depósitos
  dejan de ser "Tabla Impala": son CSV `DBIFTCD.csv`, `DBIFTCS.csv` y `F_1019.csv`, con `;` y sin
  cabecera (hito 64; `client_large.sas` líneas 284-294, 871-881 y 1510-1517). Se añade el auxiliar
  `Base_datos_Nequi.csv` (R1-16). Las lecturas Impala que el SAS demuestra son tres:
  `resultados_vspc_clientes.master_customer_data` (línea 167), `S_CANALES.SAI_SCILIBRAMD_SCIFFIMGFR`
  (línea 215) y `proceso_vspc_finanzas.MCDQ` (línea 2071). El tipo y la ubicación de cada fila los
  da el emisor al hallar la ruta en el SAS (`seccion_fuentes`); el DSN sale de la macro `%ambiente`
  (D a IMPALA, C a IMPALAC, P a IMPALAP; línea 1770 y siguientes).
- **1.2 Intercambio de totales y lookups (sin caché)**, sección nueva en
  `src/sgm/proceso/secciones_intercambio.py`. Las filas vienen de la clave `intercambios` del YAML.
  El SAS no tiene cachés; el texto lo fija el emisor. Los lookups de Excel se leen dentro de
  `job_producto`: el de tipo de documento (CTE y AHO) sí; el de NEQUI, país y DANE no (R1-16, R1-05).
  Los totales viajan en archivos por producto, mecanismo (b) del hito 97d; `job_producto` aún no los
  escribe, y el documento lo dice.
- **1.3 Variables del periodo**, `seccion_periodo`. El padre `job_exogena_depositos` lee la fecha
  del Excel de validación y deja `periodo_anio`, `periodo_mes` y `periodo_dia` en el contexto; los
  hijos las heredan (hito 63). No hay `job_insumos`. La fila sale de `decisiones/client_large.jobs.yaml`.
- **3 Jobs emitidos y componentes**, `src/sgm/proceso/secciones_jobs.py`. `componentes_emitidos`
  llama a `talend_command` (el mismo emisor que `sgm talend`) escribiendo en una carpeta temporal y
  cuenta los `<node>` de cada `.item`. No se copia ninguna cifra. Un Job de un componente se marca
  como esqueleto. `job_producto` queda por encima del límite de 20 del manual, con 21 componentes.
  Se retiró la tabla de etapas de la sección 3 (sus conteos siguen en el resumen).
- **Diferencias conocidas** (`src/sgm/conformidad/estado.py`). Se añaden F06 a F08 (depósitos como
  tablas Impala), C01 a C10 (cachés) y G01 a G03 (periodo), cada una con su motivo. Cambio de
  semántica: el motivo conocido solo se aplica cuando hay diferencia real con el manual. Antes ganaba
  siempre, y así F06 marcaba como diferente un programa cuyo YAML sí coincide con el manual.
- **Pruebas**: `tests/unit/test_proceso_secciones_intercambio.py` (5), `tests/unit/test_proceso_secciones_jobs.py`
  (6), `tests/unit/test_proceso_diseno_real.py` (7, sobre `client_large.sas`) y una prueba nueva en
  `test_conformidad_estado.py`. Las secciones 1.2 y 1.3 pasan a `SECCIONES_EMITIDAS`, así que sus
  xfail de presencia se quitan porque la prueba pasa de verdad.
- **Propuesta al manual (R5-06)**: `docs/propuesta-correcciones-diseno-manual.md`, 17 puntos con
  hito, línea del SAS y recomendación. El manual no se toca.

### Conformidad: antes y después (salida literal de `sgm conformidad`)

Antes de los cambios:

```text
Conformidad de client_large.sas contra el diseño manual (118 filas)
  derivadas:  9
  declaradas: 7
  pendientes: 99
  diferencias: 3
  porcentaje derivado: 7.6 %
Diferencias con motivo:
  F04 (sección 1.1, Códigos DANE): el SAS sí lee CODIGOS_DANE.xlsx; el manual lo daba por pendiente (el migrador halla más)
  X01 (sección 2.1, ruta_insumos): el SAS da la misma carpeta de insumos; el manual pide confirmarla por entorno (DC-07) y el migrador no lo dice
  X06 (sección 2.1, arch_dane): el SAS sí nombra CODIGOS_DANE.xlsx, como en F04; el manual lo daba por pendiente
```

Después de los cambios:

```text
Conformidad de client_large.sas contra el diseño manual (118 filas)
  derivadas:  9
  declaradas: 4
  pendientes: 86
  diferencias: 19
  porcentaje derivado: 7.6 %
Diferencias con motivo:
  F04 (sección 1.1, Códigos DANE): el SAS sí lee CODIGOS_DANE.xlsx; el manual lo daba por pendiente (el migrador halla más)
  F06 (sección 1.1, Depósitos corriente (origen CTE)): el origen es un CSV bajado con PROC DOWNLOAD (DBIFTCD.csv, DBIFTCS.csv, F_1019.csv; hito 64), no una tabla de Impala
  F07 (sección 1.1, Depósitos ahorros (origen AHO)): el origen es un CSV bajado con PROC DOWNLOAD (DBIFTCD.csv, DBIFTCS.csv, F_1019.csv; hito 64), no una tabla de Impala
  F08 (sección 1.1, Depósitos Nequi (origen NEQUI)): el origen es un CSV bajado con PROC DOWNLOAD (DBIFTCD.csv, DBIFTCS.csv, F_1019.csv; hito 64), no una tabla de Impala
  C01 (sección 1.2, cache_hom_doc): no hay caché: job_producto lee el Excel de tipo de documento (hitos 70 y 85)
  C02 (sección 1.2, cache_hom_nequi): no hay caché ni lookup de NEQUI en job_producto: pendiente (R1-16)
  C03 (sección 1.2, cache_paises): no hay caché ni lookup: la validación de ubicación no está en el job_producto de este programa (R1-05)
  C04 (sección 1.2, cache_dane): no hay caché ni lookup: la validación de ubicación no está en el job_producto de este programa (R1-05)
  C05 (sección 1.2, totales_origen_cte): no hay caché: los totales viajan en archivos por producto en la carpeta de trabajo (hito 97d, mecanismo b); job_producto aún no los escribe
  C06 (sección 1.2, totales_origen_aho): no hay caché: los totales viajan en archivos por producto en la carpeta de trabajo (hito 97d, mecanismo b); job_producto aún no los escribe
  C07 (sección 1.2, totales_origen_nequi): no hay caché: los totales viajan en archivos por producto en la carpeta de trabajo (hito 97d, mecanismo b); job_producto aún no los escribe
  C08 (sección 1.2, totales_salida_cte): no hay caché: los totales viajan en archivos por producto en la carpeta de trabajo (hito 97d, mecanismo b); job_producto aún no los escribe
  C09 (sección 1.2, totales_salida_aho): no hay caché: los totales viajan en archivos por producto en la carpeta de trabajo (hito 97d, mecanismo b); job_producto aún no los escribe
  C10 (sección 1.2, totales_salida_nequi): no hay caché: los totales viajan en archivos por producto en la carpeta de trabajo (hito 97d, mecanismo b); job_producto aún no los escribe
  G01 (sección 1.3, periodo_anio): el padre lee la fecha y la pasa por contexto (hito 63); no la lee job_insumos, que se eliminó
  G02 (sección 1.3, periodo_mes): el padre lee la fecha y la pasa por contexto (hito 63); no la lee job_insumos, que se eliminó
  G03 (sección 1.3, periodo_dia): el padre lee la fecha y la pasa por contexto (hito 63); no la lee job_insumos, que se eliminó
  X01 (sección 2.1, ruta_insumos): el SAS da la misma carpeta de insumos; el manual pide confirmarla por entorno (DC-07) y el migrador no lo dice
  X06 (sección 2.1, arch_dane): el SAS sí nombra CODIGOS_DANE.xlsx, como en F04; el manual lo daba por pendiente
```

Las 9 derivadas no bajan (meta del hito: no bajar). Las declaradas bajan de 7 a 4 porque F06 a F08
pasan a diferencias con motivo. Las diferencias suben de 3 a 19: 16 nuevas, todas en
`DIFERENCIAS_CONOCIDAS`.

### Pruebas

- `uv run pytest -q -n auto`: 2094 pasan, 26 se saltan, 129 xfail.
- `uv run ruff check .`: limpio.
- Ajustes de pruebas existentes, sin borrar aserciones:
  - `tests/conformidad/test_linea_base.py`: lista de diferencias medidas (19 ids).
  - `tests/unit/test_tablero.py`: conformidad 16 a 13 filas cumplidas y 3 a 5 secciones emitidas.
    El tablero cuenta filas emitidas que no están en `DIFERENCIAS_CONOCIDAS`; F06 a F08 salen de
    ese conteo, no del de derivadas.
  - `tests/unit/test_conformidad_estado.py`: la prueba de "diferencia conocida" tenía un caso sin
    diferencia real; se le da una diferencia real y se añade la prueba del caso coincidente.
  - `tests/unit/test_proceso_insumos.py`: la prueba de los cinco Excel elige solo las fuentes con
    ubicación `ruta_insumos`; antes elegía todas las que tienen `busca`, y las fuentes CSV e Impala
    nuevas la rompían. La aserción no cambia.

### Métricas

- Derivadas 9 de 118 (sin cambio), declaradas 4 (antes 7), pendientes 86 (antes 99), diferencias
  19 (antes 3).
- Componentes emitidos hoy para `client_large.sas` (por la sección 3): `job_producto` 21,
  `job_exogena_depositos` 13, `job_totales` 13, `job_conciliacion` 16. El último número cambia
  porque la otra sesión trabaja en `jobs_conciliacion.py` sin commitear; no es de este hito.

### No verificado

- No se ejecutó Studio. Este hito no toca Jobs ni `.item`; cambia el documento y la conformidad.
- `componentes_emitidos` depende de la firma de `talend_command`, que la otra sesión modifica en
  `cli_talend.py` sin commitear. Si cambia, la sección 3 falla con un mensaje claro.
- `tCacheIn` y `tCacheOut` entre Jobs no se han probado; la propuesta lo dice (punto 4).
- El tablero mide "filas cumplidas" con un criterio distinto del de `sgm conformidad`. No se corrigió.

### Pendiente

- R3-05 (joblets) para que `job_producto` baje de 20 componentes. Hasta entonces la sección 3 lo dice.
- DC-04 (tolerancia) y la decisión de exógena frente a `TOTAL_*` (propuesta, punto 11).
- Escritura de `totales_origen_<p>.csv` y `totales_salida_<p>.csv` en `job_producto` (R2-02).

### Decisiones

- Sección 3: el conteo viene del emisor real en una carpeta temporal, no de un valor fijo. Así el
  documento no puede decir más de lo que el código emite.
- Sección 1.2: el texto de cada intercambio está en `decisiones/`, con su evidencia en el hito que
  lo sostiene. Lo que el emisor no hace aún dice "pendiente" con su motivo.
- Diferencias conocidas: solo cuentan cuando hay diferencia real (ver arriba).

## Hito 99. Referencia SAS: `leforinforref` (Formats and Informats), la guía que se buscaba con el nombre equivocado

- Fecha: 2026-11-05. Pedido del usuario: revisar seis URL de `documentation.sas.com` y agregar lo que
  sirviera.
- Qué se hizo:
  - Cinco de las seis URL son guías que ya están: `mcrolref`, `lepg`, `lefunctionsref`,
    `ledsoptsref` y `proc`. No se volvieron a bajar.
  - La sexta sí faltaba y era la que el proyecto daba por perdida: el docset se llama
    **`leforinforref`** (con `forinfor`), no `leforinfref`. Con el nombre correcto responde 200 por
    las dos plantillas de URL, así que el 404 de los hitos 44b y siguientes era un error de
    transcripción del nombre, no una guía ausente. Es *SAS 9.4 Formats and Informats: Reference*
    (766 páginas, 4.9 MB): formats en la p. 15 y el diccionario de informats en la p. 553.
  - `tools/referencia/fuentes.py`: novena entrada del catálogo, con la plantilla de siempre (no
    necesita el campo `base`). Artefactos: `leforinforref.pdf` (no versionado), `leforinforref.txt`
    (903 KB, 766 páginas, 2 en blanco) y `leforinforref.INDEX.md` (21 KB, 539 secciones).
  - `docs/referencia/sas/README.md`: novena fila de la tabla y una nota que explica el nombre
    correcto, para que nadie vuelva a buscar `leforinfref`. `docs/referencia/README.md`: «9 guías» y
    se quita de «Qué no está aquí» la guía de formatos, que era el único faltante de la colección.
  - Medición sobre la regla `fecha` de `rules/sas/informats.yaml`, que nombra 11 informats de fecha u
    hora: el diccionario de la guía tiene informats de esa familia que la regla no nombra. Se
    comprobaron uno por uno en el índice: `ANYDTDTE` (p. 617), `ANYDTDTM` (p. 620), `ANYDTTME`
    (p. 623), `B8601DA` (p. 628), `B8601DN` (p. 631), `E8601DA` (p. 654), `RMFDUR` (p. 706),
    `RMFSTAMP` (p. 707), `SHRSTAMP` (p. 731) y `SMFSTAMP` (p. 733). Los tres `ANYDT*` leen fecha,
    hora o fecha-hora «en cualquier forma»; los `B8601`/`E8601` son ISO 8601; los `RMF`/`SHR`/`SMF`
    son sellos y duraciones de mainframe.
- Decisiones:
  - **No se toca `rules/sas/informats.yaml` en este hito.** Cada informat nuevo obliga a decidir su
    tipo en Talend (Date, BigDecimal, Long, Double) y a probarlo; agregar nombres sin esa prueba
    sería inventar. La guía queda local y la lista de arriba es el punto de partida del hito que lo
    haga.
  - La nota del nombre va en los dos README, no solo en `PROGRESS.md`: el error de transcripción
    vivió en la documentación del proyecto durante decenas de hitos y es lo que hay que evitar que
    vuelva.
- Pruebas: ninguna nueva. La prueba que exige `.txt` y `.INDEX.md` por guía recorre `SAS_DOCSETS` y
  ya cubre `leforinforref`.
- Verificación: `uv run ruff check .`: limpio. `uv run pytest -q tests/unit/test_referencia_tools.py`:
  12 pasadas. Suite completa: 2249 casos, 5 fallos, y los cinco son de la serie que está trabajando
  en `src/sgm/talend_item/` sin commitear: tres esperan 21 nodos en `job_producto` y el emitido tiene
  25, `test_no_script_specific_names` marca `src/sgm/talend_item/flujos_totales.py:11` por decir
  «exogena», y `test_tools_ci` arrastra ese estado. Ninguno toca `docs/referencia/` ni
  `tools/referencia/`; este hito no cambió código de `src/`.
- Métricas: `leforinforref.txt` 903 KB (766 páginas), `leforinforref.INDEX.md` 21 KB (539 secciones),
  `docs/referencia/sas/` de 8 a 9 guías, que es la colección `pgmsascdc` completa salvo
  `lesysoptsref`.
- Bloqueos: `rules/sas/informats.yaml` sigue con los 11 nombres de antes; la deuda ahora es de reglas,
  no de documentación. La versión exacta de SAS del cliente sigue sin confirmar (tarea 9).
- No verificado: no se leyó la guía entera; el recuento de informats de fecha/hora sin cubrir no se
  cerró con un número, porque el diccionario mezcla formats e informats en el texto extraído y un
  conteo automático daba resultados inestables. Se citan los casos comprobados a mano.

## Hito 100. Catálogo de documentación SAS por capas y las cuatro guías de entorno (sistema, Grid, UNIX, CONNECT)

- Fecha: 2026-11-05. Pedido del usuario: un catálogo de documentación oficial de SAS por prioridad
  («para que la IA entienda SAS 9.4 y ayude a construir el traductor»), con la instrucción de
  quedarse con él.
- Qué se hizo:
  - `docs/referencia/catalogo-sas.md` (nuevo): el catálogo ordenado en las cuatro capas del pedido
    —A semántica, B transformaciones, C entorno y ejecución, D construcción en Talend— con el estado
    real de cada guía (descargada, disponible sin bajar, no existe con ese nombre), el orden de
    descarga que se siguió y la regla del proyecto: ninguna equivalencia sin fuente y página.
  - Cuatro guías nuevas, todas de la colección `pgmsascdc` (no hicieron falta URL especiales):
    `lesysoptsref` (System Options: Reference, 514 páginas), `gridref` (Grid Computing in SAS 9.4,
    374), `hostunx` (Companion for UNIX Environments, 702) y `connref` (SAS/CONNECT 9.4 User's
    Guide, 500). Artefactos: `.pdf` (no versionados), `.txt` con marca de página y `.INDEX.md` por
    sección, los tres con `descargar.py` y `texto.py`/`indice.py`.
  - Las cuatro se justifican con evidencia del repositorio, no por completitud:
    `tests/fixtures/sas/client/client_large.sas` se generó en `sasgrid.bancolombia.corp` y en
    `SASGRIDCOMP1.APPS.BANCOLOMBIA.CORP` (Grid); los casos de `tests/corpus/L8/validaciones/` traen
    `signon` y `RSUBMIT` (SAS/CONNECT); `rules/sas/plumbing.yaml` ya separa `x`, `%sysexec` y
    `systask` del trabajo de datos (UNIX); y `docs/plan-sgm-v2/02-fases.md` tiene la fase J3.4 de
    orquestación con `sasgsub`, `sas -sysin` y Control-M (Grid otra vez).
  - Páginas que quedan citadas en el catálogo y en el README, para no volver a buscarlas:
    `MERGENOBY` (p. 265), `MISSING=` (p. 266), `VALIDVARNAME=` (p. 412) y `YEARCUTOFF=` (p. 432) en
    `lesysoptsref`; `SASGSUB` (p. 321) en `gridref`; `SIGNON`/`SIGNOFF` (p. 151), `RSUBMIT` (p. 185)
    y librerías remotas (p. 31) en `connref`; primer/segundo plano (p. 33) y `fileref` (p. 129) en
    `hostunx`.
  - `docs/referencia/sas/README.md`: cuatro filas más en la tabla (13 en total) y puntero al
    catálogo. `docs/referencia/README.md`: «13 guías», el catálogo como documento propio y «Qué no
    está aquí» reescrito.
- Decisiones:
  - **No se baja `nlsref`** (7.7 MB, responde): ninguna regla depende todavía de la codificación. Se
    anota como disponible, con el disparador («un archivo con encoding declarado»).
  - **No se baja nada de SAS/STAT, SAS/ACCESS, ODS ni DS2**: el catálogo lo condiciona a que el
    corpus los use, y hoy no aparecen. La regla queda escrita en el catálogo: se comprueba con una
    búsqueda antes de bajar, no por si acaso.
  - El catálogo vive en `docs/referencia/`, no en `PROGRESS.md`: es una decisión viva (qué falta y
    por qué), no la bitácora de un hito.
  - El documento de logging no tiene docset en la colección (`logref` da 404). No se inventa una URL:
    queda como «buscar en el Help Center» si llega a hacer falta.
- Pruebas: `tests/unit/test_referencia_tools.py`, una nueva: cada guía de `SAS_DOCSETS` tiene su fila
  en la tabla de `sas/README.md`. La que exige `.txt` y `.INDEX.md` ya cubre las trece. Total del
  archivo: 13.
- Verificación: `uv run ruff check .`: limpio. `uv run pytest -q tests/unit/test_referencia_tools.py`:
  13 pasadas. Suite completa: 2257 casos, **2101 pasadas, 26 omitidas y 128 `xfailed`**, con un solo
  fallo, `test_no_script_specific_names`, por `src/sgm/talend_item/flujos_totales.py:11`, que dice
  «exogena»: es de la serie que trabaja en `src/sgm/talend_item/` sin commitear. Este hito no cambió
  código de `src/` ni de `rules/`.
- Métricas: `docs/referencia/sas/` de 9 a 13 guías; `.txt` nuevos de 617 KB a 1.1 MB; `catalogo-sas.md`
  108 líneas. PDF nuevos: 15.5 MB, no versionados.
- Bloqueos: la deuda sigue siendo de reglas, no de documentación: `rules/sas/informats.yaml` con 11
  nombres y las opciones de sistema sin regla propia. La versión exacta de SAS del cliente sigue sin
  confirmar (tarea 9).
- No verificado: no se leyó ninguna de las cuatro guías entera; la revisión fue por índice y por
  búsquedas. Que el cliente use `MERGENOBY` o `YEARCUTOFF` con valores distintos del de omisión no se
  puede saber desde el repositorio: eso lo dirá una revisión de los `autoexec` y los scripts de
  lanzamiento.

## Hito 101. Catálogos de opciones, informats y procedimientos; el de funciones pasa de 3 a 22 reconocidas

- Fecha: 2026-11-05. Pedido del usuario: «hazlo todo» sobre las cinco acciones propuestas al revisar
  el catálogo de documentación (opciones, informats, funciones, procedimientos y opciones que cambian
  el resultado).
- Qué se hizo:
  - `rules/sas/catalogo/opciones-sistema.yaml` (nuevo, 9 entradas): las opciones que el corpus usa de
    verdad, con página y clase. `REMOTE=` (41 usos, `connref.pdf` p. 130), `COMAMID=` (41, p. 123),
    `SASCmd=` (30, p. 135), `SYMBOLGEN` (60, `mcrolref.pdf` p. 501), `MLOGIC` (30, p. 485), `MPRINT`
    (30, p. 489), `SOURCE` (60, `lesysoptsref.pdf` p. 346), `SOURCE2` (30, p. 347) y `SYNTAXCHECK`
    (30, p. 381). Todas `no_verificada`: el repo no las trata, y son entorno o diagnóstico, no
    transformación.
  - `rules/sas/catalogo/informats-usados.yaml` (nuevo, 17 entradas): los que el traductor tipa
    (`$w.` p. 616, `w.` y `w.d` p. 556, DATE 649, DATETIME 650, DDMMYY 653, JULIAN 678, MMDDYY 682,
    MONYY 684, TIME 736, YYMMDD 755, YYQ 759) y los cinco de la familia que no tipa (`ANYDTDTE` 617,
    `ANYDTDTM` 620, `ANYDTTME` 623, `B8601DA` 628, `E8601DA` 654), estos como `no_verificada`.
  - `rules/sas/catalogo/procs-usados.yaml` (nuevo, 9 entradas): los `PROC` del programa grande con su
    página. `PROC SQL` (521 usos, `sqlproc.pdf` p. 269) es el único `reconocida`; DELETE (216,
    `proc.pdf` p. 837), SORT (31, p. 2449), CONTENTS (30, p. 541), UPLOAD (22, `connref.pdf` p. 247),
    EXPORT (22, p. 901), IMPORT (9, p. 1373), DOWNLOAD (4, p. 287) y PWENCODE (1, p. 1997) no tienen
    tratamiento propio.
  - `rules/sas/catalogo/opciones-resultado.yaml` (nuevo, 4 entradas): `MERGENOBY` (p. 265),
    `MISSING=` (266), `VALIDVARNAME=` (412) y `YEARCUTOFF=` (432). Ninguna aparece en el corpus; el
    catálogo existe para que la decisión quede con página y estado.
  - `docs/opciones-de-sistema.md` (nuevo): la decisión escrita. Un `OPTIONS` nunca se convierte en
    transformación; si el programa fija una de las cuatro que cambian el resultado, el paso lleva
    `Pendiente:` con la opción y su página; si no la fija, no se emite nada, porque el valor de
    omisión del cliente no está en el repositorio; y un informat de año de dos dígitos sin
    `YEARCUTOFF` deja `Pendiente: fecha de dos dígitos sin YEARCUTOFF`.
  - **Corrección del catálogo de funciones**: decía 3 reconocidas y el traductor ya convierte 22. El
    criterio viejo medía el acomodo de los archivos («hay regla en `rules/sas/functions`»), no la
    capacidad: las funciones de varios argumentos viven en la tabla del traductor de Talend
    (`src/sgm/expressions/talend_tabla.py`), no en un YAML de una línea. Se actualizaron 19 entradas
    con su sitio de implementación (`input`, `cats`, `cat`, `date`, `datetime`, `sum`, `left`,
    `length`, `int`, `count`, `compress`, `ifn`, `ifc`, `substrn`, `round`, `put`, `max`, `mod`,
    `year`), y quedan 14 `no_verificada` con nota cuando hay algo que decir: `SUBSTR (right of =)`
    (el parser la clasifica como asignación y el emisor todavía no escribe el reemplazo de la
    subcadena), `TIME` (no está en la tabla; sí `today`, `date` y `datetime`) y `RANUNI` (no
    determinista: se marca pendiente).
  - **Corrección de la regla de informats**: `rules/sas/informats.yaml` nombraba `dtdate` y `dtmonyy`
    como informats de fecha. En la guía no existen como informats: son formats (cero títulos
    `DTDATEw. Informat` en `leforinforref.txt`). Se quitaron; la regla queda con 9 nombres, todos
    verificados en el diccionario.
- Decisiones:
  - «Reconocida» pasa a significar «el traductor ya la convierte», venga de una regla YAML o de la
    tabla del traductor. El catálogo de funciones no servía para medir cobertura mientras midiera
    otra cosa.
  - Dos catálogos de opciones en vez de uno: `opciones-sistema` es lo que el corpus usa (y una prueba
    exige que aparezca); `opciones-resultado` es lo que cambia resultados aunque hoy no se use. Juntar
    los dos habría dejado entradas que la prueba de uso no puede sostener.
  - La decisión de `docs/opciones-de-sistema.md` no se codifica en este hito. Tocar la pasada que lee
    `OPTIONS` y el registro de pendientes es comportamiento, no documentación, y el pedido era dejar
    la decisión escrita y con fuente. Queda anotado como lo que falta.
- Pruebas: `tests/unit/test_catalogo_sas.py` (34, cuatro nuevas y una reescrita):
  - el mapa de guías citables pasa de 5 a 9 (entran `leforinforref`, `lesysoptsref`, `connref` y
    `proc`), así que toda página citada por los catálogos nuevos se comprueba contra su índice;
  - `test_cada_funcion_reconocida_tiene_su_implementacion`: la regla YAML existe y su `sas` coincide,
    o el nombre está en la tabla del traductor;
  - `test_los_informats_de_la_regla_existen_en_la_guia`: cada nombre de la regla `fecha` tiene su
    título `XXXw. Informat` en el diccionario. Es la prueba que habría detectado `DTDATE` y
    `DTMONYY`;
  - `test_los_informats_del_catalogo_coinciden_con_la_regla`: `reconocida` si la regla lo tipa,
    `no_verificada` si no, en los dos sentidos;
  - `test_las_opciones_del_catalogo_aparecen_en_el_corpus` y `test_los_procs_del_catalogo_aparecen_en_el_programa_grande`:
    el catálogo es de lo que se usa, y una entrada inventada no pasa.
- Verificación: `uv run ruff check .`: limpio. `uv run pytest -q tests/unit/test_catalogo_sas.py`:
  34 pasadas. Suite completa: 2266 pruebas, 0 fallos, 0 errores, 155 omitidas (las series paralelas de
  `talend_item` quedaron verdes entre tanto).
- Métricas: 4 catálogos nuevos (9 + 17 + 9 + 4 = 39 entradas con página), 19 entradas de funciones
  corregidas, 2 nombres falsos fuera de la regla de informats, 1 documento de decisión.
- Bloqueos: la regla de `OPTIONS` sigue sin codificar; para cerrarla hacen falta el `autoexec` y los
  scripts de lanzamiento del cliente, que el repositorio no tiene.
- No verificado: los usos de cada función y de cada `PROC` salen del catálogo y del conteo sobre
  `client_large.sas`, no de ejecutar el programa. Que la tabla del traductor haga lo mismo que SAS en
  los bordes (missing, blancos finales) lo dicen sus avisos y las pruebas de expresión, no este hito.

## Hito 100d. R2-02 (parte 2): `job_producto` escribe los totales que leen `job_totales` y `job_conciliacion`; prueba en Studio parcial

- Fecha: 2026-11-05. Serie `d` (sesión sin Studio para R5-02 en paralelo; esta sesión sí usó Studio).
  Plan: `docs/plan-reescritura/ruta-a-produccion.md`, fila R2-02. Diseño: `docs/diseno-talend-exogena-depositos.md`,
  sección 1.2 (salidas de `job_producto`) y secciones 3.4 y 3.5.
- Estado: **parcial, no cerrado.** La parte que faltaba (que el `job_producto` emitido escriba los archivos que
  leen `job_totales` y `job_conciliacion`) está hecha y probada en Studio en una corrida. El intento siguiente
  quedó bloqueado por Studio (ver "Bloqueos").

### Qué se hizo

- `src/sgm/talend_item/flujos_totales.py` (nuevo, en el límite de 300 líneas): dos formatos (`tMap_tot_origen` y
  `tMap_tot_salida`) y dos escrituras con el esquema de `jobs_totales.COLUMNAS_TOTALES`:
  - `totales_origen_<sufijo>.csv`: el agregado de origen que ya tenía `job_producto` (`tAggregateRow_1`). Se
    añadió una operación: `saldos_origen`, conteo de saldos no nulos (un faltante no cuenta).
  - `totales_salida_<sufijo>.csv`: el agregado de la rama `validos` (`tAggregateRow_2`), que ya existía. El conteo
    de saldos no vacíos va vacío, como en el caso `L8/totales/04`.
  - Un campo nulo se escribe vacío, nunca como cero (`x == null ? "" : ...`). La suma sale con `toPlainString()`.
- `src/sgm/talend_item/jobs_producto.py` (285 líneas): parámetro `escribe_totales` (por omisión `False`; sin él el
  Job queda como antes). Exige la columna de saldo y la validación de producto; si falta una, falla con `ValueError`.
  Cuando hay totales, los logs `tLogRow_1` y `tLogRow_2` cuelgan del formato y no del agregado (ver hallazgo 1).
- `src/sgm/cli_talend.py`: `escribe_totales` vale cuando hay periodo, `archivo_totales` y validación. Pendientes
  nuevos: la definición de la salida (ver decisiones) y el conteo real de componentes de `job_producto` si pasa de 20.
  El aviso `Pendiente:` de que `job_producto` no escribe los totales solo sale si el flag no aplica.
- Pruebas: `tests/unit/test_talend_jobs_producto_totales.py` (8 pruebas nuevas). Ajustes legítimos de conteos fijos:
  `tests/unit/test_tablero.py` (`job_producto` de 21 a 25 componentes; total del programa grande de 63 a 67),
  `tests/unit/test_talend_emision_cuenta_real.py` y `tests/unit/test_talend_emision_flujos_fila.py` (21 a 25).
  Son 4 componentes netos: dos formatos y dos escrituras nuevas, más los dos logs que cuelgan del formato, menos
  los dos logs de los agregados que se quitan.
- Herramientas: `tools/prueba_totales_producto.py` (harness de Studio: emite, compila, exporta y corre los tres Jobs)
  y `tools/prueba_totales_producto_datos.py` (oráculo independiente con `csv`, `zipfile` y `Decimal`, sin usar el Job
  ni el productor de `tools/`).

### Decisiones

- **Definición de `totales_salida` (no cerrada).** Se usó "saldos validados" del manual (sección 1.2): las filas de
  la rama `validos` de `job_producto`, es decir, con `TIPO_DOC` homologado. Motivo: el encargo lo fija y es la única
  definición de `totales_salida` que da el manual. Las otras dos no se usaron:
  - `L8/totales/05` (válidos más rechazados, `CONCILIACION_*` del SAS): sí es una regla que el SAS demuestra para
    conciliar, pero el manual define la salida de otra forma.
  - `L8/totales/04` (`TIPO_CTA <> '03'`): el propio caso lo declara "regla de este caso, no del SAS".
  Consecuencia medida en Studio: con un rechazo, `origen - salida = rechazados` y `job_conciliacion` dice NO CONCILIA.
  Con la definición de `L8/05` el mismo caso concilia. El manual y `L8/05` no coinciden. Queda como decisión
  pendiente para negocio y el equipo; no se cambió el manual ni el caso.
- **Componentes de `job_producto`: 25, por encima del límite de 20 de G3 (antes 21, ya por encima).** No se
  dividió en un hijo `job_producto_totales`: la salida necesita las filas validadas, que solo existen en memoria
  dentro del Job. Un hijo tendría que repetir la validación del tipo de documento. El aviso `Pendiente:` de
  `sgm talend` lleva el conteo real.
- **Fecha de la prueba: `2026-10-01`** (`periodo_anio=2026`, `periodo_mes=10`, `periodo_dia=01`). El caso no declara fecha.
- **Codificación de `TIPO_DOC` en la prueba (ver salvedad 1).** Los códigos `TD01`..`TD04` del corpus se escriben como
  `1`..`4`, y el Excel de homologación se genera con `CNAME` numérico 1..4.
- **Oráculo:** calculado desde el CSV de origen (fila por fila, con `Decimal`). Un faltante no suma y un campo en
  blanco es faltante (`tests/corpus/semantica/vectores.yaml`). La tolerancia de comparación es 0,005 (`caso.yaml`).

### Hallazgos de Studio

1. **Un agregado no puede alimentar dos componentes.** Con dos conexiones principales, la segunda (el `tMap` de
   formato) recibía filas con los campos nulos. Las corridas `v100a` y `v100b` lo mostraron: `totales_origen_CTE.csv`
   con `CTE;origen;;;`. El log del agregado seguía bien (`90|90|988051`). Solución: un solo flujo principal del
   agregado al `tMap`, y el log sale del `tMap` como segunda salida (`log_origen`, `log_salida`).
2. **Salida sin filas en `v100a`.** Con `TIPO_DOC` tal cual (normalizado como numérico, ver salvedad 1) todas las filas
   salieron rechazadas y `totales_salida` quedó solo con cabecera. En `v100b`, con códigos numéricos, la salida sí
   tuvo fila, pero con los campos vacíos por el fan-out del hallazgo 1. Qué hace `tAggregateRow` cuando no entra
   ninguna fila sigue sin comprobarse (salvedad 3).

### Evidencia de Studio 8.0.1 (`PRJ_BANCOLOMBIA`, corrida `v100c`, la última completa)

Comando: `uv run python tools/prueba_totales_producto.py --proyecto "C:/Talend/8.0.1/studio/workspace/talendbancolombia-963626413/PRJ_BANCOLOMBIA" --java-bin "C:/Talend/8.0.1/zulu21.50.19-ca-jdk21.0.11-win_x64/bin" --m2 "C:/Talend/8.0.1/studio/configuration/.m2/repository" --sufijo v100c`.
Se quitan las líneas de `--context_param` y de pila (`at ...`) y el texto de `job_producto` del log, que es fijo.

```text
Proyecto: C:\Talend\8.0.1\studio\workspace\talendbancolombia-963626413\PRJ_BANCOLOMBIA
Sufijo: v100c
Compilando: ['job_producto_v100c', 'job_totales_v100c', 'job_conciliacion_v100c']
[tal_cual] job_producto CTE: código 0
CTE|origen|90|90|988051
CTE|salida|90||988051
[tal_cual] job_producto AHO: código 0
AHO|origen|65|65|662095
AHO|salida|65||662095
[tal_cual] job_totales: código 0
[tal_cual] job_conciliacion: código 0
job_conciliacion: CTE, AHO
Contenido literal de totales_exogena_20261001.csv:
PRODUCTO;TIPO;NRO_FILAS;NRO_SALDOS_NO_VACIOS;SUMA_SALDO
CTE;origen;90;90;988051
CTE;salida;90;;988051
AHO;origen;65;65;662095
AHO;salida;65;;662095
Contenido literal de conciliacion_20261001.csv:
PRODUCTO;DIF_FILAS;DIF_SALDO
CTE;0;0
AHO;0;0
RESULTADO tal_cual: OK
[planta] job_producto CTE: código 0
CTE|origen|90|90|988051
CTE|salida|89||1000056
[planta] job_producto AHO: código 0
AHO|origen|65|65|662095
AHO|salida|65||662095
[planta] job_totales: código 0
[planta] job_conciliacion: código 3
job_conciliacion: CTE, AHO
[ERROR] 14:57:47 prj_bancolombia.job_conciliacion_v100c_0_1.job_conciliacion_v100c- tDie_conc - The die message: NO CONCILIA CTE: diferencia de filas 1, diferencia de saldo -12005 (tolerancia 0)
Contenido literal de totales_exogena_20261001.csv:
PRODUCTO;TIPO;NRO_FILAS;NRO_SALDOS_NO_VACIOS;SUMA_SALDO
CTE;origen;90;90;988051
CTE;salida;89;;1000056
AHO;origen;65;65;662095
AHO;salida;65;;662095
Contenido literal de conciliacion_20261001.csv:
PRODUCTO;DIF_FILAS;DIF_SALDO
CTE;1;-12005
AHO;0;0
RESULTADO planta: OK
Limpieza: 6 archivos de Jobs borrados de process/ y builds borrados
Código de salida del harness: 0
```

Lectura: el oráculo (sin el Job) da origen CTE 90 filas, 90 saldos no vacíos y suma 988051; salida CTE 90 y 988051
(`tal_cual`), y en `planta` salida 89 y 1000056, con origen 90 = 89 + 1 rechazado. La fila plantada tiene saldo
`-12005`, así que la diferencia de saldo es `988051 - 1000056 = -12005`. `job_conciliacion` sale con 0 en
`tal_cual` y con 3 en `planta`, y el mensaje nombra a CTE con diferencia de filas 1 y de saldo -12005.

La corrida `v100c` se hizo antes de un cambio que no toca la lógica: la variable local `exogena` del harness se
renombró a `final` para pasar la regla de nombres (`test_no_script_specific_names`). Ver salvedad 5.

### Salvedades y lo no verificado

1. **Códigos de `TIPO_DOC` no originales.** El corpus `v05` trae `TD01`..`TD04`. El Job normaliza `TIPO_DOC` con el
   informat numérico del SAS (`input(left(VAR9), 8.)`, R1-03), así que `TD01` queda vacío y todas las filas se
   rechazan (`v100a`, `v100b`: 90 y 65). Por eso la prueba usa `1`..`4`. Con los códigos del corpus, la validación
   no se prueba de extremo a extremo. R1-03 sigue pendiente.
2. **Ubicación (R1-05) fuera del Job probado.** El harness no tiene insumos de ubicación. El Job que `sgm talend`
   emite sí la incluiría si el programa la declara. No se probó esa rama con totales.
3. **Sin filas validadas.** Si ninguna fila pasa la validación, `tAggregateRow_2` puede no emitir fila y
   `totales_salida` quedaría solo con cabecera. No se comprobó en Studio. `job_totales` y `job_conciliacion` no
   tienen tratamiento para ese caso.
4. **Definición de la salida.** Ver decisiones. Mientras no se decida, la conciliación de `client_large` no
   concilia cuando hay rechazos de tipo de documento.
5. **Harness modificado después de `v100c`.** Solo un renombre de variable local (`exogena` a `final`). El intento
   `v100d` con el harness final no llegó a ejecutarse (ver bloqueos).
6. **Protocolo.** El harness habla con el puente de Studio (`127.0.0.1:3927` y `3930`), el mismo protocolo de los
   hitos 85 a 98d. `AGENTS.md` prohíbe MCP en este trabajo; el encargo pidió Studio, y el puente no está en `src/`.
   Queda anotado para decidir si el protocolo de `tools/` se mantiene.
7. **No verificado:** paralelismo; `tUnite` (sigue sin compilar en Studio 8.0.1, hito 97d); las columnas de
   `TOTAL_AHORROS_CONS` y `TOTAL_CORRIENTE` (el SAS escribe 13 sumas, hito 97d); la tolerancia de negocio (DC-04).
   La corrida no repitió el caso `L8/totales/04` con este Job. Ese caso sigue cubierto por `v97j`, con el productor
   mínimo de `tools/`.

### Bloqueos

- **Studio dejó de responder durante la corrida `v100d`.** La compilación del lote falló con
  `BRIDGE_UNAVAILABLE`: "El bridge de Talend Studio en http://127.0.0.1:3930 no contesto en 25000 ms: Studio puede
  estar ocupado (compilando o con un dialogo abierto)". Una segunda llamada de salud
  (`talend_bridge_refresh_workspace`) devolvió `HTTP_500`: "El hilo de la interfaz de Studio esta ocupado (se acabo
  el tiempo de espera)". Puede haber un diálogo modal abierto. **No se reinició Studio.** La limpieza de la corrida
  fallida borró los 6 archivos copiados a `process/`; no quedó ningún Job `v100*` en el proyecto.
  Pendiente: repetir la corrida con un sufijo nuevo cuando Studio responda, para que el harness final quede con
  evidencia propia.

### Pruebas

- `uv run ruff check .`: sin errores.
- `uv run pytest -q -n auto` (corrida final, 171 s): 2111 pasadas, 26 omitidas y 129 `xfailed`, sin fallos. Una corrida
  anterior, hecha en paralelo con otra, falló en `tests/unit/test_invariantes_produccion.py::test_archivo_grande_compila_dentro_del_limite`
  por carga; pasa al correrla sola (5 de 5).
- Studio: `v100a` (fallo de fan-out y de codificación), `v100b` (fallo de fan-out, con códigos numéricos), `v100c` (OK, ambos escenarios), `v100d` (bloqueado en el puente).

### Métricas

- `flujos_totales.py`, `jobs_producto.py` (285 líneas), `cli_talend.py`, `tools/prueba_totales_producto.py` y
  `tools/prueba_totales_producto_datos.py` (cada uno debajo de 300 líneas).
- Componentes: `job_producto` 21 a 25; `job_totales` 13 y `job_conciliacion` 16 sin cambios. Total del programa grande: 63 a 67.
- Dependencias nuevas: ninguna.

### Bloqueos y pendientes de este hito

- Decisión de la salida de totales (validos del manual frente a validos más rechazados de `L8/05`).
- Repetir `v100d` cuando Studio responda.
- Dividir `job_producto` (25 componentes frente al límite de 20 de G3), o aceptar la excepción.
- Columnas de la exógena (`TOTAL_AHORROS_CONS`, `TOTAL_CORRIENTE`), tolerancia de negocio (DC-04) y `tUnite`.

## Hito 102. `AGENTS.md` declara la documentación de referencia: dónde está, cómo se cita y qué la vigila

- Fecha: 2026-11-05. Pregunta del usuario: si `AGENTS.md` sabe que existe esta documentación. No lo
  sabía: el archivo hablaba de `env/schemas.json`, del corpus y de las reglas, pero no nombraba
  `docs/referencia/`, ni los catálogos, ni la obligación de citar una página. Un agente que empezara
  hoy podía escribir reglas sin saber que hay 13 guías a un `grep` de distancia.
- Qué se hizo: sección nueva «Documentación de referencia» entre «Prohibido en esta tarea» y
  «Numeración de hitos», con siete puntos:
  - las 13 guías y los tres archivos de cada una (`<docset>.pdf` no versionado, `<docset>.txt` con
    marcas `<!-- página N -->`, `<docset>.INDEX.md` con sección → página), más las páginas de Talend
    por componente;
  - la receta para no leer el PDF ni el `.txt` entero: sección en el `.INDEX.md`, luego
    `grep -n "<!-- página 265 -->"` sobre el `.txt`;
  - el reparto «qué guía para qué»: `lrcon` semántica, `lestmtsref` sintaxis, `lefunctionsref`
    funciones, `leforinforref` formats e informats, `sqlproc` y `proc` procedimientos, `lesysoptsref`
    y `ledsoptsref` opciones, `mcrolref` macros, `lepg` uso, `gridref`/`hostunx`/`connref` entorno;
    con la advertencia de que el docset es `leforinforref` y `leforinfref` da 404;
  - `tools/referencia/`: quién es el catálogo de docsets, quién baja, quién genera índice y texto
    (con `uv run --with pypdf`) y quién cruza el catálogo de Talend con las páginas;
  - el esquema de `rules/sas/catalogo/*.yaml` (`schemas/rules/catalogo.schema.json`, campos `id`,
    `nombre`, `fuente`, `estado`) y el significado de los cuatro estados, incluido que `reconocida`
    vale tanto para una regla YAML como para la tabla de `src/sgm/expressions/`;
  - la regla de fondo: **si no hay página, no hay equivalencia**; se emite `Pendiente:` con el
    motivo, como hizo `docs/opciones-de-sistema.md`;
  - los dos archivos de prueba que lo vigilan y el aviso de que los `.pdf` están en `.gitignore`.
- Pruebas: dos nuevas en `tests/unit/test_referencia_tools.py` (15 en el archivo, 50 con
  `test_catalogo_sas.py`):
  - `test_agents_md_dice_donde_esta_la_documentacion`: `AGENTS.md` nombra `docs/referencia/`,
    `rules/sas/catalogo/` y `schemas/rules/catalogo.schema.json`;
  - `test_agents_md_nombra_cada_guia_sas`: cada docset de `fuentes.SAS_DOCSETS` aparece entre
    comillas invertidas. Se compara con comillas y no con el nombre suelto porque `proc` aparecería
    por casualidad dentro de `PROC SQL`: la prueba pasaría sin que la guía esté nombrada.
- Decisiones:
  - Una sección, no una línea en «Forma de trabajar». La documentación no es un hábito más: es de
    dónde sale lo que la regla 6 prohíbe inventar, y por eso va pegada a las prohibiciones.
  - La prueba se escribe contra `fuentes.SAS_DOCSETS`, no contra una lista copiada: al añadir una
    guía al catálogo, la prueba falla hasta que `AGENTS.md` la nombre. Es el mismo patrón de la
    prueba que exige fila en la tabla de `sas/README.md`.
  - No se documenta en `AGENTS.md` el detalle de qué guía falta por bajar (nlsref, STAT/ACCESS/ODS):
    eso es estado, cambia, y su sitio es `docs/referencia/README.md`. `AGENTS.md` dice dónde mirar.
- Métricas: `AGENTS.md` pasa de 39 a 71 líneas; 13 guías nombradas, 6 herramientas de
  `tools/referencia/`, 4 estados explicados; 2 pruebas nuevas.
- Bloqueos: ninguno.
- Verificación: `uv run ruff check .`: limpio. Suite completa: 2268 pruebas, 0 fallos, 0 errores,
  155 omitidas (las dos de este hito incluidas).
- No verificado: que un agente lea la sección no se puede probar. Las pruebas garantizan que está y
  que nombra las guías; que se use depende de que se lea, como el resto de `AGENTS.md`.

## Hito 102m. Plan del migrador general hasta producción

- Fecha: 2026-11-05
- Qué se hizo: se escribió `docs/plan-reescritura/plan-migrador-general.md` (DC-01 decidida: migrador general). Define el 100 % con siete criterios medibles (C1 a C7), la arquitectura por capas con contratos, el catálogo de traducciones SAS a Talend, la pirámide de pruebas rápida (anillos A a D, Studio solo en lote), 15 controles de calidad de los Jobs, 11 decisiones con valor por omisión (MG-D01 a MG-D11), 15 fases MG-P0 a MG-P14 con tareas, aceptación y horas (895 h de agente más las tareas de personas), compuertas GM0 a GM8, riesgos y el protocolo de cierre. Incorpora el uso opcional de `talend-mcp` por CLI o MCP como backend de verificación y construcción (MG-D11, MG-P0-07 a MG-P0-09 y la sección 4.1).
- Medido antes de escribirlo: `sgm talend`, `sgm proceso` y `sgm diseno` sobre un programa del corpus distinto de `client_large.sas` fallan o devuelven 0 Jobs (exigen YAML por programa).
- Pendiente: confirmación escrita del usuario para actualizar la regla 1 de `AGENTS.md` (MG-P0-07). Otra sesión editó `AGENTS.md` en paralelo y no se tocó.
- Sin cambios de código: no se corrieron pruebas nuevas.

## Hito 105m. Planes ejecutables del migrador general (MG-01 y MG-02) y degradación elegante

- Fecha: 2026-11-05
- Qué se hizo: con la habilidad `superpowers:writing-plans` se escribieron `docs/superpowers/plans/2026-11-05-mg-01-fundacion-rapida.md` (6 tareas: backend de Talend por archivos o CLI de `talend-mcp`, salud de Studio, compilación en lote, ciclo rápido) y `2026-11-05-mg-02-rebanada-vertical.md` (10 tareas: `sgm migrar` sin YAML para `PROC IMPORT`, `PROC SQL` simple y `PROC EXPORT`, contextos, validador, intérprete y aceptación del corpus L0 a L2), más un índice (`README.md`) con los diez planes siguientes.
- Hallazgos que cambian el plan maestro: (1) `sqlglot` y `jsonschema` ya están aprobadas desde el hito 80, así que MG-D02 no es una decisión pendiente; (2) el pipeline `analyze_program` y `compile_file` ya produce un `Plan` con operadores y candidatos de componente: no hace falta un IR nuevo, sino enriquecer sus parámetros y escribir el emisor de `Plan` a `.item`; (3) `sgm compile` sobre `l2_01` deja `read_file` solo con la ruta y el `derive` del `SELECT` con `assignments: []`.
- Requisito del usuario incorporado: el migrador no falla nunca, omite y documenta lo que no puede, y deja la configuración y las credenciales pendientes en contextos y en `configuracion-pendiente.md`.
- Sin cambios de código; no se corrieron pruebas nuevas.

## Hito 103. La prueba del cierre corría la suite dentro de la suite: un pytest anidado topaba con el guardia de borrado del entorno

- Fecha: 2026-11-05. Apareció al cerrar el hito de los planes: `test_tools_ci` fallaba en la suite
  completa y pasaba aislado. Se diagnosticó antes de tocar nada.
- Qué pasaba. El fallo era del paso **`cruces del corpus`** del propio cierre: `ruff` salía OK,
  `cruces` FALLA y `oráculo` OK. La salida del paso fallido no terminaba con el resumen de pytest,
  sino con
  `[safe-delete][SAFE_DELETE_BULK_CONFIRM_REQUIRED] {"count":293,"threshold":50,...}`.
  La prueba llamaba a `ci.main(["--sin-suite", "--sin-tablero"])`, que corre los pasos de verdad, y
  uno de ellos es `pytest -q -n0` sobre `test_corpus_totales_cruce.py` y `test_corpus_validaciones.py`
  — los mismos archivos que la suite ya estaba corriendo en ese momento. Al terminar, pytest limpia
  sus directorios `garbage-*` de `%TEMP%/pytest-of-<usuario>/`; con 293 archivos dentro, el guardia
  de borrado masivo del entorno corta la operación y el proceso anidado sale distinto de cero. Aislado
  pasaba porque el conjunto a borrar era pequeño.
- Por qué la prueba estaba mal escrita. El encabezado de `tests/unit/test_tools_ci.py` dice, desde el
  primer día: «No corre la suite (sería correr pytest dentro de pytest): los pasos se prueban con
  comandos triviales». Esta prueba hacía exactamente lo que el archivo prohíbe.
- Qué se hizo:
  - La prueba sustituye `ci.pasos` por dos pasos triviales con `monkeypatch` y comprueba lo que su
    nombre dice: que el cierre devuelve 0, imprime «Todo verde.» y arma el informe (`| uno | OK |`).
  - El mensaje del fallo ahora incluye el informe del cierre: antes solo decía `assert 1 == 0` y
    había que adivinar qué paso había fallado. Así se encontró este.
- Cobertura que no se pierde: los dos archivos del corpus son parte de la suite y corren en ella;
  `ruff check .` corre en el cierre y en `test_ruff_se_resuelve_en_el_entorno_de_uv`; el oráculo tiene
  `test_corpus_oraculo_faltantes.py` y `test_corpus_oraculo_sql.py`, y además pasó en la corrida que
  falló. Lo único que desaparece es la duplicación que causaba la carrera.
- Pruebas: `tests/unit/test_tools_ci.py`, 7 pasadas. Suite completa: 2272 pruebas, 0 fallos, 0 errores,
  155 omitidas. El proceso sale con código 1 porque el guardia del entorno corta la limpieza de los
  temporales de pytest al final de la corrida; no hay ninguna prueba roja. Una corrida mínima
  (`pytest -q tests/unit/test_agents_md.py`) sale con 0 y sin el mensaje, así que el código no lo
  altera el proyecto.
- Decisiones:
  - No se toca `tools/ci.py`: el cierre está bien; lo que estaba mal era correrlo dentro de la suite.
  - No se marca `skip` ni `xfail`. Una prueba que no puede correr en su propio entorno se arregla, no
    se silencia.
  - El arreglo vale aunque el guardia del entorno no exista: un `pytest -n0` anidado sobre los mismos
    archivos que la suite está corriendo es una carrera por diseño, y en una máquina sin guardia
    habría fallado igual de vez en cuando, más tarde.
- Métricas: 1 prueba reescrita, 1 mensaje de fallo que ahora explica el fallo, 0 pruebas perdidas.
- Bloqueos: el guardia de borrado del entorno sigue actuando sobre los temporales de pytest. Deja 74
  directorios `garbage-*` en `%TEMP%/pytest-of-<usuario>/` y corta la limpieza, con lo que la suite
  completa termina con código 1 aunque no haya pruebas rojas. Limpiarlos es un borrado masivo (293
  archivos en uno de ellos) y el propio guardia pide confirmación: queda para el usuario. No se tocó
  `tools/ci.py`, que no tiene la culpa.
- No verificado: que el guardia sea la única causa posible de un fallo del paso `cruces`. El detalle
  del paso se capturó en una de las corridas; las otras fallaron en la misma prueba con el mismo
  síntoma (0 fallos de test, código de salida distinto de cero).

## Hito 104. `AGENTS.md` dice cuál es el plan maestro y en qué orden se leen los tres planes

- Fecha: 2026-11-05. Pedido del usuario: «hazlo» sobre la asimetría anotada al cerrar el hito 102 —
  `AGENTS.md` ya describía la referencia de SAS, pero no el plan que dice qué hacer.
- Qué se hizo: sección «Planes y orden de lectura», después de la de documentación, con los tres
  documentos y su precedencia:
  - **`docs/plan-reescritura/ruta-a-produccion.md` es el plan maestro**: tareas `R<fase>-<n>` con
    dueño, dependencias, entrega y criterio de terminado; define N1 (paridad con el diseño manual, la
    meta que pidió el usuario), N2 (equivalencia verificada) y N3 (producción). Reemplaza el orden de
    trabajo de `tareas-agente.md` y de `plan-corpus-y-equivalencia.md`, que quedan como detalle.
  - **`docs/plan-reescritura/plan.md`**: arquitectura (frontend → grafo de linaje → modelo de proceso
    → emisores) y tabla «Estado por fase», la foto más reciente del avance.
  - **`docs/plan-sgm-v2/`**: vigente para reparto (`01`), contratos (`05`), ciclo de huecos (`03`),
    puntos de extensión (`04`) y calidad (`06`); **su secuencia de fases (`02-fases.md`) no**, porque
    quedó superada por `plan.md`.
  - Antes de tomar una tarea: el plan maestro entero (§0 explica cómo leerlo) y luego `PROGRESS.md`.
    El plan es la intención, `PROGRESS.md` el hecho; si el plan contradice el código, se corrige el
    plan o el código en el mismo cambio, nunca se deja la contradicción (es la regla que ya traía el
    README de `plan-sgm-v2`).
  - Lo que depende del nombre del cliente va a `decisiones/<programa>.*.yaml`, nunca a `src/` ni a
    `rules/`.
- **Corrección de una ruta muerta**: `docs/plan-sgm-v2/00-README.md` decía «Estos archivos van en el
  repositorio, en `docs/plan/`». Esa carpeta no existe con ese nombre: quien la siguiera no
  encontraba nada. Ahora dice `docs/plan-sgm-v2/`.
- **Atribución**: el cambio de `AGENTS.md` quedó dentro del commit `b57533b` («hito 102m») de la serie
  paralela, que commiteó el archivo mientras estaba sucio. El contenido es el de este hito; este commit
  trae el resto (la ruta muerta, las pruebas y esta entrada). No se reescribió la historia: `AGENTS.md`
  prohíbe enmendar y ese commit ya estaba publicado.
- Pruebas: `tests/unit/test_agents_md.py` (nuevo, 6 pruebas). Las dos de `AGENTS.md` que vivían en
  `tests/unit/test_referencia_tools.py` se trasladaron allí, no se borraron: ese archivo queda con 13
  pruebas de las herramientas de referencia y este con todo lo que se afirma sobre `AGENTS.md`.
  - `test_agents_md_dice_donde_esta_la_documentacion` y `test_agents_md_nombra_cada_guia_sas`: las dos
    trasladadas.
  - `test_agents_md_dice_cual_es_el_plan_maestro`: nombra los tres planes y la expresión «plan maestro».
  - `test_agents_md_avisa_que_la_secuencia_de_fases_de_plan_sgm_v2_esta_superada`: nombra
    `02-fases.md` y dice «superada». Es el error de orden que la sección existe para evitar.
  - `test_las_rutas_de_docs_que_agents_md_nombra_existen`: extrae con una expresión regular las rutas
    `docs/...` entre comillas invertidas y exige que existan. Hoy son 9; se comprobó que no pasa en
    vacío listándolas una por una.
  - `test_el_readme_de_plan_sgm_v2_no_apunta_a_una_carpeta_inexistente`: cierra la ruta muerta.
- Decisiones:
  - Un archivo de prueba propio para `AGENTS.md`. Las aserciones sobre un archivo no son pruebas de
    las herramientas de referencia; mezcladas, la prueba de referencia crecía por un motivo que no era
    el suyo.
  - La prueba de rutas es genérica y no una lista copiada: cualquier `docs/...` que se añada a
    `AGENTS.md` queda comprobado sin tocar la prueba. Descarta las rutas con comodín o con `<docset>`,
    que no son archivos concretos y no se pueden comprobar.
  - Se comprueban dos frases del texto («plan maestro», «superada»). Es una prueba frágil ante una
    reescritura de la redacción, y se acepta: lo que hay que garantizar es que la instrucción esté, y
    la instrucción es el texto.
  - No se tocó `ruta-a-produccion.md` ni `plan.md`: los lleva la serie paralela y este hito solo los
    cita. El plan maestro cambia a diario; `AGENTS.md` dice dónde está, no lo que dice hoy.
- Métricas: `AGENTS.md` pasa de 71 a 92 líneas; 3 planes con su precedencia, 9 rutas de `docs/`
  comprobadas, 1 ruta muerta corregida; 6 pruebas nuevas (2 de ellas trasladadas).
- Bloqueos: ninguno en este hito. La suite se pudo cerrar gracias al hito 103, que quitó el pytest
  anidado de `test_tools_ci`.
- Verificación: `uv run ruff check .`: limpio. `tests/unit/test_agents_md.py` y
  `tests/unit/test_referencia_tools.py`: 19 pasadas. Suite completa: 2272 pruebas, 0 fallos, 0 errores,
  155 omitidas.
- No verificado: que un agente respete el orden de lectura no se puede probar. Las pruebas garantizan
  que la instrucción está, que nombra el plan maestro y que las rutas a las que manda existen.

## Hito 103m. MG-01 cerrado: backend de Talend, salud de Studio, lote y ciclo rápido

- Fecha: 2026-11-05. Ejecución del plan `docs/superpowers/plans/2026-11-05-mg-01-fundacion-rapida.md`
  (seis tareas, un commit por tarea).
- Qué se hizo:
  - **`src/sgm/backend_talend/`** (`base.py`, `archivos.py`, `talend_cli.py`, `salud.py`): interfaz
    `BackendTalend` con `escribir`, `compilar_lote` y `verificar`. `ArchivosBackend` escribe el par
    `.item`/`.properties` con lo que ya había y no necesita Studio; `TalendCliBackend` hereda de él y
    añade la CLI con el ejecutor inyectado, tiempo máximo y traducción de `FileNotFoundError` y
    `TimeoutExpired` a `BackendNoDisponible`. Un contexto con credenciales se rechaza con
    `ValueError` antes de armar la línea de comandos.
  - **`tools/studio_salud.py`**: ping y diálogos, diez segundos de corte, una línea de salida y
    código 0 o 1. En esta máquina tarda 4,5 s y nombra los dos modales abiertos.
  - **`tools/corpus_lib/studio_lote.py`** y `corpus_studio.py lote`: copian los Jobs a `process/`
    con sufijo nuevo reutilizando `_copiar_jobs`, `sufijo_nuevo` y `renombrar` de `studio_validar`,
    compilan en **una** llamada y borran lo copiado en un `finally`, sin tocar Jobs ajenos.
  - **`tools/ciclo_rapido.py`**: `ruff` sobre los `.py` tocados, la suite sin la marca `studio` y el
    oráculo de cada caso tocado; corta en el primer fallo. La marca `studio` queda registrada en
    `pyproject.toml` y `addopts` pasa a `-n auto -m 'not studio'`.
  - **`tests/unit/test_backend_aislado.py`**: recorre los 199 módulos de `src/sgm/` y exige que
    ninguno nombre `talend-mcp`, `mcp_cliente` ni `"bun"` fuera de `backend_talend/`.
- **Lo que el plan suponía y no era así** (corregido contra la CLI real, respuestas guardadas en
  `tests/fixtures/talend_cli/`):
  1. `talend_bridge_ping` no devuelve un booleano `readWrite` sino `mode: "readWrite"`. La primera
     versión de la comprobación decía «no da permiso de escritura» con Studio en modo escritura.
  2. El ping **no ve los diálogos**: decía `readWrite` con dos modales bloqueando el IDE. La salud
     ahora pregunta también a `talend_studio_ui_dialogs` y nombra los títulos.
  3. `talend_job_build_batch` devuelve `data.result.jobs` (mapa nombre → `{ok, error}`), no las
     listas `compilan`/`noCompilan` del plan. Se acepta también la forma resumida como respaldo.
  4. `talend_job_verify` no acepta `context` (solo `job`, `run`, `installMissing`, `timeoutMs`): se
     manda `run: false` y el contexto se usa solo para rechazar secretos.
  5. `findings` es un mapa `{errors, warnings}`, no una lista: se aplana a `[ERROR] ...`/`[WARN] ...`.
- Decisiones:
  - Los nombres de la interfaz son los del plan (`BackendNoDisponible`, `ResultadoLote`,
    `Veredicto`, `comprobar_salud`), en español, como los módulos de `talend_item/`. `AGENTS.md`
    pide identificadores en inglés en archivos nuevos; se sigue el plan, que es más específico y fue
    aprobado, y se anota aquí.
  - `verificar` no ejecuta el Job (`run: false`): compilar no es ejecutar y el flujo de migración no
    quiere efectos externos.
- Pruebas: `test_backend_archivos.py` (4), `test_backend_talend_cli.py` (13),
  `test_backend_salud.py` (6), `test_backend_aislado.py` (2), `test_corpus_studio_lote.py` (4),
  `test_ciclo_rapido.py` (8). Suite completa: 2153 pruebas, 0 fallos, 26 omitidas, 129 xfailed.
- Medidas: salud de Studio 4,5 s; oráculo de un caso 2,0 s; veinte casos 38,7 s; suite completa
  94 s; ciclo con veinte casos ≈ 133 s (objetivo 90 s, no cumplido: el cuello es la suite).
- Bloqueo: **no se pudo compilar en lote contra Studio**. Hay dos modales abiertos y la salud lo
  detecta; `corpus_studio.py lote` llega a la comprobación y sale con 1 sin copiar Jobs. Falta
  medir el lote real (MG-P0-03 y MG-P0-09) cuando se cierren.

## Hito 104m. Primera rebanada vertical del migrador general: `sgm migrar` sin ningún YAML

- Fecha: 2026-11-05. Ejecución de las tareas 1 a 9 del plan
  `docs/superpowers/plans/2026-11-05-mg-02-rebanada-vertical.md`. La tarea 10 (lote en Studio) queda
  pendiente de que Studio esté libre.
- Qué se hizo: `sgm migrar <programa.sas> --out <carpeta>` toma un programa SAS y deja una carpeta
  que se abre en Studio y se lee sin abrir nada más: `process/` con el `.item` y el `.properties`,
  `contextos/<grupo>.yaml` con las rutas fuera del Job, `pendientes.md` con el código, el motivo y la
  línea del SAS de cada cosa que no se tradujo, `configuracion-pendiente.md` con lo que hay que
  llenar en cada entorno, `decisiones-tomadas.md` con lo que el migrador eligió y cómo cambiarlo, y
  `trace.json` más `migracion.log` con la traza a las líneas del SAS y la causa técnica de cada fallo.
  Sale con código 0 siempre; el 2 queda para el uso incorrecto de la línea de comandos.
- **Lo que el corpus dice, anillo por anillo** (43 casos de `L0` a `L2` en estado `traducible` o
  `revisado`, sobre 45 programas):
  - **Anillo A, el Job**: **15 de 45** casos se traducen completos, sin un solo pendiente que no sea
    de tipo — 7 de `L0`, 3 de `L1` y 5 de `L2`. Los otros 30 están en la lista viva
    `tests/corpus/migrar_pendientes.yaml` con su primer motivo, y esa lista es una prueba: un caso de
    fuera que tenga pendientes la rompe, y un caso de dentro que ya no tenga ninguno también.
  - **Anillo B, el intérprete del plan**: **14 de 43** casos dan las filas esperadas — 3 de `L0`, 3 de
    `L1` y 8 de `L2`. Los 29 restantes son `xfail(strict=True)` con el motivo escrito: 27 por pasos
    que el intérprete todavía no ejecuta (`sort`, `dedup`, `select`, `rename`, `aggregate`,
    subconsultas) y 2 por huecos del plan que no son suyos (abajo).
  - **Anillo C, Studio**: pendiente de la tarea 10.
- **Robustez** (la instrucción de no fallar nunca, medida): los **190** programas de
  `tests/fixtures/sas` se migran en **25 s en total**, sin una excepción, y los 190 dejan su
  `pendientes.md`. Un `PROC REG`, un archivo vacío, uno con bytes aleatorios, uno truncado a mitad de
  sentencia y un `%macro` sin `%mend` salen con código 0 y su explicación en el informe. Los 45 Jobs
  de `L0` a `L2` dan `validar_job(job) == []`.
- **Dos huecos del plan que no son del migrador**, anotados para los planes siguientes:
  1. `l0_02`: el `WHERE=` de un `SET` no llega al plan; el analizador lo descarta, así que el
     migrador no puede ni avisar. El caso sale con `P-ESQUEMA-VACIO` porque no queda ninguna columna
     demostrada.
  2. `l2_12`: el alias de la auto-unión se pierde y las dos referencias quedan
     `id_cliente < id_cliente`.
- **Dos defectos que la ejecución encontró**:
  1. Un operador del plan que no quedó en ningún `subjob` no se recorría nunca: el `PROC REG` existía,
     tenía su línea, y se perdía en silencio. Ahora los operadores que nadie reclamó se recorren al
     final, y `ResultadoMigracion.visitados` deja la invariante comprobable.
  2. Los `.properties` llevaban la fecha del reloj, así que dos corridas del mismo programa no eran
     comparables. El backend acepta una fecha y `sgm migrar` le pasa la de modificación del programa:
     dos corridas dan los mismos bytes y la prueba lo compara archivo por archivo.
- Decisiones:
  - **La lista de pendientes vivos no cuenta los `P-TIPO-DESCONOCIDO`.** Sin catálogo del entorno no
    hay tipo que demostrar y el Job se ejecuta igual con `String`; contarlos dejaría los 45 casos en
    la lista para siempre y la lista no diría nada. Lo que cuenta es lo que no se tradujo.
  - `migrar()` es la función pura y no lanza; `migrar_command()` es el envoltorio de `typer` y solo
    añade las dos validaciones de ruta.
  - `--backend talend` toma la carpeta de `talend-mcp` y el proyecto de `SGM_TALEND_DIR` y
    `SGM_TALEND_PROJECT`; sin ellas es uso incorrecto de la línea de comandos y sale con 2.
- Pruebas nuevas: `test_migrar_esquemas.py` (9), `test_desde_plan.py` (11),
  `test_desde_plan_contextos.py` (5), `test_validador_job.py` (8), `test_migrar_interprete.py` (5),
  `test_migrar_corpus_anillo_b.py` (43, 29 de ellos `xfail`), `test_cli_migrar.py` (10),
  `test_migrar_corpus_aceptacion.py` (49). Suite completa: **2273 pruebas, 0 fallos, 27 omitidas,
  158 xfailed** en 133 s.

### Hito 104m (cierre). Anillo C del migrador: el lote en Studio está escrito y no se pudo medir

- Fecha: 2026-11-05. Tarea 10 del plan `2026-11-05-mg-02-rebanada-vertical.md`.
- Qué se hizo: `tests/studio/test_migrar_lote.py`, con la marca `studio`. Migra los casos de `L0` a
  `L2` que la lista viva da por completos —los mismos que vigila la aceptación, ni uno más—, los
  compila **en una sola llamada** con `compilar_en_lote` y exige `no_compilan == {}` y que el número
  de compilados sea el de carpetas. Se salta con el motivo a la vista si faltan `TALEND_MCP_DIR` y
  `TALEND_PROJECT` o si `comprobar_salud` no da `Salud(True, ...)`: no se finge que pasó.
- **Lo que no se pudo medir, y por qué.** Dos comprobaciones seguidas, las dos con el mismo resultado:
  - `uv run pytest tests/studio -m studio -v` → `SKIPPED: faltan TALEND_MCP_DIR y TALEND_PROJECT en el
    entorno`.
  - Con las rutas documentadas en `docs/plan-reescritura/fase5-talend-instalado.md`
    (`C:/Users/USUARIO_BISOLUTION1/code/talend-mcp` y
    `C:/Talend/8.0.1/studio/workspace/talendbancolombia-963626413/PRJ_BANCOLOMBIA`),
    `uv run python tools/studio_salud.py --talend-dir ... --proyecto ...` sale con 1 y dice: «Studio
    no está disponible: no se pudo comprobar si hay diálogos abiertos: la CLI de talend-mcp no
    respondió en 10 s».
- Consecuencia: quedan sin hacer el paso 2 (medir el lote y anotar el tiempo) y el paso 3 (ejecutar
  con datos `l0_01`, `l2_01` y `l2_02` con `tools/corpus_studio.py validar` y pegar la salida). No es
  un fallo del migrador: la prueba está escrita, se salta sola y el día que Studio responda mide lo
  que tiene que medir. Es el mismo bloqueo que dejó abierto el hito 103m.
- Plan maestro: `docs/plan-reescritura/plan-migrador-general.md` gana el estado de MG-P1, MG-P2,
  MG-P5, MG-P8, MG-P10 y MG-P11 al 5 de noviembre, con lo hecho y lo que falta de cada uno.

## Hito 106m. MG-03: expresiones con evidencia y DATA step básico en los anillos A/B

- Fecha: 2026-11-06.
- Qué se hizo:
  - `SET(dataset(WHERE=(...)))` conserva la expresión al analizar fuentes, la baja a filtro en el plan
    y la emite en `expressionFilter` del `tMap`. `l0_02_where_opcion` ya no figura en la lista viva
    de pendientes.
  - Se añadieron regresiones de anillo A para `WHERE=` y para transformaciones aisladas `KEEP`,
    `DROP` y `RENAME`; esos modificadores sin asignación ahora se emiten como `tMap`.
  - El intérprete de referencia evalúa subsetting `IF` con la regla SAS documentada: verdadero si el
    valor numérico no es cero ni faltante (`lestmtsref`, p. 130). Añadidas implementaciones puntuales
    y pruebas del anillo B para las funciones L4 respaldadas por los vectores del repositorio: `INPUT`
    con informat `w.d`, `LEFT`, `SUBSTR`/`SUBSTRN`, `COALESCEC`, `COMPRESS`, `SCAN` y `ROUND`.
  - El anillo B compara nombres de tablas y columnas sin distinguir mayúsculas, conforme al contrato
    del intérprete; no altera ni regenera los CSV esperados.
- Continuación A/B:
  - Se implementaron ramas encadenadas `IF/THEN`, `ELSE IF` y `ELSE` para asignaciones al mismo
    destino, tanto en la evaluación del plan como en la expresión ternaria emitida por `tMap`.
    El intérprete ahora evalúa asignaciones DATA step en orden; `l0_12_bandera_numerica` pasa en B y
    salió de la lista viva de pendientes.
  - Se actualizó el golden de `generalization/etl_archivos_simple.sas`: la cadena `ELSE IF` deja de
    generar un `filter` inválido y pasa a una derivación ternaria única. La prueba de equivalencia
    sigue activa contra ese nuevo plan; la coincidencia de filas no se toma del golden.
  - `l0_07_if_then_else` también pasa en B y se quitó su `xfail`. Sigue en la lista A con
    `P-ESQUEMA-VACIO`: sin catálogo ni ruta de muestra resoluble, `sgm migrar` no demuestra la
    columna `saldo`; no se inventó su esquema.
  - La aceptación del corpus compara la clave real del primer pendiente y confirmó los motivos
    vigentes para `l0_07` y `l0_13`.
- Pruebas: anillo B completo: 42 pasan y 20 quedan `xfail` con sus motivos; suite completa:
  **2335 passed, 27 skipped, 149 xfailed**. `uv run ruff check .`: limpio. La verificación
  focalizada de B, emisor, aceptación y goldens: 130 pasan, 1 se salta y 20 `xfail`.
- Anillo C: el lote `tests/studio/test_migrar_lote.py -m studio` pasó; compilaron los 17 Jobs
  completos de L0–L2 en una sola llamada. La ejecución representativa pasó en Studio para
  `l0_06_asignacion` (cálculo) y `l0_02_where_opcion` (filtro), ambos comparados contra sus CSV
  esperados. Se migraron con `--muestra` para que la cabecera demostrara todas las columnas; sin la
  muestra, la prueba de ejecución inicial evidenció columnas faltantes y no se contó como éxito.
  `--java-bin` apuntó al JDK Zulu 21 incluido con Studio, pues no hay `java` en el `PATH`.
- Alcance pendiente de MG-03: `OUTPUT` condicional, catálogo íntegro de vectores y funciones, y
  verificación C. MG-P3-02/03/05 permanecen parciales, y MG-P3-04/06/09 y MG-P4-02 a 09 siguen
  pendientes. El estado detallado queda en
  `docs/plan-reescritura/plan-migrador-general.md`.
- Decisiones: solo se amplía la cobertura B a casos L4 marcados traducibles/revisados; los casos cuyo
  alcance excede el plan conservan su `xfail`. Se mantiene `l0_04_drop` en la lista viva mientras sus
  pendientes no estén resueltos.
- No se completan por este plan `OUTPUT` condicional/múltiple, el catálogo íntegro de funciones y
  vectores, ni los bloques MG-P3-04/06/07/08/09 y MG-P4-02 a 09. Cada sentencia sin representación
  completa permanece pendiente; no se declara soporte de `MERGE`, estado por fila ni macros. El
  estado de MG-03 se limita a las capacidades descritas arriba, no a cerrar MG-P3 o MG-P4 globales.

## Hito 107. MG-03: modificadores de COMPRESS, delimitadores de SCAN y OUTPUT explícito

- Fecha: 2026-11-06.
- Qué se hizo:
  - `COMPRESS` traduce los modificadores `K`, `D` e `I` usados por L4; listas literales se tratan
    como caracteres y los modificadores no implementados dejan la expresión pendiente.
  - `SCAN` usa el juego de delimitadores ASCII documentado para SAS, devuelve cadena vacía cuando
    falta la palabra solicitada y rechaza la cuenta cero, que la guía define como inválida. Fuente:
    `lefunctionsref.pdf`, CALL SCAN p. 442 y SCAN p. 1505.
  - Cada operación derivada de sentencia DATA step conserva evidencia de la línea concreta.
    `OUTPUT` explícito conserva destino y rama en la IR; sin emisor de salidas múltiples queda
    pendiente, no se pierde ni se inventa una traducción.
  - Se actualizaron los golden afectados por el cambio intencional de evidencia y nodos `OUTPUT`;
    las pruebas de igualdad y de compatibilidad de goldens pasan sin relajar su contrato.
- Pruebas: suite completa **2358 passed, 27 skipped, 149 xfailed**; `uv run ruff check .` limpio.
  Anillo A L4: 20 pasaron. Anillo B focalizado: 142 pasaron, 1 se saltó y 20 `xfail`.
- Anillo C: una compilación conjunta pasó para 24 Jobs (17 completos L0–L2 y siete L4 de
  `COMPRESS`/`SCAN`). `l4_06_compress_modificador_k` y `l4_14_scan_palabra` se ejecutaron en Studio
  con el JDK de Studio y coincidieron con sus CSV esperados.
- Bloqueos/hallazgos: un lote exploratorio de todos los casos L4 falló en cinco Jobs por
  incompatibilidades Java: dos casos `INPUT`, `ROUND`, comparación de tipo y `PUT` de fechas. Se
  excluyeron del lote C enfocado y quedan sin validación de Studio; no se declaran resueltos.
- Decisiones: se limita la aceptación C a los casos de las funciones implementadas en este cierre;
  la compilación amplia no se usa para atribuir soporte a los casos con incompatibilidades. MG-04
  no se inicia en este hito. El alcance aún pendiente está detallado en
  `docs/plan-reescritura/plan-migrador-general.md` y al final del plan ejecutable de MG-03.

## Hito 108m. El plan maestro pasa a ser el del migrador general, con su porcentaje de avance

- Fecha: 2026-11-06.
- Qué se hizo:
  - `AGENTS.md` declara `docs/plan-reescritura/plan-migrador-general.md` como plan maestro y deja
    `ruta-a-produccion.md` como detalle subordinado (pista del programa grande y operación). El orden de
    lectura antes de tomar una tarea parte del plan del migrador general.
  - `ruta-a-produccion.md` y `plan.md` llevan un aviso al principio que remite al plan maestro.
    `plan-migrador-general.md` marca su sección 2 como foto de partida superada.
  - Nueva sección 11b de `plan-migrador-general.md`: avance medido con método reproducible (crédito
    por tarea multiplicado por sus horas). Resultado: **175,75 de 895 h, 19,6 %**; por fase, P0 68 %, P1 58 %,
    P2 24 %, P3 18 %, P4 8 %, P5 15 %, P6 5 %, P7 0 %, P8 19 %, P9 25 %, P10 23 %, P11 13 %, P12 0 %,
    P13 4 %, P14 0 %.
  - `tests/unit/test_agents_md.py` exige también que `AGENTS.md` nombre `plan-migrador-general.md`.
- Decisiones: el crédito de cada tarea es un juicio mío a partir de las secciones «Estado» y de
  `PROGRESS.md`; las tareas heredadas que nadie midió contra el corpus (macros) cuentan 0. Los
  termómetros del corpus (anillo B 42 de 62, anillo A 17 de 45 en L0 a L2) acompañan la cifra de horas.
- No se commitea: los cambios de código sin commitear de antes de este hito no son de este trabajo.
- Reparto (misma fecha): `docs/plan-reescritura/reparto-andres-byron.md` divide las 719,25 h que
  faltan en 359,0 h (Andres: P1, P4, P5, P8, P9, P14) y 360,25 h (Byron: P0 resto, P2, P3, P6, P7, P10 a
  P13), con dueños por directorio, letras de serie (`m` Andres, `n` Byron) y puntos de encuentro.
- Hallazgo: `origin/main` tiene 14 commits de Byron (`hito 20` a `33`, 3 de noviembre) sobre el hito
  19; el `main` local los supera por 144 y hay solapamiento en `expressions/` y en la numeración. No se
  subió nada: la integración es la tarea 0 del reparto.

<!-- Hitos 20n a 33n: serie de Byron integrada desde origin/main el 2026-11-06 (6 de noviembre); sus números
originales 20 a 33 chocaban con los de la serie principal. Ver docs/plan-reescritura/reparto-andres-byron.md. -->


## Hito 20n. Dejar INPUT con informat dinámico pendiente

- Fecha: 2026-11-03
- Qué se hizo: se dividió el traductor en núcleo, lexer, parser, familias de funciones y registro. La fachada conserva `translate_to_talend`, `Unsupported`, `Result` y `E`; `ExpressionParser` recibe el registro por argumento. Los ocho módulos tienen menos de 300 líneas.
- Comportamiento: el parser valida la procedencia antes de serializar el informat. Acepta un único token `fmt`, `str` o `num` con punto que cumpla `\d+\.\d*`; macros sin resolver, columnas y expresiones compuestas quedan pendientes con una explicación en español que no reproduce valores. Los mapeos de literales no cambian.
- Pruebas: se observó RED para las macros, columnas y expresiones compuestas antes del cambio. Las pruebas sintéticas verifican el hueco `FUNCION_NO_MAPEADA` sin candidata, literales numéricos/de texto/fecha, macro constante expandida, aritmética numérica y mensajes sin valores de origen. La macro constante mantiene su traducción inline existente, sin duplicarla como candidata.
- Métricas: el segundo adjunto se recompiló solo en memoria mediante `compile_batch`, antes y después. Conserva 21 candidatas y 21 huecos; sus cuatro llamadas INPUT candidatas tienen un único informat numérico literal. No demuestra informats dinámicos. En el caso sintético de macro sin resolver, una candidata pasa a cero y aparece un hueco de función no mapeada. No se modificó `metrics/baseline.json`.
- Decisiones: mantener informats dinámicos pendientes hasta contar con un valor literal demostrado; conservar el token numérico con punto evita alterar la tokenización de las expresiones numéricas generales. No se agregaron dependencias ni datos de los adjuntos.
- Verificación: `uv run pytest -q`: 392 pasan, 1 se salta; focalizadas: 44 pasan; `uv run ruff check .`: limpio; `uv run sgm rules validate`: válido; `uv run sgm metrics tests/fixtures/sas --check`: ninguna métrica empeora (189 programas). `git diff --check`: limpio. El control de tiempo se repitió sin pytest concurrente después de dos mediciones afectadas por contención; no se cambió la línea base.
- Bloqueos: ninguno. Continúa pendiente validar las candidatas literales en Talend Studio.


## Hito 21n. Corregir bordes de INPUT

- Fecha: 2026-11-03
- Qué se hizo: se rechazan informats con macrovariable sin resolver dentro de comillas dobles en INPUT/INPUTN; se conservan cadenas simples y macros ya expandidas. El lexer reconoce formatos con dígitos intercalados y mantiene exactamente el Java de e8601da./e8601dt. en INPUT y PUT, sin aceptar columnas calificadas ni expresiones compuestas.
- Evidencia: cada asignación DATA conserva archivo, línea inicial y final en metadatos internos del operador. Se propagan al fusionar o reemplazar operadores, y p10 usa ese origen para el hueco. Las firmas, parámetros y el JSON de operadores no cambian. Dos referencias golden actualizan solo la evidencia de seis huecos de asignación.
- Diagnósticos: ambos lexers de expresiones emiten un motivo estático, sin fragmentos del origen; se cubren la excepción directa y las advertencias del wrapper translate.
- Pruebas: RED observado para macros entre comillas dobles, cuatro combinaciones ISO, evidencia DATA multilínea (derive agrupado y map fusionado) y fuga léxica directa y del wrapper. Las regresiones conservan literales simples, macros expandidas y rechazo de columnas/expresiones.
- Decisiones: guardar la evidencia por texto de expresión fuera de los parámetros evita alterar firmas, deduplicación y contratos JSON; se conserva y une en Graph.merge/replace. El error léxico mantiene el motivo útil sin reproducir valores. El lexer inline existente recibe solo este saneamiento puntual; no se amplía el alcance a su modularización.
- Bloqueos: ninguno.
- Verificación: focales de expresiones, evidencia IR y golden: 86 pasan; `uv run pytest -q`: 409 pasan, 1 se salta (86,85 s); `uv run ruff check .`: limpio; `uv run sgm rules validate`: válido; `uv run sgm metrics tests/fixtures/sas --check`: ninguna métrica empeora en 189 programas, sin modificar baseline. La primera suite señaló únicamente dos golden con evidencia antigua; se actualizaron solo esas ubicaciones y se repitió completa. El diff respeta los finales de línea históricos y pasa el control de espacios con CRLF permitido.


## Hito 22n. Preservar origen de filtros repetidos

- Fecha: 2026-11-03
- Qué se hizo: la evidencia interna usa la ruta estructural de cada ocurrencia en los parámetros (asignación, paso o rama), en lugar del texto de la expresión. DATA registra el origen preciso de filtros y asignaciones; p06 rebasa las rutas al formar pasos y ramas; p10 consulta la ocurrencia correspondiente. Se elimina el transporte plano al reemplazar operadores y se mantiene la unión por ruta al fusionar operadores equivalentes.
- Pruebas: RED observado para filtro/asignación con texto idéntico en líneas 3 y 4, dos asignaciones repetidas y dos filtros repetidos. Las regresiones verifican archivo y rango de cada hueco por separado; también se cubren ramas fusionadas con expresiones iguales.
- Compatibilidad: no cambia la traducción, parámetros, firmas ni JSON del operador. Se revisaron todos los consumidores del metadato. La fusión SQL produce exec_sql, sin consumidores de expresión en p10; la fusión de flujo conserva rutas por paso/rama. Una referencia golden actualiza únicamente la evidencia de un hueco de filtro al rango preciso.
- Decisiones: usar rutas de ocurrencia evita que expresiones iguales de constructos o posiciones distintas compartan origen. La evidencia permanece fuera de los parámetros y las firmas. Sin dependencias nuevas.
- Plan: se marcaron completos los ocho pasos tras verificar evidencia, implementación, regresiones, actualización de PROGRESS y commits de los hitos 20–22.
- Bloqueos: ninguno; la re-revisión acotada de la ronda 2/5 quedó aprobada sin nuevas regresiones.
- Verificación: 99 focales pasan; `uv run pytest -q`: 413 pasan, 1 se salta (100,69 s); `uv run ruff check .`: limpio; `uv run sgm rules validate`: válido; `uv run sgm metrics tests/fixtures/sas --check`: ninguna métrica empeora en 189 programas, baseline sin cambios. La ejecución focal inicial señaló la referencia golden del filtro con rango antiguo; se actualizó exclusivamente esa evidencia y se repitieron focales y suite completa. Autor revisión: consumidores y fusiones revisados, diff limpio permitiendo CRLF histórico; módulos afectados menores de 300 líneas.

## Hito 23n. Corregir macros y evidencia de origen

- Fecha: 2026-11-03.
- Qué se hizo: una llamada de macro sin expandir dentro de un informat entre comillas dobles queda como `FUNCION_NO_MAPEADA`, sin candidata. La expansión conserva los literales entre comillas simples y sustituye las macrovariables conocidas en comillas dobles.
- Evidencia: los filtros y asignaciones DATA usan el archivo y el rango inclusivo de la sentencia que produjo el lexer, también cuando la sentencia llegó por inclusión o desde una macro de otro archivo. El plan sigue perteneciendo al programa que la compiló.
- Pruebas: antes del arreglo, seis casos sintéticos fallaron por los cuatro hallazgos y dos controles pasaron. Después pasaron 119 focales con cobertura de macros, rangos, fusión, ocurrencias repetidas y golden. Suite final: 421 pasan y una se salta (102,38 s). Ruff limpio y reglas válidas.
- Métricas: el trinquete final pasa con 13,5 s para 189 programas, 8532 pasos SAS, 629 nodos y 1328 componentes. Dos mediciones anteriores excedieron solo el tiempo (21,3 y 21,6 s frente a 15,9 s + 20 %). El hito 22, cargado en memoria bajo las mismas condiciones, registró 21,4 s. La sustitución y el etiquetado DATA sumaron 0,021 s en el perfil. Se conservó la línea base.
- Decisiones: conservar las dos clases de comillas de SAS antes de traducir el informat, sin añadir equivalencias. Guardar el origen en cada sentencia conserva las rutas por ocurrencia del hito 22 incluso si un mismo DATA combina archivos distintos.
- Bloqueos: ninguno. Las candidatas históricas siguen pendientes de validación en Talend Studio.


## Hito 24n. Preservar espacios en literales SAS de expresiones

- Fecha: 2026-11-03
- Qué se hizo: la limpieza previa al parseo ahora colapsa espacios solo fuera de literales; conserva intactos los espacios en cadenas con comillas simples o dobles y las comillas duplicadas de SAS.
- Hallazgo: `_clean` aplicaba una expresión regular sobre todo el texto. Cuatro regresiones RED demostraron que `'a   b'`, `"a   b"`, cadenas con comillas SAS duplicadas y concatenaciones cambiaban el contenido antes de traducirse a Java.
- Pruebas: las cuatro regresiones pasan tras el cambio; no cambia la normalización de espacios alrededor de expresiones.
- Verificación: `uv run pytest -q`: 425 pasan y 1 se salta; `uv run ruff check .`: limpio; `uv run sgm rules validate`: válido; `uv run sgm metrics tests/fixtures/sas --check`: ninguna métrica empeora (189 programas, 8532 pasos SAS, 629 nodos, 1328 componentes); `git diff --check`: limpio.
- Decisión: los espacios dentro de un literal son datos y no se normalizan. No se agregaron dependencias ni se modificó la línea base.
- Bloqueos: ninguno.


## Hito 25n. Evitar índices inválidos al traducir SCAN

- Fecha: 2026-11-03
- Qué se hizo: las posiciones enteras negativas de `SCAN` cuentan desde el final y usan un índice dinámico protegido por la longitud del arreglo. Cero, decimales y valores mayores al rango de índice de Java quedan pendientes; ya no se truncan ni producen índices negativos o literales Java inválidos.
- Evidencia: `tests/fixtures/sas/real/learning-sas-by-example/Example_code/Programs_Used_in_the_Second_Edition.sas` contiene `scan(Name,-1,' ')` en las líneas 1595 y 2112 para obtener el último nombre.
- Pruebas: RED observado para el índice negativo, cero y posiciones fraccionarias; una regresión adicional confirma que una posición fuera del rango de Java queda pendiente. Focales: 6 pasan. Suite final: `uv run pytest -q`: 430 pasan y 1 se salta; Ruff limpio; reglas válidas; `git diff --check` limpio.
- Métricas: `sgm metrics tests/fixtures/sas --check` alternó entre una corrida válida de 19,16 s y mediciones de 20,3–23,2 s, frente al límite 19,08 s. Comparación aislada: Hito 24 23,1 s y Hito 25 23,0 s; ambas exceden el umbral, por lo que no se atribuye el tiempo al cambio de SCAN. El perfil midió la normalización nueva en 0,033 s para 877 expresiones y SCAN en 6 llamadas con tiempo redondeado a 0. No se modificó la línea base.
- Decisión: solo se traduce la posición negativa cuando es un entero dentro del rango de índices Java; las demás quedan pendientes hasta probar su equivalencia.
- Bloqueo: el trinquete de tiempo sigue excediendo el límite de forma variable también en la revisión Hito 24. Mantenerlo visible y no relajar la línea base.


## Hito 26n. Traducir COMPRESS con modificador de dígitos demostrado

- Fecha: 2026-11-03
- Qué se hizo: el parser admite el segundo argumento omitido únicamente en llamadas a `COMPRESS` y lo distingue del literal SAS `.`. El traductor cubre el patrón `compress(origen,,'kd')` con `StringHandling.EREPLACE` y la clase explícita `[0-9]`; otras combinaciones de modificadores o una lista de caracteres quedan pendientes.
- Evidencia: `tests/fixtures/sas/real/learning-sas-by-example/Example_code/Programs_Used_in_the_Second_Edition.sas` usa esta forma para limpiar números en las líneas 1228, 1520, 1527, 1529 y 3892; el comentario junto al caso telefónico indica que conserva los dígitos.
- Pruebas: la traducción directa verifica Java y guarda de nulo. Seis combinaciones no demostradas verifican que no se generaliza el mapeo. RED observado para el argumento vacío y para el literal `.` confundido con una omisión; 7 focales pasan.
- Verificación: `uv run pytest -q`: 437 pasan y 1 se salta; `uv run ruff check .`: limpio; `uv run sgm rules validate`: válido; `uv run sgm metrics tests/fixtures/sas --check`: ninguna métrica empeora (189 programas, 8532 pasos SAS, 629 nodos, 1328 componentes); `git diff --check`: limpio.
- Decisión: soportar solo la combinación literal `kd` con lista de caracteres omitida, porque es la forma probada; no inferir combinaciones equivalentes por orden o variantes de modificadores.
- Bloqueo: la expresión Java candidata aún requiere validación en Talend Studio; permanece sujeta a revisión.


## Hito 27n. Preservar punto decimal en COMPRESS con KD

- Fecha: 2026-11-03
- Qué se hizo: se amplió la combinación demostrada de `COMPRESS` para aceptar una lista de caracteres igual al literal `'.'` con el modificador exacto `'kd'`. La expresión conserva dígitos y punto decimal con el patrón `[^0-9.]`; otras listas explícitas siguen pendientes.
- Evidencia: `tests/fixtures/sas/real/ci360-download-client/macros/dsc_create_attrib.sas`, línea 97, reemplaza la coma decimal por punto y luego usa `compress(...,'.','kd')` para extraer la precisión numérica de tipos como `decimal(13,6)`.
- Pruebas: una regresión verifica el Java exacto y dos variantes de lista de caracteres sin evidencia quedan como `Unsupported`. RED observado antes del cambio. 10 focales pasan.
- Verificación: `uv run pytest -q`: 440 pasan y 1 se salta; `uv run ruff check .`: limpio; `uv run sgm rules validate`: válido; `uv run sgm metrics tests/fixtures/sas --check`: ninguna métrica empeora (189 programas, 8532 pasos SAS, 629 nodos, 1328 componentes); `git diff --check`: limpio.
- Decisión: aceptar solo el punto literal con `kd`, que es la combinación probada; no generalizar la construcción de clases regex para otras listas.
- Bloqueo: la rutina candidata aún requiere validación en Talend Studio.


## Hito 28n. Escapar listas literales de COMPRESS en Java

- Fecha: 2026-11-03
- Qué se hizo: los patrones de caracteres múltiples para `COMPRESS` ahora pasan por el escapado regex y luego por el serializador de literales Java. La llamada de referencia con espacio, paréntesis, guion y punto deja de emitir escapes inválidos en la cadena Java. Las listas que contienen barras invertidas o caracteres de control quedan pendientes porque el parser todavía no conserva el literal original separado de su representación Java.
- Evidencia: `tests/fixtures/sas/real/learning-sas-by-example/Example_code/Programs_Used_in_the_Second_Edition.sas`, línea 1513, usa `compress(Phone,' ()-.')`.
- Pruebas: una regresión comprueba la cadena Java escapada; casos con barra invertida y salto de línea verifican que no se emite una candidata dudosa. RED observado antes del cambio; 13 focales pasan.
- Verificación: `uv run pytest -q`: 443 pasan y 1 se salta; `uv run ruff check .`: limpio; `uv run sgm rules validate`: válido; `uv run sgm metrics tests/fixtures/sas --check`: ninguna métrica empeora (189 programas, 8532 pasos SAS, 629 nodos, 1328 componentes); `git diff --check`: limpio.
- Decisión: no reconstruir caracteres que ya llegan escapados en Java ni literales con controles; se dejan pendientes hasta que el lexer conserve el valor SAS original.
- Bloqueo: la rutina candidata requiere validación en Talend Studio.


## Hito 29n. Conservar el valor de literales SAS en expresiones

- Fecha: 2026-11-03
- Qué se hizo: los nodos de cadena ahora conservan, además del Java serializado, el valor literal SAS ya decodificado. `COMPRESS` usa ese valor para sus caracteres y modificadores; ya no intenta reconstruirlo desde escapes Java. Las listas con barra invertida se traducen correctamente y las cadenas con caracteres de control quedan pendientes.
- Hallazgo: la serialización Java duplicaba las barras invertidas, por lo que el hito 28 no podía distinguir una barra del escape generado por Java. También se detectó que una lista vacía producía una regex no demostrada; ahora queda pendiente.
- Pruebas: RED observado para una lista con barra invertida y para `compress(value,'')`; ambas regresiones pasan tras el cambio. Se mantiene la prueba de salto de línea pendiente. 14 focales pasan.
- Verificación: `uv run pytest -q`: 444 pasan y 1 se salta; `uv run ruff check .`: limpio; `uv run sgm rules validate`: válido; `git diff --check`: limpio.
- Métricas: `sgm metrics tests/fixtures/sas --check` marca solo `tiempo_compilacion_s`: 22,4 s en esta rama frente a 23,2 s en el commit Hito 28; ambos exceden el límite 19,08 s. No se modificó la línea base.
- Decisión: conservar el valor SAS decodificado en `E.literal`; no serializar caracteres de control como literales Java hasta tener un escapado completo.
- Bloqueo: el umbral temporal también falla en el commit de control; queda pendiente una corrida dentro del límite, sin atribuirlo a este cambio.

## Hito 30n. Escapar los delimitadores de SCAN en Java

- Fecha: 2026-11-03
- Qué se hizo: SCAN construye sus patrones desde el valor SAS decodificado y serializa cada regex como literal Java. Los delimitadores punto, ampersand y barra invertida quedan escapados en ambas capas. Los delimitadores personalizados vacíos, no literales o con caracteres de control quedan pendientes.
- Evidencia: tests/fixtures/sas/real/ts-sas-legacy-analytics/Macro/RunAll.sas, líneas 131–132, separa el nombre y la extensión con scan(basename,1,".") y scan(basename,2,".").
- Pruebas: se observó RED para punto, ampersand y delimitador vacío. Las nueve pruebas focales de SCAN pasan, incluidas las regresiones de punto, ampersand, barra invertida y delimitador vacío.
- Verificación: uv run pytest -q: 448 pasan y 1 se salta (100,14 s); uv run ruff check .: limpio; uv run sgm rules validate: válido; git diff --check: limpio.
- Métricas: uv run sgm metrics tests/fixtures/sas --check excede únicamente tiempo_compilacion_s: 24,1 s frente al límite 19,08 s. En el commit de control Hito 29, medido por separado, registró 23,6 s y excedió el mismo límite. No se modificó la línea base.
- Decisión: conservar el valor literal SAS para separar el escape regex del escape Java; no inferir comportamiento para delimitadores vacíos ni controles. Sin dependencias nuevas.
- Bloqueos: el tiempo del corpus continúa sobre el umbral también en el control; las expresiones candidatas requieren validación en Talend Studio.

## Hito 31n. Escapar los literales de patrones LIKE

- Fecha: 2026-11-03
- Qué se hizo: LIKE ahora toma el patrón SAS decodificado, escapa los caracteres que pertenecen al texto y serializa el resultado como literal Java. Solo los comodines % y _ se convierten en .* y ., respectivamente. Los patrones calculados y los que contienen caracteres de control quedan pendientes.
- Hallazgo: el parser reconstruía el patrón desde Java ya serializado y dejaba metacaracteres como punto o asterisco activos en el regex. También intentaba tratar una expresión de texto calculada como literal.
- Evidencia de wildcard: tests/fixtures/sas/real/ci360-download-client/macros/dsc_appendtocustomerdb.sas, línea 41, usa LIKE con un comodín % al final del patrón.
- Pruebas: RED observado para los metacaracteres punto y asterisco, patrones calculados y caracteres de control. Las cinco pruebas focales pasan; la barra invertida conserva su traducción esperada.
- Verificación: uv run pytest -q: 453 pasan y 1 se salta (97,50 s); uv run ruff check .: limpio; uv run sgm rules validate: válido; git diff --check: limpio.
- Métricas: uv run sgm metrics tests/fixtures/sas --check excede únicamente tiempo_compilacion_s: 22,8 s frente al límite 19,08 s. El control Hito 30 registró 24,1 s; no se modificó la línea base.
- Decisión: usar E.literal como fuente y mantener calculados o controles pendientes en vez de inferir escapes de LIKE que el patrón no demuestra. Sin dependencias nuevas.
- Bloqueos: el tiempo del corpus sigue sobre el umbral, aunque queda por debajo del control Hito 30; las expresiones candidatas requieren validación en Talend Studio.

## Hito 32n. Evitar el doble escape de ampersand en COMPRESS

- Fecha: 2026-11-03
- Qué se hizo: se eliminó el escape manual adicional de ampersand después de re.escape. La regex queda escapada una vez como patrón y luego _jstr la serializa para Java, evitando añadir la barra invertida a la lista de caracteres eliminados.
- Hallazgo: re.escape ya escapa ampersand en la versión de Python del proyecto. El reemplazo posterior lo escapaba otra vez y producía cuatro barras en el fuente Java en lugar de dos.
- Evidencia: la regresión sintética compress(value,'a&b') mostró la diferencia exacta. No se encontró una lista literal con ampersand en los programas SAS del corpus revisado.
- Pruebas: RED observado para la salida Java con ampersand; 15 pruebas focales de COMPRESS pasan tras el arreglo.
- Verificación: uv run pytest -q: 454 pasan y 1 se salta (103,39 s); uv run ruff check .: limpio; uv run sgm rules validate: válido; git diff --check: limpio.
- Métricas: uv run sgm metrics tests/fixtures/sas --check excede únicamente tiempo_compilacion_s: 27,8 s frente al límite 19,08 s. El control Hito 31, medido por separado, registró 43,7 s; la corrida previa de Hito 31 registró 22,8 s. La variación impide atribuir el tiempo a este cambio. No se modificó la línea base.
- Decisión: conservar re.escape como única codificación regex y mantener _jstr para el nivel Java. Sin dependencias nuevas.
- Bloqueos: el tiempo del corpus continúa variable y sobre el umbral; las expresiones candidatas requieren validación en Talend Studio.

## Hito 33n. Alinear el COMPRESS predeterminado del flujo integrado

- Fecha: 2026-11-03
- Qué se hizo: el traductor inline de un argumento ahora elimina el espacio literal, igual que la rutina Talend ya existente, en vez de eliminar cualquier whitespace con la regex \\s.
- Hallazgo: el flujo público translate() toma primero la ruta inline y evitaba el mapeo nuevo. Así COMPRESS(value) borraba tabulaciones y otros blancos que no estaban en su lista predeterminada.
- Evidencia: _f_compress documenta que sin lista se quitan blancos; el constructor Talend usa StringHandling.CHANGE con un espacio literal. La regresión llama al flujo integrado translate("compress(value)").
- Pruebas: RED observado en el flujo integrado; las 16 pruebas focales de COMPRESS pasan tras el cambio.
- Verificación: uv run pytest -q: 455 pasan y 1 se salta (117,90 s); uv run ruff check .: limpio; uv run sgm rules validate: válido; git diff --check: limpio.
- Métricas: uv run sgm metrics tests/fixtures/sas --check excede únicamente tiempo_compilacion_s: 25,8 s frente al límite 19,08 s. La corrida previa Hito 32 dio 27,8 s y un control Hito 31 dio 43,7 s. No se cambió la línea base.
- Decisión: alinear el atajo inline con el constructor Talend vigente, sin ampliar la lista de caracteres que se eliminan. Sin dependencias nuevas.
- Bloqueos: el trinquete de tiempo sigue variable y sobre el umbral; las expresiones candidatas requieren validación en Talend Studio.

## Hito 109m. Integración de la rama de Byron (origin/main, hitos 20n a 33n) en main

- Fecha: 2026-11-06.
- Qué se hizo: `merge` de `origin/main` (14 commits de Byron) en el `main` local. Sus entradas de
  `PROGRESS.md` se conservan como `20n` a `33n`. En los archivos con conflicto (`expressions/expressions.py`,
  `talend_parser.py`, `talend_translator.py`, `passes/p10_components.py` y los tres golden de plan) **se
  conservó la versión local**; el resto de sus cambios (`frontend/`, `ir/models.py`, `lower_data.py`,
  `p06_flow_fusion.py`, pruebas nuevas, `talend_functions*.py` y `talend_lexer.py`) entró tal cual.
- **Pendiente, no resuelto:** las pruebas de Byron `tests/unit/test_input_informat.py`,
  `test_talend_compress.py`, `test_talend_like.py` y `test_talend_scan.py` **fallan** contra la
  estructura local de expresiones (esperan `Unsupported` para informats dinámicos, el escape de
  delimitadores de `SCAN`, los patrones `LIKE` y los casos no demostrados de `COMPRESS`). No se
  relajaron ni se borraron. Los archivos `talend_functions*.py` y `talend_lexer.py` de Byron quedan sin
  uso hasta decidir qué estructura sobrevive. Esta es la tarea 0 de `reparto-andres-byron.md`: portar su
  comportamiento a la estructura local (o al revés) hasta que sus pruebas pasen.
- Pruebas: la suite completa **no está en verde** por lo anterior. No se miró el resto de la lista de
  fallos más allá de esos cuatro archivos; se subió por decisión del usuario sin más corridas.

## Hito 110m. Comparaciones del DATA step como 1/0 y ajustes de funciones (cambios pendientes, sin cerrar)

- Fecha: 2026-11-06.
- Qué se hizo: `expression_type` reconoce predicados como `Boolean`; el emisor del `tMap` los convierte a
  `Long` 1/0 (en SAS una comparación vale 1 o 0, no un booleano de Java). Ajustes en
  `expressions_funciones.py` y `talend_funciones.py`, y pruebas en `test_tipos_codigo.py`,
  `test_talend_translator.py`, `test_migrar_corpus_l4_a.py` y `tests/studio/test_migrar_lote.py`.
- Estado: subido por petición del usuario sin correr la suite completa; estos cambios venían sin commitear
  de antes de la sesión y no se verificaron aquí. Se subió tras `git pull --rebase` sobre la integración de
  Byron (hito 109m); las pruebas de expresiones de Byron siguen siendo la tarea 0.

## Hito 111n. MG-03: validar Java de INPUT, ROUND y predicados

- Fecha: 2026-11-06.
- Qué se hizo:
  - `INPUT w.d` emite `BigDecimal`, aplica la escala implícita solo cuando el texto no contiene punto
    decimal y devuelve missing ante texto no numérico. La referencia `INPUT Function`
    (`lefunctionsref.pdf`, p. 1080) define la conversión por informat; el tipo sigue el catálogo local.
  - `ROUND` conserva `Double` y redondea los empates alejándose de cero (`lefunctionsref.pdf`, p. 1486).
  - Los predicados demostrables se tipan como booleanos internamente y se serializan como `Long` 1/0
    en columnas DATA step. Se añadieron regresiones de comparación y `MISSING`.
  - El lote C incorpora casos L4 `traducible`/`revisado` y deja fuera `l4_20_put_fechas_pendiente`, sin
    vector independiente ni equivalencia sustentada. `OUTPUT` mantiene pendiente explícito porque el
    emisor aún no modela todas las ramas y destinos.
- Pruebas: suite completa **2361 passed, 27 skipped, 149 xfailed**; `uv run ruff check .` limpio.
  A/B focalizado: **161 passed, 1 skipped, 20 xfailed**.
- Anillo C: bloqueado, no fallido. El bridge de Studio no respondió (`ECONNREFUSED` en
  `127.0.0.1:3930`); no comenzó la compilación. Reintentar el lote conjunto y ejecutar/comparar
  `l4_02`, `l4_03`, `l4_18` y `l4_19` cuando Studio y el bridge estén disponibles.
- Decisiones: no se declara C pasado ni se marca MG-03 global completo. `OUTPUT` parcial no se emite;
  MG-04 no se inicia.

## Hitos 111m a 114m. Cuatro tareas H del carril de Andres, hechas por agentes haiku y revisadas

- Fecha: 2026-11-06. Cada tarea la hizo un subagente `haiku` en su propio worktree; yo revisé el
  diff y la integré. No se corrió la suite completa en cada una; sí al final (ver abajo).
- **111m, MG-P9-06 (disposición en el lienzo).** `talend_item/disposicion.py`: `disponer(job)` pone
  `x = 200 * profundidad` (camino más largo, Kahn con corte de ciclos) e `y = 96 * fila`. El validador
  gana la regla 7: dos nodos en la misma (x, y) es error. **Falta** llamar a `disponer` desde el
  emisor (`desde_plan*.py`); mientras no se llame, el control Q11 está probado pero no activo.
- **112m, MG-P9-07 y MG-P8-07 (parcial).** Solo el modelo: `Job.proposito`, `descripcion`, `autor` y
  `Nodo.comentario`. **No se escribe nada en el `.item` ni en el `.properties`**: ningún fixture ni
  guía trae una nota, `COMMENT`, `purpose`, `description` o `author` de Studio, y no se inventa el
  formato. Bloqueo: hace falta un Job y un `.properties` guardados por Studio con esos campos. Ojo con
  el nombre: `render_properties(autor=...)` es un id de usuario; `Job.autor` es un nombre.
- **113m, MG-P9-05 (parcial).** `tests/unit/test_conexiones_tipos.py`: `Main` pasa contra el Job real
  de `tests/fixtures`; los otros 9 tipos (OnSubjobOk, OnComponentOk, Run if, OnSubjobError, Iterate,
  Lookup, Reject, Filter, ORDER) son `xfail` estricto porque no hay Job de Studio en el repo con qué
  compararlos. Hay Jobs reales en el proyecto de talend-mcp (`workspace/.../PRJ_BANCOLOMBIA/process/`)
  con SUBJOB_OK, COMPONENT_OK, RUN_IF, ITERATE y FILTER; **copiar uno saneado a
  `tests/fixtures/talend/` necesita la aprobación del usuario** (es de un cliente). ORDER no es un tipo
  de conexión en Talend; falta aclarar qué quería probar la tarea. Aviso: el `lineStyle 4` de
  SUBJOB_ERROR que dice la documentación de talend-mcp no está en ningún `.item`; no se tomó.
- **114m, MG-P14-01.** Versión única (`importlib.metadata`), `sgm --version`, `CHANGELOG.md` y
  `uv build --wheel` correcto (`sgm-0.2.0`). Se corrigió una frase obsoleta del changelog.
- Decisión: las pruebas en `xfail` estricto cuentan 0 para el crédito del avance (sección 11b).

## Hito 115m. `ORDER BY` y `DISTINCT` se emiten (tSortRow, tUniqRow) y el `SELECT` por fin proyecta

- Fecha: 2026-11-06. MG-P5-01 y MG-P5-02 (parte), MG-P1-02 (parte) y MG-P10-01 (parte).
- Qué se hizo:
  - `talend_item/desde_plan_orden.py`: `sort` a `tSortRow` y `dedup` a `tUniqRow`. El criterio lleva
    `COLNAME`/`SORT`/`ORDER` con la forma de un Job real guardado por Studio (num para numéricos,
    date para fechas, alpha para el resto). `ORDER BY 2` se resuelve por posición. La llave del
    DISTINCT es el `SELECT` entero y distingue mayúsculas. Si una columna no existe, todo el nodo
    queda pendiente (`P-ORDEN-COLUMNA-DESCONOCIDA`): un orden a medias da otro resultado sin avisar.
    Las conexiones de estos nodos llevan nombre propio (`<nodo>_in`, `<nodo>_out`) porque `row1` ya es
    la fila principal del `tMap` de detrás; la salida del `tUniqRow` usa el conector `UNIQUE`.
  - `migrar/interprete.py` (zona de Byron, excepción anotada: verifica mi emisor): ejecuta `sort`
    (faltante primero en ascendente, estable, `ORDER BY 2`) y `dedup`.
  - **Defecto encontrado y corregido:** `select a, b from t where ...` no generaba proyección en el
    plan ("la lectura ya trae `a`"), así que con la CSV completa saldrían las 5 columnas de entrada y
    no las 3 pedidas. El anillo B lo dejaba pasar porque solo compara las columnas del esperado.
    `lower_sql_flow._necesita_proyeccion` ahora proyecta siempre que hay lista de columnas, salvo con
    agregados (que ya entregan solo las suyas). Efecto: el filtro viaja como paso de un `map` y el
    golden de `client_poc` se regeneró (los `external_load` absorben más pasos).
  - `migrar/esquemas.py` cuenta las llaves de `ORDER BY`/`DISTINCT` como columnas usadas.
  - Pruebas ajustadas por la nueva forma (sin quitar aserciones): `test_sql_flujo`, `test_sql_with`
    miran el filtro como paso de un `map`; `test_migrar_interprete` usa `aggregate` como ejemplo de paso
    no soportado, porque `sort` ya se ejecuta. Se quitaron del `CONOCIDOS` del anillo B los 14 casos
    de `sort`/`dedup` (eran `xfail` estricto). La lista viva `migrar_pendientes.yaml` baja de 27 a 17.
- Pruebas: suite completa **2420 pasan, 55 fallan** (los 55 de Byron, sin cambios), `ruff` limpio.
  Anillo B: 56 pasan y 6 `xfail` (antes 42 y 20). Anillo A: 28 de 45 casos de L0 a L2 migran sin
  pendientes de traducción (antes 18).
- **No verificado en Studio:** ni `tSortRow` ni `tUniqRow` emitidos por `sgm migrar` se compilaron ni
  se ejecutaron. Queda por ver cómo ordena `tSortRow` los nulos frente al faltante de SAS (primero en
  ascendente); el intérprete lo asume por la documentación (`sqlproc`), no por Studio.
- Hallazgo para Byron (P10-01): el comparador del anillo B ignora columnas de más en la salida. Hay
  que hacerlo estricto, o esta clase de defecto pasa sin que nadie lo vea.
- Pendiente sin tocar en este hito: `P-FILTRO-SIN-TRADUCIR` (8 casos), `P-ESQUEMA-VACIO` (6),
  `P-ASIGNACION-SIN-TRADUCIR` (3) y `P-OPERADOR-SIN-SOPORTE` (1).

## Hito 116m. El `tMap` lee los nombres como SAS y admite el orden que el traductor ya guarda

- Fecha: 2026-11-06. MG-P5 (parte, filtros y uniones) y MG-P1-02 (parte, tipos).
- Qué se hizo:
  - **Defecto real (excepción):** con `--muestra`, `ON t.tipo_doc = h.CNAME` rompía con
    `KeyError: El lookup 'row2' no tiene las columnas ['cname']` (`P-FALLO-INTERNO`). El traductor baja
    los nombres a minúsculas y la cabecera trae `CNAME`. Ahora llaves, filtros y asignaciones del
    `tMap` resuelven el nombre sin distinguir mayúsculas y escriben el que trae la fuente.
  - `cubrir_faltante` reconocía solo las comparaciones de orden que él mismo envolvía, y rechazaba
    las que el traductor ya escribe con su guarda (`x != null && ...` para `>`/`>=`, `x == null || ...`
    para `<`/`<=`). Ahora las admite sin envolverlas, con una condición de tipo: la forma `Number` pide
    columna numérica y la forma `Comparable` contra un literal de texto pide columna de texto. Si el
    tipo no lo demuestra, queda pendiente con ese motivo.
  - `migrar/esquemas.py`: comparar por orden con un número literal (`x >= 5`, `5 < x`,
    `x BETWEEN 2 AND 5`) demuestra que la columna es numérica; y los textos de las ramas de un
    `CASE WHEN` (condición, resultado, `ELSE`) ahora cuentan al deducir tipos.
  - Prueba nueva `test_tmap_nombres_y_ordenes.py` (7 casos).
- Efecto en el corpus: la lista viva `migrar_pendientes.yaml` baja de 17 a 14 casos
  (`l1_09_between_fechas`, `l1_14_expresion_compuesta` y `l2_04_validacion_tipo_doc` salen).
  **Con `--muestra`** (la forma de uso real, la cabecera dice las columnas) son 10 casos con
  pendiente, no 14; la diferencia son los filtros sobre columnas sin calificar tras un `JOIN`
  (`l2_13`, `l2_14`, `l2_04`), que sin cabecera no se pueden atribuir a una tabla.
- Lo que queda con `--muestra` y su causa: `l0_09` (`union` sin emisor), `l0_12` (decisión vieja:
  columna derivada numérica en condición), `l0_13` (`IF/ELSE` con `DO`/`END`), `l2_06`, `l2_07` y
  `l2_15` (subconsulta en `IN`), `l2_08` (`aggregate` sin emisor), `l2_11` (tres tablas: sin llave
  para la tercera), `l2_12` (auto-`JOIN`: el plan pierde los alias `a` y `b` y el filtro queda
  `id_cliente < id_cliente`), `l2_14` (`ORDER BY` tras el `map` sin columnas para la escritura).
- Pruebas: suite completa 2418 pasan más las 7 nuevas, 57 fallan (los 55 de Byron y las 2 de la
  lista viva, que se regeneró en este mismo hito), `ruff` limpio.
- Aviso para quien edite con scripts: `\b` dentro de un texto normal de Python es el carácter de
  retroceso, no el límite de palabra; las expresiones regulares van en cadenas crudas.

## Hito 117m. `GROUP BY` se emite (tAggregateRow) y L3 entra en los anillos A y B

- Fecha: 2026-11-06. MG-P5-03 (parte: agregados simples), MG-P9 (parte) y MG-P10-01 (parte).
- Qué se hizo:
  - `talend_item/desde_plan_agregado.py`: `aggregate` a `tAggregateRow`. Tabla `GROUPBYS` con las
    columnas de grupo y `OPERATIONS` con `FUNCION(columna)` para `COUNT`, `SUM`, `AVG`/`MEAN`, `MIN`,
    `MAX` y `COUNT(DISTINCT col)`. `COUNT(*)` cuenta filas (`IGNORE_NULL=false`); el resto ignora el
    faltante, como SAS. El esquema de salida lleva los tipos (`count` es `Long`; `sum` de entero es
    `Long`, de real `Double`; `avg` es `Double`). Todo o nada: un agregado que no es
    `FUNCION(columna)` (`COUNT(*) - COUNT(x)`, una subconsulta escalar, `SUM` sobre texto) deja el
    nodo pendiente con `P-AGREGADO-SIN-TRADUCIR` o `P-AGREGADO-COLUMNA-DESCONOCIDA`.
  - `migrar/interprete.py` (zona de Byron, excepción anotada: verifica mi emisor): ejecuta `aggregate`
    con la semántica de `sqlproc` (faltante ignorado, sin valores da faltante, faltante en la llave es
    un grupo, grupos en orden de llaves, un agregado total sobre cero filas da una fila).
  - `ir/lower_sql_flow.py`: tras un `JOIN` el agregado lee un `derive` con las columnas que agrupa y
    suma (calificadas por tabla), porque el cruce no las entregaba; y la proyección del `SELECT` ya no
    se aplica detrás de un agregado aunque haya cruce (borraba las columnas agregadas).
  - `talend_item/validador.py`: la regla de columnas por conexión también se salta `tAggregateRow`,
    como ya hacía con `tMap`: su esquema de entrada lo da la conexión, no su bloque de metadatos.
  - `desde_plan.py`: `sort`, `dedup` y `aggregate` figuran como productores de su tabla (la escritura
    de detrás encontraba su columna sin esto solo por casualidad), y si el nodo falla su salida queda
    vacía, para que la escritura sea un pendiente y no un nodo sin entrada (Job inválido).
  - `migrar/esquemas.py`: los agregados cuentan al deducir tipos (`SUM(x)`, `AVG(x)` hacen numérica a
    `x`).
  - **Instrumento de medida:** el anillo A (`test_migrar_corpus_aceptacion.py`) ahora migra cada caso
    con su `entradas/` como muestra, que es como se usa `sgm migrar --muestra`, y cubre L0 a L3
    (57 casos). Sin muestra, un filtro sobre columna sin calificar tras un `JOIN` no se puede atribuir
    a una tabla. El anillo B también corre L3.
- Resultado: **47 de 57 casos migran sin pendientes de traducción** (82 %). El anillo B: 66 pasan y 8
  `xfail` conocidos. Lista viva: 10 casos (`l0_09` union, `l0_12`, `l0_13` DO/END, `l2_06`, `l2_07`,
  `l2_15` IN con subconsulta, `l2_11` tres tablas, `l2_12` auto-JOIN, `l3_01` agregado compuesto,
  `l3_09` subconsulta escalar).
- Pruebas: suite completa 2455 pasan, 55 fallan (los de Byron, sin cambios), `ruff` limpio. Pruebas
  nuevas: `test_emisor_orden_y_agregado.py` (6; cubre también `tSortRow` y `tUniqRow`, que hasta hoy
  no tenían prueba propia).
- **No verificado en Studio** (ni `tSortRow`, ni `tUniqRow`, ni `tAggregateRow`):
  * el valor `distinct` del `FUNCTION` para `COUNT(DISTINCT)` sale de la memoria del componente, no
    de un Job guardado;
  * qué devuelve `sum` de un grupo cuyos valores son todos nulos (SAS da faltante; Talend podría dar
    cero o nulo): `l3_02` lo prueba y solo el anillo C lo dirá;
  * el orden de los grupos que entrega `tAggregateRow` no es el de SAS (que sale por llave); los
    casos de L3 piden `ORDER BY`, y el intérprete sí ordena por llave.
- **Decisión que queda para el usuario:** una columna sin tipo demostrado se escribe `String`, y un
  `ORDER BY saldo` sobre ella ordena como texto (`"100" < "50"`). La muestra podría demostrar el tipo
  por su contenido, como hace `PROC IMPORT`; cambiaría los tipos de lectura de todos los Jobs y hay
  que verificarlo en Studio antes. No se tocó.

## Hito 118m. `UNION`/`SET` a `tUnite` y `IN`/`NOT IN` con subconsulta como cruce de existencia

- Fecha: 2026-11-06. MG-P5-04 (parte, subconsultas), MG-P4 (parte, `SET` de varias tablas).
- Qué se hizo:
  - `talend_item/desde_plan_union.py`: `union` a `tUnite`, con una conexión de entrada por tabla
    (`<nodo>_in1`, `_in2`...). Queda pendiente si las entradas no traen las mismas columnas en el
    mismo orden (`P-UNION-ESQUEMAS-DISTINTOS`: SAS junta por nombre, `tUnite` no) o si es `UNION` sin
    `ALL` (`P-UNION-SIN-ALL`: pide un `tUniqRow` detrás). El intérprete apila por nombre y rellena
    con faltante.
  - `ir/sql_tree.py`: `col [NOT] IN (SELECT k FROM t [WHERE ...])` con subconsulta simple (una tabla,
    sin cruces ni agrupación, una columna) sale del `WHERE` como `SemiSpec`. Otras formas se quedan
    como estaban y siguen pendientes.
  - `ir/lower_sql_flow.py`: cada `SemiSpec` baja a una cadena aparte (lectura, filtro, llave,
    `dedup`) que termina en una tabla temporal `WORK.__in_l<línea>_<n>`, y a un cruce con ella:
    interno para `IN`, izquierdo más `missing(llave)` para `NOT IN`. La subconsulta se reduce a
    llaves únicas para no repetir filas. En SAS el faltante es un valor más.
  - `t.*` del `SELECT` se califica con la tabla y el emisor lo expande con las columnas de esa
    entrada (antes: `la tabla 't' no es una entrada del mapa`, que arrastraba `l2_15` y `l3_09`).
- Lista viva: de 10 a 6 casos (`l0_12`, `l0_13`, `l2_11`, `l2_12`, `l3_01`, `l3_09`). **51 de 57
  casos migran sin pendientes de traducción** (89 %). Anillo B: 68 pasan y 6 `xfail`.
- Pruebas: 2461 pasan, 55 fallan (los de Byron), `ruff` limpio. Nuevas: `test_emisor_union.py` (4) y
  `test_in_subconsulta.py` (5).
- No verificado en Studio: el orden de entrada de `tUnite` (hoy el de las conexiones en el `.item`) y
  el resto de nodos del hito 117m.
- Limitación conocida: el intérprete no expande `t.*` tras un `JOIN` (no sabe qué columnas son de
  `t`), y por eso `l2_15` sigue como `xfail` del anillo B aunque el emisor ya lo traduce.

## Hito 119m. Cruces encadenados (`a JOIN b JOIN c`) y `IF ... THEN DO; ... END; ELSE ...`

- Fecha: 2026-11-06. MG-P5-02 (parte, cruces), MG-P4-03 (parte, bloques `DO`).
- Qué se hizo:
  - **Cruce de tres tablas** (`desde_plan.py`, `desde_plan_map.py`): el `tMap` del segundo cruce recibe
    el resultado del primero como entrada principal (`Fuente.compuesta`), y ya no cuenta como lookup
    sin llave la tabla que el primer cruce consumió (la arista directa del plan es redundante). Las
    columnas `tabla.col` de una tabla ya cruzada se resuelven en esa entrada. Un `SELECT *` sobre un
    cruce trae ahora las columnas de todas las tablas (antes solo las de la principal).
  - **`lower_data_bloques.py`**: una cadena `IF / ELSE IF / ELSE` con bloques `DO; ... END;` baja a una
    asignación condicional por columna (el `conditional` que ya existía). Se deja sin traducir, con su
    nota, lo que cambiaría el resultado: una columna asignada dos veces en la misma rama, una expresión
    que lee otra columna de la cadena, dos columnas asignadas que las condiciones también leen, y
    sentencias que no son asignaciones. La columna que las condiciones leen se asigna la última, porque
    SAS evalúa la condición una vez, antes de asignar nada.
- Lista viva: de 6 a 4 casos (`l0_12`, `l2_12`, `l3_01`, `l3_09`). **53 de 57 casos migran sin
  pendientes de traducción** (93 %). Anillo B: 69 pasan y 5 `xfail`.
- Pruebas: 2471 pasan, 55 fallan (los de Byron), `ruff` limpio. Nueva: `test_data_bloques_do.py` (4).
- Lo que queda de L0 a L3: `l0_12` (decisión vieja sobre columna derivada numérica en una condición),
  `l2_12` (auto-`JOIN`: el plan pierde los alias y la misma tabla tendría que entrar dos veces al
  `tMap`), `l3_01` y `l3_09` (expresión sobre agregados y subconsulta escalar: piden un `tMap` detrás
  del `tAggregateRow`).

## Hito 120m. L4 a L6 entran en el anillo A; `MERGE`, `BY _ALL_` y `%LET` resuelto

- Fecha: 2026-11-06. MG-P4-01 (parte, `MERGE`), MG-P6-01 (parte, `PROC SORT NODUP`).
- Alcance del anillo A: ahora L0 a L6 (101 casos). **L4: 20 de 20 sin pendientes.** L5 y L6 traen la
  lista de lo que falta; el total pasa a 78 de 101 sin pendientes de traducción (77 %).
- Qué se hizo:
  - `MERGE ... BY k` (emisor): las llaves salen del `BY` cuando el paso no trae pares de columnas;
    la tabla principal es la primera de `sources`; las banderas `IN=` son columnas `Long` (1 en la
    principal; en una consulta, «su llave no es nula tras el cruce izquierdo») y también valen dentro
    de un `IF` posterior como booleano. Un tipo de unión que no sea `inner`/`left` (el `full` de un
    `MERGE` sin `IF`, `right`, o no deducible) **ya no se emite como `left` en silencio**: queda
    `P-UNION-TIPO-SIN-SOPORTE`, porque un `tMap` no hace `full outer`.
  - `MERGE` (intérprete, zona de Byron, excepción anotada): junta por grupo de llave fila con fila,
    sin producto; la tabla que se queda sin filas conserva sus últimos valores y su `IN=` sigue en 1;
    salida por llave. Cubre `l6_01` a `l6_04`.
  - `BY _ALL_` (`PROC SORT ... NODUP`): son todas las columnas de la entrada, en `tSortRow`,
    `tUniqRow` y el intérprete (`l6_09`).
  - `%LET` ya sustituido en el programa deja de ser un pendiente de traducción: es la nota
    `P-CONFIGURACION-RESUELTA` (como `P-TIPO-DESCONOCIDO`, no cuenta como pérdida), que dice que el
    valor está dentro del Job y no hay variable de contexto.
- Lista viva (anillo A): `l0_12`, `l2_12`, `l3_01`, `l3_09` (como antes) y de L5/L6: `l5_03`, `l5_12`
  (`iterate` sin `tRunJob`), `l5_06` (`%sysfunc`, es de macros), `l5_09` (`SELECT INTO` sin
  `tSetGlobalVar`), `l6_01` a `l6_04` y `l6_11` (`MERGE` completo: falta `full outer`),
  `l6_05`, `l6_06`, `l6_07`, `l6_10` (`stateful_row`: `RETAIN` y `FIRST./LAST.` piden `tJavaRow`),
  `l6_12` (`iterate`).
- Pruebas: 2524 pasan, 55 fallan (los de Byron), `ruff` limpio. Nueva: `test_merge_y_all.py` (5).
- Lo que sigue y por qué es lo mayor: (a) `full outer` de `MERGE` = dos `tMap` (uno por lado, el
  segundo con rechazo de unión), `tUnite` y `tSortRow`, y la tabla que se usa dos veces pide
  `tReplicate`; (b) `RETAIN`/`FIRST.`/`LAST.` a `tJavaRow` con estado y entrada ordenada; (c)
  `iterate`/`tRunJob` (padre e hijos, fase 8). Ninguno se puede verificar sin Studio.

## Hito 121m. Las plantillas (`iterate`) se despliegan en línea: una macro llamada N veces se migra

- Fecha: 2026-11-06. MG-P8 (parte): decisión de arquitectura provisional; MG-P9-03 sigue abierto.
- Problema: la pasada 7 sustituía los bloques repetidos (una macro llamada con otros argumentos) por un
  `iterate` y dejaba del Job hijo solo las firmas del cuerpo. El emisor no tenía qué escribir:
  `P-OPERADOR-SIN-SOPORTE ... tRunJob` y el trabajo de esas llamadas **se perdía** (`l5_03`, `l5_12`).
- Decisión (provisional, hasta que haya Jobs hijos con datos entre Jobs verificados en Studio): **cada
  instancia se escribe en línea**, que es lo que el SAS hacía. La pasada 7 guarda en
  `Plan.iteraciones` los operadores y aristas que sustituyó (campo que no se serializa: los golden no
  cambian) y `ir/desplegar.plan_desplegado` los devuelve a un plan nuevo. `migrar`, `plan_a_jobs` y el
  intérprete lo usan; el `iterate` cuenta como visitado. El `tRunJob` real queda para MG-P9-03.
- Otros arreglos del hito:
  - Una cuenta de literales (`ID <= 1 * 3`, lo que deja `%eval` al expandir) cuenta como literal numérico
    para deducir el tipo y para el faltante.
  - El intérprete ignora `%LET`/`OPTIONS` ya sustituidos (`unsupported` con razón `CONFIGURACION`).
- Resultado: anillo A 80 de 101 sin pendientes de traducción (79 %); el anillo B ahora cubre L0 a L6
  (82 pasan, 10 `xfail` con su motivo; `l5_03`, `l5_12` y `l6_12` pasan).
- Pruebas: 2538 pasan, 55 fallan (los de Byron), `ruff` limpio. Nueva: `test_desplegar_plantillas.py` (4).
- Lo que falta de L5: `l5_06` (`%sysfunc` dentro de `%let`: macros), `l5_09` (`SELECT INTO`: pide
  `tSetGlobalVar` y un disparador `OnSubjobOk` entre dos subjobs, más que `&ANIO` llegue a la expresión).

## Hito 122m. `BY` con `FIRST.`, `LAST.`, `RETAIN` y suma: modelo en el plan e intérprete

- Fecha: 2026-11-06. MG-P4 (parte: estado entre filas). **El emisor a Talend no está hecho.**
- Qué se hizo:
  - `ir/lower_data_grupos.py`: un DATA step con `BY` y `RETAIN`, `FIRST.`/`LAST.` o la sentencia de suma
    (`acum + x`) se baja a **un** `stateful_row` con `reason: by_group` y un programa por fila
    (`retain`, `asigna`, `si`, `suma`, `filtra`). Antes eran sentencias sueltas que el plan dejaba como
    texto sin traducir. Un paso con otra cosa (`ELSE`, `DO`, `OUTPUT`, `KEEP`...) sigue el camino de
    siempre.
  - Intérprete (zona de Byron, excepción anotada): ejecuta ese programa con la semántica del SAS:
    `FIRST.v`/`LAST.v` por grupo (con varias llaves, `first` de la segunda vale 1 si cambió la
    primera), variables retenidas que pasan de una fila a la siguiente, suma que empieza en 0 e
    ignora el faltante, y `IF cond;` que descarta la fila pero deja su efecto en lo retenido.
  - Resultado en el anillo B: `l6_05` y `l6_10` pasan; `l6_06`, `l6_07` y `l6_11` (estado
    `pendiente_revision`, fuera del anillo) coinciden con su esperado cuando se comparan a mano.
- Lo que falta, y por qué no se hizo: **escribirlo en Talend**. `LAST.` pide mirar la fila siguiente,
  que `tJavaRow` no tiene; las salidas posibles (conteo por grupo unido de vuelta con `tMap`, o
  `tJavaFlex` con una fila de retraso y una fila centinela) tienen detalles de Studio que no se deben
  escribir a ciegas. Sigue como `P-OPERADOR-SIN-SOPORTE` (`stateful_row`).
- Pruebas: 2543 pasan más las nuevas, 55 fallan (los de Byron), `ruff` limpio. Nueva:
  `test_data_por_grupo.py` (4).
- **Studio:** disponible (talend-mcp responde, proyecto `PRJ_BANCOLOMBIA`), pero el lote C escribe
  Jobs en ese proyecto y la acción fue bloqueada por permisos: nadie ha autorizado todavía usarlo. Los
  nodos de los hitos 115m a 121m siguen sin compilar. Se extendió `tests/studio/test_migrar_lote.py`
  a L0–L6 para correrlo en cuanto se autorice.

## Hito 123m. Expresión sobre agregados (`COUNT(*) - COUNT(x)`): agregar cada llamada y calcular detrás

- Fecha: 2026-11-06. MG-P5-03 (parte).
- Qué se hizo (`ir/lower_sql_flow.py`): una expresión del `SELECT` que combina agregados (`COUNT(*) -
  COUNT(saldo)`, `SUM(a) / COUNT(*)`, `ROUND(AVG(x), 2)`) ya no es un agregado imposible. Cada
  llamada se agrega por su cuenta con un nombre oculto (`agg_1`, `agg_2`) y un `derive` detrás arma las
  columnas del `SELECT` en su orden, con la expresión sobre esos nombres (un `tMap` en el Job). Una
  subconsulta escalar, o un agregado sin alias, sigue pendiente. Con un `JOIN` delante, el cruce
  entrega también las columnas que leen las llamadas ocultas.
- Anillo B: `l3_01` pasa (era `xfail`). Anillo A: **84 de 101** sin pendientes de traducción (83 %).
  Lista viva: 17 casos (`l0_12`, `l2_12`, `l3_09`, `l5_06`, `l5_09`, `l6_01` a `l6_07`, `l6_10`,
  `l6_11`, `l6_12`).
- Pruebas: suite 2544 pasan, 55 fallan (los de Byron), `ruff` limpio. El test del emisor que daba
  `l3_01` por pendiente ahora comprueba el `tAggregateRow` con `agg_1`/`agg_2` y el `tMap`; la
  subconsulta escalar tiene el suyo.

## Hito 124m. Avance recalculado: 27,1 %

- Fecha: 2026-11-06. Sin cambios de código.
- Se recalculó la sección 11b de `plan-migrador-general.md` con los hitos 108m a 123m: **de 19,6 % a
  27,1 %** (242,75 h de 895). Suben P1 (+2,5), P4 (+14), P5 (+25), P6 (+1,5), P7 (+8), P8 (+2),
  P9 (+8) y P10 (+6). Los créditos son un juicio; lo que está escrito pero sin Studio cuenta 0,25.
- Termómetros: anillo A 84 de 101 casos de L0 a L6 sin pendientes de traducción (83 %); anillo B 86
  de 93 elegibles pasan (92 %).

## Hito 125m. Primera compilación en Studio de los nodos nuevos: 85 de 85 compilan tras tres arreglos

- Fecha: 2026-11-07. Studio 8.0.1, proyecto `PRJ_BANCOLOMBIA` (de pruebas, autorizado por el usuario).
- Hallazgo de entorno: el Studio abierto trabaja en `C:/Talend/8.0.1/studio/workspace3/...`, no en
  `workspace/`. En la ruta equivocada todo da «El job no existe en el repositorio». Se pregunta con
  `talend_bridge_workspace_state`. Además el puente corta cada llamada a los 25 s: un lote de 85 Jobs
  lo deja compilando minutos sin contestar. Lotes de 3 a 4, y esperar `comprobar_salud` entre uno y
  otro. `docs/guia-validacion-studio.md` corregida.
- Primera pasada (85 Jobs, los casos de L0 a L6 sin pendientes de traducción): **67 compilan, 13
  fallan, 5 sin respuesta del puente**. Los errores, literales de `javac` y del generador:
  * `tSortRow` terminal (9 casos): `error: cannot find symbol  defaultRow` — sin conexión de salida
    el generador no declara la fila. Una tabla final de `PROC SQL` que no se exporta no tiene
    consumidor.
  * `tUnite` (`l0_09`): `Cannot invoke IMetadataTable.getListColumns() because "preMetadata" is
    null`. La plantilla JET de `tUnite` solo mira conexiones `FLOW_MERGE` (`EConnectionType`, id 10);
    se habían escrito como FLOW.
  * `l0_13`: `incompatible types: double cannot be converted to Long` en
    `(row1.saldo == null || row1.saldo < 0) ? 0 : row1.saldo`: la columna de salida salía `Long` por
    el literal `0` y la rama `ELSE` es `Double`.
  * `l3_01`: `long cannot be converted to Double` en `(row1.agg_1 - row1.agg_2)`: dos `Long` restados
    dan `long`, y la columna se había declarado `Double`.
- Arreglos (`desde_plan.py`, `desde_plan_map.py`): las entradas de un `tUnite` salen como conexión
  `MERGE` con `lineStyle` 10; un `tSortRow`/`tUniqRow`/`tAggregateRow`/`tUnite` sin consumidor recibe
  un `tLogRow` (debajo de la fila de nodos, para no pisar a otro); el tipo de una columna condicional
  es el más ancho de sus ramas, y el de una expresión entre columnas enteras sin división es `Long`.
- Segunda pasada completa con los arreglos: **64 compilan, 0 fallan, 21 sin respuesta del puente**; los
  21 reintentados de uno en uno: 20 compilan y el último (`l2_13`) compila solo. **Total: 85 de 85.**
  Ningún Job de prueba quedó en `process/` (0 archivos con el sufijo de la corrida).
- **Lo que esto prueba y lo que no.** Compilar solo dice que el `.item` abre y que el Java generado
  compila. **No se ejecutó ningún Job ni se comparó ninguna salida con el esperado.** Siguen sin
  verificar: el valor `distinct` del `FUNCTION` de `COUNT(DISTINCT)`, el resultado de `sum` con un
  grupo de nulos, el orden de entrada de `tUnite`, y que `tSortRow` ordene los nulos como SAS.
- Pruebas: suite 2546 pasan, 55 fallan (los de Byron), `ruff` limpio. El anillo A sigue en 84 de 101.

## Hito 126m. Suite en verde: expresiones de Byron portadas y compuerta de liberación

- Fecha: 2026-11-07. Tarea 0 de `reparto-andres-byron.md` (parte) y MG-P14-02.
- Qué se hizo (`expressions/`):
  * `talend_base.E` guarda el literal SAS (`literal`) y el tokenizador acepta informats con letras y
    dígitos (`e8601da.`); el mensaje de un token no soportado ya no repite el texto del programa.
  * `INPUT`/`INPUTN`: un informat dinámico (macrovariable, columna, concatenación o función) queda
    `Unsupported`; un entero sin punto decimal también; `10.` conserva la advertencia y `8.2` sigue
    emitiendo `BigDecimal`. El argumento omitido de COMPRESS (`compress(x,,'kd')`) se lee como lista
    vacía.
  * `COMPRESS`: `kd` emite `StringHandling.EREPLACE` con `[^0-9]` o `[^0-9.]`; una lista literal usa
    `EREPLACE` con los caracteres escapados; un solo carácter usa `CHANGE`; lo no demostrado queda
    pendiente.
  * `SCAN`: delimitador literal escapado para Java y regex, cuenta negativa desde el final y rechazo
    de posición cero, fraccionaria o fuera de rango; sin delimitador se conserva la forma anterior.
  * `LIKE`: el patrón se escapa (los metacaracteres son texto) y los caracteres de control quedan
    pendientes.
  * `_clean` ya no colapsa los espacios ni los saltos de línea dentro de un literal.
  * `p10_components`: el hueco de una expresión cita `expression_evidence` de esa ocurrencia (archivo
    y líneas exactos), no la evidencia del paso entero.
- Ajuste de emisión (`talend_item/desde_plan_expresiones.py`): comparar la longitud de un arreglo con
  un literal (`.length >= 2`) no es una comparación de orden de SAS y no bloquea la asignación. Lo
  destapó `l4_15` al cambiar SCAN.
- Golden: se regeneraron `p1_merge_first_last.plan.json` (el hueco pasa de dos evidencias de la
  sentencia a la línea 20 de la expresión) y `client__client_poc.plan.json` (`compress(v,' ')` emite
  `CHANGE` de un carácter en vez de `replaceAll`). Son los dos cambios buscados; no se relajó ninguna
  prueba.
- Compuerta de liberación (MG-P14-02): `tools/liberacion.py` corre `ruff`, la suite con cuatro
  workers, el oráculo, dos migraciones byte a byte, `sgm secretos` sobre esa salida y la coherencia de
  versión. `docs/produccion.md` deja el estado, la lista de verificación y los bloqueos; `README.md`
  documenta el comando.
- Pruebas: `tools/liberacion.py` en verde: **2 601 pasan, 27 se saltan, 145 xfail**; oráculo 117
  casos con 0 fallas; determinismo, 11 archivos idénticos; 0 hallazgos de secretos; versión 0.2.0
  coherente entre `pyproject.toml`, el paquete y el changelog. `ruff` limpio.
- Lo que no prueba: ningún Job se ejecutó ni se comparó con su esperado. La compuerta no lanza el
  lote de Studio (`talend_job_build_batch`), así que MG-P14-02 sigue parcial y no se reclama crédito
  de la fase: el avance global sigue en 27,1 % (242,75 h). El resto de P14 y las tareas de personas
  siguen en 0.

## Hito 127m. Backend MCP del producto y un solo cliente para las herramientas

- Fecha: 2026-11-08.
- Qué se hizo:
  - `src/sgm/backend_talend/mcp.py`: `McpBackend` habla con `talend-mcp` por HTTP JSON-RPC, con
    transporte inyectable, `initialize` solo cuando el servidor lo pide, lectura de JSON o SSE, tope
    de tiempo y errores como `BackendNoDisponible`.
  - `src/sgm/backend_talend/comun.py`: un solo mapeo de respuestas para CLI y MCP. Reconoce
    `data.result.jobs` (la forma real del puente), la lista de estados y la forma resumida; el
    veredicto se busca también en `data`.
  - El backend MCP se usa desde la librería y las herramientas (`studio_salud.py --mcp`,
    `corpus_studio.py lote --backend mcp`); `sgm migrar` sigue escribiendo archivos, porque compilar
    exige copiar los Jobs al proyecto y no se hace por sorpresa.
  - `tools/mcp_cliente.py` deja de duplicar el protocolo: `MCP` es el backend del producto con
    `ErrorValidacion`; `tools/studio_salud.py` y `corpus_studio.py lote` aceptan MCP.
  - Pruebas: `tests/unit/test_backend_mcp.py` (11 casos). `test_backend_aislado.py` vigila que
    `TALEND_MCP_URL` no salga de `backend_talend/`.
  - Documentación corregida donde todavía decía que el MCP estaba prohibido: guía de Studio, fase 5,
    plan maestro (sección 4.1 y MG-P0-08), `02-fases.md` y el plan de producción.
- Pruebas: suite completa **2611 pasan, 27 se saltan, 145 xfail**; `ruff` limpio. Focalizado de
  backends, salud, CLI y validador: 67 pasan.
- Decisiones: el handshake es opcional porque el servidor actual es stateless; se intenta
  `tools/call` directo y, si el servidor pide sesión, se negocia y se reintenta una vez. Un `isError`
  con `data` es un veredicto negativo, no un fallo de transporte. El cliente MCP de `tools/` ya no
  tiene protocolo propio.
- Límites: no se ejecutó contra Studio real ni contra el servidor MCP en este hito (el puerto 3927
  no estaba escuchando); las pruebas usan un transporte falso con las formas de respuesta medidas
  antes. La compuerta de liberación sigue sin lanzar el lote de Studio.

## Hito 128m. Backend MCP probado contra el servidor real y tope de respuesta corregido

- Fecha: 2026-11-08.
- Qué se hizo:
  - Se levantó `talend-mcp` (`bun run start:server`, 258 herramientas) y se probó el backend contra
    el servidor real, no con transporte falso.
  - `comun.detalle` desenvuelve el sobre `{ok, data}` del MCP y sigue leyendo la respuesta plana de
    la CLI; `salud.py` lo usa para `mode` y `blocked`. Prueba nueva:
    `test_salud_lee_el_sobre_data_del_mcp`.
  - `TransporteHttp` envuelve `http.client.HTTPException` (`IncompleteRead`) en
    `BackendNoDisponible`; antes una conexión cortada salía como traza. Prueba nueva:
    `test_transporte_http_envuelve_una_respuesta_incompleta`.
  - En `talend-mcp` se corrigió un error de unidades: todas las respuestas `tools/call` se cortaban
    a los 100 ms con `res.destroy()`. Ahora usan `TALEND_MCP_TOOL_TIMEOUT_MS` (600 000 ms por
    omisión). `bun run verify` en ese repositorio: 862 pasan, 182 escenarios válidos.
- Evidencia real:
  - `uv run python tools/studio_salud.py --mcp` imprime «Studio responde y deja escribir» y sale 0.
  - `compilar_lote(["POC_Azure_Job"])` devuelve `no_compilan` con «No se encuentra la carpeta
    generada del job POC_Azure_Job»: es la respuesta negativa del puente, no un fallo de transporte.
  - `verificar("JbCTM", {})` devuelve `ok` con 0 hallazgos en 14,7 s.
- Pruebas: suite completa **2613 pasan, 27 se saltan, 145 xfail**; `ruff` limpio. Focalizado de
  backend MCP y salud: 18 pasan.
- Decisiones: no se cambió el contrato de `llamar` (el MCP entrega el sobre y la CLI entrega `data`)
  porque los validadores leen el sobre para distinguir servidor y puente; la salud usa `detalle`.
  El tope de bytes sigue siendo `maxResponseBytes`/`TALEND_MCP_MAX_RESPONSE_BYTES`; el plazo de la
  tool no es un tope de tamaño.
- Límites: el lote real devuelve «carpeta generada» para los Jobs probados del workspace; el puente
  no las regenera, aunque `verificar` sí compila. No se ejecutó un Job ni se comparó contra SAS, y
  la compuerta de liberación sigue sin lanzar el lote de Studio.

## Hito 129m. `sgm studio`: el backend MCP entra en la CLI del producto

- Fecha: 2026-11-08.
- Qué se hizo:
  - Nuevo grupo `sgm studio` (`src/sgm/cli_studio.py`) con `salud`, `compilar` y `verificar`.
    `--backend mcp` es la opción por omisión y habla con el servidor ya arrancado;
    `--backend talend` usa la CLI y exige `--talend-dir` y `--proyecto`, igual que `sgm migrar` con
    `--backend talend`.
  - `compilar` acepta `--refrescar` y varios Jobs; imprime `OK`/`FALLA` por Job y sale 1 si alguno
    no compila. `verificar` acepta `--contexto CLAVE=VALOR` repetido, imprime el veredicto y sus
    hallazgos, y sale 1 solo con `error`; los avisos no ocultan el resultado.
  - El grupo se registra en `src/sgm/cli.py`; no se añadió ninguna dependencia ni se movió el
    protocolo fuera de `backend_talend/`.
  - `tests/unit/test_cli_studio.py` (12 casos) usa un backend falso: salud, lote mixto, refresco,
    contexto, backend caído y uso incorrecto. `test_backend_aislado.py` obligó a que la ayuda del
    comando no nombre la dependencia ni su variable de entorno.
- Evidencia real:
  - `uv run sgm studio salud` → «Studio responde y deja escribir», salida 0.
  - `uv run sgm studio compilar POC_Azure_Job` → `FALLA POC_Azure_Job: No se encuentra la carpeta
    generada del job POC_Azure_Job`, salida 1 (respuesta del puente, no del transporte).
  - `uv run sgm studio verificar JbCTM` → `Veredicto: ok`, salida 0.
- Pruebas: suite completa **2625 pasan, 27 se saltan, 145 xfail**; `ruff` limpio.
- Decisiones: los nombres `mcp` y `talend` siguen el `--backend talend` que ya existía; el backend talend toma las rutas de las opciones o de
  `SGM_TALEND_DIR` y `SGM_TALEND_PROJECT`; el tiempo
  por omisión es 10 s para salud, 120 s para el lote y 600 s para verificar. `compilar` no copia
  Jobs ni regenera código: solo compila los que ya están en el proyecto.
- Límites: el lote sigue devolviendo «carpeta generada» para los Jobs del workspace que se probaron;
  no se ejecutó ningún Job ni se comparó contra SAS. La compuerta de liberación no lanza el lote de
  Studio.

## Hito 130m. Bloque `esquemas` en `caso.yaml` (MG-P1-02, piloto)

- Fecha: 2026-11-09.
- Qué se hizo:
  - `tools/corpus_lib/esquemas_caso.py`: valida el bloque `esquemas` de `caso.yaml`. Cada columna es
    un tipo demostrado (`tipo`, `linea` del SAS, `longitud` opcional en String) o `pendiente` con
    `motivo`. El tipo debe estar en `TIPOS` (los de `Column.type`).
  - `tools/corpus_lib/caso.py`: acepta el campo `esquemas`, lo valida y lo deja en `Caso.extra`.
  - Piloto con 2 casos: `L0/l0_07_if_then_else` (`nivel` String, longitud 5, línea 12, por `LENGTH`)
    y `L1/l1_01_select_columnas` (columnas de `PROC IMPORT` CSV como `pendiente`).
  - `tests/unit/test_corpus_esquemas.py` (13 casos): forma válida, entradas inválidas, nombres,
    bloque vacío y carga de los dos casos piloto.
- Pruebas: suite completa **2638 pasan, 27 se saltan, 145 xfail**; `ruff check .` limpio.
  La línea base previa era 2625 pasan.
- Decisiones:
  - Columnas de `PROC IMPORT` DBMS=CSV sin `LENGTH` ni `GUESSINGROWS` quedan `pendiente`. El tipo
    lo fija el dato y el SAS no lo demuestra (AGENTS.md, regla 6). Aprobado por el usuario.
  - `uv run pytest` lo bloquea Application Control de Windows (`pytest.exe`). Se usa
    `uv run python -m pytest`.
- Límites:
  - Solo 2 de 117 casos llevan bloque `esquemas`. MG-P1-02 **no está cerrado**.
  - Falta la inferencia que compare el tipo de `sgm migrar` con el declarado: hoy `esquemas.py` solo
    demuestra `Double`, y la pasada 9 propaga `LENGTH` y `FORMAT` sin que `migrar` los lea.

## Hito 131m. Bloque `esquemas` en los 45 casos de L0 a L2 (MG-P1-02)

- Fecha: 2026-11-09.
- Qué se hizo:
  - Se añadió el bloque `esquemas` a 44 de los 45 casos de L0 a L2 (L0, L1 y L2, con el piloto del
    hito 130m). Lo escribieron agentes `haiku` por nivel, y yo revisé la muestra y el cargador.
  - `l0_09_set_dos_tablas` no lleva bloque: sus tablas no nombran columnas (`SET` sin `KEEP`), y el
    cargador rechaza un mapa vacío. El motivo está en un comentario YAML del caso.
  - Se completó el piloto: `l0_07` declara `WORK.clientes` y `l1_01` declara `WORK.basico`.
  - `tests/unit/test_corpus_esquemas.py` recorre el corpus: cada tipo demostrado cita una línea del
    SAS que contiene `LENGTH` o `FORMAT` con el nombre de la columna.
- Resultado:
  - 44 casos con bloque: 3 tipos demostrados (`LENGTH` en `l0_07`, `l0_08` y `l0_13`) y 273 columnas
    pendientes.
  - Ningún programa de L1 ni de L2 declara tipos (sin `LENGTH`, `FORMAT`, `INFORMAT` ni `CAST`).
- Pruebas: suite completa **2640 pasan, 27 se saltan, 145 xfail**; `ruff check .` limpio.
- Límites:
  - MG-P1-02 **sigue abierto**. Falta la comparación con la inferencia de `sgm migrar`.
  - L3 a L8 no tienen bloque. L8 anida sus casos en grupos y tiene su propio formato de tablas.

## Hito 132m. MERGE nunca sale como tMap (MG-P4-04, corrección)

- Fecha: 2026-11-09.
- Qué se hizo:
  - El emisor (`talend_item/desde_plan_map.py`, `_tipo_soportado`) deja como pendiente
    `P-UNION-TIPO-SIN-SOPORTE` cualquier join que venga de un `MERGE`. Se reconoce por la forma de sus
    parámetros: un `MERGE` tiene `by` y no `keys`; un JOIN de SQL tiene `keys`. No se añadió ningún
    parámetro nuevo, así que la firma y los goldens no cambian.
  - Motivo: el `tMap` cruza por llave y no hace el emparejamiento fila con fila de SAS cuando la llave
    se repite. Con `IF` (inner o left) el emisor sí lo emitía como lookup, y eso daba resultados
    distintos sin aviso. El intérprete (`migrar/interprete.py`, `_mezclar`) sí es correcto.
  - Comentario de `lower_data._join_type`: decía «equivale a full outer», que contradice el plan. Ahora
    dice que no es un JOIN de producto y remite al intérprete.
  - `tests/unit/test_merge_y_all.py`: la prueba `test_el_merge_con_if_de_la_primera_sale_como_tmap_con_banderas`
    afirmaba que el MERGE con `IF` sale como tMap. Era el comportamiento incorrecto; se cambió a
    `test_el_merge_con_if_de_la_primera_queda_pendiente_y_no_sale_como_tmap`, que afirma el pendiente
    y que no hay tMap. Se quitó un import sin uso.
- Pruebas: suite completa **2640 pasan, 27 se saltan, 145 xfail**; `ruff check .` limpio.
- Límites:
  - El emisor de MERGE sigue sin existir. Para emitir un MERGE fila con fila hace falta `tJavaRow` o una
    secuencia por grupo (MG-P4-04); eso no está hecho.
  - Ningún caso de Studio usaba MERGE, así que la compilación de 85 Jobs no cambia.

## Hito 133m. El largo de `LENGTH` llega al Job (MG-P1-02, comparación)

- Fecha: 2026-11-09.
- Qué se hizo:
  - `talend_item/desde_plan_map.py`: las columnas de salida de un `tMap` toman el largo que el DATA step
    fija con `LENGTH` (`_longitudes_declaradas`, lee el `declared` de los pasos `derive`). Antes salían
    con `longitud=-1`. Se conserva el largo en el renombrado.
  - `tests/unit/test_corpus_esquemas_migrar.py`: para cada tipo demostrado del bloque `esquemas` con
    largo, `sgm migrar` debe emitir esa columna con ese largo. Cubre `nivel` (`l0_07`), `etiqueta`
    (`l0_08`) y `revision` (`l0_13`).
- Evidencia: en `l0_07`, `nivel` sale como `id_String` con longitud 5 en `tMap` y en la salida.
- Pruebas: suite completa **2643 pasan, 27 se saltan, 145 xfail**; `ruff check .` limpio.
- Límites:
  - MG-P1-02 **sigue abierto**. La comparación cubre solo los tipos que el SAS demuestra; los tipos de
    `PROC IMPORT` siguen siendo `String` por omisión con `P-TIPO-DESCONOCIDO`, como el criterio exige.
  - El cambio altera el `.item` de cualquier Job con `LENGTH`. No se volvió a compilar en Studio: el
    lote de Studio de esta sesión no se ejecutó.

## Hito 134m. Constructores validados de los 14 operadores del plan lógico (MG-P1-03)

- Fecha: 2026-11-09.
- Qué se hizo:
  - `src/sgm/ir/operadores.py`: un constructor por operador de la sección 4 del plan (`leer`,
    `leer_archivo`, `escribir`, `filtrar`, `proyectar`, `renombrar`, `calcular`, `unir`, `combinar`,
    `agregar`, `ordenar`, `deduplicar`, `concatenar`, `pivotar`, `iterar`, `controlar`). Cada uno valida
    sus parámetros, normaliza nombres a minúsculas y devuelve un `Operator` con su firma.
  - `ir/models.py`: nuevo kind `pivot` (PROC TRANSPOSE). Se crea como `hueco`; no tiene lowering.
  - Correspondencia: `combinar` (MERGE) usa el kind `join` con `by`, igual que el lowering de
    `lower_data.py`. `controlar` produce `stateful_row`.
  - `tests/unit/test_ir_operadores.py` (22 pruebas): cada constructor, firma, `Graph` que los acepta,
    `pivotar` como hueco y los parámetros inválidos.
- Pruebas: suite completa **2665 pasan, 27 se saltan, 145 xfail**; `ruff check .` limpio.
- Decisiones:
  - Los constructores son la forma validada de crear operadores nuevos. El lowering existente
    (`Builder.op`) no cambia, para no tocar firmas ni goldens.
  - Identificadores en inglés; mensajes y docstrings en español (AGENTS.md).
- Límites:
  - MG-P1-03 **sigue abierto** en lo que pide el criterio: «L1 a L3 construyen su plan». Los
    constructores no los usa todavía ningún pase.
  - `pivotar` no tiene traducción de `PROC TRANSPOSE`; es un hueco explícito.

## Hito 135m. Constructores con la forma que usa el lowering (MG-P1-03, ajuste)

- Fecha: 2026-11-09.
- Qué se hizo:
  - `unir` (`ir/operadores.py`) recibe `keys` como pares (izquierda, derecha) y produce la misma forma
    que `lower_sql_flow.py`: `by`, `keys`, `join_type`, `sources`, `condition`. Acepta `cross` sin llave.
    Antes usaba `by` y no coincidía con lo que el emisor de `tMap` lee.
  - `combinar` (MERGE) mantiene la forma de `lower_data.py`: `by`, `join_type`, `sources` y sin `keys`.
  - `tests/unit/test_ir_operadores.py`: 25 pruebas, incluida la forma de `unir`, `cross` y la forma de
    `combinar`.
- Pruebas: suite completa **2668 pasan, 27 se saltan, 145 xfail**; `ruff check .` limpio.
- Decisiones:
  - Se adaptan los constructores al lowering existente. No se migra el lowering a los constructores: eso
    cambiaría la forma de las uniones y del emisor, y queda como tarea aparte con revisión.
- Límites:
  - Ningún pase usa `unir` ni `combinar` todavía. MG-P1-03 sigue abierto en el criterio «L1 a L3
    construyen su plan».

## Hito 136m. Los constructores reproducen la firma del lowering en L1 a L3 (MG-P1-03)

- Fecha: 2026-11-09.
- Qué se hizo:
  - `tests/unit/test_ir_operadores_corpus.py`: para cada operador de los planes de L1, L2 y L3, se
    reconstruye con su constructor a partir de sus parámetros y debe dar la misma firma que el
    lowering. Cubre `join`, `filter`, `select`, `sort`, `dedup` y `union`.
  - La prueba encontró desviaciones reales, que se corrigieron en `ir/operadores.py`:
    - `ordenar`: `descending` es una lista por clave, como guarda el lowering, y acepta `outputs`.
    - `deduplicar`, `filtrar`: aceptan `outputs` opcional, que solo aparece si se da.
    - `unir`: `sources` es la tabla base del FROM y puede venir vacía; el resto va en `keys`.
  - Se ajustó la prueba negativa de `unir` al contrato nuevo.
- Pruebas: suite completa **2710 pasan, 27 se saltan, 145 xfail**; `ruff check .` limpio.
- Límites:
  - La prueba cubre seis kinds. `aggregate`, `derive`, `rename`, `read`, `read_file` y `write` no
    tienen reconstrucción en la prueba todavía.
  - MG-P1-03 sigue abierto en el criterio «L1 a L3 construyen su plan»: los constructores ya
    reproducen la forma del lowering, pero ningún pase los usa.

## Hito 137m. Constructores de `aggregate` y `derive` reproducen la firma del lowering (MG-P1-03)

- Fecha: 2026-11-09.
- Qué se hizo:
  - `ir/operadores.py`:
    - `calcular` conserva las claves extra de cada asignación (por ejemplo `origin`) y acepta los
      opcionales del lowering: `outputs`, `modo` (`agrega`) y `declared` (LENGTH, FORMAT).
    - `agregar` acepta `outputs`, `pendiente` y `status`; con `pendiente` el operador es `parcial`.
  - `tests/unit/test_ir_operadores_corpus.py` reconstruye también `aggregate` y `derive`. Los planes de
    L1 a L3 reproducen la firma del lowering en todos sus operadores de esos kinds.
  - `tests/unit/test_ir_operadores.py`: dos pruebas nuevas para los parámetros opcionales.
- Pruebas: suite completa **2712 pasan, 27 se saltan, 145 xfail**; `ruff check .` limpio.
- Límites:
  - La prueba aún no cubre `rename`, `read`, `read_file` ni `write`.
  - MG-P1-03 sigue abierto en el criterio «L1 a L3 construyen su plan»: los constructores reproducen
    la forma del lowering, pero ningún pase los usa.

## Hito 138m. Constructores de lectura y escritura reproducen la firma del lowering (MG-P1-03)

- Fecha: 2026-11-09.
- Qué se hizo:
  - `ir/operadores.py`:
    - `leer` tiene dos formas, igual que el lowering: la de SQL (solo `dataset`) y la de DATA step
      (`dataset` e `in`, aunque valga None). Se elige con `incluir_bandera`.
    - `leer_archivo` siempre incluye sus opciones (`dbms`, `delimiter`, `getnames`, `sheet`,
      `guessingrows`), aunque valgan None.
    - Nuevo `escribir_archivo` (kind `write_file`), con `inputs`, `outfile`, `dbms` y `delimiter`.
  - `tests/unit/test_ir_operadores_corpus.py` reconstruye `read`, `write`, `read_file` y `write_file`.
    Los planes de L1 a L3 reproducen la firma del lowering en todos los operadores con constructor.
  - `tests/unit/test_ir_operadores.py`: pruebas de las dos formas de `leer` y de las opciones de los
    archivos.
- Pruebas: suite completa **2714 pasan, 27 se saltan, 145 xfail**; `ruff check .` limpio.
- Límites:
  - `rename` no aparece en los planes de L1 a L3, así que la comprobación no lo cubre.
  - MG-P1-03 sigue abierto en el criterio «L1 a L3 construyen su plan»: los constructores reproducen
    la forma del lowering, pero ningún pase los usa.

## Hito 139m. Estado de MG-P1 en el plan maestro (sin cambio de código)

- Fecha: 2026-11-09.
- Qué se hizo: se añadió a la sección MG-P1 de `plan-migrador-general.md` el avance de los hitos 130m a
  138m, con lo que cumple y lo que no. No se recalculó la tabla de créditos de la sección 11b: el
  método pide un juicio por tarea que todavía no está acordado.
- Pruebas: sin cambios de código; la última suite completa es la del hito 138m (2714 pasan).
- Pendientes que quedan abiertos: MG-P1-02 (comparación con `sgm migrar` para tipos de `PROC IMPORT`;
  bloques de L3 a L8), MG-P1-03 (migrar el lowering a los constructores, decisión de revisión), y la
  verificación en Studio del `.item` con `LENGTH`, bloqueada por el MCP.

## Hito 140m. Créditos de MG-P1 con el método de la sección 11b (propuesta, sin cambiar la cifra)

- Fecha: 2026-11-09.
- Qué se hizo: se recalculó la fila de MG-P1 con el método de la sección 11b, tarea por tarea. No se
  cambió la tabla del plan: la asignación de créditos es un juicio y el 43,0 de 70 del hito 126m no se
  puede reconstruir desde el plan.
- Propuesta por tarea (1 = hecha; 0,5 = parcial con ejecución; 0,25 = casos puntuales; 0 = sin evidencia):
  - MG-P1-01 (8 h): 1. MG-P1-02 (12 h): 0,25. MG-P1-03 (14 h): 0,5. MG-P1-04 (12 h): 0,5.
  - MG-P1-05 (12 h): 0,5. MG-P1-06 (6 h): 0,25. MG-P1-07 (3 h): 1. MG-P1-08 (3 h): 1.
  - Total: **37,5 de 70 (53,6 %)**, frente a 43,0 (61 %) que dice la sección 11b.
- Decisión pendiente: confirmar la asignación de créditos. Si se confirma, la sección 11b se corrige y
  el avance global baja en la misma proporción; no se corrige hasta que el usuario lo decida.
- Pruebas: sin cambios de código.

## Hito 141m. Créditos de MG-P1 aplicados, uniones de SQL por el constructor `unir` y estado de Studio

- Fecha: 2026-11-09.
- Qué se hizo:
  - **Plan (sección 11b):** MG-P1 pasa de 43,0 a 37,5 horas de crédito (54 %), con la asignación por tarea
    del hito 140m. El total pasa de 242,75 a 237,25 h, y el avance global de 27,1 % a 26,5 %. Las demás
    fases no cambian: no se reevaluaron en este hito.
  - **Lowering de SQL (`ir/lower_sql_flow.py`):** las uniones (`JOIN` y semijoin de `IN`/`NOT IN`) construyen
    sus parámetros con `operadores.unir`. Si el constructor rechaza la unión, se usa la forma anterior
    (`legado`), así que ningún programa que migraba deja de hacerlo.
  - Las demás operaciones (`filter`, `derive`, `aggregate`, `sort`, `dedup`) siguen construyéndose
    directamente con `Builder.op`. Su equivalencia con los constructores la comprueba
    `test_ir_operadores_corpus.py` en L1 a L3.
- Pruebas: suite completa **2714 pasan, 27 se saltan, 145 xfail**; `ruff check .` limpio.
- Studio: `sgm studio salud` sigue sin conexión (MCP en 127.0.0.1:3927 rechazado). La verificación del
  `.item` con `LENGTH` queda pendiente hasta que Studio esté abierto con su MCP.
- Límites:
  - MG-P1-03 sigue con el criterio «L1 a L3 construyen su plan» sin cumplirse del todo: las uniones ya
    pasan por el constructor, pero `filter`, `derive`, `aggregate`, `sort` y `dedup` no.

## Hito 142m. Pasos de SQL construidos por el constructor (MG-P1-03)

- Fecha: 2026-11-09.
- Qué se hizo: en `ir/lower_sql_flow.py`, los pasos `filter`, `derive`, `dedup` y `sort` de `PROC SQL`
  toman sus parámetros de `operadores.filtrar`, `calcular`, `deduplicar` y `ordenar` mediante el helper
  `_paso`. Si el constructor rechaza el paso, se usa la forma anterior, como con las uniones (hito 141m).
  Se añadió `_paso` al final de `lower_sql_flow.py`.
- Pruebas: suite completa **2714 pasan, 27 se saltan, 145 xfail**; `ruff check .` limpio. Las pruebas de
  golden y de equivalencia (`test_golden*.py`) pasan sin cambios, así que las firmas no cambian en el
  corpus.
- Límites:
  - `aggregate` de SQL sigue construyéndose con `chain.step`, y `sort` y `dedup` de `PROC SORT`
    (`ir/lower_procs.py`) tampoco pasan por el constructor.
  - `ruff format` se aplicó a `lower_sql_flow.py`; cambió también una condición ajena a estos pasos (un
    `if` que cabía en una línea).
  - Studio sigue sin responder: la verificación del `.item` con `LENGTH` sigue pendiente.

## Hito 143m. Studio verificado de extremo a extremo para `l0_07`; recuperación documentada

- Fecha: 2026-11-09.
- Qué pasó: `sgm studio salud` no conectaba. Talend Studio estaba abierto (proceso
  `Talend-Studio-win-x86_64`, bridge en el puerto 3930), pero el servidor MCP de `talend-mcp`
  (puerto 3927) no estaba corriendo. No era un fallo de Studio ni hizo falta reinstalar nada.
- Qué se hizo:
  - Se arrancó `talend-mcp` tal como lo documenta `docs/guia-validacion-studio.md`, con
    `TALEND_MCP_ALLOW_WRITE=1 TALEND_MCP_ALLOW_EXECUTE=1 bun run start:server` desde
    `C:\Users\USUARIO_BISOLUTION1\code\talend-mcp`. No se modificó su código. `healthz` responde
    `{"ok":true,"service":"talend-mcp","toolCount":258}`.
  - `sgm studio salud` pasó a «Studio responde y deja escribir».
  - Se emitió `l0_07_if_then_else` a una carpeta de trabajo y se ejecutó en Studio con
    `tools/corpus_studio.py validar`. Primer intento: `--padre` mal (`job_programa_0`), y luego
    «no se encuentra la ruta» porque faltaba el `mapa.yaml`. Con el mapa: **coincide, 0 diferencias**.
- Documentado: `docs/guia-validacion-studio.md`, sección 7 (diagnóstico, arranque, y los dos errores
  de `validar`). `AGENTS.md` tiene un apartado corto que apunta a esa sección.
- Límites: `talend-mcp` se apaga con reinicios y al cerrar la terminal que lo lanzó. Solo se verificó
  `l0_07`; los demás casos y el lote completo de Studio siguen sin correr.

## Hito 144m. Intento de lote de L0 a L2 en Studio: bloqueado por Studio, no por el código

- Fecha: 2026-11-09.
- Qué se hizo: se emitieron los 45 casos de L0 a L2 (todos con código de salida 0) y se preparó una
  carpeta por caso con sus `.item` y `.properties`. Se lanzó `tools/corpus_studio.py lote` con los 45 y
  el backend `mcp`.
- Resultado: el MCP respondió a `healthz`, pero el puente de Studio (3930) no contestó en 25 s
  (`BRIDGE_UNAVAILABLE`). Después, `sgm studio salud` falla por el mismo motivo: las llamadas al MCP
  agotan el tiempo. Diagnóstico: probablemente un diálogo modal abierto en Talend Studio o una
  compilación en curso. No se pudo comprobar porque la ventana de Studio no es accesible desde aquí.
- Pendiente: cerrar el diálogo o esperar en Studio y reintentar `lote` con los 45 casos. Ver la sección 7
  de `docs/guia-validacion-studio.md`.
- Pruebas: sin cambios de código en este hito.

## Hito 145m. Lote de L0 a L2 en Studio por tandas; un bloqueo en L1 que pide revisión en la ventana

- Fecha: 2026-11-09.
- Validación sin Studio: los 45 Jobs emitidos de L0 a L2 pasan `validar_job` (sin defectos
  estructurales). No hay herramienta de `talend-mcp` que compile sin el puente de Studio:
  `talend_validation_validate_design` solo valida la especificación en memoria.
- Compilación en Studio por tandas de 5: los 20 primeros Jobs (L0 completo hasta `l0_11`, y
  `l1_01`) compilan. Al llegar a `l1_06`, la tanda no contestó en 25 s (`BRIDGE_UNAVAILABLE`), y
  después Studio dejó de responder (`timed out` en el MCP). Pendiente: revisar en la ventana de Studio
  qué diálogo aparece tras compilar `l1_06` o `l1_07`, antes de volver a probar.
- Lección: el puente de Studio corta a los 25 s por llamada. Una tanda de 5 Jobs tarda entre 12 y 23 s:
  conviene tandas de 2 a 3 y `studio salud` antes de cada una.

## Hito 146m. Compilación en Studio de L0 a L2, caso por caso: 43 de 45

- Fecha: 2026-11-09.
- Resultado en Studio real (`lote` con backend `mcp`, un caso por llamada para no pasar el límite del
  puente):
  - L0: 15 de 15 compilan. L1: 13 de 15 (`l1_01` a `l1_13`). L2: 15 de 15.
  - **Fallan `l1_14_expresion_compuesta` y `l1_15_distinct_tildes`** con `BRIDGE_UNAVAILABLE`: el puente no
    contesta en 25 s. Repetido en varios intentos, así que no es un fallo transitorio.
  - Ningún caso dispara un error de compilación real: en ningún caso Studio devolvió «no compila».
- Diagnóstico con el MCP (`talend_bridge_log_tail`): el log de Studio muestra «El hilo de la interfaz de
  Studio está ocupado (se acabó el tiempo de espera)» en `/workbench/dialogs/list`, peticiones lentas de
  `/workspace/refresh` de unos 10 s y «Conexión interrumpida atendiendo /automation/job/build-batch».
  El hilo de la interfaz de Studio se queda ocupado y el puente no llega a responder.
- Lo que no está resuelto: por qué esos dos Jobs bloquean el hilo. Hipótesis sin verificar: la expresión
  del `tMap` (`BETWEEN` como `>=`/`<=`, `LIKE` como `matches`, o el `DISTINCT` de `l1_15`). Los demás
  casos con `tMap` y con tildes compilan.
- Pendiente: mirar el `tMap` de `l1_14` y `l1_15` en la ventana de Studio, y el log completo con
  `talend_bridge_log_tail` en el momento del fallo.
- Pruebas: sin cambios de código en este hito.

## Hito 147m. Aislamiento de la construcción que bloquea el puente en `l1_14` (variantes)

- Fecha: 2026-11-09.
- Método: variantes del programa de `l1_14`, emitidas y compiladas en Studio una por una. Las variantes
  viven en el scratchpad, no en el corpus.
- Resultados (compilación en Studio):
  - Sin `ORDER BY neto DESC, id_venta`: **compila**.
  - `BETWEEN` cambiado a `cantidad >= 2` (sin cota superior): **compila**.
  - Sin `LIKE 'T%'`: **bloquea el puente** (`BRIDGE_UNAVAILABLE`). El `LIKE` no es la causa.
  - Sin la expresión `(monto - 50) * cantidad`: no se pudo medir; Studio quedó ocupado tras la variante
    anterior y no respondió al chequeo previo.
- Estado: tras la última variante, `talend_bridge_log_tail` muestra «El hilo de la interfaz de Studio
  está ocupado» en `/workspace/refresh`. Hace falta mirar la ventana de Studio y cerrar el diálogo.
- Pendiente: compilar `soloOrdenMixto` (solo el `ORDER BY` con dos claves y sentidos distintos),
  `soloOrdenNeto` (un solo sentido) y `soloBetween` (solo el `BETWEEN` original), una vez Studio responda.
  Si `soloOrdenMixto` bloquea, la causa es el `tSortRow` con dos claves de sentido distinto.
- Pruebas: sin cambios de código en este hito.

## Hito 148m. Causa probable del bloqueo de `l1_14` y `l1_15`: el límite de 25 s del puente

- Fecha: 2026-11-09.
- Resultados (Studio, una compilación por variante):
  - `soloOrdenMixto` (solo el `ORDER BY` de dos claves), `soloOrdenNeto` y `soloBetween`: **compilan**.
  - `l1_14` completo (`WHERE` con `LIKE` y `BETWEEN`, más `ORDER BY`) y `l1_15`: **bloquean el puente**.
  - Quitar cualquiera de las piezas de `l1_14` lo hace compilar (hito 147m). Un Job simple tarda 11 s.
- Diagnóstico: el log del puente dice que el hilo de la interfaz no contesta en 25 s. La constante de 25 s
  está en el plugin del puente (`com.andres.talend.bridge`, en el propio Studio), no en `talend-mcp` ni en
  `sgm`. Hipótesis: el Job completo tarda más de 25 s en generarse y compilarse; quitar una pieza lo acorta.
  Sin confirmar: no se pudo medir el tiempo de `l1_14` completo porque el puente corta antes de responder.
- Lo que no es: no es un error de compilación. Ningún caso devuelve «no compila»; el puente corta antes.
- Propuesta: subir el tiempo de espera de la interfaz en el plugin del puente (de 25 s a un valor mayor) o
  partir `l1_14` en dos Jobs. Lo primero es un cambio en código del puente, que es del usuario.
- Pruebas: sin cambios de código en el repositorio en este hito.

## Hito 150m. Conexiones de `tMap` que Studio no carga, validador que lo impide, y CASE de texto

- Fecha: 2026-11-09.
- Problema reportado por el usuario: al abrir un Job, Studio muestra «Error al cargar el trabajo» en la
  conexión `tSortRow_1_in` y después en `row1`.
- Causas encontradas y corregidas:
  1. **Nombre de la conexión que sale de un `tMap`** (`talend_item/desde_plan.py`, `_nombre`). Studio exige
     que coincida con la `outputTables` del `tMap`. El código le daba prioridad al destino (`_in`), y eso
     no carga. Ahora, si el `tMap` tiene un único consumidor, la conexión lleva el nombre de la salida.
     Una primera versión sobrescribió `_consumidores` y otra quitó el fallback `row1`; ambas se corrigieron.
  2. **Validador (`talend_item/validador.py`, `_nombres_de_tmap`)**: una conexión que sale de un `tMap` tiene
     que llamarse como una de sus salidas, y una que entra en un `tMap` como una de sus entradas. Si no,
     el defecto queda como `P-JOB-INVALIDO`.
  3. **El Job con defectos no se escribe** (`cli_migrar._validar`). Antes se escribía y Studio lo rechazaba.
     Ahora queda solo el pendiente con su motivo. Afecta a `l1_10`, `l2_11`, `l2_15`, `l3_07`, `l5_11`, todos
     en `tests/corpus/migrar_pendientes.yaml` como `P-JOB-INVALIDO`.
  4. **`CASE` de texto tipado como predicado** (`ir/types_code.py`, `expression_type`). `IS MISSING` dentro
     de un `CASE` hacía booleana la expresión entera, y el emisor la envolvía como `Long`. Causaba errores
     de Java en `l2_08`.
- Pruebas: suite completa **2717 pasan, 27 se saltan, 145 xfail**; `ruff` limpio. Nuevas pruebas en
  `tests/unit/test_conexion_salida_tmap.py`.
- Studio: tras corregir, el lote de L0 a L2 se reemitió (42 Jobs con `.item`), y la compilación se
  interrumpió por «Network Issue Occured» en Studio: hay un diálogo abierto. Pendiente: cerrarlo y repetir.
- Límites:
  - `l3_07`: un `tMap` con dos consumidores sigue sin nombre de salida correcto; queda como pendiente.
  - `l1_10`, `l2_11`, `l2_15`: un `tMap` que alimenta a otro `tMap`. No se emite; falta el diseño de esa
    conexión (que la salida del primero tenga el nombre de la entrada del segundo).
  - Lo que Studio abre sin error no se ha comprobado con la ventana de la GUI para los 42 Jobs; la
    compilación por lote sí se comprueba, la carga en la GUI no.

## Hito 151m. Optimizador del plan: las tablas intermedias de `WORK` se funden en un solo `tMap`

- Fecha: 2026-11-10.
- Pedido del usuario: migrar como lo haría un analista de Talend (fuentes, destinos y transformaciones),
  no paso a paso con una tabla de `WORK` entre cada dos sentencias.
- Qué se hizo:
  - Paquete nuevo `src/sgm/optimizar/`. `optimizar(plan)` devuelve una copia del plan con el diseño de
    Talend y un `Informe` con cada decisión. Lo llama `plan_a_jobs` después de desplegar las plantillas.
  - Regla `fundir-pasos-encadenados` (`cadenas.py`, `forma.py`, `reescribir.py`, `sustituir.py`): si una
    tabla de `WORK` la escribe un paso y la lee un solo paso, una vez, y no se exporta, los dos pasos
    quedan en un `map`. Los cruces pasan a ser lookups del mismo `tMap`, los filtros se unen y cada
    columna se escribe con la expresión completa (`doble + 1` pasa a `(monto * 2) + 1`).
  - La fusión se demuestra antes de hacerse. No se funde si: el paso tiene `modo: agrega`, `KEEP`/`DROP`,
    `RENAME` o ramas; la intermedia la leen dos pasos o es frontera; una columna no se puede atribuir a
    una tabla; la llave de un cruce es una columna calculada; o la intermedia entra por el lado de
    consulta de un cruce y el paso anterior filtra o cruza (aplicado después de un `LEFT JOIN`, el
    filtro quitaría filas que el SAS conserva).
  - `talend_item/desde_plan_map.py`: un `map` admite varios pasos `join`. Cada lookup toma las llaves y
    el tipo (interno o externo) del cruce que lo nombra, y su llave puede ser una columna de un lookup
    anterior (`row2.ciudad`).
  - `ir/models.py`: `Graph.rewire_inputs`, para fijar el orden de las entradas de un operador.
  - `decisiones-tomadas.md` tiene la sección «Diseño del Job» con cada tabla que no se escribe y las
    líneas del SAS que cubre. La traza de un nodo fundido incluye las líneas de todos sus pasos.
- Resultado en el corpus: `l1_10`, `l2_11`, `l2_15` y `l5_11` pasaban de no escribir Job
  (`P-JOB-INVALIDO`, un `tMap` que alimenta a otro) a un Job válido. `l2_11` (tres tablas) queda con
  tres lecturas y un `tMap`; `l2_15` (validación en cascada) pasa de tres `tMap` a dos. Se quitaron de
  `tests/corpus/migrar_pendientes.yaml`. Sigue en la lista `l3_07` (un `tMap` con dos consumidores).
- Pruebas: suite completa **2745 pasan, 27 se saltan, 146 xfail**; `ruff` limpio. Nuevas:
  `tests/unit/test_optimizar_cadenas.py` (5), `tests/unit/test_optimizar_corpus.py` (el plan optimizado
  da lo mismo que `esperado/` en los casos que cambian) y `tests/unit/test_optimizar_sustituir.py` (20).
  `test_un_tmap_que_alimenta_a_otro_no_se_escribe...` afirmaba la limitación vieja sobre `l1_10`; se
  reemplazó por `test_dos_etapas_encadenadas_se_hacen_en_un_solo_tmap`.
- Sin verificar: **no se compiló nada en Studio**; el servidor MCP (puerto 3927) estaba apagado. Lo
  comprobado es el intérprete contra `esperado/` y el validador estructural del `.item`.
- Límites:
  - `l2_15` queda como xfail en la prueba de equivalencia: el intérprete no expande `t.*` tras un `JOIN`
    (el mismo hueco que ya tenía en el anillo B sin optimizar).
  - Los DATA step encadenados (`modo: agrega`, `KEEP`, `DROP`, `RENAME`) todavía no se funden.
- Decisiones:
  - Una tabla de `WORK` que solo lee el paso siguiente no es una salida del programa, aunque el caso
    del corpus la declare en `salidas` (`aceptadas` en `l2_15`, `base_lealtad` en `l5_11`). El Job no
    la escribe y `decisiones-tomadas.md` lo dice.
  - El optimizador trabaja sobre el plan, no sobre el Job: así el intérprete ejecuta el plan
    optimizado y la equivalencia se comprueba sin Studio.

## Hito 152m. Leer y calcular una sola vez: duplicados unidos, `tReplicate` y `tMap` con ramas

- Fecha: 2026-11-10.
- Qué se hizo:
  - `optimizar/duplicados.py`, regla `calcular-una-vez`: dos operadores con el mismo tipo, los mismos
    parámetros (sin contar el nombre del resultado) y las mismas entradas se unen en uno. Va de arriba
    abajo, así que al unir dos lecturas se pueden unir los pasos que las siguen. Las referencias al
    nombre que desaparece (`__in_l26_1.clave_in1`) se cambian por el que queda. No se unen dos
    operadores cuyos resultados se vuelven a juntar más abajo.
  - `optimizar()` alterna las dos reglas hasta que ninguna cambia nada.
  - Emisor (`talend_item/desde_plan.py`): un nodo con varios consumidores reparte su flujo con un
    `tReplicate` (plantilla ya existente). Una lectura con varios consumidores ya no se copia, salvo
    que sus ramas se vuelvan a juntar (un cruce de la tabla consigo misma, `l2_15`): ahí sigue una
    lectura por rama. Si pasa lo mismo con un nodo que no es lectura queda `P-REPARTO-RECONVERGE`.
  - Un `map` con ramas (`branches`) es un `tMap` con una salida por rama, cada una con su condición.
    Antes las ramas se ignoraban.
  - Los nombres de fila (`row1`) y de salida (`out1`) de los `tMap` ya no se repiten dentro de un Job:
    cada `tMap` numera a partir de los que ya usó el anterior. Antes, dos `tMap` del mismo Job tenían
    los dos `row1` y `out1`.
  - `ir/models.py`: `Graph.in_edges`, `out_edges` y `descendants`.
- Resultado en el corpus (101 casos de `L0` a `L6`, con `--muestra`):
  - **Todos escriben Job.** Antes del hito 151m, cinco no lo escribían. `l3_07` sale de
    `migrar_pendientes.yaml`, que ya no tiene ningún `P-JOB-INVALIDO`.
  - `l2_07` (`IN` y `NOT IN` de la misma subconsulta): de 4 lecturas, 4 `tMap` y 2 `tUniqRow` a
    2 lecturas, 3 `tMap` y 1 `tUniqRow`. `l3_05` (tres `GROUP BY` iguales): de 3 lecturas y
    3 `tAggregateRow` a 1 y 1. `l2_04`: de 4 lecturas a 2.
  - Total de lecturas: 140 en 96 Jobs antes; 131 en 101 Jobs ahora. `tReplicate`: 17.
  - `client_large.sas`: 45 decisiones (30 fusiones, 15 cálculos repetidos), los defectos de Job bajan de
    30 a 19 y los operadores sin soporte de 1669 a 1541. Sigue sin escribir Job. Tarda 8,0 s (6,7 s
    antes).
- Pruebas: suite completa **2750 pasan, 27 se saltan, 146 xfail**; `ruff` limpio. Cuatro pruebas nuevas
  en `tests/unit/test_desde_plan.py` (reparto, ramas que se juntan, nombres únicos, `tMap` con ramas).
  `test_la_misma_tabla_leida_dos_veces_da_un_nodo_por_consumidor` afirmaba el diseño viejo y se
  reemplazó por `..._se_lee_una_vez_y_se_reparte`.
- Sin verificar: **nada de esto se compiló en Studio** (MCP apagado). En particular no está comprobado
  que Studio acepte dos `tMap` que comparten a la vez el `tReplicate` de su fila principal y el de su
  lookup (`l2_07`), ni la forma exacta del `.item` de `tReplicate` más allá de su plantilla. Es la
  tarea MG-P8b-09.
- Problema encontrado y corregido: la primera versión reiniciaba el recorrido después de cada cambio
  y `client_large.sas` pasó de 7 s a 191 s. Ahora cada regla hace una pasada en orden de flujo.
- Límites:
  - Una rama que nombra su tabla y la lee otro paso a través de un `read` todavía no se conecta.
  - Dos `tMap` hermanos sobre la misma fuente quedan detrás de un `tReplicate`; una persona haría
    un `tMap` con dos salidas (MG-P8b-06).
  - Una tabla final de `WORK` que no se exporta y cuyo productor tiene otros consumidores ya no
    recibe su `tLogRow`.
- Decisiones:
  - Repartir con `tReplicate` y no con salidas duplicadas del `tMap`: sirve para cualquier
    componente y deja el `tMap` con una salida por significado.
  - Plan actualizado en el mismo cambio: fase `MG-P8b` en `plan-migrador-general.md`.

## Hito 153m. Fusionar por versión cuando SAS reutiliza nombres de `WORK`

- Fecha: 2026-11-10.
- Qué se corrigió: el optimizador no trata como consumidor externo una lectura de `WORK.temporal`
  que está conectada a otro productor y, por tanto, corresponde a otra versión de la tabla. El
  emisor también resuelve un `read` por la arista de su productor; usa el nombre del conjunto solo
  cuando no hay arista. Esto evita confundir productores distintos que reutilizan el mismo nombre.
- Prueba de regresión: se reutiliza `WORK.temporal` dos veces y se comprueba que se funden las dos
  cadenas válidas y que ambas salidas conservan sus filas y columnas.
- Pruebas: `uv run python -m pytest -q`: **2751 pasan, 27 se saltan, 146 xfail**; `uv run ruff check .`:
  limpio.
- Sin verificar en Studio: el servidor MCP no estaba disponible en esta sesión. La prueba cubre el
  plan y el intérprete, no la compilación del `.item` optimizado.
- Decisión: cuando un operador `read` tiene aristas de entrada, estas son la fuente autoritativa de
  su versión; el nombre SAS es solo fallback para una lectura sin productor explícito.

## Hito 154m. Fusión acotada de DATA step aditivos

- Fecha: 2026-11-10.
- Qué se hizo: la fusión combina en orden las asignaciones `modo: agrega` de dos DATA step y reescribe
  referencias a las columnas calculadas por el primero. `KEEP`, `DROP` y `RENAME` se trasladan al
  `tMap` final cuando aparecen en el consumidor. La semántica de salida de estos modificadores se
  apoya en `lestmtsref`, pp. 91-92 (DROP), 216-217 (KEEP) y 326-327 (RENAME).
- Pruebas: se comparan las filas tras dos DATA step aditivos y se cubren `KEEP` + `RENAME` y `DROP`
  al final de la cadena. Suite completa: **2754 pasan, 27 se saltan, 146 xfail**; `ruff` limpio.
- Límite: es una entrega parcial de MG-P8b-05. No se funde si `KEEP`, `DROP` o `RENAME` aparece en
  el productor, porque cambia la interfaz de columnas del paso intermedio; tampoco se fusionan
  declaraciones `LENGTH`/`FORMAT`. Aún falta un caso nuevo del corpus y demostrar estos límites con
  la batería de equivalencia del corpus.
- Decisión: no inferir alias ni columnas que sobreviven a un modificador del productor; mantener
  esos pasos separados hasta modelar explícitamente su interfaz y probarla.

## Hito 155m. Caso de corpus para DATA step encadenados

- Fecha: 2026-11-10.
- Qué se hizo: se agregó `l1_16_data_steps_encadenados` con entrada CSV, dos DATA step aditivos,
  `KEEP`, `RENAME` y salida esperada. El anillo B compara el plan optimizado contra esa salida.
- Oráculo: el verificador A solo ejecuta la salida de `CREATE TABLE`; este caso produce la salida con
  DATA step, por lo que queda en capa C con esperado manual y se comprueba con el intérprete. No se
  cambió ni se debilitó el oráculo.
- Se ajustó el tablero del corpus a 118 casos (117 con esperado).
- Límite de MG-P8b-05: los modificadores `KEEP`/`DROP`/`RENAME` en el productor siguen evitando la
  fusión; hace falta modelar la interfaz de columnas para poder trasladarlos sin alterar referencias.

## Hito 156m. Un `tMap` ramificado para transformaciones hermanas

- Fecha: 2026-11-10.
- Qué se hizo: mapas hermanos que leen el mismo conjunto, usan la misma proyección y filtran por
  columnas que pasan intactas se convierten en un solo `map` con dos salidas filtradas. También se
  consolidan las lecturas puras duplicadas del mismo conjunto, sin cambiar el comportamiento de
  lectores con parámetros distintos. El intérprete ejecuta los pasos compartidos y reparte sus filas
  según las ramas.
- Caso del plan: `l2_10_is_missing_numerico_y_texto` queda con un `tMap` ramificado y conserva ambas
  salidas; la prueba de corpus compara el resultado con `esperado/`. Se añadió otra prueba de forma e
  interpretación con filtros complementarios.
- Límites: si una rama filtra por una columna que la proyección no conserva o que calcula/modifica,
  no se agrupa. `l2_07` (filtro sobre `canal` que no sale) y `l3_05` (filtros hermanos de agregado)
  siguen pendientes; tampoco se admiten proyecciones distintas por rama.
- Pruebas: suite completa **2762 pasan, 27 se saltan, 146 xfail**; `ruff` limpio. La prueba nueva de
  forma para `l2_10` se añade en este hito y se vuelve a correr la suite completa antes del commit.

## Hito 157m. Ramificar filtros de grupos después de un agregado

- Fecha: 2026-11-10.
- Qué se hizo: dos operadores `filter` hermanos que consumen el mismo agregado se convierten en un
  `map` sin pasos compartidos y con una salida filtrada por rama. Así `l3_05_having_conteo` genera
  ambos grupos desde un solo agregado, en vez de duplicar el `tAggregateRow` y repartirlo.
- Verificación: el caso de corpus mantiene las salidas de `grupos_grandes` y `grupos_pequenos` contra
  `esperado/`; la prueba estructural confirma el único mapa con ambas ramas.
- Límites: `l2_07` sigue pendiente; combinar `IN` y `NOT IN` requiere un `tMap` con flujo de rechazo
  del cruce, no solo filtros hermanos sobre un mismo flujo.

## Hito 158m. Salida de rechazo para `NOT IN` de una subconsulta

- Fecha: 2026-11-10.
- Qué se hizo: el optimizador reconoce, con fuentes, llaves y proyección iguales, un `INNER JOIN` y su
  `LEFT JOIN` hermano filtrado por `missing(clave_lookup)`. Los combina en un único mapa: coincidencias
  por la salida normal y no coincidencias por `rejectInnerJoin`. El emisor escribe el rechazo como
  conexión `REJECT`; el intérprete usa temporalmente el left join para repartir filas y valida la
  equivalencia de ambas salidas.
- Verificación: `l2_07_not_in_subconsulta` coincide con `esperado/`; prueba estructural confirma el
  mapa ramificado, y prueba del Job confirma `innerJoin="true"` junto con `rejectInnerJoin="true"`.
  El trabajo existente de `l2_10` y `l3_05` también se mantiene.
- Límites: solo se aplica al patrón con una llave demostrable, `missing` de la columna del lookup y
  una única derivación común. La ejecución real en Talend Studio queda pendiente.
- Pruebas: suite completa **2765 pasan, 27 se saltan, 146 xfail**; `ruff` limpio.

## Hito 159m. Conservar destino calificado al empujar SQL a la misma base

- Fecha: 2026-11-10.
- Qué se hizo: se añadió `l2_16_sql_en_misma_base`, con una fuente y un destino `LIBNAME` asignados
  a Impala. El caso es estructural y queda `sin_esperado`: no se conecta a una base. Su prueba confirma
  que `push_to_db` emite un único `exec_sql` con `CREATE TABLE LZ.salida ... FROM LZ.origen`.
- Corrección: `_output_name` antes convertía cualquier punto en guion bajo y alteraba destinos
  permanentes (`LZ.salida` → `LZ_salida`). Ahora solo retira el prefijo `WORK.`; las tablas de
  biblioteca conservan su calificación.
- Pendiente previo revisado: `client_large.sas` emite actualmente dos, no cuatro, casos de
  `P-REPARTO-RECONVERGE` (líneas 1384 y 1554). MG-P8b-07 queda bloqueado: la documentación de
  `talend-mcp` registra que `tHashInput` compila pero no recibe filas en la topología probada
  (INTERNALS 70). No se emitirá como solución hasta validar un transporte que funcione.
- Pruebas: `tests/unit/test_push_db.py` (6 pruebas) y la validación del corpus pasan. Suite completa:
  **2768 pasan, 27 se saltan, 146 xfail**; `ruff` limpio.
- Decisión: continuar con MG-P8b-08 al estar bloqueado P8b-07 por un componente dependiente; no
  conectar a ninguna base y limitar la prueba a la forma del SQL emitido.

## Hito 160m. Compilación del optimizador en Studio y tipo de `CASE`

- Fecha: 2026-11-10.
- Qué se hizo: con Studio abierto y MCP respondiendo, se generaron y compilaron en lote 56 Jobs de
  L0–L3. La primera compilación encontró un error real en `l2_08_case_when_tras_left_join`: una
  condición comparativa dentro de un `CASE` clasificaba el valor de texto como Boolean y el emisor
  lo envolvía en `Long.valueOf`.
- Corrección: la expresión regular de detección de `CASE` contenía un carácter de control en vez de
  `\b`. Corregida la frontera de palabra; se añadió regresión de tipo y del `.item` en
  `test_conexion_salida_tmap.py`. `l2_08` compiló individualmente y luego el lote regenerado pasó:
  **56 compilan, 0 fallan**. Studio quedó saludable y el arnés retiró sus Jobs temporales del proyecto.
- Alcance: se excluyeron `l1_14_expresion_compuesta` y `l1_15_distinct_tildes`, que ya tenían bloqueo
  de bridge documentado en hitos 146–148, y `l2_16_sql_en_misma_base`, que necesita asignar la
  biblioteca al motor para generar su Job de base. No se ejecutaron Jobs ni se conectó a ninguna base.
- Pruebas: suite completa **2769 pasan, 27 se saltan, 146 xfail**; `ruff` limpio.
- Límite: MG-P8b-09 sigue parcial hasta compilar los dos casos con bloqueo previo y el Job de base
  con su configuración estructural. MG-P8b-07 continúa bloqueado por la validación pendiente de
  `tHashInput`.

## Hito 161m. Reintento de casos bloqueados por el bridge

- Fecha: 2026-11-10.
- Qué se hizo: con Studio y el bridge sanos se regeneraron y compilaron `l1_14_expresion_compuesta`
  y `l1_15_distinct_tildes`, antes bloqueados por el límite de respuesta del bridge (hitos 146m–148m).
  Ahora hay **58 Jobs** de L0–L3 compilados en los lotes de los hitos 160m y 161m. El arnés limpió los
  Jobs temporales del proyecto; no quedó ninguno `h160`/`h161` en `process/`.
- Límite remanente de MG-P8b-09: `l2_16_sql_en_misma_base` sigue sin compilar. Con `LZ` asignado a
  Impala, la pasada genera `exec_sql`, pero `plan_a_jobs` registra que no existe emisor para
  `tImpalaRow`; además los nodos `read`/destino de base no tienen aún traducción en este camino.
  No se conectó a una base ni se envió un Job incompleto a Studio.
- Studio responde y deja escribir tras los lotes. Sin cambios de código en este hito; la suite de
  2769 pruebas y `ruff` quedaron en verde en el hito 160m.
- Decisión: el siguiente trabajo es completar la emisión de `exec_sql`/`tImpalaRow` para MG-P8b-08;
  entonces se podrá incluir `l2_16` en el lote sin conectar a Impala.

## Hito 162m. Emitir `exec_sql` como `tImpalaRow`

- Fecha: 2026-11-10.
- Qué se hizo: el emisor de Jobs ahora traduce `exec_sql` asignado a `tImpalaRow` usando la plantilla
  guardada desde Studio y coloca el SQL en `QUERY`. Desactiva el enlace de plantilla a una conexión
  inexistente; no agrega servidor, credenciales ni parámetros supuestos. El Job conserva un pendiente
  `P-CONEXION-BASE` para configurar host, puerto, base y autenticación, y el `LIBNAME` sigue señalado
  como configuración de sesión pendiente.
- Regresión: `test_push_db.py` genera `l2_16_sql_en_misma_base` por `plan_a_jobs`, verifica el
  componente, el SQL, la falta de conexión inventada, los pendientes y el `.item` escrito.
- Validación Studio: se generó un Job con `tImpalaRow`, pero no se pudo compilar. El MCP primero
  respondió a salud; la llamada de compilación agotó 180 s esperando al bridge de Studio en el puerto
  3930. Las comprobaciones posteriores informaron módulos de terceros requeridos. No se reinstaló ni
  modificó el plugin, y no se conectó a Impala ni se ejecutó el SQL.
- Pruebas: suite completa **2770 pasan, 27 se saltan, 146 xfail**; `ruff` limpio.
- Límite: MG-P8b-08 sigue parcial: `read` de base y destino permanente `write` aún no tienen emisor,
  y el Job no quedó validado en Studio. MG-P8b-09 se mantiene parcial hasta validar `l2_16` en Studio.
- Decisión: dejar la configuración de conexión al usuario y posponer la compilación hasta que Studio
  vuelva a exponer su bridge; no adivinar parámetros ni instalar componentes durante la incidencia.

## Hito 163m. Plegar fronteras de base dentro del SQL

- Fecha: 2026-11-10.
- Qué se hizo: cuando un `read` de Impala alimenta directamente un `exec_sql` del mismo motor y el
  SQL contiene la tabla leída, el emisor pliega esa lectura en el SQL, que ya realiza el `FROM` en la
  base. El `write` posterior se pliega sobre el `tImpalaRow` porque el `CREATE TABLE` materializa el
  destino. `l2_16` deja de reportar operadores sin soporte para lectura/salida y genera solo el nodo
  de SQL; la configuración de sesión y la conexión permanecen como pendientes explícitos.
- Regresión: se amplió el seam de `plan_a_jobs`/`.item` para exigir que no queden pendientes de
  lectura ni destino permanente al emitir el SQL de `l2_16`.
- Pruebas: suite completa **2770 pasan, 27 se saltan, 146 xfail**; `ruff` limpio.
- Validación Studio: sigue bloqueada por la incidencia de bridge descrita en el hito 162m. No se
  ejecutó el Job ni se conectó a Impala.
- Límite: MG-P8b-08 continúa parcial hasta configurar la conexión y compilar el Job en Studio.
- Decisión: solo plegar la lectura cuando fuente y `exec_sql` comparten `db:impala`, hay arista
  directa y el SQL contiene el dataset; otros casos conservan el pendiente en vez de inferir una
  equivalencia.

## Hito 164m. Compilar `l2_16` con `tImpalaRow` en Studio

- Fecha: 2026-11-10.
- Qué se hizo: el primer build reveló dos detalles de generación Java del componente Impala: campos
  vacíos de host/puerto/base se insertan como expresiones sin literal, y el campo PASSWORD vacío se
  inserta en un `if` como código Java vacío. Se escriben las tres cadenas vacías con comillas y se
  usa el literal tipado `((String)null)` para PASS, sin guardar credenciales. Se mantiene `HIVE2`, el
  driver predeterminado de la plantilla de Studio; no se fuerza el driver Impala que no compila con
  la biblioteca disponible.
- Studio presentó el diálogo oficial de 11 módulos externos; el usuario aceptó las licencias y la
  instalación terminó. No se reinstaló ni actualizó el plugin MCP. Después, `l2_16` compiló:
  **1 de 1 Jobs**. Sumado a los 58 Jobs de los hitos 160m–161m, MG-P8b-09 queda en **59 compilados**.
- El test de regresión verifica el `tImpalaRow`, el SQL, los literales de conexión vacíos, la ausencia
  de credenciales, los pendientes explícitos y el `.item` escrito.
- Pruebas: suite completa **2770 pasan, 27 se saltan, 146 xfail**; `ruff` limpio.
- Límite: no se ejecutó el Job ni se conectó a Impala. Host, puerto, base y autenticación continúan
  en `P-CONEXION-BASE`; MG-P8b-08 sigue parcial hasta configurar y validar la ejecución.
- Decisión: el hito acepta la compilación del Job, no su ejecución; la conexión no se configura con
  valores inventados y el SQL permanece sin ejecutarse.

## Hito 165. Integrar `origin/main` y reconciliar la referencia del plan

- Fecha: 2026-11-10.
- Qué se hizo: se integraron los 19 commits remotos con merge, conservando los cambios locales. Se
  resolvieron las discrepancias del intérprete para agregados por fila, expansión de `alias.*`,
  salidas `DUPOUT`, subconsultas versionadas y `NOT IN`; el metadato de subconsulta ya no altera la
  firma del operador ni impide unir las ramas compatibles.
- Se actualizó el golden de `client/client_poc.sas` tras revisar las incorporaciones de cargas
  externas Impala y el orden de salida de agregados. La equivalencia estructural queda documentada
  por hash canónico y la prueba de golden mantiene igualdad exacta. La aceptación del corpus contempla
  que la compuerta de seguridad bloquee artefactos con hallazgos sin publicarlos.
- Pruebas: `uv run python -m pytest -q`: **3008 pasan, 27 se saltan, 142 xfail**;
  `uv run ruff check .` y `git diff --check`: limpios.
- Decisión: las escrituras posteriores que reutilizan un nombre de tabla deben esperar al consumo
  completo de la subconsulta; ordenar solo su lectura permitiría que la versión futura sustituyera la
  anterior antes de ejecutar el cruce.

## Hito 166. `OUTPUT` con varios destinos en parser, IR e intérprete (MG-P4-02 parcial)

- Fecha: 2026-11-10.
- Qué se hizo: el parser recoge todos los nombres de `OUTPUT`; la IR registra el destino múltiple y
  cada sentencia como productor de sus datasets. Si el DATA step contiene al menos un `OUTPUT`
  explícito, no se añade la salida implícita del encabezado. El intérprete distribuye cada observación
  a todos los destinos nombrados y aplica la rama `ELSE` como complemento de la condición previa,
  cuando es demostrable.
- Referencia: `lestmtsref`, pp. 273–274: `OUTPUT` puede nombrar varios datasets y su uso explícito
  suprime la salida automática al final de la iteración. La forma sin destinos usa las salidas del
  encabezado en SAS, pero se deja pendiente en esta implementación.
- Pruebas: suite completa **3011 pasan, 27 se saltan, 142 xfail**; `uv run ruff check .` y
  `git diff --check` limpios.
- Alcance pendiente: Talend aún no emite el enrutamiento de `split` a múltiples salidas. Se conserva
  como pendiente explícito; MG-P4-02 permanece parcial y no se avanza a MG-P4-03 todavía.
- Decisión: la clasificación de destinos en `params.targets` solo se agrega para más de un destino;
  `params.target` mantiene compatibilidad con planes anteriores de un destino.

## Hito 167. Emisión Talend de `OUTPUT` explícito no condicional (MG-P4-02 parcial)

- Fecha: 2026-11-10.
- Qué se hizo: un `OUTPUT` con uno o varios destinos explícitos y sin condición se emite como un
  `tMap` con una salida por destino. Las salidas conservan el esquema de entrada; se verificó que
  desaparece el pendiente genérico del operador `split` y que la plantilla contiene todos los
  `outputTables` esperados.
- Límites: no se emiten `OUTPUT` sin destino, las ramas `IF/ELSE` ni múltiples sentencias `OUTPUT`
  encadenadas. Esas formas quedan pendientes, en vez de emitir un flujo parcial. No se validó este
  `tMap` en Studio; la aceptación es de generación y pruebas unitarias.
- Pruebas: suite completa **3013 pasan, 27 se saltan, 142 xfail**; Ruff y `git diff --check` limpios.
- Decisión: se limita la emisión a un operador `split` incondicional con destinos demostrados. Las
  ramas condicionales necesitan un único `tMap` que conserve todas las filas y aplique filtros
  complementarios sin encadenar salidas ya filtradas.

## Hito 168. Enrutamiento condicional y `OUTPUT;` terminal (MG-P4-02 parcial)

- Fecha: 2026-11-10.
- Qué se hizo: se agrupa un par terminal `IF ... THEN OUTPUT; ELSE OUTPUT;` en un `map` con ramas
  filtradas y condición complementaria; cada destino se vuelve una salida del `tMap`. Un único
  `OUTPUT;` terminal toma los destinos del encabezado `DATA`, como establece SAS. Se conserva como
  pendiente el caso de varias sentencias `OUTPUT` encadenadas fuera del par condicional reconocido.
- Validación: pruebas de IR, interpretación y XML generado para ambos destinos; suite completa
  **3016 pasan, 27 se saltan, 142 xfail**; Ruff y `git diff --check` limpios.
- Límites: no se añadió aún un caso L6 al corpus ni se compiló el Job en Studio; por ello MG-P4-02
  permanece parcial. La transformación del par IF/ELSE solo se aplica cuando es el final del DATA step.
- Decisión: el `ELSE` se traduce como complemento de la condición original únicamente para el par
  inmediato terminal, sin reordenar sentencias ni extender la equivalencia a `ELSE IF` o `DO`.

## Hito 169. Caso L6 de `OUTPUT` con varios destinos

- Fecha: 2026-11-10.
- Qué se hizo: se agregó `L6/l6_13_output_multiple_destinos` al corpus, con entradas y tres CSV
  esperados generados desde una función de referencia explícita. El caso cubre la rama THEN con dos
  destinos y la ELSE con un tercero; el anillo B compara todas las salidas con el intérprete. Se
  añade además una prueba de emisión del mismo programa con tres salidas de `tMap` y tres exportaciones.
- Se amplió el generador de casos L6 para reproducir los esperados de varias tablas. El tablero refleja
  el corpus ampliado: 120 casos, 13 de nivel L6 y 118 con esperado.
- Pruebas: suite completa **3022 pasan, 28 se saltan, 142 xfail**; `uv run ruff check .` y
  `git diff --check` limpios. También pasan el anillo B del caso y la regeneración del corpus.
- Bloqueo: `sgm studio salud` detectó el diálogo `Network Issue Occured`; no se pudo compilar el Job.
  Se sigue la instrucción del repositorio: no reinstalar ni cambiar Talend ante este error.
- Estado: MG-P4-02 sigue parcial; quedan pendientes otras secuencias de `OUTPUT` y la compilación
  del caso en Studio.
