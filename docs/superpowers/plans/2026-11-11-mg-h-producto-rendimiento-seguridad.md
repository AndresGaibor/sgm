# MG-H: Experiencia de uso, rendimiento y seguridad Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Cerrar MG-P11, MG-P12 y MG-P13 y la compuerta GM6: que `sgm migrar` de una carpeta entregue un proyecto ordenado por dependencias con sobreescrituras YAML validadas, `explicar` y `comparar` sobre `trace.json`, mensajes de pendiente estables con sugerencia y guías generadas; que repetir una corrida sea más rápido con la misma salida y que los Jobs generados tengan límites de volumen medidos y plantillas de JVM; y que ningún informe, registro ni salida de rechazo copie secretos ni datos personales, con una decisión escrita sobre el código de salida de `sgm migrar` ante un secreto.

**Architecture:** Cambios solo en `sgm-v2` (Python), en cinco zonas: `src/sgm/cli*.py` (comandos), `src/sgm/migrar/` (ajustes, dependencias entre programas, registro de códigos, informes), `src/sgm/seguridad/` (privacidad y compuerta), `src/sgm/talend_item/` (enmascarado en el cierre del Job y plantillas de JVM) y `tools/performance/` (banco de volumen y regresión). Cada capacidad nueva entra con su prueba rápida (sin Studio); lo que exige Studio o contenedor se mide al final y, si el entorno no responde, la tarea queda con «lote pendiente» y su motivo.

**Tech Stack:** Python 3.12, Typer, PyYAML, pytest, ruff; `networkx` (ya permitido) para el orden por dependencias. Sin dependencias nuevas. `uv run python -m pytest` y `uv run python -m sgm.cli` (en este Windows `uv run pytest` y `uv run sgm` pueden bloquearse por Control de aplicaciones).

**Spec:** `docs/plan-reescritura/plan-migrador-general.md` (MG-P11-02 a 06, MG-P12-02 a 04, MG-P13-01 residual, 02, 03, 05 residual; criterios C2, C4 y C6; compuerta GM6) y `docs/superpowers/plans/2026-11-11-ruta-al-100.md` (Plan H).

## Lo ya hecho que este plan no repite

Comprobado en `git log` y en `PROGRESS.md` el 12 de noviembre de 2026:

