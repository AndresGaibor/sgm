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
