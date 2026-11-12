# MG-E: Macros Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Que el expansor de macros de `sgm` (`src/sgm/frontend/macros*.py`) resuelva todo lo que un programa SAS puede resolver sin ejecutarse (`%LET`, `&var`, `&&var&i`, `%MACRO` con parámetros, `%IF`, `%DO` con y sin límites constantes, `%EVAL`, `%SYSFUNC`, citado, `%INCLUDE`, autollamadas), detecte los bloques que se repiten con otro parámetro (contrato con el Plan F1, joblets), trate las variables de macro de tiempo de ejecución (`SELECT INTO`, `CALL SYMPUT`) y deje como `Pendiente:` con código estable lo que no se puede demostrar (`CALL EXECUTE`, opciones del sistema que cambian resultados). Cierra MG-P7 con `L5` completo en el anillo B y en el lote C de Studio.

**Architecture:** Cambios solo en `sgm-v2` (Python). Hay **dos expansores** y no se deben confundir: `src/sgm/frontend/macros*.py` (el del producto, `Expander`, evaluación parcial sobre sentencias del lexer, marca lo no constante como `MacroDynamic` con motivo `MACRO_DINAMICA`) y `tools/corpus_lib/expansor_macros.py` (el del oráculo del corpus: expande el texto completo y falla con `ErrorMacro` ante lo que no conoce; lo usan `tools/corpus_lib/generar_entradas_l4l6.py` y `tools/corpus_datos/validaciones_sas.py`). Cada construcción nueva entra con un caso de `tests/corpus/L5/` cuyo esperado se calcula a mano según la página de `mcrolref`, con el patrón del Plan B: prueba unitaria del expansor primero, caso del corpus en el anillo B (`tests/unit/test_migrar_corpus_anillo_b.py`), anillo A (`sgm migrar`) y lote de Studio al final. Lo que una página no demuestra queda como `Pendiente:` con su código, no como un valor supuesto.

**Tech Stack:** Python 3.12, pytest, ruff, `pyyaml`; `uv run python -m pytest` y `uv run python -m sgm.cli` (en este Windows `uv run pytest` puede bloquearse por Control de aplicaciones).

**Spec:** `docs/plan-reescritura/plan-migrador-general.md` (MG-P7-01 a MG-P7-07, MG-D04, secciones 2, 5.2 y 11b) y `docs/superpowers/plans/2026-11-11-ruta-al-100.md`.

**Horas del plan maestro cubiertas:** MG-P7 restante 52 h (60 h menos 8 h acreditadas; el plan maestro §11b dice «L5: 8 de 12 pasan en B», pero hoy pasan 10 de 12: ver E-1).

**Serie de hitos:** `n` (carril de Byron, E-1 a E-19). La letra va en el título de la entrada de `PROGRESS.md` y en el mensaje del commit. El Plan C usa también `n` para procedimientos (C-16 a C-23): antes de escribir, buscar el último `## Hito` de `PROGRESS.md` y sumar uno; el número es único, la letra no.

## Global Constraints

- Sin `git push`, sin `--amend`. Un commit local por hito: `hito N n: <resumen>`, terminado con la línea `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Antes de escribir, buscar el último `## Hito` de `PROGRESS.md` (al redactar este plan era el 198) y sumar uno; si otra sesión ya tomó el número, tomar el siguiente. No renumerar entradas publicadas.
- No tocar `tools/ci.py`, `tools/validacion.py`, `tools/instalar_ganchos.py`, `README.md` ni `.githooks/` (son del Plan A y están sin commitear).
- Nada de nombres de scripts de ejemplo (`cod1`, `cod2`, `cars_poc`, `exogena`, `split2`, `split3`, `executeBulkload`, `waitForBulkLoads`, `bulkload_generic`) en `src/` ni `rules/`; lo vigila `tests/unit/test_no_script_specific_names.py`. Los casos del programa pequeño del cliente (E-11) usan nombres neutros (`ciclo_append`, `tabla_base`); el nombre del cliente vive en `tests/corpus_reales/` y en `decisiones/`, no en `src/`.
- Si el SAS no demuestra un tipo, una columna, un valor o una equivalencia: `Pendiente:` con motivo y código `P-xxx`. Nunca un valor supuesto.
- Si no hay página de la guía SAS, no hay equivalencia. Cada regla nueva cita `<guía>, p. N` con una página que exista en `docs/referencia/sas/<guía>.INDEX.md`. No leer el PDF ni el `.txt` entero: ubicar la sección en el `.INDEX.md` y la página con `grep -n "<!-- página N -->" docs/referencia/sas/mcrolref.txt`. Los números de página de este plan son páginas del PDF (las del `.INDEX.md`), comprobadas con ese marcador al redactar: `mcrolref` 58, 59, 118, 139, 311, 315, 344, 357, 372, 403, 404, 413, 419, 423 y `lesysoptsref` 265, 266, 412, 432 existen.
- **Catálogo:** `tests/unit/test_catalogo_sas.py` exige que el literal `(p. N)` de cada `fuente` esté en el `.INDEX.md` de su guía. Si la página exacta de una opción no es una entrada del índice, `fuente` cita la entrada indexada que la contiene y la página exacta va en `nota`. Cada tarea que suma una construcción actualiza el YAML de `rules/sas/catalogo/` que corresponde (`funciones-macro.yaml`, `opciones-resultado.yaml`, `funciones-usadas.yaml`, `sentencias-data-step.yaml`) y su `estado`. Las sentencias de macro (`%LET`, `%DO`, `%IF`, `%MACRO`, `%GLOBAL`, `%LOCAL`) no tienen entrada hoy en ningún YAML del catálogo: la crea E-1 en `rules/sas/catalogo/sentencias-macro.yaml` (archivo nuevo; el esquema es `schemas/rules/catalogo.schema.json`).
- **Casos del corpus:** los casos nuevos van a `tests/corpus/L5/l5_<NN>_<nombre>/` con `caso.yaml` (`nivel: L5`, `construcciones`, `capa: A` o `B`, `tolerancia: 0`, `orden_relevante: false`, `estado: traducible` o `revisado`, `salidas`, `razonamiento` con la página, `fuentes_url`, `invariantes`), `programa.sas` (con `PROC IMPORT DATAFILE='.../entradas/X.csv'`, como los casos existentes), `entradas/*.csv` y `esperado/*.csv`. Numeración `l5_13` a `l5_29`, reservada a este plan (`l5_01` a `l5_12` ya existen). El esperado se calcula a mano según SAS y se escribe a mano: el oráculo no reproduce los casos de macros con ejecución.
- No borrar ni debilitar pruebas. Un caso que no se puede traducir queda en `tests/corpus/migrar_pendientes.yaml` con su motivo, no se quita del corpus. Quitar una entrada de `CONOCIDOS` en `tests/unit/test_migrar_corpus_anillo_b.py` cuando el caso pasa es lo que la prueba exige (`xfail(strict=True)`): no es debilitarla.
- Archivos de menos de 300 líneas. Hoy `macros.py` (204), `macros_modelo.py` (170), `macros_control.py` (142), `macros_llamadas.py` (72) y `macro_index.py` (87) caben, pero `tools/corpus_lib/expansor_macros.py` (277) queda al borde: si una tarea lo pasa de 300, extrae primero. `src/sgm/migrar/interprete.py` (1103 líneas) y `src/sgm/ir/lower_sql_flow.py` (608) ya pasan de 300: E-14 extrae a un módulo nuevo antes de tocarlos, en un paso propio y sin cambio de comportamiento.
- Código e identificadores en inglés (excepto los nombres de operadores de `operadores.py`, que están en español y se conservan); comentarios, docstrings y mensajes en español.
- Después de cada tarea: `uv run python -m pytest -q` y `uv run ruff check src tests tools` en verde. Para iterar se corre solo el archivo de la tarea (`-p no:cacheprovider`); la suite completa se corre al cerrar cada tarea.
- Studio: se usa solo en el lote de cierre (E-Gate) y en E-11, con `tools/validar_caso_studio.py <caso>` y `tools/corpus_studio.py lote ...`. Si `sgm studio salud` no conecta, no reinstalar nada ni cambiar `talend-mcp` (ver `docs/guia-validacion-studio.md`, sección 7): la tarea queda con «lote C pendiente» y su motivo, y no se cuenta como pasada.

## Review Focus

- **Nunca se adivina:** un valor de macro desconocido queda desconocido y el texto original se conserva (`macros_modelo.py`, docstring). Toda función nueva que resuelva algo devuelve «no sé» (`None` o el texto intacto) ante una entrada que no demuestra. Tests en E-2, E-3, E-4 y E-5.
- **`%STR` no es `%NRSTR`:** `%STR` enmascara caracteres especiales pero deja resolver `&` y `%`; `%NRSTR` también los enmascara (`mcrolref`, p. 118 y 119). Tratarlos igual cambia el valor del filtro. Test en E-2.
- **Alcance de variables:** una macro llamada recibe una copia de las variables del llamador (`LlamadasMixin._call`: `local = dict(env)`), y hoy un `%LET` dentro de ella no vuelve al llamador. SAS actualiza la variable global si ya existe (`mcrolref`, p. 73 y 82). Test y caso en E-8.
- **El expansor del producto y el del oráculo deben coincidir** en lo que ambos soportan; si divergen, el caso del corpus se calcula con uno y se traduce con el otro. Test de paridad en E-1.
- **Ningún pase nuevo puede cambiar la firma de los Jobs ya validados** en L0 a L4 y L6 (los `test_golden*.py` y `test_ir_operadores_corpus.py` deben seguir idénticos). `Expanded` y `_flatten` los consumen `program.py` y `flow/model.py`: E-10 y E-11 agregan campos con valor por omisión y no cambian el orden de los pasos.
- **Un Job parcial nunca se emite:** una macro que depende de la ejecución (`CALL EXECUTE`, `%DO` con límite leído de datos) queda como paso `unsupported` con su código; nunca se desenrolla un número supuesto de vueltas. Tests en E-13 y E-15.

---

## Parte I. Expansor estático completo (MG-P7-01, 16 h)

### Task E-1: Línea base medida de L5, paridad de expansores y catálogo de sentencias de macro (serie `n`)

Medido al redactar: `uv run python -m pytest tests/unit/test_migrar_corpus_anillo_b.py -q -p no:cacheprovider -k L5` da **10 pasan, 2 `xfail`** (`l5_08_str_filtro_completo`: «la macro variable &FILTRO llega a la expresión sin resolver»; `l5_09_into_primer_fila`: «SELECT INTO deja la macro variable &ANIO sin resolver en la consulta»), y `tests/corpus/migrar_pendientes.yaml` lista solo `l5_09_into_primer_fila: P-ESQUEMA-NO-PORTABLE` (anillo A). El plan maestro dice 8 de 12: está desactualizado; esta tarea lo corrige con la cifra medida.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\linea_base_macros.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\rules\sas\catalogo\sentencias-macro.yaml`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\docs\plan-reescritura\plan-migrador-general.md` (solo la fila `MG-P7 Macros` de §11b)
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_linea_base_macros.py`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_paridad_expansores.py`

**Interfaces:**
- Consumes: `analyze_program(files: dict[str, str], external_files: dict[str, str] | None = None) -> ProgramAnalysis` (`sgm/frontend/program.py:104`; `ProgramAnalysis.items` es una lista de `ProgramItem` con `.item`), `MacroDynamic` (`sgm/frontend/macros_modelo.py:40`, campos `text`, `detail`, `line`, `end_line`, `reason`), `expandir(texto: str, into: dict[str, str] | None = None) -> str` (`tools/corpus_lib/expansor_macros.py:54`), `casos_de_nivel(corpus: Path, nivel: str) -> list[Caso]` (`tools/corpus_lib/caso.py:208`).
- Produces:
  ```python
  def medir(corpus: Path, pendientes: Path) -> dict:
      """Por caso de L5: cuántos MacroDynamic deja `analyze_program`, con su `detail`, y el código de
      `migrar_pendientes.yaml` si el caso está allí. Devuelve {"casos": {nombre: {"dinamicos": n,
      "motivos": [...], "pendiente_a": codigo | None}}, "total": n}. Salida JSON en
      `out/linea_base_macros.json` (no versionada)."""
  ```

