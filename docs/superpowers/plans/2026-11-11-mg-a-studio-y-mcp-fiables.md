# MG-A: Studio y `talend-mcp` fiables Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Que ninguna validación en Studio se pierda ni bloquee el trabajo: Studio se detecta, se recupera o se declara caído en menos de 30 s, las validaciones pendientes quedan en cola, y el MCP resuelve los dos huecos técnicos que frenan el emisor (`tHashInput` y joblets).

**Architecture:** Cambios en dos repositorios. En `talend-mcp` (TypeScript, Bun; autorizado por el usuario el 11 de noviembre de 2026) se añade una máquina de estados de Studio, una herramienta `talend_studio_ensure_ready`, y las herramientas de joblet con prueba L5. En `sgm-v2` (Python) la salud llama a esa herramienta, y el arnés `corpus_studio.py` guarda en cola lo que no pudo validar. El núcleo de `sgm` sigue sin depender del MCP: todo pasa por `src/sgm/backend_talend/`.

**Tech Stack:** Bun + `bun test` + TypeScript (talend-mcp); Python 3.12 + pytest + ruff + `uv run python -m pytest` (sgm-v2).

**Spec:** `docs/plan-reescritura/plan-migrador-general.md` (MG-P0-02, MG-P0-08, MG-P8b-07, MG-P9-03) y `docs/superpowers/plans/2026-11-11-ruta-al-100.md` (Plan A).

## Global Constraints

- Sin `git push`. Commits locales: en `sgm-v2` `hito N<letra>: <resumen>`; en `talend-mcp` el estilo del repositorio (`feat(studio): ...`, `fix(bridge): ...`).
- No reinstalar Studio ni matar procesos de Studio salvo con `force` explícito y registrado; `talend_studio_restart` ya cierra con `CloseMainWindow` y espera 120 s (`CLOSE_WAIT_MS`).
- No copiar `mcp/`, `contract/` ni `talend_adapter/` del repositorio viejo; no agregar la dependencia Python `mcp`; no crear `.mcp.json` en `sgm-v2`.
- El núcleo de `sgm` no importa el MCP fuera de `src/sgm/backend_talend/`; lo vigila `tests/unit/test_backend_aislado.py`.
- Ningún secreto en líneas de comandos ni registros.
- Archivos de menos de 300 líneas; código en inglés, comentarios y mensajes en español.
- En Windows: `uv run python -m pytest` y `uv run python -m sgm.cli`, no `uv run pytest`.
- Siguiente número de hito: 191 (revisar el último `## Hito` de `PROGRESS.md` antes de escribir).
- Todo lo que no se pueda ejecutar en Studio se anota como pendiente con su motivo; no se cuenta como validado.

## Review Focus

- Studio abierto con el bridge mudo (puertos 3927 y 3930 sin escuchar): debe dar `BRIDGE_DEAD` en menos de 30 s, nunca una espera de 180 s. Test en A-1 y A-2.
- Un diálogo modal bloquea el bridge (por ejemplo, "Network Issue" o el de 11 módulos externos del hito 164m): el estado debe ser `MODAL_BLOCKING` y nombrar el título del diálogo. Test en A-1.
- Dos lotes a la vez sobre la misma instalación: el segundo debe fallar con `STUDIO_BUSY`, no corromper el primero. Test en A-2.
- Una validación en cola no se cuenta como pasada, y no se pierde si el proceso muere a mitad del lote: el archivo de cola se escribe de forma atómica. Test en A-8.
- Job con nombre repetido (Studio cachea por id): el reintento usa sufijo nuevo y no reutiliza el cacheado. Test en A-8.

---

### Task A-1: Estado de Studio como función pura

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\talend-mcp\src\talend\studio\studio-state.ts`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\talend-mcp\tests\talend\studio-state.test.ts`

**Interfaces:**
- Produces:
  ```ts
  export type StudioState =
    | "READY" | "NOT_RUNNING" | "WAITING_LOGIN" | "BRIDGE_DEAD" | "MODAL_BLOCKING" | "BUSY";
  export interface StudioProbe {
    pid?: number;            // proceso Talend-Studio, si existe
    pingOk: boolean;         // GET http://127.0.0.1:3930/ping respondió
    pingMs?: number;
    modalTitles: string[];   // diálogos abiertos, vacío si no hay
    loginScreen: boolean;    // la ventana dice "Talend Cloud Data Fabric"
    runningJob: boolean;     // hay un build o una ejecución en curso
  }
  export function classifyStudioState(probe: StudioProbe): { state: StudioState; reason: string };
  ```

