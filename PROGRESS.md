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
