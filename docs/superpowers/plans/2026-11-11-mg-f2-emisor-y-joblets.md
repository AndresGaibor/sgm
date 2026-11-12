# MG-F2: Emisor de Talend (plantillas, joblets, contextos, conexiones y lienzo) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Que el emisor de `sgm` escriba cualquier Job que el plan lógico pida con una biblioteca completa de plantillas (los 54 nombres de componente que expande la lista de MG-P9-01, cada uno compilado y ejecutado con datos), con reutilización real (joblet validado en Studio 8.0.1 o su plan B con `tRunJob`), contextos `Default`/`DEV`/`QA`/`PROD` ejecutados, todos los tipos de conexión con prueba, lienzo sin superposición, propiedades y notas con la línea de SAS, y rutinas Java solo cuando una expresión inline no alcance. Cierra MG-P9 y el hito GM4.

**Architecture:** Cambios en `sgm-v2` (Python), casi todos en `src/sgm/talend_item/` y en `rules/talend/`; el acceso a Studio sigue pasando solo por `src/sgm/backend_talend/` (decisión del usuario del 5 de noviembre de 2026: `talend-mcp` se usa para crear, compilar, ejecutar y verificar, y el núcleo de `sgm` sigue escribiendo Jobs sin Studio abierto). Una plantilla es un JSON extraído de un nodo real guardado por Studio (`extraccion.plantilla_desde_nodo`); nunca se inventa un parámetro. Cada tarea que toca Studio tiene su parte local (prueba unitaria, sin Studio) y su parte de lote C (ejecución); si Studio no responde, la tarea cierra la parte local y queda **«lote C pendiente»** con su motivo, sin contarse como validada.

**Tech Stack:** Python 3.12, pytest, ruff, pyyaml; `uv run python -m pytest` y `uv run python -m sgm.cli` (en este Windows `uv run pytest` puede bloquearse por Control de aplicaciones).

**Spec:** `docs/plan-reescritura/plan-migrador-general.md` (MG-P9-01 a MG-P9-10, sección 2 con los hallazgos de Studio 8.0.1, sección 5 y sección 11b), `docs/superpowers/plans/2026-11-11-mg-a-studio-y-mcp-fiables.md` (tareas A-5 y A-6) y `docs/superpowers/plans/2026-11-11-ruta-al-100.md`.

**Horas del plan maestro cubiertas:** MG-P9 restante 73,5 h (108 h menos 34,5 h acreditadas): P9-01 20 h, P9-02 8 h, P9-03 14 h, P9-04 6,5 h, P9-05 5 h, P9-06 2 h, P9-07 3 h, P9-08 5 h, P9-10 6 h, P9-09 4 h (más un día-persona que no se cuenta como horas de agente).

**Estado de partida (medido al redactar, 11 de noviembre de 2026; la tarea F2-1 lo vuelve a medir):**

- `src/sgm/talend_item/plantillas/` tiene 26 JSON. De los 54 nombres que expande la lista de MG-P9-01 (7 de archivo, 32 de transformación y control, 12 de bases de datos Impala y PostgreSQL, y `tHashOutput`, `tHashInput`, `tBufferOutput`) **existen 25 y faltan 29**: `tFileInputPositional`, `tFileInputRegex`, `tFileOutputPositional`, `tFileOutputExcel`, `tFileList`, `tFileCopy`, `tFileDelete`, `tFilterRow`, `tJoin`, `tNormalize`, `tDenormalize`, `tConvertType`, `tIterateToFlow`, `tLoop`, `tStatCatcher`, `tContextLoad`, `tSleep`, `tWaitForFile`, `tSendMail`, `tSystem`, `tImpalaOutput`, `tImpalaClose`, `tImpalaCommit` y los seis de PostgreSQL (`Connection`, `Input`, `Output`, `Row`, `Close`, `Commit`). Hay un borrador de `tPostgresqlInput` en `tools/contenedores/talend_plantillas/` que no está en `src/`.
- `src/sgm/talend_item/conexiones.py` (69 líneas) escribe `OnSubjobOk`, `OnComponentOk`, `Iterate`, `Run if` y `Lookup`. `tests/unit/test_conexiones_tipos.py` trae pruebas por tipo (`SUBJOB_ERROR`, `REJECT`, `FILTER`, `ORDER`, `ITERATE`, `LOOKUP`, ...) **marcadas `xfail` estricto** porque no hay un Job guardado por Studio que sirva de referencia en `tests/fixtures/talend/` (solo `hijo_0.1.item`, con una fila `FLOW`).
- `src/sgm/talend_item/desde_plan_contextos.py` (108 líneas) crea los cuatro grupos con las mismas claves y `sgm migrar` escribe `contextos/<grupo>.yaml` (`src/sgm/cli_migrar.py`, `_contexto_yaml`), pero nada **lee** esos YAML al volver a emitir y ningún Job se ejecutó con `--context=DEV` ni `QA`. `tContextLoad` no tiene plantilla.
- `src/sgm/talend_item/disposicion.py` (87 líneas) pone cada nodo en la columna de su profundidad y en una fila por orden de aparición; no agrupa subjobs y el validador solo detecta dos nodos en el mismo punto exacto. `Nodo.comentario` y `Job.proposito`/`descripcion`/`autor` existen pero **no se escriben** (los comentarios del modelo dicen que falta el formato verificado).
- Joblets: el hito 194 escribió un joblet mínimo con el generador de `talend-mcp` y no pudo confirmar la carga (el hilo de la interfaz estaba ocupado); se adoptó provisionalmente el plan B (`tRunJob`). `plan_a_jobs` hoy **despliega en línea** las instancias de plantilla (`plan_desplegado`) hasta que haya Jobs hijos.
- Hallazgos de Studio 8.0.1 que este plan respeta (sección 2 del plan maestro): `tUnite` no compila (usar `APPEND` secuencial u otra unión); `tHashOutput` no se comparte entre Jobs; `DIE_ON_ERROR` vale `false` por omisión en los lectores; un `tAggregateRow` con dos salidas principales entrega vacío a la segunda; `tUniqRow` exige el esquema también en el bloque FLOW; `tFileInputExcel` exige `PASSWORD` no vacío en formato 2007; `tDie` en un Prejob necesita `EXIT_JVM=true`; Studio cachea Jobs por id (usar nombre nuevo por intento); `talend_job_execute` no carga contextos (exportar el Build Job y ejecutar el lanzador); un diálogo modal «Network Issue» bloquea el puente; un componente que no arranca su subjob no puede tener enlaces `OnSubjobOk` (hito 193); tras conectar un `SUBJOB_OK` Studio vuelve a propagar esquemas y puede borrar los valores de un `tFixedFlowInput`.

## Global Constraints

- Sin `git push` ni `--amend`. Un commit local por hito: `hito N m: <resumen>` (letra `m`, carril de Andres) con la línea final `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Antes de escribir, buscar el último `## Hito` de `PROGRESS.md` (al redactar este plan era el 198) y sumar uno; si otra sesión ya tomó el número, tomar el siguiente. No renumerar entradas publicadas. Cada commit actualiza `PROGRESS.md` (fecha, qué se hizo, pruebas, métricas, bloqueos, decisiones).
- No tocar `tools/ci.py`, `tools/validacion.py`, `tools/instalar_ganchos.py`, `README.md`, `.githooks/` ni `tests/unit/test_validacion.py` (son del Plan A y están sin commitear). No reutilizar los archivos de los planes `mg-b` ni `mg-k`.
- Nada de nombres de scripts de ejemplo (`cod1`, `cod2`, `cars_poc`, `exogena`, `split2`, `split3`, `executeBulkload`, `waitForBulkLoads`, `bulkload_generic`) en `src/` ni en `rules/`; lo vigila `tests/unit/test_no_script_specific_names.py`. Lo que dependa de un cliente va a `decisiones/<programa>.*.yaml`.
- Prohibido copiar `mcp/`, `contract/` ni `talend_adapter/` del repositorio viejo, agregar la dependencia `mcp` o crear `.mcp.json`. Studio se alcanza solo por `src/sgm/backend_talend/` y por los arneses de `tools/` ya existentes (`tools/validar_caso_studio.py <caso>`, `tools/corpus_studio.py lote|validar`).
- Si Studio no conecta (`uv run python -m sgm.cli studio salud`), **no reinstalar nada ni cambiar `talend-mcp`**: ver `docs/guia-validacion-studio.md`, sección 7. La parte de lote C queda «lote C pendiente» con su motivo y se encola con `tools/corpus_studio.py pendientes`; no cuenta como pasada.
- Ninguna plantilla guarda un secreto ni un dato de otro Job: contraseñas, usuarios, servidores, rutas y `UNIQUE_NAME` del Job de origen se neutralizan al extraer. Una contraseña se reemplaza por `'***'` o por vacío; nunca se copia.
- Si el SAS no demuestra un valor, una columna o una equivalencia: `Pendiente:` con motivo y código. Si no hay página de la guía, no hay equivalencia (aplica a cualquier regla nueva de expresiones, F2-17).
- No borrar ni debilitar pruebas. Un `xfail` solo se quita cuando su referencia de Studio existe en `tests/fixtures/talend/` y la prueba pasa comparando de verdad.
- Archivos de código de menos de 300 líneas. Ya pasan de 300 y **no se tocan en este plan**: `src/sgm/talend_item/desde_plan.py` (859) y `desde_plan_map.py` (815). Lo nuevo va en módulos nuevos que `plan_a_jobs` llama desde fuera.
- Código e identificadores en inglés cuando son nuevos y no extienden el modelo (el modelo de `talend_item` está en español y se conserva); comentarios, docstrings y mensajes en español.
- Después de cada tarea: `uv run python -m pytest tests/unit -q -p no:cacheprovider -k "<módulo de la tarea>"`, `uv run ruff check src tests tools` y, antes del commit, la suite de `tests/unit/test_talend_*.py`, `test_conexiones_tipos.py`, `test_disposicion.py`, `test_validador_job.py` y los `test_golden*.py` (las firmas de los Jobs ya validados en L0 a L3 no cambian).

## Review Focus

- Una plantilla instanciada con `nodo_desde_plantilla` solo cambia lo pedido: un parámetro que la plantilla no tiene es `KeyError`, y los sensibles (`PASS`, `PASSWORD`, usuario, servidor) salen vacíos. Test en F2-1 sobre las 54.
- «Compila y ejecuta con datos» significa: el Job de humo de F2-3 compila en Studio y su salida coincide con el esperado fila a fila; compilar sin ejecutar no cuenta. Excepción declarada y con motivo: `tSendMail` (sin servidor SMTP en el entorno) solo compila.
- Joblet o Job hijo: la decisión se toma una vez, por regla escrita (F2-9), y depende de un hecho medido en Studio (F2-8); no se emite un joblet que Studio no cargó.
- Los contextos de producción nunca llevan secreto: `contextos/<grupo>.yaml` no admite una variable cuyo nombre sea de credencial (`sin_secretos` de `src/sgm/backend_talend/comun.py` y `_SECRETO` de `cli_migrar.py`).
- Todo `xfail` de `test_conexiones_tipos.py` se resuelve con una referencia real de Studio, no con una referencia escrita a mano (F2-13 y F2-14).
- El lienzo no puede superponer ni nodos ni cajas de subjob ni notas (F2-15); el cálculo es determinista.
- Nada se «adopta» del MCP sin que Studio abra y guarde el resultado sin cambios (F2-18 y F2-19).

---

## Parte I. Biblioteca de plantillas (MG-P9-01 y MG-P9-02, 28 h)

### Task F2-1: Catálogo único de plantillas con metadatos y línea base medida

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\rules\talend\plantillas_prioritarias.yaml`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\rules\talend\plantillas_meta.yaml`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\talend_item\plantillas_catalogo.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\linea_base_plantillas.py`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_plantillas_catalogo.py`

**Interfaces:**
- Consumes (`src/sgm/talend_item/plantillas.py`):
  ```python
  def cargar(componente: str) -> dict
  def disponibles() -> list[str]
  ```