- [ ] **Step 1: Write the failing test** con una tabla de sondas y su estado: sin `pid` es `NOT_RUNNING`; con `pid`, `pingOk=false` y `loginScreen=true` es `WAITING_LOGIN`; con `pid`, `pingOk=false`, sin login es `BRIDGE_DEAD`; con `pingOk=true` y `modalTitles=["Network Issue"]` es `MODAL_BLOCKING` y `reason` contiene `"Network Issue"`; con `pingOk=true` y `runningJob=true` es `BUSY`; con `pingOk=true` y nada más es `READY`.
- [ ] **Step 2: Run test to verify it fails**

  Run: `cd C:\Users\USUARIO_BISOLUTION1\code\talend-mcp && bun test tests/talend/studio-state.test.ts`
  Expected: FAIL (módulo inexistente).
- [ ] **Step 3: Implement `classifyStudioState`** en `studio-state.ts`; precedencia: `NOT_RUNNING`, `WAITING_LOGIN`, `BRIDGE_DEAD`, `MODAL_BLOCKING`, `BUSY`, `READY`.
- [ ] **Step 4: Run test to verify it passes** (mismo comando; Expected: PASS).
- [ ] **Step 5: Commit**

  ```bash
  git add src/talend/studio/studio-state.ts tests/talend/studio-state.test.ts
  git commit -m "feat(studio): clasifica el estado de Studio desde una sonda"
  ```

### Task A-2: `talend_studio_ensure_ready`

**Files:**
- Create: `src/talend/studio/studio-ensure-ready.ts`, `src/presentation/tools/studio/ensure-ready.tool.ts`
- Modify: `src/server/registered-tools/preset-sets.ts` (registrar la tool en el preset donde está `talend_studio_restart`), `src/talend/studio/studio-restart.ts` (solo exportar lo que falte: `studioPid`, `waitForStudioBridge`)
- Test: `tests/talend/studio-ensure-ready.test.ts`, y el test de conformidad existente `tests/tools/tool-conformance.test.ts` debe seguir verde

**Interfaces:**
- Consumes: `classifyStudioState`, `studioPid(attempts?, timeoutMs?)`, `restartStudio({force?})`, `waitForStudioBridge(...)` de `studio-restart.ts`.
- Produces:
  ```ts
  export interface EnsureOptions { restart?: boolean; waitMs?: number /* 25_000 por omisión */; probe?: () => Promise<StudioProbe> }
  export interface EnsureResult { state: StudioState; reason: string; recovered: boolean; elapsedMs: number }
  export async function ensureStudioReady(options?: EnsureOptions): Promise<EnsureResult>;
  ```
  Tool: `talend_studio_ensure_ready` con `{ restart?: boolean, waitMs?: number }`, salida `EnsureResult`.

- [ ] **Step 1: Write the failing test** con `probe` inyectado: (a) sonda `READY` devuelve `{state:"READY", recovered:false}`; (b) sonda `BRIDGE_DEAD` con `restart:false` devuelve `BRIDGE_DEAD` en menos de `waitMs` sin llamar a `restartStudio`; (c) con `restart:true` y una sonda que pasa de `BRIDGE_DEAD` a `READY` en la segunda lectura devuelve `recovered:true`; (d) una segunda llamada concurrente devuelve `BUSY` con `reason` que contiene `"STUDIO_BUSY"`.
- [ ] **Step 2: Run test to verify it fails**

  Run: `bun test tests/talend/studio-ensure-ready.test.ts` — Expected: FAIL.
- [ ] **Step 3: Implement `ensureStudioReady`** con una guarda de exclusión mutua en memoria (una promesa activa) y la tool en `ensure-ready.tool.ts`; el tiempo máximo de toda la llamada es `waitMs`, no 180 s.
- [ ] **Step 4: Run** `bun test tests/talend/studio-ensure-ready.test.ts tests/tools/tool-conformance.test.ts` — Expected: PASS.
- [ ] **Step 5: Commit** `feat(studio): talend_studio_ensure_ready con plazo corto y exclusión mutua`.

