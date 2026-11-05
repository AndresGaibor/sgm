# MG-01 Fundación rápida: backend de Talend, lote y ciclo de desarrollo

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Dejar listo el entorno que hace rápido todo el desarrollo posterior: un módulo `backend_talend` (archivos o CLI de `talend-mcp`), una compilación de Jobs en lote y un ciclo de pruebas de menos de 90 segundos.

**Architecture:** `src/sgm/backend_talend/` define un `Protocol` y dos implementaciones. `ArchivosBackend` escribe con `talend_item.escritura.escribir_job` y no depende de nada. `TalendCliBackend` llama a la CLI `talend` de `talend-mcp` por `subprocess` con un ejecutor inyectable (así se prueba sin Studio). Las herramientas de `tools/` consumen la interfaz, no la CLI.

**Tech Stack:** Python 3.12, `pytest`, `ruff`, `subprocess`, `dataclasses`. Sin dependencias nuevas.

**Spec:** `docs/plan-reescritura/plan-migrador-general.md`, secciones 0.2, 4.1, 6.1 y tareas MG-P0-02 a MG-P0-09.

## Global Constraints

- Archivos de 300 líneas como máximo; una responsabilidad por archivo.
- Identificadores en inglés (los módulos de `talend_item/` usan nombres en español: no mezclar en archivos nuevos); comentarios, docstrings y mensajes de error en español.
- `uv run pytest -q -n auto` y `uv run ruff check .` en verde antes de cada commit; `ruff` con 100 columnas.
- Dependencias permitidas: `networkx`, `typer`, `pyyaml`, `sqlglot`, `jsonschema` (aprobadas en el hito 80) y las de desarrollo `pytest`, `pytest-xdist`, `ruff`.
- Sin `git push`. Commit por tarea: `hito N<letra>: <resumen>` terminando con `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Sin `--amend` ni `rebase` sobre commits ajenos. `git add` solo de los archivos de la tarea.
- Ningún secreto en la línea de comandos, en el registro ni en las pruebas.
- Las pruebas que necesitan Talend Studio llevan `@pytest.mark.studio` y no corren por omisión (se registra la marca en `pyproject.toml`).
- Studio es un recurso compartido: nunca dos corridas a la vez.
- El `PROGRESS.md` se anexa con un script que añade bytes UTF-8 (el archivo mezcla codificaciones); nunca se reescribe entero.

## Review Focus

1. La CLI de Talend no está instalada o `bun` no está en el `PATH`: debe fallar con `BackendNoDisponible` y mensaje claro, no con una traza (test en Task 2).
2. La CLI devuelve JSON inválido o vacío: error controlado, no `JSONDecodeError` (test en Task 2).
3. La CLI se cuelga: el tiempo máximo corta y devuelve error (test en Task 2).
4. El lote deja Jobs de prueba copiados en `process/` si algo falla a la mitad: se limpian siempre (test en Task 4).
5. Un módulo del núcleo importa la CLI de Talend sin pasar por `backend_talend`: la prueba de aislamiento lo detecta (Task 3).

---

### Task 1: Tipos y backend de archivos

**Files:**
- Create: `src/sgm/backend_talend/__init__.py`
- Create: `src/sgm/backend_talend/base.py`
- Create: `src/sgm/backend_talend/archivos.py`
- Test: `tests/unit/test_backend_archivos.py`

**Interfaces:**
- Consumes: `sgm.talend_item.modelo.Job`; `sgm.talend_item.escritura.escribir_job(job: Job, carpeta: Path, fecha: str | None = None) -> tuple[Path, Path]`.
- Produces (en `base.py`):
  - `class BackendNoDisponible(RuntimeError)`
  - `@dataclass(frozen=True) class ResultadoLote: compilan: tuple[str, ...]; no_compilan: dict[str, str]` (nombre a motivo)
  - `@dataclass(frozen=True) class Veredicto: nivel: str; hallazgos: tuple[str, ...]` donde `nivel` es `"ok"`, `"ok_con_avisos"` o `"error"`
  - `class BackendTalend(Protocol): def escribir(self, jobs: list[Job], carpeta: Path) -> list[Path]; def compilar_lote(self, nombres: list[str]) -> ResultadoLote; def verificar(self, nombre: str, contexto: dict[str, str]) -> Veredicto`
- Produces (en `archivos.py`): `class ArchivosBackend` que cumple `BackendTalend`; `compilar_lote` y `verificar` lanzan `BackendNoDisponible("el backend de archivos no compila ni ejecuta")`.

- [ ] **Step 1: Write the failing tests** en `tests/unit/test_backend_archivos.py`:
  - `test_escribir_devuelve_un_item_y_un_properties_por_job(tmp_path)`: con dos `Job(nombre="a")`, `Job(nombre="b")` mínimos, `ArchivosBackend().escribir(jobs, tmp_path)` devuelve 4 rutas y los 4 archivos existen.
  - `test_compilar_lote_no_esta_disponible(tmp_path)`: `pytest.raises(BackendNoDisponible)`.
  - `test_resultado_lote_es_inmutable()`: asignar `compilan` lanza `FrozenInstanceError`.
- [ ] **Step 2: Run** `uv run pytest tests/unit/test_backend_archivos.py -v`. Expected: FAIL por `ModuleNotFoundError: sgm.backend_talend`.
- [ ] **Step 3: Implement** los tipos de `base.py` y `ArchivosBackend.escribir` (llama a `escribir_job` por cada Job y devuelve las rutas en orden). `__init__.py` reexporta los nombres públicos.
- [ ] **Step 4: Run** el mismo comando. Expected: 3 passed. Luego `uv run ruff check src/sgm/backend_talend tests/unit/test_backend_archivos.py`: sin errores.
- [ ] **Step 5: Commit** `hito 103m: MG-P0-08 (1), tipos y backend de archivos de backend_talend`.

---

### Task 2: Backend por CLI de talend-mcp

**Files:**
- Create: `src/sgm/backend_talend/talend_cli.py`
- Test: `tests/unit/test_backend_talend_cli.py`

**Interfaces:**
- Consumes: `BackendTalend`, `ResultadoLote`, `Veredicto`, `BackendNoDisponible` de la Task 1.
- Produces: `class TalendCliBackend(ArchivosBackend)` con `__init__(self, talend_dir: Path, proyecto: Path, ejecutor: Ejecutor | None = None, tiempo_max: float = 120.0)`; `Ejecutor = Callable[[list[str], float], tuple[int, str]]` (argumentos, tiempo máximo; devuelve código y salida estándar). El ejecutor por omisión usa `subprocess.run(..., capture_output=True, text=True, timeout=...)` y traduce `FileNotFoundError` y `TimeoutExpired` a `BackendNoDisponible`.
- La CLI se invoca así: `["bun", "run", "cli", "--project", str(proyecto), "--json", "tools", "call", "<tool>", "--input", "<json>", "--yes"]` con `cwd=talend_dir`.
- `compilar_lote(nombres)` llama a `talend_job_build_batch` con `{"jobs": nombres, "parallelism": 4}` y mapea la respuesta a `ResultadoLote`. `verificar(nombre, contexto)` llama a `talend_job_verify` con `{"job": nombre, "context": contexto}` y mapea `verdict` a `Veredicto.nivel`.

- [ ] **Step 1: Write the failing tests** con un ejecutor falso (lista de llamadas y respuesta fija):
  - `test_compilar_lote_arma_la_linea_de_comandos`: el ejecutor recibe una lista que contiene `"talend_job_build_batch"` y un `--input` con JSON cuyo campo `jobs` es la lista pedida.
  - `test_compilar_lote_mapea_no_compilan`: respuesta `{"ok": true, "data": {"noCompilan": [{"job": "b", "error": "x"}], "compilan": ["a"]}}` da `ResultadoLote(compilan=("a",), no_compilan={"b": "x"})`.
  - `test_verificar_mapea_el_veredicto`: `verdict: "ok_con_avisos"` y `findings: ["[WARN] ..."]` dan `Veredicto("ok_con_avisos", ("[WARN] ...",))`.
  - `test_cli_ausente_lanza_backend_no_disponible`: ejecutor por omisión con `talend_dir` inexistente lanza `BackendNoDisponible` con el texto `"no se encontró"`.
  - `test_json_invalido_lanza_error_controlado`: salida `"no es json"` lanza `BackendNoDisponible` con `"respuesta no válida"`.
  - `test_tiempo_maximo_se_propaga`: el ejecutor recibe el `tiempo_max` configurado.
  - `test_ningun_secreto_en_la_linea`: ninguna palabra de la línea contiene `password` (los contextos con contraseña se rechazan con `ValueError` antes de llamar).
- [ ] **Step 2: Run** `uv run pytest tests/unit/test_backend_talend_cli.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement** la clase. Para la forma exacta de las respuestas ejecutar una vez, a mano, `bun run cli --project <proyecto> --json tools call talend_job_build_batch --input '{"jobs":["no_existe"]}' --yes` en `C:\Users\USUARIO_BISOLUTION1\code\talend-mcp`, guardar la salida real en `tests/fixtures/talend_cli/build_batch.json` y ajustar el mapeo a ella; hacer lo mismo con `talend_job_verify`.
- [ ] **Step 4: Run** el mismo comando. Expected: 7 passed. `ruff` limpio.
- [ ] **Step 5: Commit** `hito 103m: MG-P0-08 (2), backend de Talend por CLI con ejecutor inyectable`.

