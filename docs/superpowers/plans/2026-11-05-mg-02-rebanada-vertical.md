# MG-02 Rebanada vertical: `sgm migrar` de un programa SAS simple a Jobs de Talend

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `sgm migrar programa.sas --out carpeta` convierte, **sin ningún YAML**, un programa con `PROC IMPORT`, `PROC SQL` (selección, filtro, `INNER`/`LEFT JOIN`) y `PROC EXPORT` en un Job de Talend con contextos, y los casos `L0` a `L2` del corpus pasan los anillos A y B.

**Architecture:** Se reutiliza el pipeline que ya existe: `frontend.analyze_program`, `compile.compile_file(analysis, program, ctx_base) -> Compiled` (con `Plan`, `Operator`, candidatos de componente por `rules/mapping/*.yaml`). Falta enriquecer los parámetros de los operadores (hoy son de nivel de guía: `read_file` solo trae la ruta y el `derive` de un `SELECT` trae `assignments: []`), y un emisor nuevo `Plan` a `Job` de `talend_item` que use las plantillas y `tmap()` que ya funcionan. Un intérprete de referencia ejecuta el `Plan` en Python (anillo B) y un validador estructural revisa el `Job` (anillo A).

**Tech Stack:** Python 3.12, `sqlglot` (ya aprobada), `typer`, `pyyaml`, `pytest`. Sin dependencias nuevas.

**Spec:** `docs/plan-reescritura/plan-migrador-general.md` (secciones 0.1b, 4, 5.1, 5.3, 6.1, 7; tareas MG-P1, MG-P2-01, MG-P5-01/02, MG-P8, MG-P9-04, MG-P10-01/02, MG-P11-01). Requiere el plan `2026-11-05-mg-01-fundacion-rapida.md` terminado para la Task 10.

## Global Constraints

- Archivos de 300 líneas como máximo; una responsabilidad por archivo. `src/sgm/cli.py` ya está cerca del límite: registrar el comando nuevo con dos líneas y poner el código en `cli_migrar.py`.
- Código e identificadores en inglés en archivos nuevos (los módulos de `talend_item/` usan español: al modificarlos, seguir su estilo); comentarios, docstrings y mensajes en español.
- Nada de nombres de scripts del cliente en `src/` ni `rules/` (`cod1`, `cod2`, `cars_poc`, `exogena`, `split2`, `split3`, `executeBulkload`, `waitForBulkLoads`, `bulkload_generic`); `tests/unit/test_no_script_specific_names.py` lo vigila.
- Ninguna equivalencia sin fuente. Lo que el SAS no demuestre (un tipo, una columna) queda como pendiente con código y motivo; nunca se inventa.
- **Semántica SAS obligatoria** (`tests/corpus/semantica/vectores.yaml`): el faltante numérico es menor que cualquier número; el texto en blanco es faltante y es igual a `''`; los blancos finales no cuentan al comparar texto.
- **Degradación elegante (instrucción del usuario):** `sgm migrar` no aborta nunca. Cada operador se traduce aislado: si lanza una excepción, se captura, se omite y se documenta como pendiente `P-FALLO-INTERNO` (con la línea del SAS; la causa técnica va a un archivo de registro, no a la pantalla). Lo que depende de configuración o credenciales ausentes se deja como parámetro de contexto vacío y se lista en `configuracion-pendiente.md`. El código de salida es 0 salvo uso incorrecto de la línea de comandos.
- Ninguna ruta, servidor, usuario ni contraseña dentro del Job: todo va a variables de contexto con grupos Default, DEV, QA y PROD con las mismas claves.
- `uv run pytest -q -n auto` y `uv run ruff check .` en verde antes de cada commit; `ruff` a 100 columnas. Sin `git push`; commit por tarea `hito N<letra>: ...` con la línea `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`; sin `--amend`; `git add` solo de los archivos propios.
- El `PROGRESS.md` se anexa con un script que añade bytes UTF-8.
- Pruebas de Talend Studio con `@pytest.mark.studio` (no corren por omisión).

## Review Focus

