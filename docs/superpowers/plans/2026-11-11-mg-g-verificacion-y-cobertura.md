# MG-G: Verificación, cobertura y calidad Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Dejar el «100 %» medible de verdad: que cada criterio C1 a C6 del plan maestro tenga un comando que lo mide y una cifra que se pega en `PROGRESS.md`, que el intérprete de referencia (anillo B) cubra todo el corpus `traducible` incluidos los niveles L7 y L9, que `sgm migrar` no falle nunca (ni con programas basura), que un generador de programas encuentre y reduzca errores de composición, que el arnés demuestre por mutación que detecta un esperado alterado, y que una corrida nocturna (anillo D) avise de toda regresión. Cierra MG-P0 (restante) y MG-P10 (restante) y la compuerta GM5.

**Architecture:** Cambios solo en `sgm-v2`, en zonas de verificación que casi no se pisan con los planes de Andres: `tools/` (medidores, generador, nocturna, tablero), `tools/corpus_lib/` (casos L7 y L9), `src/sgm/cobertura/` (módulo nuevo, comando `sgm cobertura`), `tests/unit/` y `docs/`. El principio de todos los medidores: **no inventan datos**; leen lo que ya existe (corpus, reglas, `PROGRESS.md`, salida de `sgm migrar`), escriben un JSON en `out/criterios/` (no versionado) y el tablero único los junta; lo que no se mide dice «no medido» con su motivo. El intérprete (`src/sgm/migrar/`) lo mantienen los planes B, C y E: este plan **mide** y **protege** (trinquete), no implementa semántica SAS nueva.

**Tech Stack:** Python 3.12, pytest, ruff, `pyyaml`, `typer`; `javac` suelto solo en G-9 (el JDK de Studio, con `skipif` y registro «no medido» si no está). `uv run python -m pytest` y `uv run python -m sgm.cli` (en este Windows `uv run pytest` puede bloquearse por Control de aplicaciones).

**Spec:** `docs/plan-reescritura/plan-migrador-general.md` (sección 1: C1 a C7; sección 6: pirámide de pruebas y generador 6.3; MG-P0-01, MG-P0-05, MG-P0-06, MG-P10-01, P10-03 a P10-09; sección 11b), `docs/plan-reescritura/reparto-andres-byron.md` y `docs/superpowers/plans/2026-11-11-ruta-al-100.md`.

**Horas del plan maestro cubiertas:** MG-P10 restante 56 h (80 h menos 24 h acreditadas) + MG-P0 restante 12 h = 68 h. Tabla por tarea al final («Resumen de horas»).

**Series de hitos:** `n` = verificación (carril de Byron, G-1 a G-20 y G-Gate). La letra va en el título de la entrada de `PROGRESS.md` y en el mensaje del commit. G-Gate lo cierra Byron con los lotes de los planes de Andres ya integrados.

## Global Constraints

- Sin `git push`, sin `--amend`. Un commit local por hito: `hito N n: <resumen>`, terminado con la línea `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Antes de escribir, buscar el último `## Hito` de `PROGRESS.md` (al redactar este plan era el 198) y sumar uno; si otra sesión ya tomó el número, tomar el siguiente (después de G-2 se usa `tools/auditar_progress.py --siguiente n`). No renumerar entradas publicadas.
- No tocar `tools/ci.py`, `tools/validacion.py`, `tools/instalar_ganchos.py`, `README.md` ni `.githooks/` (son del Plan A y estaban sin commitear). G-18 **consume** `tools/ci.py` si ya está integrado, sin modificarlo.
- `PROGRESS.md` solo se **edita al final** (apéndice de la entrada del hito); nunca se reescribe, se reordena ni se cambia su codificación (es UTF-8 con CRLF y líneas de hasta 640 caracteres; lo audita G-1).
- Nada de nombres de scripts de ejemplo (`cod1`, `cod2`, `cars_poc`, `exogena`, `split2`, `split3`, `executeBulkload`, `waitForBulkLoads`, `bulkload_generic`) en `src/` ni `rules/`; lo vigila `tests/unit/test_no_script_specific_names.py`. Los medidores de `tools/` tampoco los llevan: reciben el programa por argumento. No leer ningún archivo de la carpeta Descargas con contraseñas en claro.
- Si el SAS no demuestra un tipo, una columna, un valor o una equivalencia: `Pendiente:` con motivo y código `P-xxx`. Nunca un valor supuesto. Los casos nuevos (G-11, G-12) llevan su esperado **por construcción** (el generador de datos escribe la verdad) o con la página de la guía en `razonamiento`; si la página no demuestra el resultado, el caso queda `pendiente_revision`, no se inventa.
- Si no hay página de la guía SAS, no hay equivalencia. Cada regla o entrada de catálogo nueva cita `<guía>, p. N` con una página que exista en `docs/referencia/sas/<guía>.INDEX.md` (`tests/unit/test_catalogo_sas.py` lo vigila). No leer el PDF ni el `.txt` entero.
- No borrar ni debilitar pruebas. Los trinquetes (G-8, G-15, G-16) solo se **endurecen**: un número que baja se actualiza en el mismo hito con la causa; uno que sube se rechaza.
- Archivos de código de menos de 300 líneas. `tools/tablero.py` ya tiene 240: lo nuevo del tablero va en `tools/tablero_criterios.py` y `tools/tablero.py` solo lo importa. `src/sgm/migrar/interprete.py` (1103 líneas) **no se toca** en este plan.
- Código e identificadores en inglés (los nombres de los módulos de `tools/` y de las funciones de dominio están en español, como los de `tools/` existentes y `operadores.py`); comentarios, docstrings, mensajes y documentación en español.
- Después de cada tarea: `uv run python -m pytest -q -p no:cacheprovider <archivo de la tarea>` en verde y `uv run ruff check src tests tools`. La suite completa **no** se corre en cada paso: solo al cerrar G-Gate (y una vez al cerrar G-3, que es la prueba de determinismo).
- Studio: este plan lo usa en un solo punto, el lote de cierre de G-Gate para los casos L7 y L9 (`uv run python tools/validar_caso_studio.py <caso>` y `tools/corpus_studio.py lote ...`). Si `sgm studio salud` no conecta, no reinstalar nada ni cambiar `talend-mcp` (`docs/guia-validacion-studio.md`, sección 7): «lote C pendiente» con su motivo; no se cuenta como pasada. Todo lo demás de este plan es anillo A y B (sin Studio).

## Review Focus

- **Un medidor que no mide no sirve:** cada medidor (G-3, G-5, G-8, G-9, G-15, G-17) tiene una prueba con un caso construido donde la cifra se conoce de antemano, y otra donde el dato falta y la salida dice «no medido», nunca 0 % ni 100 %. Tests en cada tarea.
- **El tablero no calcula, lee:** `tools/tablero_criterios.py` no corre pruebas ni migra; lee los JSON de `out/criterios/` con su fecha. Un JSON de más de 7 días se marca «vencido». Test en G-6.
- **Trinquetes, no metas:** G-8 (casos de `CONOCIDOS`), G-15 (programas que fallan) y G-16 (mutantes no detectados) fijan un tope que solo baja; cada entrada de una lista de excepciones lleva su plan dueño. Un caso que no se puede traducir queda en `tests/corpus/migrar_pendientes.yaml` con su motivo, no se quita del corpus.
- **Independencia del esperado:** los casos generados (G-11, G-12) y el generador de programas (G-13) calculan su esperado con código **independiente** de `src/sgm/ir/` y de `src/sgm/migrar/` (un oráculo escrito desde la página de la guía, como el de B-17 de `2026-11-11-mg-b-datastep-y-plan-logico.md`). Un esperado calculado con el propio intérprete no prueba el intérprete. Test en G-13.
- **C2 son dos propiedades:** (a) pasos del SAS igual a pasos traducidos más pasos pendientes, y (b) `sgm migrar` termina con código 0 y escribe sus archivos sobre cada programa del repositorio y sobre entradas basura. G-15 prueba la segunda sobre cada `.sas` versionado y sobre basura; la primera ya la vigila `tests/unit/test_invariantes_produccion.py` y no se repite.
- **Determinismo (C5):** no basta con comparar dos corridas con el mismo `PYTHONHASHSEED`. La causa típica de bytes distintos es iterar un `set` o un `dict` de claves de texto; la semilla de 0 a 9 la cambia. G-3 corre en procesos separados.
- **Seguridad de la salida:** los medidores escriben en `out/` y no copian texto de los programas del cliente a ningún informe versionado (solo conteos, nombres de caso y códigos `P-xxx`); G-15 comprueba que ninguna salida de un programa basura contenga el texto de la entrada.
- **Ningún medidor cambia la firma de los Jobs:** G-1 a G-20 no modifican `src/sgm/ir/`, `src/sgm/migrar/` ni `src/sgm/talend_item/`; los `test_golden*.py` deben seguir idénticos.

---

## Parte I. MG-P0 restante: preparación y tablero (12 h)

### Task G-1: Auditor de `PROGRESS.md` (MG-P0-01, parte 1; serie `n`)

El archivo mide miles de líneas, usa CRLF y trae series con letra (`103m`, `166` a `190`, `73c`). El plan maestro pide «sin números duplicados». Antes de ordenar nada hace falta una herramienta que **solo lea** y diga qué hay. Al redactar este plan, un conteo rápido dio 221 encabezados `## Hito` y ningún identificador (número más letra) repetido; los encabezados `## Decisiones` y `## Decisiones (hito N)` no son hitos y se ignoran. La auditoría dice si eso sigue siendo cierto y, si no, dónde.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\auditar_progress.py`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_auditar_progress.py`

**Interfaces:**
- Consumes: nada del código (lee `PROGRESS.md` como bytes).
- Produces:
  ```python
  @dataclass(frozen=True)
  class EntradaHito:
      numero: int          # 103
      letra: str           # "m" ("" si no tiene)
      titulo: str          # texto después del punto
      linea: int           # línea (base 1) del encabezado

  @dataclass(frozen=True)
  class Auditoria:
      entradas: tuple[EntradaHito, ...]
      repetidos: tuple[str, ...]        # identificadores "103m" que salen más de una vez
      fuera_de_orden: tuple[str, ...]   # "hito 40 (línea 900) viene después del hito 44 (línea 800)": solo dentro de una misma serie
      codificacion: str                 # "utf-8", "utf-8-bom", "ilegible"
      saltos_de_linea: dict[str, int]   # {"crlf": n, "lf": n, "cr": n}
      lineas_con_caracteres_raros: tuple[int, ...]   # U+FFFD o secuencias tipo "Ã©" (utf-8 leído como latin-1)

  def auditar(contenido: bytes) -> Auditoria: ...
  def ultimo_numero(auditoria: Auditoria) -> int: ...
  ```
  CLI: `uv run python tools/auditar_progress.py [--archivo PROGRESS.md] [--json]`; código de salida 0 si no hay repetidos ni caracteres raros, 1 si hay, 2 si el archivo no se puede leer. **No escribe en `PROGRESS.md` nunca.**

- [ ] **Step 1: Write the failing test.** En `tests/unit/test_auditar_progress.py`, con bytes construidos en la prueba: `b"## Hito 1. a\r\n## Hito 2. b\r\n## Hito 2. c\r\n"` da `repetidos == ("2",)` y `saltos_de_linea == {"crlf": 3, "lf": 0, "cr": 0}`; `b"## Hito 103m. x\n## Hito 104. y\n## Hito 104m. z\n"` no tiene repetidos (`104` y `104m` son series distintas, regla de AGENTS.md); `b"## Hito 5. a\n## Hito 3. b\n"` da un `fuera_de_orden` solo si ambos son de la misma serie (aquí sí); `"## Hito 7. caf\u00c3\u00a9\n".encode("utf-8")` marca la línea 1 en `lineas_con_caracteres_raros`; `b"\xef\xbb\xbf## Hito 1. a\n"` da `codificacion == "utf-8-bom"`; bytes inválidos como UTF-8 (`b"## Hito 1. \xe9\n"`) dan `"ilegible"` sin lanzar. Un encabezado `## Decisiones (hito 2)` no cuenta como hito. `ultimo_numero` sobre `103m, 198, 166` devuelve 198.
- [ ] **Step 2: Run test to verify it fails.** `uv run python -m pytest tests/unit/test_auditar_progress.py -q -p no:cacheprovider`; esperado: no existe el módulo.
- [ ] **Step 3: Implement** `auditar` con una expresión regular sobre líneas `^## Hito (\d+)([a-z]*)\b\.?\s*(.*)$`. Decodificar con `utf-8` estricto; si falla, `codificacion = "ilegible"` y analizar con `errors="replace"`. Los saltos se cuentan sobre los bytes (`\r\n`, `\n` solo, `\r` solo). Los caracteres raros: la línea contiene `\ufffd` o coincide con `[ÃÂ][\x80-\xbf\u00a0-\u00bf]`. Sin dependencias nuevas.
- [ ] **Step 4: Run test to verify it passes.** Correr la herramienta sobre el archivo real: `uv run python tools/auditar_progress.py --json` y **pegar la salida en el cuerpo de la entrada de `PROGRESS.md`** de este hito (cuántos hitos, repetidos, fuera de orden, líneas raras y saltos de línea). Si hay repetidos, listarlos: se resuelven en G-2, no aquí.
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N n: auditor de solo lectura de PROGRESS.md` (con la línea `Co-Authored-By`).

---

### Task G-2: Número siguiente por serie y procedimiento seguro de ordenado (MG-P0-01, cierre; serie `n`)

Cierra MG-P0-01: «sin números duplicados; enlace presente». Como `PROGRESS.md` no se reescribe a la ligera, el cierre es una **regla comprobable** (una prueba que impide que alguien introduzca un duplicado) más un procedimiento escrito, no un reordenado masivo.

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\auditar_progress.py` (opción `--siguiente`)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\docs\plan-reescritura\procedimiento-progress.md`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\docs\plan-reescritura\plan.md` (una línea que vincule el plan maestro y este procedimiento: MG-P0-01 pide «vincular este plan desde `plan.md`»; comprobar con `Grep` si ya está y no duplicarlo)
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_auditar_progress.py`

**Interfaces:**
- Consumes: `auditar(contenido: bytes) -> Auditoria`, `ultimo_numero(auditoria) -> int` (G-1).
- Produces:
  ```python
  def siguiente(auditoria: Auditoria, letra: str) -> str:
      """Identificador libre para la serie `letra`: ultimo_numero + 1 seguido de la letra
      (`siguiente(a, "n") == "199n"` si el último número usado en cualquier serie es 198)."""
  ```
  CLI: `uv run python tools/auditar_progress.py --siguiente n` imprime `199n`.

- [ ] **Step 1: Write the failing tests.** `siguiente(auditar(b"## Hito 198. a\n## Hito 103m. b\n"), "n") == "199n"`; con la letra vacía devuelve `"199"`. Y una prueba contra el archivo real: `test_progress_real_sin_identificadores_repetidos` lee `PROGRESS.md` del repositorio y exige `auditar(...).repetidos == ()` (esta prueba es el trinquete: si otra sesión duplica un número, falla con el identificador y las dos líneas).
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_auditar_progress.py -q -p no:cacheprovider -k "siguiente or real"`; esperado: `ImportError: siguiente`.
- [ ] **Step 3: Implement** `siguiente` y la opción `--siguiente LETRA` (imprime y sale con 0; no escribe nada). Si la prueba del archivo real falla porque hay repetidos de verdad, **no** reordenar: anotar los identificadores repetidos en `procedimiento-progress.md` y fijarlos como lista `CONOCIDOS_REPETIDOS` en la prueba con su causa (la entrada publicada no se renumera, AGENTS.md); la prueba exige entonces que no aparezca ningún repetido fuera de esa lista.
- [ ] **Step 4: Escribir** `docs/plan-reescritura/procedimiento-progress.md` (menos de 80 líneas, en español) con: cómo tomar el número (`--siguiente n`), qué hacer si dos sesiones chocan (la segunda toma el siguiente y lo anota en «Decisiones»), por qué no se reordena ni se cambia el final de línea (diff enorme y conflictos con la otra sesión), y el **único** procedimiento seguro para una reordenación futura si se decidiera: copia en `out/`, reordenar por bloques completos de `## Hito` (nunca línea a línea), comparar con `auditar` que el número de hitos y de líneas es idéntico y que `diff <(sort original) <(sort nuevo)` está vacío, y solo entonces reemplazar, en un commit aparte. Verificar el enlace en `plan.md`.
- [ ] **Step 5: Run** los tests de la tarea y `uv run ruff check src tests tools`. **Commit** `hito N n: siguiente numero por serie y procedimiento seguro para PROGRESS.md`.