- Produces (`plantillas_catalogo.py`):
  ```python
  @dataclass(frozen=True)
  class MetaPlantilla:
      componente: str
      familia: str                         # "archivo", "transformacion", "control", "base_de_datos", "memoria"
      obligatorios: tuple[str, ...]        # nombres de parámetro que el emisor debe dar siempre
      neutralizados: tuple[str, ...]       # parámetros que la extracción deja en blanco o en valor neutro
      sensibles: tuple[str, ...]           # nunca con valor en el repositorio (PASS, PASSWORD, ...)
      estado: str                          # "con_plantilla" | "sin_plantilla" | "sin_pagina"

  def prioritarias() -> list[str]          # los 54 nombres de plantillas_prioritarias.yaml, en orden
  def meta(componente: str) -> MetaPlantilla   # KeyError si no está en plantillas_meta.yaml
  def estado_biblioteca() -> dict[str, list[str]]  # estado -> componentes
  ```
  `plantillas_prioritarias.yaml`: lista `componentes:` con `nombre` y `familia`. `plantillas_meta.yaml`: una entrada por componente con plantilla; `estado` se calcula, no se escribe.

- [ ] **Step 1: Write the failing test.** En `test_plantillas_catalogo.py`: `len(prioritarias()) == 54`; `"tFileInputPositional"` y `"tPostgresqlCommit"` están en la lista; `estado_biblioteca()["con_plantilla"]` tiene 25 nombres y `estado_biblioteca()["sin_plantilla"]` tiene 29 (`sorted` de los 29 listados arriba); `"PASSWORD"` está en `meta("tFileInputExcel").neutralizados` y no en `sensibles` (Studio 8.0.1 exige `PASSWORD` no vacío en formato 2007: la plantilla lo lleva con un valor neutro documentado, que no es una contraseña real); `meta("tImpalaConnection").sensibles` contiene `PASS` y `USER`; `meta("tFileInputDelimited").obligatorios` contiene `FILENAME`; para **cada** plantilla de `disponibles()`: todo parámetro de `meta(c).sensibles` existe en `cargar(c)["parametros"]` y su valor es `""` o `None`; `meta("tNoExiste")` lanza `KeyError`.
- [ ] **Step 2: Run test to verify it fails.** `uv run python -m pytest tests/unit/test_plantillas_catalogo.py -q -p no:cacheprovider`; esperado: no existe el módulo.
- [ ] **Step 3: Implement.** Escribir `plantillas_prioritarias.yaml` con los 54 nombres (7 de archivo, 32 de transformación y control, `tImpala` y `tPostgresql` por `Connection`, `Input`, `Output`, `Row`, `Close`, `Commit`, y `tHashOutput`, `tHashInput`, `tBufferOutput`). Verificar cada nombre con `grep -c '"name": "<nombre>"' rules/talend/components.json`; los de Impala no están en `components.json` (539 componentes) pero sí en `rules/talend/official-component-inventory.json`: se verifican ahí y, si alguno no aparece, queda `estado: sin_pagina` con motivo y no se genera (regla «sin página no hay equivalencia»). `plantillas_meta.yaml`: para las 25 existentes, derivar `sensibles` y `neutralizados` **leyendo el JSON de la plantilla** (los parámetros de campo `PASSWORD` y los llamados `PASS`, `USER`, `HOST`, `DBNAME`, `FILENAME`) y `obligatorios` de los parámetros con `REQUIRED` verdadero en `components.json`. `plantillas_catalogo.py` carga ambos YAML con `yaml.safe_load` y no pasa de 120 líneas.
- [ ] **Step 4: Run test to verify it passes** y `uv run python tools/linea_base_plantillas.py` (imprime una tabla por familia con `con_plantilla`/`sin_plantilla` y escribe `out/linea_base_plantillas.json`, no versionado). Pegar las cifras (25 de 54 al redactar) en `PROGRESS.md` como línea base de este plan. Luego `uv run ruff check src tests tools`.
- [ ] **Step 5: Commit.** `hito N m: catalogo unico de plantillas con metadatos y linea base`.

---

### Task F2-2: Generador automatizado de plantilla nueva (agregar un componente en menos de 30 minutos)

Hoy hay dos extractores casi iguales: `tools/extraer_plantilla.py` (escribe en `src/`) y `tools/contenedores/extraer_plantillas_talend.py` (escribe en `tools/contenedores/talend_plantillas/`, y vacía `PASS`). Este paso los reemplaza por uno solo que además neutraliza según el catálogo y deja la prueba escrita.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\talend_item\plantillas_nueva.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\nueva_plantilla.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\extraer_plantilla.py` (pasa a delegar en `crear_plantilla`)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\contenedores\extraer_plantillas_talend.py` (delega y se mantiene su nombre)
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_plantillas_nueva.py`

**Interfaces:**
- Consumes: `extraccion.plantilla_desde_nodo(nodo: Element) -> dict[str, object]`, `plantillas.DIRECTORIO: Path`, `plantillas_catalogo.meta(...)`.
- Produces (`plantillas_nueva.py`):
  ```python
  SENSIBLES_POR_OMISION = ("PASS", "PASSWORD", "USER", "HOST", "PORT", "DBNAME", "TOKEN")

  def crear_plantilla(
      item: Path,
      componente: str,
      destino: Path | None = None,
      sensibles: tuple[str, ...] = SENSIBLES_POR_OMISION,
  ) -> Path:
      """Extrae `componente` del primer nodo de `item`, vacía los sensibles, comprueba que
      `nodo_desde_plantilla` la instancia y escribe `<destino>/<componente>.json`.
      Si el componente no está en el `.item`: `LookupError` con el nombre."""

  def entrada_meta(componente: str, plantilla: dict) -> dict:
      """Entrada lista para `plantillas_meta.yaml`: obligatorios, neutralizados y sensibles
      calculados de la plantilla."""
  ```
  `tools/nueva_plantilla.py <archivo.item> <Componente>...` llama a ambas, imprime la entrada de `plantillas_meta.yaml` y la línea de `plantillas_humo.yaml` por completar. Tres pasos para el usuario: guardar el Job de origen en Studio, ejecutar el comando, completar el caso de humo (F2-3).

- [ ] **Step 1: Write the failing test.** Con un `.item` mínimo en `tmp_path` que traiga `tSortRow` y un nodo `tFileInputDelimited` con `FILENAME="C:/otro/job/x.csv"`, `PASS` con valor `"secreto"` y `UNIQUE_NAME` `tFileInputDelimited_7`: `crear_plantilla(item, "tFileInputDelimited", tmp_path)` escribe el JSON; en él `PASS` queda `""` y no aparece la cadena `secreto` ni `tFileInputDelimited_7` (se sustituyó por el marcador `UNICO`); `crear_plantilla(item, "tNoEsta", tmp_path)` lanza `LookupError`; el JSON generado se instancia con `nodo_desde_plantilla("tFileInputDelimited", "tFileInputDelimited_1")` (con `plantillas.DIRECTORIO` apuntado a `tmp_path` por `monkeypatch`) sin error.
- [ ] **Step 2: Run test to verify it fails.** `uv run python -m pytest tests/unit/test_plantillas_nueva.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement** `crear_plantilla` y `entrada_meta` reutilizando `plantilla_desde_nodo` (sin copiar su lógica) y `tools/nueva_plantilla.py` con `argparse` (`item`, `componentes...`, `--destino`). Hacer que los dos extractores viejos llamen a `crear_plantilla`; su `main` y sus mensajes no cambian (`tests/unit/test_talend_plantillas.py` y `test_desplegar_plantillas.py` deben seguir en verde).
- [ ] **Step 4: Run** `uv run python -m pytest tests/unit/test_plantillas_nueva.py tests/unit/test_talend_plantillas.py tests/unit/test_talend_plantillas_extra.py -q -p no:cacheprovider` y `uv run ruff check src tests tools`. Documentar en `docs/guia-validacion-studio.md` (sección nueva «Agregar una plantilla de componente», 10 líneas: los tres pasos y el criterio «el componente aparece en `plantillas_meta.yaml` y en `plantillas_humo.yaml`»).
- [ ] **Step 5: Commit.** `hito N m: generador unico de plantillas con neutralizacion por catalogo`.

---

