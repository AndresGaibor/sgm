# MG-F1: Planificador de arquitectura y optimizador Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Que `sgm migrar` y `sgm diseno` produzcan por omisión la arquitectura que haría una persona en Talend, sin YAML de agrupación: un Job padre que orquesta por las dependencias reales del linaje, Jobs hijos segmentados por etapa y región, ningún Job con más de 20 componentes, bloques repetidos como joblet (o `tRunJob` como plan B), datos que pasan entre Jobs por archivos de trabajo, errores y registro por defecto, nombres y `trace.json` completos; y que el optimizador termine sus reglas pendientes (MG-P8b-05 a 08). La lista de calidad Q1 a Q15 del plan maestro (sección 7) deja de ser una tabla y pasa a ser pruebas automáticas sobre cada salida del corpus.

**Architecture:** Un paquete nuevo `src/sgm/planificador/` (el paso 6 del flujo del plan maestro: «planificador, agrupa en Jobs, joblets, padre, contextos, límites») que trabaja **sobre el `Plan` ya compilado y optimizado** y produce sub-planes: cada hijo es un `Plan` normal que el emisor de siempre (`plan_a_jobs`) convierte en un Job, así que `desde_plan.py` (859 líneas) y `desde_plan_map.py` (815) no se tocan. Un arista del grafo que cruza de un hijo a otro se materializa como `write_file` en el productor y `read_file` en el consumidor, con la ruta en un parámetro de contexto (nunca `tHash*` entre Jobs). El padre se escribe aparte, con `run_job` y `al_terminar_subjob` de `jobs_diseno.py`/`conexiones.py`. Un paquete nuevo `src/sgm/calidad/` trae un verificador por criterio Q, que se ejecutan sobre la salida de `migrar` del corpus. Las reglas de optimizador siguen en `src/sgm/optimizar/` y se demuestran con el intérprete contra `esperado/`, sin Studio.

**Tech Stack:** Python 3.12, pytest, ruff, `networkx` (ya dependencia permitida; los cortes y componentes conexos); `uv run python -m pytest` y `uv run python -m sgm.cli` (en este Windows `uv run pytest` puede bloquearse por Control de aplicaciones).

**Spec:** `docs/plan-reescritura/plan-migrador-general.md` (MG-P8-01 a MG-P8-07, MG-P8b-05 a MG-P8b-08, sección 7 con Q1 a Q15, sección 11b), `docs/plan-reescritura/ruta-a-produccion.md` (DC-08, R2-07) y `docs/superpowers/plans/2026-11-11-ruta-al-100.md`.

**Horas del plan maestro cubiertas:** MG-P8 restante 55 h (MG-P8-01, 02, 03, 05, 06 y 07; MG-P8-04 está hecho desde el hito 104m) + MG-P8b restante 6 h (MG-P8b-05, 06, 07, 08) = 61 h.

**Serie de hitos:** `m` (carril de Andres, F1-1 a F1-Gate). La letra va en el título de la entrada de `PROGRESS.md` y en el mensaje del commit. Los Planes hermanos usan `m` y `n` en paralelo: la serie `m` ya la usa el Plan C (SQL); el número de hito es lo que no se repite, no la letra.

## Global Constraints

- Sin `git push`, sin `--amend`. Un commit local por hito: `hito N m: <resumen>`, terminado con la línea `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Antes de escribir, buscar el último `## Hito` de `PROGRESS.md` (al redactar este plan era el 198) y sumar uno; si otra sesión ya tomó el número, tomar el siguiente. No renumerar entradas publicadas.
- No tocar `tools/ci.py`, `tools/validacion.py`, `tools/instalar_ganchos.py`, `README.md` ni `.githooks/` (son del Plan A y estaban sin commitear al escribir este plan).
- Nada de nombres de scripts de ejemplo (`cod1`, `cod2`, `cars_poc`, `exogena`, `split2`, `split3`, `executeBulkload`, `waitForBulkLoads`, `bulkload_generic`) en `src/` ni `rules/`; lo vigila `tests/unit/test_no_script_specific_names.py`. Las reglas del planificador se basan en la estructura del grafo (tipo de operador, aristas, conjuntos de datos), nunca en el nombre de un programa. Lo que dependa del nombre del cliente va a `decisiones/<programa>.*.yaml`.
- Si el SAS no demuestra un tipo, una columna, un valor o una equivalencia: `Pendiente:` con motivo y código `P-xxx`. Nunca un valor supuesto. Un Job parcial que difiere de SAS no se emite.
- Si una regla nueva del optimizador reescribe una semántica de SAS, cita `<guía>, p. N` de una página que exista en `docs/referencia/sas/<guía>.INDEX.md`, y su equivalencia se comprueba con el intérprete contra `esperado/` sin Studio. La validación en Studio usa `tools/validar_caso_studio.py <caso>`; si `sgm studio salud` no conecta, no reinstalar nada ni cambiar `talend-mcp` (ver `docs/guia-validacion-studio.md`, sección 7): la tarea queda «lote C pendiente» con su motivo y no se cuenta como pasada.
- No borrar ni debilitar pruebas. Los `xfail` de este plan son **estrictos** (`strict=True`): una prueba que debía fallar y pasa rompe la suite, y la tarea que la arregla quita su `xfail` en el mismo commit. Los `test_golden*.py`, `test_ir_operadores_corpus.py` y `test_optimizar_corpus.py` deben seguir idénticos hasta F1-Gate (ver Review Focus).
- Archivos de código de menos de 300 líneas. Ya pasan de 300 y **no se tocan**: `desde_plan.py` (859; única excepción, F1-18, que sustituye un bloque por una llamada y no lo hace crecer) y `desde_plan_map.py` (815). Pasan de 300 y se parten primero, en un paso propio y sin cambio de comportamiento, cuando una tarea los toca: `cli_migrar.py` (340 líneas, F1-12) y `migrar/informes.py` (312, F1-14). Si una tarea toca un archivo que ya tiene más de 280 líneas, el primer paso extrae lo que necesita a un módulo nuevo.
- Código e identificadores en inglés cuando son de bajo nivel; los nombres del dominio (`segmento`, `etapa`, `traspaso`, `hallazgo`) siguen la convención de `src/sgm/optimizar/` y `src/sgm/proceso/`, que están en español. Comentarios, docstrings, mensajes y documentación en español.
- Después de cada tarea: `uv run python -m pytest -q` y `uv run ruff check src tests tools` en verde. Para iterar se corre solo el archivo de la tarea (`-p no:cacheprovider`); la suite completa se corre al cerrar cada tarea.
- **Arquitectura planificada es opcional hasta F1-Gate.** `sgm migrar --arquitectura plana|planificada` (F1-12): `plana` es la conducta de hoy y sigue por omisión hasta que el Gate cambia el valor. Así los golden y las 101 aceptaciones del corpus no cambian mientras se construye.

## Review Focus

- **Un Job hijo nunca cambia el resultado del programa.** Partir un plan en sub-planes y materializar las aristas cortadas como archivos de trabajo tiene que dar las mismas tablas finales que el plan entero: la prueba de F1-11 ejecuta los sub-planes en orden con el intérprete y compara con `esperado/` de cada caso. Tipos y orden de columnas viajan en el esquema del archivo; un tipo no demostrado no se cambia a `String` en silencio.
- **El corte por tamaño minimiza datos que cruzan, no solo el tamaño.** F1-10 usa programación dinámica sobre un orden topológico y cuenta aristas cortadas; el orden de los operadores no puede cambiar entre corridas (Q13, determinismo).
- **`tHash*` solo dentro de un Job.** `tHashOutput`/`tHashInput` comparten memoria del proceso y no sobreviven entre Jobs; entre Jobs el traspaso es un archivo de trabajo. F1-11 y F1-18 prueban las dos mitades de esa regla.
- **Fallo parcial (DC-08) configurable, con el valor seguro por omisión:** si falla un hijo, el padre falla (`falla_todo`). La alternativa `continua` se activa con una decisión del equipo (`decisiones/<programa>.decisiones.yaml`), nunca sola. F1-13.
- **Los criterios Q se prueban sobre el Job emitido, no sobre el plan.** Un verificador que mira el plan no ve lo que Studio abre. Cada verificador recibe `Job` (`talend_item/modelo.py`) y el texto de `render_item(job)`.
- **Ningún pase nuevo puede cambiar la firma de los Jobs ya validados** en L0 a L3 mientras `arquitectura` sea `plana`.

---

## Parte I. Medición y lista de calidad Q1 a Q15 (serie `m`, 11 h)

Se empieza midiendo: no se sabe cuántos Jobs del corpus pasan hoy de 20 componentes ni cuántos criterios Q ya se cumplen. La lista Q se escribe como código antes que el planificador, para que cada tarea siguiente cierre criterios y la medida diga cuánto falta.

### Task F1-1: Línea base medida de tamaño, regiones y cruces (serie `m`)

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\linea_base_planificador.py`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_linea_base_planificador.py`

**Interfaces:**
- Consumes: `migrar(source: Path, out: Path, esquemas: Path | None = None, muestra: Path | None = None, backend: str = "archivos") -> ResultadoMigrar` (`src/sgm/cli_migrar.py:271`; `ResultadoMigrar.jobs: list[Job]`); `Job.nodos` (`src/sgm/talend_item/modelo.py`); `compile_file(...)`, `project_base()` y `analyze_program({nombre: texto})` (el patrón de `tests/unit/test_optimizar_corpus.py`, líneas 14 a 40).
- Produces:
  ```python
  ESTRUCTURALES = frozenset({"tPrejob", "tPostjob"})  # no cuentan para el límite de componentes

  def componentes(job: Job) -> int:
      """Nodos del Job sin `tPrejob` ni `tPostjob`: la medida de Q4."""

  def medir(programas: dict[str, Path], trabajo: Path) -> dict:
      """Por programa: Jobs emitidos, componentes de cada uno, el mayor, operadores del plan,
      componentes conexos del grafo del plan (regiones) y aristas que cruzan entre ellos por
      conjuntos permanentes. Salida JSON en `out/linea_base_planificador.json` (no versionada)."""
  ```