---

### Task G-3: Prueba de determinismo con `PYTHONHASHSEED` de 0 a 9 sobre todo el corpus (criterio C5; MG-P10-01, parte determinista; serie `n`)

C5 dice «la misma entrada da exactamente los mismos bytes». Hoy lo prueba `tools/liberacion.py` (`_salida`: dos migraciones de **un** programa en el **mismo** proceso) y eso no detecta lo que cambia con la semilla de hash (iterar un `set` o un `dict` con claves de texto). Hay un antecedente: el hito 33 de `PROGRESS.md` anotó un fallo intermitente de `tests/unit/test_compile_outputs.py::test_guia_y_json_no_contienen_secretos_sin_enmascarar` («no reproducido»), y el hito 44 probó solo la compilación del programa grande con `PYTHONHASHSEED` de 0 a 9 sin coincidencias; la causa quedó «no determinada; si reaparece, anotar la lista `secrets` y la semilla». Esta tarea lo cierra **sobre el corpus completo** y con un proceso por semilla.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\programas_repo.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\determinismo.py`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_determinismo.py`

**Interfaces:**
- Consumes: `migrar(source: Path, out: Path, esquemas: Path | None = None, muestra: Path | None = None, backend: str = "archivos") -> ResultadoMigrar` (`src/sgm/cli_migrar.py:271`; campos `carpeta: Path` y `escritos: list[Path]`); `todos_los_casos(corpus: Path) -> list[Caso]` (`tools/corpus_lib/caso.py:216`; `Caso.programa` y `Caso.entradas`).
- Produces:
  ```python
  # tools/programas_repo.py
  def programas_del_repositorio(raiz: Path) -> list[Path]:
      """Cada `.sas` versionado (`git ls-files`; sin git, `rglob`), en orden estable por ruta
      relativa. G-15 lo reutiliza para el criterio C2."""

  # tools/determinismo.py
  def huella_de_programas(programas: list[Path], destino: Path) -> dict[str, dict[str, str]]:
      """Migra cada programa dentro de este proceso a `destino` y devuelve
      {ruta relativa del programa: {archivo relativo: sha256 hex}}. El `destino` es el mismo
      en cada semilla: la ruta de salida no puede ser una diferencia legítima."""

  def comparar_huellas(por_semilla: dict[int, dict[str, dict[str, str]]]) -> list[dict]:
      """Lista de {"programa", "archivo", "semillas": [..]} con las semillas cuyo hash difiere
      del de la menor semilla. Vacía si todo coincide."""

  def correr(raiz: Path, semillas: range = range(10)) -> dict:
      """Un subproceso por semilla (`PYTHONHASHSEED=<k>`, `python tools/determinismo.py --worker`)
      y escribe `out/criterios/c5_determinismo.json` con fecha, cifra, semillas, programas,
      archivos y diferencias."""
  ```
  CLI: `uv run python tools/determinismo.py [--semillas 10] [--raiz .]`; código 0 si no hay diferencias, 1 si las hay. Modo interno `--worker --lista <archivo> --salida <json>`.

- [ ] **Step 1: Write the failing tests.** En `tests/unit/test_determinismo.py`: (a) `comparar_huellas({0: {"p.sas": {"a.item": "x"}}, 1: {"p.sas": {"a.item": "x"}}, 2: {"p.sas": {"a.item": "y"}}})` devuelve `[{"programa": "p.sas", "archivo": "a.item", "semillas": [2]}]`; con tres huellas iguales, `[]`; un archivo que falta en una semilla cuenta como diferencia (su hash es `None`). (b) `programas_del_repositorio(tmp_path)` sobre una carpeta sin git con `b/z.sas`, `a/y.SAS` y `a/x.txt` devuelve las dos rutas de SAS en el orden `a/y.SAS`, `b/z.sas`. (c) Integración con dos programas pequeños del corpus (`L0/l0_01_where_sentencia/programa.sas` y `L1/l1_01_select_columnas/programa.sas`) y las semillas 0 y 1: `correr(...)` devuelve `diferencias == []` y `archivos > 0`.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_determinismo.py -q -p no:cacheprovider`; esperado: no existe el módulo.
- [ ] **Step 3: Implement.** `programas_del_repositorio` con `git ls-files` (`subprocess.run(["git", "ls-files", "*.sas", "*.SAS"], cwd=raiz)`); si falla, `rglob` sin distinguir mayúsculas. `huella_de_programas` llama a `migrar` por programa (con `muestra=<carpeta entradas>` cuando el programa es el `programa.sas` de un caso con carpeta `entradas/`, como en `tests/unit/test_migrar_corpus_aceptacion.py`), calcula `hashlib.sha256` de cada archivo de `resultado.carpeta` (recorrido ordenado) y limpia el destino entre programas. `correr` lanza `[sys.executable, "tools/determinismo.py", "--worker", ...]` con `env={**os.environ, "PYTHONHASHSEED": str(k)}`, de a un subproceso (el destino es compartido) y escribe el JSON. Nada de rutas absolutas ni texto del programa en el JSON: solo ruta relativa, nombre de archivo y semillas.
- [ ] **Step 4: Run tests to verify they pass.** Luego la corrida real: `uv run python tools/determinismo.py --semillas 10` (corpus L0 a L8 más fixtures; si tarda más de 10 minutos, correrla en segundo plano). Si hay diferencias: **no** se arreglan aquí; cada una se anota en `PROGRESS.md` con programa, archivo y semillas y se pide el arreglo al plan dueño de la zona (emisor: Plan F2; plan lógico: Plan B). El criterio C5 queda en el tablero como `N de M archivos estables`, no como 100 % supuesto. Anotar también el número real de programas que enumera `programas_del_repositorio`: el plan maestro dice 189 y `git ls-files '*.sas'` dio 375 al redactar este plan; la cifra de C2 se corrige en el plan maestro con lo que excluya el conteo (verificar al ejecutar qué carpetas cuenta el 189).
- [ ] **Step 5: Reabrir el hito 33.** Correr diez veces la prueba del antecedente, una por semilla: `for s in 0 1 2 3 4 5 6 7 8 9; do PYTHONHASHSEED=$s uv run python -m pytest tests/unit/test_compile_outputs.py -q -p no:cacheprovider -k secretos_sin_enmascarar || echo "FALLA semilla $s"; done` (en PowerShell: `0..9 | ForEach-Object { $env:PYTHONHASHSEED=$_; uv run python -m pytest ... }`). Anotar el resultado en `PROGRESS.md` (diez de diez, o la semilla y la lista `secrets` que muestra pytest). Correr una vez la suite completa (`uv run python -m pytest -q`) y anotar el conteo.
- [ ] **Step 6: Run** `uv run ruff check src tests tools`. **Commit** `hito N n: determinismo con PYTHONHASHSEED de 0 a 9 sobre todo el corpus` (con la línea `Co-Authored-By`).

---

### Task G-4: Un comando recalcula la tabla 11b desde un YAML de créditos (MG-P0-05, parte 1; serie `n`)

Hoy la tabla «Avance medido» (sección 11b del plan maestro) se recalcula a mano: el viernes se suman créditos, se divide y se reescribe. El método es fijo («cada tarea aporta sus horas multiplicadas por un crédito: 1, 0,5, 0,25 o 0»), así que es un cálculo. El YAML es la **fuente** de los créditos; la tabla del plan es la **salida**. Se conserva el juicio humano (los créditos) y se automatiza la aritmética.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\avance_creditos.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\docs\plan-reescritura\creditos.yaml` (lo genera `--importar` desde la tabla actual; no se copia a mano)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\docs\plan-reescritura\plan-migrador-general.md` (solo dos líneas de marca, `<!-- avance:inicio -->` y `<!-- avance:fin -->`, alrededor de la tabla de la sección 11b que empieza en «| Fase | Horas | Crédito | % de la fase | Qué sostiene la cifra |»; otras sesiones editan el plan maestro: mirar `git status` y hacer el cambio con `Edit` de esas dos líneas, nunca reescribir la sección)
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_avance_creditos.py`

**Interfaces:**
- Consumes: `yaml.safe_load` y `yaml.safe_dump` (pyyaml, ya dependencia).
- Produces:
  ```python
  @dataclass(frozen=True)
  class Fase:
      id: str                        # "MG-P5"
      nombre: str                    # "`PROC SQL`"
      horas: float                   # 80
      credito_sin_desglosar: float   # 37.0: crédito todavía no repartido por tarea
      tareas: tuple[tuple[str, float, float], ...]  # (id "MG-P5-02", horas, fraccion 0..1)
      sostiene: str                  # texto de la columna «Qué sostiene la cifra»

  def cargar(ruta: Path) -> tuple[Fase, ...]: ...         # ValueError si fraccion fuera de [0,1], ids repetidos u horas de tareas > horas de la fase
  def credito(fase: Fase) -> float: ...                    # credito_sin_desglosar + sum(horas * fraccion)
  def porcentaje(horas: float, credito: float) -> int: ... # redondeo medio hacia arriba: porcentaje(37, 25.0) == 68
  def formato_credito(valor: float) -> str: ...           # 25.0 -> "25,0"; 0.75 -> "0,75"; 237.25 -> "237,25"
  def tabla_markdown(fases: tuple[Fase, ...]) -> str: ... # cabecera, una fila por fase y fila "**Total**" con un decimal en el %
  def importar(plan: Path) -> str: ...                    # lee la tabla actual y devuelve el YAML inicial
  def actualizar_plan(plan: Path, tabla: str) -> bool: ... # reemplaza solo lo de entre las marcas; False si no hay marcas
  ```
  CLI: `uv run python tools/avance_creditos.py [--yaml RUTA] [--plan RUTA] (--importar | --imprimir | --actualizar | --verificar)`. `--verificar` sale con 1 si la tabla del plan no es la que sale del YAML. Lo que se corre un viernes: editar una línea de `creditos.yaml` y correr `--actualizar`.