- [ ] **Step 1: Write the failing tests.** `test_linea_base_macros.py`: con un corpus mínimo en `tmp_path` (un caso `L5/l5_99_x` cuyo `programa.sas` es `%let n = 1;\n%if &z = 1 %then %do;\nPROC SQL; CREATE TABLE WORK.A AS SELECT 1 AS X FROM WORK.B; QUIT;\n%end;`), `medir(tmp_path, tmp_path / "p.yaml")` devuelve `casos["l5_99_x"]["dinamicos"] == 1` y `"condición no constante" in casos["l5_99_x"]["motivos"][0]`; con `p.yaml` = `l5_99_x: P-ESQUEMA-NO-PORTABLE`, `pendiente_a == "P-ESQUEMA-NO-PORTABLE"`. `test_paridad_expansores.py`: para cada caso de `tests/corpus/L5` con `estado` traducible, las tablas que crea `analyze_program` (nombres de `CREATE TABLE`) son las mismas que las de `expandir(programa)`; los dos casos conocidos que difieren (`l5_08`, `l5_09`) se listan en una constante `DIVERGENCIAS` con su motivo, y la prueba falla si aparece una divergencia no listada **o** si una listada ya no diverge.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_linea_base_macros.py tests/unit/test_paridad_expansores.py -q -p no:cacheprovider`; esperado: no existe `linea_base_macros`.
- [ ] **Step 3: Implement** `medir` (carga con `corpus_lib.caso`, `yaml.safe_load` para los pendientes; sin dependencias nuevas). Crear `sentencias-macro.yaml` con `id: sentencias-macro`, `kind: catalogo`, `version: 1` y entradas `let-macro` (`fuente: mcrolref.pdf, p. 419`), `do-to-macro` (p. 404), `do-while-macro` (p. 407), `do-until-macro` (p. 406), `if-then-else-macro` (p. 413), `global-macro` (p. 410), `local-macro` (p. 421), `macro-statement` (p. 423), `put-macro` (p. 432); `estado: reconocida` para `let-macro`, `do-to-macro`, `if-then-else-macro` y `macro-statement`; `no_reconocida` para el resto (E-7 y E-8 las suben). Ajustar la forma exacta al esquema de `schemas/rules/catalogo.schema.json` y a `opciones-resultado.yaml` (mismo molde).
- [ ] **Step 4: Run tests to verify they pass**, luego `uv run python tools/linea_base_macros.py tests/corpus` y pegar en `PROGRESS.md`: casos de L5 con dinámicos, motivos y los dos `xfail` actuales (la línea base de este plan). Reescribir en §11b la fila `MG-P7` con la cifra medida (B: 10 de 12; A: 11 de 12) y su método.
- [ ] **Step 5: Run** `uv run ruff check src tests tools` y `uv run python -m pytest tests/unit/test_catalogo_sas.py -q -p no:cacheprovider`. **Commit** `hito N n: linea base medida de macros, paridad de expansores y catalogo de sentencias de macro`.

---

### Task E-2: `%STR` y `%NRSTR` en `%LET` (MG-P7-01, citado; serie `n`)

Cierra `l5_08` (hoy `xfail`). `Expander._let` (`macros.py`) hace `self._subst(raw, env)` y, si el valor conserva `%` o `&`, deja `env[name] = None`: un `%str(...)` completo siempre queda desconocido. Regla (`mcrolref`, p. 118 «%STR and %NRSTR Functions», p. 119 «Using % Signs with %STR», diccionario p. 357): `%STR` enmascara caracteres especiales en la compilación pero **sí resuelve** `&` y `%`; `%NRSTR` además los enmascara. El resultado de `%STR(texto)` en `%LET` es `texto`.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\frontend\macros_cita.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\frontend\macros.py` (`_let`, líneas 121-142)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_migrar_corpus_anillo_b.py` (quitar `l5_08_str_filtro_completo` de `CONOCIDOS`)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\rules\sas\catalogo\funciones-macro.yaml` (`str` y `nrstr`: `fuente` ya apunta a `mcrolref.pdf, p. 349`/`357` según la entrada; subir a `reconocida` solo `str`)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\L5\l5_13_str_con_variable\{caso.yaml, programa.sas, entradas\CUENTAS.csv, esperado\RES.csv}`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_macros_cita.py`

**Interfaces:**
- Consumes: `Expander._subst(text: str, env: dict[str, str | None]) -> str` (`macros.py`), `Expander._dynamic(stmt: Stmt, detail: str) -> MacroDynamic`, `_LET` (`macros_modelo.py`).
- Produces:
  ```python
  def desenvolver_cita(valor: str) -> tuple[str, str] | None:
      """Si `valor` es por completo `%str(...)` o `%nrstr(...)` con paréntesis balanceados,
      devuelve (texto_interior, "str" | "nrstr"); si no, None. No resuelve nada."""
  ```
  y en `_let`: un `%str` interior se sustituye con `self._subst` y se guarda; un `%nrstr` sin `&` ni `%` se trata como `%str`; con `&` o `%` deja `env[name] = None` y devuelve `self._dynamic(s, "%nrstr conserva & y % sin resolver: <name>")`.

**Caso `L5/l5_13_str_con_variable` (`capa: B`, `estado: revisado`, razonamiento: «mcrolref, p. 118 y 119: %STR deja resolver &LIM»).**
`programa.sas`:
```sas
PROC IMPORT DATAFILE='.../entradas/CUENTAS.csv' OUT=WORK.CUENTAS DBMS=CSV REPLACE; GETNAMES=YES; RUN;
%let LIM = 100;
%let FILTRO = %str(SALDO > &LIM AND ESTADO = 'ACTIVO');
PROC SQL;
CREATE TABLE WORK.RES AS
SELECT ID, SALDO FROM WORK.CUENTAS WHERE &FILTRO;
QUIT;
```
Entrada `CUENTAS.csv`: `ID,SALDO,ESTADO` / `1,150,ACTIVO` / `2,80,ACTIVO` / `3,100,ACTIVO` / `4,300,INACTIVO` / `5,101,ACTIVO`. Esperado a mano (el filtro queda `SALDO > 100 AND ESTADO = 'ACTIVO'`; el 3 vale 100, no es mayor; el 4 es inactivo; el 2 no llega): `RES.csv` = `ID,SALDO` / `1,150` / `5,101`. Invariante: `filas(RES) == 2`.

- [ ] **Step 1: Write the failing tests** en `test_macros_cita.py`: `desenvolver_cita("%str(a > 1)") == ("a > 1", "str")`; `desenvolver_cita("%nrstr(x)") == ("x", "nrstr")`; `desenvolver_cita("%str(a)b") is None`; `desenvolver_cita("%str(f(x))") == ("f(x)", "str")` (paréntesis anidados). Con `analyze_program({"p.sas": "%let l = 100;\n%let f = %str(s > &l);\ndata o; set t; where &f; run;"})`, la sentencia `where` del paso queda `s > 100`. Con `%let f = %nrstr(a&b);` el resultado trae un `MacroDynamic` cuyo `detail` empieza por `%nrstr conserva`. Agregar el caso del corpus.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_macros_cita.py tests/unit/test_migrar_corpus_anillo_b.py -q -p no:cacheprovider -k "cita or l5_13 or l5_08"`; esperado: no existe `macros_cita` y `l5_13` falla.
- [ ] **Step 3: Implement** `desenvolver_cita` (balanceo de paréntesis a mano, sin regex recursiva; comillas simples y dobles dentro del texto no cuentan para el balanceo: mismo criterio que `split_top` de `macros_modelo.py`) y el cambio de `_let`: antes de `self._subst(raw, env)`, `if (cita := desenvolver_cita(raw)): ...`. `%str` con comilla suelta (`%'`) queda `MacroDynamic` con `Pendiente: P-MACRO-COMILLA-SUELTA` (p. 119, «Using Unmatched Quotation Marks and Parentheses»: no se implementa el enmascarado).
- [ ] **Step 4: Run tests to verify they pass.** Quitar `l5_08` de `CONOCIDOS` y correr `tests/unit/test_migrar_corpus_anillo_b.py -k L5`: ahora `l5_08` y `l5_13` pasan y `strict=True` obliga a quitar la marca. Actualizar `funciones-macro.yaml` y `sentencias-macro.yaml` (nada que subir en este último). Correr `tests/unit/test_macros.py tests/unit/test_catalogo_sas.py` y el golden (no deben cambiar).
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N n: %STR y %NRSTR en %LET; l5_08 pasa en el anillo B`.

---

### Task E-3: `%SYSFUNC` con funciones de texto deterministas (MG-P7-01; serie `n`)

Hoy `_static_sysfunc` (`macros.py:186`) resuelve solo `%SYSFUNC(UPCASE(x))`. Se amplía a las funciones de texto que no dependen del entorno, citadas: `%SYSFUNC` (`mcrolref`, p. 372), `LOWCASE` (`lefunctionsref`, p. 1219), `STRIP` (p. 1568), `TRIM` (p. 1624), `UPCASE` (p. 1638). Las que dependen de la fecha o del entorno (`TODAY`, `DATE`, `DATETIME`, `PUTN`, `GETOPTION`, `SYSGET`, `EXIST`) siguen dinámicas (valor de ejecución: E-13 las registra). La guarda ya existente (`_upcase_options`: `ENCODING`, `LOCALE`, `TRANTAB` o `OPTIONS` con macro) vale también para `LOWCASE`.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\frontend\macros_sysfunc.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\frontend\macros.py` (`_static_sysfunc` y `_SYSFUNC_UPCASE` salen de este archivo; queda `from sgm.frontend.macros_sysfunc import evaluar_sysfunc`)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\rules\sas\catalogo\funciones-macro.yaml` (`sysfunc`: subir a `reconocida` con `nota` «UPCASE, LOWCASE, STRIP, TRIM; lo demás, dinámico»)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\rules\sas\catalogo\funciones-usadas.yaml` (`lowcase-function`, `strip-function`, `trim-function` si existen: `estado` según lo que el expansor haga)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\L5\l5_14_sysfunc_lowcase_en_literal\{caso.yaml, programa.sas, entradas\CANALES.csv, esperado\RES.csv}`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_macros_sysfunc.py` (los tests de `%sysfunc` de `tests/unit/test_macros.py` líneas 80-115 siguen verdes sin cambios)

**Interfaces:**
- Consumes: `Expander._upcase_options: frozenset[str]` (`macros.py:60`), `_DYNAMIC_FN` (`macros_modelo.py`).
- Produces:
  ```python
  def evaluar_sysfunc(texto: str) -> str | None:
      """Valor de `%sysfunc(f(arg))` con f en {upcase, lowcase, strip, trim} y `arg` ASCII sin
      `&`, `%` ni comas; None en cualquier otro caso. `strip` quita blancos a los dos lados;
      `trim`, a la derecha."""
  ```

**Caso `L5/l5_14_sysfunc_lowcase_en_literal` (`capa: B`, `estado: revisado`, razonamiento: «mcrolref, p. 372; lefunctionsref, p. 1219: LOWCASE»).**
`programa.sas`:
```sas
PROC IMPORT DATAFILE='.../entradas/CANALES.csv' OUT=WORK.CANALES DBMS=CSV REPLACE; GETNAMES=YES; RUN;
%let CANAL = %sysfunc(lowcase(WEB));
PROC SQL;
CREATE TABLE WORK.RES AS
SELECT ID FROM WORK.CANALES WHERE CANAL = "&CANAL.";
QUIT;
```
Entrada `CANALES.csv`: `ID,CANAL` / `1,web` / `2,WEB` / `3,app` / `4,web`. Esperado a mano (la comparación de cadenas de `PROC SQL` distingue mayúsculas; el filtro queda `CANAL = "web"`): `RES.csv` = `ID` / `1` / `4`. Invariante: `filas(RES) == 2`.

- [ ] **Step 1: Write the failing tests** en `test_macros_sysfunc.py`: `evaluar_sysfunc("%sysfunc(lowcase(WEB))") == "web"`; `evaluar_sysfunc("%sysfunc(strip(  ab  ))") == "ab"`; `evaluar_sysfunc("%sysfunc(trim(ab  ))") == "ab"`; `evaluar_sysfunc("%sysfunc(today())") is None`; `evaluar_sysfunc("%sysfunc(lowcase(Ñ))") is None` (no ASCII: la regla no está demostrada). Con `analyze_program` y `options encoding=latin1;` antes, `%let c = %sysfunc(lowcase(WEB));` queda `MacroDynamic` (guarda de opciones).
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_macros_sysfunc.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement** mover y ampliar. `evaluar_sysfunc` no hace `eval` ni `getattr`: tabla cerrada `{"upcase": str.upper, "lowcase": str.lower, "strip": str.strip, "trim": str.rstrip}`. Agregar el caso del corpus.
- [ ] **Step 4: Run tests to verify they pass**, `tests/unit/test_macros.py`, `tests/unit/test_migrar_corpus_anillo_b.py -k "L5"` (`l5_06` y `l5_14` pasan) y el golden. Actualizar los dos YAML del catálogo.
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N n: %SYSFUNC con LOWCASE, STRIP y TRIM, y guarda de opciones para LOWCASE`.

---

### Task E-4: `&&var&i` y referencias indirectas (MG-P7-01; serie `n`)

`macro_index.substitute` resuelve `&var` y `&var.` en una sola pasada; `&&t&i.` (una de las tres formas que usa `tests/fixtures/sas/p2_codigo_dinamico.sas`) no se resuelve. Regla (`mcrolref`, p. 58 «Referencing Macro Variables Indirectly», p. 59 «Using More Than Two Ampersands»): dos `&` seguidos se vuelven uno y el texto se vuelve a explorar; `&&&x` resuelve `x` y después el nombre que contiene.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\frontend\macros_indirecta.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\frontend\macro_index.py` (`substitute`, líneas 21-37, llama a `resolver_referencias` cuando el texto trae `&&`)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\corpus_lib\expansor_macros.py` (`_AMPERSAND` y `_valor`, líneas 40 y 109: mismo comportamiento; si el archivo pasa de 300 líneas, extraer `_procesar` primero)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\L5\l5_15_indirecta_doble_ampersand\{caso.yaml, programa.sas, entradas\VENTAS.csv, entradas\PAGOS.csv, entradas\CLIENTES.csv, esperado\COPIA_1.csv, esperado\COPIA_2.csv, esperado\COPIA_3.csv}`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\rules\sas\catalogo\sentencias-macro.yaml` (entrada `referencia-indirecta`, `fuente: mcrolref.pdf, p. 58`, `estado: reconocida`)
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_macros_indirecta.py`

**Interfaces:**
- Consumes: `substitute(text: str, variables: dict[str, str]) -> tuple[str, bool]` (`macro_index.py:21`).
- Produces:
  ```python
  def resolver_referencias(texto: str, variables: dict[str, str], max_pasadas: int = 10) -> tuple[str, bool]:
      """Resuelve `&x`, `&x.` y `&&...` por pasadas: en cada una, `&&` pasa a `&` y las
      referencias simples conocidas se sustituyen. Se detiene cuando no quedan `&` o no hay
      cambio. Si queda alguna sin resolver devuelve el texto ORIGINAL y False. No toca lo que
      está entre comillas simples."""
  ```