- [ ] **Step 1: Write the failing test.** Con un programa mínimo en `tmp_path` (un `PROC IMPORT` a `WORK.A` y un `PROC SQL` que crea `WORK.B` desde `WORK.A` y lo exporta con `PROC EXPORT`), `medir({"p": ruta}, tmp_path / "out")["p"]` cumple `jobs == 1`, `mayor == componentes(job)` y `componentes` de un `Job` armado a mano con `tPrejob`, `tPostjob` y dos nodos más vale `2`.
- [ ] **Step 2: Run test to verify it fails.** `uv run python -m pytest tests/unit/test_linea_base_planificador.py -q -p no:cacheprovider`; esperado: no existe el módulo.
- [ ] **Step 3: Implement** `componentes` y `medir` con `migrar` (no reimplementar el compilador) y `networkx` para los componentes conexos del `Graph` del plan (`graph.edges()` da `Edge(src, dst, dataset)`). Sin dependencias nuevas.
- [ ] **Step 4: Run test to verify it passes**, correr `uv run python tools/linea_base_planificador.py tests/corpus tests/fixtures/sas` y pegar en `PROGRESS.md` la línea base: cuántos programas, cuántos Jobs, cuántos pasan de 20 componentes y el mayor de todos, cuántos programas tienen más de una región y cuántas aristas cruzan por conjunto permanente. Esa cifra fija el alcance real de F1-10 (si ningún Job del corpus pasa de 20, F1-10 se prueba con un plan sintético, y se dice).
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N m: linea base medida de tamano y regiones de los Jobs` (con la línea `Co-Authored-By`).

---

### Task F1-2: Modelo de calidad y criterios Q1, Q2 y Q12 (contextos y secretos; serie `m`)

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\calidad\__init__.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\calidad\modelo.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\calidad\contexto.py`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_calidad_contexto.py`

**Interfaces:**
- Consumes: `Job`, `Nodo`, `Fila`, `ParametroContexto` (`talend_item/modelo.py`; `Fila = tuple[str, str, str | None, str | None]` = `(campo, nombre, valor, show)`); `render_item(job: Job) -> str` (`talend_item/item.py:161`); `escanear_texto(texto: str, archivo: str = "<texto>") -> list[Hallazgo]` (`seguridad/escaner_secretos.py:68`); `GRUPOS = ("Default", "DEV", "QA", "PROD")`.
- Produces:
  ```python
  # modelo.py
  @dataclass(frozen=True)
  class Hallazgo:
      criterio: str    # "Q1" a "Q15"
      job: str
      nodo: str        # UNIQUE_NAME o "" si es del Job
      mensaje: str

  @dataclass(frozen=True)
  class Salida:
      """Lo que dejó migrar un programa, en la forma que los verificadores leen."""
      jobs: tuple[Job, ...]
      traza: dict[str, list[int]]
      padre: str | None           # nombre del Job padre, o None si la arquitectura es plana

  Verificador = Callable[[Salida], list[Hallazgo]]
  CRITERIOS: dict[str, Verificador]   # se llena con @criterio("Q1")

  # contexto.py
  def q1_nada_fijo(salida: Salida) -> list[Hallazgo]:
      """Rutas absolutas, `jdbc:`, servidores y fechas literales dentro de los parámetros de un nodo
      (menos las que están como `context.<nombre>`)."""
  def q2_contextos_completos(salida: Salida) -> list[Hallazgo]:
      """Mismas claves en Default, DEV, QA y PROD; contraseñas vacías o `***`; el tipo coincide con
      el valor (`id_Integer` con entero, `id_Date` con fecha)."""
  def q12_sin_secretos(salida: Salida) -> list[Hallazgo]:
      """El escáner de secretos sobre `render_item` de cada Job y sobre sus parámetros de contexto."""
  ```

- [ ] **Step 1: Write the failing test.** Un `Job` armado a mano con un nodo que tiene `Fila("TEXT", "FILENAME", '"C:\\datos\\entrada.csv"', None)` da un `Hallazgo("Q1", ...)` y con `context.dir_entrada + "/entrada.csv"` no da ninguno. Un `Job` con el grupo `QA` sin la clave `dir_entrada` que `Default` sí tiene da `Q2`. Una `ParametroContexto("clave_base", "id_Password", "abc123")` da `Q2` y con valor `"***"` no. Un nodo con `PASS = "hunter2"` da `Q12`.
- [ ] **Step 2: Run test to verify it fails.** `uv run python -m pytest tests/unit/test_calidad_contexto.py -q -p no:cacheprovider`; esperado: no existe el paquete.
- [ ] **Step 3: Implement** el modelo y los tres verificadores. Q1 mira solo los parámetros `TEXT`/`FILE`/`DIRECTORY` y los literales de SQL de `tImpalaRow`/`tMap`; una ruta relativa sin unidad ni barra inicial no es «fija» (`"entrada.csv"` es un nombre). Un `@criterio("Q1")` registra la función en `CRITERIOS`.
- [ ] **Step 4: Run test to verify it passes.** Después, sobre cuatro Jobs reales de `tests/corpus/L1`, correr los tres verificadores y anotar en `PROGRESS.md` cuántos hallazgos salen: es la medida inicial de Q1, Q2 y Q12, no una condición de verde (el estado de cada Q lo gobierna F1-5).
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N m: modelo de calidad y criterios Q1, Q2 y Q12`.

---

### Task F1-3: Criterios Q4, Q8, Q9, Q11 y Q15 (estructura y rendimiento; serie `m`)

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\calidad\estructura.py`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_calidad_estructura.py`

**Interfaces:**
- Consumes: `Salida`, `Hallazgo`, `criterio` (F1-2); `componentes(job: Job) -> int` (F1-1); `validar_job(job: Job) -> list[str]` (`talend_item/validador.py:235`, cuyo `_superposicion` ya detecta cajas solapadas); `Columna(nombre, tipo="id_String", nulable, clave, longitud, precision, patron)`.
- Produces:
  ```python
  LIMITE_POR_OMISION = 20

  def q4_tamano(salida: Salida, limite: int = LIMITE_POR_OMISION) -> list[Hallazgo]:
      """Un Job con más de `limite` componentes (sin `tPrejob`/`tPostjob`)."""
  def q8_esquemas_tipados(salida: Salida) -> list[Hallazgo]:
      """Un `tMap` o lector donde todas las columnas son `id_String` sin que lo diga un pendiente de
      tipo, y una columna `id_BigDecimal` sin `longitud` y `precision`."""
  def q9_lectores_estrictos(salida: Salida) -> list[Hallazgo]:
      """`tFileInputDelimited`/`tFileInputExcel` con `DIE_ON_ERROR` distinto de `true`."""
  def q11_disposicion(salida: Salida) -> list[Hallazgo]:
      """Cajas superpuestas, usando `validar_job` (solo los defectos de superposición)."""
  def q15_rendimiento(salida: Salida) -> list[Hallazgo]:
      """Un `tMap` con lookup en `LOAD_ONCE` sobre un lookup que no es de archivo pequeño (lo
      justifica el pendiente de volumen), y un `tMap` con un cruce sin llave (producto cartesiano)."""
  ```

- [ ] **Step 1: Write the failing test.** Un `Job` armado con 21 nodos `tMap` da un `Hallazgo("Q4", ...)` con el mensaje `"21 componentes; el límite es 20"`, y con 20 no da ninguno; con `tPrejob` y `tPostjob` además de los 20, tampoco. Un `tFileInputDelimited` con `DIE_ON_ERROR=false` da `Q9`. Dos nodos con la misma `x` e `y` dan `Q11`.
- [ ] **Step 2: Run test to verify it fails.** `uv run python -m pytest tests/unit/test_calidad_estructura.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement.** Antes de escribir Q9 y Q15 comprobar con `Grep` en `src/sgm/talend_item/plantillas/tFileInputDelimited.json` y `tMap.json` el nombre exacto de los parámetros (`DIE_ON_ERROR`, `LOAD_ONCE` o el que traiga la plantilla): si el nombre no coincide, usar el real y anotarlo. Q15 es revisión estática; no ejecuta nada.
- [ ] **Step 4: Run test to verify it passes.** Dejar `Q15` en una sola comprobación (producto cartesiano) y dejar anotado en `PROGRESS.md` que la «prueba de volumen» del plan maestro no se automatiza aquí: queda para el lote de rendimiento (`tools/performance/`), con sus propios datos.
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N m: criterios Q4, Q8, Q9, Q11 y Q15 como verificadores`.

---

### Task F1-4: Criterios Q3, Q5, Q6, Q7, Q10, Q13 y Q14 (orquestación, errores, registro y trazabilidad; serie `m`)

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\calidad\orquestacion.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\calidad\trazabilidad.py`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_calidad_orquestacion.py`

**Interfaces:**
- Consumes: `Salida`, `Hallazgo`, `criterio` (F1-2); `Conexion(origen, destino, nombre, conector, estilo, parametros, etiqueta)` con `estilo` 1 = OnSubjobOk (`talend_item/modelo.py`, `conexiones.py`); `render_item(job)`.
- Produces:
  ```python
  def q3_padre_por_dependencias(salida: Salida) -> list[Hallazgo]:
      """Si `salida.padre` no es None: cada `tRunJob` del padre apunta a un Job que existe en
      `salida.jobs` y los hijos van encadenados por `OnSubjobOk`. Si es None: sin hallazgos (la
      arquitectura plana no tiene padre)."""
  def q5_joblets_repetidos(salida: Salida) -> list[Hallazgo]:
      """Dos Jobs o dos tramos de un Job con la misma secuencia de componentes y mapeos (misma
      huella) y que no usan un joblet ni un hijo común."""
  def q6_errores(salida: Salida) -> list[Hallazgo]:
      """Cada subjob crítico (el que escribe una salida) con `OnSubjobError` hacia un `tDie` con
      `EXIT_CODE` y mensaje no vacíos, y un `tLogCatcher` en el Job."""
  def q7_registro(salida: Salida) -> list[Hallazgo]:
      """El parámetro de contexto `log_nivel` existe y hay un componente que escribe el
      `NB_LINE` de cada etapa."""
  def q10_nombres(salida: Salida) -> list[Hallazgo]:
      """Nombres de Job únicos y legibles (`^[A-Za-z][A-Za-z0-9_]*$`, sin el `UNIQUE_NAME` genérico
      como único nombre), y cada nodo de `traza` con al menos una línea del SAS."""
  def q13_determinismo(salida: Salida, otra: Salida) -> list[Hallazgo]:
      """Dos corridas dan el mismo `render_item` y la misma `traza`, byte a byte."""
  def q14_ida_y_vuelta(salida: Salida) -> list[Hallazgo]:
      """Sin Studio: el Job no depende de un parámetro que Studio reescribe al abrirlo
      (ver F2-19). Con Studio: `tools/comparar_item.py` (lo crea F2-19; hasta entonces el
      criterio devuelve el hallazgo `pendiente: lote C`)."""
  ```

- [ ] **Step 1: Write the failing test.** `Job` de padre armado a mano con un `tRunJob` hacia `h_no_existe` da `Q3`. Un `Job` con un subjob que escribe `tFileOutputDelimited` y sin `OnSubjobError` da `Q6`. `q13_determinismo` con dos `Salida` cuyo `jobs` difieren en un nodo da un hallazgo con el nombre del Job. Dos `Job` de nombre `Job1` dan `Q10`.
- [ ] **Step 2: Run test to verify it fails.** `uv run python -m pytest tests/unit/test_calidad_orquestacion.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement.** Q6 y Q7 reconocen el `tDie` y el `tLogCatcher` por el nombre del componente (`Nodo.componente`). El código de `lineStyle` de `OnSubjobError` no está verificado en el repositorio (`conexiones.py` solo trae OnSubjobOk = 1, OnComponentOk = 3, Run if = 6): **verificar al ejecutar** en `docs/` de `talend-mcp` o con el fixture que deja F2-13, y mientras tanto Q6 reconoce el disparador por `Conexion.conector == "SUBJOB_ERROR"`.
- [ ] **Step 4: Run test to verify it passes.** Q14 sin Studio comprueba solo lo estático; su hallazgo `pendiente: lote C` es esperado hasta F2-19 y no cuenta como fallo ni como cumplido (F1-5 lo lista aparte).
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N m: criterios Q3, Q5, Q6, Q7, Q10, Q13 y Q14 como verificadores`.

---

### Task F1-5: Q1 a Q15 sobre el corpus, con tablero de avance (serie `m`)

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_calidad_corpus.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\calidad_jobs.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\calidad\corpus.py`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_calidad_tablero.py`

**Interfaces:**
- Consumes: `CRITERIOS` (F1-2); `migrar(...)` (`cli_migrar.py:271`); `casos()`, `CORPUS`, `ESTADOS`, `NIVELES` de `tests/unit/test_migrar_corpus_anillo_b.py`; `tests/corpus/migrar_pendientes.yaml`.
- Produces:
  ```python
  # src/sgm/calidad/corpus.py
  def salida_de(resultado: ResultadoMigrar, padre: str | None = None) -> Salida: ...
  def evaluar(programas: dict[str, Path], trabajo: Path) -> dict[str, dict[str, int]]:
      """{criterio: {"jobs": n, "cumplen": n, "hallazgos": n}} sobre todos los Jobs emitidos."""
  def porcentaje(tablero: dict[str, dict[str, int]]) -> dict[str, float]

  # tests/unit/test_calidad_corpus.py
  ABIERTAS: dict[str, str]   # criterio -> tarea que lo cierra: {"Q3": "F1-12", "Q4": "F1-10", ...}
  ```

