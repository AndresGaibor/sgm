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
  - hito 29: divisi�n de los archivos de m�s de 300 l�neas (R9, fase 3.10): cli.py queda en 276 (comandos a cli_decisiones.py y cli_util.py), expressions.py en 131 (m�s expressions_base.py, expressions_funciones.py, expressions_parser.py), 	alend_translator.py en 43 (m�s 	alend_base.py, 	alend_parser.py, 	alend_funciones.py, 	alend_tabla.py), macros.py en 163 (m�s macros_modelo.py, macros_control.py, macros_llamadas.py), steps.py en 216 (m�s steps_tipos.py), p10_components.py en 194 (m�s eglas_mapeo.py). La salida no cambia: goldens id�nticos.
- Reparaci�n incluida en hito 29: el trabajo de divisi�n ven�a sin terminar y la suite no importaba (	alend_parser.py con un import vac�o y un error de sintaxis; _FUNCTIONS a medio mover a 	alend_tabla.py). Se complet� el movimiento y se dej� el �rbol en verde.
- Verificaci�n: uv run pytest -q: 428 pasan, 1 se salta; uv run ruff check .: limpio; metrics --check: sin empeorar. Ning�n archivo de src/ supera 300 l�neas.

## Hito 28. Partir los archivos de más de 300 líneas: fase 3.10

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