### Task F2-3: Arnés de humo por plantilla (compila y ejecuta con datos)

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\rules\talend\plantillas_humo.yaml`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\talend_item\plantillas_humo.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\validar_plantilla_studio.py`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_plantillas_humo.py`

**Interfaces:**
- Consumes: `plantillas.nodo_desde_plantilla(componente, unico, x=0, y=0, valores=None, tablas=None, columnas=None, ruta_java=None) -> Nodo`; `componentes.fixed_flow_input(...)` y `componentes.log_row(...)` (`src/sgm/talend_item/componentes.py`); `item.render_item(job: Job) -> str`; `BackendTalend.escribir/refrescar/compilar_lote/verificar` (`src/sgm/backend_talend/base.py`); el formato de un caso del corpus (`tests/corpus/L0/l0_01_where_sentencia/`: `caso.yaml` con `nivel`, `construcciones`, `capa`, `tolerancia`, `orden_relevante`, `estado`, `salidas`, `razonamiento`, `revisor`; carpetas `entradas/` y `esperado/`) y `tools/corpus_studio.py validar <caso> --jobs ... --padre ... --corpus ...`.
- Produces (`plantillas_humo.py`):
  ```python
  @dataclass(frozen=True)
  class CasoHumo:
      componente: str
      forma: str                      # "transformacion" | "lector" | "escritor" | "control" | "base_de_datos"
      columnas: tuple[Columna, ...]
      filas: tuple[tuple[str, ...], ...]       # datos de entrada
      esperado: tuple[tuple[str, ...], ...]    # salida esperada, fila a fila
      valores: dict[str, str]                  # parámetros de la plantilla
      tablas: dict[str, tuple[tuple[str, str], ...]]
      solo_compila: str = ""                   # motivo; vacío si ejecuta

  def casos_humo() -> dict[str, CasoHumo]       # lee rules/talend/plantillas_humo.yaml
  def job_de_humo(caso: CasoHumo, nombre: str) -> Job
  def caso_de_corpus(caso: CasoHumo, carpeta: Path) -> Path   # escribe caso.yaml, entradas/, esperado/
  ```
  `job_de_humo` arma, según `forma`: `fixed_flow_input -> componente -> tLogRow` (transformacion), `componente (lee entradas/x.csv) -> tLogRow` (lector), `fixed_flow_input -> componente (escribe salida/x.csv)` (escritor), un Job de un subjob con el componente de control y un `tLogRow` que imprime la marca (control), y `tFixedFlowInput -> componente` contra el contenedor de `tools/contenedores/postgres` o `impala` (base_de_datos).

- [ ] **Step 1: Write the failing test.** `plantillas_humo.yaml` con las 25 plantillas que ya existen que admiten humo directo; con `tSortRow` (entrada `("2","b"),("1","a")`, criterio por `id` ascendente) `job_de_humo(casos_humo()["tSortRow"], "humo_tSortRow")` devuelve un Job con 3 nodos (`tFixedFlowInput`, `tSortRow`, `tLogRow`), 2 conexiones `FLOW`, `validar_job(job) == []` y `render_item` es XML que `ET.fromstring` lee; `caso_de_corpus` escribe `entradas/`, `esperado/` con `1,a` y `2,b` (esperado fila a fila, en ese orden) y un `caso.yaml` que `tools.corpus_lib.caso.cargar_caso` carga sin error; un componente sin caso en el YAML hace fallar `test_todo_componente_con_plantilla_tiene_humo` (el test recorre `plantillas.disponibles()` y exige caso o `solo_compila` con motivo).
- [ ] **Step 2: Run test to verify it fails.**
- [ ] **Step 3: Implement** los tres módulos. `tools/validar_plantilla_studio.py <Componente>...` por cada componente: `job_de_humo`, `caso_de_corpus` en una carpeta temporal, `ArchivosBackend.escribir` + `refrescar` + `compilar_lote`, y luego `corpus_studio validar` (mismo camino que `tools/validar_caso_studio.py`). Sin Studio: imprime `lote C pendiente: <motivo de comprobar_salud>` y sale con 3, sin contar el componente como validado. No escribe nada dentro del repositorio.
- [ ] **Step 4: Run** `uv run python -m pytest tests/unit/test_plantillas_humo.py -q -p no:cacheprovider`, `uv run ruff check src tests tools`; si `uv run python -m sgm.cli studio salud` responde `ok`, `uv run python tools/validar_plantilla_studio.py tSortRow tUniqRow tAggregateRow tReplicate tFlowToIterate tJavaRow` y pegar el resultado literal en `PROGRESS.md`; si no responde, anotar «lote C pendiente» con el estado de salud.
- [ ] **Step 5: Commit.** `hito N m: arnes de humo por plantilla con caso de corpus generado`.

---
### Task F2-4: Lote de plantillas de archivos (7)

`tFileInputPositional`, `tFileInputRegex`, `tFileOutputPositional`, `tFileOutputExcel`, `tFileList`, `tFileCopy`, `tFileDelete`.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\talend_item\plantillas\<Componente>.json` (siete, uno por componente; salen del generador de F2-2)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\rules\talend\plantillas_meta.yaml`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\rules\talend\plantillas_humo.yaml`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_plantillas_lote_archivos.py`

**Interfaces:**
- Consumes: `crear_plantilla(item: Path, componente: str, destino: Path | None = None, sensibles: tuple[str, ...] = SENSIBLES_POR_OMISION) -> Path` (F2-2); `casos_humo() -> dict[str, CasoHumo]` y `job_de_humo(caso: CasoHumo, nombre: str) -> Job` (F2-3); `nodo_desde_plantilla(...)`.
- Produces: siete plantillas con entrada en `plantillas_meta.yaml` (`estado` calculado `con_plantilla`) y siete casos de humo. Datos concretos (los nombres de `valores` y `tablas` se toman del JSON extraído; `nodo_desde_plantilla` lanza `KeyError` si un nombre no existe):
  - `tFileInputPositional`: lector; `entradas/ancho.txt` con las líneas `001Ana  ` y `002Luis `, anchos `3,5`, esperado `001|Ana` y `002|Luis` (si la plantilla no recorta el relleno, el esperado conserva los espacios y se escribe así).
  - `tFileInputRegex`: lector; líneas `a=1;b=x` y `a=2;b=y`, expresión `a=(\d+);b=(\w)`, esperado `1|x` y `2|y`.
  - `tFileOutputPositional`: escritor; filas `("1","Ana")` y `("2","Luis")`, formatos `3` y `5`; el archivo `salida/ancho.txt` es el esperado.
  - `tFileOutputExcel`: escritor; hoja `Hoja1`, formato `.xlsx`, dos filas; el esperado se compara releyendo con `tFileInputExcel` en un segundo subjob (el hallazgo de `PASSWORD` no vacío en 2007 aplica a esa lectura y ya está en su plantilla).
  - `tFileList`: control; `entradas/` con `a.csv` y `b.csv`, máscara `*.csv`, conexión `Iterate` a un `tLogRow` que imprime `((String)globalMap.get("tFileList_1_CURRENT_FILE"))`; esperado `a.csv` y `b.csv`.
  - `tFileCopy`: control; copia `entradas/a.csv` a `salida/a.csv`; esperado el contenido del archivo copiado.
  - `tFileDelete`: control; `tFileCopy` a `salida/x.csv`, `OnSubjobOk`, `tFileDelete` de `salida/x.csv`, `OnSubjobOk`, `tFileExist` que imprime `existe=false`.

- [ ] **Step 1: Write the failing test.** Para cada uno de los siete: `nodo_desde_plantilla(c, f"{c}_1")` instancia; el JSON no contiene la cadena `C:/` ni el `UNIQUE_NAME` de otro Job; `meta(c)` existe; `casos_humo()[c]` existe; `job_de_humo(...)` pasa `validar_job(job) == []` y se escribe como XML válido. Para `tFileList` y `tFileDelete`, las conexiones del humo se comprueban por tipo (`ITERATE` y `SUBJOB_OK`).
- [ ] **Step 2: Run test to verify it fails.** `uv run python -m pytest tests/unit/test_plantillas_lote_archivos.py -q -p no:cacheprovider`; esperado: no hay plantilla.
- [ ] **Step 3: Obtener los siete nodos reales.** Armar el Job de origen con `talend_components_generate_template` del MCP o a mano en Studio, guardarlo desde Studio y ejecutar `uv run python tools/nueva_plantilla.py <Job>.item tFileInputPositional tFileInputRegex tFileOutputPositional tFileOutputExcel tFileList tFileCopy tFileDelete`. Revisar cada JSON (sin contraseñas, sin rutas del equipo); completar `plantillas_meta.yaml` y `plantillas_humo.yaml` con las entradas que imprime el generador y los datos de arriba.
- [ ] **Step 4: Run test to verify it passes**, `uv run ruff check src tests tools` y, con Studio disponible, `uv run python tools/validar_plantilla_studio.py tFileInputPositional tFileInputRegex tFileOutputPositional tFileOutputExcel tFileList tFileCopy tFileDelete`. Anotar en `PROGRESS.md` el resultado literal por componente; el que no compile o no ejecute con datos queda `pendiente` con el error y no se cuenta. Sin Studio: «lote C pendiente» con el estado de salud.
- [ ] **Step 5: Commit.** `hito N m: siete plantillas de archivos con prueba de humo` (más la línea `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`).

---

### Task F2-5: Lote de plantillas de transformación (7)

`tFilterRow`, `tJoin`, `tNormalize`, `tDenormalize`, `tConvertType`, `tIterateToFlow`, `tLoop`.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\talend_item\plantillas\<Componente>.json` (siete)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\rules\talend\plantillas_meta.yaml`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\rules\talend\plantillas_humo.yaml`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_plantillas_lote_transformacion.py`

**Interfaces:**
- Consumes: igual que F2-4; `conexiones.lookup(origen: str, destino: str, nombre: str = "row2") -> Conexion` para `tJoin`.
- Produces: siete plantillas, meta y humo. Casos con datos concretos:
  - `tFilterRow`: filas `("1","50")` y `("2","900")`, condición `saldo >= 100`; salida principal `2|900`. Los conectores `FILTER` y `REJECT` se prueban en F2-14; aquí solo la salida principal.
  - `tJoin`: principal `(1,Ana)` y `(2,Luis)`; búsqueda `(1,Quito)`; unión interna por `id`; esperado `1|Ana|Quito`; la búsqueda entra por `lookup(...)`.
  - `tNormalize`: fila `("1","a;b")`, separador `;`, esperado `1|a` y `1|b`.
  - `tDenormalize`: filas `("1","a")` y `("1","b")`, separador `;`, esperado `1|a;b`.
  - `tConvertType`: columna `"12"` de String a Integer, esperado `12`; con `"x"` el rechazo imprime el motivo (se anota en meta qué parámetro de la plantilla controla el rechazo).
  - `tIterateToFlow`: `tFileList` por `Iterate` a `tIterateToFlow` con el valor `CURRENT_FILE`; esperado una fila por archivo.
  - `tLoop`: `FOR` de 1 a 3 con paso 1, `Iterate` a un `tLogRow` que imprime `((Integer)globalMap.get("tLoop_1_CURRENT_VALUE"))`; esperado `1`, `2`, `3`.

- [ ] **Step 1: Write the failing test.** Mismas comprobaciones que F2-4 Step 1 para los siete; además, `tFilterRow` instanciada con `tablas={"CONDITIONS": (("INPUT_COLUMN", "saldo"), ("FUNCTION", ">="), ("RVALUE", "100"))}` conserva el orden de las celdas (los `elementRef` se confirman contra el JSON extraído y el test usa los que salgan).
- [ ] **Step 2: Run test to verify it fails.** `uv run python -m pytest tests/unit/test_plantillas_lote_transformacion.py -q -p no:cacheprovider`.
- [ ] **Step 3: Obtener los siete nodos reales** como en F2-4 Step 3 (`tools/nueva_plantilla.py` con los siete nombres); completar meta y humo. Respetar el hallazgo de que un `tAggregateRow` con dos salidas principales entrega vacío a la segunda: ningún caso de este lote usa dos salidas principales de un mismo componente.
- [ ] **Step 4: Run test to verify it passes**, ruff y, con Studio, `uv run python tools/validar_plantilla_studio.py tFilterRow tJoin tNormalize tDenormalize tConvertType tIterateToFlow tLoop`. Resultado literal en `PROGRESS.md`; sin Studio: «lote C pendiente».
- [ ] **Step 5: Commit.** `hito N m: siete plantillas de transformacion con prueba de humo` (con la línea de coautoría).

---

### Task F2-6: Lote de plantillas de control y utilidades (6)

`tStatCatcher`, `tContextLoad`, `tSleep`, `tWaitForFile`, `tSendMail`, `tSystem`.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\talend_item\plantillas\<Componente>.json` (seis)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\rules\talend\plantillas_meta.yaml`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\rules\talend\plantillas_humo.yaml`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_plantillas_lote_control.py`

**Interfaces:**
- Consumes: igual que F2-4.
- Produces: seis plantillas, meta y humo:
  - `tStatCatcher`: recoge las estadísticas de un `tLogRow` y las imprime; esperado una fila con el nombre del componente (se compara solo esa columna; las marcas de tiempo se normalizan y la regla queda en `CasoHumo`).
  - `tContextLoad`: lee `entradas/ctx.csv` con la fila `("clave_a","uno")` y carga `clave_a` en la variable de contexto `clave_a` ya declarada; un `tLogRow` posterior imprime `context.clave_a`; esperado `uno`. La usa F2-11.
  - `tSleep`: pausa de `1` segundo y un `tLogRow` posterior imprime `listo`; esperado `listo` (la pausa no se mide).
  - `tWaitForFile`: espera `entradas/a.csv` (existe), máximo `5` segundos; esperado `listo`.
  - `tSendMail`: **solo compila** (`solo_compila: "sin servidor SMTP en el entorno; ejecutarlo requeriría un servidor real"`); servidor, usuario y contraseña quedan vacíos y son sensibles.
  - `tSystem`: ejecuta `cmd /c echo hola` y un `tLogRow` imprime `((String)globalMap.get("tSystem_1_OUTPUT"))`; esperado `hola`.

- [ ] **Step 1: Write the failing test.** Mismas comprobaciones de F2-4 Step 1; `meta("tSendMail").sensibles` contiene `PASS` y el parámetro del servidor (nombre real tomado del JSON extraído), `casos_humo()["tSendMail"].solo_compila` no está vacío y `meta("tContextLoad").obligatorios` contiene el parámetro del archivo de entrada.
- [ ] **Step 2: Run test to verify it fails.** `uv run python -m pytest tests/unit/test_plantillas_lote_control.py -q -p no:cacheprovider`.
- [ ] **Step 3: Obtener los seis nodos reales** con `tools/nueva_plantilla.py`; revisar a mano `tSendMail` y `tSystem` (no dejar comandos ni correos del Job de origen).
- [ ] **Step 4: Run test to verify it passes**, ruff y, con Studio, `uv run python tools/validar_plantilla_studio.py tStatCatcher tContextLoad tSleep tWaitForFile tSystem` (`tSendMail` se compila con `tools/corpus_studio.py lote`). Resultado literal en `PROGRESS.md`; sin Studio: «lote C pendiente».
- [ ] **Step 5: Commit.** `hito N m: seis plantillas de control y utilidades con prueba de humo` (con la línea de coautoría).

---

### Task F2-7: Lote de plantillas de bases de datos (PostgreSQL e Impala, 9)

`tPostgresqlConnection`, `tPostgresqlInput`, `tPostgresqlOutput`, `tPostgresqlRow`, `tPostgresqlClose`, `tPostgresqlCommit`, `tImpalaOutput`, `tImpalaClose`, `tImpalaCommit`. (`tImpalaConnection`, `tImpalaInput` y `tImpalaRow` ya tienen plantilla.)

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\talend_item\plantillas\<Componente>.json` (nueve; `tPostgresqlInput` parte del borrador `tools/contenedores/talend_plantillas/tPostgresqlInput.json`, que se revisa con `tools/nueva_plantilla.py` y se mueve a esta carpeta con `git mv`)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\rules\talend\plantillas_meta.yaml`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\rules\talend\plantillas_humo.yaml`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_plantillas_lote_bases.py`

**Interfaces:**
- Consumes: igual que F2-4; el contenedor de PostgreSQL de `tools/contenedores/postgres` y el de Impala de `tools/contenedores/impala` (se levantan como documenta cada carpeta).
- Produces: nueve plantillas con `sensibles` `HOST`, `PORT`, `DBNAME`, `USER` y `PASS` (los nombres reales salen del JSON extraído), siempre vacíos en el JSON. Los valores del contenedor del equipo viajan como variables de contexto del Job de humo (`db_host`, `db_puerto`, `db_nombre`, `db_usuario`), nunca en el JSON ni en `plantillas_humo.yaml`. Caso PostgreSQL: subjob con `tPostgresqlConnection`, `OnSubjobOk` a `tFixedFlowInput -> tPostgresqlOutput` (inserta `(1,"Ana")` y `(2,"Luis")` en `humo_plantilla`, creada con `CREATE_IF_NOT_EXISTS`), `OnSubjobOk` a `tPostgresqlInput` (`select id, nombre from humo_plantilla order by id`; esperado `1|Ana` y `2|Luis`), `OnSubjobOk` a `tPostgresqlRow` (`drop table humo_plantilla`), y al final `tPostgresqlCommit` y `tPostgresqlClose`. Impala: los tres componentes nuevos se comprueban igual contra el contenedor de Impala; si alguno no está en `rules/talend/official-component-inventory.json` (F2-1 lo dejó escrito), queda `sin_pagina` y se emite `Pendiente:` en vez de plantilla.

- [ ] **Step 1: Write the failing test.** Mismas comprobaciones de F2-4 Step 1 para los nueve (menos los `sin_pagina`); el JSON de cada uno tiene `""` en `HOST`, `USER` y `PASS`; ninguna cadena `localhost`, `5432` ni un usuario aparece en `plantillas_humo.yaml`; el humo de PostgreSQL pasa `validar_job(job) == []` y sus conexiones `SUBJOB_OK` salen de nodos de arranque de subjob (hito 193: un componente intermedio no puede tener enlaces de subjob).
- [ ] **Step 2: Run test to verify it fails.** `uv run python -m pytest tests/unit/test_plantillas_lote_bases.py -q -p no:cacheprovider`.
- [ ] **Step 3: Obtener los nodos reales** con `tools/nueva_plantilla.py` desde un Job de origen guardado por Studio y mover el borrador de `tPostgresqlInput` revisándolo. Completar meta y humo.
- [ ] **Step 4: Run test to verify it passes**, ruff y, con Studio y el contenedor levantado, `uv run python tools/validar_plantilla_studio.py tPostgresqlConnection tPostgresqlInput tPostgresqlOutput tPostgresqlRow tPostgresqlClose tPostgresqlCommit tImpalaOutput tImpalaClose tImpalaCommit`. Con esto la biblioteca queda en 54 de 54 (menos los `sin_pagina` con motivo): volver a correr `uv run python tools/linea_base_plantillas.py` y pegar la tabla final en `PROGRESS.md`. Sin Studio o sin contenedor: «lote C pendiente».
- [ ] **Step 5: Commit.** `hito N m: nueve plantillas de bases de datos y biblioteca completa` (con la línea de coautoría).

---

## Parte II. Joblets y reutilización (MG-P9-03, 14 h)

### Task F2-8: Escritor de joblets y spike de carga en Studio 8.0.1

Depende de `talend-mcp`, tarea A-6 del Plan A. El hito 194 escribió un joblet mínimo con el generador de `talend-mcp` (`JL_prueba_mcp`) y no pudo confirmar la carga porque el hilo de la interfaz de Studio estaba ocupado; `docs/studio-internals/11-joblets-desde-archivo.md` de `talend-mcp` dice qué falta. Esta tarea escribe el emisor propio de joblets y repite el spike con el hilo libre.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\talend_item\joblets.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\fixtures\talend\joblet_minimo.item` (el que produce Studio o el generador de `talend-mcp`; se copia, no se escribe a mano)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\fixtures\talend\joblet_minimo.properties`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\talend_item\modelo.py` (campo `joblet: bool = False` en `Job`)
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_joblets.py`

**Interfaces:**
- Consumes: `Job`, `Nodo`, `Conexion`, `ParametroContexto` (`modelo.py`); `render_item(job: Job) -> str` y `render_properties(job: Job, autor: str = "_0KqD4YE9EfGMqbenmdd8gw", fecha: str = "") -> str` (`item.py`); `nodo_desde_plantilla(...)` para `tJobletInput` y `tJobletOutput` (sus plantillas se generan con `tools/nueva_plantilla.py` desde el joblet que Studio guardó, en el paso 4).
- Produces (`joblets.py`):
  ```python
  CARPETA_JOBLETS = "joblets"          # carpeta del proyecto donde Studio guarda los joblets
  TIPO_PROPERTIES = "TalendProperties:JobletProcessItem"

  def joblet_desde_nodos(
      nombre: str,
      entrada: tuple[Columna, ...],
      salida: tuple[Columna, ...],
      nucleo: list[Nodo],
      conexiones: list[Conexion],
      parametros: list[ParametroContexto],
  ) -> Job:
      """Job con `joblet=True`: `tJobletInput` -> núcleo -> `tJobletOutput`, con sus parámetros."""

  def render_joblet_item(job: Job) -> str
  def render_joblet_properties(job: Job, autor: str = "_0KqD4YE9EfGMqbenmdd8gw", fecha: str = "") -> str

  def nodo_joblet(unico: str, joblet: str, valores: dict[str, str]) -> Nodo:
      """Nodo que usa el joblet `joblet` desde un Job, con el valor de cada parámetro de contexto."""
  ```

- [ ] **Step 1: Spike de carga (lote C, manual y breve).** Con `uv run python -m sgm.cli studio salud` en `ok`: copiar el joblet mínimo del generador de `talend-mcp` a `<proyecto>/joblets/`, refrescar con `uv run python -m sgm.cli studio compilar` (que llama a `refrescar`) y comprobar que Studio lo lista y que un Job nuevo puede usarlo. Anotar el resultado literal («cargable desde archivo: sí/no», ruta y versión del `.item`) en `PROGRESS.md` y en `docs/guia-validacion-studio.md` (sección nueva «Joblets»). Copiar a `tests/fixtures/talend/` el `.item` y el `.properties` que Studio acepte. **Si Studio no responde:** el paso queda «lote C pendiente», se siguen los pasos 2 a 5 con el fixture de `talend-mcp` y la decisión de F2-9 usa el plan B.
- [ ] **Step 2: Write the failing test.** `joblet_desde_nodos("JL_prueba", entrada=(Columna("id", "id_Integer"),), salida=(Columna("id", "id_Integer"),), nucleo=[], conexiones=[], parametros=[ParametroContexto("umbral", "id_Integer", "10")])` produce un Job con `joblet=True`, nodos `tJobletInput` y `tJobletOutput` unidos por una conexión `FLOW` `row1`; `render_joblet_properties` contiene `TalendProperties:JobletProcessItem` y **no** `TalendProperties:ProcessItem`; `render_joblet_item` incluye `<contextParameter` con `name="umbral"`; `nodo_joblet("JL_prueba_1", "JL_prueba", {"umbral": "20"})` lleva el valor `20` en el parámetro de contexto del nodo. Si el fixture existe, la estructura (elementos y atributos, ignorando ids y fechas) coincide con él.
- [ ] **Step 3: Run test to verify it fails.** `uv run python -m pytest tests/unit/test_joblets.py -q -p no:cacheprovider`.
- [ ] **Step 4: Implement** `joblets.py` (menos de 200 líneas) y el campo `joblet` de `Job` (por omisión `False`; ningún Job existente cambia). Generar las plantillas de `tJobletInput` y `tJobletOutput` con `tools/nueva_plantilla.py` desde el joblet que guardó Studio. Run: `uv run python -m pytest tests/unit/test_joblets.py tests/unit/test_talend_item.py tests/unit/test_validador_job.py -q -p no:cacheprovider` y `uv run ruff check src tests tools`.
- [ ] **Step 5: Commit.** `hito N m: escritor de joblets y resultado del spike de carga` (con la línea de coautoría).

---

### Task F2-9: Plan B con Job hijo `tRunJob` y la regla de cuándo cada uno

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\talend_item\reutilizacion.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\rules\talend\capacidades_studio.yaml`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\docs\reutilizacion-joblet-o-job-hijo.md`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_reutilizacion.py`