**Caso `L5/l5_15_indirecta_doble_ampersand` (`capa: B`, `estado: revisado`, razonamiento: «mcrolref, p. 58 y 59: &&T&I. resuelve primero &I y después &T1»).**
`programa.sas`:
```sas
PROC IMPORT DATAFILE='.../entradas/VENTAS.csv' OUT=WORK.VENTAS DBMS=CSV REPLACE; GETNAMES=YES; RUN;
PROC IMPORT DATAFILE='.../entradas/PAGOS.csv' OUT=WORK.PAGOS DBMS=CSV REPLACE; GETNAMES=YES; RUN;
PROC IMPORT DATAFILE='.../entradas/CLIENTES.csv' OUT=WORK.CLIENTES DBMS=CSV REPLACE; GETNAMES=YES; RUN;
%let N = 3;
%let T1 = VENTAS; %let T2 = PAGOS; %let T3 = CLIENTES;
%macro copiar;
%do I = 1 %to &N.;
PROC SQL;
CREATE TABLE WORK.COPIA_&I. AS SELECT ID FROM WORK.&&T&I.;
QUIT;
%end;
%mend copiar;
%copiar;
```
Entradas (columna `ID`): `VENTAS.csv` = `1`, `2`; `PAGOS.csv` = `3`; `CLIENTES.csv` = `4`, `5`, `6`. Esperado a mano: `COPIA_1.csv` = `ID` / `1` / `2` (vuelta 1: `&&T&I.` → `&T1` → `VENTAS`); `COPIA_2.csv` = `ID` / `3`; `COPIA_3.csv` = `ID` / `4` / `5` / `6`. Invariantes: `filas(COPIA_1) == 2`, `filas(COPIA_2) == 1`, `filas(COPIA_3) == 3`.

- [ ] **Step 1: Write the failing tests** en `test_macros_indirecta.py`: `resolver_referencias("WORK.&&t&i.", {"t1": "VENTAS", "i": "1"}) == ("WORK.VENTAS", True)`; `resolver_referencias("&&&a", {"a": "b", "b": "7"}) == ("7", True)`; `resolver_referencias("&&t&i", {"t1": "X"}) == ("&&t&i", False)` (`i` desconocida: texto original); `resolver_referencias("'&&t&i'", {"t1": "X", "i": "1"}) == ("'&&t&i'", True)` (comilla simple: no se toca). Con `analyze_program` y el programa del caso, los pasos `CREATE TABLE` salen con `COPIA_1`, `COPIA_2`, `COPIA_3` y leen `VENTAS`, `PAGOS`, `CLIENTES`.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_macros_indirecta.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement** el algoritmo por pasadas con una expresión regular simple `&&|&([A-Za-z_]\w*)\.?` y `re.sub` con función; `substitute` delega solo si el texto contiene `&&` (el resto del comportamiento, idéntico). Dejar un comentario con `mcrolref.pdf, p. 58`.
- [ ] **Step 4: Run tests to verify they pass**, `tests/unit/test_macros.py`, `tests/unit/test_migrar_corpus_anillo_b.py -k L5` y el golden. Agregar la entrada del catálogo; `tests/unit/test_catalogo_sas.py` en verde.
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N n: referencias indirectas &&var&i en el expansor y en el oraculo`.

---

### Task E-5: `%IF` con condiciones compuestas, parámetros y `%LENGTH` (MG-P7-01 y MG-P7-05, primer hueco; serie `n`)

`ControlMixin._condition` (`macros_control.py:23`) devuelve `None` si tras sustituir queda `&` o `%`, o si el texto trae `and`, `or`, `not` o `in`. Es el origen del hueco anotado en `tests/corpus/HUECOS_FRONTEND_TOTALES.md` (`%IF &estado. = CONCILIA %THEN %DO;`, `%IF %LENGTH(&mes.) = 2 %THEN %DO;`, `%IF %LENGTH(&dia.) = 10 %THEN %DO;`, dentro de macros con parámetros). Regla: `%IF` evalúa su condición como `%EVAL` (`mcrolref`, p. 413 «%IF-%THEN/%ELSE Macro Statement» y p. 344 «%EVAL»); `%LENGTH` está en el diccionario de funciones de macro (p. 347 según `funciones-macro.yaml`).

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\frontend\macros_condicion.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\frontend\macros_control.py` (`_condition` pasa a llamar a `evaluar_condicion`; la tabla de operadores de las líneas 23-60 se mueve al módulo nuevo en un paso propio y sin cambio de comportamiento)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\rules\sas\catalogo\sentencias-macro.yaml` (`if-then-else-macro`: la `nota` pasa a «condiciones con and/or/not, %LENGTH, %UPCASE y %EVAL») y `rules\sas\catalogo\funciones-macro.yaml` (`length` y `upcase` a `reconocida`)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\L5\l5_16_if_compuesto_con_parametro\{caso.yaml, programa.sas, entradas\DATOS.csv, esperado\OK.csv, esperado\NO.csv}`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_macros_condicion.py`

**Interfaces:**
- Consumes: `_COMPARE`, `_int(text: str) -> int | None`, `_unquote(text: str) -> str` (`macros_modelo.py`), `Expander._subst(text: str, env: dict[str, str | None]) -> str`.
- Produces:
  ```python
  def evaluar_condicion(texto: str) -> bool | None:
      """Valor de una condición de `%IF` ya sustituida. Soporta comparaciones (`=`, `eq`, `^=`, `ne`,
      `<`, `lt`, `<=`, `le`, `>`, `gt`, `>=`, `ge`), `and`, `or`, `not` (precedencia: not, and, or) y
      los operandos `%length(x)`, `%upcase(x)` y `%eval(expr)` con argumento constante. Dos enteros se
      comparan como números; si no, como texto sin distinguir mayúsculas (como `_condition` hoy).
      None ante `&`, `%` sin resolver o una función desconocida."""
  ```

**Caso `L5/l5_16_if_compuesto_con_parametro` (`capa: B`, `estado: revisado`, razonamiento: «mcrolref, p. 413 y 344: and, comparación de texto y %LENGTH con el parámetro de la macro»).**
`programa.sas`:
```sas
PROC IMPORT DATAFILE='.../entradas/DATOS.csv' OUT=WORK.DATOS DBMS=CSV REPLACE; GETNAMES=YES; RUN;
%macro marca(estado=);
%if &estado. = CONCILIA and %length(&estado.) = 8 %then %do;
PROC SQL;
CREATE TABLE WORK.OK AS SELECT ID FROM WORK.DATOS WHERE ID <= 2;
QUIT;
%end;
%else %do;
PROC SQL;
CREATE TABLE WORK.NO AS SELECT ID FROM WORK.DATOS WHERE ID > 2;
QUIT;
%end;
%mend marca;
%marca(estado=CONCILIA);
%marca(estado=DIFIERE);
```
Entrada `DATOS.csv`: `ID` / `1` / `2` / `3`. Esperado a mano: la primera llamada cumple `CONCILIA = CONCILIA` y `%LENGTH(CONCILIA) = 8` (C-O-N-C-I-L-I-A) y crea `OK`; la segunda falla la comparación y crea `NO`. `OK.csv` = `ID` / `1` / `2`; `NO.csv` = `ID` / `3`. Invariantes: `filas(OK) == 2`, `filas(NO) == 1`.

- [ ] **Step 1: Write the failing tests** en `test_macros_condicion.py`: `evaluar_condicion("CONCILIA = CONCILIA and 8 = 8") is True`; `evaluar_condicion("DIFIERE = CONCILIA and 8 = 8") is False`; `evaluar_condicion("a = a or b = c") is True`; `evaluar_condicion("not 1 = 2") is True`; `evaluar_condicion("%length(CONCILIA) = 8") is True`; `evaluar_condicion("%upcase(ab) = AB") is True`; `evaluar_condicion("%eval(2+3) > 4") is True`; `evaluar_condicion("&x = 1") is None`; `evaluar_condicion("%foo(1) = 1") is None`. Con `analyze_program` y el programa del caso hay **cero** `MacroDynamic` y los pasos son `CREATE TABLE OK` y `CREATE TABLE NO`. Para los tres programas del hueco (`tests/corpus/L8/totales/05_conciliacion/programa.sas`, `06_periodo_fecha`, `07_impala_lectura`), `analyze_program` ya no deja `MacroDynamic` con `detail` que empiece por `condición no constante` en las líneas 160, 118 y 108; si alguna sigue (por ejemplo, un argumento que viene de una variable de ejecución), el test exige que el motivo lo diga y la causa se anota en `HUECOS_FRONTEND_TOTALES.md`.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_macros_condicion.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement.** Primero mover la tabla de operadores a `macros_condicion.py` (golden y `tests/unit/test_macros.py` idénticos); luego sumar `and`/`or`/`not` con un analizador de dos niveles (partir por `or`, luego por `and`, sin regex recursiva; las palabras se reconocen solo entre blancos y fuera de comillas) y las tres funciones. Un operando que es una función no listada devuelve `None`.
- [ ] **Step 4: Run tests to verify they pass**, `tests/unit/test_macros.py`, las pruebas de flujo (`ls tests/unit | grep flow`), `tests/unit/test_migrar_corpus_anillo_b.py -k L5` y el golden. Actualizar los catálogos.
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N n: %IF compuesto con parametros y %LENGTH; cierra el primer hueco del analizador`.

---

### Task E-6: `%EVAL` entero completo (MG-P7-01; serie `n`)

`_eval_call` (`macros.py:179`) delega en `_int` (`macros_modelo.py:153`) con `_INT_EXPR`; no está probado qué hace con `/`, `**` ni con el negativo. `%EVAL` opera solo con enteros (`mcrolref`, p. 344): un operando decimal es un error de SAS, no un valor.

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\frontend\macros_modelo.py` (`_int`, línea 153)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\corpus_lib\expansor_util.py` (`_entero_seguro`, línea 16: mismo conjunto de operadores)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\L5\l5_17_eval_encadenado\{caso.yaml, programa.sas, entradas\BASE.csv, esperado\RES.csv}`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_macros_eval.py`

**Interfaces:**
- Consumes: `_int(text: str) -> int | None`, `_entero_seguro(nodo: ast.AST) -> int` (`expansor_util.py:16`).
- Produces: `_int` evalúa `+ - * ( )` y el menos unario sobre enteros. `/` y `**` solo si la guía lo demuestra: **verificar al ejecutar** con `grep -n "<!-- página 344 -->" docs/referencia/sas/mcrolref.txt` y las páginas 345 y 346 buscando la frase sobre la división entera; si no hay frase que diga cómo se redondea `/`, `/` y `**` devuelven `None` (queda dinámico, `Pendiente: P-EVAL-DIVISION`). Un operando con punto decimal devuelve `None`.

**Caso `L5/l5_17_eval_encadenado` (`capa: B`, `estado: revisado`, razonamiento: «mcrolref, p. 344: %EVAL aritmética entera»).**
`programa.sas`:
```sas
PROC IMPORT DATAFILE='.../entradas/BASE.csv' OUT=WORK.BASE DBMS=CSV REPLACE; GETNAMES=YES; RUN;
%let N = %eval(2*3+1);
%let M = %eval(&N. - 4);
PROC SQL;
CREATE TABLE WORK.RES AS SELECT ID FROM WORK.BASE WHERE ID <= &N. AND ID > &M.;
QUIT;
```
Entrada `BASE.csv`: `ID` / `1` a `9` (nueve filas). Esperado a mano: `N = 7` (la multiplicación va antes), `M = 7 - 4 = 3`; el filtro es `ID <= 7 AND ID > 3`. `RES.csv` = `ID` / `4` / `5` / `6` / `7`. Invariante: `filas(RES) == 4`.

- [ ] **Step 1: Write the failing tests** en `test_macros_eval.py`: `_int("%eval(2*3+1)") == 7`; `_int("%eval(7-4)") == 3`; `_int("%eval(-3+5)") == 2`; `_int("%eval(1.5+1)") is None`; para `%eval(3>2)` fijar lo que diga p. 344 (verdadero como `1`, o `None` si la página no lo demuestra) y citarlo en el test. Con `analyze_program`, `%let n = %eval(2*3+1);\n%let m = %eval(&n. - 4);\ndata o; set t; where id <= &n. and id > &m.; run;` produce el `where` `id <= 7 and id > 3`.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_macros_eval.py -q -p no:cacheprovider`; si ya pasan los de `+ - *`, anotarlo (la tarea se reduce a los límites del operador y al caso) y dejar solo los que fallan.
- [ ] **Step 3: Implement** el cambio mínimo de `_int` y de `_entero_seguro` y el caso.
- [ ] **Step 4: Run tests to verify they pass**, `tests/unit/test_macros.py`, `tests/unit/test_migrar_corpus_anillo_b.py -k L5` y el golden. `funciones-macro.yaml`: `eval` queda `reconocida`; la `nota` lista los operadores.
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N n: %EVAL entero con encadenado y limites del operador`.

---

### Task E-7: `%DO %WHILE`, `%DO %UNTIL` con condición constante (MG-P7-01; serie `n`)

Hoy `ControlMixin._do` (`macros_control.py:107`) muestra el cuerpo **una sola vez** y lo marca dinámico cuando el `%DO` no es `%DO i = a %TO b` (`%do %while`, `%do %until`). Con condición constante y variables que el cuerpo actualiza con `%LET`, el bucle es estático y se desenrolla. Regla: `%DO %WHILE` evalúa la condición antes de cada vuelta (`mcrolref`, p. 407); `%DO %UNTIL`, después (p. 406); `%DO i=start %TO stop` toma los límites al entrar (p. 404; ya está reconocido).

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\frontend\macros_bucles.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\frontend\macros_control.py` (`_do`: la rama «%do %while / %until» llama a `_do_condicional`; `ControlMixin` hereda de `BuclesMixin`)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\rules\sas\catalogo\sentencias-macro.yaml` (`do-while-macro` y `do-until-macro` a `reconocida`)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\L5\l5_18_do_while_con_contador\{caso.yaml, programa.sas, entradas\BASE.csv, esperado\T_1.csv, esperado\T_2.csv, esperado\T_3.csv}`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_macros_bucles.py`