### Task A-3: Sonda real y latido

**Files:**
- Create: `src/talend/studio/studio-probe.ts`
- Modify: `scripts/start.ts` (la opción `--watch-bridge` escribe `workspace/.bridge-heartbeat.json` con `{state, reason, at}` cada 10 s)
- Test: `tests/talend/studio-probe.test.ts`

**Interfaces:**
- Produces: `export async function probeStudio(): Promise<StudioProbe>` (usa `studioPid`, un `fetch` con `AbortSignal.timeout(3000)` a `/ping`, la lista de diálogos que ya expone `/automation/workbench` o el equivalente del bridge, y la lectura del título de la ventana).

- [ ] **Step 1: Write the failing test** con `fetch` interceptado como en `tests/talend/bridge-client-routes.test.ts`: `/ping` que nunca responde produce `pingOk:false` en menos de 3,5 s; `/ping` ok produce `pingOk:true` y `pingMs` numérico.
- [ ] **Step 2: Run test to verify it fails** — `bun test tests/talend/studio-probe.test.ts`.
- [ ] **Step 3: Implement `probeStudio`**; si `/ping` falla no se consultan diálogos (se evita colgar dos veces).
- [ ] **Step 4: Run** el test — Expected: PASS. Luego `bun run typecheck`.
- [ ] **Step 5: Commit** `feat(studio): sonda real y latido del bridge`.