**Interfaces:**
- Consumes: `nodo_desde_plantilla("tRunJob", unico, valores=..., tablas=...) -> Nodo` (la plantilla `tRunJob.json` existe); `conexiones.al_terminar_subjob(origen: str, destino: str, n: int = 1) -> Conexion`; `joblets.joblet_desde_nodos(...)` y `joblets.nodo_joblet(...)` (F2-8).
- Produces (`reutilizacion.py`):
  ```python
  @dataclass(frozen=True)
  class BloqueReutilizable:
      nombre: str
      entradas_de_fila: int            # conectores de fila que entran al bloque
      salidas_de_fila: int
      tiene_subjobs_propios: bool      # contiene OnSubjobOk, prejob o postjob internos
      necesita_contexto_propio: bool   # lee o cambia variables de contexto que el padre no comparte
      se_ejecuta_solo: bool            # debe poder correrse como Job independiente

  def decidir(bloque: BloqueReutilizable, capacidades: dict[str, bool]) -> str:
      """`"joblet"` o `"job_hijo"`; nunca otra cosa."""

  def nodo_job_hijo(unico: str, hijo: str, contexto_padre: dict[str, str]) -> Nodo:
      """`tRunJob` que llama al Job `hijo` pasando cada variable con `PARAM_VALUE`."""

  def capacidades() -> dict[str, bool]   # lee capacidades_studio.yaml: {"joblet_desde_archivo": bool}
  ```
  Regla (escrita en `docs/reutilizacion-joblet-o-job-hijo.md` y probada): es `"joblet"` solo si `capacidades["joblet_desde_archivo"]` es `True`, el bloque tiene al menos una entrada o una salida de fila, **no** tiene subjobs propios, **no** necesita contexto propio y **no** se ejecuta solo. En cualquier otro caso es `"job_hijo"`. Por omisión (`joblet_desde_archivo: false`, hasta que F2-8 Step 1 lo demuestre) todo es `"job_hijo"`.