---

### Task 3: Aislamiento y salud rápida

**Files:**
- Create: `src/sgm/backend_talend/salud.py`
- Create: `tools/studio_salud.py`
- Test: `tests/unit/test_backend_aislado.py`, `tests/unit/test_backend_salud.py`

**Interfaces:**
- Consumes: `TalendCliBackend` (Task 2).
- Produces: `@dataclass(frozen=True) class Salud: ok: bool; motivo: str`; `def comprobar_salud(backend: TalendCliBackend, tiempo_max: float = 10.0) -> Salud`, que llama a la tool `talend_bridge_ping`; si responde `readWrite` devuelve `Salud(True, "")`; ante diálogo bloqueado o tiempo agotado devuelve `Salud(False, "<motivo>")` con el texto `"revisa si hay un diálogo abierto en Talend Studio"`.

- [ ] **Step 1: Write the failing tests.**
  - `test_aislamiento`: recorre `src/sgm/**/*.py` salvo `backend_talend/` y comprueba que ninguno contiene `"talend-mcp"`, `"mcp_cliente"`, ni `'"bun"'`; el mensaje de fallo lista los archivos.
  - `test_salud_ok`: ejecutor falso con respuesta de ping `readWrite` da `Salud(True, "")`.
  - `test_salud_dialogo_bloqueado`: ejecutor que devuelve `{"error": {"code": "STUDIO_DIALOG_OPEN"}}` da `Salud(False, ...)` con el texto del diálogo.
  - `test_salud_tiempo_agotado`: ejecutor que lanza `BackendNoDisponible` da `Salud(False, ...)` en menos de 1 s.