1. **Faltante en un filtro.** `WHERE saldo < 500` es verdadero con `saldo` faltante en SAS y no en Java. Test en Task 4 (`test_filtro_con_faltante_es_nulo_seguro`) y en Task 7 (el intérprete lo reproduce).
2. **Tabla sin esquema conocido.** Sin catálogo, ni muestra, ni uso que lo deduzca, el tipo es `String` con pendiente `P-TIPO-DESCONOCIDO`; no se inventa un tipo. Test en Task 2.
3. **Operador sin soporte.** Un `PROC REG` o una construcción que la rebanada no traduce no desaparece: aparece en `pendientes.md` con su línea. La propiedad de la Task 9 (`test_ningun_operador_se_pierde`) lo comprueba sobre todo el corpus `L0` a `L2`.
4. **Nombres repetidos.** Dos pasos que crean `WORK.tmp` en puntos distintos, o dos tablas con el mismo alias, no producen `UNIQUE_NAME` repetido. Test en Task 6.
5. **Rutas literales.** `DATAFILE='/data/x.csv'` no debe quedar en el `.item`; va a `context.ruta_<tabla>`. Test en Task 5.
6. **Un operador que lanza una excepción.** Un paso con sintaxis inesperada no tumba la migración: los demás operadores se traducen y el fallido va a `pendientes.md` como `P-FALLO-INTERNO`. Test en Task 4 (`test_un_operador_que_falla_no_detiene_a_los_demas`) y propiedad de robustez en Task 9.
7. **Entrada basura.** Archivo vacío, binario o SAS truncado: `sgm migrar` sale con 0, escribe `pendientes.md` explicándolo y no deja una carpeta a medias. Test en Task 8.
8. **Llaves con blancos o mayúsculas distintas.** `'CC '` y `'CC'` son la misma llave en SAS. Test en Task 7 sobre `l2_03` y en Task 4 (la unión recorta blancos finales).

---

### Task 1: Parámetros completos de `PROC IMPORT` y `PROC EXPORT`

**Files:**
- Modify: `src/sgm/ir/lower_procs.py:44-62` (ramas `import` y `export` de `lower_proc`)
- Modify (solo si el analizador no guarda la opción): `src/sgm/frontend/steps.py` (`_parse_proc`)
- Test: `tests/unit/test_ir_import_export_params.py`

**Interfaces:**
- Produces: el operador `read_file` lleva `params["dbms"]: str | None` (`"csv"`, `"dlm"`, `"xlsx"`, ...), `params["delimiter"]: str | None`, `params["getnames"]: bool`, `params["sheet"]: str | None`, `params["guessingrows"]: int | None`; el operador `write_file` lleva `params["dbms"]`, `params["delimiter"]`. Los valores salen del texto del paso; si no están, `None`/`False`.

- [ ] **Step 1: Write the failing test** `test_import_csv_con_getnames_y_delimitador`: analizar y compilar `PROC IMPORT DATAFILE='a.csv' OUT=WORK.X DBMS=CSV REPLACE; GETNAMES=YES; DELIMITER=';'; RUN;` (usar `analyze_program({"p.sas": texto})` y `compile_file(...)`) y comprobar que el operador `read_file` tiene `dbms == "csv"`, `getnames is True`, `delimiter == ";"`. Otros dos tests: `test_import_xlsx_con_hoja` (`DBMS=XLSX; SHEET="Hoja1";` da `sheet == "Hoja1"`) y `test_export_sin_delimitador_da_none`.
- [ ] **Step 2: Run** `uv run pytest tests/unit/test_ir_import_export_params.py -v`. Expected: FAIL con `KeyError: 'dbms'`.
- [ ] **Step 3: Implement** la lectura en `lower_proc`: tomar `dbms` de `step.options`, y `GETNAMES`, `DELIMITER`, `SHEET`, `GUESSINGROWS` de las sentencias del cuerpo (`step.clauses` o el texto crudo; si el analizador no las expone, añadirlas a `Proc.clauses` en `_parse_proc`). Conservar las claves actuales (`datafile`, `outputs`, `inputs`, `outfile`).
- [ ] **Step 4: Run** el test y `uv run pytest tests/unit -k "ir or lower" -q`. Expected: todo en verde (los pases existentes no dependen del conjunto exacto de claves; si alguno sí, actualizar su test con la clave nueva).
- [ ] **Step 5: Commit** `hito 104m: MG-P2-01 (1), PROC IMPORT y EXPORT con dbms, delimitador, hoja y cabecera en el IR`.