- [ ] **Step 1: Write the failing test.** `decidir(BloqueReutilizable("normalizar", 1, 1, False, False, False), {"joblet_desde_archivo": True}) == "joblet"`; el mismo bloque con `{"joblet_desde_archivo": False}` es `"job_hijo"`; con `tiene_subjobs_propios=True`, `necesita_contexto_propio=True` o `se_ejecuta_solo=True` (cada uno por separado) es `"job_hijo"` aun con la capacidad en `True`; `nodo_job_hijo("tRunJob_1", "JH_normalizar", {"anio": "2026"})` conserva el orden de parámetros de la plantilla, lleva el nombre del Job en el parámetro del proceso y una fila de `PARAM_VALUE` con `anio` y `2026`; `capacidades()` devuelve `{"joblet_desde_archivo": False}` mientras el spike no lo cambie.
- [ ] **Step 2: Run test to verify it fails.** `uv run python -m pytest tests/unit/test_reutilizacion.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement** `reutilizacion.py` (menos de 150 líneas) y el YAML con un comentario por capacidad (quién la midió, en qué hito y con qué versión de Studio). Escribir `docs/reutilizacion-joblet-o-job-hijo.md` (una página: la regla, cuándo cada uno, el plan B y su límite: `tRunJob` arranca otro Job con su propio proceso y no comparte `tHashOutput`, hallazgo del plan maestro).
- [ ] **Step 4: Run** `uv run python -m pytest tests/unit/test_reutilizacion.py tests/unit/test_no_script_specific_names.py -q -p no:cacheprovider` y `uv run ruff check src tests tools`.
- [ ] **Step 5: Commit.** `hito N m: regla joblet o job hijo y emisor del plan B` (con la línea de coautoría).

---

### Task F2-10: Un bloque reutilizable usado en dos Jobs, compilado y ejecutado

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\talend_item\reutilizacion_jobs.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\validar_reutilizacion_studio.py`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_reutilizacion_jobs.py`

**Interfaces:**
- Consumes: `decidir(...)`, `nodo_job_hijo(...)`, `capacidades()` (F2-9); `joblet_desde_nodos(...)` y `nodo_joblet(...)` (F2-8); `job_de_humo` y `caso_de_corpus` de F2-3 como modelo del arnés.
- Produces (`reutilizacion_jobs.py`):
  ```python
  @dataclass(frozen=True)
  class PruebaReutilizacion:
      mecanismo: str                  # "joblet" | "job_hijo"
      jobs: tuple[Job, ...]           # el bloque (joblet o hijo) y los dos Jobs que lo usan
      esperados: dict[str, tuple[tuple[str, ...], ...]]   # Job -> filas esperadas

  def prueba_de_dos_jobs(mecanismo: str) -> PruebaReutilizacion
  ```
  El bloque filtra `saldo >= umbral` con un parámetro de contexto `umbral`; el Job A lo usa con `umbral=100` y el Job B con `umbral=500` sobre las filas `("1","50")`, `("2","300")`, `("3","900")`; esperado A: `2|300` y `3|900`; esperado B: `3|900`.

- [ ] **Step 1: Write the failing test.** `prueba_de_dos_jobs("job_hijo")` devuelve tres Jobs (hijo, A y B), `validar_job` de cada uno da `[]`, A y B contienen un nodo `tRunJob` con `PARAM_VALUE` distinto (`100` y `500`) y los esperados son los de arriba; `prueba_de_dos_jobs("joblet")` devuelve el joblet (`joblet=True`) y los dos Jobs con un nodo del joblet cada uno; un mecanismo distinto lanza `ValueError`.
- [ ] **Step 2: Run test to verify it fails.** `uv run python -m pytest tests/unit/test_reutilizacion_jobs.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement** el módulo y `tools/validar_reutilizacion_studio.py [--mecanismo joblet|job_hijo]` (por omisión el que dé `decidir` con `capacidades()`): escribe los Jobs con el backend, refresca, compila en lote y ejecuta A y B comparando con los esperados.
- [ ] **Step 4: Run** el test, ruff y, con Studio, `uv run python tools/validar_reutilizacion_studio.py`. Si F2-8 Step 1 demostró que el joblet carga, correr también `--mecanismo joblet` y, solo si pasa, cambiar `joblet_desde_archivo` a `true` en `capacidades_studio.yaml` en este mismo commit. Si el joblet no carga, el plan B (`job_hijo`) es el que debe pasar y basta para el criterio de MG-P9-03. Resultado literal en `PROGRESS.md`; sin Studio: «lote C pendiente».
- [ ] **Step 5: Commit.** `hito N m: bloque reutilizable usado en dos Jobs, compilado y ejecutado` (con la línea de coautoría).

---

## Parte III. Contextos por entorno (MG-P9-04, 6,5 h)

### Task F2-11: Valores por entorno desde `contextos/<grupo>.yaml` y `tContextLoad`

Hoy `sgm migrar` escribe `contextos/<grupo>.yaml` (`cli_migrar._contexto_yaml`) y el texto dice «editar estos valores y volver a importar el Job», pero ningún código **lee** esos archivos: el valor editado a mano no llega al `.item`. `src/sgm/cli_migrar.py` tiene 340 líneas: el primer paso lo parte sin cambiar comportamiento.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\cli_migrar_contextos.py` (recibe `_contexto_yaml` y `_SECRETO`, movidos desde `cli_migrar.py`)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\cli_migrar.py` (importa de `cli_migrar_contextos`; queda por debajo de 300 líneas)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\talend_item\contextos_entorno.py`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_contextos_entorno.py`

**Interfaces:**
- Consumes: `Job.contextos: dict[str, list[ParametroContexto]]` y `ParametroContexto(nombre, tipo, valor, comentario, pedir)` (`modelo.py`); `desde_plan_contextos.GRUPOS = ("Default", "DEV", "QA", "PROD")`; `sin_secretos(contexto: dict[str, str]) -> None` (`src/sgm/backend_talend/comun.py`, lanza si una clave es de credencial y trae valor); `nodo_desde_plantilla("tContextLoad", ...)` (F2-6).
- Produces (`contextos_entorno.py`):
  ```python
  def leer_grupo(ruta: Path) -> tuple[str, dict[str, str]]:
      """(grupo, {variable: valor}) de un `contextos/<grupo>.yaml`. `ValueError` si el archivo
      no tiene `grupo` y `variables`, o si una variable repite nombre."""

  def aplicar_valores(job: Job, carpeta: Path) -> Job:
      """Job nuevo con el valor de cada variable tomado de `carpeta/<grupo>.yaml`.
      `ValueError` si el YAML trae una variable que el grupo del Job no tiene (o al revés):
      los cuatro grupos deben conservar las mismas claves en el mismo orden."""

  def nodo_carga_de_contexto(unico: str, archivo: str, variables: tuple[str, ...]) -> Nodo:
      """`tContextLoad` que lee `archivo` (par clave;valor) y declara las `variables` que carga."""
  ```

- [ ] **Step 1: Partir `cli_migrar.py` sin cambio de comportamiento.** Mover `_contexto_yaml` y `_SECRETO` a `cli_migrar_contextos.py` e importarlos. Run: `uv run python -m pytest tests/unit -q -p no:cacheprovider -k "migrar"`; la salida debe ser idéntica a la de antes de mover.
- [ ] **Step 2: Write the failing test.** Con `Job("J", contextos={"Default": [ParametroContexto("ruta_ventas", valor="a.csv")], "DEV": [ParametroContexto("ruta_ventas")], "QA": [ParametroContexto("ruta_ventas")], "PROD": [ParametroContexto("ruta_ventas")]})` y una carpeta `tmp_path` con `DEV.yaml` (`ruta_ventas: "/dev/ventas.csv"`) y `QA.yaml` (`/qa/ventas.csv`): `aplicar_valores` deja `/dev/ventas.csv` en `DEV`, `/qa/ventas.csv` en `QA`, `a.csv` en `Default` y `""` en `PROD` (sin archivo no cambia); el original no se muta; un `QA.yaml` con una variable `otra` extra lanza `ValueError` citando `otra`; un YAML con `clave_password: "abc"` lanza por `sin_secretos`; `nodo_carga_de_contexto("tContextLoad_1", "ctx.csv", ("clave_a",))` instancia la plantilla de F2-6 con el nombre del archivo.
- [ ] **Step 3: Run test to verify it fails.** `uv run python -m pytest tests/unit/test_contextos_entorno.py -q -p no:cacheprovider`.
- [ ] **Step 4: Implement** `contextos_entorno.py` (menos de 120 líneas) y, en `sgm migrar`, cuando `<out>/<programa>/contextos/` ya existe, aplicar `aplicar_valores` antes de escribir el `.item` y **no** pisar el YAML editado (hoy lo reescribe; el cambio es no reescribirlo si existe y avisar en el informe de migración). Run los tests de la tarea, `uv run python -m pytest tests/unit/test_desde_plan_contextos.py tests/unit/test_talend_contextos.py -q -p no:cacheprovider` y `uv run ruff check src tests tools`.
- [ ] **Step 5: Commit.** `hito N m: valores por entorno leidos de contextos/<grupo>.yaml y tContextLoad` (con la línea de coautoría).

---

### Task F2-12: Job ejecutado con `DEV` y con `QA` (el valor de cada variable impreso)

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\talend_item\contextos_humo.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\validar_contextos_studio.py`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_contextos_humo.py`

**Interfaces:**
- Consumes: `aplicar_valores(job: Job, carpeta: Path) -> Job` (F2-11); `fixed_flow_input(...)` y `log_row(...)` (`componentes.py`); `caso_de_corpus(caso, carpeta)` de F2-3 como modelo; `tools/corpus_studio.py validar <caso> --jobs ... --padre ... --grupo-contexto <grupo>` (ya existe la opción `--grupo-contexto`).
- Produces (`contextos_humo.py`):
  ```python
  def job_imprime_contexto(nombre: str, variables: tuple[str, ...]) -> Job:
      """`tFixedFlowInput` con una fila cuyas columnas valen `context.<variable>`, a `tLogRow`.
      Declara las variables en los cuatro grupos."""

  VALORES_DE_PRUEBA = {"DEV": {"origen": "valor-dev", "umbral": "10"},
                       "QA": {"origen": "valor-qa", "umbral": "20"},
                       "PROD": {"origen": "valor-prod", "umbral": "30"}}
  ```
  Sin secretos: ninguna variable de `VALORES_DE_PRUEBA` es de credencial.

- [ ] **Step 1: Write the failing test.** `job_imprime_contexto("humo_ctx", ("origen", "umbral"))` tiene los cuatro grupos con las dos variables en el mismo orden, y su `tFixedFlowInput` usa `context.origen` y `context.umbral`; `validar_job(job) == []`; aplicado `aplicar_valores` con `VALORES_DE_PRUEBA` escritos como YAML, `render_item` del grupo `QA` contiene `value="valor-qa"`.
- [ ] **Step 2: Run test to verify it fails.** `uv run python -m pytest tests/unit/test_contextos_humo.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement** el módulo y `tools/validar_contextos_studio.py [--grupos DEV QA]`: para cada grupo escribe un caso de corpus temporal con el esperado de ese grupo (`valor-dev|10`, `valor-qa|20`), exporta el Build Job y ejecuta el lanzador con `--context=<grupo>` (nunca `talend_job_execute`, que no carga contextos: `docs/guia-validacion-studio.md`, secciones del paso 5 y 6), y compara. Sin Studio: `lote C pendiente: <motivo>` y salida 3.
- [ ] **Step 4: Run** el test, ruff y, con Studio, `uv run python tools/validar_contextos_studio.py --grupos DEV QA`; el criterio de MG-P9-04 es que cada ejecución imprima el valor de su grupo. Pegar la salida literal en `PROGRESS.md`; `PROD` solo se verifica escrito (no se ejecuta contra producción).
- [ ] **Step 5: Commit.** `hito N m: contextos DEV y QA ejecutados con su valor impreso` (con la línea de coautoría).

---

## Parte IV. Conexiones y triggers (MG-P9-05, 5 h)

### Task F2-13: Referencia de Studio para los disparadores y quitar sus `xfail`

`tests/unit/test_conexiones_tipos.py` busca la conexión de referencia en **todos** los `*.item` de `tests/fixtures/talend/` (`_conexion_de_studio`). Un `xfail` estricto que pasa falla, así que al agregar la referencia se quita el decorador de cada prueba que ya pasa.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\fixtures\talend\conexiones_disparadores_0.1.item` (guardado por Studio, no escrito a mano)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\talend_item\conexiones.py` (`al_error_subjob`, `al_error_componente`)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_conexiones_tipos.py`