**Interfaces:**
- Consumes: `evaluar_condicion(texto: str) -> bool | None` (E-5), `Expander._block(stmts: list[Stmt], i: int, file: str, env: dict, depth: int, nested: bool) -> tuple[list[object], int]`, `MAX_ITERATIONS` (1000).
- Produces:
  ```python
  class BuclesMixin:
      def _do_condicional(self, stmts: list[Stmt], i: int, file: str, env: dict, depth: int) -> tuple[list[object], int]:
          """`%do %while(cond)` y `%do %until(cond)`. Despliega el cuerpo mientras la condición,
          evaluada con `env` tras cada vuelta, sea constante. Si en algún punto es None, o se pasan
          `MAX_ITERATIONS` vueltas, devuelve el cuerpo una vez y un MacroDynamic con `detail` que
          empieza por `P-MACRO-BUCLE-NO-CONSTANTE`."""
  ```

**Caso `L5/l5_18_do_while_con_contador` (`capa: B`, `estado: revisado`, razonamiento: «mcrolref, p. 407: %DO %WHILE con contador que el cuerpo actualiza»).**
`programa.sas`:
```sas
PROC IMPORT DATAFILE='.../entradas/BASE.csv' OUT=WORK.BASE DBMS=CSV REPLACE; GETNAMES=YES; RUN;
%let K = 1;
%macro tablas;
%do %while(&K. <= 3);
PROC SQL;
CREATE TABLE WORK.T_&K. AS SELECT ID FROM WORK.BASE WHERE ID = &K.;
QUIT;
%let K = %eval(&K. + 1);
%end;
%mend tablas;
%tablas;
```
Entrada `BASE.csv`: `ID` / `1` / `2` / `3` / `4`. Esperado a mano: el cuerpo corre con `K` = 1, 2 y 3 y la condición `4 <= 3` corta. `T_1.csv` = `ID` / `1`; `T_2.csv` = `ID` / `2`; `T_3.csv` = `ID` / `3`. No existe `T_4`. Invariantes: `filas(T_1) == 1`, `filas(T_2) == 1`, `filas(T_3) == 1`.

- [ ] **Step 1: Write the failing tests** en `test_macros_bucles.py`: con el programa del caso, `analyze_program` da tres `CREATE TABLE` (`T_1`, `T_2`, `T_3`) y ningún `MacroDynamic`; un `%do %until(&k. > 2)` con `%let k = 1;` y `%let k = %eval(&k.+1);` en el cuerpo da dos vueltas (`k` = 1 y 2); un `%do %while(&q. < 3)` con `q` sin valor da un solo cuerpo y un `MacroDynamic` cuyo `detail` empieza por `P-MACRO-BUCLE-NO-CONSTANTE`; `%while(1 = 1)` (la condición nunca cambia) se corta en `MAX_ITERATIONS` con el mismo código y no se cuelga.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_macros_bucles.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement.** La condición se evalúa con `self._subst` y `evaluar_condicion` en cada vuelta, con el mismo `env` (el `%let` del cuerpo lo actualiza); `%until` ejecuta el cuerpo primero. Agregar el caso del corpus.
- [ ] **Step 4: Run tests to verify they pass**, `tests/unit/test_macros.py::test_do_no_constante_muestra_el_cuerpo_una_vez` (sigue pasando: usa un `%do i` con límite desconocido), `tests/unit/test_migrar_corpus_anillo_b.py -k L5` y el golden.
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N n: %DO %WHILE y %DO %UNTIL con condicion constante`.

---

### Task E-8: Alcance de variables: `%LOCAL`, `%GLOBAL` y `%LET` dentro de una macro (MG-P7-01; serie `n`)

`LlamadasMixin._call` (`macros_llamadas.py`) hace `local = dict(env)` y nunca copia de vuelta: un `%LET` dentro de una macro que cambia una variable global **se pierde** al volver. Regla (`mcrolref`, p. 73 «Scopes of Macro Variables», p. 82 «Examples of Macro Variable Scopes», `%GLOBAL` p. 410, `%LOCAL` p. 421): un `%LET` dentro de una macro cambia la variable global si ya existe y no hay una local con ese nombre; si no existe en ninguna parte, la crea local. Los parámetros y lo declarado con `%LOCAL` son locales; lo declarado con `%GLOBAL` crea una global.

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\frontend\macros_llamadas.py` (`_call`)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\frontend\macros.py` (`_block`: ramas `%local` y `%global`; `__init__`: `self._locales: list[set[str]] = []`)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\rules\sas\catalogo\sentencias-macro.yaml` (`global-macro` y `local-macro` a `reconocida`)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\L5\l5_19_alcance_global_y_local\{caso.yaml, programa.sas, entradas\SALDOS.csv, esperado\RES.csv}`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_macros_alcance.py`

**Interfaces:**
- Consumes: `Expander._call(call: re.Match, s: Stmt, env: dict, depth: int, file: str) -> list[object]`, `MacroEntry.params: list[tuple[str, str | None]]`.
- Produces: tras expandir el cuerpo, `_call` copia al `env` del llamador cada variable que **existía en `env` antes de la llamada** y que no es parámetro ni `%local` del marco, y cada `%global` nuevo; el resto (locales, parámetros, variables creadas dentro) no sale. `%local a b;` y `%global a b;` se consumen sin producir pasos.

**Caso `L5/l5_19_alcance_global_y_local` (`capa: B`, `estado: revisado`, razonamiento: «mcrolref, p. 73 y 82: el %LET de una macro cambia la global existente»).**
`programa.sas`:
```sas
PROC IMPORT DATAFILE='.../entradas/SALDOS.csv' OUT=WORK.SALDOS DBMS=CSV REPLACE; GETNAMES=YES; RUN;
%let CORTE = 100;
%macro sube;
%local TMP;
%let TMP = 50;
%let CORTE = %eval(&CORTE. + &TMP.);
%mend sube;
%sube;
PROC SQL;
CREATE TABLE WORK.RES AS SELECT ID FROM WORK.SALDOS WHERE SALDO >= &CORTE.;
QUIT;
```
Entrada `SALDOS.csv`: `ID,SALDO` / `1,100` / `2,149` / `3,150` / `4,200`. Esperado a mano: `CORTE` existe como global (100); dentro de `sube`, `%LET CORTE` la cambia a `100 + 50 = 150` (no hay local con ese nombre); `TMP` es local y no sale. El filtro es `SALDO >= 150`: `RES.csv` = `ID` / `3` / `4`. (Con el alcance mal resuelto saldrían las cuatro filas.) Invariante: `filas(RES) == 2`.

- [ ] **Step 1: Write the failing tests** en `test_macros_alcance.py`: con el programa del caso, el `WHERE` queda `SALDO >= 150`; con `%macro m; %let nuevo = 1; %mend; %m; data x_&nuevo; set t; run;` la salida conserva `x_&nuevo` (variable local, no sale); con `%macro m; %global g; %let g = 7; %mend; %m; data x_&g; set t; run;` sale `x_7`; con `%macro m(a); %let a = 9; %mend; %let a = 1; %m(5); data x_&a; set t; run;` sale `x_1` (el parámetro es local y no pisa la global).
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_macros_alcance.py -q -p no:cacheprovider`; esperado: el primero da `SALDO >= &CORTE.` o `>= 100`.
- [ ] **Step 3: Implement** la pila de marcos (`self._locales`) y la copia de vuelta; los `%if` con condición no constante ya dejan variables en `None` (`ControlMixin._if`): esa regla se conserva y la copia de vuelta propaga también el `None`. Dejar un comentario con `mcrolref.pdf, p. 73`.
- [ ] **Step 4: Run tests to verify they pass**, `tests/unit/test_macros.py`, `tests/unit/test_migrar_corpus_anillo_b.py -k L5`, el golden y `tests/unit/test_golden_equivalencia.py` (si algún programa del corpus dependía del comportamiento anterior, el diff se revisa a mano y se anota en `PROGRESS.md`, no se acepta a ciegas).
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N n: alcance de variables de macro (%LOCAL, %GLOBAL, %LET dentro de una macro)`.

---

## Parte II. `%INCLUDE` y autollamadas (MG-P7-03, 4 h)

### Task E-9: Autollamada con fin constante y `%INCLUDE` sin resolver (serie `n`)

`MAX_DEPTH = 20` (`macros_modelo.py`) corta la recursión con un `MacroDynamic` de `detail` «recursión de macros al llamar %x» (`LlamadasMixin._call`). Un argumento `%eval(&n. - 1)` hoy deja el parámetro en `None` (el valor conserva `%`), así que una macro que se llama a sí misma con un contador no se resuelve. Y un `%include` sin resolver devuelve la sentencia cruda (`_include`) y registra `unresolved_includes`: hay que medir si eso llega al informe de pendientes. Páginas: `%MACRO` (`mcrolref`, p. 423) y `%IF` (p. 413) para la recursión; `%INCLUDE` (`lestmtsref`, p. 134, entrada `include-statement` de `sentencias-data-step.yaml`, hoy `no_reconocida`).

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\frontend\macros_llamadas.py` (`_call`: los argumentos pasan por `_eval_call`; el `detail` de recursión empieza por `P-MACRO-RECURSION`; `_include` según el resultado del paso 1)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\rules\sas\catalogo\sentencias-data-step.yaml` (`include-statement`: `reconocida` si el medido muestra que el expansor lo resuelve; la `nota` dice qué no resuelve)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\L5\l5_20_autollamada_con_fin\{caso.yaml, programa.sas, entradas\BASE.csv, esperado\TAB_3.csv, esperado\TAB_2.csv, esperado\TAB_1.csv}`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_macros_autollamada.py`

**Interfaces:**
- Consumes: `_eval_call(text: str) -> int | None` (`macros.py`), `MAX_DEPTH`, `Expander.unresolved_includes: list[tuple[str, str, str]]`, `analyze_program(files: dict[str, str], external_files: dict[str, str] | None = None) -> ProgramAnalysis`.
- Produces: argumentos de llamada con `%eval(...)` constante ya valuados; `MacroDynamic.detail` de recursión: `"P-MACRO-RECURSION: la macro %<nombre> se llama a sí misma más de 20 veces; no se desenrolla"`; el `%include` sin resolver conserva `unresolved_includes` y, **solo si el paso 1 muestra que hoy se pierde en silencio**, agrega un `MacroDynamic` con `detail` `P-INCLUDE-NO-RESUELTO: <ruta>`.

**Caso `L5/l5_20_autollamada_con_fin` (`capa: B`, `estado: revisado`, razonamiento: «mcrolref, p. 423 y 413: la macro se llama a sí misma hasta que %IF corta»).**
`programa.sas`:
```sas
PROC IMPORT DATAFILE='.../entradas/BASE.csv' OUT=WORK.BASE DBMS=CSV REPLACE; GETNAMES=YES; RUN;
%macro cuenta(n);
%if &n. > 0 %then %do;
PROC SQL;
CREATE TABLE WORK.TAB_&n. AS SELECT ID FROM WORK.BASE WHERE ID <= &n.;
QUIT;
%cuenta(%eval(&n. - 1));
%end;
%mend cuenta;
%cuenta(3);
```
Entrada `BASE.csv`: `ID` / `1` / `2` / `3`. Esperado a mano: `cuenta(3)` crea `TAB_3` y llama a `cuenta(2)`, que crea `TAB_2` y llama a `cuenta(1)`, que crea `TAB_1` y llama a `cuenta(0)`, que no hace nada. `TAB_3.csv` = `ID` / `1` / `2` / `3`; `TAB_2.csv` = `ID` / `1` / `2`; `TAB_1.csv` = `ID` / `1`. Invariantes: `filas(TAB_3) == 3`, `filas(TAB_2) == 2`, `filas(TAB_1) == 1`.

- [ ] **Step 1: Medir.** Con un programa que tiene `%include 'no_existe.sas';` seguido de `data x; set t; run;`, correr `uv run python -m sgm.cli migrar <programa> --out out/e9` (flags según `sgm migrar --help`) y anotar en `PROGRESS.md` si el `%include` aparece en `pendientes.md`. Si aparece, no se toca `_include`; si no, se aplica el `MacroDynamic` descrito en `Produces`.
- [ ] **Step 2: Write the failing tests** en `test_macros_autollamada.py`: con el programa del caso salen `TAB_3`, `TAB_2`, `TAB_1` y ningún `MacroDynamic`; una macro `%macro r(n); %r(&n.); %mend; %r(1);` produce un `MacroDynamic` con `detail` que empieza por `P-MACRO-RECURSION` y no se cuelga; `analyze_program({"main.sas": "%include 'inc/tablas.sas';\n", "inc/tablas.sas": "data a; set b; run;\n"})` trae el paso `a` (`resolve_path` de `macro_index.py`); `tests/fixtures/sas/p0_macro_include.sas` ya lo cubre `tests/unit/test_macros.py::test_include_resuelto_expande_la_macro_del_archivo_incluido`: se referencia, no se duplica. El corpus L5 quizá no pueda adjuntar un `.sas` incluido (`Caso.programa` es un solo `programa.sas`): **verificar al ejecutar** con `sed -n 41,76p tools/corpus_lib/caso.py`; si es así, el `%INCLUDE` se prueba solo con `analyze_program(files)` y el `caso.yaml` de `l5_20` no lo menciona.
- [ ] **Step 3: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_macros_autollamada.py -q -p no:cacheprovider`.
- [ ] **Step 4: Implement** el valuado de `%eval` en los argumentos (mismo criterio que `_let`: `if (ev := _eval_call(value)) is not None: value = str(ev)`), el prefijo de código en el `detail` de recursión y, si corresponde, el `MacroDynamic` del include. Run tests, `tests/unit/test_macros.py`, `tests/unit/test_migrar_corpus_anillo_b.py -k L5` y el golden; actualizar el catálogo.
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N n: autollamadas con fin constante, P-MACRO-RECURSION y %INCLUDE sin resolver`.

---

## Parte III. Bloques repetidos y bucles de `APPEND` (MG-P7-02, 10 h)

### Task E-10: Registro de invocaciones y informe de bloques repetidos (contrato con el Plan F1; serie `n`)