### Task A-4: Spike del límite de 25 s del bridge

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\talend-mcp\docs\studio-internals\09-limite-de-respuesta-del-bridge.md`
- Test: el caso que lo reproduce, en `tests/talend/bridge-transport-errors.test.ts`

**Interfaces:**
- Produces: decisión escrita y una de dos soluciones con prueba: (a) la operación larga (`build-batch`, `compile`) responde `202` con un `jobId` y se consulta con `GET /automation/jobs/:jobId`; o (b) el cliente parte la operación en tramos. La que gane se implementa en A-4b.

- [ ] **Step 1: Reproducir** con `l1_14_expresion_compuesta` y `l1_15_distinct_tildes` (hitos 146m a 148m de `PROGRESS.md` en `sgm-v2`): registrar tiempo de compilación, tamaño de la respuesta y el instante en que el bridge corta. Resultado literal al documento.
- [ ] **Step 2: Decidir** (a) o (b) con esta regla: si el tiempo de compilación de un solo Job pasa de 20 s, (a); si el problema es el tamaño de la respuesta, (b).
- [ ] **Step 3: Write the failing test** que simula una respuesta del bridge de 40 s y exige que el cliente HTTP (`src/modules/studio-bridge/adapters/bridge-transport.ts`) no se cuelgue ni devuelva éxito falso.
- [ ] **Step 4: Implement** la solución elegida en `bridge-transport.ts` (y en el bridge Java `talend-studio-bridge/` solo si es (a)).
- [ ] **Step 5: Run** `bun test tests/talend/bridge-transport-errors.test.ts` y, con Studio sano, compilar los dos casos del paso 1. Expected: los dos compilan.
- [ ] **Step 6: Commit** `fix(bridge): operaciones largas sin superar el plazo de respuesta`.

### Task A-5: Spike y arreglo de `tHashInput` (INTERNALS 70)

**Files:**
- Modify: `src/talend/job-generator/` (el componente `tHashInput` según lo que revele el spike), `docs/studio-internals/07-componentes-avanzados.md` (sección 70 pasa de "pendiente" a causa y solución)
- Test: el escenario existente `tests/fixtures/talend/escenarios-l5/transformaciones/hash-memoria-entre-subjobs.json` deja de estar marcado `pendiente`

**Interfaces:**
- Produces: `tHashOutput` seguido de `tHashInput` en el mismo Job entrega las filas escritas. Esto desbloquea `MG-P8b-07` (reconvergencia de ramas sin `P-REPARTO-RECONVERGE`).

- [ ] **Step 1: Bisecar** con el Job de la sección 70: leer el Java generado del `tHashInput` (`tHashFile_<job>_<pid>_tHashOutput_2.iterator()`), añadir impresiones de la clave en escritura y en lectura, y comparar. Hipótesis a descartar en este orden: la clave difiere entre escritura y lectura; el `tHashOutput` no llegó a `CLOSE` antes de leer (orden de subjobs); la opción de "limpiar tras leer" vacía el mapa.
- [ ] **Step 2: Write the failing test** quitando `pendiente` del escenario L5.
- [ ] **Step 3: Run** `bun run l5:validar` filtrado: `bun run scripts/execution-check.ts --suite transformaciones` — Expected: FAIL en ese escenario.
- [ ] **Step 4: Implement** la corrección que el paso 1 demuestre; si es de configuración, en el generador; si es de orden, en la conexión `SUBJOB_OK`.
- [ ] **Step 5: Run** la misma suite — Expected: PASS con las filas esperadas.
- [ ] **Step 6: Commit** `fix(talend): tHashInput lee lo que escribe tHashOutput en el mismo Job`.

### Task A-6: Joblets de extremo a extremo (MG-P9-03, lado MCP)

**Files:**
- Modify: `src/talend/job-generator/joblet.ts` (ya existe `buildJobletItemXml(spec: JobletSpec)`), `src/talend/job-crud/joblet.ts`
- Create: `src/presentation/tools/jobs/joblet.tool.ts` (`talend_joblets_create_from_spec`), `tests/fixtures/talend/escenarios-l5/control/joblet-con-parametros-en-dos-jobs.json`
- Test: `tests/talend/joblet.test.ts`

**Interfaces:**
- Consumes: `JobletSpec`, `buildJobletItemXml` (devuelve `{ xml, rootId }`).
- Produces: un joblet con una variable de contexto, creado desde archivos, usado por dos Jobs distintos, que compila y se ejecuta con salida verificada. Si Studio 8.0.1 no carga el joblet escrito a mano, el resultado es el plan B: un Job hijo con `tRunJob`, con la regla escrita de cuándo usar cada uno. La decisión se toma en esta tarea y no después.

- [ ] **Step 1: Spike de carga.** Escribir un joblet mínimo (`tJobletInput` a `tJobletOutput`) en `process/`, refrescar el workspace y comprobar que Studio lo lista. Anotar el resultado literal y la ruta (`joblets/` o `process/`).
- [ ] **Step 2: Write the failing test** (`tests/talend/joblet.test.ts`): el `.item` generado contiene los nodos `tJobletInput` y `tJobletOutput`, el parámetro de contexto del joblet y su `.properties` con el tipo de elemento de joblet.
- [ ] **Step 3: Implement** la tool y la corrección del generador que exija el spike.
- [ ] **Step 4: Escenario L5.** Dos Jobs que usan el mismo joblet con valores distintos del parámetro; la salida de cada uno se compara con su CSV esperado. Run: `bun run scripts/execution-check.ts --suite control` — Expected: PASS.
- [ ] **Step 5: Decisión escrita** en `docs/studio-internals/07-componentes-avanzados.md`: "joblet cargable desde archivo: sí/no", y si no, el plan B con `tRunJob` y su regla.
- [ ] **Step 6: Commit** `feat(joblets): crear y usar joblets con parámetros, con escenario L5`.

### Task A-7: Spike de compilación sin la interfaz de Studio

**Files:**
- Create: `docs/studio-internals/10-compilar-sin-ventana.md`
- Test: ninguna hasta decidir; si se adopta, `tests/talend/build-headless.test.ts`

**Interfaces:**
- Produces: un informe con tres opciones medidas sobre los mismos 20 Jobs: (1) bridge actual (`talend_job_build_batch`); (2) el modo de línea de comandos de Studio (`-application org.talend.commandline.CommandLine`, si la instalación 8.0.1 lo trae); (3) Build Job de un Job y compilación con Maven/JDK. Regla de adopción: solo si compila 20 Jobs en menos de 3 min con el mismo resultado que la opción 1.

- [ ] **Step 1: Comprobar** qué existe en `C:\Talend\8.0.1\studio` (plugins `org.talend.commandline*`). Registrar la lista.
- [ ] **Step 2: Medir** las opciones disponibles sobre los 20 primeros Jobs de L0 a L1; registrar tiempo y si coincide el resultado.
- [ ] **Step 3: Decidir** con la regla de adopción. Si se adopta, escribir la prueba que falla (`build-headless.test.ts`: dado un Job válido devuelve `ok:true` sin llamar al bridge) y la tool `talend_job_build_headless`. Si no, cerrar con el informe y la razón.
- [ ] **Step 4: Commit** `docs(studio): informe de compilación sin ventana` (y `feat(...)` si se adopta).

### Task A-8: Cola de validaciones pendientes en `sgm-v2`

**Files:**
- Create: `tools/corpus_lib/studio_cola.py`
- Modify: `tools/corpus_studio.py` (subcomando `lote` y `validar`: si la salud falla, escribe en la cola y sale con un código distinto de 0 y mensaje claro; nuevo subcomando `pendientes` que reintenta la cola)
- Test: `tests/unit/test_studio_cola.py`

**Interfaces:**
- Produces:
  ```python
  @dataclass(frozen=True)
  class Pendiente:
      caso: str           # "L6/l6_18_output_condicional_sin_destino_con_continuacion"
      motivo: str         # código de estado: "BRIDGE_DEAD", "MODAL_BLOCKING"...
      intentos: int

  def encolar(ruta: Path, pendiente: Pendiente) -> None  # escritura atómica (archivo temporal y reemplazo)
  def leer(ruta: Path) -> list[Pendiente]
  def vaciar(ruta: Path, resueltos: set[str]) -> None
  ```
  La cola vive en `out/studio-pendientes.json` (fuera de git).

- [ ] **Step 1: Write the failing test**: encolar dos casos, leer devuelve los dos; `vaciar` quita solo el resuelto; un archivo corrupto devuelve lista vacía y no lanza; encolar es atómico (el archivo temporal no queda).
- [ ] **Step 2: Run** `uv run python -m pytest tests/unit/test_studio_cola.py -q` — Expected: FAIL.
- [ ] **Step 3: Implement** `studio_cola.py`; el reintento usa un sufijo nuevo por intento (`mg<id>a`, `mg<id>b`) porque Studio cachea los Jobs por id.
- [ ] **Step 4: Run** el test y `uv run ruff check .` — Expected: PASS y limpio.
- [ ] **Step 5: Commit** `hito 191: cola de validaciones pendientes de Studio`.

### Task A-9: La salud de `sgm` usa `ensure_ready`

**Files:**
- Modify: `src/sgm/backend_talend/salud.py` (`comprobar_salud`), `src/sgm/backend_talend/comun.py` (constante `TOOL_ENSURE = "talend_studio_ensure_ready"`), `src/sgm/cli_studio.py` (`sgm studio salud` muestra el estado)
- Test: `tests/unit/test_backend_salud.py` (ampliar)

**Interfaces:**
- Consumes: `Salud` y `Llamable.llamar(tool, entrada, tiempo_max)` de `salud.py`.
- Produces: `Salud` gana el campo `estado: str` (uno de `StudioState`) y `comprobar_salud` intenta una sola recuperación cuando el estado es `BRIDGE_DEAD` y el llamador pasó `recuperar=True`; en cualquier otro caso no toca Studio.

- [ ] **Step 1: Write the failing test** con un doble de backend que devuelve `BRIDGE_DEAD` y después `READY` en la llamada con `restart:true`: con `recuperar=True` la salud queda `ok`; con `recuperar=False` queda no-`ok` y el motivo contiene `BRIDGE_DEAD`. Con `MODAL_BLOCKING` el motivo incluye el título del diálogo y no se reintenta.
- [ ] **Step 2: Run** `uv run python -m pytest tests/unit/test_backend_salud.py -q` — Expected: FAIL.
- [ ] **Step 3: Implement** el cambio manteniendo el tiempo máximo de 10 s por llamada.
- [ ] **Step 4: Run** `uv run python -m pytest -q -n auto` y `uv run ruff check .` — Expected: verdes.
- [ ] **Step 5: Commit** `hito 192: la salud de Studio distingue estados y se recupera una vez`.

### Task A-10: Vaciar la cola y reconciliar lo pendiente

**Files:**
- Modify: `PROGRESS.md` (entrada del hito), `docs/plan-reescritura/plan-migrador-general.md` (estado de MG-P4-02 y MG-P8b-07), `AGENTS.md` (sección «Studio y `talend-mcp`»: autorización del 11 de noviembre de 2026 para modificar `talend-mcp`, con la frontera de que el núcleo de `sgm` no lo importa)

- [ ] **Step 1: Con Studio sano**, correr `uv run python tools/corpus_studio.py pendientes` y vaciar la cola: `L6/l6_18`, `l6_22`, `l6_23`, `l6_24` (hitos 187 a 190).
- [ ] **Step 2: Anotar** el resultado literal de cada uno (`1 casos, 1 coinciden` o la diferencia) en `PROGRESS.md`; los que fallen quedan como bloqueo con su motivo, no se cuentan.
- [ ] **Step 3: Actualizar** `AGENTS.md` con la autorización y el plan maestro con el nuevo estado.
- [ ] **Step 4: Run** `uv run python -m pytest -q -n auto` y `uv run ruff check .` — Expected: verdes.
- [ ] **Step 5: Commit** `hito 193: validación pendiente de OUTPUT en Studio y autorización sobre talend-mcp`.

## Estado de ejecución (11 de noviembre de 2026, hitos 191 y 192)

| Tarea | Estado |
|---|---|
| A-1 estado de Studio | hecha en `talend-mcp` (`studio-state.ts`, commit `ae151d2`) |
| A-2 `ensure_ready` como tool | cambiada: lo que faltaba era un proceso de fondo, no una tool. Hecho como `bun run supervisor` (reinicia el MCP; commit `ae151d2`) |
| A-3 sonda y latido | latido hecho en `logs/supervisor.json`; la sonda de diálogos la reemplaza A-11 |
| A-4 límite de 25 s del bridge | **parcial** (hito 195, en `talend-mcp`): `build` y `build-batch` heredaban los 2 500 ms del cliente y se abortaban a mitad; ahora llevan 180 s y 300 s propios, con prueba de que una lectura lenta se corta limpia y no finge éxito. Falta medir un lote real de más de 20 s |
| A-5 `tHashInput` | **hecha** (hito 193): el `SUBJOB_OK` salia del `tHashOutput` y eso es un diseno invalido; el enlace se cuelga del `tFixedFlowInput` de arranque y ese nodo lleva `schemaDespuesDeConectar` porque conectar borra sus valores. Escenario `transformaciones/hash-memoria-entre-subjobs` en verde |
| A-6 joblets de extremo a extremo | spike hecho (hito 194): el joblet se escribe en `joblets/`, pero no se pudo confirmar que Studio lo cargue (refresco con el IDE ocupado; el endpoint de componentes no enumera joblets). Se adopta el plan B con `tRunJob` hasta verlo en la interfaz |
| A-7 compilar sin ventana | reconocimiento hecho (`docs/studio-internals/10-compilar-sin-ventana.md`): esta instalación no trae `org.talend.commandline*`, así que la opción de línea de comandos no existe; falta medir la opción de Maven/JDK |
| A-8 cola de validaciones | **hecha** (hito 192): `tools/corpus_lib/studio_cola.py`, `validar` y `lote` encolan cuando no hay Studio, subcomando `pendientes` |
| A-9 la salud de `sgm` usa el estado | **hecha** (hito 192): `Salud.estado`, una sola recuperación con `--recuperar`, caso `MODAL_BLOCKING` que no reintenta |
| A-10 vaciar lo pendiente | hecho para `l6_18`, `l6_22`, `l6_23`, `l6_24` (4 de 4 coinciden); falta la nota de `AGENTS.md` |
| **A-11 nuevo: diálogos autónomos** | **hecha** (`src/talend/studio/modals/`, commit `e88783c`): lee por UI Automation, decide, pulsa y registra; el supervisor lo corre cada 5 s |

A-11: `talend_studio_handle_modals` quedó registrada como tool del MCP en el hito 192 (con `dryRun`
y sus anotaciones de seguridad; conformidad de tools y `tsc` verdes). Queda un caso más de la
política por cada diálogo nuevo que aparezca en `logs/modales.jsonl`.

## Self-review

- **Cobertura:** los cinco bloqueos documentados están cubiertos: bridge mudo (A-1 a A-3, A-9), límite de 25 s (A-4), `tHashInput` (A-5), joblets (A-6), dependencia total de la ventana (A-7), validaciones perdidas (A-8, A-10).
- **Tipos:** `StudioState` y `StudioProbe` se definen en A-1 y los usan A-2, A-3 y A-9; `EnsureResult.state` es `StudioState`; `Salud.estado` en Python repite los mismos seis literales.
- **Proporción:** plan de 10 tareas con firmas y pruebas; los cuerpos de las funciones los decide quien implementa.