**Interfaces:**
- Consumes: `al_terminar_subjob(origen: str, destino: str, n: int = 1) -> Conexion`, `al_terminar_componente(...)`, `iterar(origen: str, destino: str, n: int = 1, paralelo: int = 0) -> Conexion`, `si(origen: str, destino: str, condicion: str, n: int = 1) -> Conexion`, `lookup(origen: str, destino: str, nombre: str = "row2") -> Conexion`, y el privado `_disparador(origen, destino, n, conector, estilo, base) -> Conexion`.
- Produces:
  ```python
  def al_error_subjob(origen: str, destino: str, n: int = 1) -> Conexion:
      """`OnSubjobError`: el destino corre si el subjob del origen falla."""

  def al_error_componente(origen: str, destino: str, n: int = 1) -> Conexion:
      """`OnComponentError`: el destino corre si el origen falla."""
  ```
  `lineStyle`, `connectorName` y parámetros de ambas salen del Job de referencia de Studio, no de `docs/studio-internals` de `talend-mcp` (que dice 4 para `SUBJOB_ERROR` sin un `.item` que lo contenga).

- [ ] **Step 1: Obtener la referencia (lote C).** En Studio, armar el Job `conexiones_disparadores` con un `tFixedFlowInput` y `tLogRow` unidos por: `OnSubjobOk`, `OnComponentOk`, `OnSubjobError`, `OnComponentError`, `Run if` e `Iterate` (con un `tFileList`), y un `tMap` con una entrada `Lookup`; guardarlo y copiar su `.item` a `tests/fixtures/talend/conexiones_disparadores_0.1.item`. Anotar `connectorName`, `lineStyle` y parámetros de cada una en `docs/guia-validacion-studio.md` (sección 4, que hoy deja `SUBJOB_ERROR` pendiente, tarea R2-05). Sin Studio: «lote C pendiente», y las pruebas de los pasos 2 a 5 usan el `.item` que ya produjo el generador de `talend-mcp` para esos tipos, marcado en el fixture como no guardado por Studio hasta que se repita.
- [ ] **Step 2: Write the failing test.** En `test_conexiones_tipos.py`: quitar el `xfail` de `test_on_subjob_error_tiene_referencia_de_studio`, `test_iterate_se_escribe_como_studio` y `test_lookup_se_escribe_como_studio`, y de cada otra prueba cuyo conector ya esté en el fixture; reescribir la primera para que llame `al_error_subjob("tFixedFlowInput_1", "tLogRow_1")` y compare con `_comparar_con_studio("SUBJOB_ERROR", elemento)`; agregar `test_on_component_error_se_escribe_como_studio` análoga con `al_error_componente`.
- [ ] **Step 3: Run test to verify it fails.** `uv run python -m pytest tests/unit/test_conexiones_tipos.py -q -p no:cacheprovider`; esperado: no existe `al_error_subjob`.
- [ ] **Step 4: Implement** las dos funciones con `_disparador` (menos de 12 líneas cada una). Run el archivo de pruebas completo: no debe quedar un `XPASS` ni un `xfail` de los tipos de este paso; los que siguen en `xfail` (`REJECT`, `FILTER`, `ORDER`) son F2-14. `uv run ruff check src tests tools`.
- [ ] **Step 5: Commit.** `hito N m: OnSubjobError y OnComponentError desde referencia de Studio, sin xfail en disparadores` (con la línea de coautoría).

---

### Task F2-14: `Reject`, `Filter` y orden de ejecución con `ORDER`

El `xfail` de `ORDER` dice que no es un tipo de conexión (no está en `components.json`) y que el único `ORDER` conocido es un parámetro de `tSortRow`. La tarea aclara qué es el «orden de ejecución» de MG-P9-05 y lo prueba.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\fixtures\talend\conexiones_filas_0.1.item` (guardado por Studio)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\talend_item\conexiones.py` (`rechazo`, `filtro`)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\talend_item\modelo.py` (campo `orden: int = 0` en `Conexion`)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\talend_item\item.py` (escribe las conexiones de un mismo origen por `orden`)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_conexiones_tipos.py`

**Interfaces:**
- Consumes: `Conexion(origen, destino, nombre, conector, estilo, parametros, etiqueta)` (`modelo.py`); `_conexion_de_studio(conector: str) -> ET.Element` del test.
- Produces:
  ```python
  def rechazo(origen: str, destino: str, nombre: str = "reject") -> Conexion:
      """`Reject` de un componente que lo admite (por ejemplo `tFileInputDelimited`, `tMap`)."""

  def filtro(origen: str, destino: str, nombre: str = "filter") -> Conexion:
      """`Filter` de `tFilterRow`: las filas que cumplen la condición."""
  ```
  y `Conexion.orden: int = 0` (por omisión 0: nada cambia en los Jobs existentes).

- [ ] **Step 1: Referencia de Studio (lote C).** Armar y guardar el Job `conexiones_filas`: un `tFilterRow` con salidas `Filter` y `Reject`; un `tFileInputDelimited` con `Reject`; un `tMap` con dos salidas principales (`Main`); y un componente de arranque con dos `OnSubjobOk` hacia dos subjobs. Copiar el `.item` al fixture. Con el `.item` a la vista **responder por escrito en `docs/guia-validacion-studio.md`** cómo fija Studio el orden: en los Jobs de Studio 8.0.1 el orden de los subjobs hijos de un mismo disparador y el de las salidas de un componente se escribe en `<connection ... outputId=...>` o por la posición del elemento en el archivo (lo que muestre el fixture). Sin Studio: «lote C pendiente» y `ORDER` sigue en `xfail` con ese motivo.
- [ ] **Step 2: Write the failing test.** Quitar los `xfail` de `test_reject_se_escribe_como_studio` y `test_filter_se_escribe_como_studio` y reescribirlas con `rechazo(...)` y `filtro(...)`; reemplazar `test_el_orden_de_ejecucion_con_order` por: un Job de un origen con dos conexiones `OnSubjobOk` de `orden` 2 y 1 se escribe con la de `orden=1` primero (o con el `outputId` que el fixture muestre), y con ambas de `orden=0` se conserva el orden de la lista.
- [ ] **Step 3: Run test to verify it fails.** `uv run python -m pytest tests/unit/test_conexiones_tipos.py -q -p no:cacheprovider`.
- [ ] **Step 4: Implement** `rechazo`, `filtro`, el campo `orden` y el orden en `item._conexion`/`render_item` (ordenar con `sorted(..., key=lambda c: (c.origen, c.orden))` de forma estable solo cuando alguna `orden` no es 0). Run: el archivo completo, `uv run python -m pytest tests/unit/test_talend_item.py tests/unit/test_validador_job.py -q -p no:cacheprovider` y los `test_golden*.py` (idénticos), y `uv run ruff check src tests tools`. Criterio de MG-P9-05: cada tipo (`OnSubjobOk`, `OnComponentOk`, `Run if`, `OnSubjobError`, `Iterate`, `Lookup`, `Reject`, `Main`, `Filter`, orden) con una prueba **sin `xfail`**; `Main` ya la tiene (`test_fila_main_flow_coincide_con_el_job_real`).
- [ ] **Step 5: Commit.** `hito N m: Reject, Filter y orden de ejecucion con referencia de Studio` (con la línea de coautoría).

---

## Parte V. Lienzo, propiedades y notas (MG-P9-06 y MG-P9-07, 5 h)

### Task F2-15: Disposición por subjobs sin superposición de cajas (Q11)

Hoy `disponer(job: Job) -> Job` (`src/sgm/talend_item/disposicion.py`, 87 líneas) calcula columna por profundidad y fila por orden de aparición, y el validador (`_superposicion`, `validador.py`) solo detecta dos nodos en el mismo punto. Falta: subjobs agrupados (cada subjob en su propia banda), separación suficiente para que las etiquetas y la caja del subjob no se pisen, y un validador de cajas.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\talend_item\subjobs.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\talend_item\validador_lienzo.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\talend_item\disposicion.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\talend_item\validador.py` (llama a `validador_lienzo.cajas_superpuestas`; el archivo hoy tiene 249 líneas y el cambio es de 3)
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_disposicion_subjobs.py`

**Interfaces:**
- Consumes: `disponer(job: Job) -> Job`, `ANCHO_COLUMNA = 200`, `ALTO_FILA = 96`, `item._subjobs(job)` (escribe un bloque `<subjob>` por cada nodo de arranque; es la referencia de qué nodos arrancan un subjob), `Conexion.estilo` (`1` `OnSubjobOk`, `3` `OnComponentOk`, `0` fila).
- Produces:
  ```python
  # subjobs.py
  def subjobs_de(job: Job) -> list[list[str]]:
      """UNIQUE_NAME de cada subjob, en orden de ejecución: nodos unidos por filas (FLOW, LOOKUP,
      REJECT, FILTER, ITERATE) van juntos; un disparador (SUBJOB_OK/ERROR, COMPONENT_OK/ERROR,
      RUN_IF) separa subjobs."""

  # validador_lienzo.py
  ANCHO_CAJA = 120
  ALTO_CAJA = 64
  def cajas_superpuestas(job: Job) -> list[str]:
      """Mensaje por cada par de nodos cuyas cajas (ANCHO_CAJA x ALTO_CAJA desde x, y) se tocan."""
  ```
  `disponer` pasa a poner cada subjob en una banda vertical propia: dentro del subjob, columna por profundidad como hoy; entre subjobs, la fila inicial del siguiente es la última fila usada más una fila de separación. `disposicion.ANCHO_COLUMNA` y `ALTO_FILA` se conservan; el Job de un solo subjob queda **idéntico** al de hoy.

- [ ] **Step 1: Write the failing test.** (a) Dos subjobs unidos por `OnSubjobOk`, el primero con 3 nodos en cadena y el segundo con 2: tras `disponer`, ningún par de cajas se superpone (`cajas_superpuestas(job) == []`) y todas las `y` del segundo subjob son mayores que las del primero; (b) un Job de un subjob (`tFixedFlowInput -> tMap -> tLogRow`) queda con las mismas posiciones que da hoy (`(0,0)`, `(200,0)`, `(400,0)`); (c) un `tMap` con una entrada `Lookup` y dos salidas ocupa tres filas distintas en la columna siguiente y `cajas_superpuestas` es `[]`; (d) dos nodos en `(0,0)` y `(60,30)` son reportados por `cajas_superpuestas` aunque no estén en el mismo punto; (e) dos corridas dan el mismo resultado; (f) el Job de entrada no se muta.
- [ ] **Step 2: Run test to verify it fails.** `uv run python -m pytest tests/unit/test_disposicion_subjobs.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement** `subjobs_de` (componentes conexos por conexiones de fila) y el nuevo `disponer`; si `disposicion.py` pasa de 150 líneas, la profundidad se mantiene allí y el reparto de bandas va a `subjobs.py`. Enganchar `cajas_superpuestas` en `validar_job`.
- [ ] **Step 4: Run** `uv run python -m pytest tests/unit/test_disposicion.py tests/unit/test_disposicion_subjobs.py tests/unit/test_validador_job.py -q -p no:cacheprovider` (los 10 de `test_disposicion.py` siguen en verde: no se debilitan) y los `test_golden*.py`; `uv run ruff check src tests tools`. Con Studio, abrir un Job grande migrado y confirmar a ojo (captura en `PROGRESS.md`) que ninguna caja se superpone; es la validación de Q11.
- [ ] **Step 5: Commit.** `hito N m: lienzo por subjobs sin superposicion de cajas` (con la línea de coautoría).

---

### Task F2-16: Propiedades del Job y notas con la línea de SAS (Q10)

`Job.proposito`, `Job.descripcion`, `Job.autor` y `Nodo.comentario` existen en `modelo.py` pero no se escriben, porque los nombres de clave de Studio no están verificados en ningún fixture. `desde_plan.py` ya sabe la línea de origen (`_linea(op)` toma `op.evidence[0].line_start`).

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\fixtures\talend\propiedades_y_notas_0.1.item` y `propiedades_y_notas_0.1.properties` (guardados por Studio)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\talend_item\notas.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\talend_item\anotaciones.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\talend_item\modelo.py` (`Nota`, `Job.notas`)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\talend_item\item.py` (escribe el comentario del nodo, las notas y, en el `.properties`, propósito y descripción)
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_anotaciones.py`