Un bloque repetido es la misma macro (mismo cuerpo, `MacroEntry.key`) llamada dos o más veces con algún argumento distinto. Hoy `Expanded` guarda nombre, clave y pasos, pero no los argumentos: `LlamadasMixin._call` los resuelve en `local` y los descarta. Esta tarea los registra y define el **formato del informe**, que es el contrato que consume el Plan F1 (MG-P8-03, joblets; el escritor de joblets es F2-8 a F2-10 del Plan F2). Cambiar una clave del informe exige subir `version` y avisar al dueño del Plan F1.

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\frontend\macros_llamadas.py` (`_call`: `self.invocaciones.append(Invocacion(...))`)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\frontend\macros.py` (`Expander.__init__`: `self.invocaciones: list[Invocacion] = []`)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\frontend\program.py` (`ProgramAnalysis`, línea 36: campo `invocaciones`; `analyze_program` lo copia del `Expander`, línea 126)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\frontend\repeticiones.py`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_repeticiones.py`

**Interfaces:**
- Consumes: `Expanded(name, key, items)`, `MacroEntry(name, params, body, file, line, key)`, `ProgramAnalysis` (`items`, `index`, `unresolved_includes`).
- Produces:
  ```python
  @dataclass(frozen=True)
  class Invocacion:
      macro: str; huella: str; archivo: str; linea: int
      args: dict[str, str | None]   # valor resuelto de cada parámetro; None si no es constante
      pasos: int                    # pasos que produjo esa invocación

  @dataclass(frozen=True)
  class BloqueRepetido:
      origen: str                   # "llamada" | "bucle" (E-11)
      macro: str                    # macro llamada, o contenedora del %DO ("" si ninguna)
      huella: str
      parametros_variables: list[str]
      parametros_fijos: dict[str, str | None]
      invocaciones: list[Invocacion]
      candidata_joblet: bool        # True si hay >=1 parámetro variable y todos sus valores son constantes

  def detectar_repeticiones(analysis: ProgramAnalysis) -> list[BloqueRepetido]: ...
  def informe_a_dict(bloques: list[BloqueRepetido]) -> dict:
      """{"version": 1, "bloques": [ {origen, macro, huella, parametros_variables, parametros_fijos,
      invocaciones: [{linea, args, pasos}], candidata_joblet} ]}. Las claves quedan fijas por
      `test_formato_informe_repeticiones`."""
  ```

- [ ] **Step 1: Write the failing tests** en `test_repeticiones.py`: con `%macro p(t=, anio=2025); data o_&t; set s_&t; run; %mend;\n%p(t=a);\n%p(t=b);\n%p(t=c, anio=2024);`, `detectar_repeticiones(analyze_program({"p.sas": texto}))` devuelve **un** bloque, `macro == "p"`, `parametros_variables == ["t", "anio"]` (`anio` varía entre 2025 y 2024), tres invocaciones con `pasos == 1` y `candidata_joblet is True`; con `%p(t=a);` una sola vez, `[]`; con dos llamadas idénticas (`%p(t=a); %p(t=a);`), `[]` (no hay parámetro que varíe: es una repetición literal, no un joblet); con `%p(t=&x.)` donde `x` no es constante, `candidata_joblet is False`. `test_formato_informe_repeticiones`: `set(informe_a_dict(bloques)["bloques"][0]) == {"origen", "macro", "huella", "parametros_variables", "parametros_fijos", "invocaciones", "candidata_joblet"}` y `informe["version"] == 1`.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_repeticiones.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement.** Agrupar por `huella`; los selectores de ambiente (`Expander.selectors`) se excluyen (sus ramas son contextos, no joblets). `Expanded` no cambia, por lo que `_flatten` y el golden quedan idénticos.
- [ ] **Step 4: Run tests to verify they pass**, `tests/unit/test_macros.py`, el golden y `tests/unit/test_flow*.py`.
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N n: invocaciones de macro registradas e informe de bloques repetidos (contrato F1)`.

---

### Task E-11: Bucles `%DO` como bloque repetido y el patrón de `PROC APPEND` en bucle (contrato con el Plan K, K-6; serie `n`)

El programa pequeño del cliente tiene un bucle `%DO i=1 %TO 15` con un `PROC APPEND` sobre la misma tabla en cada vuelta y llamadas a macros de SAS Studio. K-6 parametriza el límite (`%let repeticiones = 15;` y `%do i=1 %to &repeticiones.;`) y necesita saber (a) que el expansor desenrolla las 15 vueltas y (b) que el informe las ve como un bloque repetido con el contador como parámetro. Esta tarea entrega ambas cosas; el operador `PROC APPEND` es del Plan B (B-8, `proc.pdf`, p. 161 y 162 según K-6: **verificar al ejecutar** con `grep -n "<!-- página 161 -->" docs/referencia/sas/proc.txt`).

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\frontend\macros_control.py` (`_do`, bucle `for value in values`: `self.iteraciones.append(...)`) y `macros_bucles.py` (E-7, mismo registro por vuelta)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\frontend\macros.py` (`self.iteraciones: list[Iteracion] = []`) y `program.py` (campo `iteraciones`)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\frontend\repeticiones.py` (E-10)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\L5\l5_21_do_append_parametrizado\{caso.yaml, programa.sas, entradas\ACUM.csv, entradas\UNO.csv, esperado\ACUM.csv}`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_repeticiones_bucles.py`

**Interfaces:**
- Consumes: `detectar_repeticiones`, `BloqueRepetido` (E-10), `Expander._do`.
- Produces:
  ```python
  @dataclass(frozen=True)
  class Iteracion:
      variable: str; valor: str; archivo: str; linea_do: int; macro: str; pasos: int
  ```
  `detectar_repeticiones` suma un `BloqueRepetido(origen="bucle", macro=<contenedora>, parametros_variables=[variable], invocaciones=[una por vuelta con args={variable: valor}])` por cada `%DO` desenrollado con 2 o más vueltas y al menos un paso por vuelta.

**Caso `L5/l5_21_do_append_parametrizado` (`capa: B`, `estado: parcial` hasta que exista B-8, luego `revisado`; razonamiento: «mcrolref, p. 404: %DO con límite de una macrovariable; proc.pdf, p. 161 y 162: APPEND»).** Usa una tabla `DATA=` distinta de `BASE=`: que la misma tabla sea `BASE=` y `DATA=` no está demostrado por la guía (es el `Pendiente: P-APPEND-MISMA-TABLA` de K-6).
`programa.sas`:
```sas
PROC IMPORT DATAFILE='.../entradas/ACUM.csv' OUT=WORK.ACUM DBMS=CSV REPLACE; GETNAMES=YES; RUN;
PROC IMPORT DATAFILE='.../entradas/UNO.csv' OUT=WORK.UNO DBMS=CSV REPLACE; GETNAMES=YES; RUN;
%let REPETICIONES = 3;
%macro agrega;
%do I = 1 %to &REPETICIONES.;
PROC APPEND BASE=WORK.ACUM DATA=WORK.UNO; RUN;
%end;
%mend agrega;
%agrega;
```
Entradas: `ACUM.csv` = `ID` / `1`; `UNO.csv` = `ID` / `7` / `8`. Esperado a mano: cada vuelta agrega las dos filas de `UNO` al final de `ACUM`; tres vueltas: `ACUM.csv` = `ID` / `1` / `7` / `8` / `7` / `8` / `7` / `8` (7 filas). Invariante: `filas(ACUM) == 1 + 3 * 2`.

- [ ] **Step 1: Write the failing tests** en `test_repeticiones_bucles.py`: con el programa del caso, `analysis.iteraciones` tiene 3 elementos con `variable == "i"`, valores `"1"`, `"2"`, `"3"`, `macro == "agrega"`; `detectar_repeticiones` da un bloque `origen == "bucle"` con `parametros_variables == ["i"]` y tres invocaciones; con `%let repeticiones = 15;` y un cuerpo con una sentencia `proc append base=a data=b; run;`, hay **15** pasos `PROC APPEND` (la cifra que K-6 espera del expansor); con un solo vuelta, ningún bloque.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_repeticiones_bucles.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement.** `Iteracion` se registra en una lista paralela (no se envuelve cada vuelta en un `Expanded`: eso cambiaría `call`/`outer` en `_flatten` y la firma de los Jobs). Agregar el caso; `estado: parcial` con `motivo: «PROC APPEND sin operador (Plan B, B-8)»`.
- [ ] **Step 4: Run tests to verify they pass**, el golden, `tests/unit/test_macros.py` y `tests/unit/test_migrar_corpus_anillo_b.py -k L5` (el caso `parcial` no se ejecuta: `ESTADOS = ("traducible", "revisado")`). Pegar en `PROGRESS.md` el número de pasos `PROC APPEND` medidos.
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N n: bucles %DO registrados como bloque repetido; caso de APPEND parametrizado`.

---

### Task E-12: Informe de repeticiones sobre los programas del repositorio (serie `n`)

Aceptación de MG-P7-02: «informe de repeticiones en los programas del repositorio».

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\informe_repeticiones.py`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_informe_repeticiones.py`

**Interfaces:**
- Consumes: `analyze_program`, `detectar_repeticiones`, `informe_a_dict` (E-10).
- Produces:
  ```python
  def informar(programas: list[Path]) -> dict:
      """{"version": 1, "programas": {ruta: informe_a_dict(...)}, "total_bloques": n,
      "candidatas_joblet": m}. Se escribe en `out/repeticiones.json` (no versionado)."""
  ```

- [ ] **Step 1: Write the failing test.** Con dos `.sas` en `tmp_path` (uno con `%p(t=a); %p(t=b);` sobre una macro `p`, otro sin repeticiones), `informar` devuelve `total_bloques == 1` y `candidatas_joblet == 1`, y un programa con un error de lectura queda con `"error"` en su clave sin abortar el resto.
- [ ] **Step 2: Run test to verify it fails.** `uv run python -m pytest tests/unit/test_informe_repeticiones.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement** el recorrido de `tests/fixtures/sas/**/*.sas` (con `client_large.sas` aparte, ver paso 4) y `tests/corpus/**/programa.sas`.
- [ ] **Step 4: Run** `uv run python tools/informe_repeticiones.py` y pegar en `PROGRESS.md`: bloques y candidatas por programa. `client_large.sas` (~800 KB) se corre solo, con `timeout` de 10 minutos; si no termina, se parte por rangos con el rebanador de K-8 (Plan K) y se anota. El informe no se versiona.
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N n: informe de repeticiones sobre los programas del repositorio`.

---

## Parte IV. Variables de macro de ejecución y código dinámico (MG-P7-04 y MG-P7-06, 12 h)

### Task E-13: Registro de variables de macro de ejecución y candidatas a contexto (contratos con Plan B, MG-P4-08, y Plan C, MG-P5-07; serie `n`)

El expansor ya marca lo dinámico (`_ordinary`: `call symput`, `into :var`, `%sysfunc` sobre datos), pero no dice **qué variable** nace en ejecución ni **dónde se usa**. Sin eso, B y C no saben qué referencia `&var` posterior depende de un valor calculado. Reparto: el Plan C (MG-P5-07) ya emite `set_variable` para `SELECT INTO` (`lower_sql_flow.py`, función de `into_vars`); el Plan B (MG-P4-08) emite el operador de `CALL SYMPUT`; **este plan registra** el origen y los usos y decide el destino (variable global del Job o variable de contexto). Páginas: `CALL SYMPUT` (`mcrolref`, p. 315, y el alcance especial de p. 93), `INTO` (`sqlproc`, p. 312).

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\frontend\macros_ejecucion.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\frontend\macros.py` (`_ordinary`, líneas 144-155) y `program.py` (campos `variables_ejecucion` y `candidatas_contexto`)
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_macros_ejecucion.py`

**Interfaces:**
- Consumes: `Let(name: str, value: str, line: int, end_line: int, text: str)` (`steps_tipos.py:50`), `_SYMPUT`, `_INTO`, `_DYNAMIC_FN` (`macros_modelo.py`).
- Produces:
  ```python
  @dataclass(frozen=True)
  class VariableEjecucion:
      nombre: str; origen: str   # "into" | "symput" | "sysfunc"
      archivo: str; linea: int; usos: list[int]   # líneas donde aparece &nombre
      en_limite_de_bucle: bool   # se usa como límite o condición de %DO / %IF

  @dataclass(frozen=True)
  class CandidataContexto:
      nombre: str; valor: str; linea: int; usos: list[int]
      limite_de_bucle: bool      # alimenta el límite de un %DO (K-6: `repeticiones`)

  def variables_de_ejecucion(analysis: ProgramAnalysis) -> list[VariableEjecucion]: ...
  def candidatas_a_contexto(analysis: ProgramAnalysis) -> list[CandidataContexto]:
      """`%let` con valor constante en el nivel superior del programa que se usa después; las
      consume MG-P8-04 (contextos por programa, Plan F2: F2-11)."""
  ```
  Regla de destino, documentada en el docstring: valor constante de `%let` a **variable de contexto**; valor calculado en ejecución (`into`, `symput`, `sysfunc` sobre datos) a **variable global del Job** (`tSetGlobalVar`), sin pasar por contexto. Si `en_limite_de_bucle`, el `%DO` no se puede desenrollar: `P-MACRO-BUCLE-NO-CONSTANTE` con `variable de ejecución: <nombre>` (E-7).