- [ ] **Step 1: Write the failing test.** `test_calidad_tablero.py`: con dos `Salida` armadas (una que cumple Q4 y otra que no), `porcentaje(evaluar(...))["Q4"] == 50.0`. `test_calidad_corpus.py`: parametrizada por criterio Q1 a Q15; para cada uno corre `evaluar` sobre los casos de `tests/corpus/L0` a `L3` que no están en `migrar_pendientes.yaml` y exige `hallazgos == 0`, salvo los de `ABIERTAS`, que van con `@pytest.mark.xfail(strict=True, reason="cierra F1-n")`.
- [ ] **Step 2: Run test to verify it fails.** `uv run python -m pytest tests/unit/test_calidad_tablero.py tests/unit/test_calidad_corpus.py -q -p no:cacheprovider`; esperado: no existe `sgm.calidad.corpus`.
- [ ] **Step 3: Implement** `corpus.py` y `tools/calidad_jobs.py` (imprime la tabla de Q1 a Q15 con su porcentaje y la tarea que lo cierra). Correrlo una vez y poner en `ABIERTAS` exactamente los criterios que hoy tienen hallazgos, con la tarea que los cierra según este plan: Q1 y Q2 (F1-12 si el hallazgo es de contextos de los hijos; F1-19 si es de la conexión a la base; si es de otra causa, una tarea nueva en este plan antes del Gate), Q3 (F1-12), Q4 (F1-12), Q5 (F1-15), Q6 y Q7 (F1-13), Q10 (F1-14), Q14 (F2-19, Studio). Un criterio que ya cumple no se lista.
- [ ] **Step 4: Run test to verify it passes** y pegar en `PROGRESS.md` la tabla de `tools/calidad_jobs.py`: es la línea base de Q1 a Q15 (porcentaje por criterio sobre el corpus que ya se migra). El plan maestro mide «Q1 a Q15 al 100 %»; esta cifra es el denominador y su evolución, una fila por hito.
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N m: Q1 a Q15 como pruebas sobre el corpus con tablero de avance`.

---
## Parte II. Planificador: segmentación, tamaño y traspaso (MG-P8-01, 02 y 05; serie `m`, 21 h)

El planificador no lee texto SAS: lee el `Plan` que ya compiló `sgm` (grafo de operadores, aristas con su conjunto de datos, evidencias con la línea de origen). Todo lo que sigue sale de la estructura del grafo.

### Task F1-6: Regiones y dependencias desde el linaje (MG-P8-01, parte 1; serie `m`)

Hoy `src/sgm/lineage.py` calcula dependencias **entre programas** (`graph_of`, `fronteras`) y `src/sgm/flow/regiones.py` divide el texto por un marcador (`dividir_regiones(texto, marcador)`), que es una decisión del equipo. Esta tarea calcula las regiones **dentro de un programa** desde el grafo, sin marcador.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\planificador\__init__.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\planificador\modelo.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\planificador\linaje.py`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_planificador_linaje.py`

**Interfaces:**
- Consumes: `Plan`, `Graph` (`graph.operators() -> list[Operator]`, `graph.edges() -> list[Edge]`, `graph.topological() -> list[str]`), `Operator(id, kind, params, ...)`, `Edge(src, dst, dataset, materialize)` (`src/sgm/ir/models.py`); constructores `leer`, `leer_archivo`, `escribir`, `escribir_archivo` (`src/sgm/ir/operadores.py`); `Graph.add_operator`, `Graph.add_edge`. Los datos permanentes se reconocen como en `lineage._datasets`: `params["dataset"]` de `read`/`write`, `params["outputs"]`, `params["inputs"]`/`params["sources"]`; un conjunto cuyo nombre empieza por `WORK.` es local.
- Produces:
  ```python
  # modelo.py
  @dataclass(frozen=True)
  class Region:
      indice: int
      operadores: tuple[str, ...]       # ids en orden topológico del plan
      escribe: frozenset[str]           # permanentes ("LIB.tabla") y archivos ("archivo:<ruta>")
      lee: frozenset[str]

  @dataclass(frozen=True)
  class Dependencia:
      origen: int                       # índice de la región que escribe
      destino: int                      # índice de la región que lee
      via: str                          # el conjunto o el archivo que las une

  # linaje.py
  def regiones_de(plan: Plan) -> list[Region]:
      """Componentes conexos del grafo de operadores, ordenados por su primer operador en el orden
      topológico. Un operador sin aristas es su propia región."""
  def dependencias(regiones: list[Region]) -> list[Dependencia]:
      """A -> B si A escribe un conjunto permanente o un archivo que B lee."""
  def orden_de_ejecucion(regiones: list[Region], deps: list[Dependencia]) -> list[list[int]]:
      """Oleadas: las regiones de una misma oleada no dependen entre sí. Los ciclos entre regiones
      se agrupan en una sola oleada, como hace `lineage.py` con los programas."""
  ```

- [ ] **Step 1: Write the failing test.** Con un `Plan` armado a mano (sin SAS) con cuatro operadores: `leer_archivo("r1", "in/a.csv", ["WORK.A"])`, `escribir("w1", "ANAL.salida")`, `leer("r2", ...)` de `ANAL.salida` y `escribir_archivo("w2", ["WORK.B"], "out/b.csv")`, con aristas `r1 -> w1` y `r2 -> w2`: `regiones_de(plan)` devuelve dos regiones, la primera con `escribe == frozenset({"ANAL.salida"})` y la segunda con `lee == frozenset({"ANAL.salida"})`; `dependencias(...) == [Dependencia(0, 1, "ANAL.salida")]`; `orden_de_ejecucion(...) == [[0], [1]]`. Con dos regiones que se escriben y se leen mutuamente, `orden_de_ejecucion` las devuelve en la misma oleada.
- [ ] **Step 2: Run test to verify it fails.** `uv run python -m pytest tests/unit/test_planificador_linaje.py -q -p no:cacheprovider`; esperado: no existe el paquete.
- [ ] **Step 3: Implement** con `networkx` (`weakly_connected_components` sobre un `DiGraph` con las aristas del plan; `condensation` para los ciclos entre regiones; `topological_generations` para las oleadas). El orden dentro de cada componente es el de `graph.topological()`; el orden entre componentes es el del primer operador, para que dos corridas den lo mismo (Q13).
- [ ] **Step 4: Run test to verify it passes.** Después, correr `regiones_de` sobre los planes de `tests/corpus/L1` y `L8` (con `compile_file(analyze_program({"p.sas": texto}), "p.sas", project_base()).plan`) y anotar en `PROGRESS.md` cuántas regiones salen por programa; debe coincidir con la línea base de F1-1.
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N m: regiones y dependencias desde el linaje del plan`.

---

### Task F1-7: Etapas por estructura: insumos, producto, totales y cierre (MG-P8-01, parte 2; serie `m`)

El plan maestro pide etapas «insumos, producto, totales, cierre». `src/sgm/proceso/etapas.py` ya carga etapas **declaradas** (`cargar_etapas`, `etapa_de`); esta tarea las deduce de la estructura y deja la declaración como prioridad.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\planificador\etapas.py`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_planificador_etapas.py`

**Interfaces:**
- Consumes: `Region`, `Dependencia` (F1-6); `Operator.kind` (valores `read`, `read_file`, `write`, `write_file`, `map`, `filter`, `aggregate`, `join`, `exec_sql`, `external_load`, `iterate`; verificar los nombres reales con `Grep` de `"kind"` en `src/sgm/ir/operadores.py` en el paso 3); `EtapaDeclarada` y `etapa_de(etiqueta: str, etapas: list[EtapaDeclarada]) -> str | None` (`proceso/etapas.py`).
- Produces:
  ```python
  ETAPAS = ("insumos", "producto", "totales", "cierre")

  def etapa_de_region(
      region: Region, plan: Plan, deps: list[Dependencia], total: int
  ) -> str:
      """Reglas, en este orden (la primera que cumple):
      1. `cierre`: no escribe nada permanente ni archivo y depende de todas las demás, o solo
         tiene operadores de control o `exec_sql` de limpieza.
      2. `insumos`: no depende de ninguna región y al menos otra región lee lo que escribe.
      3. `totales`: tiene un `aggregate` y todas sus salidas salen de agregados.
      4. `producto`: el resto (escribe una salida final).
      """
  def etapas_de(
      plan: Plan,
      regiones: list[Region],
      deps: list[Dependencia],
      declaradas: list[EtapaDeclarada] | None = None,
  ) -> dict[int, str]:
      """Región -> etapa; la etapa declarada por el equipo gana sobre la deducida."""
  ```

- [ ] **Step 1: Write the failing test.** Con las dos regiones del plan de F1-6 y una tercera que lee `ANAL.salida`, agrega con `agregar(...)` y escribe `ANAL.resumen`: `etapas_de(...) == {0: "insumos", 1: "producto", 2: "totales"}`; una cuarta sin salidas que depende de las tres da `"cierre"`. Una región sin dependencias que nadie lee es `producto`, no `insumos`.
- [ ] **Step 2: Run test to verify it fails.** `uv run python -m pytest tests/unit/test_planificador_etapas.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement.** Ninguna regla puede nombrar una tabla ni un programa (`test_no_script_specific_names.py`). Una etapa declarada se busca con `etapa_de(etiqueta, declaradas)` sobre la etiqueta de la primera evidencia de la región (`Evidence.label`).
- [ ] **Step 4: Run test to verify it passes.** Correr `etapas_de` sobre `tests/corpus/L8/totales` y `tests/corpus/L8/validaciones` y anotar el reparto en `PROGRESS.md`. Si una región cae en `producto` y es claramente de totales, la regla 3 está floja: se ajusta la regla, no se agrega una excepción.
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N m: etapas del planificador deducidas de la estructura`.

---