- [ ] **Step 1: Write the failing tests.** Con un YAML mínimo en `tmp_path`: una fase `MG-P0` de 37 h con `credito_sin_desglosar: 25.0` da `credito == 25.0`, `porcentaje(37, 25.0) == 68` y la fila `| MG-P0 Preparación | 37 | 25,0 | 68 % | ... |`; una fase con `credito_sin_desglosar: 10.0` y `tareas: [[MG-P5-02, 8, 0.5]]` da `credito == 14.0`; `formato_credito(0.75) == "0,75"` y `formato_credito(237.25) == "237,25"`; el total de fases que suman 895 h y 237,25 de crédito imprime `| **Total** | **895** | **237,25** | **26,5 %** | |`; `cargar` lanza `ValueError` con el id si una fracción es `1.5`, si dos tareas repiten id o si las horas de las tareas superan las de la fase; `actualizar_plan` sobre un Markdown con marcas cambia solo lo de entre ellas (el resto, idéntico byte a byte) y devuelve `False` sin marcas.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_avance_creditos.py -q -p no:cacheprovider`; esperado: no existe el módulo.
- [ ] **Step 3: Implement** el módulo (menos de 200 líneas). `importar` parsea las filas `| MG-P<n> ... | horas | crédito | % | sostiene |` (con comas decimales), conserva la columna «Qué sostiene la cifra» tal cual y pone todo el crédito en `credito_sin_desglosar`: es honesto, porque el desglose por tarea no está registrado en ninguna parte. Escribir con `yaml.safe_dump(..., allow_unicode=True, sort_keys=False)`.
- [ ] **Step 4: Run tests to verify they pass.** Poner las dos marcas en el plan maestro, correr `uv run python tools/avance_creditos.py --importar > docs/plan-reescritura/creditos.yaml` y comprobar `--verificar`: la tabla regenerada debe ser **idéntica** a la actual (si difiere en el redondeo o el formato se ajustan `porcentaje` y `formato_credito`, no el YAML). Anotar de paso que la frase «Reparto del trabajo restante (719,25 h)» de la sección 11b no coincide con 895 − 237,25 = 657,75: la herramienta imprime `restante = horas − crédito` y, si no cuadra con el texto del plan, **se corrige el texto del plan en el mismo cambio** (AGENTS.md: el plan no se contradice con el código); verificar al ejecutar cuál es la cifra vigente y qué incluye `reparto-andres-byron.md`.
- [ ] **Step 5: Agregar la prueba de coherencia** `test_la_tabla_del_plan_sale_del_yaml` (llama a `--verificar` por función) en `tests/unit/test_avance_creditos.py`. Es el trinquete: nadie edita la tabla a mano sin pasar por el YAML. Si otra sesión edita la tabla del plan a mano mientras se ejecuta esta tarea, regenerar el YAML con `--importar` antes de correr la prueba.
- [ ] **Step 6: Run** `uv run ruff check src tests tools`. **Commit** `hito N n: la tabla 11b sale de un YAML de creditos con un comando`.

---

### Task G-5: Termómetro por regiones del programa real grande (MG-P10-09, parte 1; serie `n`)

Las horas dependen de un juicio; el termómetro directo no. Para el programa grande del cliente, el diseño ya divide el SAS en regiones (`decisiones/<programa>.agrupacion.yaml` trae el marcador). Esta tarea mide, **por región**, cuántas líneas del SAS quedaron cubiertas por nodos emitidos y cuántas por un pendiente: «la región 7 está al 40 %» dice dónde cerrar brechas.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\termometro_regiones.py`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_termometro_regiones.py`

**Interfaces:**
- Consumes: `dividir_regiones(texto: str, marcador: str) -> list[Region]` y `region_de_linea(regiones: list[Region], linea: int) -> int` (`src/sgm/flow/regiones.py:46,72`; `Region` trae `indice`, `linea_inicio`, `linea_fin`, `etiquetas`); `cargar_declaracion(ruta)` de `sgm.agrupacion` (su resultado trae `.marcador`, como lo usa `tools/medir_regiones.py:35`); `migrar(...) -> ResultadoMigrar` con `traza: dict[str, list[int]]` (nodo a líneas del SAS) y `pendientes: list[PendienteMigracion]` (`src/sgm/migrar/esquemas.py:52`; campos `codigo`, `motivo`, `linea`).
- Produces:
  ```python
  @dataclass(frozen=True)
  class FilaRegion:
      indice: int
      linea_inicio: int
      linea_fin: int
      lineas_traducidas: int      # líneas distintas del SAS con al menos un nodo en la traza
      lineas_pendientes: int      # líneas distintas con un pendiente con línea y sin nodo
      pendientes_sin_linea: int   # pendientes con linea None: no se reparten por región
      porcentaje: int | None      # round(100 * traducidas / (traducidas + pendientes)); None si la región no tiene pasos

  def termometro(texto: str, marcador: str, traza: dict[str, list[int]], pendientes: list) -> list[FilaRegion]: ...
  def a_markdown(filas: list[FilaRegion]) -> str: ...
  ```
  CLI: `uv run python tools/termometro_regiones.py --sas RUTA.sas --agrupacion RUTA.agrupacion.yaml [--json]`; escribe `out/criterios/termometro_regiones.json` (solo conteos por región, **sin texto del SAS**).

- [ ] **Step 1: Write the failing test.** Con un SAS de seis líneas dividido por el marcador `%macro` en dos regiones (líneas 1 a 3 y 4 a 6), traza `{"tMap_1": [1, 2], "tSortRow_1": [5]}` y un pendiente en la línea 6: `termometro(...)` devuelve la región 0 con `lineas_traducidas == 2`, `lineas_pendientes == 0`, `porcentaje == 100` y la región 1 con `lineas_traducidas == 1`, `lineas_pendientes == 1`, `porcentaje == 50`; un pendiente con `linea=None` suma a `pendientes_sin_linea` de la región 0 y **no** cambia el porcentaje; una región sin ninguna línea cubierta ni pendiente tiene `porcentaje is None` (no 0 ni 100).
- [ ] **Step 2: Run test to verify it fails.** `uv run python -m pytest tests/unit/test_termometro_regiones.py -q -p no:cacheprovider`; esperado: no existe el módulo.
- [ ] **Step 3: Implement** `termometro` con `region_de_linea` y `a_markdown` (una fila por región: rango, traducidas, pendientes, porcentaje o «sin pasos»). El `main` migra el programa a una carpeta temporal con `migrar(Path(sas), tmp)` y escribe el JSON.
- [ ] **Step 4: Run test to verify it passes.** Correr sobre el programa grande real: `uv run python tools/termometro_regiones.py --sas tests/fixtures/sas/client/client_large.sas --agrupacion decisiones/client_large.agrupacion.yaml` (los nombres de archivo solo se pasan por argumento, nunca se escriben en `tools/` ni en `src/`). Pegar la tabla por regiones en `PROGRESS.md` como **línea base** del termómetro; los pendientes sin línea se informan aparte (cantidad), no se reparten.
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N n: termometro por regiones del programa real grande`.

---

### Task G-6: Tablero único de criterios C1 a C6 y tiempos del ciclo rápido (MG-P0-05, cierre; tiempos de MG-P0-04 y P0-09; serie `n`)