- [ ] **Step 2: Run** los dos archivos. Expected: FAIL.
- [ ] **Step 3: Implement** `comprobar_salud` y `tools/studio_salud.py` (argparse: `--talend-dir`, `--proyecto`; imprime una línea y sale con 0 o 1).
- [ ] **Step 4: Run** los tests y `uv run python tools/studio_salud.py --talend-dir C:/Users/USUARIO_BISOLUTION1/code/talend-mcp --proyecto C:/Talend/8.0.1/studio/workspace/talendbancolombia-963626413/PRJ_BANCOLOMBIA`. Expected: tests passed; la herramienta tarda menos de 10 s y da `ok` si Studio está libre, o el motivo si no.
- [ ] **Step 5: Commit** `hito 103m: MG-P0-02 y MG-P0-07, salud de Studio y prueba de aislamiento del backend`.

---

### Task 4: Compilación en lote del corpus

**Files:**
- Create: `tools/corpus_lib/studio_lote.py`
- Modify: `tools/corpus_studio.py` (subcomando `lote`)
- Test: `tests/unit/test_corpus_studio_lote.py`

**Interfaces:**
- Consumes: `BackendTalend.compilar_lote`; la carpeta de Jobs de cada caso (`*.item` y `*.properties`).
- Produces: `def compilar_en_lote(carpetas: list[Path], proyecto: Path, backend: BackendTalend, sufijo: str) -> ResultadoLote`: copia todos los pares `.item`/`.properties` a `<proyecto>/process/` renombrados con `sufijo` (Studio cachea por id), llama a `backend.compilar_lote` **una sola vez**, y borra lo copiado en un `finally`.

- [ ] **Step 1: Write the failing tests** con un backend falso:
  - `test_copia_llama_una_vez_y_limpia`: dos carpetas con un Job cada una; el backend recibe una sola llamada con los dos nombres con sufijo; después de volver, `process/` no contiene archivos.
  - `test_limpia_aunque_el_backend_falle`: el backend lanza `BackendNoDisponible`; `process/` queda sin archivos y la excepción se propaga.
  - `test_no_pisa_jobs_ajenos`: si ya existe `process/otro_0.1.item`, sigue existiendo al terminar.
  - `test_nombres_con_sufijo_unico`: dos llamadas seguidas con distinto `sufijo` no colisionan.