- [ ] **Step 1: Write the failing tests** en `test_macros_ejecucion.py`: con `proc sql; select max(anio) into :a from t; quit;\nproc sql; create table r as select x from s where y = &a; quit;`, `variables_de_ejecucion` devuelve una con `nombre == "a"`, `origen == "into"`, `usos == [<línea del create>]`; con `data _null_; set t; call symput('b', x); run;` y un `%do i = 1 %to &b;`, `origen == "symput"` y `en_limite_de_bucle is True`; con `%let repeticiones = 15;\n%macro m; %do i = 1 %to &repeticiones.; data a; set b; run; %end; %mend; %m;`, `candidatas_a_contexto` devuelve `nombre == "repeticiones"`, `valor == "15"`, `limite_de_bucle is True`; un `%let` que solo se define y no se usa no es candidata.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_macros_ejecucion.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement.** El registro se llena en `_ordinary` (al ver `into :x`, `call symput('x'`, o un `%let` con `%sysfunc` dinámico) y los usos se buscan con `substitute` sobre las sentencias posteriores. No toca los pasos ni el golden.
- [ ] **Step 4: Run tests to verify they pass**, `tests/unit/test_macros.py` y el golden. Avisar en `PROGRESS.md` («Decisiones») qué consume cada plan: B-`MG-P4-08` usa `origen == "symput"`; C-`MG-P5-07` usa `origen == "into"`; F2-11 usa `candidatas_a_contexto`.
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N n: variables de macro de ejecucion y candidatas a contexto registradas`.

---

### Task E-14: Intérprete: `set_variable` y referencias `&var` en el anillo B (cierra `l5_09`; serie `n`)

`l5_09_into_primer_fila` es el último `xfail` de L5 en B: «SELECT INTO deja la macro variable &ANIO sin resolver en la consulta». El lowering ya emite `set_variable` con `variable`, `separator`, `column`, `expression` (`lower_sql_flow.py:541-566`); el intérprete (`_ejecutar`, `interprete.py:967`) no lo ejecuta. Regla (`sqlproc`, p. 312 «INTO Clause»; el caso ya cita «varias filas toma la primera»: **verificar al ejecutar** con `grep -n "<!-- página 312 -->" docs/referencia/sas/sqlproc.txt`; si la página no dice «primera fila», `Pendiente: P-INTO-VARIAS-FILAS` y el caso queda `xfail` con ese motivo). El anillo A de `l5_09` sigue con `P-ESQUEMA-NO-PORTABLE` (la columna `AÑO`: nombre no portable): esa decisión es de nombres de columna y no se toma aquí; por eso se agrega un gemelo ASCII.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\interprete_variables.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\interprete.py` (`_ejecutar`, línea 967, y `ejecutar_plan`, línea 1076; **primero** un paso propio que mueva a `interprete_variables.py` solo lo nuevo, sin tocar el resto del archivo de 1103 líneas)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_migrar_corpus_anillo_b.py` (quitar `l5_09_into_primer_fila` de `CONOCIDOS`)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\L5\l5_22_into_primer_fila_ascii\{caso.yaml, programa.sas, entradas\VALIDACION.csv, entradas\DATOS.csv, esperado\RES.csv}`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_interprete_variables.py`

**Interfaces:**
- Consumes: `ejecutar_plan(plan: Plan, entradas: dict[str, list[dict[str, str | None]]]) -> dict[str, list[dict[str, str | None]]]`, `_valor(nodo, fila: dict) -> object` (`interprete.py:268`), `NoSoportadoEnInterprete`.
- Produces:
  ```python
  def valor_de_variable(op: Operator, filas: list[dict]) -> str | None:
      """Valor que `set_variable` deja en `op.params["variable"]`: la columna `op.params["column"]`
      de la primera fila (`separator` None) o todas unidas por el separador. Sin filas, None."""
  def sustituir_referencias(texto: str, variables: dict[str, str]) -> str:
      """Sustituye `&nombre` y `&nombre.` conocidas en una expresión del plan, sin distinguir
      mayúsculas; lo desconocido se deja y el intérprete lo rechaza con NoSoportadoEnInterprete."""
  ```
  `ejecutar_plan` lleva un `variables: dict[str, str]` por ejecución, lo llena en cada `set_variable` y lo pasa a la evaluación de expresiones posteriores.

**Caso `L5/l5_22_into_primer_fila_ascii` (`capa: B`, `estado: revisado`, razonamiento: «sqlproc, p. 312: INTO con varias filas toma la primera»).**
`programa.sas`:
```sas
PROC IMPORT DATAFILE='.../entradas/VALIDACION.csv' OUT=WORK.VALIDACION DBMS=CSV REPLACE; GETNAMES=YES; RUN;
PROC IMPORT DATAFILE='.../entradas/DATOS.csv' OUT=WORK.DATOS DBMS=CSV REPLACE; GETNAMES=YES; RUN;
PROC SQL;
SELECT ANIO INTO :ANIO FROM WORK.VALIDACION;
QUIT;
PROC SQL;
CREATE TABLE WORK.RES AS
SELECT ID, SALDO, &ANIO AS ANIO_CORTE FROM WORK.DATOS WHERE SALDO >= 100;
QUIT;
```
Entradas: `VALIDACION.csv` = `ANIO` / `2024` / `2025`; `DATOS.csv` = `ID,SALDO` / `1,150` / `2,80` / `3,100`. Esperado a mano: `ANIO` toma la primera fila, `2024`; `SALDO >= 100` deja los ids 1 y 3. `RES.csv` = `ID,SALDO,ANIO_CORTE` / `1,150,2024` / `3,100,2024`. Invariante: `filas(RES) == 2`.

- [ ] **Step 1: Medir.** `uv run python -m sgm.cli migrar tests/corpus/L5/l5_22_into_primer_fila_ascii/programa.sas --out out/e14 --muestra tests/corpus/L5/l5_22_into_primer_fila_ascii/entradas` (flags según `sgm migrar --help`) y anotar si el plan trae el `set_variable` y dónde queda el texto `&ANIO` (en la expresión del `map`).
- [ ] **Step 2: Write the failing tests** en `test_interprete_variables.py`: `valor_de_variable` con dos filas `[{"anio": "2024"}, {"anio": "2025"}]` y `column="ANIO"` devuelve `"2024"`; con `separator=","` devuelve `"2024,2025"`; sin filas, `None`; `sustituir_referencias("&ANIO AS A", {"anio": "2024"}) == "2024 AS A"`; `sustituir_referencias("&X.", {}) == "&X."`. El caso `l5_22` pasa en `test_migrar_corpus_anillo_b.py`.
- [ ] **Step 3: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_interprete_variables.py tests/unit/test_migrar_corpus_anillo_b.py -q -p no:cacheprovider -k "variables or l5_22 or l5_09"`.
- [ ] **Step 4: Implement** el módulo, el hilo de `variables` por `ejecutar_plan` y el caso. Quitar `l5_09` de `CONOCIDOS` solo si el paso 1 mostró que `&ANIO` llega al intérprete; `strict=True` lo obliga. Correr el anillo B completo, `tests/unit/test_migrar_interprete.py` y el golden (idénticos).
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N n: set_variable y &var en el interprete; l5_09 pasa en el anillo B`.

---

### Task E-15: `CALL EXECUTE` y código dinámico como pendiente con código estable (MG-D04; serie `n`)

Decisión MG-D04 del plan maestro: el código generado por datos no se traduce; es **pendiente con motivo** o se reescribe a mano. Hoy el expansor deja pasar `call execute` como una sentencia ordinaria dentro de un `DATA _NULL_`, sin motivo propio (`_ordinary` solo reconoce `call symput`). Regla: `CALL EXECUTE` empuja texto que SAS ejecuta después del paso (`mcrolref`, p. 311 «CALL EXECUTE Routine» y p. 139 «CALL EXECUTE Routine Timing Details»; `lefunctionsref`, p. 324 según `funciones-usadas.yaml`). Qué se genera depende de las filas de la tabla: sin ejecutar no se sabe.

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\frontend\macros_modelo.py` (`_CALL_EXECUTE = re.compile(r"(?i)\bcall\s+execute\s*\(")` y `_RESOLVE = re.compile(r"(?i)\b(resolve|dosubl)\s*\(")`)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\frontend\macros.py` (`_ordinary`: antes de `_SYMPUT`)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\motivos.py` (línea 52 y vecinas: registrar el código si la lista de motivos lo exige; verificar con `sed -n 40,70p src/sgm/motivos.py`)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\rules\sas\catalogo\funciones-usadas.yaml` (`call-execute-routine`: `estado: no_reconocida`, `nota` con el código y la forma de reescritura)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\docs\codigo-dinamico.md` (decisión MG-D04: el código `P-CODIGO-DINAMICO`, qué lo dispara y la forma de reescribir; una página)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\L5\l5_23_call_execute_pendiente\{caso.yaml, programa.sas, entradas\TABLAS.csv, entradas\VENTAS.csv, entradas\PAGOS.csv}` y `tests\corpus\L5\l5_24_call_execute_reescrito\{caso.yaml, programa.sas, entradas\VENTAS.csv, entradas\PAGOS.csv, esperado\R_VENTAS.csv, esperado\R_PAGOS.csv}`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_codigo_dinamico.py`

**Interfaces:**
- Consumes: `Expander._dynamic(stmt: Stmt, detail: str) -> MacroDynamic`.
- Produces: `MacroDynamic.detail == "P-CODIGO-DINAMICO: CALL EXECUTE genera código con los datos de la tabla; reescribir como una llamada directa por cada fila de la tabla de control"` (`RESOLVE` y `DOSUBL`: mismo código y su nombre). Código **estable**: no se cambia sin subir la versión del documento.

**Casos.** `l5_23_call_execute_pendiente` (`estado: parcial`, `motivo: P-CODIGO-DINAMICO`, sin `esperado/`: lo que se genera depende de los datos y no se calcula a mano). `programa.sas`:
```sas
PROC IMPORT DATAFILE='.../entradas/TABLAS.csv' OUT=WORK.TABLAS DBMS=CSV REPLACE; GETNAMES=YES; RUN;
PROC IMPORT DATAFILE='.../entradas/VENTAS.csv' OUT=WORK.VENTAS DBMS=CSV REPLACE; GETNAMES=YES; RUN;
PROC IMPORT DATAFILE='.../entradas/PAGOS.csv' OUT=WORK.PAGOS DBMS=CSV REPLACE; GETNAMES=YES; RUN;
%macro procesar(tabla=);
PROC SQL; CREATE TABLE WORK.R_&tabla. AS SELECT ID FROM WORK.&tabla.; QUIT;
%mend procesar;
DATA _NULL_;
  SET WORK.TABLAS;
  CALL EXECUTE(CATS('%nrstr(%procesar(tabla=', NOMBRE, '))'));
RUN;
```
Entradas: `TABLAS.csv` = `NOMBRE` / `VENTAS` / `PAGOS`; `VENTAS.csv` = `ID` / `1` / `2`; `PAGOS.csv` = `ID` / `3`. `l5_24_call_execute_reescrito` (`capa: B`, `estado: revisado`, razonamiento: «MG-D04: reescritura a mano a una llamada por fila; mcrolref, p. 311») es el mismo programa **sin** `TABLAS` ni `DATA _NULL_`, con `%procesar(tabla=VENTAS); %procesar(tabla=PAGOS);`. Esperado a mano: `R_VENTAS.csv` = `ID` / `1` / `2`; `R_PAGOS.csv` = `ID` / `3`. Invariantes: `filas(R_VENTAS) == 2`, `filas(R_PAGOS) == 1`. La reescritura solo es válida si la tabla de control es estática; el documento lo dice y la decisión es del equipo, no del traductor.

- [ ] **Step 1: Write the failing tests** en `test_codigo_dinamico.py`: con el programa de `l5_23`, `analyze_program` devuelve un `MacroDynamic` cuyo `detail` empieza por `P-CODIGO-DINAMICO` y **ningún** paso `CREATE TABLE R_*`; con `l5_24` salen `R_VENTAS` y `R_PAGOS` y cero dinámicos; `test_ningun_codigo_dinamico_se_traduce`: sobre `tests/fixtures/sas/p2_codigo_dinamico.sas`, el `call execute` de la línea 4 queda con ese código y `x '...'` y `systask` conservan su tratamiento actual (no se tocan aquí).
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_codigo_dinamico.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement** las dos expresiones y la rama de `_ordinary`; escribir `docs/codigo-dinamico.md` con el código, la regla y el ejemplo de reescritura (sin nombres de scripts del cliente). Agregar `l5_23` a `tests/corpus/migrar_pendientes.yaml` con `P-CODIGO-DINAMICO` **solo si** `test_solo_los_casos_listados_tienen_pendientes` recorre casos `parcial` (verificar: `sed -n 100,160p tests/unit/test_migrar_corpus_aceptacion.py`).
- [ ] **Step 4: Run tests to verify they pass**, `tests/unit/test_macros.py`, `tests/unit/test_catalogo_sas.py`, `tests/unit/test_migrar_corpus_aceptacion.py` y el golden.
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N n: CALL EXECUTE y codigo dinamico como pendiente P-CODIGO-DINAMICO (MG-D04)`.

---

## Parte V. Opciones del sistema que cambian resultados (MG-P7-07, 6 h)

### Task E-16: Detección y aviso de `MISSING=`, `YEARCUTOFF=`, `VALIDVARNAME=` y `MERGENOBY=` (serie `n`)

`docs/opciones-de-sistema.md` decide la regla y declara que **no está codificada**: el traductor no mira las sentencias `OPTIONS` en busca de estas cuatro. Páginas de `lesysoptsref.pdf` (existen en el `.txt`): `MERGENOBY` p. 265, `MISSING=` p. 266, `VALIDVARNAME=` p. 412, `YEARCUTOFF=` p. 432. Regla vigente (del documento): (1) un `OPTIONS` nunca se vuelve transformación; (2) si el programa fija una de las cuatro, el paso lleva `Pendiente:` con el nombre y la página, sin asumir el valor; (3) si no la fija, no se emite nada; (4) un informat de año de dos dígitos sin `YEARCUTOFF` fijado deja la columna con `Pendiente: fecha de dos dígitos sin YEARCUTOFF`.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\frontend\opciones_resultado.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\ir\lower.py` (línea 43, donde `OPTIONS` se vuelve `unsupported` con `reason: "CONFIGURACION"`: las cuatro salen con `reason: "OPCION_RESULTADO"`) y `src\sgm\motivos.py` (línea 52: registrar `OPCION_RESULTADO`)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\rules\sas\catalogo\opciones-resultado.yaml` (las cuatro entradas de `no_verificada` a `reconocida`; `nota` con el código)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\docs\opciones-de-sistema.md` (sección «Estado»: la regla ya está codificada; qué falta: el `autoexec` del cliente)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\L5\l5_25_missing_fijado_pendiente\{caso.yaml, programa.sas, entradas\DATOS.csv}` (`estado: parcial`, `motivo: P-OPCION-MISSING`; sin `esperado/`: con `MISSING=` fijado el valor de omisión del cliente no está en el repositorio y lo que SAS calcula no es demostrable)
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_opciones_resultado.py`