### Task F1-8: Segmentar el plan en sub-planes por región (MG-P8-01, parte 3; serie `m`)

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\planificador\modelo.py` (creado en F1-6)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\planificador\segmentar.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\planificador\nombres.py`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_planificador_segmentar.py`

**Interfaces:**
- Consumes: `regiones_de`, `dependencias`, `orden_de_ejecucion` (F1-6); `etapas_de` (F1-7); `Plan(program, graph, jobs, not_migrated, pending, gaps, joblets, ...)` y `Job(name, subjobs, contexts, context_groups, children)` (`ir/models.py`); `optimizar(plan: Plan) -> tuple[Plan, Informe]` (`optimizar/__init__.py:142`); `plan_desplegado(plan) -> tuple[Plan, set[str]]` (`ir/desplegar.py:17`).
- Produces:
  ```python
  # modelo.py (se amplía)
  @dataclass(frozen=True)
  class Segmento:
      nombre: str                       # único y legible: `<etapa>_<n>_<tabla principal>`
      etapa: str
      regiones: tuple[int, ...]
      plan: Plan                        # sub-plan normal: lo emite `plan_a_jobs`
      depende_de: tuple[str, ...]       # nombres de segmentos

  @dataclass(frozen=True)
  class PlanDeJobs:
      programa: str
      segmentos: tuple[Segmento, ...]
      oleadas: tuple[tuple[str, ...], ...]

  # nombres.py
  def nombre_legible(etapa: str, numero: int, tabla: str) -> str:
      """`totales_02_resumen`: minúsculas, `[a-z0-9_]`, sin biblioteca; la tabla es el conjunto de
      salida principal de la región. Sin salida: `<etapa>_<n>`."""

  # segmentar.py
  def segmentar(plan: Plan) -> PlanDeJobs:
      """Un segmento por región, con su sub-plan. El plan de entrada ya está desplegado y
      optimizado: el planificador no repite al optimizador."""
  ```

- [ ] **Step 1: Write the failing test.** Con el plan de cuatro operadores de F1-6, `segmentar(plan)` devuelve dos segmentos, `[s.nombre for s in ...] == ["insumos_01_salida", "producto_02_b"]`, el segundo con `depende_de == ("insumos_01_salida",)`, y cada `segmento.plan.graph.operators()` contiene solo sus ids. Los `Plan` resultantes no comparten `Graph` con el original (`is not`). Ninguna arista de un sub-plan apunta a un operador que no está en él.
- [ ] **Step 2: Run test to verify it fails.** `uv run python -m pytest tests/unit/test_planificador_segmentar.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement.** El sub-plan copia (`copy.deepcopy`) los operadores de su región y sus aristas, sus `not_migrated` por `op_id`, y un único `Job` con los subjobs del plan original filtrados a esos ids (los ids que no estaban en ningún subjob se omiten: `_Job.armar` los añade solo al final, `desde_plan.py:760`). `plan.pending`, `plan.gaps` y `plan.joblets` van al segmento cuyo operador los origina (la evidencia da la línea); lo que no tiene operador va al primer segmento, y la prueba verifica que la suma de pendientes de los segmentos es igual a la del plan. Dos segmentos con el mismo nombre legible reciben el sufijo `_b`, `_c`.
- [ ] **Step 4: Run test to verify it passes.** Segmentar los planes de `tests/corpus/L8` y de `tests/fixtures/sas` y ejecutar `plan_a_jobs` sobre cada sub-plan: ninguno lanza excepción y los `visitados` de todos los segmentos juntos cubren los operadores del plan entero (nada se pierde). Anotar en `PROGRESS.md` cuántos programas quedan en más de un segmento.
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N m: segmentacion del plan en sub-planes por region`.

---

### Task F1-9: `sgm diseno` sin YAML produce padre e hijos (MG-P8-01, cierre; serie `m`)

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\diseno.py` (32 líneas)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\cli_diseno.py` (82 líneas)
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_diseno_planificado.py`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_diseno.py` (sin cambios: debe seguir verde)

**Interfaces:**
- Consumes: `diseno_de_programa(programa: str, texto: str, plan, declaracion: Declaracion | None = None) -> dict` (`diseno.py:16`); `segmentar(plan) -> PlanDeJobs` (F1-8); `_declaracion(programa, ruta, carpeta=None)` (`cli_diseno.py`).
- Produces:
  ```python
  # diseno.py
  def diseno_de_programa(programa, texto, plan, declaracion=None) -> dict:
      """Igual que hoy, más la clave `"planificacion"`:
      {"segmentos": [{"nombre", "etapa", "depende_de", "operadores"}], "oleadas": [[nombre, ...]],
       "padre": {"hijos": [nombre, ...]}}
      La clave `"agrupacion"` y las demás que escribe `diseno_del_job` (`joblets`, `job_padre`,
      `firmas_de_componente`, `contexto`) no cambian de nombre ni de forma. Con `declaracion`,
      `agrupacion` sigue mandando y `planificacion` se escribe igual, como referencia."""
  ```

- [ ] **Step 1: Write the failing test.** Parametrizada por los casos de `tests/corpus/L1` a `L8` y por los programas de `tests/fixtures/sas`: sin ningún `decisiones/*.agrupacion.yaml`, `diseno_de_programa(...)["planificacion"]` existe, `padre.hijos` no está vacío y cada hijo de `padre.hijos` está en `segmentos`. Un programa con una sola región da un padre con un hijo.
- [ ] **Step 2: Run test to verify it fails.** `uv run python -m pytest tests/unit/test_diseno_planificado.py -q -p no:cacheprovider`; esperado: `KeyError: 'planificacion'`.
- [ ] **Step 3: Implement.** `diseno_de_programa` llama a `plan_desplegado` y `optimizar` antes de `segmentar`, en el mismo orden que `plan_a_jobs` (`desde_plan.py:833`), para que el diseño describa lo que `migrar` va a emitir. `cli_diseno.diseno_command` suma al mensaje de salida el número de segmentos y de oleadas.
- [ ] **Step 4: Run test to verify it passes**, más `tests/unit/test_diseno.py`, `test_agrupacion.py`, `test_objetivo_diseno.py` y `test_proceso_diseno_real.py`, sin cambios. Correr `uv run python -m sgm.cli diseno tests/fixtures/sas --out out/diseno-f1` y anotar en `PROGRESS.md` cuántos programas terminaron con padre e hijos y cuántos fallaron, con el motivo; un programa que falla se anota con su código, no se esconde.
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N m: sgm diseno sin YAML produce padre e hijos desde el linaje`.

---

### Task F1-10: Política de tamaño: tramos de a lo más 20 componentes con los menos datos cruzando (MG-P8-02; serie `m`)

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\planificador\modelo.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\planificador\tamano.py`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_planificador_tamano.py`

**Interfaces:**
- Consumes: `Segmento` (F1-8); `Graph.topological()`, `Graph.edges()`; `componentes(job: Job) -> int` (F1-1).
- Produces:
  ```python
  # modelo.py
  LIMITE_COMPONENTES = 20      # `calidad.estructura.LIMITE_POR_OMISION` vale lo mismo: una prueba lo exige

  @dataclass(frozen=True)
  class Corte:
      origen: str              # id del operador productor
      destino: str             # id del operador consumidor
      dataset: str             # el conjunto que cruza

  # tamano.py
  def peso_de(op: Operator) -> int:
      """Componentes que el emisor suele escribir para el operador: 1, y 1 más por cada lookup de
      un `map` (verificar el nombre del parámetro de los cruces con `Grep` de `lookup` en
      `desde_plan_map.py`; solo se lee, no se modifica)."""
  def tramos(
      orden: list[str], aristas: list[tuple[str, str]], pesos: dict[str, int], limite: int
  ) -> list[tuple[str, ...]]:
      """Parte `orden` (topológico) en tramos contiguos de peso <= `limite` que minimizan el número
      de aristas cortadas (una arista que atraviesa dos cortes cuenta dos veces: pasa por un
      archivo en cada salto). Programación dinámica O(n * limite). Desempate: menos tramos, y entre
      iguales el primer corte más a la derecha. Un operador cuyo peso solo ya supera el límite
      queda solo en su tramo."""
  def partir(segmento: Segmento, limite: int = LIMITE_COMPONENTES) -> tuple[list[tuple[str, ...]], list[Corte]]:
      """Tramos del segmento y los `Corte` que quedan entre ellos."""
  ```

- [ ] **Step 1: Write the failing test.** Cadena `o1..o6` con aristas `o1-o2, o2-o3, o3-o4, o4-o5, o5-o6` y una más `o1-o3`, todos de peso 1 y `limite=3`: `tramos(...) == [("o1","o2","o3"), ("o4","o5","o6")]` y `partir` da un solo `Corte("o3","o4",...)`; un corte en `o2|o3` habría cruzado `o2-o3` y `o1-o3`. Con `limite=6` no hay corte. Un operador de peso 25 con `limite=20` queda solo en su tramo y `partir` anota `P-OPERADOR-EXCEDE-LIMITE` en la lista de avisos. La partición es la misma en dos corridas con el mismo grafo (Q13).
- [ ] **Step 2: Run test to verify it fails.** `uv run python -m pytest tests/unit/test_planificador_tamano.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement** el DP: `mejor[k]` = costo mínimo de partir los primeros `k` operadores; `mejor[k] = min(mejor[j] + cruces(j))` para `j` desde `k-1` hacia atrás mientras el peso de `orden[j:k]` no pase de `limite`; `cruces(j)` = aristas con `pos(origen) < j <= pos(destino)`, calculadas con un barrido de diferencias. Añadir la prueba `calidad.estructura.LIMITE_POR_OMISION == LIMITE_COMPONENTES`.
- [ ] **Step 4: Run test to verify it passes.** Con el plan sintético de la línea base de F1-1: si ningún Job del corpus pasa de 20 componentes, armar un plan sintético de 45 operadores en tres bloques de 15 unidos por una sola arista y comprobar que `partir` corta exactamente en esas dos aristas (3 tramos de 15), no por posición.
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N m: politica de tamano con cortes de minimo cruce`.

---

### Task F1-11: Paso de datos entre Jobs por archivos de trabajo (MG-P8-05; serie `m`)

Entre dos Jobs el traspaso es un archivo de trabajo (el mecanismo (b) validado del plan maestro). `tHashOutput`/`tHashInput` comparten memoria **dentro** de un Job y no sirven entre Jobs. Un `tBufferOutput` con `tRunJob` y una conexión compartida son las otras dos opciones del plan maestro: esta tarea decide cuál aplica y emite solo la que está demostrada.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\planificador\traspaso.py`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_planificador_traspaso.py`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_planificador_equivalencia.py`

**Interfaces:**
- Consumes: `Corte` y `partir` (F1-10); `Segmento` (F1-8); `escribir_archivo(op_id, inputs, outfile, dbms=None, delimiter=None, evidence=None)` y `leer_archivo(op_id, datafile, outputs, dbms=None, delimiter=None, getnames=None, sheet=None, guessingrows=None, evidence=None)` (`ir/operadores.py:81` y `109`); `contextos_de_plan(plan: Plan) -> dict[str, list[ParametroContexto]]` y `rutas_de_plan(plan)` (`desde_plan_contextos.py:38` y `67`: una ruta literal pasa a la variable `ruta_<tabla>`, y la misma tabla en una lectura y en una escritura da la misma variable); `ejecutar_plan(plan, entradas) -> dict[str, list[dict]]` (`migrar/interprete.py`); `plan_a_jobs(plan, esquemas, ruta_java=None)`.
- Produces:
  ```python
  MECANISMOS = ("archivo", "conexion", "buffer")      # "hash" no existe entre Jobs

  def mecanismo_de(corte: Corte, plan: Plan, decididos: dict[str, str] | None = None) -> str:
      """`conexion` si los dos extremos del corte tienen `placement` que empieza con `db:` (la
      tabla ya vive en la base: el consumidor la lee de allí, sin archivo ni operador nuevo);
      `buffer` solo si `decididos[corte.dataset] == "buffer"` (decisión del equipo); en cualquier
      otro caso `archivo`."""
  def aplicar_cortes(
      segmento: Segmento, tramos: list[tuple[str, ...]], decididos: dict[str, str] | None = None
  ) -> list[Segmento]:
      """Un segmento por tramo. En el segmento productor, un `write_file` del conjunto que cruza
      (CSV con cabecera, ruta relativa `trabajo/<tabla>.csv`); en el consumidor, un `read_file`
      de esa misma ruta que produce el mismo conjunto. El esquema del archivo es el del
      productor: columna, tipo y orden. `buffer` sale como `Pendiente: P-TRASPASO-BUFFER`
      mientras no haya un spike de Studio que lo demuestre."""
  ```

- [ ] **Step 1: Write the failing tests.** (a) `test_planificador_traspaso.py`: con un plan de seis operadores y el corte de F1-10, `aplicar_cortes` devuelve dos segmentos; el primero termina en un `write_file` cuyo `outfile` es `trabajo/<tabla>.csv`, el segundo empieza en un `read_file` con ese `datafile` y los mismos `outputs`; `mecanismo_de` devuelve `"archivo"`, `"conexion"` si los dos operadores tienen `placement="db:impala"` y `"archivo"` aunque `decididos` diga `"hash"` (valor no permitido, se ignora y se anota). Al emitir con `plan_a_jobs` ningún nodo de ningún Job tiene un `componente` que empiece por `tHash`. Los dos Jobs comparten la variable de contexto `ruta_<tabla>`. (b) `test_planificador_equivalencia.py`: sobre los casos de `tests/corpus/L1` a `L3` con más de un operador, partir con `limite=2`, ejecutar los sub-planes en orden con `ejecutar_plan` pasando al segundo las filas de la tabla que cruza, y comparar las tablas de salida con `esperado/` (mismo criterio que `test_optimizar_corpus.py`: `_entradas`, `_esperado`, `orden_relevante`).
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_planificador_traspaso.py tests/unit/test_planificador_equivalencia.py -q -p no:cacheprovider`; esperado: no existe `traspaso`.
- [ ] **Step 3: Implement.** Un conjunto que cruza hacia dos consumidores en tramos distintos se escribe **una** vez. El nombre del operador nuevo es `<tabla>_traspaso_w` y `<tabla>_traspaso_r` (los ids de operador tienen que ser únicos en el sub-plan). Verificar al ejecutar cómo nombra `ejecutar_plan` las entradas de un `read_file` (`Grep` de `read_file` en `src/sgm/migrar/interprete.py`) y adaptar el paso que alimenta al segundo plan.
- [ ] **Step 4: Run tests to verify they pass.** Un caso del corpus cuya salida difiere al partir se anota con su motivo (por ejemplo orden relevante o un tipo que el CSV no conserva) en `PROGRESS.md` y en un `xfail` estricto con ese motivo; no se baja el límite hasta que pasen.
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N m: traspaso de datos entre Jobs por archivos de trabajo`.

---

### Task F1-12: Padre por dependencias, hijos emitidos y `sgm migrar --arquitectura` (MG-P8-01 y 02, cierre; Q3 y Q4; serie `m`)

`cli_migrar.py` tiene 340 líneas: el primer paso extrae la escritura de salidas a un módulo nuevo, sin cambio de comportamiento.

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\cli_migrar.py` (extraer `_escribir`, `_contexto_yaml` y `_validar`)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\escritura.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\arquitectura.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\talend_item\padre_planificado.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\cli_migrar_comando.py` (opciones `--arquitectura` y `--limite-componentes`)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_calidad_corpus.py` (F1-5: Q3 y Q4 salen de `ABIERTAS`)
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_padre_planificado.py`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_migrar_planificado.py`

**Interfaces:**
- Consumes: `run_job(unico, hijo, proyecto, parametros=None, x=0, y=0, ruta_java=None) -> Nodo` (`jobs_diseno.py:42`); `al_terminar_subjob(origen, destino, n=1) -> Conexion` (`conexiones.py:27`); `segmentar`, `partir`, `aplicar_cortes` (F1-8, F1-10, F1-11); `plan_a_jobs(plan, esquemas, ruta_java=None) -> ResultadoMigracion`; `contextos_de_plan(plan)`; `disponer(job: Job) -> Job` (`talend_item/disposicion.py:74`); `validar_job(job) -> list[str]`; `migrar(source, out, esquemas=None, muestra=None, backend="archivos") -> ResultadoMigrar` (`cli_migrar.py:271`).
- Produces:
  ```python
  # talend_item/padre_planificado.py
  def padre_desde_segmentos(
      nombre: str,
      plan_de_jobs: PlanDeJobs,
      hijos: dict[str, Job],
      proyecto: str,
      ruta_java: str | None = None,
  ) -> Job:
      """Job padre: un `tRunJob` por segmento (el contexto completo se transmite), encadenados con
      `OnSubjobOk` en el orden de las oleadas; dentro de una oleada, en orden de nombre (la
      ejecución en paralelo no se emite). Los contextos del padre son la unión por nombre de los de
      los hijos, con las mismas claves en Default, DEV, QA y PROD."""

  # migrar/arquitectura.py
  ARQUITECTURAS = ("plana", "planificada")

  def migrar_planificado(
      plan: Plan, esquemas: dict[str, list[Column]], proyecto: str, limite: int = LIMITE_COMPONENTES
  ) -> tuple[ResultadoMigracion, PlanDeJobs, str]:
      """`segmentar` -> `partir` y `aplicar_cortes` (lazo: si un hijo emitido pasa del límite por
      los nodos de apoyo del emisor, se repite con `limite - exceso`, hasta 3 veces; después, el
      pendiente `P-JOB-EXCEDE-LIMITE` con el nombre del hijo) -> `plan_a_jobs` por segmento -> padre.
      Devuelve el resultado con los hijos y el padre al final, el plan de jobs y el nombre del padre."""

  # cli_migrar.py
  def migrar(source, out, esquemas=None, muestra=None, backend="archivos",
             arquitectura: str = "plana", limite_componentes: int = LIMITE_COMPONENTES,
             proyecto: str = "SGM") -> ResultadoMigrar: ...
  ```
  `ResultadoMigrar` gana `traza_por_job: dict[str, dict[str, list[int]]]` (el `traza` plano de hoy usa el `UNIQUE_NAME` del nodo, que se repite entre Jobs: `tMap_1` existe en cada hijo) y `padre: str | None`. Verificar al ejecutar de dónde toma `cli_talend.py` (línea 152) el nombre de proyecto del padre (`Arquitectura`); `proyecto="SGM"` es el valor por omisión mientras no haya otro.

- [ ] **Step 1: Extraer sin cambio de comportamiento.** Mover `_escribir`, `_contexto_yaml` y `_validar` de `cli_migrar.py` a `migrar/escritura.py` y dejar el `import`. Correr `tests/unit/test_cli_migrar.py`, `test_migrar_corpus_aceptacion.py` y `test_golden.py`: mismas pasadas que antes (anotar el conteo). `wc -l` de `cli_migrar.py`: menos de 300.
- [ ] **Step 2: Write the failing tests.** `test_padre_planificado.py`: con un `PlanDeJobs` de dos segmentos (el segundo depende del primero) y dos `Job` hijos, `padre_desde_segmentos` da un Job con dos `tRunJob`, una conexión `OnSubjobOk` del primero al segundo y `validar_job(padre) == []`; los contextos del padre tienen las mismas claves en los cuatro grupos. `test_migrar_planificado.py`: `migrar(caso_L8_totales, tmp_path, arquitectura="planificada")` deja más de un Job en `resultado.jobs`, `resultado.padre` es el último, `validar_job` no da defectos en ninguno, `q3_padre_por_dependencias` y `q4_tamano` no dan hallazgos, y `arquitectura="plana"` da lo mismo que hoy (mismos Jobs, mismos bytes).
- [ ] **Step 3: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_padre_planificado.py tests/unit/test_migrar_planificado.py -q -p no:cacheprovider`.
- [ ] **Step 4: Implement** `padre_desde_segmentos`, `migrar_planificado` y las dos opciones de la CLI (`--arquitectura plana|planificada`, `--limite-componentes N`, `--proyecto`). `migrar` escribe cada hijo y el padre en `<out>/<programa>/process/` con el mismo escritor que hoy y `trace.json` por Job con `traza_por_job` (F1-14 completa el contenido). La arquitectura `plana` no pasa por el planificador. Si el programa queda en un solo segmento, se emite ese Job sin padre.
- [ ] **Step 5: Run tests to verify they pass.** Quitar Q3 y Q4 de `ABIERTAS` en `test_calidad_corpus.py` y hacer que la prueba corra con `arquitectura="planificada"`; el tablero (`tools/calidad_jobs.py`) debe dar Q3 y Q4 al 100 % sobre el corpus; anotarlo en `PROGRESS.md`. Después correr la aceptación de los 101 casos con `planificada`: los pendientes de traducción tienen que ser los mismos de `migrar_pendientes.yaml` (el planificador no puede crear ni esconder pendientes).
- [ ] **Step 6: Run** `uv run ruff check src tests tools`. **Commit** `hito N m: padre por dependencias y migrar con arquitectura planificada`.

---

## Parte III. Errores, trazabilidad y reutilización (MG-P8-06, 07 y 03; serie `m`, 13 h)

### Task F1-13: Errores y registro por defecto, con política de fallo parcial (MG-P8-06; Q6 y Q7; serie `m`)

La decisión DC-08 (`ruta-a-produccion.md`, línea 82) tiene valor por omisión «falla todo» (`DIE_ON_CHILD_ERROR`). R2-07 ya probó los tres escenarios con `tools/prueba_fallo_producto.py` en los Jobs hechos a mano del padre de `sgm talend`; esta tarea lo hace por omisión en los Jobs que sale del planificador.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\talend_item\errores_registro.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\arquitectura.py` (F1-12: llamada a `con_errores_y_registro` sobre cada hijo y a `con_politica_de_fallo` sobre el padre)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_calidad_corpus.py` (Q6 y Q7 salen de `ABIERTAS`)
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_errores_registro.py`

**Interfaces:**
- Consumes: `nodo_desde_plantilla(componente, unico, x, y, valores, tablas, columnas, ruta_java)` (`talend_item/plantillas.py`; plantillas `tDie` con parámetros `MESSAGE`, `CODE`, `EXIT_JVM`; `tLogCatcher`; `tJava` con `CODE`; `tRunJob` con `DIE_ON_CHILD_ERROR`); `al_terminar_subjob`, `Conexion(origen, destino, nombre, conector, estilo, parametros, etiqueta)` (`conexiones.py`, `modelo.py`); `ParametroContexto` y los cuatro grupos de `Job.contextos`; `componentes(job)` (F1-1); `q6_errores`, `q7_registro` (F1-4).
- Produces:
  ```python
  @dataclass(frozen=True)
  class PoliticaErrores:
      fallo_parcial: str = "falla_todo"     # "falla_todo" | "continua" (DC-08)
      log_nivel: str = "INFO"               # valor de `context.log_nivel` en Default
      codigo_base: int = 20                 # EXIT CODE de `tDie`: codigo_base + n del subjob

  def politica_desde(decisiones: dict | None) -> PoliticaErrores:
      """Lee la clave `fallo_parcial` de `decisiones/<programa>.decisiones.yaml`; un valor que no
      es de los dos permitidos es un `ValueError` con el valor recibido."""
  def con_errores_y_registro(job: Job, politica: PoliticaErrores, ruta_java: str | None = None) -> Job:
      """Para cada subjob que escribe una salida (`tFileOutputDelimited`, `tFileOutputExcel`,
      `tImpalaRow`, ...): un `OnSubjobError` hacia un `tDie` con mensaje `"<job>: fallo en
      <subjob>"` y código propio; un `tLogCatcher` unido a un `tLogRow`; y, tras cada subjob que
      termina bien, un `tJava` que imprime `NB_LINE` del componente final si `context.log_nivel` no
      es `ERROR`. Suma el parámetro `log_nivel` (`id_String`) a los cuatro grupos de contexto."""
  def con_politica_de_fallo(padre: Job, politica: PoliticaErrores, ruta_java: str | None = None) -> Job:
      """`falla_todo`: cada `tRunJob` con `DIE_ON_CHILD_ERROR=true`. `continua`: en `false`, y el
      padre termina con código distinto de cero si algún hijo falló (un `tJava` que cuenta fallos en
      `globalMap` y un `tDie` en el postjob); nunca termina con código 0 habiendo fallado un hijo."""
  ```

- [ ] **Step 1: Write the failing test.** Un `Job` con dos subjobs, uno que escribe `tFileOutputDelimited` y otro que solo calcula: `con_errores_y_registro` agrega exactamente un `tDie` con `CODE` igual a `codigo_base + 1`, una conexión de conector `SUBJOB_ERROR` hacia él, un `tLogCatcher` y los `tJava` de registro; `q6_errores` y `q7_registro` no dan hallazgos y `validar_job` sigue vacío. `politica_desde({"fallo_parcial": "continua"}).fallo_parcial == "continua"`, `politica_desde(None).fallo_parcial == "falla_todo"` y `politica_desde({"fallo_parcial": "ignorar"})` lanza `ValueError`. Un padre de tres `tRunJob`: con `falla_todo` los tres tienen `DIE_ON_CHILD_ERROR=true`; con `continua`, `false` y hay un `tDie` en el postjob.
- [ ] **Step 2: Run test to verify it fails.** `uv run python -m pytest tests/unit/test_errores_registro.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement.** El `lineStyle` de `OnSubjobError` no está en `conexiones.py` (solo 1, 3, 6, 7 y 13 están verificados): confirmarlo con el fixture que deja F2-13 (referencia de Studio para los disparadores) o con un Job guardado por Studio, y copiar el valor al módulo con su fuente en un comentario; no escribir un número supuesto. Mientras no esté, el test usa el conector `SUBJOB_ERROR` y la tarea queda con «lote C pendiente».
- [ ] **Step 4: Run test to verify it passes.** Quitar Q6 y Q7 de `ABIERTAS` y comprobar el tablero (`tools/calidad_jobs.py`): Q6 y Q7 al 100 % sobre el corpus con `planificada`. Con Studio disponible: correr los tres escenarios de `tools/prueba_fallo_producto.py` sobre un programa planificado (hijo sin su archivo de entrada): con `falla_todo` el código de salida del padre es distinto de cero; con `continua`, el hijo siguiente corre y el padre sale distinto de cero. Si Studio no responde, «lote C pendiente» con el motivo.
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N m: errores y registro por defecto con politica de fallo parcial`.

---

### Task F1-14: Nombres únicos y `trace.json` completo (MG-P8-07; Q10; serie `m`)

`informes.trace_json` (`migrar/informes.py:202`) da por Job `nodo -> líneas del SAS`, y las claves son el `UNIQUE_NAME` del nodo, que se repite entre Jobs (`tMap_1` en cada hijo). Q10 pide además nombres legibles, únicos y una traza de **todos** los nodos. Las notas y las propiedades dentro del `.item` son de F2-16 (Plan F2); aquí va el informe y la convención de nombres.

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\informes.py` (312 líneas: `trace_json` se mueve a `trazabilidad.py` y se reexporta)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\trazabilidad.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\escritura.py` (F1-12: escribe el `trace.json` nuevo)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_calidad_corpus.py` (Q10 sale de `ABIERTAS`)
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_trazabilidad.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\docs\convencion-de-nombres.md`

**Interfaces:**
- Consumes: `trace_json(programa: str, jobs: list[Job], traza: dict[str, list[int]]) -> str` (`informes.py:202`); `Decision(regla, resumen, lineas, tabla)` (`optimizar/__init__.py:24`); `PlanDeJobs`, `Segmento` (F1-8); `ResultadoMigrar.traza_por_job` (F1-12); `nombre_legible` (F1-8); `q10_nombres` (F1-4).
- Produces:
  ```python
  APOYO = frozenset({"tPrejob", "tPostjob", "tDie", "tLogCatcher", "tLogRow", "tRunJob", "tJava"})

  def trace_completo(
      programa: str,
      jobs: list[Job],
      traza_por_job: dict[str, dict[str, list[int]]],
      decisiones: list[Decision],
      plan_de_jobs: PlanDeJobs | None = None,
      padre: str | None = None,
  ) -> dict:
      """Mantiene la forma `jobs[job][nodo] -> [líneas]` (quien la lee hoy no cambia) y agrega a la
      raíz: `version: 2`, `arquitectura` (`plana` o `planificada`), `padre`, `segmentos`
      ({nombre: {etapa, depende_de}}), `oleadas`, `decisiones` ({regla, lineas, resumen}) y
      `sin_traza` ({job: [nodo, ...]}) con los nodos sin línea de SAS que **no** son de apoyo.
      Ordenado y con `sort_keys`: dos corridas dan los mismos bytes (Q13)."""
  ```
  `docs/convencion-de-nombres.md` fija la convención: Job `<etapa>_<nn>_<tabla>` en minúsculas y `[a-z0-9_]`, padre `padre_<programa>`, variable de contexto `ruta_<tabla>`, y el `UNIQUE_NAME` de Talend para los nodos.

- [ ] **Step 1: Extraer sin cambio de comportamiento.** Mover `trace_json` a `trazabilidad.py` y reexportarlo desde `informes.py`. Antes: `Grep` de `trace.json` y `trace_json` en `tests/` y `tools/` para ver quién lo lee (`test_cli_migrar.py` y otros); la forma `jobs.<job>.<nodo> -> líneas` no cambia. Los tests de esos lectores siguen verdes; `wc -l informes.py` baja de 300.
- [ ] **Step 2: Write the failing test.** Con dos `Job` que tienen cada uno un `tMap_1` y trazas distintas (`{"j1": {"tMap_1": [10, 11]}, "j2": {"tMap_1": [40]}}`), `trace_completo(...)["jobs"]["j2"]["tMap_1"] == [40]` (no se mezclan), `["version"] == 2`, y un nodo `tFileInputDelimited_2` sin línea queda en `sin_traza["j1"]`, pero un `tRunJob_1` y un `tDie_1` no. `json.dumps(..., sort_keys=True)` de dos llamadas con el mismo argumento es idéntico.
- [ ] **Step 3: Run test to verify it fails.** `uv run python -m pytest tests/unit/test_trazabilidad.py -q -p no:cacheprovider`.
- [ ] **Step 4: Implement** `trace_completo` y escribirlo desde `escritura.py`. Con `arquitectura="plana"` el `trace.json` conserva sus claves de siempre más las nuevas.
- [ ] **Step 5: Run test to verify it passes.** Quitar Q10 de `ABIERTAS`: `q10_nombres` da cero hallazgos sobre el corpus con `planificada` y el escrito de `sin_traza` está vacío salvo los nodos de apoyo. Los nodos de un hijo creado por un corte (`write_file`/`read_file` de F1-11) heredan la línea del operador que cruzaba, para que no queden sin traza; si no la heredan, se arregla en `aplicar_cortes` (F1-11), no se agregan a `APOYO`.
- [ ] **Step 6: Run** `uv run ruff check src tests tools`. **Commit** `hito N m: nombres unicos y trace.json completo por Job`.

---

### Task F1-15: Bloques repetidos a joblet, con `tRunJob` como plan B (MG-P8-03; Q5; serie `m`)

Hoy las plantillas repetidas se despliegan en línea (`plan_desplegado`, `ir/desplegar.py:17`) y `p07_templates.py` registra cada bloque en `plan.joblets` (claves `id`, `etiquetas`, `operaciones`, `apariciones`, `parametros`, `instancias`, `fuente`) y la llamada como un operador `iterate` (`iterar(op_id, template, instancias)`, `ir/operadores.py:355`; el original queda en `plan.iteraciones[iterate_id]` con `operadores` y `aristas`). Esta tarea decide, por bloque, si se extrae y cómo.

**Depende de otros planes** (ver `Dependencias`): E-10 (`detectar_repeticiones`, `informe_a_dict`; informe de bloques repetidos de las macros), F2-8 (`joblet_desde_nodos`, `nodo_joblet`) y F2-9 (`decidir`, `BloqueReutilizable`, `nodo_job_hijo`).

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\ir\desplegar.py` (parámetro `conservar` con valor por omisión que no cambia nada)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\planificador\reutilizacion.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\planificador\extraer.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\arquitectura.py` (F1-12: el paso de reutilización antes de `segmentar`)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_calidad_corpus.py` (Q5 sale de `ABIERTAS`)
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_planificador_reutilizacion.py`

**Interfaces:**
- Consumes: `plan_desplegado(plan: Plan) -> tuple[Plan, set[str]]` (`ir/desplegar.py:17`); `decidir(bloque: BloqueReutilizable, capacidades: dict[str, bool]) -> str` (`"joblet"` o `"job_hijo"`), `BloqueReutilizable(nombre, entradas_de_fila, salidas_de_fila, tiene_subjobs_propios, necesita_contexto_propio, se_ejecuta_solo)`, `nodo_job_hijo(unico, hijo, contexto_padre) -> Nodo`, `capacidades() -> dict[str, bool]` (F2-9); `joblet_desde_nodos(nombre, entrada, salida, nucleo, conexiones, parametros) -> Job` y `nodo_joblet(unico, joblet, valores) -> Nodo` (F2-8); `detectar_repeticiones(analysis) -> list[BloqueRepetido]` e `informe_a_dict(bloques) -> dict` con clave `version: 1` y `bloques[].{origen, macro, huella, parametros_variables, parametros_fijos, invocaciones, candidata_joblet}` (E-10).
- Produces:
  ```python
  # ir/desplegar.py
  def plan_desplegado(plan: Plan, conservar: frozenset[str] = frozenset()) -> tuple[Plan, set[str]]:
      """Igual que hoy, salvo que los `iterate` de `conservar` quedan sin desplegar."""

  # planificador/reutilizacion.py
  @dataclass(frozen=True)
  class BloqueExtraido:
      iterate_id: str
      nombre: str                    # `macro` del informe de E-10 si coincide; si no, `util_<n>`
      decision: str                  # "joblet" | "job_hijo"
      parametros: tuple[str, ...]    # los que varían entre instancias: pasan a contexto
      instancias: int

  def bloques_a_extraer(
      plan: Plan, repeticiones: dict | None, capacidades: dict[str, bool]
  ) -> list[BloqueExtraido]:
      """Todo `iterate` con 2 o más instancias. El nombre sale del informe de repeticiones de las
      macros (E-10) cuando una invocación cae en las líneas de la evidencia del bloque; la
      decisión, de `decidir`."""

  # planificador/extraer.py
  def extraer_bloque(plan: Plan, bloque: BloqueExtraido) -> Segmento:
      """El cuerpo (de `plan.iteraciones[bloque.iterate_id]`) como sub-plan propio; en el padre,
      una llamada por instancia con sus parámetros de contexto (`tRunJob` o nodo de joblet)."""
  ```

- [ ] **Step 1: Write the failing tests.** (a) Con un plan armado a mano de dos instancias de la misma plantilla que varían en un parámetro, `bloques_a_extraer(plan, None, {"joblet_desde_archivo": False})` devuelve un bloque con `decision == "job_hijo"` e `instancias == 2`; con `{"joblet_desde_archivo": True}` y un bloque con una entrada y una salida de fila y sin subjobs propios, `"joblet"`. Con un informe de repeticiones `{"version": 1, "bloques": [{"macro": "cargar_mes", "candidata_joblet": True, "invocaciones": [{"linea": 12}, {"linea": 30}], ...}]}` y la evidencia del bloque en esas líneas, `nombre == "cargar_mes"`. (b) `plan_desplegado(plan, conservar=frozenset({id}))` deja ese `iterate` en el grafo y sin él es idéntico a hoy (golden). (c) Con un programa del corpus con repeticiones (buscar con `Grep` de `iterate` en los planes de `tests/corpus/L5`; si ninguno, usar `tests/corpus/L5/l5_11*` o el primero que traiga `plan.joblets`), `migrar(..., arquitectura="planificada")` deja un Job utilitario único y `q5_joblets_repetidos` no da hallazgos; con la arquitectura `plana` el mismo programa conserva el despliegue en línea y su Job no cambia.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_planificador_reutilizacion.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement.** Verificar al ejecutar la forma exacta de cada elemento de `instancias` (`Grep` de `instancias` en `src/sgm/passes/p07_templates.py` y en `ir/operadores.py:355`) antes de mapear los parámetros a variables de contexto. El plan B (`job_hijo`) es el camino por omisión mientras `capacidades()["joblet_desde_archivo"]` sea `False`; el camino `joblet` se escribe y se prueba pero no se activa hasta que F2-8 Step 1 lo confirme en Studio.
- [ ] **Step 4: Run tests to verify they pass.** Quitar Q5 de `ABIERTAS`. Con Studio disponible, compilar y ejecutar el caso del paso 1(c) con `tools/validar_caso_studio.py <caso>`; si Studio no responde, «lote C pendiente» con el motivo, y Q5 no se cuenta como cerrado en el Gate.
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N m: bloques repetidos a joblet o Job hijo desde el planificador`.

---

## Parte IV. Optimizador del diseño: lo que queda de MG-P8b (serie `m`, 6 h)

Las cuatro tareas siguen la regla del plan maestro para el optimizador: la equivalencia se comprueba con el intérprete contra `esperado/` y sin Studio (`tests/unit/test_optimizar_corpus.py`); Studio solo valida la ejecución al final.

### Task F1-16: Fundir DATA step encadenados con `KEEP`, `DROP` y `RENAME` en el productor (MG-P8b-05; serie `m`)

El hito 155m dejó el límite escrito: los modificadores en el productor evitan la fusión porque falta modelar la interfaz de columnas que ve el consumidor. Hoy `optimizar.cadenas.fundir` lanza `NoFusionable` y los dos DATA step quedan como dos `tMap` con una tabla de `WORK` en medio.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\optimizar\interfaz.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\optimizar\cadenas.py` (173 líneas; usa `interfaz` en `_pasos_fundidos`)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\L1\l1_17_data_steps_modificadores_en_productor\{caso.yaml, programa.sas, entradas\ventas.csv, esperado\final.csv}`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\rules\sas\catalogo\procs-usados.yaml` o el YAML de `rules/sas/catalogo/` que cubra opciones de data set (comprobar con `Grep` de `KEEP` en esa carpeta; actualizar `estado` y `fuente: ledsoptsref.pdf, p. 57`, entrada del índice «KEEP= Data Set Option (p. 57)»)
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_optimizar_interfaz.py`

**Interfaces:**
- Consumes: `Forma(uniones, filtros, proyeccion, selecciones, renombrados)`, `forma_de(op: Operator) -> Forma`, `NoFusionable` (`optimizar/forma.py`); `fundir(plan, a_id, lecturas_de) -> tuple[str, list[str], str | None]` (`cadenas.py:130`); `primero_de`, `reescribir(texto, primero, segundo_cruza)` (`reescribir.py`); `optimizar(plan) -> tuple[Plan, Informe]`.
- Produces:
  ```python
  @dataclass(frozen=True)
  class Interfaz:
      visibles: tuple[str, ...]             # columnas que el consumidor puede nombrar, en orden
      renombres: dict[str, str]             # nombre que ve el consumidor -> nombre en el productor

  def interfaz_de(forma: Forma) -> Interfaz | None:
      """Columnas que deja un productor con `KEEP`/`DROP`/`RENAME`. `None` si no se pueden
      demostrar (una columna no declarada, un `DROP` de algo que no existe)."""
  def referencia_valida(expresion: str, interfaz: Interfaz) -> bool:
      """Falso si la expresión del consumidor nombra una columna que el productor quitó: el SAS la
      leería como faltante y el `tMap` fundido no, y esa diferencia no se esconde."""
  ```

- [ ] **Step 1: Write the failing tests.** Caso `l1_17_data_steps_modificadores_en_productor` (`capa: C`, `estado: traducible`, `orden_relevante: true`, `razonamiento` con el mismo texto que `l1_16` y la página de `KEEP=`): `programa.sas` con un `PROC IMPORT` a `WORK.ventas`, `DATA WORK.calculada(KEEP=id monto RENAME=(monto=base)); SET WORK.ventas; doble = monto * 2; RUN;`, `DATA WORK.final; SET WORK.calculada; total = base + 1; RUN;` y un `PROC EXPORT` de `final`. `ventas.csv` = `id,monto` / `1,10` / `2,20`. Esperado: `final.csv` = `id,base,total` / `1,10,11` / `2,20,21`. Antes de escribirlo, confirmar en `docs/referencia/sas/ledsoptsref.txt` (página 57 y la entrada de `RENAME=` del `.INDEX.md`) el orden en que SAS aplica `KEEP` y `RENAME`; si la página no lo dice, el caso queda `estado: pendiente` con ese motivo. En `test_optimizar_interfaz.py`: `referencia_valida("doble + 1", Interfaz(("id", "base"), {"base": "monto"}))` es `False` y `referencia_valida("base + 1", ...)` es `True`; el plan de `l1_17` optimizado tiene **un** `map` y no `write`/`read` de `WORK.calculada`.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_optimizar_interfaz.py tests/unit/test_optimizar_corpus.py -q -p no:cacheprovider -k "interfaz or l1_17"`; esperado: `NoFusionable` (hoy no se fusiona).
- [ ] **Step 3: Implement** `interfaz_de` y usarla en `_pasos_fundidos`: las referencias del consumidor a un nombre renombrado se sustituyen por el nombre del productor con `sustituir` (`optimizar/sustituir.py`), y una referencia a una columna quitada lanza `NoFusionable("el segundo paso nombra `doble`, que el primero quita")`. El `KEEP`/`RENAME` del propio consumidor se conserva en la salida, como hoy hace `l1_16`.
- [ ] **Step 4: Run tests to verify they pass**, y `tests/unit/test_optimizar_corpus.py` completo: `l1_16` y todos los demás idénticos; el plan optimizado de `l1_17` ejecutado con el intérprete da `esperado/final.csv`. Un segundo caso negativo en el test unitario (el consumidor usa `doble`) no se fusiona y queda como hoy.
- [ ] **Step 5: Run** `uv run ruff check src tests tools` y `tests/unit/test_catalogo_sas.py`. **Commit** `hito N m: fusion de DATA step con KEEP, DROP y RENAME en el productor`.

---

### Task F1-17: Hermanos sobre la misma fuente: validar en Studio la ejecución (MG-P8b-06; serie `m`)

El hito 158m dejó `l2_07`, `l2_10` y `l3_05` sin `tReplicate`: un `tMap` con varias salidas filtradas y, en `l2_07`, el rechazo del cruce como salida de `NOT IN`. Falta lo que el plan maestro pide como aceptación: que el Job **ejecute** en Studio y dé las mismas tablas que `esperado/`.

**Files:**
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_hermanos_sin_replicate.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\PROGRESS.md` (resultado del lote)

**Interfaces:**
- Consumes: `migrar(...)` (`cli_migrar.py:271`); `validar_job(job)`; `Nodo.componente`; `tools/validar_caso_studio.py <caso>` y `tools/corpus_studio.py lote ...`; casos `tests/corpus/L2/l2_07_not_in_subconsulta`, `tests/corpus/L2/l2_10_is_missing_numerico_y_texto` y `tests/corpus/L3/l3_05_having_conteo`.
- Produces: la prueba `test_hermanos_sin_replicate(caso)`, que exige, por caso: ningún nodo `tReplicate`, un único `tMap` (o `tAggregateRow` más un `tMap`, en `l3_05`) con tantas salidas como tablas finales del caso, `validar_job == []`.

- [ ] **Step 1: Write the failing test.** Parametrizada por los tres casos; esperado hoy: pasa o falla según lo que dejó el hito 158m. Si ya pasa, el test se agrega igual (fija la forma) y se sigue con el paso 3.
- [ ] **Step 2: Run test.** `uv run python -m pytest tests/unit/test_hermanos_sin_replicate.py -q -p no:cacheprovider`. Si falla, el hallazgo se arregla en `optimizar/ramas.py` (243 líneas; no más de 300: si el arreglo lo pasa, extraer primero) con la prueba de forma que corresponda, no aquí.
- [ ] **Step 3: Validar en Studio.** `uv run python tools/validar_caso_studio.py l2_07_not_in_subconsulta l2_10_is_missing_numerico_y_texto l3_05_having_conteo` (necesita `sgm studio salud` en verde; si no conecta, no reinstalar nada: «lote C pendiente» con el motivo y la tarea sigue abierta).
- [ ] **Step 4: Anotar** en `PROGRESS.md` por caso: compila, ejecuta, filas por salida y si coincide con `esperado/`. Una diferencia no se arregla en el esperado: se abre un `xfail` estricto con el hallazgo.
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N m: hermanos sobre la misma fuente validados en Studio`.

---

### Task F1-18: `tHashOutput` y `tHashInput` para ramas que reconvergen (MG-P8b-07; serie `m`)

El plan maestro dejó esta tarea bloqueada porque `tHashInput` no entregaba filas en la topología probada del MCP (INTERNALS 70). El Plan A, tarea A-5, la **resolvió en el hito 193**: el enlace salía del `tHashOutput`, y eso es un diseño inválido; se cuelga del `tFixedFlowInput` de arranque, que lleva `schemaDespuesDeConectar`. Esta tarea usa ese diseño en el emisor propio. El hash vale solo dentro de un Job (F1-11 no lo usa entre Jobs).

**Depende de:** Plan A, A-5 (hecha). **Excepción a la regla de no tocar `desde_plan.py`:** el bloque del pendiente (`desde_plan.py:615-625`, unas diez líneas) se sustituye por una llamada a un módulo nuevo; el archivo no crece. Plan K, K-4, también modifica `desde_plan.py`: quien llegue segundo hace rebase.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\talend_item\desde_plan_hash.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\talend_item\desde_plan.py` (solo `_repartos`, el bloque `if self._reconvergen(consumidores):` de la línea 614; la constante `RECONVERGE` se queda para el caso en que `desde_plan_hash` devuelve `None`)
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_desde_plan_hash.py`

**Interfaces:**
- Consumes: `nodo_desde_plantilla(...)` con `tHashOutput` (parámetros `LINK_WITH`, `LIST`, `DATA_WRITE_MODEL`, `KEYS_MANAGEMENT`, `APPEND`) y `tHashInput` (`LINK_WITH`, `LIST`, `RELEASE_CACHE`); `al_terminar_subjob`; `Columna`; la prueba de A-5 en `talend-mcp` (escenario `transformaciones/hash-memoria-entre-subjobs`) y `docs/studio-internals/70` (verificar al ejecutar la forma exacta de las conexiones: quién dispara a quién y por qué el `tFixedFlowInput` de arranque).
- Produces:
  ```python
  def reparto_con_hash(
      origen: Nodo,
      columnas: list[Columna],
      consumidores: list[str],
      unico: Callable[[str], str],
      ruta_java: str | None,
  ) -> tuple[list[Nodo], list[Conexion], dict[str, str]] | None:
      """`tHashOutput` tras el origen (un cache con nombre propio en `LINK_WITH`) y un `tHashInput`
      por consumidor, que lee ese cache con las mismas columnas, en subjobs que arrancan con
      `OnSubjobOk` tras el del origen. Devuelve los nodos nuevos, las conexiones y
      `consumidor -> unico del tHashInput` para que `_repartos` re-enganche cada consumidor.
      `None` si el consumidor no es un componente de flujo."""
  ```

- [ ] **Step 1: Medir.** `uv run python -m sgm.cli migrar tests/fixtures/sas/client/client_large.sas --out out/cl-f1` y contar en `out/cl-f1/client_large/pendientes.md` las apariciones de `P-REPARTO-RECONVERGE` (el hito 163m anotó las líneas 1384 y 1554). Es el denominador de la aceptación.
- [ ] **Step 2: Write the failing test.** Con un plan sintético donde un `read_file` alimenta dos pasos que luego se unen con un `join`: hoy `plan_a_jobs` deja el pendiente `P-REPARTO-RECONVERGE`; esperado nuevo: sin ese pendiente, un `tHashOutput` y dos `tHashInput` con el mismo `LINK_WITH`, los dos `tHashInput` con las columnas del origen, y `validar_job == []`. Un origen que es una lectura de archivo sigue resolviéndose «una lectura por rama» (comportamiento de `_instancias`, no cambia).
- [ ] **Step 3: Run test to verify it fails.** `uv run python -m pytest tests/unit/test_desde_plan_hash.py -q -p no:cacheprovider`.
- [ ] **Step 4: Implement** `reparto_con_hash` y la llamada desde `_repartos`. Sin tocar nada más de `desde_plan.py`.
- [ ] **Step 5: Run test to verify it passes**, más `tests/unit/test_migrar_corpus_aceptacion.py` (los `pendientes` que cambian son los de `P-REPARTO-RECONVERGE` y nada más: `migrar_pendientes.yaml` se actualiza solo con eso). Con Studio: compilar y ejecutar el caso sintético con `tools/validar_caso_studio.py`; si los dos `tHashInput` no entregan filas, se vuelve al pendiente con su motivo y se anota en `PROGRESS.md` (la tarea queda «lote C pendiente», no cerrada).
- [ ] **Step 6: Run** `uv run ruff check src tests tools`. **Commit** `hito N m: tHashOutput y tHashInput para ramas que reconvergen`.

---

### Task F1-19: Cálculo en la base con conexión por contexto, dentro de la arquitectura planificada (MG-P8b-08; serie `m`)

El hito 164m dejó `tImpalaRow` compilando con SQL calificado; la conexión y la ejecución quedaron pendientes. El Plan K, K-4, saca `HOST`, `PORT` y `DBNAME` al contexto y trae el grupo `DEV` del contenedor. Esta tarea cierra la parte que le toca al planificador: un corte entre dos operadores que ya están en la base no pasa por un archivo, y el Job resultante cumple Q1.

**Depende de:** Plan K, K-4 (`parametros_conexion(en_contexto=True)`, `contextos_de_plan(plan, dev)`).

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\planificador\traspaso.py` (F1-11: la rama `conexion` ya existe; aquí se prueba con el caso real)
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_calculo_en_base_planificado.py`

**Interfaces:**
- Consumes: `mecanismo_de(corte, plan, decididos=None) -> str` (F1-11); `parametros_conexion(en_contexto: bool) -> dict[str, str]`, `VARIABLES_BASE` (K-4); `q1_nada_fijo` (F1-2); caso `tests/corpus/L2/l2_16_sql_en_misma_base`; `placement` `db:impala` de `Operator`.
- Produces: la prueba `test_corte_en_la_base_no_usa_archivo`, y el criterio en `calidad/contexto.py` (F1-2) de que un `tImpalaRow` cuyo `HOST` es un literal es hallazgo `Q1`.

- [ ] **Step 1: Write the failing test.** Con `l2_16_sql_en_misma_base` migrado con `arquitectura="planificada"` y `limite=2` (para forzar un corte entre dos `exec_sql`), `mecanismo_de` devuelve `"conexion"`, los Jobs no contienen `tFileOutputDelimited` de traspaso, el `tImpalaRow` tiene `HOST` igual a `context.impala_host` y `q1_nada_fijo` no da hallazgos; con el contexto de K-4 apagado (`en_contexto=False`) el `HOST` literal da un hallazgo `Q1`.
- [ ] **Step 2: Run test to verify it fails.** `uv run python -m pytest tests/unit/test_calculo_en_base_planificado.py -q -p no:cacheprovider`; si K-4 no está integrado, la prueba se marca `skip` con ese motivo y se anota en `PROGRESS.md`; no se simula K-4.
- [ ] **Step 3: Implement** lo que falte en `traspaso.py` y `calidad/contexto.py` (el criterio Q1 sobre `tImpalaRow`).
- [ ] **Step 4: Run test to verify it passes.** Con el contenedor de Impala arriba (`tools/contenedores/`, ver K-3 y K-4): ejecutar el caso con `DEV` y anotar en `PROGRESS.md` las filas de la tabla destino. Sin contenedor o sin Studio: «lote C pendiente» con el motivo.
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N m: cortes en la base sin archivo y conexion por contexto en la arquitectura planificada`.

---

## Parte V. Compuerta

### Task F1-Gate: Arquitectura planificada por omisión y Q1 a Q15 al 100 % (MG-P8 cierre, GM4 parte del planificador; serie `m`)

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\cli_migrar.py` y `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\cli_migrar_comando.py` (el valor por omisión de `--arquitectura` pasa a `planificada`)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_calidad_corpus.py` (`ABIERTAS` queda vacía o con solo Q14 y lo que Studio no pudo)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_golden.py`, `test_cli_migrar.py` y los que fijen la conducta por omisión (cada uno pasa `arquitectura="plana"` y gana una gemela con `planificada`: no se pierde cobertura)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\docs\plan-reescritura\plan-migrador-general.md` (filas MG-P8-01 a 07 y MG-P8b-05 a 08, tabla 11b y GM4)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\docs\plan-reescritura\plan.md` (tabla «Estado por fase»)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\PROGRESS.md`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_gate_f1.py`

**Interfaces:**
- Consumes: `evaluar(programas, trabajo, arquitectura)` y `porcentaje(tablero)` (F1-5); `diseno_de_programa(...)` (F1-9); `migrar(...)` (F1-12); `tools/corpus_studio.py lote ...`.
- Produces: `test_gate_f1.py` con tres pruebas: `test_q1_a_q15_al_cien_por_cien_en_el_corpus` (cada criterio, salvo los de una lista `LOTE_C` con su motivo, da `hallazgos == 0` sobre los casos de `L0` a `L3` y `L8` que `migrar_pendientes.yaml` no lista), `test_diseno_sin_yaml_en_todo_el_corpus` (F1-9 sobre `L1` a `L8` y `tests/fixtures/sas`, sin `decisiones/*.agrupacion.yaml`) y `test_ningun_job_pasa_de_veinte_componentes`.

- [ ] **Step 1: Medir.** `uv run python tools/calidad_jobs.py` con `--arquitectura planificada`: la tabla de Q1 a Q15 y su porcentaje. Todo criterio por debajo de 100 % se explica con su tarea, o se arregla ahora.
- [ ] **Step 2: Cambiar el valor por omisión** a `planificada` y arreglar los tests que fijaban la conducta anterior como se dijo en `Files`. Correr la aceptación (`test_migrar_corpus_aceptacion.py`): los casos con pendientes de traducción son los mismos de `migrar_pendientes.yaml`.
- [ ] **Step 3: Write the Gate test** y correrlo: `uv run python -m pytest tests/unit/test_gate_f1.py -q -p no:cacheprovider`.
- [ ] **Step 4: Lote C.** Con `sgm studio salud` en verde: `tools/corpus_studio.py lote` sobre `L0` a `L3` y `L8` con la arquitectura planificada, y compilar el padre y sus hijos de un programa de `L8`. Las compilaciones que fallan se anotan con su Job y su motivo; un lote parcial no cierra la compuerta. Si Studio no conecta: «lote C pendiente» con el motivo, la compuerta queda abierta en lo que Studio demuestra (Q14, F1-13, F1-15, F1-17, F1-18, F1-19) y cerrada en el resto, y se dice así en `PROGRESS.md`.
- [ ] **Step 5: Actualizar los documentos.** Estado de las filas MG-P8-01, 02, 03, 05, 06, 07 y MG-P8b-05 a 08 en `plan-migrador-general.md`; recalcular el porcentaje de la sección 11b con su método (horas acreditadas por fase; no inventar un porcentaje); `plan.md` y `PROGRESS.md` con fecha, cifras de la medida del Step 1, pruebas, bloqueos y decisiones. Dejar la lista `LOTE_C` con su motivo en la entrada.
- [ ] **Step 6: Run** suite completa `uv run python -m pytest -q` y `uv run ruff check src tests tools`. **Commit** `hito N m: F1-Gate arquitectura planificada por omision y Q1 a Q15 medidos` (con la línea `Co-Authored-By`).

---

## Dependencias

| Tarea de este plan | Necesita | Dónde | Si no está |
|---|---|---|---|
| F1-3 (Q11 pasa) | Disposición por subjobs sin superposición | Plan F2, F2-15 | Q11 queda en `ABIERTAS` con ese motivo |
| F1-4 (Q10, Q14) | Propiedades y notas en el `.item`; ida y vuelta en Studio | Plan F2, F2-16 y F2-19 | Q14 devuelve `pendiente: lote C`; las notas dentro del `.item` no son de este plan |
| F1-13 | Referencia de Studio para `OnSubjobError` (`lineStyle`) | Plan F2, F2-13 | el test usa el conector `SUBJOB_ERROR`; la tarea queda «lote C pendiente» |
| F1-15 | Informe de bloques repetidos `informe_a_dict` (E-10) | Plan E, E-10 | el bloque se nombra `util_<n>`, sin el nombre de la macro |
| F1-15 | `joblet_desde_nodos`, `nodo_joblet` (F2-8) y `decidir`, `nodo_job_hijo`, `capacidades` (F2-9) | Plan F2 | no se puede escribir `reutilizacion.py`: la tarea espera a F2-9. Si F2-8 no confirma la carga de joblets, `capacidades()["joblet_desde_archivo"]` es `False` y el camino por omisión es el Job hijo |
| F1-18 | `tHashInput` que entrega filas | Plan A, A-5 (hecha, hito 193) | pendiente `P-REPARTO-RECONVERGE`, como hoy |
| F1-18 | modifica `desde_plan.py` (excepción: solo sustituye el bloque del pendiente) | Plan K, K-4 también lo modifica | quien llegue segundo hace rebase sobre el otro |
| F1-12 | modifica `cli_migrar.py` y `cli_migrar_comando.py` | Plan K, K-4 (`--contexto-dev`) | quien llegue segundo hace rebase; F1-12 extrae `escritura.py` primero |
| F1-19 | `parametros_conexion`, `contextos_de_plan(plan, dev)` | Plan K, K-4 | la prueba se marca `skip` con ese motivo |
| F1-Gate (lote C) | Studio y el Gate del Plan F2 (F2-20, arquitectura con contextos y joblets) | Plan F2 | el Gate de F1 se cierra en lo que no necesita Studio |

El Plan F1 no necesita nada de los Planes B, C ni D: no toca `desde_plan_map.py`, `interprete.py` ni el frontend. Los casos de SQL o de DATA step que esos planes agreguen al corpus entran solos en Q1 a Q15 y en la segmentación.

## Self-review

- **Cobertura del alcance pedido.** MG-P8-01 = F1-6 a F1-9 y F1-12; MG-P8-02 = F1-10 y F1-12; MG-P8-03 = F1-15; MG-P8-05 = F1-11; MG-P8-06 = F1-13; MG-P8-07 = F1-14; Q1 a Q15 como pruebas = F1-2 a F1-5; MG-P8b-05 = F1-16; MG-P8b-06 = F1-17; MG-P8b-07 = F1-18; MG-P8b-08 = F1-19; cierre = F1-Gate. MG-P8-04 (contextos por programa) ya está hecho (hito 104m) y no se repite.
- **Interfaces copiadas del código real** (a mayo de este plan): `diseno_de_programa`, `plan_a_jobs`, `migrar`, `optimizar`, `plan_desplegado`, `run_job`, `al_terminar_subjob`, `validar_job`, `render_item`, `leer_archivo`, `escribir_archivo`, `contextos_de_plan`, `rutas_de_plan`, `trace_json`, `Forma`, `fundir`, `Job`, `Nodo`, `Conexion`, `ParametroContexto`, `Plan`, `Graph`, `Edge`. Las de F2, E y K se citan tal como las describen sus planes y se verifican al integrar.
- **Cosas que se verifican al ejecutar, no se suponen:** los nombres de `Operator.kind` (F1-7), el nombre del parámetro de lookups de `map` (F1-10), cómo nombra `ejecutar_plan` las entradas de un `read_file` (F1-11), el `lineStyle` de `OnSubjobError` (F1-13), el nombre del proyecto del padre (F1-12), la forma de cada elemento de `instancias` (F1-15), el orden de aplicación de `KEEP` y `RENAME` (F1-16) y el esquema de conexiones del hash (F1-18).
- **Decisiones tomadas aquí** (anotar en `PROGRESS.md`, «Decisiones», al ejecutar): (1) el límite de componentes es 20 y se cuenta sin `tPrejob` ni `tPostjob`; (2) dentro de una oleada los hijos van en secuencia, no en paralelo (el paralelo entre hijos que comparten una conexión de base no está demostrado); (3) entre Jobs el traspaso es un archivo `trabajo/<tabla>.csv` con la variable `ruta_<tabla>`; (4) un programa con un solo segmento se emite como un Job sin padre (el padre de un solo hijo no agrega orquestación); `sgm diseno` sí lo describe con un hijo; (5) la política de fallo parcial por omisión es `falla_todo`; (6) la arquitectura `plana` se conserva como opción, no se borra.
- **Sin marcadores sin decidir:** cada paso trae el valor, el comando o la firma; lo que depende de otro plan está en `Dependencias` con su alternativa.
- **Archivos de menos de 300 líneas:** los módulos nuevos se mantienen bajo ese tamaño; `cli_migrar.py` e `informes.py` se parten en F1-12 y F1-14; `desde_plan.py` solo cambia en F1-18, y solo sustituye líneas por una llamada.
- **Nombres de scripts del cliente:** ninguna regla ni nombre de `src/` los usa; los casos del corpus que se citan son nombres de caso (`l2_16_...`), no de script.

## Resumen de horas

| Tarea | Horas | Del plan maestro |
|---|---:|---|
| F1-1 línea base | 1 | MG-P8-01 |
| F1-2 modelo y Q1, Q2, Q12 | 2 | MG-P8-06/07 (Q) |
| F1-3 Q4, Q8, Q9, Q11, Q15 | 3 | MG-P8-06/07 (Q) |
| F1-4 Q3, Q5, Q6, Q7, Q10, Q13, Q14 | 3 | MG-P8-06/07 (Q) |
| F1-5 tablero Q1 a Q15 sobre el corpus | 2 | MG-P8-06/07 (Q) |
| F1-6 regiones y dependencias | 3 | MG-P8-01 |
| F1-7 etapas | 3 | MG-P8-01 |
| F1-8 segmentación | 6 | MG-P8-01 |
| F1-9 `sgm diseno` sin YAML | 2 | MG-P8-01 |
| F1-10 política de tamaño | 5 | MG-P8-02 |
| F1-11 traspaso entre Jobs | 4 | MG-P8-05 |
| F1-12 padre y `migrar --arquitectura` | 6 | MG-P8-01 y 02 |
| F1-13 errores y registro | 4 | MG-P8-06 |
| F1-14 nombres y `trace.json` | 3 | MG-P8-07 |
| F1-15 joblets y Job hijo | 6 | MG-P8-03 |
| F1-16 DATA step con modificadores | 2 | MG-P8b-05 |
| F1-17 hermanos validados en Studio | 1 | MG-P8b-06 |
| F1-18 `tHash*` en reconvergencia | 2 | MG-P8b-07 |
| F1-19 cálculo en la base | 1 | MG-P8b-08 |
| F1-Gate | 2 | MG-P8 cierre |
| **Total** | **61** | MG-P8 restante 55 h + MG-P8b restante 6 h |