---

### Task 2: Esquemas de las tablas de entrada

**Files:**
- Create: `src/sgm/migrar/__init__.py`, `src/sgm/migrar/esquemas.py`
- Test: `tests/unit/test_migrar_esquemas.py`

**Interfaces:**
- Consumes: `sgm.ir.models.Plan`, `Column`; `sgm.catalog.schemas.load_schemas(directory: Path) -> dict[str, list[Column]]`.
- Produces: `@dataclass(frozen=True) class PendienteMigracion: codigo: str; mensaje: str; linea: int | None`; `def esquemas_de_entrada(plan: Plan, catalogo: dict[str, list[Column]], muestra: Path | None) -> tuple[dict[str, list[Column]], list[PendienteMigracion]]`. La clave es el nombre calificado en minúsculas (`work.clientes`). Orden de prioridad por tabla: catálogo, cabecera del CSV de `muestra` (archivo con el nombre base del `datafile`; columnas `String` con `source="file_header"`), columnas usadas aguas abajo (`source="derived"`, `String`). Toda columna sin tipo demostrado produce `PendienteMigracion("P-TIPO-DESCONOCIDO", ..., linea)` una vez por tabla.

- [ ] **Step 1: Write the failing tests.** `test_catalogo_tiene_prioridad`, `test_cabecera_de_la_muestra` (CSV `id;nombre` en `tmp_path` da dos columnas `String`), `test_columnas_usadas_aguas_abajo` (programa de `l2_01` sin catálogo ni muestra da `id_cliente`, `nombre`, `id_venta`, `monto`, ...), `test_sin_tipo_demostrado_publica_pendiente` (el pendiente `P-TIPO-DESCONOCIDO` existe y trae la línea del `PROC IMPORT`), `test_no_inventa_tipos` (ningún `Column.type` distinto de `None` si no vino del catálogo).
- [ ] **Step 2: Run** `uv run pytest tests/unit/test_migrar_esquemas.py -v`. Expected: FAIL (`ModuleNotFoundError`).
- [ ] **Step 3: Implement** `esquemas_de_entrada`. Las columnas usadas salen de las referencias de los operadores `map`/`filter` aguas abajo (`params["steps"]`, `params["condition"]`, expresiones); reutilizar `sgm.ir.sql_tree` para resolver alias a tabla.
- [ ] **Step 4: Run** el test. Expected: 5 passed.
- [ ] **Step 5: Commit** `hito 104m: MG-P1-02 (1), esquemas de entrada sin YAML con pendientes de tipo`.

---

### Task 3: Operador `map` con selección y llaves de unión

**Files:**
- Modify: `src/sgm/ir/lower_sql.py` y `src/sgm/ir/lower_sql_flow.py` (donde se crean los pasos `join` y `derive`)
- Test: `tests/unit/test_ir_map_columnas.py`

**Interfaces:**
- Produces: dentro de `params["steps"]`, el paso `join` lleva `keys: list[tuple[str, str]]` (columna de la principal, columna del lookup, ya resueltas a nombre de tabla, no de alias), `join_type` (`"inner"` o `"left"`) y `sources`; el paso `derive` lleva `assignments: list[{"target": str, "expression": str, "origin": "columna" | "expresion"}]`, uno por elemento del `SELECT`, en orden.