**Interfaces:**
- Consumes: `Stmt` (`lexer.py:76`) y `split_statements(src: str, *, file: str | None = None, line_start: int = 1) -> list[Stmt]`.
- Produces:
  ```python
  @dataclass(frozen=True)
  class OpcionDetectada:
      nombre: str      # "MERGENOBY" | "MISSING" | "VALIDVARNAME" | "YEARCUTOFF"
      valor: str; linea: int
      pagina: int      # página de lesysoptsref.pdf
      codigo: str      # "P-OPCION-<NOMBRE>"

  def detectar_opciones(stmts: list[Stmt]) -> list[OpcionDetectada]: ...
  def fechas_de_dos_digitos(stmts: list[Stmt], opciones: list[OpcionDetectada]) -> list[int]:
      """Líneas con un informat de año de dos dígitos (`yymmdd6.`, `mmddyy6.`, `date7.`) cuando
      el programa no fija YEARCUTOFF; el aviso es `P-FECHA-DOS-DIGITOS`."""
  ```

- [ ] **Step 1: Write the failing tests** en `test_opciones_resultado.py`: `detectar_opciones(split_statements("options mergenoby=error missing='X';"))` devuelve dos con `(nombre, valor, pagina)` = `("MERGENOBY", "error", 265)` y `("MISSING", "'X'", 266)`; `options validvarname=any yearcutoff=1940;` da `("VALIDVARNAME", "any", 412)` y `("YEARCUTOFF", "1940", 432)`; `options symbolgen nomprint;` da `[]` (diagnóstico: fontanería, no resultado); `fechas_de_dos_digitos` sobre `data a; input f yymmdd6.; run;` sin `YEARCUTOFF` da `[1]`, y con `options yearcutoff=1940;` antes da `[]`. Con `analyze_program`/`sgm migrar` de `l5_25`, el informe de pendientes trae `P-OPCION-MISSING` con `lesysoptsref.pdf, p. 266` y el paso no se emite como transformación.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_opciones_resultado.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement** con expresiones simples sobre `Stmt.text` (`^\s*options\b`; un `OPTIONS` con varias opciones se parte por blancos fuera de comillas). Las opciones de entorno y diagnóstico siguen como `CONFIGURACION` (no cambian). Actualizar el catálogo y el documento.
- [ ] **Step 4: Run tests to verify they pass**, `tests/unit/test_catalogo_sas.py` (las cuatro páginas están en `lesysoptsref.INDEX.md`: líneas 202, 203, 300 y 309), `tests/unit/test_migrar_corpus_aceptacion.py` (ningún caso del corpus fija estas opciones: ninguno cambia) y el golden.
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N n: deteccion y aviso de las cuatro opciones del sistema que cambian resultados`.

---

## Parte VI. Huecos del analizador (MG-P7-05, 12 h; el `%IF` con parámetro ya está en E-5)

### Task E-17: `PROC DOWNLOAD` dentro de `RSUBMIT` con lectura y escritura (serie `n`)

Hueco H1 de `tests/corpus/HUECOS_FRONTEND.md`: `PROC DOWNLOAD INFILE='<origen>' OUTFILE='<destino>'` queda como paso `proc` sin lectura ni escritura, y el linaje pierde el origen real del archivo (ocurrencias en `tests/corpus/L8/validaciones/v01_tipo_doc` líneas 49 y 62, y los otros siete programas; `v03` trae cuatro dentro de un mismo `RSUBMIT`). Páginas: `connref.pdf`, «Tips for Using PROC DOWNLOAD Only» (p. 117, entrada del índice); la entrada «DOWNLOAD Procedure» y su página exacta **verificar al ejecutar** con `grep -n -i "DOWNLOAD Procedure" docs/referencia/sas/connref.INDEX.md` (el `UPLOAD Procedure` está en p. 245); si no hay entrada, `fuente` cita p. 117.

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\facts\structural.py` y `src\sgm\facts\textual.py` (ya tratan `UPLOAD`: ubicar con `grep -n -i upload src/sgm/facts/*.py` y agregar `DOWNLOAD` con la lectura de `INFILE=` y la escritura de `OUTFILE=`)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\HUECOS_FRONTEND.md` (H1: marcar resuelto con el hito)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\rules\sas\catalogo\procs-usados.yaml` (entrada de `PROC DOWNLOAD`, o la que corresponda)
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_proc_download.py`

**Interfaces:**
- Consumes: `build_flows(...)` (`src/sgm/flow/model.py:284`; firma exacta: `sed -n 284,300p src/sgm/flow/model.py`), `FlowStep`.
- Produces: el paso `PROC DOWNLOAD` trae `reads = [<INFILE>]` y `writes = [<OUTFILE>]` como archivos externos (no tablas); no inventa un esquema. El **efecto** (copia local) lo define el Plan K (K-5, `RSUBMIT`/`UPLOAD`/`DOWNLOAD` como copias locales): aquí solo el linaje.

**Caso:** sin caso de datos nuevo (no transforma filas); el caso es el hueco medido: los ocho programas de `L8/validaciones` (con `PROC DOWNLOAD` en las líneas de H1) y `tests/fixtures/sas/client/client_poc.sas` si lo contiene.

- [ ] **Step 1: Write the failing test** en `test_proc_download.py`: `PROC DOWNLOAD INFILE='/remoto/a.csv' OUTFILE='/local/a.csv'; RUN;` dentro de `RSUBMIT; ... ENDRSUBMIT;` da un paso con `reads == ["/remoto/a.csv"]` y `writes == ["/local/a.csv"]`; para `tests/corpus/L8/validaciones/v03_pais_dane/programa.sas`, las cuatro descargas (líneas 88, 90, 103 y 105) aparecen con su origen como entrada externa.
- [ ] **Step 2: Run test to verify it fails.** `uv run python -m pytest tests/unit/test_proc_download.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement** y correr `build_flows` sobre los ocho programas: ninguno lanza excepción y ninguno pierde el origen.
- [ ] **Step 4: Run tests to verify they pass**, las pruebas de `facts` y de `flow` (`ls tests/unit | grep -i "facts\|flow"`) y el golden de linaje.
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N n: PROC DOWNLOAD con origen y destino en el linaje`.

---

### Task E-18: Tablas de `WORK` «leídas antes de crearse» y macros de SAS Studio sin definición (contrato con K-6; serie `n`)

`PROGRESS.md` (línea 1382) anota «3 WORK que se leen antes de crearse (`SABANA_SIN_*`): no se investigó cómo se crean (probablemente macro dinámica)». En `tests/corpus/L8/validaciones/v08_nequi_cadena/programa.sas` la tabla aparece primero como argumento de `%web_drop_table(WORK.SABANA_SIN_VACIOS_NEQUI);` (línea 189), luego se crea (línea 194) y se abre con `%web_open_table(...)` (línea 202). Hipótesis a confirmar en el paso 1: el argumento de una llamada a macro **no definida en el proyecto** se cuenta como lectura. Las dos macros son de SAS Studio y no tienen definición en el repositorio ni página en `mcrolref`: sin página, no hay equivalencia (`Pendiente: P-MACRO-STUDIO`).

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\proceso\entradas_salidas.py` (donde el linaje reparte entradas; verificar con `grep -n "SABANA\|externas" src/sgm/proceso/entradas_salidas.py | head`)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\frontend\macros.py` (`_block`: llamada a una macro que el índice no conoce)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_validaciones_sas.py` (la prueba existente referencia `SABANA_SIN`: se endurece, no se debilita)
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_macro_no_definida.py`

**Interfaces:**
- Consumes: `MacroIndex.get(name: str)` (devuelve `None` si no está definida), `Expander._dynamic`.
- Produces: una llamada `%nombre(...)` a una macro sin definición produce `MacroDynamic` con `detail == "P-MACRO-STUDIO: %<nombre> es una macro de SAS Studio sin definición en el proyecto; no se asume su efecto"` cuando el nombre empieza por `web_`, y `"P-MACRO-NO-DEFINIDA: ..."` en otro caso; sus argumentos **no** cuentan como lecturas de tablas. Ningún Job se emite con efectos supuestos: `%web_drop_table` (borra una tabla) y `%web_open_table` (la muestra) quedan pendientes.

**Caso `L5/l5_26_macro_studio_pendiente` (`estado: parcial`, `motivo: P-MACRO-STUDIO`; sin `esperado/` de la macro: no hay página; sí una salida para lo que la rodea).** `programa.sas`:
```sas
PROC IMPORT DATAFILE='.../entradas/DATOS.csv' OUT=WORK.DATOS DBMS=CSV REPLACE; GETNAMES=YES; RUN;
%web_drop_table(WORK.RES);
PROC SQL; CREATE TABLE WORK.RES AS SELECT ID FROM WORK.DATOS WHERE ID > 1; QUIT;
%web_open_table(WORK.RES);
```
Entrada `DATOS.csv`: `ID` / `1` / `2` / `3`. La tabla `RES` (ids 2 y 3) se calcula a mano y va en `esperado/RES.csv` **como referencia de lo que no depende de las macros**; el caso sigue `parcial` hasta que el usuario decida si una llamada pendiente deja traducible el resto del programa (decisión de producto, se anota en `PROGRESS.md`).

- [ ] **Step 1: Medir.** `uv run python -m sgm.cli proceso` o `build_flows` sobre `v08_nequi_cadena` (flags según `--help`) y anotar si `SABANA_SIN_VACIOS_NEQUI` aparece como entrada externa y por qué. Si la causa no es la hipótesis, anotar la causa real en `PROGRESS.md` y ajustar `Produces` antes de seguir.
- [ ] **Step 2: Write the failing tests** en `test_macro_no_definida.py`: `analyze_program({"p.sas": "%web_drop_table(WORK.X);\ndata o; set s; run;"})` trae un `MacroDynamic` con `detail` que empieza por `P-MACRO-STUDIO` y `WORK.X` no aparece como lectura en `build_flows`; `%otra(1);` da `P-MACRO-NO-DEFINIDA`; una macro definida en el mismo programa sigue expandiéndose (sin cambio).
- [ ] **Step 3: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_macro_no_definida.py -q -p no:cacheprovider`.
- [ ] **Step 4: Implement** y correr `tests/unit/test_validaciones_sas.py`, las pruebas de flujo, el golden y `uv run python -m pytest tests/unit/test_no_script_specific_names.py -q -p no:cacheprovider`. Contrato con K-6: el programa pequeño trae `%web_drop_table` y `%web_open_table` en su rebanada; ambas quedan como `P-MACRO-STUDIO` y la rebanada migra sin ellas (K-6, paso 1, los cuenta).
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N n: macros de SAS Studio sin definicion como pendiente; sus argumentos no son lecturas`.

---

### Task E-19: `sql_tree` con subconsultas en `FROM` (serie `n`)

`ir/sql_tree.py` lanza `SqlNotSelect("origen que no es una tabla")` ante una subconsulta en `FROM` (`docs/plan-reescritura/fase0-auditoria-reuso.md`, líneas 81 y 121); el lowering deja el paso como hueco. Regla: una tabla derivada es una consulta con nombre propio que se evalúa antes de la externa (`sqlproc`, «Query Expressions» y «In-Line Views»: **verificar al ejecutar** con `grep -n -i "in-line view" docs/referencia/sas/sqlproc.INDEX.md` y citar la página; sin entrada, `Pendiente: P-SUBCONSULTA-EN-FROM` y el caso queda `parcial`). La solución elegida es **desanidar** en pasos intermedios, que el lowering ya sabe traducir uno por uno, en vez de agregar un tipo de nodo nuevo al plan.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\ir\sql_desanidar.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\ir\sql_tree.py` (`build`, línea 299: ante una subconsulta en `FROM` lanza `SqlNotSelect` con un mensaje que nombra `desanidar`) y el llamador de `build` en el lowering (ubicar con `grep -n "sql_tree" src/sgm/ir/*.py`)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\L5\l5_27_subconsulta_en_from\{caso.yaml, programa.sas, entradas\VENTAS.csv, esperado\RES.csv}` (va en `L5` solo por reservar numeración; si el Plan C prefiere `L3`, se mueve sin cambiar el contenido)
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_sql_desanidar.py`

**Interfaces:**
- Consumes: `build(sql: str) -> SqlTree` (`sql_tree.py:299`), `SqlNotSelect`, `sqlglot` (ya es dependencia de `sql_tree.py`).
- Produces:
  ```python
  def desanidar(sql: str) -> list[tuple[str | None, str]]:
      """Lista ordenada de (nombre_temporal, select) para una consulta con tablas derivadas en
      FROM: primero cada derivada (nombrada `__sub<n>` en WORK), al final la externa con el
      nombre en lugar de la subconsulta y el destino original (None). Sin derivadas devuelve
      [(None, sql)]. Las derivadas anidadas se resuelven de adentro hacia afuera."""
  ```
  El alias de la derivada se conserva (`FROM __sub1 t`). Las subconsultas de `WHERE` (`IN`, `EXISTS`, escalares) **no** se tocan: son del Plan C (C-8 y C-9).

**Caso `L5/l5_27_subconsulta_en_from` (`capa: B`, `estado: revisado`, razonamiento: «sqlproc: tabla derivada; el agregado se evalúa antes del filtro externo»).**
`programa.sas`:
```sas
PROC IMPORT DATAFILE='.../entradas/VENTAS.csv' OUT=WORK.VENTAS DBMS=CSV REPLACE; GETNAMES=YES; RUN;
PROC SQL;
CREATE TABLE WORK.RES AS
SELECT t.PRODUCTO, t.TOTAL
FROM (SELECT PRODUCTO, SUM(MONTO) AS TOTAL FROM WORK.VENTAS GROUP BY PRODUCTO) t
WHERE t.TOTAL > 10;
QUIT;
```
Entrada `VENTAS.csv`: `PRODUCTO,MONTO` / `A,10` / `A,20` / `B,5` / `B,1` / `C,30`. Esperado a mano: totales `A = 30`, `B = 6`, `C = 30`; el filtro externo `TOTAL > 10` quita a `B`. `RES.csv` = `PRODUCTO,TOTAL` / `A,30` / `C,30`. Invariante: `filas(RES) == 2`.

