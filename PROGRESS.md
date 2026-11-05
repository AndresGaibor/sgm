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