- [ ] **Step 1: Write the failing tests.** `test_select_de_columnas_da_asignaciones` (programa de `l2_01`: `assignments` igual a `[{"target":"id_venta","expression":"ventas.id_venta","origin":"columna"}, {"target":"nombre","expression":"clientes.nombre",...}, {"target":"monto",...}]`), `test_inner_join_tiene_llaves` (`keys == [("ventas.id_cliente","clientes.id_cliente")]`, `join_type == "inner"`), `test_left_join_conserva_el_tipo`, `test_join_con_dos_llaves` (caso `l2_03`).
- [ ] **Step 2: Run** `uv run pytest tests/unit/test_ir_map_columnas.py -v`. Expected: FAIL (`assignments` vacío).
- [ ] **Step 3: Implement** el llenado desde `SqlTree`/`SelectSpec` (`Item`, `JoinSpec`): `ir/sql_tree.py` ya extrae `Source`, `JoinSpec` e `Item`; hoy el lowering los descarta en el caso simple. No cambiar la firma de los pasos existentes: solo completar campos.
- [ ] **Step 4: Run** el test y `uv run pytest -q -n auto -k "ir or passes or lower or p10"`. Expected: verde; si un golden de guía cambia por las asignaciones nuevas, regenerar el golden y revisar el diff a mano.
- [ ] **Step 5: Commit** `hito 104m: MG-P5-01 (1), el operador map conserva selección y llaves de unión`.

---

### Task 4: Emisor `Plan` a `Job`

**Files:**
- Create: `src/sgm/talend_item/desde_plan.py` (orquestación), `src/sgm/talend_item/desde_plan_nodos.py` (nodos de lectura/escritura), `src/sgm/talend_item/desde_plan_map.py` (el `tMap`)
- Test: `tests/unit/test_desde_plan.py`

**Interfaces:**
- Consumes: `Plan`, `Operator` (`sgm.ir.models`); `esquemas_de_entrada` y `PendienteMigracion` (Task 2); `sgm.talend_item.plantillas.nodo_desde_plantilla(componente, unico, x, y, valores, tablas, columnas, ruta_java)`; `sgm.talend_item.tmap.tmap`, `EntradaMap`, `SalidaMap`; `sgm.talend_item.conexiones`; `sgm.expressions.expressions.translate(sas) -> Translation`.
- Produces: `@dataclass class ResultadoMigracion: jobs: list[Job]; pendientes: list[PendienteMigracion]; traza: dict[str, list[int]]` (UNIQUE_NAME a líneas de SAS) y `def plan_a_jobs(plan: Plan, esquemas: dict[str, list[Column]], ruta_java: str | None = None) -> ResultadoMigracion`. Un Job por cada `plan.jobs` (nombre `job_<programa>` en minúsculas y sin extensión). `read_file` con `dbms` csv/dlm a `tFileInputDelimited` (cabecera según `getnames`, separador según `delimiter` o `";"`... **no** inventar: sin delimitador conocido, pendiente `P-DELIMITADOR`); `xlsx` a `tFileInputExcel`; `write_file` a `tFileOutputDelimited` o `tFileOutputExcel`; `map` con paso `join` y `derive` a un `tMap` con entrada principal, lookup(s) con `union_interna` según `join_type` y una salida con las asignaciones; `filter` a la expresión de filtro de la salida del `tMap`.

- [ ] **Step 1: Write the failing tests** sobre el programa de `l2_01` (leído de `tests/corpus/L2/l2_01_inner_join_clientes_ventas/programa.sas`, compilado en el test):
  - `test_un_job_con_cuatro_nodos`: un `Job` con 2 `tFileInputDelimited`, 1 `tMap`, 1 `tFileOutputDelimited`.
  - `test_conexiones_principal_lookup_y_salida`: 3 conexiones de tipo `FLOW`, una de ellas lookup (`estilo == 8`).
  - `test_inner_join_activa_union_interna`: la entrada lookup del `tMap` tiene `union_interna is True`.
  - `test_left_join_no_activa_union_interna` con `l2_02`.
  - `test_filtro_con_faltante_es_nulo_seguro`: para `WHERE saldo < 500` (caso `L1`), el `expressionFilter` generado compila y contiene la comprobación de `null` antes de comparar y es verdadero con `saldo == null` (verificar compilando la expresión con `javac` sobre un molde mínimo si hay JDK; si no, comprobar la forma textual y marcar `skipif`).
  - `test_traza_apunta_a_las_lineas_del_sas`: `traza["tMap_1"]` contiene la línea del `CREATE TABLE`.
  - `test_un_operador_que_falla_no_detiene_a_los_demas`: con un `monkeypatch` que hace lanzar `RuntimeError` a la traducción del `tMap`, `plan_a_jobs` devuelve los nodos de lectura y escritura y un `PendienteMigracion("P-FALLO-INTERNO", ..., linea)`; no propaga la excepción.