| Tarea del plan maestro | Hito | Qué quedó | Qué falta (lo cubre este plan) |
|---|---|---|---|
| MG-P11-01 | 104m y 132 | `sgm migrar <archivo o carpeta> --out`: Jobs, `trace.json`, `pendientes.md`, `cobertura.md` (por programa), `contextos/`, `configuracion-pendiente.md`, `decisiones-tomadas.md`, `migracion.log`; carpeta recursiva en orden de ruta; `cli_migrar_comando.py` | nada de P11-01 |
| MG-P12-01 | 133 | `tools/performance/migrar.py` y `metrics/performance/mg-p12-01.json`: `client_large.sas` 835 630 bytes en 6,848 s y 93,9 MB; carpeta de 189 programas en 10,860 s y 81,7 MB; ambos bajo 120 s y 1 GB | solo regresión continua y la segunda corrida con caché (H-17) |
| MG-P13-01 | 134 | `sgm migrar` genera en staging, escanea y solo publica si está limpio (`seguridad/compuerta_migracion.py`); `.github/workflows/seguridad-nocturna.yml` | decisión escrita sobre el código de salida 1 frente a C2, informe de bloqueo y su prueba (H-11) |
| MG-P13-04 | 136 | `docs/sbom.md`, `docs/sbom.spdx.json`, `docs/sbom.distribuciones.json`, `tools/seguridad/generar_sbom.py --check` | nada de código; queda la decisión legal de licencia del propio SGM (H-21) y la verificación `--check` en el H-Gate |
| MG-P13-05 | 135 | Identificadores SQL y nombres Java hostiles bloqueados (`java_identificadores.py`, `java_literals.py`, `ir/sql_tree.py`, `ir/sql_render.py`) | valores hostiles dentro de literales (cadenas con comillas, `--`, `;`, `\`, `*/`) en SQL empujado y en expresiones Java: prueba de barrido y arreglos (H-15) |
| MG-P11-02 a 06, MG-P12-02 a 04, MG-P13-02, 03 | (ninguno) | sin empezar; `src/sgm/cache.py` existe pero solo la usa el comando antiguo de `cli.py`, no `sgm migrar` | todo lo de abajo |

**Horas del plan maestro cubiertas:** MG-P11 restante 22 h (30 menos 8 acreditadas) + MG-P12 restante 22 h (30 menos 8) + MG-P13 restante 5 h de P13-03 (más 0,5 día-persona de P13-02, que no cuenta como crédito de agente) = 49 h de crédito. H-11 (decisión de salida) y H-15 (residual de P13-05) suman 3 h de trabajo que no acreditan horas nuevas: P13-01 y P13-05 ya están acreditadas y aquí solo se cierran sus huecos.

**Series de hitos:** `n` (carril de Byron, H-1 a H-21). La letra va en el título de la entrada de `PROGRESS.md` y en el mensaje del commit.

## Global Constraints

- Sin `git push`, sin `--amend`. Un commit local por tarea: `hito N n: <resumen>`, terminado con la línea `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. La `N` se toma al ejecutar: buscar el último `## Hito` de `PROGRESS.md` (al redactar este plan era el 198) y sumar uno; si otra sesión ya tomó el número, el siguiente. No renumerar entradas publicadas.
- No tocar `tools/ci.py`, `tools/validacion.py`, `tools/instalar_ganchos.py`, `README.md` ni `.githooks/` (son del Plan A y están sin commitear). `tools/performance/` y `tools/seguridad/` sí son de este plan.
- Nada de nombres de scripts de ejemplo (`cod1`, `cod2`, `cars_poc`, `exogena`, `split2`, `split3`, `executeBulkload`, `waitForBulkLoads`, `bulkload_generic`) en `src/` ni `rules/`; lo vigila `tests/unit/test_no_script_specific_names.py`. Las listas de columnas sensibles y los códigos se basan en estructura o en palabras genéricas, no en el cliente.
- **No leer ni citar `Cod2.txt` de Descargas** (tiene una contraseña en claro). H-21 solo pide a una persona que la rote; ningún agente abre ese archivo.
- No guardar secretos ni datos personales en pruebas: los valores hostiles y las contraseñas de prueba son cadenas inventadas y obviamente falsas (`clave-de-prueba-1`), nunca copiadas de un fixture real.
- Si el SAS no demuestra algo: `Pendiente:` con motivo y código `P-xxx`; nunca un valor supuesto. Una opción de Talend solo se emite si la página de `docs/referencia/talend/` la documenta; si no, el paso queda pendiente con su código.
- Archivos de menos de 300 líneas. Hoy `src/sgm/cli.py` tiene 299 y `src/sgm/cli_migrar.py` 340: H-1 parte `cli.py` antes de que alguna tarea registre un comando, y toda tarea que toque `cli_migrar.py` extrae primero su bloque a un módulo nuevo (H-5 y H-17 lo hacen en un paso propio, sin cambio de comportamiento).
- Código e identificadores en inglés; comentarios, docstrings, mensajes de usuario y documentación en español.
- Después de cada tarea: `uv run python -m pytest -q` y `uv run ruff check src tests tools` en verde. Para iterar se corre solo el archivo de la tarea con `-p no:cacheprovider`.
- Studio y contenedores: solo en H-20 (lote de volumen, que usa el backend `talend` por `src/sgm/backend_talend/`) y en el H-Gate. Si `sgm studio salud` no conecta, no reinstalar nada ni cambiar `talend-mcp` (`docs/guia-validacion-studio.md`, sección 7). Si `docker version` no responde, la tarea queda con «lote de volumen pendiente» y su motivo, y no se cuenta como pasada.

## Review Focus

- **Un solo código de salida con significado:** `sgm migrar` termina 0 cuando migró (con o sin pendientes), 1 solo cuando la compuerta de secretos bloqueó un paquete, y 2 por uso incorrecto (Typer). C2 mide «sin fallos» contando el 1 por secreto aparte como `bloqueado_por_secreto`. Test en H-11.
- **La compuerta no se salta con la caché:** un paquete restaurado de `.sgm-cache/` pasa otra vez por `publicar_con_revision`. Un paquete bloqueado nunca se guarda en la caché. Test en H-16.
- **Ningún informe copia datos:** ni `pendientes.md`, ni `cobertura.md`, ni `trace.json`, ni `migracion.log`, ni el cierre `tLogRow` de un Job repiten valores de una muestra ni columnas sensibles sin que se haya pedido. Tests en H-12 a H-14.
- **Los mensajes no inventan:** cada código de pendiente tiene texto, causa y sugerencia, y la sugerencia nombra una acción que existe (un comando, un archivo o una decisión), nunca «contacte soporte». Test que recorre el código fuente en H-2.
- **El orden entre programas no es el de ruta:** el lote sigue migrando en orden de ruta (determinista), pero el orden de ejecución sale de lo que cada programa lee y escribe en bibliotecas permanentes; un ciclo se informa, no se oculta. Test en H-6.
- **Límites de volumen medidos, no supuestos:** `docs/volumen-limites.md` solo afirma lo que `metrics/performance/mg-p12-02.json` midió en esta máquina, con sus condiciones.
- **Ningún pase nuevo puede cambiar la firma de los Jobs ya validados** (`test_golden*.py`, `test_ir_operadores_corpus.py` idénticos): el enmascarado de H-13 solo actúa cuando hay columnas sensibles en el cierre.

---

## Parte I. MG-P11 restante: experiencia de uso (serie `n`, 22 h)

### Task H-1: Partir `cli.py` y mover `explain` a su módulo (MG-P11-04, preparación; serie `n`)

`cli.py` tiene 299 líneas y las tareas H-8 y H-9 registran comandos nuevos. Esta tarea no cambia comportamiento.

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\cli.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\cli_explicar.py`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_explain.py` (sin cambios: debe seguir verde)

**Interfaces:**
- Consumes: `explain_mod.explicar(archivo: Path, linea: int, env: Env | None = None) -> str` (`src/sgm/explain.py:27`); `_env()` de `src/sgm/cli_util.py`; la función `explain(ref: Annotated[str, typer.Argument(...)]) -> None` registrada con `@app.command()` en `cli.py:221-233`.
- Produces: `cli_explicar.explain_command(ref: str) -> None` con el mismo cuerpo y el mismo mensaje de error; `cli.py` lo registra con `app.command("explain")(explain_command)`. El nombre del comando y su texto de ayuda no cambian.

- [ ] **Step 1: Medir.** `uv run python -m pytest tests/unit/test_explain.py tests/unit/test_cli_migrar.py -q -p no:cacheprovider`; anotar las pasadas (la referencia que no debe cambiar) y `wc -l src/sgm/cli.py`.
- [ ] **Step 2: Write the failing test** en `tests/unit/test_cli_explicar.py`: `from sgm.cli_explicar import explain_command` importa; `CliRunner().invoke(app, ["explain", "no-existe.sas:3"])` termina con `exit_code == 2` y el mensaje contiene `no existe` (hoy lo da `explicar`).
- [ ] **Step 3: Run test to verify it fails.** `uv run python -m pytest tests/unit/test_cli_explicar.py -q -p no:cacheprovider`; esperado: `ModuleNotFoundError: sgm.cli_explicar`.
- [ ] **Step 4: Implement.** Mover el cuerpo de `explain` a `cli_explicar.py` (con `from sgm.cli_util import _env` y `from sgm import explain as explain_mod`) y registrar el comando en `cli.py`. `wc -l src/sgm/cli.py` debe bajar a menos de 285.
- [ ] **Step 5: Run** la tanda del paso 1 y la del paso 2: mismas pasadas más las nuevas. `uv run ruff check src tests tools`. **Commit** `hito N n: el comando explain pasa a su modulo, cli.py baja de 300 lineas` (con la línea `Co-Authored-By`).

---

### Task H-2: Registro de códigos de pendiente con texto y sugerencia (MG-P11-05, parte 1; serie `n`)

Hoy los códigos `P-xxx` viven como literales sueltos (`P-SIN-PASOS`, `P-FALLO-ESCRITURA`, `P-AGREGADO-SIN-TRADUCIR`, `P-UNION-SIN-LLAVES`, ...) y el mensaje lo escribe cada módulo; nada garantiza que un código nuevo tenga explicación ni sugerencia.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\rules\mensajes\pendientes.yaml`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\codigos_pendiente.py`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_codigos_pendiente.py`

**Interfaces:**
- Consumes: `PendienteMigracion(codigo: str, mensaje: str, linea: int | None)` (`src/sgm/migrar/esquemas.py:52`); la carga de YAML con `yaml.safe_load` como en `src/sgm/motivos.py:_cargar`.
- Produces:
  ```python
  @dataclass(frozen=True)
  class TextoPendiente:
      codigo: str      # "P-SIN-PASOS"
      titulo: str      # una línea, en español
      causa: str       # por qué el migrador no pudo seguir
      sugerencia: str  # qué hacer: un comando, un archivo o una decisión que existen

  def texto_de(codigo: str) -> TextoPendiente | None: ...
  def codigos_registrados() -> frozenset[str]: ...
  def codigos_en_codigo_fuente(raiz: Path) -> frozenset[str]:
      """Cada literal `"P-[A-Z0-9-]+"` de `src/**/*.py` (sin comentarios)."""
  ```
  Formato de `pendientes.yaml`: una clave por código con `titulo`, `causa` y `sugerencia`.

- [ ] **Step 1: Write the failing tests.** (a) `texto_de("P-SIN-PASOS")` devuelve un `TextoPendiente` con `titulo` no vacío y `sugerencia` que contiene `%include` (el motivo real es una macro sin `%mend` o un `%include` ausente); `texto_de("P-NO-EXISTE")` es `None`. (b) **Prueba de barrido:** `codigos_en_codigo_fuente(raiz) - codigos_registrados()` es el conjunto vacío; el mensaje del `assert` lista los códigos sin texto. (c) Ninguna `sugerencia` contiene «contacte», «soporte» ni «TBD», y cada una tiene al menos 20 caracteres.
- [ ] **Step 2: Run test to verify it fails.** `uv run python -m pytest tests/unit/test_codigos_pendiente.py -q -p no:cacheprovider`; esperado: no existe el módulo.
- [ ] **Step 3: Implement.** Generar `pendientes.yaml` con una entrada por cada código que hoy devuelva `codigos_en_codigo_fuente` (al redactar el plan eran 43, de `P-AGREGADO-COLUMNA-DESCONOCIDA` a `P-UNION-TIPO-SIN-SOPORTE`; incluye los de series viejas `P-CTX-01`, `P-DB-01`, `P-ERR-01`, `P-NAME-01`, `P-NAME-02`, `P-SEC-01`, `P-SIZE-01`). Cada texto sale del código que lo emite (leer su `mensaje` real con `Grep`), no de una suposición; donde la causa no se pueda leer del código, la entrada dice «verificar al ejecutar» en `causa` y el paso lo anota en `PROGRESS.md`. Las sugerencias nombran cosas que existen: `--esquemas <carpeta>` (esquema ausente), `decisiones/<programa>.decisiones.yaml` (decisión de diseño), `--muestra <carpeta>` (tipos), `rules/` (regla nueva con `sgm rules new`).
- [ ] **Step 4: Run test to verify it passes.** Después `uv run python -m pytest tests/unit/test_no_script_specific_names.py -q -p no:cacheprovider` (el YAML no debe nombrar scripts del cliente).
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N n: registro de codigos de pendiente con texto y sugerencia`.

---

### Task H-3: `pendientes.md` y la consola muestran la sugerencia (MG-P11-05, parte 2; serie `n`)

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\informes.py` (312 líneas: extraer primero `pendientes_md` a `src/sgm/migrar/informes_pendientes.py`, paso sin cambio de comportamiento)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\informes_pendientes.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\cli_migrar_comando.py`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_informes_pendientes.py`

**Interfaces:**
- Consumes: `pendientes_md(programa: str, pendientes: list[PendienteMigracion]) -> str` (`informes.py:48`); `codigos_pendiente.texto_de(codigo) -> TextoPendiente | None` (H-2).
- Produces:
  ```python
  # informes_pendientes.py (informes.py lo reexporta con el mismo nombre)
  def pendientes_md(programa: str, pendientes: list[PendienteMigracion]) -> str:
      """Tabla `Código | Línea | Motivo | Qué hacer`; debajo, una sección `## Códigos` con
      título, causa y sugerencia de cada código presente, sin repetir los ya explicados."""
  ```
  La salida de `sgm migrar` de un programa con pendientes suma la línea `  ver <carpeta>/pendientes.md (sugerencias por código)`.

- [ ] **Step 1: Extraer** `pendientes_md` y `_orden` a `informes_pendientes.py` sin cambiar el texto de salida; `tests/unit/test_cli_migrar.py` y los tests de informes siguen idénticos (anotar el conteo antes y después). `wc -l src/sgm/migrar/informes.py` baja de 300.
- [ ] **Step 2: Write the failing tests.** Con `[PendienteMigracion("P-SIN-PASOS", "vacío", None), PendienteMigracion("P-SIN-PASOS", "otro", 7)]`: la salida contiene una sola sección `### P-SIN-PASOS` en `## Códigos`; la fila de la línea 7 aparece antes que la de línea `—`; el texto de la sugerencia de H-2 está en la salida. Con un código desconocido (`P-NO-EXISTE`) la fila sale con `Qué hacer` = `sin texto registrado` y la sección no se genera (el test de H-2 ya impide que pase en el código real).
- [ ] **Step 3: Run tests to verify they fail**; esperado: la tabla tiene tres columnas.
- [ ] **Step 4: Implement** la cuarta columna y la sección `## Códigos` con `texto_de`. Mantener la salida determinista (orden por línea, código y mensaje).
- [ ] **Step 5: Run** `tests/unit/test_cli_migrar.py` (el caso `test_pendientes_se_listan_con_codigo_y_linea` se actualiza para esperar la columna nueva: se amplía, no se debilita) y la suite de golden. `uv run ruff check src tests tools`. **Commit** `hito N n: pendientes.md explica cada codigo y dice que hacer`.

---

### Task H-4: Cargador y validador del YAML de ajustes con archivo y línea (MG-P11-02, parte 1; serie `n`)

El YAML de ajustes es opcional (`sgm migrar` sin YAML sigue funcionando). Lo que depende del nombre del cliente va a `decisiones/<programa>.*.yaml`, nunca a `src/` ni a `rules/`; este YAML es la forma de pasar esos ajustes a un solo comando.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\ajustes.py`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_ajustes.py`

**Interfaces:**
- Consumes: `yaml.compose(stream)` de PyYAML (los nodos traen `start_mark.line` y `start_mark.column`, base 0); `java_identificadores` (`src/sgm/java_identificadores.py`, la función que decide si un nombre es un identificador Java portable: leer su nombre real con `Grep "^def " src/sgm/java_identificadores.py` y usarla tal cual).
- Produces:
  ```python
  class ErrorDeAjustes(ValueError):
      """Un error por problema, con `archivo:línea:columna: mensaje`."""
      def __init__(self, errores: list[str]) -> None: ...

  @dataclass(frozen=True)
  class Ajustes:
      nombres: dict[str, str]       # Job generado -> nombre que pide la persona
      contexto: dict[str, str]      # parámetro de contexto -> valor (nunca un secreto)
      agrupacion: dict[str, list[str]]  # reservado: ver H-5
      privacidad_incluir: frozenset[str]   # H-12
      privacidad_excluir: frozenset[str]   # H-12
      volumen: dict[str, int]       # tabla -> filas estimadas (H-19)

  def cargar_ajustes(ruta: Path) -> Ajustes: ...
  ```
  Esquema del YAML: claves de primer nivel `nombres`, `contexto`, `agrupacion`, `privacidad` (con `incluir` y `excluir`) y `volumen` (la usa H-19); cualquier otra clave es error `clave desconocida`.

- [ ] **Step 1: Write the failing tests** con YAML en `tmp_path`. Entrada `nombres: {job_a: 3}` (valor no texto) falla con un mensaje que empieza por `ajustes.yaml:2:` y dice `se esperaba texto`. Entrada con tabulador de sangría falla con el error de sintaxis de PyYAML convertido a `ajustes.yaml:<línea>:<columna>:`. Clave `nombress:` falla con `clave desconocida 'nombress'; claves válidas: agrupacion, contexto, nombres, privacidad, volumen`. `contexto: {clave: "abc"}` falla con `parece una credencial; use una variable de entorno (docs/secretos.md)` (reutilizar la detección de nombres de `redaction.py`: `_NAME_VALUE`). Dos errores en el mismo archivo se informan juntos, ordenados por línea. Un YAML válido devuelve `Ajustes` con los cuatro campos y `cargar_ajustes` de un archivo vacío devuelve `Ajustes` con todo vacío.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_ajustes.py -q -p no:cacheprovider`; esperado: no existe el módulo.
- [ ] **Step 3: Implement** `cargar_ajustes` con `yaml.compose` para las posiciones y `yaml.safe_load` para los valores. Nombres de Job: deben ser identificadores portables según la función de `java_identificadores`.
- [ ] **Step 4: Run test to verify it passes.**
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N n: ajustes opcionales en YAML con errores de archivo y linea`.

---

### Task H-5: `sgm migrar --ajustes` aplica nombres y valores de contexto (MG-P11-02, parte 2; serie `n`)

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\cli_migrar.py` (340 líneas: extraer primero `_contexto_yaml` y `_escribir` a `src/sgm/migrar/escritura_paquete.py`, paso propio sin cambio de comportamiento; la suite y los bytes de salida deben quedar idénticos)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\escritura_paquete.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\cli_migrar_comando.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\rules\mensajes\pendientes.yaml` (códigos `P-AJUSTE-NOMBRE-SIN-JOB` y `P-AJUSTE-AGRUPACION-PENDIENTE`)
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_cli_migrar_ajustes.py`

**Interfaces:**
- Consumes: `migrar(source: Path, out: Path, esquemas: Path | None = None, muestra: Path | None = None, backend: str = "archivos") -> ResultadoMigrar` (`cli_migrar.py:271`); `ResultadoMigrar.jobs: list[Job]` y `Job.nombre`; `contextos_de_plan(plan) -> dict[str, list[ParametroContexto]]` y `GRUPOS` (`talend_item/desde_plan_contextos.py`); `cargar_ajustes(ruta: Path) -> Ajustes` (H-4).
- Produces: `migrar(..., ajustes: Ajustes | None = None)` y la opción `--ajustes <archivo.yaml>` de `sgm migrar`.
  - `nombres`: renombra el Job antes de escribir; si el nombre de origen no existe entre los Jobs generados, `PendienteMigracion("P-AJUSTE-NOMBRE-SIN-JOB", "<nombre>", None)`.
  - `contexto`: pone el valor en el parámetro del grupo de `contextos/` que se llama igual; un parámetro inexistente es `P-AJUSTE-CONTEXTO-SIN-PARAMETRO` (se agrega al YAML de H-2).
  - `agrupacion`: se valida y se informa como `P-AJUSTE-AGRUPACION-PENDIENTE` («lo define el Plan F2: padre e hijos»); no se aplica. Cuando el Plan F2 publique su interfaz, esa sección se conecta en un hito propio.
  - Sin `--ajustes` la salida es idéntica byte a byte a la de hoy.

- [ ] **Step 1: Extraer** `_contexto_yaml` y `_escribir` a `escritura_paquete.py` (sin cambio de comportamiento); correr `tests/unit/test_cli_migrar.py` y `test_golden*.py`: mismas pasadas. `wc -l src/sgm/cli_migrar.py` baja de 300.
- [ ] **Step 2: Write the failing tests.** Migrar `tests/corpus/L2/l2_01*/programa.sas` (usar el caso real que ya usa `test_migrar_l2_01_escribe_todo`) con un `ajustes.yaml` `nombres: {<job real>: Resumen_Cartera}`: existe `process/Resumen_Cartera*.item` y no el nombre anterior; `trace.json` lleva el nombre nuevo. Con `contexto: {ruta_base: /datos/qa}` y un parámetro `ruta_base` presente, `contextos/*.yaml` lleva `/datos/qa`. Un YAML con `nombres: {x: 3}` hace que el comando termine con código 2 y el mensaje `ajustes.yaml:1:` y no escribe nada en `--out`. Sin `--ajustes`, los bytes de la carpeta de salida igualan a los de una corrida sin la opción (comparar con `sorted(rglob)` y `read_bytes`).
- [ ] **Step 3: Run tests to verify they fail**; esperado: `No such option: --ajustes`.
- [ ] **Step 4: Implement** la opción (validar antes de migrar, como se hace con `validate_backend`, para no dejar carpeta a medias) y la aplicación de `nombres` y `contexto`. El nombre nuevo pasa por `java_identificadores` otra vez dentro de `migrar` (no se confía solo en H-4).
- [ ] **Step 5: Run** los tests del paso 2, la suite completa y `uv run ruff check src tests tools`. **Commit** `hito N n: sgm migrar acepta ajustes de nombres y contexto`.

---

### Task H-6: Dependencias entre programas y orden de ejecución (MG-P11-03, parte 1; serie `n`)

El lote hoy recorre por ruta relativa y avisa «el orden no representa dependencias de ejecución». Un programa depende de otro si lee una tabla de una biblioteca permanente que el otro escribe, o si lo incluye con `%include`. Las tablas de `WORK` mueren con la sesión y no crean dependencia. Limitación declarada: dos programas que llaman distinto (`LIBNAME`) a la misma carpeta física no se emparejan, porque el plan solo conoce el alias; `proyecto.md` lo dice en una nota.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\dependencias.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\cli_migrar.py` (solo el dataclass `ResultadoMigrar`: dos campos nuevos `lee` y `escribe`, y llenarlos en `migrar` desde el plan; si H-5 ya extrajo bloques, el cambio queda dentro del límite de 300 líneas)
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_dependencias.py`

**Interfaces:**
- Consumes: `leer(op_id, dataset, ...)` y `escribir(op_id, dataset, ...)` de `src/sgm/ir/operadores.py:63,127` (los operadores del plan llevan `kind` `"read"` o `"write"` y el parámetro `dataset`; el atributo exacto de `Operator` con los parámetros se lee de `src/sgm/ir/models.py` al ejecutar); `Plan.graph.operators()`.
- Produces:
  ```python
  @dataclass(frozen=True)
  class OrdenDeProyecto:
      orden: tuple[str, ...]                      # programas, dependencias primero
      aristas: tuple[tuple[str, str, str], ...]   # (productor, consumidor, tabla)
      ciclos: tuple[tuple[str, ...], ...]         # cada ciclo, con programas ordenados por nombre
      sin_productor: dict[str, tuple[str, ...]]   # programa -> tablas permanentes que lee y nadie escribe

  def tablas_permanentes(datasets: set[str]) -> set[str]:
      """Las de una biblioteca distinta de WORK (`lib.tabla`, sin distinguir mayúsculas)."""

  def orden_de_proyecto(
      lee: dict[str, set[str]], escribe: dict[str, set[str]]
  ) -> OrdenDeProyecto:
      """Orden topológico estable (desempata por nombre) con `networkx`; los programas de un
      ciclo se agrupan al final, en orden alfabético, y el ciclo se informa."""
  ```

- [ ] **Step 1: Write the failing tests.** `lee={"b": {"dw.ventas"}, "a": set(), "c": {"dw.resumen"}}`, `escribe={"a": {"dw.ventas"}, "b": {"dw.resumen"}, "c": set()}` da `orden == ("a", "b", "c")` y `aristas == (("a","b","dw.ventas"),("b","c","dw.resumen"))`. Una tabla `WORK.t` escrita por `a` y leída por `b` no crea arista. Ciclo `a`↔`b` da `ciclos == (("a","b"),)` y ambos al final. Una tabla leída que nadie escribe (`dw.maestro`) queda en `sin_productor["b"]` (es una entrada externa, no un error). Mayúsculas: `DW.Ventas` y `dw.ventas` son la misma tabla. Determinismo: mezclar el orden de las claves de los diccionarios no cambia el resultado.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_dependencias.py -q -p no:cacheprovider`; esperado: no existe el módulo.
- [ ] **Step 3: Implement** con `networkx.DiGraph`, `lexicographical_topological_sort` para el desempate, y `strongly_connected_components` para los ciclos. En `migrar`, llenar `ResultadoMigrar.lee` y `.escribe` con los `dataset` de los operadores `read` y `write` del plan original (antes del despliegue de plantillas), ya filtrados por `tablas_permanentes`.
- [ ] **Step 4: Run test to verify it passes** y la tanda de `tests/unit/test_cli_migrar.py` (sin cambios de salida).
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N n: orden de ejecucion entre programas por tablas permanentes`.

---

### Task H-7: El lote escribe `proyecto.md` y `proyecto.json` (MG-P11-03, parte 2; serie `n`)

Aceptación del plan maestro: una carpeta con 5 programas se migra a un proyecto coherente. La columna de Jobs usa `len(resultado.jobs)`; H-16 la cambia a `total_jobs` porque una restauración de caché no trae los objetos `Job`. Antes de crear `tests/corpus/proyectos/`, comprobar con `Grep "glob" tools/corpus.py tools/corpus_lib tests/unit/test_corpus*.py` que ninguna prueba recorre todo `tests/corpus/`; si alguna lo hace, la carpeta va a `tests/fixtures/proyectos/cinco_programas/` con la misma estructura.

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\cli_migrar_comando.py` (133 líneas)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\proyecto.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\proyectos\cinco_programas\{a_carga.sas, b_limpieza.sas, c_resumen.sas, d_reporte.sas, e_independiente.sas}` (carpeta nueva dentro de `tests/corpus/`; los programas son pequeños, con `LIBNAME dw` y tablas `dw.*` inventadas, sin datos reales)
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_migrar_proyecto.py`

**Interfaces:**
- Consumes: `OrdenDeProyecto` y `orden_de_proyecto(lee, escribe)` (H-6); `ResultadoMigrar` (`carpeta`, `jobs`, `pendientes`, `lee`, `escribe`); `informes.escribir(carpeta: Path, nombre: str, contenido: str) -> Path` (`informes.py:225`).
- Produces:
  ```python
  def proyecto_md(orden: OrdenDeProyecto, resultados: dict[str, ResultadoMigrar]) -> str:
      """`# Proyecto`: tabla de ejecución (n.º, programa, Jobs, pendientes, lee, escribe), lista de
      ciclos, entradas externas y la ruta de cada paquete."""
  def proyecto_json(orden: OrdenDeProyecto, resultados: dict[str, ResultadoMigrar]) -> str:
      """Mismo contenido, claves ordenadas, `ensure_ascii=False`, sin rutas absolutas."""
  ```
  `sgm migrar <carpeta>` escribe `<out>/proyecto.md` y `<out>/proyecto.json` y cambia la advertencia final por «Orden de ejecución en proyecto.md (por tablas permanentes; ver ciclos)». Un programa bloqueado por la compuerta de seguridad aparece en la tabla con `bloqueado` y no tiene ruta de paquete.

- [ ] **Step 1: Write the failing tests.** La carpeta `cinco_programas`: `a_carga` escribe `dw.base`; `b_limpieza` lee `dw.base` y escribe `dw.limpia`; `c_resumen` lee `dw.limpia` y escribe `dw.resumen`; `d_reporte` lee `dw.resumen`; `e_independiente` no toca `dw`. `CliRunner().invoke(app, ["migrar", carpeta, "--out", salida])` termina con código 0, `proyecto.json["orden"]` empieza con `a_carga` y `b_limpieza` antes de `c_resumen` antes de `d_reporte`, `e_independiente` está en la lista, y `proyecto.md` contiene la tabla. Dos corridas dan los mismos bytes. Una carpeta con un solo programa también escribe `proyecto.md`. Con `a_carga` y `b_limpieza` cruzados en ciclo (segundo directorio del test), el código sigue en 0 y el ciclo aparece en `proyecto.md`.
- [ ] **Step 2: Run tests to verify they fail**; esperado: no existe `proyecto.json`.
- [ ] **Step 3: Implement** `proyecto.py` y llamarlo desde la rama de carpeta de `migrar_command`. El recorrido y la migración siguen en orden de ruta (sin cambio de bytes en los paquetes); solo el informe del proyecto usa el orden de ejecución. Las rutas de `proyecto.md` son relativas a `--out`.
- [ ] **Step 4: Run tests to verify they pass**, más `tests/unit/test_cli_migrar.py` (`test_migrar_carpeta_conserva_rutas_y_nombres_repetidos`, `test_migrar_carpeta_es_determinista`).
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N n: la carpeta migra a un proyecto con orden de ejecucion`.

---
### Task H-8: `sgm explicar` sobre `trace.json` (MG-P11-04, parte 1; serie `n`)

Ya existe `sgm explain <archivo>:<línea>` (F1.8): compila el programa de nuevo y es lento con programas grandes. `sgm explicar` lee el paquete que dejó `sgm migrar` (`trace.json` y `pendientes.md`) y no vuelve a compilar. `explain` se conserva.

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\cli_explicar.py` (creado en H-1)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\explicar_paquete.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\cli.py` (una línea: `app.command("explicar")(explicar_command)`)
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_explicar_paquete.py`

**Interfaces:**
- Consumes: el formato de `trace.json` escrito por `informes.trace_json(programa, jobs, traza)` (`informes.py:202`): `{"programa": str, "jobs": {<Job>: {<nodo>: [líneas SAS, ordenadas]}}}`; el formato de `pendientes.md` (`pendientes_md`, tabla con código, línea y motivo; con H-3 una cuarta columna); `codigos_pendiente.texto_de(codigo)` (H-2).
- Produces:
  ```python
  def explicar_linea(paquete: Path, linea: int) -> str:
      """Texto con: Jobs y nodos cuya traza incluye la línea; pendientes de esa línea con su
      código, motivo y sugerencia; y, si no hay ninguno, la frase
      `la línea N no tiene nodo ni pendiente: es fontanería, comentario o no se tradujo`
      (nunca inventa una relación). Lanza FileNotFoundError si el paquete no tiene trace.json."""

  def explicar_command(
      paquete: Annotated[Path, typer.Argument(help="Carpeta que escribió `sgm migrar`.")],
      linea: Annotated[int, typer.Argument(help="Línea del programa SAS.")],
  ) -> None: ...
  ```
  Uso: `sgm explicar out/mi_programa 120`.

- [ ] **Step 1: Write the failing tests.** Con un paquete mínimo en `tmp_path` (`trace.json` con `{"programa":"p","jobs":{"J1":{"tMap_1":[10,11,12],"tFileOutputDelimited_1":[13]}}}` y un `pendientes.md` con una fila `P-SIN-PASOS | 20 | vacío`): `explicar_linea(paquete, 11)` contiene `J1` y `tMap_1`; `explicar_linea(paquete, 13)` contiene `tFileOutputDelimited_1`; la línea 20 lista `P-SIN-PASOS` con su sugerencia de H-2; la línea 99 devuelve la frase de «no tiene nodo ni pendiente». Una línea cubierta por dos nodos los lista a los dos en orden de nombre. Sin `trace.json` el comando termina con código 2 y dice `no es un paquete de sgm migrar`. Línea `0` o negativa: código 2.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_explicar_paquete.py -q -p no:cacheprovider`; esperado: no existe el módulo.
- [ ] **Step 3: Implement** `explicar_paquete.py` (lee JSON y parsea la tabla Markdown de `pendientes.md` por columnas; si el formato no se reconoce, solo informa los nodos) y el comando.
- [ ] **Step 4: Run test to verify it passes.** Prueba de extremo a extremo: migrar `tests/corpus/L2/l2_01*/programa.sas` con `CliRunner` y explicar una línea que `trace.json` cubra: el texto nombra un nodo real.
- [ ] **Step 5: Run** `uv run python -m pytest tests/unit/test_explain.py -q -p no:cacheprovider` (sin cambios) y `uv run ruff check src tests tools`. **Commit** `hito N n: sgm explicar lee trace.json del paquete`.

---

### Task H-9: `sgm comparar --paquete` apunta a las líneas del SAS (MG-P11-04, parte 2; serie `n`)

`comparar_command(sas: Path, talend: Path)` (`src/sgm/verify.py:91`) compara filas, sumas y huella de dos exportaciones y sale con código 1 si no coinciden. Aquí se integra con `trace.json`: ante una diferencia, dice qué nodos de salida y qué líneas del SAS revisar.

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\verify.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\pistas_de_diferencia.py`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_comparar_salidas.py` (existente: se amplía)

**Interfaces:**
- Consumes: `comparar(sas: Path, talend: Path)` y el informe con `.coincide` y `.texto()` (`verify.py`); `explicar_paquete` (H-8) para leer `trace.json`.
- Produces:
  ```python
  # pistas_de_diferencia.py
  def pistas(paquete: Path, tabla: str) -> list[str]:
      """Líneas de texto `Job J1, nodo tFileOutputDelimited_1: líneas SAS 40-45` de los nodos de
      salida (`tFileOutput*`, `tDBOutput*`, `tLogRow`) del paquete; `tabla` filtra los nodos
      cuyo nombre contiene el stem del archivo comparado si hay alguno que coincida, y si no
      lista todos los nodos de salida. Verificar al ejecutar los prefijos reales de
      `src/sgm/talend_item/escritura.py` y `desde_plan_nodos_escritura.py`."""
  # verify.py
  def comparar_command(sas: Path, talend: Path, paquete: Path | None = None) -> None: ...
  ```
  Con `--paquete` y diferencias, la salida termina con `Dónde mirar:` y las pistas; sin `--paquete` la salida y el código son idénticos a los de hoy.

- [ ] **Step 1: Write the failing tests.** Con dos CSV que difieren (una fila de más) y un paquete mínimo con `trace.json` (`{"programa":"p","jobs":{"J1":{"tFileOutputDelimited_1":[40,41,42,43,44,45]}}}`): el código es 1 y la salida contiene `Dónde mirar:` y `líneas SAS 40-45`. Con CSV iguales: código 0 y sin `Dónde mirar:`. Sin `--paquete` con diferencias: salida exactamente igual a la anterior (se compara con el texto de `informe.texto()`). Un paquete sin `trace.json`: código 2 y `no es un paquete de sgm migrar`. Líneas no consecutivas se muestran como `40-42, 50`.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_comparar_salidas.py -q -p no:cacheprovider -k paquete`; esperado: `No such option: --paquete`.
- [ ] **Step 3: Implement** `pistas` y la opción. La tolerancia numérica de la corrida paralela (MG-D07) no se toca aquí: es de P14.
- [ ] **Step 4: Run test to verify it passes**, y el resto de `test_comparar_salidas.py` sin cambios.
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N n: sgm comparar indica nodos y lineas SAS con --paquete`.

---

### Task H-10: Guía de usuario, guía de operación y catálogo de construcciones generados (MG-P11-06; serie `n`)

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\generar_documentacion.py`
- Create (generados, versionados): `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\docs\guia-de-usuario.md`, `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\docs\guia-de-operacion.md`, `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\docs\catalogo-construcciones.md`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_generar_documentacion.py`

**Interfaces:**
- Consumes: `rules/sas/catalogo/*.yaml` (cada entrada: `id`, `nombre`, `fuente`, `estado` en `reconocida`, `no_reconocida`, `no_verificada`, `dentro_de_select`; esquema en `schemas/rules/catalogo.schema.json`); `codigos_pendiente.texto_de` y `codigos_registrados()` (H-2); la app de Typer en `sgm.cli` (`typer.main.get_command(app)` para listar comandos y opciones); `docs/secretos.md` y `docs/guia-validacion-studio.md` como remisiones, no copias.
- Produces:
  ```python
  def catalogo_md(raiz: Path) -> str:
      """Por archivo de `rules/sas/catalogo/`: tabla `Construcción | Estado | Fuente`, con totales por estado al inicio."""
  def guia_de_usuario_md(raiz: Path) -> str:
      """Qué es, instalación (`uv run python -m sgm.cli`), `sgm migrar` (opciones reales leídas de Typer), ajustes YAML (H-4), `explicar`, `comparar`, tabla de códigos de pendiente con sugerencia, y códigos de salida 0/1/2 (H-11)."""
  def guia_de_operacion_md(raiz: Path) -> str:
      """Orden de ejecución del proyecto (`proyecto.md`), contextos DEV/QA/PROD y secretos (remite a `docs/secretos.md`), JVM y volumen (remite a `docs/volumen-jvm.md`, H-20), caché (`.sgm-cache/`, H-17), qué hacer si la compuerta bloquea."""
  def main(argv: list[str] | None = None) -> int:
      """`--check`: código 1 si algún archivo difiere de lo generado, sin escribir. Sin `--check`, escribe los tres."""
  ```

- [ ] **Step 1: Write the failing tests.** `catalogo_md(raiz)` cuenta las entradas de `rules/sas/catalogo/*.yaml` y su total coincide con la suma de los totales por estado impresos. `guia_de_usuario_md` contiene cada opción de `sgm migrar` (`--out`, `--esquemas`, `--muestra`, `--backend`, y las que sumen H-5 y H-17), cada código de `codigos_registrados()` y las palabras `código 1` y `secreto`. `main(["--check"])` sobre un árbol en `tmp_path` sin los tres archivos devuelve 1; tras `main([])` devuelve 0; tras editar a mano una línea vuelve a 1. La salida es determinista (sin fechas ni rutas absolutas).
- [ ] **Step 2: Run tests to verify they fail**; esperado: no existe `tools/generar_documentacion.py`.
- [ ] **Step 3: Implement**, siguiendo el patrón de `tools/seguridad/generar_sbom.py` (modo `--check`, biblioteca estándar y PyYAML). Los textos fijos de las guías van en el generador, en español, sin Markdown suelto de plantilla de IA ni emojis.
- [ ] **Step 4: Run test to verify it passes.** Generar los tres documentos con `uv run python tools/generar_documentacion.py` y revisar a mano que la guía de operación solo remite a documentos y opciones que existen (`Glob` de cada ruta citada). Aplicar la habilidad `redaccion-documentos-bancarios` solo a los textos fijos del generador, no al catálogo generado.
- [ ] **Step 5: Run** `uv run python tools/generar_documentacion.py --check` (código 0), `uv run ruff check src tests tools`. **Commit** `hito N n: guias de usuario y operacion y catalogo de construcciones generados`.

---

## Parte II. MG-P13 restante: seguridad (serie `n`, 5 h de crédito más 3 h de cierre de huecos)

### Task H-11: Decisión del código de salida ante un secreto, informe de bloqueo y su prueba (MG-P13-01 residual y C2; serie `n`)

**La decisión (a registrar en `PROGRESS.md`, «Decisiones»):** `sgm migrar` termina con 0 cuando migró, con o sin pendientes; con **1** cuando la compuerta de secretos bloqueó al menos un paquete (el valor no se publica: regla 7 de `AGENTS.md`); con **2** por uso incorrecto (Typer). C2 no se redefine como «nunca 1»: C2 mide dos cosas, (a) pasos traducidos más pendientes igual a pasos del SAS y (b) cero trazas de Python, cero cuelgues y cero salidas sin informe; el 1 por secreto se cuenta aparte como `bloqueado_por_secreto` y no es un fallo (Plan G, G-15). Lo que cambia con esta tarea: un paquete bloqueado hoy no deja **ningún** informe (nada se publica), y la persona no sabe qué corregir. Se agrega `<out>/<programa>.bloqueado.md`, sin valores, con archivo, línea y tipo del hallazgo.

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\cli_migrar_comando.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\seguridad\informe_bloqueo.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\docs\plan-reescritura\plan-migrador-general.md` (fila C2 de la tabla de criterios, línea 105: dejar escrito que el 1 por secreto es la compuerta funcionando, igual que el texto de G-15; mismo cambio que el código, sin contradicción)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\docs\secretos.md` (sección de la compuerta: tabla de códigos de salida)
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_codigos_de_salida_migrar.py`

**Interfaces:**
- Consumes: `ResultadoMigrar.hallazgos_seguridad: tuple[Hallazgo, ...]` y `.fallo_seguridad: str | None` (`cli_migrar.py:81-82`); `Hallazgo` con `archivo`, `linea`, `tipo`, `valor` (`seguridad/escaner_secretos.py`; el `valor` ya viene enmascarado a dos caracteres más `***` y aun así **no** se escribe en el informe); `_seguridad_fallida(resultado)` y `_informar_seguridad(resultado)` de `cli_migrar_comando.py`.
- Produces:
  ```python
  def bloqueado_md(programa: str, hallazgos: tuple[Hallazgo, ...], fallo: str | None) -> str:
      """`# Paquete no publicado: <programa>`; por hallazgo `archivo:línea: tipo` (sin valor); si hay `fallo`, su texto genérico; y el paso siguiente: `reemplace el valor por una variable de entorno o por '***' y vuelva a correr sgm migrar (docs/secretos.md)`."""
  ```
  El informe se escribe en `<out>/<programa>.bloqueado.md` (fuera de la carpeta del paquete, que no se publica) y no lo marca la compuerta porque no contiene valores. Una corrida posterior sin hallazgos borra el `.bloqueado.md` del programa.

- [ ] **Step 1: Write the failing tests.** (a) Un programa con `LIBNAME x ... PASSWORD='clave-de-prueba-1';` (cadena inventada) migrado con `CliRunner`: `exit_code == 1`; existe `<out>/<programa>.bloqueado.md` con `:` y el tipo del hallazgo y **no** contiene `clave-de-prueba-1` ni `cl***`; no existe la carpeta del paquete publicada; la salida estándar no contiene la clave. (b) Un programa limpio: `exit_code == 0`, no hay `.bloqueado.md`. (c) Una carpeta con un programa limpio y otro con secreto: el limpio se publica, el otro queda con su `.bloqueado.md`, `exit_code == 1`, y el mensaje final dice `1 paquete(s) no publicado(s)` (comportamiento actual, solo se fija con prueba). (d) Un programa con pendientes pero sin secreto: `exit_code == 0` (los pendientes no son fallo). (e) Una opción inexistente: `exit_code == 2`. (f) Segunda corrida del programa de (a) ya sin la contraseña: `exit_code == 0` y el `.bloqueado.md` ya no existe. (g) **Contra C2:** en `tests/unit/test_cli_migrar.py::test_entrada_basura_sale_con_0` (ya parametrizada) se añade un comentario que remite a esta decisión; las entradas basura siguen con código 0.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_codigos_de_salida_migrar.py -q -p no:cacheprovider`; esperado: no existe `.bloqueado.md`.
- [ ] **Step 3: Implement** `informe_bloqueo.bloqueado_md` y su escritura desde `migrar_command` (rama de archivo y rama de carpeta). No se cambia ningún código de salida: la tarea fija lo que ya hace el código con una prueba y le da a la persona el informe que le faltaba.
- [ ] **Step 4: Run test to verify it passes**, más `tests/unit/test_cli_migrar.py` y las pruebas de la compuerta (`tests/unit/test_secretos_cli.py`, `test_secretos_limpios.py`, `test_secretos_plantados.py`).
- [ ] **Step 5: Corrida nocturna.** Confirmar con `Grep "secretos" docs/superpowers/plans/2026-11-11-mg-g-verificacion-y-cobertura.md` y, si el Plan G ya creó `tools/corrida_nocturna.py`, con `Grep "secretos" tools/corrida_nocturna.py`, que la corrida nocturna de Plan G ejecuta `sgm secretos` sobre `out/` y `decisiones/` (el workflow `.github/workflows/seguridad-nocturna.yml` del hito 134 ya lo hace en CI). Si el Plan G aún no está integrado, anotar en `PROGRESS.md` «P13-01 en la corrida nocturna de Plan G: pendiente de integración» y no tocar `tools/` de otro plan. Actualizar la fila C2 y `docs/secretos.md`.
- [ ] **Step 6: Run** `uv run ruff check src tests tools`. **Commit** `hito N n: codigo de salida 1 ante un secreto decidido, probado y con informe de bloqueo`.

---

### Task H-12: Lista configurable de columnas sensibles (MG-P13-03, parte 1; serie `n`)

Los registros (`tLogRow` de cierre) y los archivos de rechazo no deben copiar columnas con datos personales si nadie lo pidió. Esta tarea define qué columna es sensible; H-13 la aplica.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\rules\privacidad\columnas-sensibles.yaml`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\seguridad\privacidad.py`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_privacidad.py`

**Interfaces:**
- Consumes: `Ajustes.privacidad_incluir` y `Ajustes.privacidad_excluir` (H-4, `frozenset[str]` de nombres de columna); `ErrorDeAjustes` (H-4).
- Produces:
  ```python
  @dataclass(frozen=True)
  class PoliticaPrivacidad:
      patrones: tuple[str, ...]        # subcadenas, sin distinguir mayúsculas (del YAML)
      incluir: frozenset[str]          # columnas que se tratan como sensibles además de los patrones
      excluir: frozenset[str]          # columnas que NO se enmascaran aunque coincidan con un patrón (decisión explícita)

  def politica(ajustes: Ajustes | None = None, ruta: Path | None = None) -> PoliticaPrivacidad: ...
  def es_sensible(nombre: str, politica: PoliticaPrivacidad) -> bool:
      """`nombre` (sin distinguir mayúsculas) está en `incluir`, o contiene un patrón y no está en `excluir`."""
  def columnas_sensibles(nombres: list[str], politica: PoliticaPrivacidad) -> list[str]: ...
  ```
  El YAML de `rules/privacidad/` lista los patrones por defecto, genéricos y en español e inglés, sin nombres de clientes: `documento`, `identificacion`, `cedula`, `nombre`, `apellido`, `telefono`, `celular`, `correo`, `email`, `direccion`, `nacimiento`, `tarjeta`, `cuenta`, `iban`, `ssn`, `phone`, `address`, `birth`. `politica()` lanza `ErrorDeAjustes` con `archivo:línea` si el YAML existe y es inválido.

- [ ] **Step 1: Write the failing tests.** `es_sensible("NUM_DOCUMENTO", politica())` es `True`; `es_sensible("monto", politica())` es `False`; con `incluir={"campo_x"}`: `es_sensible("CAMPO_X", ...)` es `True`; con `excluir={"id_documento_tipo"}`: `es_sensible("ID_DOCUMENTO_TIPO", ...)` es `False` aunque contenga `documento`. `columnas_sensibles(["a","email","monto","Telefono"], politica())` devuelve `["email","Telefono"]` en el orden de entrada. Un YAML con un patrón vacío falla con `columnas-sensibles.yaml:<línea>: patrón vacío`. `tests/unit/test_no_script_specific_names.py` sigue verde con el YAML nuevo.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_privacidad.py -q -p no:cacheprovider`; esperado: no existe el módulo.
- [ ] **Step 3: Implement.** Si `rules/` tiene un validador que recorre todos los YAML (`sgm rules validate`, `src/sgm/rules_validate.py`), comprobar con `uv run python -m sgm.cli rules validate` que el directorio nuevo no lo rompe; si lo rompe, ubicar el YAML en `env/privacidad/` y anotarlo en `PROGRESS.md`.
- [ ] **Step 4: Run test to verify it passes.**
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N n: lista configurable de columnas sensibles`.

---

### Task H-13: El `tLogRow` de cierre enmascara las columnas sensibles (MG-P13-03, parte 2; serie `n`)

`desde_plan.py::_cierres` (línea ~694) agrega un `tLogRow` al final de todo flujo sin salida; ese componente imprime las filas completas al ejecutar el Job. Cuando el flujo tiene columnas sensibles, se antepone un `tJavaRow` que las copia y reemplaza el valor sensible por `"***"`. Las salidas de rechazo del `tMap` (`rejectInnerJoin`, `desde_plan_map.py:686`) que terminan en un `tLogRow` pasan por el mismo cierre.

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\talend_item\desde_plan.py` (solo `_cierres`; el archivo ya pasa de 300 líneas: extraer primero `_cierres` a `desde_plan_cierres.py` en un paso propio, sin cambio de comportamiento)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\talend_item\desde_plan_cierres.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\talend_item\componentes.py` (función nueva junto a `log_row`)
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_cierre_enmascarado.py`

**Interfaces:**
- Consumes: `log_row(unico: str, columnas: list[Columna], x: int = 0, y: int = 0, ruta_java: str = "") -> Nodo` (`componentes.py:83`); `PoliticaPrivacidad` y `columnas_sensibles` (H-12); el componente `tJavaRow` documentado en `docs/referencia/talend/tjavarow.md` (leerlo antes: nombres de los parámetros de código e importaciones y esquema de salida); `java_literals` para escapar `"***"` y `java_identificadores` para validar los nombres de columna.
- Produces:
  ```python
  def java_row_enmascarado(
      unico: str, columnas: list[Columna], sensibles: list[str], x: int = 0, y: int = 0, ruta_java: str = ""
  ) -> Nodo:
      """`tJavaRow` con `output_row.<c> = input_row.<c>;` para cada columna y `output_row.<s> = "***";` para cada sensible; mismo esquema de entrada y de salida. Un nombre no portable lanza ValueError (el cierre lo convierte en pendiente `P-LOG-SENSIBLE-NO-PORTABLE`)."""
  ```
  `_cierres` usa `PoliticaPrivacidad` (por omisión la de `politica()`); si `columnas_sensibles(...)` está vacío, crea exactamente los mismos nodos y conexiones de hoy (los golden no cambian). Si no, crea `nodo -> tJavaRow -> tLogRow` con conexiones `FLOW`.

- [ ] **Step 1: Extraer** `_cierres` a `desde_plan_cierres.py` (sin cambio de comportamiento); `tests/unit/test_golden*.py` y `tests/unit/test_ir_operadores_corpus.py` quedan idénticos.
- [ ] **Step 2: Write the failing tests.** Con columnas `["id", "email", "monto"]`: el cierre contiene un nodo `tJavaRow` cuyo código incluye `output_row.email = "***";` y `output_row.id = input_row.id;` y **no** incluye `output_row.email = input_row.email`; hay conexión `tJavaRow -> tLogRow`. Con columnas `["id", "monto"]`: sin `tJavaRow` (igual que hoy). Con la columna `email` en `politica.excluir`: sin `tJavaRow`. Una columna sensible por `incluir` llamada `x"; System.exit(0); //` lanza `ValueError` y el cierre produce el pendiente `P-LOG-SENSIBLE-NO-PORTABLE` (código agregado a `pendientes.yaml`) sin emitir el Job parcial.
- [ ] **Step 3: Run tests to verify they fail**; esperado: no existe `java_row_enmascarado`.
- [ ] **Step 4: Implement.** Si `tjavarow.md` no documenta el parámetro que se necesita, el paso lo anota y emite `P-LOG-SENSIBLE-SIN-TJAVAROW` en vez de inventar un parámetro. **Lote de Studio (solo si `sgm studio salud` responde):** compilar un Job con `email` sensible con `tools/validar_caso_studio.py`; si no hay Studio, «lote C pendiente».
- [ ] **Step 5: Run** los golden, `test_mg_p13_emitter_security.py`, la suite completa y `uv run ruff check src tests tools`. **Commit** `hito N n: el cierre del Job enmascara columnas sensibles`.

---

### Task H-14: Los informes de `sgm migrar` no copian valores de la muestra (MG-P13-03, parte 3; serie `n`)

`--muestra` entrega archivos de datos para inferir tipos (`esquemas_de_entrada`, `src/sgm/migrar/esquemas.py`). Un mensaje de pendiente que cite un valor de la muestra copiaría datos personales a `pendientes.md`, `cobertura.md` o `migracion.log`.

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\esquemas.py` y/o `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\esquemas_tipos.py` (solo si la prueba encuentra un mensaje que copia un valor)
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_informes_sin_datos.py`

**Interfaces:**
- Consumes: `migrar(source, out, esquemas=None, muestra=None, backend="archivos") -> ResultadoMigrar`.
- Produces: la propiedad «ningún archivo de la salida contiene un valor de la muestra», como prueba. Si hace falta, `sin_valores(mensaje: str, valores: set[str]) -> str` en `esquemas.py`, que sustituya el valor por `<valor omitido>`.

- [ ] **Step 1: Write the failing test.** Programa con `PROC IMPORT DATAFILE='muestra/clientes.csv' OUT=WORK.CLIENTES DBMS=CSV REPLACE; GETNAMES=YES; RUN;` y un `clientes.csv` de muestra con valores inventados distinguibles (`ZZ-DATO-17`, `ana.prueba@example.invalid`, una fecha `31/02/2020` inválida, una columna numérica con el texto `n/d`). Se migra con `--muestra` y se recorre **cada** archivo de la salida (`rglob`, decodificado con `errors="replace"`): ninguno contiene `ZZ-DATO-17`, `ana.prueba@example.invalid` ni `n/d` como valor citado. Repetir sin `--muestra`.
- [ ] **Step 2: Run test.** Si pasa, la propiedad ya se cumple: dejar la prueba como protección y anotarlo en `PROGRESS.md` (no hay código que cambiar). Si falla, el mensaje del `assert` nombra el archivo y el valor.
- [ ] **Step 3: Implement** solo si falló: sustituir los valores citados por `<valor omitido>` en el origen del mensaje y conservar el nombre de columna y el tipo inferido.
- [ ] **Step 4: Run test to verify it passes**, más `tests/unit/test_cli_migrar.py`.
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N n: prueba de que los informes no copian valores de la muestra`.

---

### Task H-15: Valores hostiles dentro de literales SQL y Java (MG-P13-05 residual; serie `n`)

El hito 135 bloqueó identificadores y nombres hostiles. Falta el barrido sobre **valores**: cadenas del SAS con comillas, `--`, `;`, `\`, `*/` o saltos de línea que acaban dentro de un `exec_sql` empujado a la base o dentro de una expresión Java de `tMap`.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_mg_h_literales_hostiles.py`
- Modify (solo si el barrido encuentra un fallo): `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\java_literals.py`, `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\ir\sql_render.py`

**Interfaces:**
- Consumes: la función de `java_literals.py` que escapa un literal Java (leer su nombre real con `Grep "^def " src/sgm/java_literals.py`); la función pública de `ir/sql_render.py` que produce el SQL empujado (`Grep "^def " src/sgm/ir/sql_render.py`); `sqlglot.parse_one` para volver a leer el SQL emitido.
- Produces: una lista `HOSTILES` de 12 valores en el archivo de prueba y dos propiedades: (1) el SQL emitido, vuelto a analizar con `sqlglot`, contiene **un solo** literal cuyo valor es el original y ninguna sentencia adicional; (2) la expresión Java emitida tiene las comillas balanceadas, sin `*/` ni `\u` sin escapar fuera del literal y sin salto de línea dentro de la cadena.

- [ ] **Step 1: Write the failing tests.** `HOSTILES` = `["a'b", "x'; DROP TABLE t; --", "a\\b", "a\\'b", "fin\\", "a*/b", "a\nb", "a\r\nb", "\\u0022; System.exit(1); //", "%", "a\"b", "a--b"]`. Para cada uno: un programa con `PROC SQL; CREATE TABLE WORK.t AS SELECT * FROM WORK.a WHERE col = '<valor escrito como lo exige SAS, con la comilla duplicada>'; QUIT;` llevado hasta el SQL empujado y hasta la expresión del `tMap` (usar el mismo camino que `tests/unit/test_mg_p13_sql_emitter_security.py`; copiar su forma de armar el plan) y las dos propiedades de arriba.
- [ ] **Step 2: Run tests.** `uv run python -m pytest tests/unit/test_mg_h_literales_hostiles.py -q -p no:cacheprovider`. Los que fallen son hallazgos: anotar cada uno en `PROGRESS.md`.
- [ ] **Step 3: Implement** el arreglo mínimo de cada hallazgo (escapar la barra invertida antes que la comilla; sustituir `\r` y `\n` por sus escapes; rechazar con `P-ESQUEMA-NO-PORTABLE` o `SQL_NO_SOPORTADO` lo que no se pueda representar, nunca emitir un literal que cambie de sentido). Un valor que no se pueda escapar de forma demostrada queda como pendiente con motivo, no como valor supuesto.
- [ ] **Step 4: Run test to verify it passes**, más `tests/unit/test_mg_p13_emitter_security.py`, `test_mg_p13_sql_emitter_security.py` y `test_mg_p13_context_emitter_security.py`.
- [ ] **Step 5: Run** la suite completa y `uv run ruff check src tests tools`. **Commit** `hito N n: barrido de valores hostiles en literales SQL y Java`.

---

## Parte III. MG-P12 restante: caché y volumen (serie `n`, 22 h)

### Task H-16: Caché por programa para `sgm migrar` (MG-P12-04, parte 1; serie `n`)

`src/sgm/cache.py` (64 líneas) guarda salidas en `out/.cache/<clave>/` y la usa solo el comando antiguo de `cli.py` (`cache.project_key`, `cache.restore`, `cache.save`, líneas 102 a 124); `sgm migrar` no la usa y migrar una carpeta de 189 programas tarda 10,9 s (hito 133). La caché nueva es por programa: la clave cubre todo lo que cambia el paquete y la restauración vuelve a pasar por la compuerta de secretos. `cache.py` no se modifica.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\cache_paquete.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\escritura_paquete.py` (creado en H-5; el paso de publicación elige entre generar y restaurar)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\cli_migrar.py` (`migrar` recibe `cache: Path | None`; `ResultadoMigrar` gana `total_jobs: int` y `desde_cache: bool`)
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_cache_paquete.py`

**Interfaces:**
- Consumes: `rules_hash() -> str` de `src/sgm/cache.py` (huella de `rules/`, `env/` y la versión); `publicar_con_revision(carpeta_final, generar)` de `seguridad/compuerta_migracion.py` (devuelve `ResultadoCompuerta` con `publicado`, `hallazgos`, `motivo`, `archivos`); `ResultadoMigrar` (`carpeta`, `escritos`, `pendientes`, `lee`, `escribe`).
- Produces:
  ```python
  def clave_de_programa(
      texto: str, esquemas: Path | None, muestra: Path | None, backend: str,
      ajustes: Path | None, politica_privacidad: tuple[str, ...], huella_reglas: str,
  ) -> str:
      """sha256 hexadecimal de: huella de reglas, backend, texto del programa, cada archivo de
      `esquemas` y `muestra` (ruta relativa + bytes, en orden), bytes del YAML de ajustes y la
      política de privacidad. Cualquier cambio cambia la clave."""

  @dataclass(frozen=True)
  class ResumenCache:
      total_jobs: int
      pendientes: tuple[tuple[str, str, int | None], ...]   # (código, mensaje, línea)
      lee: tuple[str, ...]
      escribe: tuple[str, ...]

  def guardar(cache: Path, clave: str, paquete: Path, escritos: list[Path], resumen: ResumenCache) -> None:
      """Copia los archivos escritos a `<cache>/<clave>/paquete/` y el resumen a `resumen.json`. Se llama solo con un paquete ya publicado por la compuerta, nunca con uno bloqueado."""
  def restaurar(cache: Path, clave: str, destino: Path) -> ResumenCache | None:
      """Copia `paquete/` a `destino` (un staging) y devuelve el resumen; `None` si no hay entrada o está incompleta."""
  ```
  Solo se usa con `backend == "archivos"` (el backend `talend` escribe en Studio y no se cachea). La huella de reglas se calcula una vez por proceso (`functools.cache` en este módulo, con `limpiar_huella()` para las pruebas): en una carpeta de 189 programas no se relee `rules/` 189 veces.

- [ ] **Step 1: Write the failing tests.** (a) Misma entrada: `clave_de_programa(...)` dos veces es igual; cambiar un carácter del texto, un byte de un esquema, el backend, el YAML de ajustes o `huella_reglas` cambia la clave. (b) Migrar `tests/corpus/L2/l2_01*/programa.sas` con `cache=tmp/.sgm-cache` dos veces: la segunda tiene `desde_cache is True`, `total_jobs` igual a la primera y **todos** los bytes de la carpeta de salida iguales (`sorted(rglob)` y `read_bytes`). (c) Una entrada de caché con `resumen.json` ausente devuelve `None` y la migración se rehace (sin excepción). (d) **La compuerta no se salta:** se edita a mano un archivo de `.sgm-cache/<clave>/paquete/` poniéndole `PASSWORD='clave-de-prueba-1'`; la corrida siguiente sale con paquete no publicado, `hallazgos_seguridad` no vacío y la clave de prueba no aparece en la carpeta de salida. (e) Un paquete bloqueado por la compuerta no crea entrada en la caché. (f) Cambiar `huella_reglas` con `monkeypatch` hace una corrida nueva (miss).
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_cache_paquete.py -q -p no:cacheprovider`; esperado: no existe el módulo.
- [ ] **Step 3: Implement** `cache_paquete.py` y la integración: en `migrar`, si `cache` no es `None` y `backend == "archivos"`, calcular la clave antes de analizar; si hay entrada, `generar` copia `paquete/` al staging y la compuerta lo revisa como a cualquier paquete; si no, se migra como hoy y, al publicar, se guarda. `total_jobs` se llena en las dos rutas y el CLI y `proyecto.py` (H-7) lo usan en lugar de `len(resultado.jobs)`.
- [ ] **Step 4: Run tests to verify they pass**, más `tests/unit/test_cli_migrar.py` y `tests/unit/test_golden*.py` (sin cambios con `cache=None`).
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N n: cache por programa para sgm migrar, con la compuerta de secretos en la restauracion`.

---

### Task H-17: La caché en la CLI y la segunda corrida medida (MG-P12-04, parte 2; serie `n`)

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\cli_migrar_comando.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\.gitignore` (línea `.sgm-cache/`, si no está ya cubierta por una regla existente: `Grep "sgm-cache" .gitignore`)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\performance\migrar.py`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_cli_migrar_cache.py`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_performance_benchmark.py` (existente: se amplía)

**Interfaces:**
- Consumes: `migrar(..., cache=...)` (H-16); `run_benchmarks(project_root: Path, report_path: Path) -> dict[str, Any]` y `meets_limits(...)` de `tools/performance/migrar.py` (líneas 104 y 55; la forma exacta de los diccionarios por escenario y las claves de `metrics/performance/mg-p12-01.json` se leen del archivo antes de escribir la comparación); `measure_command(` de `tools/performance/medicion.py:82` (leer su firma).
- Produces:
  ```python
  # sgm migrar: opciones nuevas
  #   --sin-cache            no lee ni escribe `<out>/.sgm-cache/`
  #   salida de carpeta: `N programa(s) ... (K desde caché)`
  # tools/performance/migrar.py
  def comparar_corridas(primera: dict, segunda: dict, minimo_aceleracion: float = 2.0) -> dict:
      """{"aceleracion": primera_s / segunda_s, "misma_salida": bool, "cumple": aceleracion >= minimo}"""
  def regresion(base: dict, actual: dict, margen: float = 0.5) -> list[str]:
      """Mensajes de los escenarios cuyo tiempo o pico de memoria supera `base * (1 + margen)`; lista vacía si no hay regresión."""
  ```
  La caché vive en `<out>/.sgm-cache/` por omisión (la carpeta de salida es la del usuario; `_sas_programs` ya excluye la salida anidada).

- [ ] **Step 1: Write the failing tests.** `CliRunner` sobre una carpeta de dos programas: la primera corrida imprime `(0 desde caché)`, la segunda `(2 desde caché)` y deja los mismos bytes; con `--sin-cache` imprime `(0 desde caché)` y no crea `.sgm-cache/`. `comparar_corridas({"segundos": 10.0}, {"segundos": 2.0})["aceleracion"] == 5.0` y `cumple` es `True`; con `{"segundos": 10.0}` y `{"segundos": 9.0}` `cumple` es `False`. `regresion({"s": 10.0}, {"s": 16.0}, margen=0.5)` devuelve un mensaje; con 14,0 devuelve `[]` (usar las claves reales del JSON de base al escribir el test).
- [ ] **Step 2: Run tests to verify they fail**; esperado: `No such option: --sin-cache`.
- [ ] **Step 3: Implement** la opción y el recuento «desde caché». En `run_benchmarks` agregar el escenario `carpeta-segunda-corrida` (mismo árbol temporal, segunda invocación sobre la misma salida) y su comparación; **no** se reescribe `metrics/performance/mg-p12-01.json` (es la base del hito 133): el resultado nuevo va a `metrics/performance/mg-p12-04.json`.
- [ ] **Step 4: Medir.** `uv run python tools/performance/migrar.py` (solo esta máquina; tarda unos 30 s por escenario) y pegar en `PROGRESS.md`: tiempo de la primera y la segunda corrida de la carpeta de 189 programas, aceleración (aceptación del plan maestro: segunda corrida más rápida con la misma salida; el mínimo de `comparar_corridas` es 2,0) y comparación con la base del hito 133 (6,848 s y 93,9 MB para el programa grande; 10,860 s y 81,7 MB para la carpeta; límites 120 s y 1 GB).
- [ ] **Step 5: Run** `uv run python -m pytest tests/unit/test_performance_benchmark.py tests/unit/test_cli_migrar_cache.py -q -p no:cacheprovider`, la suite completa y `uv run ruff check src tests tools`. **Commit** `hito N n: cache visible en la CLI y segunda corrida medida`.

---

### Task H-18: Banco de volumen: datos sintéticos, escenarios y corredor en contenedor (MG-P12-02, parte 1; serie `n`)

El plan maestro pide 5 a 50 millones de filas en contenedor. Esta tarea deja el banco listo y probado sin Docker ni Studio; H-20 lo corre. `tools/contenedores/` ya tiene `postgres/` e `impala/` con `docker-compose.yml`; el banco de volumen no los usa (los Jobs leen y escriben archivos).

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\performance\volumen_datos.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\performance\volumen_escenarios.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\performance\volumen_contenedor.py`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_volumen_banco.py`

**Interfaces:**
- Consumes: `migrar(source, out, esquemas=None, muestra=None, backend="archivos") -> ResultadoMigrar` (`cli_migrar.py:271`); `measure_command(` de `tools/performance/medicion.py:82` solo como referencia de formato del reporte (mide el árbol de procesos del anfitrión, no el contenedor: el pico del contenedor sale de `docker stats`).
- Produces:
  ```python
  # volumen_datos.py
  def generar_tabla(destino: Path, filas: int, semilla: int = 0, llaves: int = 1000) -> Path:
      """CSV `id,llave,monto,fecha,texto` determinista (`random.Random(semilla)`), escrito en bloques de 100 000 filas; memoria constante."""
  def generar_dimension(destino: Path, llaves: int, semilla: int = 0) -> Path:
      """CSV `llave,descripcion` con `llaves` filas, una por llave."""
  # volumen_escenarios.py
  @dataclass(frozen=True)
  class Escenario:
      nombre: str            # "lookup-pequeno", "lookup-grande", "orden-total", "ramas-paralelas", "tmap-memoria"
      que_mide: str
      filas: tuple[int, ...] # (5_000_000, 20_000_000, 50_000_000)
      llaves_dimension: int
      def programa_sas(self, datos: Path, salida: Path) -> str: ...
  ESCENARIOS: dict[str, Escenario]
  # volumen_contenedor.py
  def armar_comando(
      imagen: str, directorio_job: Path, datos: Path, memoria_limite: str, jvm: list[str], lanzador: str
  ) -> list[str]:
      """argv de `docker run --rm --memory <límite> -v <job>:/job:ro -v <datos>:/datos <imagen> ...`; sin shell, sin interpolar rutas en una cadena."""
  def sondear_memoria(contenedor: str, intervalo_s: float = 1.0) -> Iterator[int]:
      """Bytes de `docker stats --no-stream --format {{.MemUsage}}`, uno por intervalo."""
  def correr(escenario: Escenario, filas: int, job: Path, jvm: list[str], memoria_limite: str) -> dict:
      """{"escenario", "filas", "segundos", "pico_memoria_bytes", "codigo", "filas_salida", "jvm", "limite_contenedor"}"""
  ```
  Los cinco escenarios: `lookup-pequeno` (unión izquierda con una dimensión de 1 000 llaves: `tMap` con `LOOKUP` en memoria); `lookup-grande` (dimensión de 5 000 000 llaves: límite de memoria del lookup y prueba de H-19); `orden-total` (`PROC SORT` sobre toda la tabla: `tSortRow`); `ramas-paralelas` (dos agregaciones independientes sobre la misma lectura: `tReplicate` y ramas); `tmap-memoria` (filtro y columnas derivadas en un solo `tMap`, sin lookups). La imagen del contenedor es una imagen de Java con la versión que exige Studio 8.0.1 (verificar al ejecutar en `docs/referencia/talend/studio-guia-jobs-contextos.md`; la imagen se pasa por parámetro, no se fija en el código).

- [ ] **Step 1: Write the failing tests.** `generar_tabla(tmp/"t.csv", 1000, semilla=3)` produce 1 001 líneas (con encabezado), dos llamadas con la misma semilla dan los mismos bytes y una semilla distinta da otros; con `tracemalloc`, generar 250 000 filas tiene un pico menor de 30 MB. `generar_dimension(..., llaves=1000)` tiene 1 001 líneas y cada llave de `generar_tabla(..., llaves=1000)` existe en la dimensión. **Cada escenario se traduce completo:** `migrar` del `programa_sas` de cada uno (con `datos` y `salida` de `tmp_path`) deja `total_jobs >= 1` y ningún pendiente (`resultado.pendientes == []`); si una construcción aún no se traduce (por ejemplo `PROC SORT`), la prueba se marca `xfail(strict=True)` con el código del pendiente en el motivo, nunca se quita el escenario. `armar_comando(...)` devuelve una lista de cadenas que contiene `--memory`, `8g`, `-Xmx` cuando se pasó en `jvm`, y cada ruta va en su propio argumento (sin armar una cadena de shell).
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_volumen_banco.py -q -p no:cacheprovider`; esperado: no existen los módulos.
- [ ] **Step 3: Implement** los tres módulos (biblioteca estándar; `subprocess.run` con lista de argumentos y `shell=False`). `correr` mide el tiempo de pared con `time.perf_counter()` y la memoria con `sondear_memoria` en un hilo; si `docker version` falla lanza `RuntimeError("docker no disponible")`, que H-20 convierte en «lote de volumen pendiente».
- [ ] **Step 4: Run test to verify it passes**; comprobar con `Grep "cod1\|cod2\|exogena" tools/performance/` que no hay nombres de scripts del cliente.
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N n: banco de volumen con datos sinteticos, cinco escenarios y corredor en contenedor`.

---

### Task H-19: Opciones de volumen en el emisor: lookups en disco y tamaño de búfer (MG-P12-02, parte 2; serie `n`)

Un lookup de millones de filas no cabe en la memoria de la JVM por omisión. `docs/referencia/talend/tmap.md` documenta tres opciones: el modelo **Load once** con **Store temp data** (los registros del lookup se guardan en un archivo local en lugar de en memoria, línea 412), el **Temp data directory path** (línea 458) y el **Max buffer size (nb of rows)** (línea 465). Ninguna se emite hoy. Para `tSortRow`, `docs/referencia/talend/tsortrow.md` solo documenta el panel de criterios: **no** se emite orden externo; ver el paso 4.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\talend_item\opciones_volumen.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\ajustes.py` (la clave `volumen`, ya reservada en el esquema de H-4)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\talend_item\desde_plan_map.py` (815 líneas: extraer primero a `desde_plan_map_lookups.py` el bloque que arma los parámetros del lookup, paso propio sin cambio de comportamiento) y, si hace falta, `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\talend_item\tmap.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\talend_item\desde_plan_map_lookups.py`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_opciones_volumen.py`

**Interfaces:**
- Consumes: `Ajustes.volumen: dict[str, int]` (tabla -> filas estimadas; enteros positivos, error `ajustes.yaml:<línea>: se esperaba un entero mayor que cero`); los nombres de los parámetros del `tMap` y del lookup tal como los escribe `tmap.py` (leer con `Grep "LOOKUP\|MATCHING\|TEMP\|BUFFER" src/sgm/talend_item/tmap.py rules/talend/components.json`; el nombre exacto de cada parámetro XML se toma de `rules/talend/components.json`, no de la interfaz gráfica).
- Produces:
  ```python
  UMBRAL_LOOKUP_EN_DISCO = 5_000_000   # filas; provisional hasta que H-20 lo mida

  @dataclass(frozen=True)
  class OpcionesLookup:
      guardar_en_disco: bool
      directorio_temporal: str | None   # parámetro de contexto, nunca una ruta fija
      filas_en_memoria: int | None      # "Max buffer size (nb of rows)"

  def opciones_de_lookup(filas_estimadas: int | None, umbral: int = UMBRAL_LOOKUP_EN_DISCO) -> OpcionesLookup:
      """Sin estimación o por debajo del umbral: `OpcionesLookup(False, None, None)` (el Job idéntico al de hoy). Con `filas_estimadas >= umbral`: `guardar_en_disco=True`, `directorio_temporal="context.ruta_temporal"` y `filas_en_memoria=1_000_000`."""
  ```
  Con el disco en uso se agrega `ruta_temporal` al grupo de contexto (queda en `contextos/*.yaml` y en `configuracion-pendiente.md` como variable por llenar, sin valor por omisión). Sin `volumen` en los ajustes el Job es byte a byte el de hoy.

- [ ] **Step 1: Extraer** el bloque de parámetros del lookup de `desde_plan_map.py` a `desde_plan_map_lookups.py` (sin cambio de comportamiento); `tests/unit/test_golden*.py`, `test_ir_operadores_corpus.py` y `tests/unit/test_desde_plan*.py` quedan idénticos.
- [ ] **Step 2: Write the failing tests.** `opciones_de_lookup(None) == OpcionesLookup(False, None, None)`; `opciones_de_lookup(4_999_999)` igual; `opciones_de_lookup(5_000_000)` es `OpcionesLookup(True, "context.ruta_temporal", 1_000_000)`. Un programa con `LEFT JOIN` a `dw.maestro` migrado con `ajustes` `volumen: {dw.maestro: 6000000}`: el `.item` del `tMap` tiene los parámetros de almacenamiento temporal en `true` y `contextos/*.yaml` tiene `ruta_temporal` vacío; con `volumen: {dw.maestro: 100}` el `.item` es idéntico al de la corrida sin ajustes. `volumen: {dw.maestro: -1}` falla con error de archivo y línea.
- [ ] **Step 3: Run tests to verify they fail**; esperado: no existe `opciones_volumen`.
- [ ] **Step 4: Implement.** Emitir solo los parámetros que `docs/referencia/talend/tmap.md` y `rules/talend/components.json` nombran; donde la página no diga el nombre del parámetro XML, el paso queda como `P-VOLUMEN-LOOKUP-SIN-PARAMETRO` (agregar a `rules/mensajes/pendientes.yaml`) y no se inventa. **Orden externo:** si `docs/referencia/talend/catalogo/tsortrow.md` no documenta una opción de orden en disco (al redactar este plan, `Grep -i "disk\|externa\|temp" docs/referencia/talend/tsortrow.md` solo encuentra el panel de criterios), no se emite: el límite de `tSortRow` en memoria se mide en H-20 y se documenta como límite, y la sugerencia de `docs/volumen-limites.md` es dividir la tabla antes de ordenarla.
- [ ] **Step 5: Run** los tests del paso 2, la suite completa y `uv run ruff check src tests tools`. **Commit** `hito N n: opciones de volumen del tMap (lookup en disco) por ajuste explicito`.

---

### Task H-20: Plantillas de JVM, lote de volumen en contenedor y límites documentados (MG-P12-02, parte 3, y MG-P12-03; serie `n`)

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\talend_item\jvm.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\rendimiento_md.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\escritura_paquete.py` (escribe `rendimiento.md` en el paquete)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\docs\volumen-jvm.md`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\docs\volumen-limites.md`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\metrics\performance\mg-p12-02.json`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_jvm.py`

**Interfaces:**
- Consumes: `ESCENARIOS` y `correr(escenario, filas, job, jvm, memoria_limite) -> dict` (H-18); `opciones_de_lookup(...)` (H-19); `Job` y `Nodo.componente` (`talend_item/modelo.py`) para contar `tMap` con lookup y `tSortRow` por Job; `escritura.py` (`fecha_studio`).
- Produces:
  ```python
  @dataclass(frozen=True)
  class PerfilJvm:
      nombre: str            # "pequeno", "mediano", "grande"
      filas_hasta: int | None
      xms: str               # "256M"
      xmx: str               # "1G"
      medido: bool           # True solo si sale de mg-p12-02.json
  def perfiles(medicion: dict | None = None) -> tuple[PerfilJvm, PerfilJvm, PerfilJvm]:
      """Sin `medicion`: tres perfiles con `medido=False` (`pequeno` -Xms256M -Xmx1G hasta 5 000 000 filas; `mediano` -Xms1G -Xmx4G hasta 20 000 000; `grande` -Xms2G -Xmx8G hasta 50 000 000). Con la medición de H-20, `xmx` pasa a ser el menor tamaño con el que el escenario más pesado de ese tramo terminó con código 0 y `medido=True`."""
  def argumentos(perfil: PerfilJvm) -> list[str]: ...   # ["-Xms1G", "-Xmx4G"]
  # rendimiento_md.py
  def rendimiento_md(programa: str, jobs: list[Job]) -> str:
      """`rendimiento.md` del paquete: tabla de perfiles (con la marca `sin medir` mientras `medido` sea False), y por Job cuántos `tMap` con lookup y cuántos `tSortRow` tiene, que son los dos puntos donde la memoria manda."""
  ```
  Los valores provisionales de la tabla son un punto de partida declarado como tal; no se presentan como medidos hasta que la corrida de este paso los confirme.

- [ ] **Step 1: Write the failing tests.** `argumentos(perfiles()[1]) == ["-Xms1G", "-Xmx4G"]`; los tres perfiles tienen `medido == False` sin medición; con una medición mínima `{"resultados": [{"escenario": "orden-total", "filas": 20000000, "limite_contenedor": "4g", "jvm": ["-Xmx3G"], "codigo": 0}]}` el perfil `mediano` pasa a `medido=True` y `xmx == "3G"`; un resultado con `codigo != 0` no baja el `xmx`. `rendimiento_md("p", jobs)` es determinista, contiene la marca `sin medir` mientras no haya medición, y cuenta un `tSortRow` y dos `tMap` con lookup de un Job de prueba. El paquete de `sgm migrar` incluye `rendimiento.md`.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_jvm.py -q -p no:cacheprovider`; esperado: no existe `jvm`.
- [ ] **Step 3: Implement** `jvm.py` y `rendimiento_md.py`; el parámetro del `.item` que lleva los argumentos de JVM (en Talend, los argumentos de la máquina virtual del Job) se busca con `Grep -ri "VM_ARGUMENTS" tools/contenedores/talend_plantillas docs/referencia/talend/studio-guia-jobs-contextos.md`: si una página o plantilla real lo documenta, `argumentos` se escribe también en el `.item`; si no, solo queda en `rendimiento.md` y en `docs/volumen-jvm.md` (instrucción para el lanzador), y se anota en `PROGRESS.md` que el `.item` no lleva JVM. Nunca se inventa el nombre del parámetro. Escribir `docs/volumen-jvm.md` con la tabla de perfiles, la relación entre `-Xmx` y el límite del contenedor (el límite debe ser al menos `-Xmx` más 512 MB de margen de la JVM), `ruta_temporal` de H-19 y la sección «qué hacer si el Job muere por memoria».
- [ ] **Step 4: Lote de volumen (solo con Docker; si `docker version` falla, escribir «lote de volumen pendiente: docker no disponible» en `PROGRESS.md` y en `docs/volumen-limites.md`, y no contar esta parte).** Para cada escenario de `ESCENARIOS` y cada tamaño de `Escenario.filas`: migrar el `programa_sas` con `sgm migrar`, compilar el Job con el backend `talend` solo si `sgm studio salud` responde (`src/sgm/backend_talend/`; si no responde, «lote de volumen pendiente: Studio no responde» y se anota qué escenarios quedaron sin Job), generar los datos con `generar_tabla` y correr `correr(...)` con el perfil que corresponda y un límite de contenedor de `-Xmx` más 512 MB. Escribir `metrics/performance/mg-p12-02.json` con el resultado por escenario y tamaño (sin rutas personales ni nombres de equipo). Los datos generados no se versionan.
- [ ] **Step 5: Documentar los límites.** `docs/volumen-limites.md` afirma solo lo que el JSON midió: por escenario y tamaño, tiempo, pico de memoria y si terminó; el tamaño a partir del cual `lookup-grande` y `orden-total` fallan con el perfil `mediano` (si fallan), el umbral que conviene para `UMBRAL_LOOKUP_EN_DISCO` (se actualiza la constante de H-19 con el valor medido, con su prueba) y las condiciones (CPU y memoria del anfitrión, versión de Java de la imagen, versión de Studio). Lo que no se midió se rotula `sin medir`.
- [ ] **Step 6: Run** `uv run python tools/generar_documentacion.py --check` (si H-10 ya está integrada; la guía de operación remite a `docs/volumen-jvm.md`), la suite completa y `uv run ruff check src tests tools`. **Commit** `hito N n: plantillas de JVM, lote de volumen en contenedor y limites documentados` (si el lote quedó pendiente, el mensaje lo dice: `... (lote de volumen pendiente)`).

---

## Parte IV. Personas y cierre

### Task H-21: Lista de verificación de persona: secretos del fixture viejo y de la copia externa (MG-P13-02; sin crédito de agente)

**Ningún agente ejecuta esta tarea ni abre los archivos que nombra.** Es una lista para una persona con acceso, con una sola salida: el estado de cada punto escrito en `PROGRESS.md`. Mide 0,5 día-persona.

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\PROGRESS.md` (una entrada `## Hito N n. MG-P13-02: secretos revisados por una persona`)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\docs\plan-reescritura\plan-migrador-general.md` (fila MG-P13-02 y sección 11b)

**Interfaces:**
- Consumes: `tests/fixtures/sas/real/ci360-download-client/macros/dsc_download.sas` (el valor `{SAS002}` en la línea 55, según el plan maestro); la copia externa del programa real grande, con una contraseña en claro hallada el 11 de noviembre de 2026 en su línea de `proc pwencode`; `uv run python -m sgm.cli secretos tests/fixtures`.
- Produces: tres casillas con fecha, nombre de quien las cerró y la decisión.

- [ ] **Punto 1: el `{SAS002}` del fixture viejo.** La persona confirma con el dueño del repositorio de origen si el valor es público (publicado en el repositorio abierto de la herramienta de terceros) o es un secreto del cliente. Si es público: anotar la URL y la fecha de la confirmación y dejarlo en la lista blanca (`src/sgm/seguridad/lista_blanca.py`, con su comentario de origen). Si es privado o no se puede confirmar: **rotarlo** en el sistema de origen, sustituir el valor del fixture por `'***'` en un commit propio y ejecutar `uv run python -m sgm.cli secretos tests/fixtures` (debe salir con código 0).
- [ ] **Punto 2: la contraseña en claro de la copia externa del programa real grande.** La persona rota esa contraseña en el sistema al que pertenece, borra o corrige la copia externa (el repositorio ya la tiene como `'***'`) y registra la fecha. **No se copia el valor a ningún archivo, mensaje ni commit.** Si la contraseña se pudo haber enviado por correo o chat, la rotación vale también para esas copias.
- [ ] **Punto 3: la licencia del propio SGM.** Una persona con autoridad decide la licencia de `sgm` (el SBOM del hito 136 la deja como `NOASSERTION` porque `pyproject.toml` no la declara) y la anota en `PROGRESS.md`; el cambio de `pyproject.toml` y la regeneración con `uv run python tools/seguridad/generar_sbom.py` los hace un agente en un hito posterior.
- [ ] **Punto 4: registrar.** Escribir en `PROGRESS.md` los tres estados (`confirmado público`, `rotado`, `pendiente`) con fecha y responsable, sin los valores. **Commit** `hito N n: secretos revisados por una persona (MG-P13-02)` solo con ese texto.

---

### Task H-Gate: Compuerta GM6 y criterios C2, C4 y C6 (serie `n`)

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\PROGRESS.md`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\docs\plan-reescritura\plan-migrador-general.md` (estado de MG-P11, MG-P12 y MG-P13, sección 11b con las horas acreditadas y el porcentaje recalculado con el método de la propia 11b)

**Interfaces:**
- Consumes: todo lo de H-1 a H-20; `tools/robustez_migrar.py` (Plan G, G-15; `entradas_basura(semilla)`); `tools/corrida_nocturna.py` (Plan G, G-18, si ya está integrada); `tools/seguridad/generar_sbom.py --check`; `tools/generar_documentacion.py --check` (H-10).
- Produces: la entrada de `PROGRESS.md` con la evidencia.

1. **GM6, `sgm migrar` con documentación, mensajes y rendimiento.**
   - [ ] Suite completa `uv run python -m pytest -q` y `uv run ruff check src tests tools` en verde; `uv run python -m sgm.cli rules validate` válido.
   - [ ] Documentación: `uv run python tools/generar_documentacion.py --check` con código 0; los tres documentos existen y cada opción de `sgm migrar` y cada código de pendiente aparece en la guía de usuario.
   - [ ] Mensajes: `tests/unit/test_codigos_pendiente.py` en verde (cada código del código fuente tiene texto y sugerencia).
   - [ ] Rendimiento: `uv run python tools/performance/migrar.py` con las dos metas del plan maestro (menos de 120 s y menos de 1 GB en `client_large.sas` y en la carpeta de 189), sin regresión de más del 50 % frente a `metrics/performance/mg-p12-01.json` (`regresion(...)` vacía), y la segunda corrida con caché más rápida con la misma salida (`mg-p12-04.json`).
   - [ ] Una carpeta de 5 programas migra a un proyecto coherente (`tests/unit/test_migrar_proyecto.py` en verde): `proyecto.md` con el orden y los ciclos.
2. **C2, traducción completa o explícita y sin fallos.**
   - [ ] La decisión de código de salida está escrita en `docs/secretos.md` y en la fila C2 del plan maestro, con `tests/unit/test_codigos_de_salida_migrar.py` en verde.
   - [ ] Si el Plan G ya está integrado, correr `uv run python tools/robustez_migrar.py` y comprobar que cuenta el código 1 por secreto como `bloqueado_por_secreto` y no como fallo; si no, anotar «C2 (robustez) depende del Plan G» sin marcarlo cumplido.
3. **C4, calidad de los Jobs (los puntos de este plan).**
   - [ ] Sin secretos: `uv run python -m sgm.cli secretos <out de un lote de prueba>` con código 0, y las pruebas de H-11 y la de H-16 (d) en verde.
   - [ ] Registro sin datos personales: `tests/unit/test_cierre_enmascarado.py` y `test_informes_sin_datos.py` en verde; **lote de Studio** del Job con columna sensible solo si `sgm studio salud` responde; si no, «lote C pendiente» con su motivo.
   - [ ] Nada fijo en el código: `ruta_temporal` y los valores de `ajustes.contexto` salen en `contextos/`, no en el `.item`.
4. **C6, operable (los puntos de este plan).**
   - [ ] CLI estable: los comandos `migrar`, `explicar`, `comparar` y `secretos` documentados con sus códigos de salida 0, 1 y 2, y la guía de operación generada. El paquete instalable en una máquina limpia y el registro de cambios son de MG-P14-01 (Plan I): no se marca C6 como cumplido aquí; se anota «C6 parcial: CLI y guía; falta empaquetado (MG-P14-01)».
5. **Cierre.**
   - [ ] `uv run python tools/seguridad/generar_sbom.py --check` con código 0 (el SBOM sigue al día con `uv.lock`).
   - [ ] `PROGRESS.md`: entrada del hito con la serie `n`, pruebas, mediciones de H-17 y H-20, lotes pendientes con su motivo, y decisiones (código de salida, caché por programa, perfiles de JVM provisionales o medidos, no emisión de orden externo por falta de página).
   - [ ] Plan maestro: horas acreditadas de MG-P11 (hasta 30), MG-P12 (hasta 30; si el lote de volumen quedó pendiente, solo las horas de H-16, H-17, H-18, H-19 y la parte de H-20 que no dependía del contenedor) y MG-P13 (3 h de P13-03 más las que ya tenía; P13-02 queda «en espera de persona» hasta que H-21 se cierre). Recalcular el porcentaje con el método de la sección 11b. **Commit** `hito N n: GM6 cerrada con evidencia (C2, C4 y C6 parciales anotados)`.

---

## Dependencias

| Este plan | Depende de | Qué pasa si no está |
|---|---|---|
| H-2 (registro de códigos) | Los planes B, C, D1, D2, E, F1, F2, G y K agregan códigos `P-xxx` | La prueba de barrido de H-2 falla en cuanto otro plan mete un código sin texto. Cada tarea de esos planes que agregue un código debe sumar su entrada a `rules/mensajes/pendientes.yaml` en el mismo commit; hasta que H-2 se integre, el que llegue primero deja la nota en su `PROGRESS.md` |
| H-5 (`agrupacion` en ajustes) | Plan F2 (padre, hijos y joblets) | `agrupacion` se valida pero no se aplica (`P-AJUSTE-AGRUPACION-PENDIENTE`); se conecta en un hito posterior cuando F2 publique su interfaz |
| H-5, H-6 y H-16 tocan `cli_migrar.py` | Planes B y C (extraen bloques de `interprete.py`, no de `cli_migrar.py`) y Plan G (G-15 lee `ResultadoMigrar`) | Sin conflicto de archivo; si G ya se integró, sus campos usados (`carpeta`, `escritos`, `hallazgos_seguridad`, `fallo_seguridad`) no cambian |
| H-7 (`proyecto.md`) | Plan F2 (proyecto coherente con padre, joblets y contextos compartidos) | `proyecto.md` solo ordena por tablas permanentes; el padre y los joblets son de F2 |
| H-9 (`comparar`) | Plan G (equivalencia de datos en `tools/`) | Sin conflicto: H-9 solo agrega una opción a `verify.comparar_command` |
| H-11 (corrida nocturna) | Plan G, G-18 (`tools/corrida_nocturna.py`) | El paso 5 de H-11 lo detecta y anota «pendiente de integración»; el workflow `.github/workflows/seguridad-nocturna.yml` del hito 134 cubre mientras tanto |
| H-13 (lote de Studio) y H-20 (lote de volumen) | Plan A (Studio y `talend-mcp` fiables) | Esas partes quedan con «lote pendiente» y su motivo; el resto de las tareas no depende de Studio |
| H-18 (escenarios) | Plan C (`PROC SORT` en `tSortRow`) y Plan F1 (`tReplicate` y ramas) | Un escenario que aún no se traduce queda `xfail(strict=True)` con su código de pendiente; no se quita |
| H-20 (JVM en `.item`) | Plantillas reales de Studio en `tools/contenedores/talend_plantillas/` | Si ninguna documenta el parámetro de la JVM del Job, los argumentos quedan solo en `rendimiento.md` y en `docs/volumen-jvm.md` |
| H-Gate (C2, robustez) | Plan G, G-15 | «C2 (robustez) depende del Plan G», sin marcar cumplido |

## Self-review

- **Cobertura de las tareas pedidas:** P11-01 y P12-01 están hechas (hitos 132 y 133) y no se repiten; P13-01 está hecha con la decisión de código de salida pendiente (H-11); P13-04 está hecha (hito 136), aquí solo la verificación `--check` en el H-Gate y la licencia (H-21); P13-05 tiene identificadores y nombres hechos (hito 135) y el barrido de valores falta (H-15). P11-02 = H-4 y H-5; P11-03 = H-6 y H-7; P11-04 = H-1, H-8 y H-9; P11-05 = H-2 y H-3; P11-06 = H-10; P12-02 = H-18, H-19 y H-20; P12-03 y la plantilla de JVM = H-20; P12-04 = H-16 y H-17; P13-03 = H-12 a H-14; P13-02 = H-21.
- **Rutas:** cada `Modify` apunta a un archivo que existe hoy (`cli.py`, `cli_migrar.py`, `cli_migrar_comando.py`, `verify.py`, `informes.py`, `desde_plan.py`, `desde_plan_map.py`, `componentes.py`, `tmap.py`, `tools/performance/migrar.py`, `docs/plan-reescritura/plan-migrador-general.md`, `docs/secretos.md`, `PROGRESS.md`) o a uno que crea una tarea anterior de este plan (`cli_explicar.py` en H-1; `ajustes.py` en H-4; `escritura_paquete.py` en H-5; `codigos_pendiente.py` y `pendientes.yaml` en H-2). Los `Create` van en carpetas existentes (`src/sgm/migrar/`, `src/sgm/seguridad/`, `src/sgm/talend_item/`, `tools/performance/`, `tests/unit/`, `docs/`, `metrics/performance/`, `rules/`) salvo `rules/mensajes/`, `rules/privacidad/` y `tests/corpus/proyectos/`, que la tarea crea.
- **Cosas a verificar al ejecutar (no se supusieron):** el atributo de `Operator` que lleva `dataset` (H-6), los prefijos reales de los nodos de salida (H-9), la firma de `measure_command` y las claves de `mg-p12-01.json` (H-17), el nombre exacto de la función de escape de `java_literals.py` y de render de `sql_render.py` (H-15), los nombres XML de los parámetros del `tMap` (H-19), el parámetro de la JVM del Job (H-20), y si `tests/corpus/proyectos/` lo recorren `tools/corpus.py` o los tests del corpus (H-7; si lo recorren, la carpeta va a `tests/fixtures/proyectos/`).
- **Sin pendientes inventados:** `tSortRow` en disco no se emite sin página; el JVM provisional se rotula `sin medir`; ninguna cifra de límites se escribe antes de la corrida. Las pruebas de secretos usan cadenas inventadas; ningún paso abre `Cod2.txt`.
- **Archivos de 300 líneas:** H-1 (`cli.py`), H-3 (`informes.py`), H-5 (`cli_migrar.py`), H-13 (`desde_plan.py`) y H-19 (`desde_plan_map.py`) extraen antes de tocar, sin cambio de comportamiento.

## Resumen de horas

| Tarea | Plan maestro | Horas de trabajo | Crédito en el avance |
|---|---|---|---|
| H-1 | MG-P11-04 (preparación) | 1 | 1 |
| H-2 | MG-P11-05 | 2,5 | 2,5 |
| H-3 | MG-P11-05 | 1,5 | 1,5 |
| H-4 | MG-P11-02 | 2 | 2 |
| H-5 | MG-P11-02 | 2 | 2 |
| H-6 | MG-P11-03 | 4 | 4 |
| H-7 | MG-P11-03 | 4 | 4 |
| H-8 | MG-P11-04 | 2 | 2 |
| H-9 | MG-P11-04 | 1 | 1 |
| H-10 | MG-P11-06 | 2 | 2 |
| **Subtotal MG-P11** | | **22** | **22** (llega a 30/30) |
| H-11 | MG-P13-01 (residual, C2) | 1 | 0 (ya acreditada en el hito 134) |
| H-12 | MG-P13-03 | 2 | 2 |
| H-13 | MG-P13-03 | 2 | 2 |
| H-14 | MG-P13-03 | 1 | 1 |
| H-15 | MG-P13-05 (residual) | 2 | 0 (ya acreditada en el hito 135) |
| H-21 | MG-P13-02 (persona) | 0 (0,5 día-persona) | 0 |
| **Subtotal MG-P13** | | **8** | **5** (más 0,75 h de P13-02 cuando la persona cierre H-21) |
| H-16 | MG-P12-04 | 2,5 | 2,5 |
| H-17 | MG-P12-04 | 1,5 | 1,5 |
| H-18 | MG-P12-02 | 4 | 4 |
| H-19 | MG-P12-02 | 4 | 4 |
| H-20 | MG-P12-02 (6) y MG-P12-03 (4) | 10 | 10 (6 de ellas solo si el lote de volumen corrió) |
| **Subtotal MG-P12** | | **22** | **22** (llega a 30/30) |
| H-Gate | GM6, C2, C4, C6 | 2 | 0 (verificación) |
| **Total** | | **54** | **49** |