`tools/tablero.py` (240 líneas) ya fotografía la sección 2 del plan (componentes, conformidad, pendientes del modelo, casos del corpus). MG-P0-05 pide que incluya «las cifras de la sección 1»: C1 a C6. El tablero **no calcula**: cada criterio tiene su medidor (G-3, G-8, G-15, G-17, `tools/calidad_jobs.py` del Plan F1, `tools/liberacion.py`) que escribe `out/criterios/<criterio>.json`; el tablero los lee y dice «no medido» donde falta.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\tablero_criterios.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\medir_tiempos.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\tablero.py` (importar `filas_criterios` y sumarlas a `filas_tablero`; el archivo queda bajo 260 líneas)
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_tablero_criterios.py`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_tablero.py` (una prueba nueva; las existentes no cambian)

**Interfaces:**
- Consumes: `filas_tablero(programa: Path, carpeta_corpus: Path, con_suite: bool) -> list[tuple[str, str]]` (`tools/tablero.py:155`); `ciclo_rapido.main(argv=None, *, archivos=None, ejecutar=None, salida=print) -> int` (`tools/ciclo_rapido.py:71`; imprime `<nombre>: <s> s (código N)` por comando).
- Produces:
  ```python
  # tools/tablero_criterios.py
  CRITERIOS: dict[str, tuple[str, str]]
  # {"C1": ("c1_cobertura.json", "G-17"), "C2": ("c2_robustez.json", "G-15"),
  #  "C3": ("c3_anillo_b.json", "G-8"), "C4": ("c4_calidad.json", "Plan F1, F1-5"),
  #  "C5": ("c5_determinismo.json", "G-3"), "C6": ("c6_liberacion.json", "tools/liberacion.py")}

  def leer_criterio(carpeta: Path, criterio: str, hoy: date) -> dict:
      """{"estado": "medido" | "vencido" | "no medido", "cifra": str, "fecha": str | None, "motivo": str}.
      Vencido: el JSON tiene más de 7 días. No medido: no existe el archivo (el motivo dice qué
      comando lo escribe) o no se puede leer."""

  def filas_criterios(carpeta: Path, hoy: date) -> list[tuple[str, str]]: ...

  # tools/medir_tiempos.py
  def medir_ciclo(archivos: list[str], ejecutar=None) -> dict[str, float]:
      """Segundos por comando del ciclo rápido y total, usando `ciclo_rapido.main` con `salida`
      capturada. Escribe `out/criterios/tiempos.json`."""
  ```
  Cada JSON de criterio trae `{"fecha": "AAAA-MM-DD", "cifra": "<texto corto>", "detalle": {...}}`; es el contrato que cumplen G-3, G-8, G-15, G-17 y `calidad_jobs.py` (Plan F1; si todavía no escribe el JSON, el tablero dice «no medido: falta `tools/calidad_jobs.py` (Plan F1, F1-5)» y G-Gate no se cierra sin él). Para C6, `tools/liberacion.py` (205 líneas) no se modifica: si no escribe un JSON, el tablero dice «no medido: correr `tools/liberacion.py`» y G-Gate anota el resultado a mano.

- [ ] **Step 1: Write the failing tests.** `leer_criterio(tmp_path, "C5", date(2026, 11, 12))` sin archivo devuelve `estado == "no medido"` y un motivo que contiene `determinismo.py`; con `{"fecha": "2026-11-11", "cifra": "10 de 10 semillas iguales"}` devuelve `medido` y esa cifra; con fecha `2026-11-01` devuelve `vencido`; con un JSON corrupto devuelve `no medido` sin lanzar. `filas_criterios` devuelve seis filas en el orden C1 a C6. `medir_ciclo(["tests/corpus/L0/l0_01_where_sentencia/programa.sas"], ejecutar=lambda c: 0)` suma los segundos de los comandos y no ejecuta nada real. Prueba nueva en `test_tablero.py`: `filas_tablero(...)` incluye una fila que empieza con `C5` (con la carpeta de criterios apuntando a un `tmp_path` vacío dice «no medido»).
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_tablero_criterios.py tests/unit/test_tablero.py -q -p no:cacheprovider`; esperado: no existe el módulo.
- [ ] **Step 3: Implement** `tablero_criterios.py` y `medir_tiempos.py` (con `Path("out/criterios")` por defecto y la fecha inyectable). En `tablero.py`: `from tablero_criterios import filas_criterios` (las herramientas de `tools/` se importan entre sí) y `filas += filas_criterios(...)`. No tocar las filas existentes ni `--suite`.
- [ ] **Step 4: Run tests to verify they pass**, luego `uv run python tools/tablero.py --markdown` (los criterios sin medidor dicen «no medido» y de quién es la tarea). Medir el tiempo del ciclo rápido para el criterio de MG-P0-04 (menos de 90 s con 20 casos): `uv run python tools/medir_tiempos.py --casos 20` toma 20 casos del corpus como si hubieran cambiado; anotar los segundos reales en `PROGRESS.md`. Si pasan de 90 s, **no se cambia el criterio**: se anota el tiempo y el comando más lento. Para MG-P0-09 (50 Jobs compilados en menos de 2 min) hace falta Studio: «lote C pendiente» salvo que `sgm studio salud` conecte; no reinstalar nada.
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N n: tablero unico con C1 a C6 y tiempos del ciclo rapido`.

---

### Task G-7: `docs/arquitectura/ir-logica.md`: cómo se reutiliza el IR que ya existe (MG-P0-06; serie `n`)

El plan maestro dice «no se crea un IR paralelo». Esta tarea lo deja escrito con ejemplos **que se ejecutan**: una prueba corre cada bloque de código del documento, de modo que el documento no puede quedar distinto del código.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\docs\arquitectura\ir-logica.md` (la carpeta `docs/arquitectura/` no existe: se crea con el archivo)
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_ir_logica_doc.py`

**Interfaces:**
- Consumes (de `src/sgm/ir/operadores.py` y `src/sgm/ir/models.py`): los constructores `leer`, `leer_archivo`, `escribir`, `escribir_archivo`, `filtrar`, `proyectar`, `renombrar`, `calcular`, `unir`, `combinar`, `agregar`, `ordenar`, `deduplicar`, `concatenar`, `pivotar`, `iterar` y `controlar` (17 funciones públicas; por ejemplo `unir(op_id, join_type, keys, sources, condition=None, evidence=None) -> Operator`, `operadores.py:196`); `Operator`, `Graph` (`add_operator`, `add_edge`, `topological`, `operators`, `edges`), `Edge` y `Plan` (`models.py:69,101,94,309`); los mapeos de `rules/mapping/*.yaml` (por ejemplo `02-filter.yaml`, `02-aggregate.yaml`, `02-dedup.yaml`).
- Produces: el documento y las pruebas `test_el_documento_ejecuta_sus_ejemplos` (extrae cada bloque de código Python del documento y lo ejecuta con `exec` en un espacio de nombres limpio) y `test_el_documento_nombra_todos_los_operadores` (cada función pública de `operadores.py` que devuelve un `Operator` aparece en el documento como `` `nombre(` ``; un operador nuevo sin documentar hace fallar la prueba).

- [ ] **Step 1: Write the failing tests.** `test_el_documento_nombra_todos_los_operadores` obtiene los nombres con `inspect.getmembers(operadores, inspect.isfunction)`, quita los que empiezan con `_` y los de otro módulo, y exige que cada uno esté en el texto. `test_el_documento_ejecuta_sus_ejemplos` exige al menos un bloque de código por operador y que todos terminen sin excepción. Fallan: no existe el documento.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_ir_logica_doc.py -q -p no:cacheprovider`; esperado: `FileNotFoundError`.
- [ ] **Step 3: Write** el documento (en español, menos de 300 líneas) con cinco secciones: (1) *Qué es y qué no es*: el IR lógico **es** `ir/models.py` (`Operator`, `Graph`, `Plan`); no hay un segundo; (2) *Los operadores*: una tabla y, por operador, un ejemplo ejecutable de 3 a 8 líneas que lo construye con el constructor real y lo agrega a un `Graph`, con los parámetros que lleva; (3) *Dónde se enriquecen los parámetros*: los que los planes B, C y E añaden (alias de tablas del auto-unión, tipo de unión `full`/`right`, `by` y `retain`, variables macro resueltas), cada uno con el plan y la tarea que lo aporta; los que todavía no existen se marcan «propuesto por el Plan X, tarea Y» con el nombre real de esa tarea, sin inventar parámetros; (4) *De operador a componente*: cómo `rules/mapping/*.yaml` elige el candidato de componente, con un ejemplo que lee `02-filter.yaml` con `yaml.safe_load` y muestra sus claves reales; (5) *Cómo se comprueba*: los anillos A y B sobre el mismo plan (`plan_a_jobs` y `ejecutar_plan`). Los ejemplos importan solo de `sgm.ir`.
- [ ] **Step 4: Run tests to verify they pass.** Si un ejemplo no corre porque la firma real difiere de lo esperado, **se corrige el documento**, no el código.
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N n: documento del IR logico con ejemplos ejecutables`.

---

## Parte II. MG-P10 restante: verificación y equivalencia (56 h)

### Task G-8: Medidor del anillo B, lista de `xfail` con dueño y trinquete (MG-P10-01; criterio C3; serie `n`)

MG-P10-01 pide «todos los casos `traducible` del corpus dan su `esperado/`». Hoy `tests/unit/test_migrar_corpus_anillo_b.py` recorre `L0` a `L6` y marca `xfail(strict=True)` los casos de `CONOCIDOS`; al redactar este plan eran **5** (`l2_12_auto_join_misma_ciudad`, `l3_07_total_origen_y_salida`, `l3_09_conciliacion_diferencia_plantada`, `l5_08_str_filtro_completo`, `l5_09_into_primer_fila`), y el anillo A tiene 16 casos más en `tests/corpus/migrar_pendientes.yaml`. Esta tarea no implementa semántica (es de los planes B, C y E): **mide** (cuáles quedan, con su motivo), **asigna dueño** a cada uno y **fija el tope** para que la lista solo baje.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\corpus_lib\anillo_b.py` (las dos funciones auxiliares que hoy son privadas del archivo de la prueba, para que el medidor y la prueba usen exactamente el mismo comparador)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_migrar_corpus_anillo_b.py` (solo reemplazar `_entradas` y `_esperado` por imports de `anillo_b`; **no tocar `CONOCIDOS`**, que editan los planes B, C y E; si hay conflicto, rebase y conservar sus entradas)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\medir_anillo_b.py`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_medir_anillo_b.py`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_anillo_b_conocidos.py`

**Interfaces:**
- Consumes: `ejecutar_plan(plan: Plan, entradas: dict[str, list[dict[str, str | None]]]) -> dict[str, list[dict[str, str | None]]]` (`src/sgm/migrar/interprete.py:1076`); `compile_file(analysis, program, ctx_base) -> Compiled`, `project_base()`, `analyze_program(files, external_files=None)`; `comparar_con_guardado(ruta: Path, tabla: Tabla, tolerancia: float, orden_relevante: bool) -> list[str]` y `leer_entradas` (`tools/corpus_lib/csv_tabla.py`); `casos_de_nivel(corpus, nivel) -> list[Caso]`.
- Produces:
  ```python
  # tools/corpus_lib/anillo_b.py
  def entradas_de(caso: Caso) -> dict[str, list[dict]]: ...                    # el cuerpo de `_entradas`
  def diferencias_de_tabla(caso: Caso, tabla: str, filas: list[dict]) -> list[str]: ...  # el cuerpo de `_esperado`
  def diferencias_de_caso(caso: Caso) -> list[str]:
      """Compila el programa del caso, ejecuta el plan y compara cada salida con `esperado/`.
      Una excepción del intérprete (`NoSoportadoEnInterprete` u otra) es una diferencia con su texto."""

  # tools/medir_anillo_b.py
  def medir(corpus: Path, conocidos: dict[str, str], niveles: tuple[str, ...] = ("L0", "L1", "L2", "L3", "L4", "L5", "L6", "L7", "L9"),
            estados: tuple[str, ...] = ("traducible", "revisado")) -> dict:
      """{"elegibles": n, "pasan": n, "xfail": {caso: motivo}, "fallan": {caso: [diferencias]},
      "xpass": [casos de `conocidos` que ya pasan], "pendientes_anillo_a": n}. Escribe
      `out/criterios/c3_anillo_b.json` con `cifra` = "N de M casos elegibles pasan; K conocidos"."""
  ```
  CLI: `uv run python tools/medir_anillo_b.py` (carga `CONOCIDOS` leyendo el archivo de la prueba con `importlib.util.spec_from_file_location`; salida 1 si hay `fallan` o `xpass`).

- [ ] **Step 1: Write the failing tests.** `test_medir_anillo_b.py` con un corpus mínimo en `tmp_path` (un caso `L1` cuyo `esperado` es correcto, uno con una celda alterada y uno listado en `conocidos`): `medir(...)` da `elegibles == 3`, `pasan == 1`, `fallan` con el caso alterado y `xfail` con el tercero; un caso de `conocidos` que ya pasa aparece en `xpass`; un nivel que no existe se ignora sin error. `test_anillo_b_conocidos.py`: `DUEÑOS: dict[str, str]` fija el plan dueño de cada entrada de `CONOCIDOS` (`l2_12_auto_join_misma_ciudad` y `l3_09_conciliacion_diferencia_plantada` y `l3_07_total_origen_y_salida`: Plan C; `l5_08_str_filtro_completo` y `l5_09_into_primer_fila`: Plan E; confirmar con la tarea de cada plan al ejecutar y escribir el id de la tarea, por ejemplo `Plan C, C-9`); la prueba exige que toda clave de `CONOCIDOS` tenga dueño, que `len(CONOCIDOS) <= TOPE` (`TOPE = 5` al redactar) y que `DUEÑOS` no tenga claves que ya no estén en `CONOCIDOS` (obliga a quitar la fila al cerrar el caso).
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_medir_anillo_b.py tests/unit/test_anillo_b_conocidos.py -q -p no:cacheprovider`; esperado: no existe el módulo.
- [ ] **Step 3: Extraer sin cambiar comportamiento.** Mover `_entradas` y `_esperado` a `corpus_lib/anillo_b.py` y que la prueba los importe. Correr `tests/unit/test_migrar_corpus_anillo_b.py` antes y después: **el mismo número de pasadas y de `xfail`** (anotarlo). Implementar `diferencias_de_caso` y `medir`.
- [ ] **Step 4: Run tests to verify they pass** y correr `uv run python tools/medir_anillo_b.py`. Pegar en `PROGRESS.md`: elegibles, pasan, los `xfail` con su motivo y su dueño, y los pendientes del anillo A. Esa es la respuesta a «di cuáles quedan». Si algún caso `L7` o `L9` ya existe (G-11, G-12) y no pasa, aparece en `fallan`, no en una lista aparte.
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N n: medidor del anillo B, xfail con dueno y tope`.

---

### Task G-9: Cada expresión Java generada compila sola con `javac` (MG-P10-03; serie `n`)

El anillo A del plan maestro incluye «las expresiones Java generadas compilan con `javac` suelto sobre un molde mínimo». Hoy solo hay una prueba con un filtro (`tests/unit/test_desde_plan.py:864`, `skipif` sin `javac`). Esta tarea la generaliza: **todas** las expresiones Java que salen de migrar el corpus se compilan en un solo archivo de molde (una `javac` por lote, no una por expresión).

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\java_suelto.py`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_java_suelto.py`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_expresiones_java_compilan.py`

**Interfaces:**
- Consumes: `Job` y `Nodo` (`src/sgm/talend_item/modelo.py`: `Nodo.componente`, `unico`, `parametros: list[Fila | Tabla]`, `columnas: list[Columna]`; `Fila = tuple[str, str, str | None, str | None]` o sea `(campo, nombre, valor, show)`; `Columna.nombre`, `Columna.tipo` como `id_Integer`); `migrar(...) -> ResultadoMigrar` (`.jobs`); `translate_to_talend(sas: str, entrada: str = "input_row") -> Result` (`src/sgm/expressions/talend_translator.py:20`; `Result.java`, `.columns`).
- Produces:
  ```python
  @dataclass(frozen=True)
  class ExpresionJava:
      job: str
      nodo: str                       # unique name, p. ej. "tFilterRow_1"
      parametro: str                  # nombre del campo del nodo
      java: str                       # la expresión ya sin escapes XML
      columnas: dict[str, str]        # nombre -> tipo Java ("Integer", "String", ...)
      usa_rutinas: bool               # llama a `routines.` o a `TalendDate.`/`StringHandling.`

  def buscar_jdk() -> Path | None:
      """`shutil.which("javac")`, luego `SGM_JDK` y `JAVA_HOME` (carpeta `bin/javac`). None si no hay."""

  def extraer_expresiones(jobs: list[Job]) -> list[ExpresionJava]: ...
  def tipo_java(tipo_talend: str) -> str: ...   # id_String -> String, id_Integer -> Integer, id_Long -> Long, id_Double -> Double, id_BigDecimal -> java.math.BigDecimal, id_Date -> java.util.Date, id_Boolean -> Boolean
  def molde(expresiones: list[ExpresionJava]) -> str: ...   # una clase con un método estático por expresión
  def compilar(expresiones: list[ExpresionJava], jdk: Path, trabajo: Path) -> list[dict]:
      """Lista de {"nodo", "parametro", "error"} de lo que no compiló (vacía si todo compila).
      Las que usan rutinas de Talend solo se compilan si `SGM_ROUTINES_JAR` apunta al jar
      (o carpeta de fuentes) de las rutinas; si no, se cuentan aparte como no medidas."""
  ```
  CLI: `uv run python tools/java_suelto.py [--corpus tests/corpus]` escribe `out/criterios/java_suelto.json` (`cifra` = «N de M compilan; K con rutinas no medidas»).

- [ ] **Step 1: Inventario real.** Antes de escribir código, listar qué parámetros llevan Java en los Jobs del corpus: `Grep` de `ADVANCED_COND`, `EXPRESSION` y `CODE` en `src/sgm/talend_item/desde_plan_expresiones.py`, `desde_plan_map.py` y `filtros_fila.py`, y escribir la lista de nombres de campo que `extraer_expresiones` reconoce (las expresiones de un `tMap` están en `Nodo.datos`, el XML de `<nodeData>`: se leen las `expression="..."` de sus entradas). Un campo que contenga Java y no esté en la lista es un hueco del medidor: se anota en `PROGRESS.md`.
- [ ] **Step 2: Write the failing tests.** `test_java_suelto.py`: `tipo_java("id_Integer") == "Integer"`; `molde([ExpresionJava("j", "tFilterRow_1", "ADVANCED_COND", "row1.saldo > 0", {"saldo": "Integer"}, False)])` contiene `static class Row { Integer saldo; }` y un método que devuelve esa expresión; `buscar_jdk()` con `SGM_JDK` apuntando a una carpeta falsa devuelve `None`. Con JDK (`skipif(buscar_jdk() is None, reason="sin JDK: javac no está en el PATH")`): `compilar` de una expresión válida devuelve `[]` y de `row1.saldo >` (inválida, plantada) devuelve un fallo con el nodo. `test_expresiones_java_compilan.py`: migra cada caso `traducible` de `L0` a `L6` a una carpeta temporal, extrae las expresiones, exige `len(expresiones) >= 40` (cifra a confirmar con el inventario del paso 1) y que `compilar` devuelva `[]`; sin JDK la prueba se salta con motivo y la cifra queda «no medido» en el tablero.
- [ ] **Step 3: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_java_suelto.py tests/unit/test_expresiones_java_compilan.py -q -p no:cacheprovider`; esperado: no existe el módulo.
- [ ] **Step 4: Implement.** `molde` genera una sola clase `Molde` con `static class Row` por tabla de columnas distinta, un método `static Object e<N>(Row row1) { return (<java>); }` por expresión y un `main` vacío; los `&lt;`, `&gt;`, `&amp;` se desescapan igual que en la prueba existente. `compilar` escribe el molde en `trabajo` y llama `javac -d <trabajo>`; asocia cada línea de error con su método por el número de línea. La ejecución (`java -cp`) no se hace aquí: el comportamiento lo cubren el anillo B y el lote C.
- [ ] **Step 5: Run tests to verify they pass.** Si `javac` no está en el PATH de esta máquina (al redactar este plan no lo estaba), buscar el JDK que usa Studio y exportarlo con `SGM_JDK` solo para la corrida (no se escribe en ningún archivo); si no hay ninguno, registrar «no medido: sin JDK» en el JSON y cerrar la tarea sin contarla como pasada (G-Gate la exige medida). Cada expresión que no compile es un defecto del emisor: se anota con su nodo y se pide el arreglo al Plan F2 (emisor); no se corrige aquí.
- [ ] **Step 6: Run** `uv run ruff check src tests tools`. **Commit** `hito N n: expresiones Java del corpus compiladas con javac suelto`.

---

### Task G-10: Biblioteca de etapas y generador de casos L7 y L9 con anomalías plantadas (MG-P10-04, parte 1; serie `n`)

L7 = programa de varias etapas con rechazos y conciliación; L9 = programa grande con datos simulados. A mano serían 40 carpetas distintas con esperados escritos a mano. Se generan: una **biblioteca de etapas** (cada una trae su SAS y su transformación de referencia en Python, escrita desde la semántica documentada y **sin importar `sgm.ir` ni `sgm.migrar`**), y un generador que compone etapas, siembra anomalías conocidas en los datos y escribe el caso con su `esperado/` por construcción. El patrón es el de `tools/corpus_lib/especificaciones_l6.py` más `datos_ficticios.py` (`col`, `generar_tabla`, `escribir_entrada`).

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\corpus_lib\etapas.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\corpus_lib\generar_l7l9.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\generar_l7l9.py` (CLI)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_migrar_corpus_anillo_b.py` (solo la tupla `NIVELES`: agregar `"L7"` y `"L9"`; los niveles que no existen todavía se ignoran, `casos_de_nivel` ya lo tolera)
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_etapas.py`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_generar_l7l9.py`

**Interfaces:**
- Consumes: `col(nombre, tipo, *args, vacios=0) -> Columna`, `generar_tabla(semilla: str, entrada: Entrada) -> tuple[list[str], list[list[str]]]`, `escribir_entrada(carpeta, nombre, encabezado, filas) -> None` (`tools/corpus_lib/datos_ficticios.py:50,58,94`); la forma de `caso.yaml` que lee `cargar_caso` (`tools/corpus_lib/caso.py:77`): `nivel`, `construcciones`, `capa`, `tolerancia`, `orden_relevante`, `estado`, `salidas`, `razonamiento`, `invariantes`.
- Produces:
  ```python
  Fila = dict[str, str | None]

  @dataclass(frozen=True)
  class Etapa:
      nombre: str                                  # "validar_monto", "depurar_duplicados", "enriquecer", "totalizar", "unir_origenes"
      construcciones: tuple[str, ...]              # para `caso.yaml`: ("DATA step", "IF/ELSE")
      def sas(self, entrada: str, salida: str, rechazo: str | None) -> str: ...
      def aplicar(self, filas: list[Fila], auxiliar: list[Fila] | None) -> tuple[list[Fila], list[Fila]]:
          """(buenas, rechazadas) calculado en Python puro con las reglas de faltantes de SAS."""

  def sembrar_anomalias(filas: list[Fila], tipo: str, cantidad: int, semilla: str) -> tuple[list[Fila], list[int]]:
      """Reemplaza `cantidad` filas por anomalías de `tipo` ("monto_negativo", "llave_nula",
      "duplicado", "llave_huerfana") y devuelve las filas y los índices plantados."""

  @dataclass(frozen=True)
  class EspecificacionCaso:
      nombre: str; nivel: str; familia: str; semilla: str
      etapas: tuple[str, ...]; anomalias: tuple[tuple[str, int], ...]

  def generar_caso(especificacion: EspecificacionCaso, corpus: Path) -> Path:
      """Escribe `programa.sas`, `entradas/*.csv`, `esperado/*.csv`, `caso.yaml` con
      `capa: B`, `estado: traducible` y los invariantes de conciliación; devuelve la carpeta."""
  ```

- [ ] **Step 1: Write the failing tests.** `test_etapas.py`: la etapa `validar_monto` con filas `[{"id": "1", "monto": "10"}, {"id": "2", "monto": "-5"}, {"id": "3", "monto": None}]` devuelve buenas `[1]` y rechazadas `[2, 3]` (regla de la etapa: monto faltante o negativo se rechaza; el faltante numérico de SAS es menor que cualquier número, `lrcon`: buscar la página en `docs/referencia/sas/lrcon.INDEX.md`, sección de valores faltantes en comparaciones, y citarla en el docstring); `depurar_duplicados` deja la primera fila por `id` y devuelve las demás como rechazadas; `sembrar_anomalias(filas, "duplicado", 2, "s")` devuelve exactamente 2 índices y es determinista con la misma semilla. `test_generar_l7l9.py`: `generar_caso(EspecificacionCaso("l7_01_prueba", "L7", "validar_rechazar_conciliar", "s", ("validar_monto",), (("monto_negativo", 3),)), tmp_path)` escribe los cuatro elementos, el `esperado/rechazados.csv` tiene **exactamente 3** filas, y `buenos.csv` más `rechazados.csv` suman las filas de `entradas/` (invariante de conciliación); el `caso.yaml` pasa por `cargar_caso`.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_etapas.py tests/unit/test_generar_l7l9.py -q -p no:cacheprovider`; esperado: no existe el módulo.
- [ ] **Step 3: Implement** `etapas.py` con las cinco etapas (cada una con su `sas` y su `aplicar`) y `sembrar_anomalias`; archivos de menos de 300 líneas. El `sas` de cada etapa usa solo construcciones que el migrador ya traduce (`PROC IMPORT`, `DATA step` con `IF/ELSE`, `PROC SORT NODUPKEY`, `PROC SQL` con `LEFT JOIN`, `GROUP BY`, `UNION ALL`, `PROC EXPORT`); lo que el migrador no soporte hoy queda como pendiente del caso, no se evita en la etapa. Implementar `generar_caso` y el CLI (`uv run python tools/generar_l7l9.py --nivel L7`).
- [ ] **Step 4: Run tests to verify they pass.** Confirmar que no se importó nada de `sgm.ir` ni `sgm.migrar` en `etapas.py` (`Grep` de `from sgm`/`import sgm` sobre el archivo: debe estar vacío; es la independencia del esperado).
- [ ] **Step 5: Run** `uv run ruff check src tests tools` y `tests/unit/test_no_script_specific_names.py`. **Commit** `hito N n: biblioteca de etapas y generador de casos L7 y L9`.

---

### Task G-11: 20 casos L7 (varias etapas con rechazos y conciliación) (MG-P10-04, parte 2; serie `n`)

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\L7\l7_01_...` a `l7_20_...` (cada uno con `caso.yaml`, `programa.sas`, `entradas\*.csv`, `esperado\*.csv`; los escribe el generador, no se tocan a mano)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\corpus_lib\especificaciones_l7.py` (la lista de las 20 `EspecificacionCaso`)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\migrar_pendientes.yaml` (solo los casos L7 que el anillo A no traduzca por completo, con su motivo; ninguno se quita del corpus)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_migrar_corpus_anillo_b.py` (solo `CONOCIDOS`: los casos L7 que el intérprete no ejecute, con su motivo, y su dueño en `DUEÑOS` de G-8; **antes de agregar uno, confirmar que no es un defecto de la etapa**)
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_corpus_l7.py`

**Interfaces:**
- Consumes: `generar_caso(especificacion: EspecificacionCaso, corpus: Path) -> Path`, `Etapa`, `sembrar_anomalias` (G-10); `todos_los_casos(corpus) -> list[Caso]`.
- Produces: `ESPECIFICACIONES_L7: tuple[EspecificacionCaso, ...]` con 20 entradas (5 familias por 4 variantes). Familias y qué planta cada una: `validar_rechazar_conciliar` (montos negativos y faltantes: 1, 3, 5 y 8 anomalías), `depurar_y_totalizar` (llaves duplicadas: 1, 2, 4 y 6), `enriquecer_con_maestro` (llaves huérfanas sin pareja en el maestro: 1, 2, 3 y 7), `etapas_encadenadas` (validar, depurar y totalizar con las tres anomalías juntas, con tamaños de 20, 50, 100 y 200 filas) y `consolidar_origenes` (`UNION ALL` de dos orígenes con conciliación por origen y llaves nulas: 1, 2, 4 y 5).

- [ ] **Step 1: Write the failing test.** `test_corpus_l7.py`: hay 20 casos en `tests/corpus/L7`; sus nombres siguen `l7_<nn>_<familia>_<variante>`; cada uno tiene `esperado/` no vacío y su `caso.yaml` declara `capa: B`; para cada uno, la suma de filas de los `esperado/` de «buenos» y «rechazados» es igual a las filas de la entrada principal (conciliación por construcción); el número de filas de `rechazados.csv` es el número de anomalías sembradas de su especificación (el invariante que las anomalías plantadas hacen medible).
- [ ] **Step 2: Run test to verify it fails.** `uv run python -m pytest tests/unit/test_corpus_l7.py -q -p no:cacheprovider`; esperado: no existe `tests/corpus/L7`.
- [ ] **Step 3: Generar.** Escribir `especificaciones_l7.py` y correr `uv run python tools/generar_l7l9.py --nivel L7`. Es **idempotente**: correrlo dos veces no cambia ningún archivo (se comprueba con `git status` limpio tras la segunda corrida; `escribir_entrada` usa `\n`).
- [ ] **Step 4: Medir en los anillos A y B.** `uv run python -m pytest tests/unit/test_migrar_corpus_aceptacion.py tests/unit/test_migrar_corpus_anillo_b.py -q -p no:cacheprovider -k L7`. Los casos que fallen se clasifican **una por una**: (a) defecto de la etapa o de su esperado (se arregla la etapa en G-10 y se regenera), (b) construcción que el migrador aún no soporta (entra en `migrar_pendientes.yaml` con su código y en `CONOCIDOS` con dueño; no se oculta), (c) defecto del intérprete (pedido al plan dueño). Anotar en `PROGRESS.md` cuántos de 20 pasan en A y en B y la lista de los demás con su causa.
- [ ] **Step 5: Run** `tests/unit/test_corpus_l7.py`, `tests/unit/test_corpus_validaciones.py` (valida la forma de todos los `caso.yaml`) y `uv run ruff check src tests tools`. **Commit** `hito N n: 20 casos L7 con anomalias plantadas y esperado por construccion`.

---

### Task G-12: 20 casos L9 (programa grande con datos simulados) (MG-P10-04, cierre; serie `n`)

Un L9 compone de 6 a 10 etapas de la biblioteca con parámetros `%LET`, varias fuentes y salidas de control. Es el análogo en pequeño del programa real grande: sirve para medir composición sin depender de un solo programa del cliente.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\L9\l9_01_...` a `l9_20_...` (generados)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\corpus_lib\especificaciones_l9.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\migrar_pendientes.yaml` y `CONOCIDOS` de `tests/unit/test_migrar_corpus_anillo_b.py` (con motivo y dueño, igual que en G-11)
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_corpus_l9.py`

**Interfaces:**
- Consumes: igual que G-11.
- Produces: `ESPECIFICACIONES_L9: tuple[EspecificacionCaso, ...]` con 20 entradas (4 familias por 5 variantes): `cartera_mensual` (tres insumos, `%LET periodo`, 8 etapas), `conciliacion_de_saldos` (dos fuentes, diferencia plantada por producto: 1, 2, 3, 5 y 8 diferencias), `consolidado_multi_origen` (de 2 a 4 orígenes con `UNION ALL`, llaves nulas y duplicadas) y `control_de_calidad_por_reglas` (una etapa de rechazo por regla, 3 a 7 reglas, cada rechazo a su propia tabla). Las cifras de anomalías (1, 2, 3, 5, 8) las plantea `sembrar_anomalias` con semilla fija; el valor esperado de cada tabla de control es conocido por construcción.

- [ ] **Step 1: Write the failing test.** `test_corpus_l9.py`: 20 casos en `tests/corpus/L9`; cada `programa.sas` tiene al menos 6 pasos (`PROC`/`DATA`, contados con una expresión regular sobre líneas que empiezan con `data `, `proc `); la conciliación por construcción (filas de entrada = buenas + suma de todas las tablas de rechazo) vale para cada caso; las filas de cada tabla de control coinciden con las anomalías de la especificación.
- [ ] **Step 2: Run test to verify it fails.** `uv run python -m pytest tests/unit/test_corpus_l9.py -q -p no:cacheprovider`; esperado: no existe `tests/corpus/L9`.
- [ ] **Step 3: Generar** con `uv run python tools/generar_l7l9.py --nivel L9` (idempotente, como en G-11).
- [ ] **Step 4: Medir y clasificar** como en G-11 (a/b/c). Medir además el tamaño: tiempo de migrar los 20 casos (anotar segundos totales) y el número de Jobs y componentes por caso, que alimentan las pruebas de rendimiento del plan maestro (MG-P12). Un L9 que tarde más de 30 s en migrar se anota como hallazgo de rendimiento, no se reduce.
- [ ] **Step 5: Correr** `uv run python tools/medir_anillo_b.py`: los 40 casos L7 y L9 ya forman parte del denominador de C3. Pegar la cifra en `PROGRESS.md`.
- [ ] **Step 6: Run** `uv run ruff check src tests tools`. **Commit** `hito N n: 20 casos L9 con datos simulados y anomalias plantadas`.

---

### Task G-13: Generador de programas SAS con oráculo independiente (MG-P10-05, parte 1; serie `n`)

El plan maestro (sección 6.3) pide un generador que combine operadores (filtro, cálculo, unión, agregado, orden, duplicados) con datos aleatorios de semilla fija y verifique el resultado. Se sigue el modelo de B-17 de `2026-11-11-mg-b-datastep-y-plan-logico.md` (gramática, oráculo propio, CLI): **el oráculo no usa el intérprete**, o el generador solo probaría que el intérprete es consistente consigo mismo.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\generador_sas\__init__.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\generador_sas\gramatica.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\generador_sas\oraculo.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\generar_programas_sas.py` (CLI)
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_generador_sas.py`

**Interfaces:**
- Consumes: `ejecutar_plan(plan, entradas)`, `compile_file`, `analyze_program`, `project_base` (como en `tests/unit/test_migrar_corpus_anillo_b.py`), `migrar(...)` (`src/sgm/cli_migrar.py:271`).
- Produces:
  ```python
  Tabla = tuple[list[str], list[list[str | None]]]   # encabezado, filas

  @dataclass(frozen=True)
  class Programa:
      semilla: int
      operadores: tuple[str, ...]        # ("filtro", "calculo", "agregado")
      sas: str
      entradas: dict[str, Tabla]
      esperado: dict[str, Tabla]         # calculado por el oráculo, no por el intérprete

  OPERADORES: tuple[str, ...] = ("filtro", "calculo", "union", "agregado", "orden", "duplicados")

  def generar(semilla: int, max_pasos: int = 4) -> Programa: ...      # determinista: misma semilla, mismo programa
  def reconstruir(operadores: tuple[str, ...], entradas: dict[str, Tabla], semilla: int) -> Programa: ...
      # arma el SAS y el esperado para una lista de operadores y entradas dadas (la usa el reductor, G-14)
  def evaluar(programa: Programa) -> dict:
      """{"termina": bool, "pendientes": [códigos], "diferencias": [str]}: corre el anillo A
      (`migrar` en carpeta temporal) y el B (`ejecutar_plan`) y compara con `programa.esperado`."""
  ```
  CLI: `uv run python tools/generar_programas_sas.py --n 200 --semilla 0 [--salida out/generador]`; escribe `out/generador/<semilla>.json` con los fallos (sin el texto del SAS más allá del programa generado, que es sintético) y `out/criterios/generador_sas.json`.

- [ ] **Step 1: Buscar las reglas en la guía.** El oráculo implementa la semántica de faltantes de SAS en comparaciones y en agregados con **una página citada por regla**: valores faltantes numéricos en comparaciones (`lrcon`; ubicar la sección en `docs/referencia/sas/lrcon.INDEX.md` y la página con `grep -n "<!-- página N -->"`), `SUM`/`COUNT`/`AVG` que ignoran faltantes (`sqlproc`, p. 83 y 88, como cita el Plan C), `NODUPKEY` (`proc`, índice de `PROC SORT`). Las páginas van en el docstring de cada función del oráculo. Lo que una página no demuestra (por ejemplo la suma de un grupo con todos los valores faltantes) **no se genera**: la gramática excluye esa combinación y la deja listada en `EXCLUIDOS` con el código `P-SUM-TODO-FALTANTE`.
- [ ] **Step 2: Write the failing tests.** `test_generador_sas.py`: `generar(7)` dos veces da el mismo `sas` y los mismos `entradas`; `generar(7, max_pasos=1).operadores` tiene un solo operador; el oráculo, con valores a mano, da: `filtro` `monto < 5` sobre `[None, 3, 9]` conserva `[None, 3]` (el faltante es menor que cualquier número); `agregado` suma de `[None, 3, 4]` da `7`; `duplicados` por `id` conserva la primera fila de cada llave; `reconstruir(("filtro",), entradas, 0).esperado` coincide con lo anterior. Y una prueba de **independencia**: `oraculo.py` no importa nada de `sgm` (`ast.parse` del archivo y revisar los `import`).
- [ ] **Step 3: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_generador_sas.py -q -p no:cacheprovider`; esperado: no existe el módulo.
- [ ] **Step 4: Implement** gramática (cada operador agrega un paso `DATA`/`PROC SQL`/`PROC SORT` al SAS sobre la tabla del paso anterior; las tablas de entrada se leen con `PROC IMPORT` de `entradas/*.csv`), oráculo (puro Python) y `evaluar`. `max_pasos` ≤ 5; columnas con tipos texto y numérico, con 10 % de faltantes sembrados.
- [ ] **Step 5: Run tests to verify they pass** y una tanda corta: `uv run python tools/generar_programas_sas.py --n 50 --semilla 0`. Anotar en `PROGRESS.md`: programas generados, cuántos terminan, cuántos con pendientes, cuántas diferencias. Las diferencias **no se descartan**: son la entrada de G-14.
- [ ] **Step 6: Run** `uv run ruff check src tests tools` y `tests/unit/test_no_script_specific_names.py`. **Commit** `hito N n: generador de programas SAS con oraculo independiente`.

---

### Task G-14: Reducción automática de fallos y promoción al corpus (MG-P10-05, cierre; serie `n`)

Aceptación del plan maestro: «encuentra y reduce al menos un error real; los fallos pasan al corpus». Si el generador no encuentra ningún error real, **se dice** y la tarea queda abierta con la cifra de programas probados; no se fabrica un fallo.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\generador_sas\reductor.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\generador_sas\promover.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\generar_programas_sas.py` (opciones `--reducir` y `--promover`)
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_reductor_sas.py`

**Interfaces:**
- Consumes: `Programa`, `reconstruir(operadores, entradas, semilla) -> Programa`, `evaluar(programa) -> dict` (G-13); `generar_caso`-like escritura de `caso.yaml` de `tools/corpus_lib/generar_l7l9.py` (G-10).
- Produces:
  ```python
  def reducir(programa: Programa, falla: Callable[[Programa], bool], limite: int = 200) -> Programa:
      """Delta debugging en tres pasos, siempre conservando `falla(candidato) is True`:
      1) quitar operadores de uno en uno (deja el menor `operadores`);
      2) bisección de filas de cada entrada (mitades, luego cuartos, luego una a una);
      3) quitar columnas que ningún operador usa.
      El resultado no se puede reducir más quitando un solo elemento. `limite` acota las
      llamadas a `falla`; al agotarse devuelve el mejor candidato hallado."""

  def promover(programa: Programa, corpus: Path, nombre: str, motivo: str) -> Path:
      """Escribe el programa reducido como caso `L6/<nombre>` (`l6_80` a `l6_99`, rango que este
      plan reserva para fallos reducidos; confirmar con Glob que está libre) con `estado:
      pendiente_revision`, el motivo en `razonamiento` y el `esperado/` del oráculo."""
  ```

- [ ] **Step 1: Write the failing tests.** `test_reductor_sas.py` con un predicado sintético (no un fallo real): `falla = lambda p: "agregado" in p.operadores and any(f[0] == "X" for f in p.entradas["a"][1])`; partiendo de un programa de 5 operadores y 40 filas con una fila `X` plantada, `reducir(...)` devuelve un programa con `operadores == ("agregado",)`, **una sola fila** en la entrada `a` (la `X`) y llama a `falla` menos de `limite` veces; con un predicado que nunca falla, `reducir` lanza `ValueError("el programa no falla")`; la reducción es determinista. `promover` con un `tmp_path` escribe `programa.sas`, `entradas/` y `esperado/`, y el `caso.yaml` pasa por `cargar_caso` con `estado == "pendiente_revision"`.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_reductor_sas.py -q -p no:cacheprovider`; esperado: no existe el módulo.
- [ ] **Step 3: Implement** `reductor.py` y `promover.py` (menos de 150 líneas cada uno) y las opciones `--reducir` (aplica `reducir` a cada programa con `diferencias` y escribe el reducido en `out/generador/`) y `--promover` (llama a `promover` solo con una bandera explícita; nunca escribe en `tests/corpus` sin ella).
- [ ] **Step 4: Run tests to verify they pass.** Correr el generador con `--n 500 --semilla 100 --reducir`. Caso A: hay al menos un fallo real; se reduce, se promueve con `--promover` a `L6/l6_80_...`, se clasifica como en G-11 (defecto del intérprete, del emisor o del oráculo: si es del oráculo, se corrige el oráculo y el caso se descarta con su explicación en `PROGRESS.md`) y se pide el arreglo al plan dueño. Caso B: no hay fallos con 500 programas; ampliar a `--n 5000`; si sigue sin haber, anotar «0 fallos en N programas» y dejar MG-P10-05 sin acreditar.
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N n: reductor automatico de fallos del generador y promocion al corpus`.

---

### Task G-15: Robustez de `sgm migrar` (criterio C2): entradas basura y todo el repositorio (MG-P10-05, aceptación C2; serie `n`)

C2 pide que `sgm migrar` termine con código 0 y escriba sus archivos sobre **cada** programa del repositorio y sobre entradas basura. Una excepción: si la salida lleva un secreto en claro, `sgm migrar` termina con código 1 **a propósito** (`cli_migrar_comando.py`: `_seguridad_fallida` y `typer.Exit(code=1)`, regla 7 de `AGENTS.md`); eso es la compuerta de seguridad funcionando, no un fallo, y se cuenta aparte como `bloqueado_por_secreto` (sigue exigiéndose que no haya traza de Python ni cuelgue, y que `pendientes.md` y `migracion.log` existan en la carpeta de salida o que el mensaje diga por qué no).

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\robustez_migrar.py`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_robustez_migrar.py`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_robustez_repositorio.py` (la corrida de los programas del repositorio, solo con `SGM_ROBUSTEZ_COMPLETA=1`)

**Interfaces:**
- Consumes: `programas_del_repositorio(raiz: Path) -> list[Path]` (G-3); la app de `sgm.cli` con `typer.testing.CliRunner` (`runner.invoke(app, ["migrar", str(origen), "--out", str(salida)])`, código en `.exit_code`); `migrar(...)` y `ResultadoMigrar` (`carpeta`, `escritos`, `hallazgos_seguridad`, `fallo_seguridad`).
- Produces:
  ```python
  def entradas_basura(semilla: int = 0) -> dict[str, bytes]:
      """Nombre -> contenido: archivo vacío; solo espacios y saltos; ceros (NUL); 4 KiB binarios
      pseudoaleatorios con semilla; UTF-16 con BOM; UTF-8 con BOM y CRLF; solo CR; una línea de
      1 MiB; 20 000 paréntesis abiertos; comentario `/*` sin cerrar; cadena `'abc` sin cerrar;
      `%macro m;` sin `%mend`; macro que se llama a sí misma; `%include` de un archivo que no
      existe; y cada programa pequeño del corpus truncado al 50 % y al 90 %."""

  def correr_uno(origen: Path, salida: Path, tiempo_maximo: float = 60.0) -> dict:
      """{"programa": ruta relativa, "codigo": int, "tiempo": float, "escribio": bool,
      "clase": "ok" | "bloqueado_por_secreto" | "falla" | "cuelga"}. Corre `python -m sgm.cli
      migrar` en un subproceso con límite de tiempo; "falla" si el código es distinto de 0 sin
      aviso de seguridad, si hay `Traceback` en la salida o si no escribió `pendientes.md`."""

  def correr(raiz: Path, completo: bool) -> dict:
      """Basura (siempre) y, con `completo`, cada programa de `programas_del_repositorio`.
      Escribe `out/criterios/c2_robustez.json` con `cifra` = «N de M programas; K basura de L»."""
  ```

- [ ] **Step 1: Write the failing tests.** `test_robustez_migrar.py`: `entradas_basura()` incluye `vacio.sas` con `b""`, una entrada con BOM (`b"\xef\xbb\xbf"` al inicio) y CRLF, y es determinista con la misma semilla; para **cada** entrada basura, `correr_uno` da `clase == "ok"` y `escribio is True` (un archivo vacío migra con el pendiente `SIN_PASOS` que ya existe en `cli_migrar.py`, no con una excepción); un programa que contiene `proc pwencode in='clave-de-prueba';` da `clase == "bloqueado_por_secreto"` **o** `ok` con la contraseña reemplazada por `'***'` (verificar al ejecutar cuál es el comportamiento real y fijar el que sea), y la salida nunca contiene `clave-de-prueba`; ninguna carpeta de salida contiene el texto de una entrada basura (revisión de seguridad: no se copia la entrada a los informes). `test_robustez_repositorio.py`: con `SGM_ROBUSTEZ_COMPLETA=1`, ningún programa de `programas_del_repositorio` da `falla` ni `cuelga`; sin la variable, `pytest.skip("corrida completa: definir SGM_ROBUSTEZ_COMPLETA=1")`.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_robustez_migrar.py -q -p no:cacheprovider`; esperado: no existe el módulo.
- [ ] **Step 3: Implement** `robustez_migrar.py` (menos de 250 líneas; los 20 000 paréntesis y la macro recursiva son los casos de pila y de bucle: si `sgm migrar` cuelga o agota la pila, `correr_uno` lo clasifica `cuelga` o `falla` y el hallazgo queda registrado).
- [ ] **Step 4: Run tests to verify they pass** y la corrida completa en segundo plano: `$env:SGM_ROBUSTEZ_COMPLETA=1; uv run python tools/robustez_migrar.py --completo` (el programa grande tarda; el límite por programa es de 60 s). Cada `falla` o `cuelga` real se resuelve **sin esconderla**: se arregla `sgm migrar` (la zona es de `src/sgm/cli_migrar.py`, de Byron en este reparto: arreglo mínimo, con la prueba que reproduce el fallo, en un hito propio) o queda en `CONOCIDOS_FALLA` de la prueba con su causa, y el tope solo baja. Anotar el número real de programas y el desglose en `PROGRESS.md` (recordar la nota de G-3: el plan maestro dice 189).
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N n: robustez de sgm migrar con entradas basura y sobre el repositorio`.

---

### Task G-16: Prueba de mutación del arnés de comparación (MG-P10-06; serie `n`)

Aceptación: «alterar un esperado y comprobar que el arnés falla: 100 % detectado». Un arnés que da verde con un esperado roto es peor que no tener arnés. Se muta **la tabla calculada** contra el `esperado/` guardado (equivale a alterar el esperado) y se exige que el comparador lo vea.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\mutar_arnes.py`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_mutar_arnes.py`

**Interfaces:**
- Consumes: `comparar_con_guardado(ruta: Path, tabla: Tabla, tolerancia: float, orden_relevante: bool) -> list[str]` y `Tabla(columnas, filas)` (`tools/corpus_lib/csv_tabla.py`); `comparar(sas: Path, talend: Path) -> Informe` (`src/sgm/verify.py:70`; el atributo que indica coincidencia se confirma leyendo `Informe` en `verify.py:17` al ejecutar); `diferencias_de_tabla(caso, tabla, filas) -> list[str]` (G-8).
- Produces:
  ```python
  MUTACIONES: tuple[str, ...] = (
      "celda_numerica_fuera_de_tolerancia", "celda_de_texto", "faltante_a_cero", "cero_a_faltante",
      "fila_borrada", "fila_duplicada", "columna_borrada", "columna_agregada",
      "encabezado_renombrado", "filas_barajadas",
  )

  def mutar(tabla: Tabla, mutacion: str, tolerancia: float, orden_relevante: bool) -> Tabla | None:
      """La tabla alterada, o None si la mutación no aplica (no hay columna numérica, la tabla
      tiene una fila, etc.). `filas_barajadas` solo es una mutación real si `orden_relevante`;
      si no, es una mutación equivalente y se cuenta aparte (el arnés NO debe detectarla)."""

  def correr(corpus: Path) -> dict:
      """{"mutantes": n, "detectados": n, "equivalentes_toleradas": n, "sobrevivientes": [(caso, tabla, mutacion)]}.
      Escribe `out/criterios/mutacion_arnes.json`."""
  ```
  CLI: `uv run python tools/mutar_arnes.py`; sale con 1 si hay sobrevivientes.

- [ ] **Step 1: Write the failing tests.** Con un CSV de tres filas en `tmp_path` y `tolerancia=0.005`: cambiar una celda numérica en `0.5` es detectada (diferencias no vacías); cambiarla en `0.001` **no** es una mutación real (queda dentro de la tolerancia y `mutar` con `celda_numerica_fuera_de_tolerancia` suma `10 * tolerancia + 1`, nunca una cantidad menor); `fila_borrada` y `fila_duplicada` son detectadas; `columna_agregada` es detectada (el comparador ve «columnas de más»); con `orden_relevante=False`, `filas_barajadas` **no** da diferencias y se cuenta como equivalente tolerada, con `orden_relevante=True` sí las da. Una prueba que **plantea un arnés roto** (un comparador falso que siempre devuelve `[]`, inyectado por parámetro `comparador`) debe producir sobrevivientes: es la prueba de que la prueba de mutación puede fallar.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_mutar_arnes.py -q -p no:cacheprovider`; esperado: no existe el módulo.
- [ ] **Step 3: Implement** `mutar` y `correr` con el comparador inyectable (`comparador=comparar_con_guardado` por omisión). `correr` recorre cada caso con `esperado/` no vacío y cada `esperado/*.csv`, y aplica las mutaciones que correspondan.
- [ ] **Step 4: Run tests to verify they pass** y `uv run python tools/mutar_arnes.py`. Si hay sobrevivientes, es un **defecto del arnés** (por ejemplo, columnas de más con el comparador de Studio): se corrige el comparador (`tools/corpus_lib/csv_tabla.py`, zona de Byron) con una prueba nueva que lo reproduce, no se debilita la mutación. Repetir para `sgm.verify.comparar` sobre un par de CSV: las mismas mutaciones deben dar código distinto de 0 en `sgm comparar`.
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N n: prueba de mutacion del arnes de comparacion`.

---

### Task G-17: `sgm cobertura` genera `docs/cobertura.md` y su JSON desde las reglas y el corpus (MG-P10-08; criterio C1; serie `n`)

C1: «lista pública y generada automáticamente de construcciones SAS soportadas, parciales y no soportadas, cada una con su motivo; 100 % de las construcciones que aparecen en el corpus y en los programas reales están clasificadas». Las fuentes ya existen: `rules/sas/catalogo/*.yaml` (cada entrada con `id`, `nombre`, `fuente`, `estado`: `reconocida`, `no_reconocida`, `no_verificada`, `dentro_de_select`; esquema en `schemas/rules/catalogo.schema.json`) y el campo `construcciones` de cada `caso.yaml`. `sgm migrar` ya escribe un `cobertura.md` **por programa** (`informes.cobertura_md`); este es el de **todo el producto**.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\cobertura\__init__.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\cobertura\clasificar.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\cobertura\informe.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\cli_cobertura.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\cli.py` (una línea de importación y una de registro, junto a las de `migrar_command`; es un archivo compartido: no reordenar nada)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\docs\cobertura.md` y `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\docs\cobertura.json` (los escribe el comando)
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_cobertura.py`

**Interfaces:**
- Consumes: las entradas de `rules/sas/catalogo/*.yaml` (la clave raíz y el cargador que ya usa `tests/unit/test_catalogo_sas.py`: leerlo y reutilizar su forma, sin cambiar el esquema); `todos_los_casos(corpus) -> list[Caso]` (`Caso.construcciones`, `Caso.estado`, `Caso.nombre`); `tests/corpus/migrar_pendientes.yaml` (caso a código `P-`).
- Produces:
  ```python
  @dataclass(frozen=True)
  class FilaCobertura:
      id: str; nombre: str; fuente: str
      clase: str            # "soportada" | "parcial" | "no soportada" | "no verificada"
      motivo: str           # por qué esa clase (caso que la demuestra, pendiente que la limita, o página sin regla)
      casos: tuple[str, ...]# casos `traducible` que la usan

  def clasificar(entradas: list[dict], casos: list[Caso], pendientes: dict[str, str]) -> tuple[list[FilaCobertura], list[str]]:
      """Reglas: `reconocida` con al menos un caso `traducible` que no esté en `pendientes` ->
      soportada; `reconocida` sin caso, o solo con casos pendientes, o `dentro_de_select` -> parcial
      (el motivo lo dice); `no_reconocida` -> no soportada; `no_verificada` -> no verificada.
      La segunda salida son las construcciones de `Caso.construcciones` que no casan por nombre
      (sin distinguir mayúsculas ni espacios) con ninguna entrada del catálogo: sin clasificar."""

  def porcentaje_clasificado(filas: list[FilaCobertura], sin_clasificar: list[str], casos: list[Caso]) -> float: ...
  def a_markdown(filas, sin_clasificar, porcentaje: float) -> str: ...
  def a_json(filas, sin_clasificar, porcentaje: float) -> str: ...      # orden estable, sin fecha: dos corridas dan los mismos bytes
  ```
  CLI: `uv run python -m sgm.cli cobertura [--corpus tests/corpus] [--catalogo rules/sas/catalogo] [--salida docs] [--verificar]`. Escribe `docs/cobertura.md`, `docs/cobertura.json` y `out/criterios/c1_cobertura.json` (`cifra` = «N de M construcciones del corpus clasificadas (P %); S sin clasificar»). `--verificar` sale con 1 si `docs/cobertura.md` no coincide con lo que saldría; **no** se usa en la suite (cada caso nuevo de otro plan lo cambiaría): lo usa G-18 y G-Gate.

- [ ] **Step 1: Write the failing tests.** Con un catálogo mínimo en `tmp_path` (tres entradas: `reconocida` con un caso `traducible`, `reconocida` sin casos, `no_reconocida`) y dos casos: `clasificar` da `soportada`, `parcial` (motivo «sin caso del corpus que la demuestre») y `no soportada`; una entrada `reconocida` cuyo único caso está en `pendientes` da `parcial` con el código `P-` en el motivo; una construcción de un caso que no está en el catálogo aparece en `sin_clasificar`; `porcentaje_clasificado` con 4 construcciones del corpus y 1 sin clasificar da `75.0`; `a_json` dos veces da los mismos bytes; el comando con `CliRunner` escribe los dos archivos y sale con 0.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_cobertura.py -q -p no:cacheprovider`; esperado: no existe el módulo.
- [ ] **Step 3: Implement** (cada archivo menos de 200 líneas). El `motivo` sale solo de datos que existen (caso, código `P-`, `fuente` y `nota` de la entrada); nunca de texto escrito a mano en el generador. Sección final del Markdown: «No verificado» con las entradas `no_verificada` y los simuladores que el plan maestro (sección 6.4) declara que faltan, leídos de la lista fija `NO_SIMULADOS = ("FTP/SFTP", "Oracle", "Teradata", "S3 local")` del módulo `informe.py` (es la regla «lo que no se pueda simular se documenta como no verificado»).
- [ ] **Step 4: Run tests to verify they pass** y generar con `uv run python -m sgm.cli cobertura`. Pegar en `PROGRESS.md` el porcentaje clasificado y la lista de `sin_clasificar`. El porcentaje de C1 **no se infla**: cada construcción sin clasificar se resuelve agregándola al catálogo con su página (`<guía>, p. N` que exista en el índice, regla de `AGENTS.md`) o, si la guía no la trae, con estado `no_verificada` y su motivo; nunca con una página supuesta (`tests/unit/test_catalogo_sas.py` lo vigila).
- [ ] **Step 4b: Integrar el informe del Plan C.** `sgm cobertura` incluye como sección «Procedimientos» el contenido de `docs/cobertura-procedimientos.md` (lo genera `tools/cobertura_procs.py` del Plan C, C-22; no se pisa): si el archivo no existe, la sección dice «sin generar» y `--verificar` no falla por eso; si existe, su tabla de procedimientos fuera de alcance debe coincidir con la del catálogo.
- [ ] **Step 5: Run** `tests/unit/test_catalogo_sas.py` y `uv run ruff check src tests tools`. **Commit** `hito N n: sgm cobertura genera docs/cobertura.md y su JSON`.

---

### Task G-18: Corrida nocturna (anillo D) con informe diario y alerta de regresión (MG-P10-07, parte 1; serie `n`)

El anillo D del plan maestro: «todo el corpus por el traductor y por Studio; informe de regresión; falla si un caso que pasaba deja de pasar». La corrida nocturna **orquesta** los medidores de este plan; no reimplementa nada.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\nocturna.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\nocturna_regresion.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\docs\operacion-nocturna.md` (cómo programarla en Windows y qué hacer con la alerta; menos de 60 líneas)
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_nocturna.py`

**Interfaces:**
- Consumes: los comandos de G-3 (`tools/determinismo.py`), G-8 (`tools/medir_anillo_b.py`), G-9 (`tools/java_suelto.py`), G-15 (`tools/robustez_migrar.py --completo`), G-16 (`tools/mutar_arnes.py`), G-17 (`python -m sgm.cli cobertura --verificar`), `tools/calidad_jobs.py` (Plan F1, F1-5; si no existe todavía, el paso se marca `no existe`, no se omite en silencio), la suite `python -m pytest -q`, y el lote de Studio (`tools/corpus_studio.py lote`) **solo** con `--studio` y si `sgm studio salud` conecta; `tools/ci.py` es del Plan A y no se invoca ni se modifica.
- Produces:
  ```python
  @dataclass(frozen=True)
  class ResultadoPaso:
      nombre: str
      comando: tuple[str, ...]
      codigo: int | None          # None si no se ejecutó
      segundos: float
      estado: str                 # "ok" | "falla" | "no ejecutado" | "no existe"
      cifra: str                  # la `cifra` del JSON del criterio, o ""
      casos_ok: tuple[str, ...]   # nombres de caso / programa que pasaron (para detectar regresiones por caso)

  def pasos(studio: bool) -> list[tuple[str, tuple[str, ...]]]: ...
  def correr(carpeta: Path, hoy: date, studio: bool = False, ejecutar=None) -> dict:
      """Corre los pasos con `ejecutar` (inyectable), escribe `carpeta/AAAA-MM-DD.json` y `.md`
      y devuelve el informe."""

  # tools/nocturna_regresion.py
  @dataclass(frozen=True)
  class Regresion:
      tipo: str       # "paso" (ok -> falla) | "caso" (un caso que pasaba ya no pasa) | "cifra" (una métrica con tope baja)
      detalle: str

  def comparar(anterior: dict | None, actual: dict) -> list[Regresion]: ...
  ```
  CLI: `uv run python tools/nocturna.py [--studio] [--carpeta out/nocturna]`; escribe `out/nocturna/ALERTA.md` y sale con 1 si `comparar` no es vacío o algún paso sin Studio falla; sale con 0 y borra `ALERTA.md` si todo está verde.

- [ ] **Step 1: Write the failing tests.** Con `ejecutar` falso: `correr` escribe el JSON y el Markdown con el nombre `2026-11-12.json`; un paso que devuelve código 1 queda `falla`; un comando cuyo archivo no existe queda `no existe` (no `ok`); sin `--studio` el paso de Studio queda `no ejecutado` con motivo; `comparar` con un `anterior` donde `anillo_b` tenía los casos `{"a", "b"}` y un `actual` con `{"a"}` devuelve una `Regresion("caso", ...)` que nombra `b`; un paso `ok` que pasa a `falla` es regresión de tipo `paso`; sin `anterior` (primera noche) no hay regresiones; un caso que antes **no** pasaba y ahora pasa no es regresión.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_nocturna.py -q -p no:cacheprovider`; esperado: no existe el módulo.
- [ ] **Step 3: Implement.** Cada paso es un subproceso con límite de tiempo (por omisión 45 min, configurable); la lista de casos que pasan sale de `out/criterios/c3_anillo_b.json` (`detalle.casos_ok`: **agregar** esa clave al JSON de G-8 y a su prueba en este paso) y de `c2_robustez.json` (`detalle.programas_ok`). El informe `.md` es una tabla: paso, estado, segundos, cifra, más la sección «Regresiones». No escribe texto de programas, solo nombres de caso.
- [ ] **Step 4: Run tests to verify they pass.** Documentar en `docs/operacion-nocturna.md` el comando de programación para Windows (`schtasks /Create /SC DAILY /ST 02:00 /TN sgm-nocturna /TR "uv run python tools/nocturna.py"`) **sin ejecutarlo**: programarla en la máquina es decisión del usuario; mientras tanto se corre a mano. Correrla una vez con `uv run python tools/nocturna.py` y pegar la tabla del informe en `PROGRESS.md`.
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N n: corrida nocturna con informe diario y alerta de regresion`.

---

### Task G-19: «Estable 14 días»: cómo se mide para GM5 (MG-P10-07, cierre; serie `n`)

GM5 dice «corpus completo (L0 a L9) en verde y corrida nocturna estable 14 días». Hay que definir los dos términos para que no sean una opinión.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\estabilidad_nocturna.py`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_estabilidad_nocturna.py`

**Interfaces:**
- Consumes: los informes `out/nocturna/AAAA-MM-DD.json` (G-18), con `pasos: list[ResultadoPaso]` y `regresiones`.
- Produces:
  ```python
  def racha(carpeta: Path, hoy: date) -> dict:
      """{"dias_consecutivos": int, "primer_dia": str | None, "rompe": str | None, "corpus_verde": bool,
      "studio": "coincide" | "pendiente" | "falla"}.
      Un día cuenta si existe su informe, no tiene regresiones y todos los pasos sin Studio están
      `ok` (un paso `no existe` rompe la racha). La racha termina en `hoy` o en `hoy - 1`.
      `corpus_verde`: en el último informe, `anillo_b` tiene 0 `fallan`, 0 `xfail` y 0 `xpass`
      sobre L0 a L9 y `robustez` 0 `falla`/`cuelga`. `studio`: el último lote C corrido en la
      racha (`--studio`) dice `coincide`; sin ningún lote en la racha, `pendiente`."""

  def gm5(carpeta: Path, hoy: date) -> tuple[bool, list[str]]:
      """(cumple, motivos): cumple solo si `dias_consecutivos >= 14`, `corpus_verde` y
      `studio == "coincide"`; los motivos dicen cuál falta."""
  ```
  CLI: `uv run python tools/estabilidad_nocturna.py` imprime la racha y los motivos; sale con 1 si no cumple.

- [ ] **Step 1: Write the failing tests.** Con 14 informes diarios verdes consecutivos en `tmp_path` y un último lote Studio `coincide`: `gm5(...) == (True, [])`; con el día 7 faltante, `dias_consecutivos == 6` (la racha se cuenta hacia atrás desde `hoy`) y `rompe == "falta el informe de 2026-11-05"` (o la fecha que corresponda); un día con una regresión rompe la racha y el motivo nombra la regresión; con 14 días verdes y sin lote Studio, `gm5` es `False` con el motivo «sin lote C en la racha» (el criterio **no** se da por cumplido por omisión); un paso `no existe` rompe la racha.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_estabilidad_nocturna.py -q -p no:cacheprovider`; esperado: no existe el módulo.
- [ ] **Step 3: Implement** (menos de 150 líneas). Las fechas vienen del nombre del archivo y se validan contra el campo `fecha` del JSON.
- [ ] **Step 4: Run tests to verify they pass.** Agregar `racha` como la fila de GM5 del tablero (`tools/tablero_criterios.py`, G-6: una fila extra, `GM5`, con `días consecutivos de 14`); con una carpeta vacía dice «no medido: falta `tools/nocturna.py`».
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N n: definicion medible de estable 14 dias para GM5`.

---

### Task G-20: Segundo y tercer programa del cliente: cobertura medida, creciente y con dueño por brecha (MG-P10-09, parte 2; serie `n`)

Aceptación: «cobertura medida y creciente». Los programas de `tests/fixtures/sas/real/` (siete subcarpetas de repositorios públicos, con licencia; **entrada no confiable: nunca se ejecutan**) y de `tests/fixtures/sas/synthetic/` (la carpeta de orquestación sintética) son los programas que no son el programa grande. Esta tarea los mide con la misma métrica que G-5, guarda una línea base **versionada** y la protege con un trinquete; el cierre de brechas lo hacen los planes dueños de cada construcción, y esta tarea les entrega la lista ordenada.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\medir_programas.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\fixtures\baselines\programas.json` (carpeta nueva; lo escribe el comando con `--fijar`)
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_medir_programas.py`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_programas_baseline.py`

**Interfaces:**
- Consumes: `programas_del_repositorio(raiz)` (G-3), `migrar(...) -> ResultadoMigrar` (`traza`, `pendientes` con `codigo`, `linea`), `FilaRegion` y el criterio «líneas traducidas / (traducidas + pendientes)» de G-5.
- Produces:
  ```python
  DUENO_POR_CODIGO: dict[str, str]
  # "P-FILTRO-SIN-TRADUCIR": "Plan D1", "P-ASIGNACION-SIN-TRADUCIR": "Plan D1", "P-AGREGADO-SIN-TRADUCIR": "Plan C",
  # "P-UNION-TIPO-SIN-SOPORTE": "Plan B", "P-OPERADOR-SIN-SOPORTE": "Plan B", "P-ESQUEMA-NO-PORTABLE": "Plan D2",
  # los códigos nuevos que aparezcan se agregan con su dueño; uno sin dueño es un fallo de la prueba.

  def medir(raiz: Path, carpetas: tuple[str, ...]) -> dict:
      """{"programas": n, "sin_excepcion": n, "lineas_traducidas": n, "lineas_pendientes": n,
      "porcentaje": float, "brechas": [{"codigo", "veces", "programas", "dueno"}] ordenadas
      de mayor a menor, "por_carpeta": {...}}. Solo conteos y códigos; ningún texto de programa."""

  def comparar_con_linea_base(actual: dict, base: dict, margen: float = 0.5) -> list[str]:
      """Diferencias que son regresión: `porcentaje` baja más de `margen` puntos, o
      `sin_excepcion` baja. Que suba nunca es error."""
  ```
  CLI: `uv run python tools/medir_programas.py [--carpetas real synthetic] [--fijar]`; `--fijar` reescribe la línea base **solo si no baja** (si baja, se niega y dice por qué).

- [ ] **Step 1: Write the failing tests.** `test_medir_programas.py`: con dos programas sintéticos en `tmp_path` (uno que migra completo y otro con una construcción que el migrador deja como pendiente `P-OPERADOR-SIN-SOPORTE`) `medir` da `programas == 2`, `lineas_pendientes >= 1`, una brecha con `codigo == "P-OPERADOR-SIN-SOPORTE"` y `dueno == "Plan B"`; las brechas vienen de mayor a menor frecuencia; `comparar_con_linea_base` con porcentajes 62,0 y 60,0 devuelve una regresión, con 62,0 y 61,8 no, con 62,0 y 70,0 no. `test_programas_baseline.py`: mide `tests/fixtures/sas/real` y `synthetic` y compara con `tests/fixtures/baselines/programas.json` (la prueba es el trinquete; si el archivo no existe se salta con «fijar con `--fijar`» **solo hasta el paso 4**, después es obligatorio); y todo código `P-` de las brechas tiene dueño en `DUENO_POR_CODIGO`.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_medir_programas.py -q -p no:cacheprovider`; esperado: no existe el módulo.
- [ ] **Step 3: Implement** (menos de 200 líneas). Cada programa se migra a una carpeta temporal con límite de tiempo; un programa que lance excepción o exceda el tiempo cuenta fuera de `sin_excepcion` (y ya lo vigila G-15, aquí solo se informa). La corrida sobre los siete repositorios de `real/` es lenta: medir por carpeta y mostrar progreso.
- [ ] **Step 4: Fijar la línea base y entregar brechas.** `uv run python tools/medir_programas.py --fijar`; pegar en `PROGRESS.md` el porcentaje por carpeta y las **diez brechas más frecuentes con su dueño**. Esa lista es el trabajo iterativo del criterio «cerrar las brechas más frecuentes»: en cada hito posterior de los planes B a F, quien cierra una brecha vuelve a correr `medir_programas.py` y, si el porcentaje sube, corre `--fijar`. Anotar en la tabla MG-P10-09 del plan maestro la línea de estado con la cifra (sin cambiar los créditos: eso lo hace G-Gate con `avance_creditos.py`).
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N n: cobertura medida de los programas reales y sinteticos con linea base`.

---

### Task G-Gate: GM5 y criterios C1, C3 y C5 medidos (serie `n`, la cierra Byron)

**Criterio de salida** (compuerta GM5 de la sección 10 del plan maestro: leer su texto con `grep -n "GM5" docs/plan-reescritura/plan-migrador-general.md` antes de empezar; lo siguiente es lo que este plan se compromete a probar). El cierre tiene dos momentos porque «estable 14 días» no se puede acelerar:
1. **G-Gate (a), todas las tareas integradas:** corpus L0 a L9 con `tools/medir_anillo_b.py` en `fallan == 0` y `xpass == 0`, y cada entrada de `CONOCIDOS` y de `migrar_pendientes.yaml` con dueño, motivo y `Pendiente:` (o página); **C1** medido (`sgm cobertura`: porcentaje clasificado y lista de `sin_clasificar` vacía o cada elemento con su motivo); **C3** medido (anillo B sobre L0 a L9, anillo A, `javac` suelto de G-9, mutación de G-16 con 0 sobrevivientes) y, con Studio, el lote C de los casos L7 y L9 que migran sin pendiente; **C5** medido (G-3: 0 diferencias en 10 semillas); C2 medido (G-15) y C4 y C6 en el tablero aunque no sean de este plan.
2. **G-Gate (b), 14 días después de empezar la corrida nocturna:** `uv run python tools/estabilidad_nocturna.py` devuelve `cumple == True` (`dias_consecutivos >= 14`, `corpus_verde`, `studio == "coincide"`). Si Studio no conecta, GM5 queda «parcial: sin lote C» con su motivo y **no** se declara cerrada.

- [ ] **Step 1: Run** `uv run python -m pytest -q` y `uv run ruff check src tests tools` (la única corrida completa de la suite de este plan además de la de G-3).
- [ ] **Step 2: Medir todo.** `uv run python tools/nocturna.py` (una corrida completa sin `--studio`) y `uv run python tools/tablero.py --markdown`: pegar la tabla de C1 a C6 en `PROGRESS.md`. Cada fila «no medido» o «vencido» se explica con su tarea o se mide ahora.
- [ ] **Step 3: Lote C.** `uv run python -m sgm.cli studio salud`; con conexión, `uv run python tools/corpus_studio.py lote <casos L7 y L9 sin pendiente> --jobs <carpeta> --proyecto <proyecto>` para compilar y `uv run python tools/validar_caso_studio.py <casos>` para ejecutar y comparar; contar aparte compilaron y ejecutaron-y-coinciden. Sin conexión: «lote C pendiente» con el motivo de `sgm studio salud` y `docs/guia-validacion-studio.md`, sección 7; no se reinstala nada ni se cambia `talend-mcp`.
- [ ] **Step 4: Recalcular el avance.** Editar en `docs/plan-reescritura/creditos.yaml` los créditos de MG-P0 y MG-P10 según el método de la sección 11b (1 = hecha y su aceptación comprobada, 0,5 = parcial con evidencia, 0,25 = puntual, 0 = sin evidencia; cada tarea de este plan acredita a lo sumo lo que su prueba demuestra) y correr `uv run python tools/avance_creditos.py --actualizar`. Actualizar el «Estado» de MG-P0 y MG-P10 en `plan-migrador-general.md` y la tabla «Estado por fase» de `plan.md` en el mismo cambio (si el plan contradice el código, se corrige uno de los dos).
- [ ] **Step 5: Registrar** en `PROGRESS.md` el hito de cierre (a): casos por anillo, `xfail` restantes con dueño, cifra de cada criterio, sobrevivientes de mutación (0), programas de robustez y qué quedó fuera con su motivo. **Commit** `hito N n: compuerta GM5 (a): criterios C1, C3 y C5 medidos`. Cuando pasen los 14 días, repetir el paso 2, correr `tools/estabilidad_nocturna.py`, registrar el hito de cierre (b) y marcar GM5 en la sección 10 del plan maestro solo si `cumple == True`. **Commit** `hito N n: compuerta GM5 (b): corrida nocturna estable 14 dias`.

---

## Resumen de horas

| Tareas | Origen | Serie | Horas |
|---|---|---|---|
| G-1, G-2 | MG-P0-01 | n | 2 |
| G-4, G-6 (tablero y créditos) | MG-P0-05 (con los tiempos de P0-04 y P0-09) | n | 5 |
| G-7 | MG-P0-06 | n | 5 |
| **Subtotal MG-P0** | | | **12** |
| G-3, G-8 | MG-P10-01 (determinismo y anillo B completo) | n | 4 |
| G-9 | MG-P10-03 | n | 6 |
| G-10, G-11, G-12 | MG-P10-04 | n | 14 |
| G-13, G-14, G-15 | MG-P10-05 (con la robustez de C2) | n | 12 |
| G-16 | MG-P10-06 | n | 3 |
| G-18, G-19 | MG-P10-07 | n | 6 |
| G-17 | MG-P10-08 | n | 6 |
| G-5, G-20 | MG-P10-09 | n | 5 |
| G-Gate | cierre (parte de MG-P10, sin horas propias: lo absorben las tareas) | n | 0 |
| **Subtotal MG-P10** | | | **56** |
| **Total** | | | **68** (MG-P0 12 + MG-P10 56) |

Por tarea: G-1 1,5; G-2 0,5; G-3 2; G-4 1; G-5 2; G-6 4; G-7 5; G-8 2; G-9 6; G-10 2; G-11 6; G-12 6; G-13 5; G-14 3; G-15 4; G-16 3; G-17 6; G-18 3; G-19 3; G-20 3. Las horas por tarea son estimaciones del plan; el crédito real se mide con el método de la sección 11b del plan maestro (G-4 lo automatiza).

## Dependencias

**Necesita de otros planes**

| De | Tarea | Para qué |
|---|---|---|
| Plan A | `tools/validar_caso_studio.py`, `tools/corpus_studio.py lote`, salud de Studio con estados; `tools/ci.py` y `tools/validacion.py` (sin commitear al redactar este plan) | G-Gate (lote C de L7 y L9) y, si ya están integrados, el paso de pruebas de G-18; este plan **no los modifica** |
| Plan B | B-17 y B-18 (generador de combinaciones de `OUTPUT`: modelo de G-10 y G-13), numeración `l6_01` a `l6_38` | G-13 y G-14 (el rango `l6_80` a `l6_99` para fallos reducidos se confirma libre con Glob al ejecutar); las etapas de L7 y L9 que usen `MERGE` o estado por fila dependen de B |
| Plan C | `tools/linea_base_sql_procs.py` (C-1), SQL completo (C-3 a C-15), numeración `l6_60` a `l6_79` y `l3_13` a `l3_34` | G-11, G-12 y G-13: etapas con `FULL JOIN`, subconsultas o `PROC MEANS` entran como los planes las soporten; G-17 entrega a C el `docs/cobertura.md` que su C-Gate exige |
| Plan D1, D2 | catálogo de funciones, formatos y entrada/salida; códigos `P-` nuevos | G-17 (entradas del catálogo con página), G-20 (`DUENO_POR_CODIGO`) |
| Plan E | macros y `%LET` en L9 (`cartera_mensual` usa `%LET periodo`) | G-12; mientras E no cierre una variable de macro, el caso queda en `CONOCIDOS` con dueño Plan E |
| Plan F1 | F1-5: `tools/calidad_jobs.py` y su tablero (Q1 a Q15); `porcentaje(tablero)` | G-6 (fila C4) y G-18 (paso de calidad); no se repiten sus verificadores `Q1` a `Q15` |
| Plan F2 | emisor: defectos que G-3 (determinismo) y G-9 (`javac`) encuentren | arreglo con prueba propia en ese plan; aquí solo se mide |
| Plan K | K-2 y K-3 (esquemas y datos sintéticos) | G-10 y G-12 si hace falta más volumen que `datos_ficticios.py` |

**Modificaciones a archivos que otros planes también tocan** (rebase obligatorio, sin cambiar lo ajeno): `tests/unit/test_migrar_corpus_anillo_b.py` (G-8 solo helpers; G-10 solo `NIVELES`; G-11 y G-12 solo entradas de `CONOCIDOS`; B, C y E editan `CONOCIDOS` y `NIVELES`), `tests/corpus/migrar_pendientes.yaml` (todos), `plan-migrador-general.md` (G-4 solo dos líneas de marca; G-Gate el «Estado» de MG-P0 y MG-P10) y `src/sgm/cli.py` (G-17: una importación y un registro).

**Entrega a otros planes**

| A | Qué |
|---|---|
| Todos | `tools/medir_anillo_b.py` (cuáles de sus casos siguen en `CONOCIDOS`), `tools/determinismo.py`, `tools/robustez_migrar.py`, `tools/generar_programas_sas.py` (fallos reducidos como casos `l6_80+`) y `tools/medir_programas.py` (brechas ordenadas con su dueño) |
| Plan C | `docs/cobertura.md` y `docs/cobertura.json` generados con `sgm cobertura` |
| Plan F1 y F2 | `tools/tablero_criterios.py` (cómo escribir `out/criterios/<criterio>.json` y qué clave `cifra` mostrar) y la corrida nocturna, que invoca `tools/calidad_jobs.py` |
| Andres (viernes) | `tools/avance_creditos.py`: editar `creditos.yaml` y `--actualizar` recalcula la tabla 11b |

## Self-review

- **Cobertura de la spec:** MG-P0-01 en G-1 y G-2; MG-P0-05 en G-4 y G-6 (más los tiempos de P0-04 y P0-09); MG-P0-06 en G-7; MG-P10-01 en G-3 y G-8; P10-03 en G-9; P10-04 en G-10 a G-12 (20 casos L7 y 20 L9 = 40); P10-05 en G-13 a G-15 (generador con reducción, entradas basura y C2); P10-06 en G-16; P10-07 en G-18 y G-19; P10-08 en G-17; P10-09 en G-5 y G-20; GM5, C1, C3 y C5 en G-Gate. El determinismo por semillas de hash es G-3; el comando que recalcula la tabla 11b es G-4; el termómetro por regiones es G-5.
- **Hechos medidos al redactar** (a confirmar al ejecutar): 221 encabezados `## Hito` y ningún identificador repetido en `PROGRESS.md` (UTF-8, CRLF); `CONOCIDOS` con 5 entradas y `migrar_pendientes.yaml` con 16; `javac` no está en el PATH de esta máquina; `git ls-files '*.sas'` da 375 y el plan maestro dice 189 para C2; `tools/tablero.py` ya existe con 240 líneas; `sgm migrar` termina con código 1 a propósito ante un secreto en claro (regla 7); la frase «719,25 h» de la sección 11b no cuadra con 895 − 237,25.
- **Lo que este plan no hace, a propósito:** no repite los verificadores Q1 a Q15 (son del Plan F1), no implementa semántica SAS en el intérprete (es de B, C y E), no programa tareas en la máquina (G-18 documenta el comando) y no usa Studio salvo el lote de G-Gate.
- **Lo que queda `Pendiente:` si la guía no lo demuestra:** la suma de un grupo con todos los valores faltantes (excluida del generador de G-13 con `P-SUM-TODO-FALTANTE`), y cualquier construcción de G-17 sin página, que se declara `no_verificada` con su motivo.
- **Independencia del esperado:** G-10 (`etapas.py`) y G-13 (`oraculo.py`) no importan `sgm`; una prueba lo comprueba con `ast`. El esperado de L7 y L9 sale de las anomalías plantadas, no del intérprete.
- **Archivos de más de 300 líneas:** ninguna tarea toca `interprete.py`, `lower_sql_flow.py` ni `desde_plan_map.py`; `tools/tablero.py` (240) solo suma una importación y una línea; los módulos nuevos se mantienen bajo 250 líneas.
- **Riesgo de coordinación:** el mismo archivo de prueba (`test_migrar_corpus_anillo_b.py`) lo tocan cuatro planes: este plan hace cambios de una línea o de dos funciones auxiliares y nunca reescribe `CONOCIDOS` ajenos.
- **Proporción:** 20 tareas más la de cierre para 68 h; los cuerpos de funciones los decide quien implementa.