- [ ] **Step 2: Run** `uv run pytest tests/unit/test_desde_plan.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement** `plan_a_jobs`. Reusar `valor_componente` de cada operador (candidato de la pasada 10) para elegir el componente, no volver a decidirlo; reusar la lógica de nulos de `talend_item/normalizacion.py` y `filtros_*.py` para los filtros (no escribir una segunda). Posiciones `x`/`y` por orden de flujo (rejilla de 192 px). Un operador cuyo `status` sea `hueco` o cuyo componente sea `none` no genera nodo: genera `PendienteMigracion("P-OPERADOR-SIN-SOPORTE", motivo, linea)`. Cada operador se traduce dentro de `try/except Exception`: el fallo se convierte en `P-FALLO-INTERNO` y el Job sigue con lo demás (un lookup sin su principal queda sin conexión y lo recoge el validador, que lo reporta como pendiente y no como error).
- [ ] **Step 4: Run** el test. Expected: 6 passed.
- [ ] **Step 5: Commit** `hito 104m: MG-P8/P9 (1), emisor Plan a Job para lectura, tMap y escritura`.

---

### Task 5: Contextos por entorno

**Files:**
- Create: `src/sgm/talend_item/desde_plan_contextos.py`
- Modify: `src/sgm/talend_item/desde_plan.py` (llamar a la función y sustituir rutas)
- Test: `tests/unit/test_desde_plan_contextos.py`

**Interfaces:**
- Produces: `def contextos_de_plan(plan: Plan) -> dict[str, list[ParametroContexto]]` con los grupos `Default`, `DEV`, `QA`, `PROD` y **las mismas claves** en todos; una variable `ruta_<tabla>` (tipo `id_String`) por cada ruta literal de `datafile`/`outfile`; el valor del literal va solo al grupo `Default` y los demás quedan vacíos; `def reemplazar_rutas(nodos, rutas: dict[str, str]) -> None` deja `context.ruta_<tabla>` en el parámetro `FILENAME` del nodo.

- [ ] **Step 1: Write the failing tests.** `test_cuatro_grupos_con_las_mismas_claves`, `test_ruta_literal_no_queda_en_el_item` (el `.item` serializado con `render_item` no contiene `entradas/clientes.csv` sino `context.ruta_clientes`), `test_el_marcador_de_ruta_con_puntos_suspensivos_se_conserva_como_valor_por_omision`, `test_sin_secretos` (ningún parámetro se llama `*pass*`/`*pwd*` con valor).
- [ ] **Step 2: Run** `uv run pytest tests/unit/test_desde_plan_contextos.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement.** El nombre de la variable sale del nombre de la tabla de WORK en minúsculas; si hay colisión, sufijo numérico estable.
- [ ] **Step 4: Run** el test. Expected: 4 passed.
- [ ] **Step 5: Commit** `hito 104m: MG-P8-04 (1), contextos Default DEV QA PROD con rutas fuera del Job`.

---

### Task 6: Validador estructural del Job (anillo A)

**Files:**
- Create: `src/sgm/talend_item/validador.py`
- Test: `tests/unit/test_validador_job.py`

**Interfaces:**
- Produces: `def validar_job(job: Job) -> list[str]` (lista de mensajes; vacía si el Job es correcto) que comprueba: `UNIQUE_NAME` únicos; cada `Conexion` apunta a nodos existentes; nombres de conexión únicos; para una conexión `FLOW`, las columnas de salida del origen igualan en nombre y orden las de entrada del destino salvo que el destino sea un `tMap`; todo nodo no inicial tiene al menos una conexión entrante; los cuatro grupos de contexto existen y tienen las mismas claves.