**Interfaces:**
- Consumes: `Nodo.comentario: str`, `Job.proposito`, `Job.descripcion`, `Job.autor` (`modelo.py`); `Operator.evidence[0].line_start` y `Evidence.file` (`src/sgm/ir/models.py`); `plan_a_jobs(plan, esquemas, ruta_java=None) -> ResultadoMigracion` (se llama a `anotar_jobs` desde fuera, **sin** tocar `desde_plan.py`, que tiene 859 líneas).
- Produces:
  ```python
  # modelo.py
  @dataclass(frozen=True)
  class Nota:
      texto: str
      x: int = 0
      y: int = 0
      ancho: int = 200
      alto: int = 60

  # anotaciones.py
  def comentario_de_linea(evidencia: Evidence) -> str:
      """`"SAS <archivo>:<línea>"`, por ejemplo `SAS programa.sas:42`."""

  def anotar_jobs(jobs: list[Job], plan: Plan) -> list[Job]:
      """Pone `comentario` en cada nodo cuyo operador tiene evidencia, y `proposito` y
      `descripcion` en cada Job (qué paso del SAS lo originó, sin inventar nada)."""
  ```
  `render_item` escribe el comentario del nodo y las notas según la forma que muestre el fixture de Studio; `render_properties` escribe propósito y descripción con las claves que muestre el `.properties` de Studio.

- [ ] **Step 1: Referencia de Studio (lote C).** En Studio crear un Job con un nodo con comentario («SAS programa.sas:42»), una nota (nota de Studio con texto) y propósito, descripción y versión rellenos; guardarlo y copiar `.item` y `.properties` a `tests/fixtures/talend/`. Anotar en `docs/guia-validacion-studio.md` los nombres de elemento y de atributo reales (el del comentario del nodo es el parámetro de nodo que el fixture muestre; la nota es un elemento propio del `.item`). Sin Studio: «lote C pendiente», y la tarea completa solo los pasos 2 a 4 con `anotar_jobs` (que no depende del formato) y deja `render_*` sin cambiar.
- [ ] **Step 2: Write the failing test.** `comentario_de_linea(Evidence("programa.sas", 42, 44, None)) == "SAS programa.sas:42"`; `anotar_jobs` sobre un plan de dos operadores (uno con evidencia en la línea 42 y otro sin) deja `comentario == "SAS programa.sas:42"` en el primer nodo y `""` en el otro (no se inventa una línea); `render_item` de un Job con `Nodo.comentario = "SAS programa.sas:42"` contiene ese texto con la forma del fixture; `render_properties` de un Job con `proposito="Carga de saldos"` lo contiene con la clave del fixture; un texto con comillas, `<` y saltos de línea se escapa y se lee igual con `ET`.
- [ ] **Step 3: Run test to verify it fails.** `uv run python -m pytest tests/unit/test_anotaciones.py -q -p no:cacheprovider`.
- [ ] **Step 4: Implement** `anotaciones.py` (menos de 100 líneas), `notas.py` (render de `Nota`) y los cambios mínimos de `item.py` (213 líneas hoy; si pasa de 280, el render de notas queda en `notas.py` y `item.py` solo lo llama). Llamar a `anotar_jobs` en la ruta de `sgm migrar` justo después de `plan_a_jobs`. Run los tests, `uv run python -m pytest tests/unit/test_talend_item.py tests/unit/test_validador_job.py -q -p no:cacheprovider`, los `test_golden*.py` (la firma de un Job no incluye comentarios; si la incluyera, se documenta el cambio de golden en `PROGRESS.md` y se regenera con la herramienta existente) y `uv run ruff check src tests tools`. Con Studio, abrir un Job migrado y ver las líneas de SAS en los nodos (captura en `PROGRESS.md`).
- [ ] **Step 5: Commit.** `hito N m: propiedades del Job y notas con la linea de SAS` (con la línea de coautoría).

---

## Parte VI. Rutinas Java compartidas (MG-P9-08, 5 h)

### Task F2-17: Rutina de repositorio solo cuando una expresión inline no alcanza

La regla del plan maestro: **solo cuando una expresión inline no alcance**. Esta tarea primero decide con datos del catálogo cuáles funciones SAS no caben inline y solo entonces escribe una rutina.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\talend_item\rutinas.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\docs\decisiones-rutinas-java.md`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_rutinas.py`

**Interfaces:**
- Consumes: `rules/sas/catalogo/funciones-usadas.yaml` (entradas con `estado: no_reconocida`, esquema `schemas/rules/catalogo.schema.json`); la tabla de funciones de `src/sgm/expressions/talend_*.py`; `render_properties(job: Job, ...)` como modelo del `.properties` de un item de Studio.
- Produces (`rutinas.py`):
  ```python
  CARPETA_RUTINAS = "code/routines"     # carpeta de rutinas en el proyecto de Studio
  TIPO_PROPERTIES = "TalendProperties:RoutineItem"

  @dataclass(frozen=True)
  class Rutina:
      nombre: str                        # clase Java, por ejemplo SgmFunciones
      fuente: str                        # código Java completo
      fuente_sas: str                    # "<guía>, p. N" de la función que implementa

  def requiere_rutina(funcion_sas: str, expresion_java_inline: str | None) -> bool:
      """`True` solo si no hay expresión inline demostrada para la función."""

  def render_rutina_item(r: Rutina) -> str
  def render_rutina_properties(r: Rutina, autor: str = "_0KqD4YE9EfGMqbenmdd8gw", fecha: str = "") -> str
  ```

- [ ] **Step 1: Decidir con datos.** Listar las funciones `no_reconocida` de `rules/sas/catalogo/funciones-usadas.yaml` (`grep -n "no_reconocida" -B4 rules/sas/catalogo/funciones-usadas.yaml`) y, por cada una, ubicar su página en `docs/referencia/sas/lefunctionsref.INDEX.md` y leer **solo esa página** del `.txt` (`grep -n "<!-- página N -->" docs/referencia/sas/lefunctionsref.txt`). Escribir en `docs/decisiones-rutinas-java.md` una tabla función / ¿cabe inline con la tabla de `src/sgm/expressions/`? / ¿hace falta rutina? / página. Si **ninguna** necesita rutina, la tarea termina aquí: la decisión («no hace falta rutina de repositorio; las expresiones se emiten inline») se registra en `PROGRESS.md` y en el documento, y los pasos 2 a 5 se omiten sin contar horas. Una función sin página no se implementa (`Pendiente:` con motivo).
- [ ] **Step 2: Write the failing test.** Para la primera función de la tabla que sí requiere rutina (se nombra al escribir el test, con el valor de la página citada): `requiere_rutina("<función>", None)` es `True`; con una expresión inline demostrada es `False`; `render_rutina_properties` contiene `TalendProperties:RoutineItem`; `render_rutina_item` contiene el código Java de la rutina y su cabecera cita `fuente_sas`; una función con rutina compila (`javac` del JDK de Studio vía `TALEND_JAVA_BIN`, o se omite la prueba con `pytest.skip("sin JDK")`) y su resultado sobre dos valores concretos coincide con el esperado que da el intérprete de referencia o la página de la guía.
- [ ] **Step 3: Run test to verify it fails.** `uv run python -m pytest tests/unit/test_rutinas.py -q -p no:cacheprovider`.
- [ ] **Step 4: Implement** `rutinas.py` (menos de 150 líneas) y la llamada desde la tabla de expresiones solo para las funciones de la tabla de decisión. Con Studio, importar la rutina, compilar un Job que la use y ejecutarlo con datos (`tools/validar_caso_studio.py <caso>` con un caso del corpus que use esa función, o un caso nuevo en `tests/corpus/` con su esperado); sin Studio: «lote C pendiente». Run los tests, `uv run python -m pytest tests/unit/test_catalogo_sas.py tests/unit/test_no_script_specific_names.py -q -p no:cacheprovider` y `uv run ruff check src tests tools`.
- [ ] **Step 5: Commit.** `hito N m: decision sobre rutinas Java compartidas y rutina de repositorio si hacia falta` (con la línea de coautoría).

---

## Parte VII. MCP, ida y vuelta y cierre (MG-P9-10 y MG-P9-09, 10 h)

### Task F2-18: Comparar el emisor propio con `talend_jobs_create_from_spec`

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\backend_talend\spec.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\talend_item\comparar_items.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\comparar_con_mcp.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\docs\informe-emisor-propio-vs-mcp.md`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_comparar_items.py`

**Interfaces:**
- Consumes: `McpBackend` y su transporte (`src/sgm/backend_talend/mcp.py`; el cliente de pruebas `tools/mcp_cliente.py` lista las herramientas del servidor y sus esquemas); `render_item(job: Job) -> str`.
- Produces:
  ```python
  # comparar_items.py
  @dataclass(frozen=True)
  class Diferencia:
      ruta: str            # ruta XPath simplificada: "node[tMap_1]/elementParameter[MAP_TYPE]"
      propio: str | None
      otro: str | None

  def comparar(item_propio: str, item_otro: str, ignorar: tuple[str, ...] = ("internalId", "id", "posX", "posY", "created_date", "modified_date")) -> list[Diferencia]:
      """Diferencias estructurales entre dos `.item`, sin ids ni posiciones ni fechas."""

  # spec.py
  def job_a_spec(job: Job) -> dict:
      """El `JobSpec` que `talend_jobs_create_from_spec` espera, armado desde un Job propio."""
  ```

- [ ] **Step 1: Leer el esquema real.** Con `uv run python tools/mcp_cliente.py` (el cliente ya existente) pedir el esquema de entrada de `talend_jobs_create_from_spec` y copiarlo literal como comentario de `spec.py`. No suponer los nombres de campo.
- [ ] **Step 2: Write the failing test.** `comparar(a, a) == []` para un `.item` cualquiera; con dos `.item` iguales salvo `posX`, `internalId` y una fecha, devuelve `[]`; con un parámetro `FILENAME` distinto devuelve una `Diferencia` con `ruta` que termina en `elementParameter[FILENAME]`, y el orden de las diferencias sigue el del documento; `job_a_spec(Job("J", nodos=[...]))` devuelve un `dict` con el nombre del Job y un nodo por cada nodo del Job (la forma exacta se fija al terminar el Step 1).
- [ ] **Step 3: Run test to verify it fails.** `uv run python -m pytest tests/unit/test_comparar_items.py -q -p no:cacheprovider`.
- [ ] **Step 4: Implement** los dos módulos y `tools/comparar_con_mcp.py <caso>`: migra el caso (`plan_a_jobs`), pide a `talend_jobs_create_from_spec` el mismo Job y escribe las diferencias en `out/`. Con Studio: correr sobre cinco casos del corpus, uno de ellos con `tMap` con metadatos (el componente difícil del plan maestro), y escribir `docs/informe-emisor-propio-vs-mcp.md` con cada diferencia explicada (causa y quién tiene razón según Studio). **Adoptar** del MCP solo lo que Studio abra y guarde sin cambios; para cada componente difícil, el camino probado queda anotado en el informe. Sin Studio: «lote C pendiente» y se entregan los dos módulos con sus pruebas.
- [ ] **Step 5: Commit.** `hito N m: comparador del emisor propio con el generador del MCP e informe de diferencias` (con la línea de coautoría).

---

### Task F2-19: Ida y vuelta en el editor de Studio (Q14: persona y agente)

Es la única tarea con una persona: abre un Job emitido en Studio y lo guarda. El agente prepara el protocolo y el comparador, y corrige el emisor hasta que Studio no cambie nada.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\ida_y_vuelta.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\docs\guia-ida-y-vuelta-studio.md`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_ida_y_vuelta.py`