- [ ] **Step 1: Write the failing tests** en `test_sql_desanidar.py`: `desanidar("SELECT t.p FROM (SELECT p FROM a) t")` da `[("__sub1", "SELECT p FROM a"), (None, "SELECT t.p FROM __sub1 t")]` (formato exacto del texto: lo que devuelva `sqlglot` con `.sql()`; el test compara tras normalizar espacios y mayúsculas); `desanidar("SELECT 1 FROM a")` da `[(None, "SELECT 1 FROM a")]`; con dos niveles, el más interno sale primero (`__sub1`) y el medio es `__sub2`. El caso `l5_27` pasa en el anillo B.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_sql_desanidar.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement** con el árbol de `sqlglot` (`exp.Subquery` dentro de `exp.From` o `exp.Join`), sin regex sobre SQL. Hacer que el lowering llame a `desanidar` cuando `build` rechaza por subconsulta en `FROM`; cada intermedio es un `CREATE TABLE WORK.__subN`.
- [ ] **Step 4: Run tests to verify they pass**, `tests/unit/test_golden.py`, `tests/unit/test_ir_operadores_corpus.py` y `tests/unit/test_migrar_corpus_anillo_b.py -k "l5_27"`. Si el anillo B falla por el agregado, la dependencia es C-6 (Plan C): marcar `xfail(strict=True)` con ese motivo.
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N n: subconsultas en FROM desanidadas en pasos intermedios`.

---

## Task E-Gate: L5 completo en el anillo B y en el lote C (serie `n`)

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\docs\plan-reescritura\plan-migrador-general.md` (fila `MG-P7 Macros` de §11b)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\PROGRESS.md` (entrada del hito)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\migrar_pendientes.yaml` (solo lo que el lote muestre)

**Interfaces:**
- Consumes: `tools/corpus_studio.py lote ...` y `tools/validar_caso_studio.py <caso>` (salida esperada `N casos, N coinciden`).
- Produces: la fila de MG-P7 recalculada con su método: horas acreditadas = horas de tareas E cerradas con evidencia (`L5` en B y en C), no estimación.

- [ ] **Step 1: Anillo B.** `uv run python -m pytest tests/unit/test_migrar_corpus_anillo_b.py -q -p no:cacheprovider -k L5`: **todos** los casos `traducible` y `revisado` de L5 pasan y `CONOCIDOS` ya no contiene ninguno de L5 (los 12 originales más `l5_13` a `l5_22` y `l5_24` y `l5_27`). Los casos `parcial` (`l5_21`, `l5_23`, `l5_25`, `l5_26`) no se ejecutan y cada uno tiene su `motivo` y su código.
- [ ] **Step 2: Lote C (Studio).** `uv run python -m sgm.cli studio salud`; si conecta, `uv run python tools/corpus_studio.py lote --corpus tests/corpus --nivel L5` (flags según `--help`) y `uv run python tools/validar_caso_studio.py l5_15_indirecta_doble_ampersand` para el desenrollado. Esperado: todos los casos de L5 que el anillo A traduce coinciden. Casos que el anillo A no traduce hoy y por qué: `l5_09_into_primer_fila` (`P-ESQUEMA-NO-PORTABLE`, nombre de columna `AÑO`) queda en `migrar_pendientes.yaml` con su motivo, y `l5_22` (su gemelo ASCII) lo cubre; `l5_09` y `l5_22` piden además `tSetGlobalVar` y un disparador `OnSubjobOk` entre dos subjobs (`PROGRESS.md`, hito 121): si el emisor no lo tiene, `l5_22` queda «lote C pendiente: set_variable sin emisor (Plan C, MG-P5-07, y Plan F2, F2-14)» y **no se cuenta como pasado**. Si Studio no conecta: «lote C pendiente» con el motivo de `sgm studio salud`, sin reinstalar nada.
- [ ] **Step 3: Cierre de cifras.** Escribir en `PROGRESS.md` la entrada `## Hito N n. Macros: L5 completo en B y en lote C` con: fecha, qué se hizo (E-1 a E-19), pruebas (suite y `ruff`), métricas (casos de L5 en B y en C, `P-xxx` nuevos con su documento), bloqueos (lo que quedó «lote C pendiente») y «Decisiones» (reglas de `%STR`/`%NRSTR`, alcance, `%IF` compuesto, destino de variables de ejecución, desanidado de `FROM`). Recalcular la fila de MG-P7 en §11b con las horas acreditadas por evidencia.
- [ ] **Step 4: Run** `uv run python -m pytest -q` (suite completa, una vez) y `uv run ruff check src tests tools`; el golden y `test_ir_operadores_corpus.py` idénticos.
- [ ] **Step 5: Commit** `hito N n: E-Gate, macros: L5 completo en B y lote C`.

---

## Dependencias

- **Plan A** (`tools/ci.py`, `tools/validacion.py`, `tools/instalar_ganchos.py`, `.githooks/`): no se tocan. `tools/validar_caso_studio.py` es del Plan A; este plan solo lo ejecuta.
- **Plan B** (datastep y plan lógico): `PROC APPEND` como operador (B-8) es lo que pasa `l5_21` de `parcial` a `revisado`; MG-P4-08 (`CALL SYMPUT`) usa `VariableEjecucion(origen="symput")` de E-13. `src/sgm/migrar/interprete.py` lo extraen también B y C: E-14 solo agrega `interprete_variables.py` y un hilo en `ejecutar_plan`; quien llegue segundo hace rebase.
- **Plan C** (SQL y procedimientos): el `set_variable` de `SELECT INTO` ya existe en `lower_sql_flow.py` (MG-P5-07); E-14 consume su forma. E-19 puede depender de C-6 (agregados) para que `l5_27` pase en B. E-19 toca el llamador de `sql_tree.build` dentro del lowering de SQL (zona de C: coordinar el orden).
- **Plan D2** (entrada y salida): E-17 (`PROC DOWNLOAD`) y K-5 comparten `RSUBMIT`; E-17 solo el linaje.
- **Plan F1/F2** (joblets, contextos): F1 consume el informe de E-10 (`informe_a_dict`, `version: 1`); F2-11 consume `candidatas_a_contexto` de E-13. El escritor de joblets (F2-8 a F2-10) no existe aún: E-10 no lo necesita.
- **Plan K** (datos de prueba): K-6 consume `Iteracion` y el desenrollado de 15 vueltas (E-11), y las llamadas `P-MACRO-STUDIO` (E-18); K-6 paso 1 mide los `PROC APPEND`. `tests/corpus_reales/` lo crea K-6: este plan no lo toca.
- **Archivos que crea este plan y que otro modifica**: `src/sgm/frontend/repeticiones.py` (E-10), `macros_ejecucion.py` (E-13) y `opciones_resultado.py` (E-16) son nuevos aquí; ningún `Modify` apunta a algo que cree otro plan salvo `interprete_uniones.py` y `lower_sql_uniones.py` del Plan C, que **este plan no toca**.
- Dentro del plan: E-5 antes de E-7 (`evaluar_condicion`); E-3 antes de E-9 (valuado de argumentos); E-7 antes de E-11 (registro por vuelta); E-10 antes de E-11 y E-12; E-13 después de E-7; E-14 después de E-13 solo por contrato (no por código).

## Self-review

- **Cobertura del plan maestro:** MG-P7-01 en E-1 a E-8 (`%LET`, `&var`, `&&var&i`, `%MACRO` con parámetros, `%IF`, `%DO` con y sin límites constantes, `%EVAL`, `%SYSFUNC`, citado); MG-P7-02 en E-10 a E-12; MG-P7-03 en E-9; MG-P7-04 en E-13 y E-14; MG-P7-05 en E-5 (el `%IF`), E-17, E-18 y E-19; MG-P7-06 en E-15; MG-P7-07 en E-16. El patrón del programa pequeño del cliente (bucle `%DO` con `PROC APPEND`, `%web_*`) en E-11 y E-18.
- **Cifras medidas, no copiadas:** el plan maestro dice «8 de 12»; hoy son 10 de 12 en B (dos `xfail`: `l5_08` y `l5_09`) y 11 de 12 en A. E-1 lo corrige. El usuario habló de «4 de 12»: la medición no lo respalda; si al ejecutar E-1 aparecen cuatro, se anota cuáles.
- **Páginas:** todas las de `mcrolref` y `lesysoptsref` citadas existen en el `.txt` (comprobadas con el marcador). Quedan **por verificar al ejecutar**: la frase de `%EVAL` sobre `/` y sobre `%EVAL(3>2)` (E-6), la página 161 y 162 de `proc.pdf` (E-11), «primera fila» en `sqlproc` p. 312 (E-14), la entrada «DOWNLOAD Procedure» de `connref` (E-17) y «In-Line View» de `sqlproc` (E-19). Cada una dice qué hacer si no está: `Pendiente:` con su código.
- **Esperados a mano:** cada caso trae su SAS completo, entradas y esperado calculado: `l5_13` (ids 1 y 5), `l5_14` (1 y 4), `l5_15` (`COPIA_1`/`2`/`3` con 2, 1 y 3 filas), `l5_16` (`OK` 1,2 y `NO` 3), `l5_17` (4 a 7), `l5_18` (`T_1`, `T_2`, `T_3`), `l5_19` (3 y 4), `l5_20` (3, 2 y 1 filas), `l5_21` (7 filas), `l5_22` (ids 1 y 3 con 2024), `l5_24` (`R_VENTAS` 1,2; `R_PAGOS` 3), `l5_27` (A 30, C 30).
- **Riesgos abiertos:** (1) `l5_09` y `l5_22` no pasan el lote C sin `tSetGlobalVar` y el disparador entre subjobs; (2) `E-8` puede cambiar la expansión de programas del corpus que dependían del alcance incorrecto: se revisa el diff a mano; (3) los números de caso `l5_13` a `l5_29` están reservados; si otro plan toma uno, se toma el siguiente libre; (4) `l5_21`, `l5_23`, `l5_25` y `l5_26` son `parcial` y por eso no cuentan para la compuerta; la compuerta no los esconde: cada uno está listado con su motivo.
- **Consistencia de nombres:** `evaluar_condicion` (E-5, usada en E-7), `Invocacion`/`BloqueRepetido`/`detectar_repeticiones`/`informe_a_dict` (E-10, usados en E-11 y E-12), `Iteracion` (E-11), `VariableEjecucion`/`CandidataContexto` (E-13), `valor_de_variable`/`sustituir_referencias` (E-14), `OpcionDetectada`/`detectar_opciones` (E-16), `desanidar` (E-19). Códigos `P-` nuevos: `P-MACRO-COMILLA-SUELTA`, `P-MACRO-BUCLE-NO-CONSTANTE`, `P-MACRO-RECURSION`, `P-INCLUDE-NO-RESUELTO`, `P-EVAL-DIVISION`, `P-CODIGO-DINAMICO`, `P-OPCION-<NOMBRE>`, `P-FECHA-DOS-DIGITOS`, `P-MACRO-STUDIO`, `P-MACRO-NO-DEFINIDA`, `P-INTO-VARIAS-FILAS`, `P-SUBCONSULTA-EN-FROM`.

## Resumen de horas

| Tarea | Tarea del plan maestro | Horas |
|---|---|---|
| E-1 Línea base, paridad y catálogo | MG-P7-01 | 2 |
| E-2 `%STR` y `%NRSTR` | MG-P7-01 | 2 |
| E-3 `%SYSFUNC` | MG-P7-01 | 2 |
| E-4 `&&var&i` | MG-P7-01 | 3 |
| E-5 `%IF` compuesto y `%LENGTH` | MG-P7-01 y MG-P7-05 | 2 |
| E-6 `%EVAL` | MG-P7-01 | 1,5 |
| E-7 `%DO %WHILE` y `%UNTIL` | MG-P7-01 | 2 |
| E-8 Alcance de variables | MG-P7-01 | 1,5 |
| E-9 Autollamadas y `%INCLUDE` | MG-P7-03 | 4 |
| E-10 Informe de repeticiones | MG-P7-02 | 4 |
| E-11 Bucles y `APPEND` | MG-P7-02 | 4 |
| E-12 Informe sobre el repositorio | MG-P7-02 | 2 |
| E-13 Variables de ejecución | MG-P7-04 | 3 |
| E-14 `set_variable` en el intérprete | MG-P7-04 | 5 |
| E-15 `CALL EXECUTE` | MG-P7-06 | 4 |
| E-16 Opciones del sistema | MG-P7-07 | 6 |
| E-17 `PROC DOWNLOAD` | MG-P7-05 | 4 |
| E-18 WORK y macros de Studio | MG-P7-05 | 4 |
| E-19 Subconsultas en `FROM` | MG-P7-05 | 4 |
| E-Gate | cierre | (incluido: 2 h dentro de las anteriores) |
| **Suma de estimaciones** | | **60** |

La suma de las tareas es **60 h brutas**, igual al total de MG-P7 del plan maestro (16 + 10 + 4 + 8 + 12 + 4 + 6). Las **52 h netas** del encargo son 60 menos las 8 h que el plan maestro ya acredita (`%LET`, macros con parámetros, `%EVAL` y `%SYSFUNC(UPCASE)`: los casos de L5 que ya pasan). Esas 8 h salen de MG-P7-01: no hay una tarea que las contenga entera, se reparten en que E-3 (la parte `UPCASE`), E-6 (`+ - *`) y E-8 (parte del paso de parámetros) parten de código que ya funciona; al cerrar cada una se acredita solo lo que su evidencia (caso en B y en C) demuestre, y el total neto de 52 h se confirma en la entrada del E-Gate, no antes. El E-Gate no suma horas propias: está incluido en las de E-1 (cifras) y en el cierre de cada tarea.