- [ ] **Step 1: Write the failing tests** con un `Job` correcto de referencia (`plan_a_jobs` sobre `l2_01`) y uno defectuoso por regla: `test_nombre_unico_repetido`, `test_conexion_a_nodo_inexistente`, `test_columnas_distintas_entre_origen_y_destino`, `test_nodo_huerfano`, `test_contextos_con_claves_distintas`, `test_el_job_de_l2_01_es_valido`.
- [ ] **Step 2: Run.** Expected: FAIL.
- [ ] **Step 3: Implement** `validar_job` (solo comprobaciones sobre el modelo, sin leer archivos).
- [ ] **Step 4: Run** el test. Expected: 6 passed.
- [ ] **Step 5: Commit** `hito 104m: MG-P10-02 (1), validador estructural de Jobs`.

---

### Task 7: Intérprete del plan (anillo B)

**Files:**
- Create: `src/sgm/migrar/interprete.py`
- Test: `tests/unit/test_migrar_interprete.py`, `tests/unit/test_migrar_corpus_anillo_b.py`

**Interfaces:**
- Produces: `def ejecutar_plan(plan: Plan, entradas: dict[str, list[dict[str, str | None]]]) -> dict[str, list[dict[str, str | None]]]`: ejecuta `read_file` (las filas ya vienen en `entradas` por nombre de tabla de WORK), `map` (pasos `join` inner/left, `filter` y `derive` de referencias de columna) y `write_file`, con la semántica SAS: comparación de texto sin blancos finales, texto en blanco es faltante, faltante numérico menor que cualquier número. Lo que no soporte lanza `NoSoportadoEnInterprete(kind)`.