**Interfaces:**
- Consumes: `comparar(item_propio: str, item_otro: str, ignorar: tuple[str, ...] = ...) -> list[Diferencia]` (F2-18); `escribir(jobs: list[Job], carpeta: Path) -> list[Path]` del backend de archivos.
- Produces (`tools/ida_y_vuelta.py`):
  ```python
  def preparar(caso: str, carpeta: Path) -> list[Path]:
      """Escribe en `carpeta/antes/` los Jobs del caso listos para que una persona los abra."""

  def informe(carpeta: Path) -> str:
      """Compara `carpeta/antes/*.item` con `carpeta/despues/*.item` (lo que guardó Studio) y
      devuelve Markdown con las diferencias agrupadas por componente y por parámetro."""
  ```

- [ ] **Step 1: Write the failing test.** Con dos carpetas `antes/` y `despues/` en `tmp_path`, `informe(carpeta)` devuelve un texto que contiene `Diferencias: 0` si los `.item` son iguales (salvo ids y fechas) y, si en `despues/` cambia `DIE_ON_ERROR` de `false` a `true` en `tFileInputDelimited_1`, contiene esa línea con el componente y el parámetro; `preparar("l0_01_where_sentencia", tmp_path)` escribe `antes/` con un `.item` y un `.properties` por Job.
- [ ] **Step 2: Run test to verify it fails.** `uv run python -m pytest tests/unit/test_ida_y_vuelta.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement** `tools/ida_y_vuelta.py` (`preparar` y `informe`, con `argparse`: `preparar <caso> <carpeta>` y `informe <carpeta>`) y escribir `docs/guia-ida-y-vuelta-studio.md`: protocolo de la persona en cinco pasos (importar los Jobs de `antes/`, abrir cada uno, no tocar nada, guardar, copiar los `.item` a `despues/`) y qué hace el agente con el informe.
- [ ] **Step 4: Día-persona (lote C).** Una persona sigue la guía sobre tres casos (uno con `tMap`, uno con contextos y uno con un disparador `Run if`); el agente corre `uv run python tools/ida_y_vuelta.py informe <carpeta>` y por cada diferencia corrige el emisor o la plantilla (la causa es casi siempre un parámetro con valor por omisión distinto, un campo `show` o el orden de los elementos) y repite hasta `Diferencias: 0`. Cada corrección lleva su prueba. Run `uv run python -m pytest tests/unit -q -p no:cacheprovider -k "talend or plantilla or conexion or disposicion"` y `uv run ruff check src tests tools`. Si la persona no está disponible: «lote C pendiente (persona)» y se entregan el protocolo y el comparador.
- [ ] **Step 5: Commit.** `hito N m: protocolo y comparador de ida y vuelta en el editor de Studio` (con la línea de coautoría).

---

### Task F2-20: F2-Gate. Arquitectura por omisión con reutilización, contextos y límites (GM4, lote C)

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\talend_item\arquitectura.py` (solo si la prueba de GM4 muestra que falta la elección de `decidir` por omisión; el archivo tiene 127 líneas)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\docs\plan-reescritura\plan-migrador-general.md` (estado de MG-P9 y porcentaje en la sección 11b)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\PROGRESS.md`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_gm4_emisor.py`

**Interfaces:**
- Consumes: `prioritarias()` y `estado_biblioteca()` (F2-1), `casos_humo()` (F2-3), `decidir(...)` y `capacidades()` (F2-9), `aplicar_valores(...)` (F2-11), `anotar_jobs(...)` (F2-16), `disponer(...)`, `validar_job(...)`.
- Produces: la prueba de aceptación GM4 y la actualización de las cifras del plan maestro.

- [ ] **Step 1: Write the failing test.** `test_gm4_emisor.py`: (a) toda entrada de `prioritarias()` con `estado` distinto de `sin_pagina` tiene plantilla, meta y caso de humo (`casos_humo()`), 54 menos los `sin_pagina` documentados; (b) para un caso del corpus con un bloque repetido, el Job emitido usa `tRunJob` o un joblet según `decidir(...)` y `capacidades()`, y `validar_job` de cada Job es `[]`; (c) los cuatro grupos de contexto tienen las mismas claves en el mismo orden y ninguna variable de credencial tiene valor; (d) `cajas_superpuestas(job) == []` para todos los Jobs emitidos del corpus `traducible` (recorrer los casos de L0 a L6 con `plan_a_jobs`); (e) ningún `xfail` en `test_conexiones_tipos.py` (leer el archivo y comprobar que no contiene `xfail`).
- [ ] **Step 2: Run test to verify it fails** donde falte una pieza y completar lo que esta fase deje a medias (la causa se anota en `PROGRESS.md`).
- [ ] **Step 3: Lote C de cierre.** Con `uv run python -m sgm.cli studio salud` en `ok`: `uv run python tools/corpus_studio.py lote <casos con bloque repetido y contextos>` y `uv run python tools/validar_caso_studio.py <caso>` para cada uno; `uv run python tools/validar_reutilizacion_studio.py` y `uv run python tools/validar_contextos_studio.py --grupos DEV QA`. Pegar la tabla (compilan, ejecutan, coinciden) y los límites (qué plantillas son `solo_compila` y por qué, qué sigue `sin_pagina`, si el joblet cargó o se quedó el plan B) en `PROGRESS.md`. Todo lo que no se pudo correr queda **«lote C pendiente»** con su motivo y se encola con `uv run python tools/corpus_studio.py pendientes`; no se cuenta como GM4 pasada.
- [ ] **Step 4: Cifras.** Volver a correr `uv run python tools/linea_base_plantillas.py`; actualizar en `plan-migrador-general.md` la fila de MG-P9 de la sección 11b con las horas reales y el porcentaje, y la sección «Estado» de la fase; si el plan contradice al código, se corrige en este mismo cambio. Run `uv run python -m pytest -q -p no:cacheprovider` (suite completa, solo aquí) y `uv run ruff check .`: ambas en verde.
- [ ] **Step 5: Commit.** `hito N m: GM4 emisor de Talend (plantillas, reutilizacion, contextos y lienzo)` (con la línea de coautoría).

---

## Dependencias

- **Plan A (`mg-a-studio-y-mcp-fiables`):** A-6 (joblets en `talend-mcp`) alimenta F2-8; A-5 ya cerró el hito 193 (`tHashInput`); A-4 y A-7 (compilar sin ventana) mejoran los lotes C pero no bloquean. Sin Studio sano, cada tarea cierra su parte local y queda «lote C pendiente».
- **Orden interno:** F2-1 a F2-3 antes de F2-4 a F2-7 (los lotes usan el generador, el catálogo y el arnés de humo); F2-6 antes de F2-11 (`tContextLoad`); F2-8 antes de F2-9 y F2-10; F2-11 antes de F2-12; F2-13 antes de F2-14 (comparten el archivo de pruebas y el fixture); F2-15 y F2-16 son independientes entre sí y de las demás; F2-18 antes de F2-19 (`comparar`); F2-20 al final.
- **Plan B (`mg-b-datastep-y-plan-logico`):** F2-9 y F2-10 dejan la regla `decidir` que consume MG-P8-03 (extracción a joblets de bloques repetidos, 14 h); el emisor desde el plan (`desde_plan_*.py`) de ese plan y las tareas F2-15 y F2-16 no editan los mismos archivos (F2-15 y F2-16 usan módulos nuevos; `desde_plan.py` y `desde_plan_map.py` no se tocan aquí).
- **Archivos compartidos con otras sesiones:** `rules/talend/plantillas_meta.yaml` y `plantillas_humo.yaml` los tocan solo F2-1 a F2-7 en orden; `item.py`, `modelo.py` y `conexiones.py` los tocan F2-8 (campo `joblet`), F2-13 y F2-14 (conexiones) y F2-16 (notas); hacer cada tarea en su orden y un commit por tarea evita conflictos.

## Self-review

- Cobertura de MG-P9: P9-01 en F2-3 a F2-7; P9-02 en F2-1 y F2-2; P9-03 en F2-8 a F2-10; P9-04 en F2-11 y F2-12; P9-05 en F2-13 y F2-14; P9-06 en F2-15; P9-07 en F2-16; P9-08 en F2-17; P9-10 en F2-18; P9-09 en F2-19; GM4 en F2-20.
- Los 29 nombres que faltan (lista en «Estado de partida») están repartidos así: 7 en F2-4, 7 en F2-5, 6 en F2-6 y 9 en F2-7 (29 en total). Los 25 que existen se cubren con casos de humo en F2-3 (todas las plantillas de `disponibles()` exigen caso o `solo_compila` con motivo).
- Cada `Modify` apunta a un archivo que existe hoy: `modelo.py`, `item.py`, `conexiones.py`, `disposicion.py`, `validador.py`, `arquitectura.py`, `cli_migrar.py`, `tools/extraer_plantilla.py`, `tools/contenedores/extraer_plantillas_talend.py`, `tests/unit/test_conexiones_tipos.py`, `rules/talend/plantillas_meta.yaml` y `plantillas_humo.yaml` (creados en F2-1 y F2-3 antes de usarse), `docs/plan-reescritura/plan-migrador-general.md`, `PROGRESS.md`. Las carpetas de los `Create` existen (`src/sgm/talend_item/`, `src/sgm/backend_talend/`, `rules/talend/`, `tools/`, `tests/unit/`, `tests/fixtures/talend/`, `docs/`).
- Ningún archivo de más de 300 líneas se modifica sin partirlo antes: `cli_migrar.py` (340) se parte en F2-11 Step 1; `desde_plan.py` y `desde_plan_map.py` no se tocan.
- Riesgos que el plan deja a la medición y no a la suposición: si Studio 8.0.1 carga un joblet escrito desde archivo (F2-8 Step 1); el `lineStyle` de `SUBJOB_ERROR`, `COMPONENT_ERROR` y `REJECT` y cómo fija Studio el orden de salidas y subjobs (F2-13, F2-14); el formato del comentario de nodo, de las notas y de las claves de propósito y descripción (F2-16); el esquema real de `talend_jobs_create_from_spec` (F2-18). En los cuatro casos hay un fixture guardado por Studio antes de escribir código y, si Studio no responde, la parte que depende de él queda «lote C pendiente».
- Impala: `tImpalaOutput`, `tImpalaClose` y `tImpalaCommit` no están en `rules/talend/components.json`; se verifican contra el inventario oficial en F2-1 y, si no aparecen, quedan `sin_pagina` con `Pendiente:`.

## Resumen de horas

| Tarea | MG-P9 | Horas |
|---|---|---|
| F2-1 Catálogo con metadatos y línea base | P9-02 | 4 |
| F2-2 Generador de plantilla nueva | P9-02 | 4 |
| F2-3 Arnés de humo por plantilla | P9-01 | 3 |
| F2-4 Plantillas de archivos (7) | P9-01 | 5 |
| F2-5 Plantillas de transformación (7) | P9-01 | 5 |
| F2-6 Plantillas de control y utilidades (6) | P9-01 | 4 |
| F2-7 Plantillas de bases de datos (9) | P9-01 | 3 |
| F2-8 Escritor de joblets y spike de carga | P9-03 | 5 |
| F2-9 Plan B `tRunJob` y regla | P9-03 | 4 |
| F2-10 Bloque reutilizable en dos Jobs | P9-03 | 5 |
| F2-11 Valores por entorno y `tContextLoad` | P9-04 | 3 |
| F2-12 Contextos DEV y QA ejecutados | P9-04 | 3,5 |
| F2-13 Disparadores con referencia de Studio | P9-05 | 3 |
| F2-14 `Reject`, `Filter` y `ORDER` | P9-05 | 2 |
| F2-15 Lienzo por subjobs | P9-06 | 2 |
| F2-16 Propiedades y notas con línea de SAS | P9-07 | 3 |
| F2-17 Rutinas Java compartidas | P9-08 | 5 |
| F2-18 Emisor propio frente al MCP | P9-10 | 6 |
| F2-19 Ida y vuelta en Studio | P9-09 | 4 (más 1 día-persona) |
| F2-20 F2-Gate (GM4, lote C) | cierre | 0 (dentro de las anteriores) |
| **Total** | | **73,5** |

P9-01 suma 20 h (F2-3 a F2-7), P9-02 8 h, P9-03 14 h, P9-04 6,5 h, P9-05 5 h, P9-06 2 h, P9-07 3 h, P9-08 5 h, P9-10 6 h y P9-09 4 h. F2-20 no suma horas propias: es la corrida de lote C y la actualización de cifras que cada tarea ya prevé.