- [ ] **Step 2: Run** `uv run pytest tests/unit/test_corpus_studio_lote.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement** `compilar_en_lote`. El renombrado reescribe el nombre del Job dentro del `.properties` y el `.item` (usar la función que ya hace esto en `tools/corpus_lib/studio_validar.py`: `sufijo_nuevo` y la copia de `_copiar_jobs`; reutilizarlas, no duplicarlas). Añadir `lote <caso...> --jobs <carpeta> --proyecto <ruta> --backend {talend_cli}` a `corpus_studio.py`.
- [ ] **Step 4: Run** los tests. Expected: 4 passed. Con Studio libre: `uv run python tools/corpus_studio.py lote l2_01_inner_join_clientes_ventas --jobs <carpeta con un Job> --proyecto <PRJ_BANCOLOMBIA>` y anotar el tiempo.
- [ ] **Step 5: Commit** `hito 103m: MG-P0-03 y MG-P0-09, compilación en lote del corpus`.

---

### Task 5: Ciclo rápido de desarrollo

**Files:**
- Create: `tools/ciclo_rapido.py`
- Modify: `pyproject.toml` (registrar la marca `studio`)
- Test: `tests/unit/test_ciclo_rapido.py`

**Interfaces:**
- Produces: `def casos_tocados(archivos: list[str]) -> list[str]` que devuelve los directorios de caso de `tests/corpus/` que contienen alguno de los archivos; `def comandos(archivos: list[str]) -> list[list[str]]` que arma, en orden: `["uv","run","ruff","check", ...archivos .py]`, `["uv","run","pytest","-q","-n","auto","-m","not studio", ...]` y, si hay casos tocados, `["uv","run","python","tools/corpus.py","oraculo", <caso>, "--verificar"]` por caso; `def main(argv=None) -> int` que obtiene los archivos con `git diff --name-only HEAD` (inyectable), ejecuta los comandos, imprime el tiempo de cada uno y sale con el primer código distinto de 0.

- [ ] **Step 1: Write the failing tests.**
  - `test_casos_tocados_detecta_el_directorio_del_caso`: `["tests/corpus/L2/l2_01_x/programa.sas"]` da `["tests/corpus/L2/l2_01_x"]`.
  - `test_sin_casos_no_hay_comando_de_oraculo`.
  - `test_ruff_solo_sobre_python`: un cambio en un `.md` no añade `ruff`.
  - `test_sale_con_el_primer_fallo`: ejecutor falso que falla en el segundo comando; `main` devuelve su código y no corre el tercero.
- [ ] **Step 2: Run** `uv run pytest tests/unit/test_ciclo_rapido.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement** `casos_tocados`, `comandos` y `main`. Registrar `markers = ["studio: necesita Talend Studio; no corre por omisión"]` en `[tool.pytest.ini_options]` y añadir `addopts` con `-m "not studio"` solo si no existe ya.
- [ ] **Step 4: Run** los tests. Expected: 4 passed. Luego medir con 20 casos tocados: `uv run python tools/ciclo_rapido.py` y comprobar que termina en menos de 90 s; si no, anotar el cuello de botella en `PROGRESS.md`.
- [ ] **Step 5: Commit** `hito 103m: MG-P0-04, ciclo rápido de desarrollo`.

---

### Task 6: Cierre del plan

**Files:**
- Modify: `PROGRESS.md` (entrada anexada), `docs/plan-reescritura/plan-migrador-general.md` (estado de MG-P0-02 a MG-P0-09)

- [ ] **Step 1: Run** `uv run pytest -q -n auto` y `uv run ruff check .`. Expected: todo en verde.
- [ ] **Step 2: Anexar** la entrada `## Hito 103m. ...` con los tiempos medidos: salud de Studio, lote de 1 y de 10 Jobs, ciclo rápido.
- [ ] **Step 3: Commit** `hito 103m: MG-01 cerrado, fundación rápida`.

## Self-Review (hecha)

- **Cobertura del spec:** MG-P0-02 (Task 3), MG-P0-03 y MG-P0-09 (Task 4), MG-P0-04 (Task 5), MG-P0-07 y MG-P0-08 (Tasks 1 a 3). MG-P0-01 (numeración), MG-P0-05 (tablero) y MG-P0-06 (documento de la IR) quedan para el plan MG-02, que es quien los usa.
- **Consistencia de tipos:** `ResultadoLote`, `Veredicto` y `BackendNoDisponible` se definen en la Task 1 y se usan con los mismos campos en las Tasks 2 a 4.
- **Proporción:** seis tareas; ningún cuerpo de función aparece, solo firmas y pruebas.