- [ ] **Step 1: Write the failing tests.** Unitarios: `test_inner_join_descarta_sin_pareja`, `test_left_join_deja_faltantes`, `test_llave_con_blancos_finales_empareja`, `test_filtro_menor_que_con_faltante_es_verdadero`. De corpus (`test_migrar_corpus_anillo_b.py`): para cada caso de `tests/corpus/L0`, `L1` y `L2` con `estado` `traducible` o `revisado` cuyo plan solo use esos operadores, cargar las entradas CSV del caso (`tools.corpus_lib.caso.cargar_caso`), ejecutar el plan y comparar con `esperado/` usando `tools.corpus_lib.studio_filas.comparar_tablas` (tolerancia y orden del `caso.yaml`). Los que usan un operador aún no soportado se parametrizan como `xfail(strict=True, reason="NoSoportadoEnInterprete: <kind>")` para que, al implementar el operador, la prueba obligue a quitar el `xfail`.
- [ ] **Step 2: Run** `uv run pytest tests/unit/test_migrar_interprete.py tests/unit/test_migrar_corpus_anillo_b.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement** el intérprete. Para el texto, importar las funciones de comparación de `tools/corpus_lib/referencia_datastep.py` si encajan; si no, escribirlas en `src/sgm/migrar/semantica.py` (la fuente de cada una es `tests/corpus/semantica/vectores.yaml`, y se prueban contra él).
- [ ] **Step 4: Run** los dos archivos. Expected: pasan los casos soportados; los demás figuran como `xfail` con motivo. Anotar cuántos pasan en cada nivel.
- [ ] **Step 5: Commit** `hito 104m: MG-P10-01 (1), intérprete del plan con la semántica de SAS`.

---

### Task 8: El comando `sgm migrar`

**Files:**
- Create: `src/sgm/cli_migrar.py`, `src/sgm/migrar/informes.py`
- Modify: `src/sgm/cli.py` (dos líneas: importar y registrar `app.command("migrar")(migrar_command)`)
- Test: `tests/unit/test_cli_migrar.py`

**Interfaces:**
- Consumes: todo lo anterior y `BackendTalend` (plan MG-01).
- Produces: `def migrar_command(source: Path, out: Path = Path("out"), esquemas: Path | None = None, muestra: Path | None = None, backend: str = "archivos") -> None` y `def migrar(source: Path, out: Path, ...) -> ResultadoMigrar` (la función pura, que no lanza). Escribe en `<out>/<programa>/`: `process/*.item` y `*.properties`, `contextos/<grupo>.yaml` (uno por grupo, sin secretos), `pendientes.md` (código, motivo, línea de cada pendiente, orden estable), `configuracion-pendiente.md` (lista de lo que la persona debe completar: variable de contexto, para qué sirve, en qué Jobs se usa, grupos), `decisiones-tomadas.md` (qué eligió el migrador y cómo cambiarlo), `trace.json` y `migracion.log` (causas técnicas de cada `P-FALLO-INTERNO`). Salida determinista: dos corridas dan los mismos bytes. **Código de salida 0 siempre**, también con archivo ilegible; solo un uso incorrecto de la línea de comandos (por ejemplo, la ruta no existe) sale con el código 2 de `typer`.

- [ ] **Step 1: Write the failing tests** con `typer.testing.CliRunner`: `test_migrar_l2_01_escribe_todo` (los cinco tipos de archivo existen), `test_sin_yaml_no_falla` (el programa no tiene `decisiones/` y sale con 0), `test_determinismo` (dos corridas, mismos bytes), `test_pendientes_se_listan_con_codigo_y_linea` (programa con un `PROC REG` produce una fila en `pendientes.md` con `P-OPERADOR-SIN-SOPORTE` y su línea), `test_entrada_basura_sale_con_0` (parametrizado: archivo vacío, bytes aleatorios, SAS truncado a mitad de una sentencia, `%macro` sin `%mend`: salida 0, `pendientes.md` presente y explicativo, ninguna traza en la salida estándar), `test_configuracion_pendiente_lista_las_variables_vacias` (para `l2_01` aparecen `ruta_clientes` y `ruta_ventas`, con su descripción) y `test_un_fallo_interno_no_deja_carpeta_a_medias` (con una excepción forzada en el escritor de un Job, el resto de los archivos existen y el fallo figura en `migracion.log`).
- [ ] **Step 2: Run.** Expected: FAIL.
- [ ] **Step 3: Implement** el comando: `analyze_program` a `compile_file` a `esquemas_de_entrada` a `plan_a_jobs` a `validar_job` (un defecto del validador se convierte en pendiente `P-JOB-INVALIDO` y en una nota en `migracion.log`; el Job se escribe igual para que la persona lo vea) a escritura con el backend elegido.
- [ ] **Step 4: Run** el test y, a mano, `uv run sgm migrar tests/corpus/L2/l2_01_inner_join_clientes_ventas/programa.sas --out $TEMP/m1`. Expected: 5 passed; carpeta con los archivos.
- [ ] **Step 5: Commit** `hito 104m: MG-P11-01 (1), sgm migrar sin YAML para programas simples`.

---

### Task 9: Aceptación en el corpus: nada se pierde

**Files:**
- Create: `tests/unit/test_migrar_corpus_aceptacion.py`, `tests/corpus/migrar_pendientes.yaml`

**Interfaces:**
- Produces: la lista viva `migrar_pendientes.yaml` (caso a motivo) de los casos de `L0`, `L1` y `L2` que `sgm migrar` todavía no traduce por completo; la prueba exige que **solo** esos casos tengan pendientes y que la lista no tenga entradas de más.

- [ ] **Step 1: Write the failing tests.** `test_robustez_sobre_todo_el_repositorio`: para cada uno de los programas `.sas` de `tests/fixtures/sas/**` (190 en el repositorio; recolectar con `glob`), `migrar(...)` no lanza, termina en menos de 60 s y escribe `pendientes.md`; es la prueba de que nada falla. `test_ningun_operador_se_pierde[caso]`: para cada caso de `L0` a `L2`, cada operador del plan tiene un nodo en la traza o un pendiente con su línea. `test_solo_los_casos_listados_tienen_pendientes`: los casos sin entrada en `migrar_pendientes.yaml` salen con cero pendientes. `test_la_lista_no_tiene_casos_resueltos`: una entrada de la lista cuyo caso ya no tiene pendientes falla (obliga a quitarla). `test_todos_los_jobs_son_validos`: `validar_job` vacío en los 45 casos.
- [ ] **Step 2: Run** `uv run pytest tests/unit/test_migrar_corpus_aceptacion.py -q`. Expected: FAIL.
- [ ] **Step 3: Generar** la lista inicial ejecutando `sgm migrar` sobre los 45 casos y volcando los que tengan pendientes, con el código del primer pendiente como motivo. Revisar a mano que ningún motivo sea un error de programación.
- [ ] **Step 4: Run** el test. Expected: pasa. Anotar en `PROGRESS.md`: casos totalmente traducidos / 45 por nivel, y cuántos pasan el anillo B.
- [ ] **Step 5: Commit** `hito 104m: MG-P10 (2), aceptación del corpus L0 a L2 con lista viva de pendientes`.

---

### Task 10: Anillo C en lote con Studio (marca `studio`)

**Files:**
- Create: `tests/studio/test_migrar_lote.py` (marca `studio`)
- Modify: `PROGRESS.md`, `docs/plan-reescritura/plan-migrador-general.md`

**Interfaces:**
- Consumes: `compilar_en_lote` y `TalendCliBackend` (plan MG-01); `tools/corpus_studio.py validar` para ejecutar con datos.

- [ ] **Step 1: Write the test** `test_los_jobs_de_l0_a_l2_compilan_en_lote`: migra los casos totalmente traducidos, llama a `compilar_en_lote` una vez y exige `no_compilan == {}`. Marca `@pytest.mark.studio`; se salta con `pytest.skip` si `comprobar_salud(...)` da `Salud(False, ...)`.
- [ ] **Step 2: Run** `uv run pytest tests/studio -m studio -v` con Studio libre. Expected: pasa; anotar el tiempo del lote.
- [ ] **Step 3: Ejecutar con datos** tres casos representativos (`l0_01`, `l2_01`, `l2_02`) con `uv run python tools/corpus_studio.py validar <caso> --jobs <carpeta> --padre <job> --proyecto <PRJ_BANCOLOMBIA>` y pegar la salida literal en `PROGRESS.md`.
- [ ] **Step 4: Anexar** la entrada del hito con las cifras de las Tasks 7, 9 y 10, y actualizar el estado de las tareas MG-P1, MG-P2-01, MG-P5-01/02 y MG-P8 en el plan maestro.
- [ ] **Step 5: Commit** `hito 104m: MG-02 cerrado, primera rebanada vertical con Studio en lote`.

## Self-Review (hecha)

- **Cobertura del spec:** IR enriquecida (Tasks 1 y 3), esquemas sin YAML (Task 2), emisor general (Task 4), contextos (Task 5), validador A (Task 6), intérprete B (Task 7), comando único (Task 8), propiedad C2 (Task 9), lote C (Task 10). No cubre aún `DATA step`, agregados, macros, joblets ni el padre multi-Job: son los planes MG-03 en adelante.
- **Consistencia de tipos:** `PendienteMigracion` (Task 2) se usa en las Tasks 4, 8 y 9; `ResultadoMigracion` (Task 4) en 8 y 9; `esquemas_de_entrada` devuelve la misma tupla en 2 y 8.
- **Requisito de no fallar nunca (instrucción del usuario):** aislamiento por operador en la Task 4, salida 0 con entrada basura y `configuracion-pendiente.md` en la Task 8, prueba de robustez sobre los 190 programas del repositorio en la Task 9.
- **Riesgo declarado:** `translate()` (expresiones) fue escrito para la guía; su seguridad ante faltantes no está probada para este uso. La prueba `test_filtro_con_faltante_es_nulo_seguro` (Task 4) es la que lo decide: si falla, se reutiliza la generación de `talend_item/filtros_*.py`, que sí está validada en Studio, y se registra en `PROGRESS.md`.
- **Proporción:** diez tareas, solo firmas, pruebas y valores del corpus; ningún cuerpo de función.
