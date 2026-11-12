# MG-B: DATA step y plan lógico Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Que el plan lógico se construya por constructores validados para todo el corpus `traducible`, con esquemas de tipos demostrados, y que el DATA step de L6 (`OUTPUT`, `SET` de varios datasets, `MERGE`, estado por fila, `ARRAY`/`DO`, `UPDATE`) tenga semántica SAS real en el intérprete (anillo B), traducción en `sgm migrar` (anillo A) y una validación en Studio (anillo C), cerrando MG-P1 y MG-P4.

**Architecture:** Cambios solo en `sgm-v2` (Python), en tres zonas: `src/sgm/ir/` (constructores y lowering), `src/sgm/migrar/` (intérprete de referencia y esquemas) y `src/sgm/talend_item/` (emisor desde el plan). El estado por fila (`RETAIN`, `FIRST.`/`LAST.`, `LAG`, sentencia suma) y `MERGE` no se emiten como `JOIN`: llevan un operador propio con la semántica del PDV, y el emisor lo convierte en `tSortRow` + `tJavaRow` con estado. Los casos de `OUTPUT` salen de un generador de combinaciones, no de un hito por variante.

**Tech Stack:** Python 3.12, pytest, ruff; `uv run python -m pytest` y `uv run python -m sgm.cli` (en este Windows `uv run pytest` puede bloquearse por Control de aplicaciones).

**Spec:** `docs/plan-reescritura/plan-migrador-general.md` (MG-P1-02 a MG-P1-06, MG-P4-01 a MG-P4-09, secciones 4, 5.2 y 11b) y `docs/superpowers/plans/2026-11-11-ruta-al-100.md`.

**Horas del plan maestro cubiertas:** MG-P1 restante 32,5 h (70 h menos los 37,5 h acreditados en el hito 140m) + MG-P4 restante 69 h = 101,5 h.

## Global Constraints

- Sin `git push`. Un commit local por hito: `hito N<m>: <resumen>` (letra `m`, carril de Andres). Antes de escribir, buscar el último `## Hito` de `PROGRESS.md` (al redactar este plan era el 198) y sumar uno; si otra sesión ya tomó el número, tomar el siguiente. No renumerar entradas publicadas.
- No tocar `tools/ci.py`, `tools/validacion.py`, `README.md` ni `.githooks/` (son del Plan A y están sin commitear).
- Nada de nombres de scripts de ejemplo (`cod1`, `cod2`, `cars_poc`, `exogena`, `split2`, `split3`, `executeBulkload`, `waitForBulkLoads`, `bulkload_generic`) en `src/` ni `rules/`; lo vigila `tests/unit/test_no_script_specific_names.py`.
- Si el SAS no demuestra un tipo, una columna, un valor o una equivalencia: `Pendiente:` con motivo y código `P-xxx`. Nunca un valor supuesto.
- Si no hay página de la guía SAS, no hay equivalencia. Cada regla nueva cita `<guía>, p. N` con una página que exista en `docs/referencia/sas/<guía>.INDEX.md`; `tests/unit/test_catalogo_sas.py` lo vigila. No leer el PDF ni el `.txt` entero: ubicar la sección en el `.INDEX.md` y la página con `grep -n "<!-- página N -->" docs/referencia/sas/<guía>.txt`.
- No borrar ni debilitar pruebas. Un caso que no se puede traducir queda en `tests/corpus/migrar_pendientes.yaml` con su motivo, no se quita del corpus.
- Archivos de menos de 300 líneas. Ya pasan de 300: `src/sgm/ir/lower_data.py` (770), `src/sgm/migrar/interprete.py` (1103) y `src/sgm/talend_item/desde_plan_map.py` (815). Toda tarea que los toca extrae primero el bloque a un módulo nuevo en un paso propio y sin cambio de comportamiento (la suite y el golden deben quedar idénticos).
- Código e identificadores en inglés (los nombres de operadores de `operadores.py` están en español y se conservan); comentarios, docstrings y mensajes en español.
- Después de cada tarea: `uv run python -m pytest -q` y `uv run ruff check .` en verde.
- Studio: se usa en tres puntos y nada más: la investigación de `SET` (B-9), el lote de `OUTPUT` (B-18) y el lote de cierre (B-Gate). Si `sgm studio salud` no conecta, no reinstalar nada ni cambiar `talend-mcp` (ver `docs/guia-validacion-studio.md`, sección 7); la validación queda pendiente con su motivo y no se cuenta como pasada.

## Review Focus

- `MERGE` no es un `JOIN`: con claves repetidas en ambos lados el resultado es la suma de los máximos por grupo (`lrcon`, p. 597 a 601; `lestmtsref`, p. 243). Test en B-11 con `l6_02`.
- El faltante numérico es menor que cualquier número y el texto en blanco es faltante (`lrcon`); una comparación con `null` en Java no puede lanzar. Test en B-13 y B-20.
- Estado por fila (`RETAIN`, sentencia suma) reinicia por grupo solo donde SAS lo hace: la sentencia suma retiene y arranca en 0; `RETAIN x;` sin valor arranca en faltante (`lestmtsref`, p. 331 y 360). Test en B-13.
- Un Job parcial nunca se emite: si una combinación de `OUTPUT` o una unión no se puede demostrar, el paso queda como pendiente con código y el caso en `migrar_pendientes.yaml`. Test en B-12, B-15 y B-17.
- Ningún pase nuevo puede cambiar la firma de los Jobs ya validados en L0 a L3 (los `test_golden*.py` y `test_ir_operadores_corpus.py` deben seguir idénticos).

---

## Parte I. MG-P1 restante (32,5 h)

### Task B-1: Línea base medida de MG-P1 y L6

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\linea_base_plan_logico.py`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_linea_base_plan_logico.py`

**Interfaces:**
- Produces:
  ```python
  def medir(corpus: Path) -> dict:
      """Por caso `traducible` de L0 a L8: pasos del SAS, operadores del plan, operadores
      construidos con `ir/operadores.py`, pendientes por código, y coincidencia en el anillo B."""
  ```
  Salida JSON en `out/linea_base_plan_logico.json` (no versionada).

- [ ] **Step 1: Write the failing test.** Con un corpus mínimo en `tmp_path` (un caso `L0` con `SET` y `WHERE`), `medir` devuelve `{"casos": 1, "operadores": N, "construidos_por_constructor": M, "pendientes": {}}` con `M <= N`. Un caso con `MERGE` no soportado debe sumar `P-UNION-TIPO-SIN-SOPORTE` en `pendientes`.
- [ ] **Step 2: Run test to verify it fails.** `uv run python -m pytest tests/unit/test_linea_base_plan_logico.py -q`; esperado: no existe el módulo.
- [ ] **Step 3: Implement.** Reutilizar `sgm.migrar` (la misma ruta que `tests/unit/test_corpus_esquemas_migrar.py`) y contar un operador como «construido» cuando su `params` es idéntico al que devuelve el constructor homónimo de `sgm.ir.operadores` (la comparación que ya hace `tests/unit/test_ir_operadores_corpus.py`).
- [ ] **Step 4: Run test to verify it passes** y ejecutar `uv run python tools/linea_base_plan_logico.py` sobre `tests/corpus`; pegar las cifras (casos, % construidos por constructor, pendientes por código, casos de L6 que coinciden en B) en `PROGRESS.md` como línea base de este plan.
- [ ] **Step 5: Commit.** `hito N m: linea base medida del plan logico y de L6`.

---

### Task B-2: Tipos de columna demostrados por `PROC IMPORT` (MG-P1-02, parte 1)

Hoy `esquemas_de_entrada` (`src/sgm/migrar/esquemas.py`, `esquemas_tipos.py`) deduce nombres de columna de `PROC IMPORT` pero, sin catálogo, sale `String` con `P-TIPO-DESCONOCIDO`. SAS decide el tipo de cada columna de un `PROC IMPORT` leyendo las primeras `GUESSINGROWS=` filas (20 por omisión): esa regla sí es demostrable con la muestra.

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\esquemas_tipos.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\tipos_import.py`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_tipos_import.py`

**Interfaces:**
- Produces:
  ```python
  def tipo_desde_muestra(valores: list[str], guessingrows: int = 20) -> TipoDemostrado | None:
      """`numerico` si todos los valores no vacíos de las primeras `guessingrows` filas son
      numéricos; `caracter` si alguno no lo es; `None` si la muestra no alcanza (sin filas)."""
  ```
  `TipoDemostrado` lleva `tipo_sas`, `fuente` (`"PROC IMPORT, GUESSINGROWS=<n>"`) y `evidencia` (filas leídas).

**Fuente SAS:** la sección de `PROC IMPORT` y `GUESSINGROWS=` en `proc.pdf` (el catálogo `rules/sas/catalogo/procs-usados.yaml` la cita en p. 1373). Localizarla con `grep -n "GUESSINGROWS" docs/referencia/sas/proc.txt | head`, leer solo esa página y citar `proc.pdf, p. N` en el docstring.

- [ ] **Step 1: Write the failing test.** Tabla de columnas: `["1","2","3"]` es numérico; `["1","x"]` es carácter; `["", ""]` es `None` (no se inventa tipo); una columna con 25 filas donde la fila 22 es texto y `guessingrows=20` sigue siendo numérica **y queda marcada `P-TIPO-FUERA-DE-MUESTRA`** (SAS tampoco la vería; el riesgo se anota, no se oculta).
- [ ] **Step 2: Run test to verify it fails.**
- [ ] **Step 3: Implement** `tipo_desde_muestra`; en `esquemas_tipos.py` llamarla cuando el programa trae la muestra (`--muestra`) y no hay tipo de `LENGTH`/informat/catálogo. Orden de prioridad de las fuentes de tipo: catálogo del entorno, `LENGTH`/`INPUT`/`FORMAT`, muestra de `PROC IMPORT`, `String` con `P-TIPO-DESCONOCIDO`.
- [ ] **Step 4: Run** `uv run python -m pytest tests/unit/test_tipos_import.py tests/unit/test_corpus_esquemas_migrar.py -q`. El conteo de `P-TIPO-DESCONOCIDO` en el corpus debe bajar o quedar igual, nunca subir.
- [ ] **Step 5: Commit.** `hito N m: tipos de PROC IMPORT demostrados por la muestra`.

---

### Task B-3: Tipos desde `INPUT`, `LENGTH`, `FORMAT`, `ATTRIB`, `CREATE TABLE`, `SELECT` y `SET` (MG-P1-02, parte 2)

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\esquemas.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\esquemas_propagacion.py`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_esquemas_propagacion.py`

**Reglas con página (verificar cada una en el `.INDEX.md` y citar):**
- Tipo de una variable creada por asignación: `lrcon`, «Create a New Variable Using an Assignment Statement» (p. 69); creada por `LENGTH`/`ATTRIB`/`FORMAT`/`INFORMAT`: `lrcon` p. 68 y 73.
- Conversión de tipo y sus avisos: `lrcon`, «Variable Type Conversions» (p. 75).
- `SET a b`: el tipo y el largo de una variable que viene de varios datasets lo fija el primero que la define (`lestmtsref`, `SET Statement`, p. 343); si el segundo trae otro tipo SAS emite error, y la regla aquí es pendiente `P-UNION-TIPO-CONFLICTO` con ambos orígenes.
- `CREATE TABLE ... AS SELECT`: tipo de una columna calculada según `sqlproc` (buscar «CREATE TABLE» y «column modifiers» en `sqlproc.INDEX.md`).

- [ ] **Step 1: Write the failing test.** Cuatro programas mínimos: (a) `LENGTH x $8; x='a';` da `x` carácter, largo 8, fuente `LENGTH`; (b) `y = x + 1;` sin tipo de `x` da `y` numérico demostrado (la aritmética lo exige) y `x` pendiente; (c) `SET a b;` con `a.k` numérico y `b.k` carácter da `P-UNION-TIPO-CONFLICTO`; (d) `CREATE TABLE t AS SELECT count(*) AS n` da `n` numérico.
- [ ] **Step 2: Run test to verify it fails.**
- [ ] **Step 3: Implement** la propagación en una pasada sobre el plan (`ir/`) en orden topológico: cada operador hereda las columnas de su entrada y aplica su efecto (`calcular` añade, `proyectar` filtra, `renombrar` renombra, `unir`/`combinar` unen con la regla de prioridad). Cada columna lleva `fuente` y `evidencia` (línea del SAS).
- [ ] **Step 4: Run** `uv run python -m pytest tests/unit/test_esquemas_propagacion.py tests/unit/test_corpus_esquemas.py -q`.
- [ ] **Step 5: Commit.** `hito N m: esquemas propagados por el plan con su fuente`.

---

### Task B-4: Esquema de cada tabla del corpus coincide con `caso.yaml` (cierra MG-P1-02)

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_corpus_esquemas.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\L3` a `L8` (`caso.yaml`: bloque `esquemas`)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\proponer_esquemas_caso.py`

El bloque `esquemas` existe hoy solo en los 45 casos de L0 a L2 (hito 130m a 138m). El aceptance de MG-P1-02 es «esquema de cada tabla del corpus coincide con el declarado».

- [ ] **Step 1: Write the failing test.** Parametrizar `test_corpus_esquemas.py` sobre todos los casos `traducible` de L0 a L8 y exigir que `esquema_inferido(caso) == caso.esquemas` para columnas con tipo demostrado; las columnas pendientes deben estar en `caso.esquemas_pendientes` con motivo.
- [ ] **Step 2: Run test to verify it fails** (L3 a L8 sin bloque).
- [ ] **Step 3: Implement** `tools/proponer_esquemas_caso.py`: para un caso imprime el bloque `esquemas` que sale del migrador, para que una persona lo revise. **No se escribe a ciegas:** cada tipo se contrasta con el SAS y con la entrada `entradas/*.csv` antes de pegarlo; un tipo que no se puede demostrar entra como pendiente con motivo, no como `String`.
- [ ] **Step 4: Run** `uv run python -m pytest tests/unit/test_corpus_esquemas.py tests/unit/test_corpus_esquemas_migrar.py -q`.
- [ ] **Step 5: Commit.** `hito N m: esquemas declarados en todo el corpus traducible`.

---

### Task B-5: Operadores del plan lógico usados por los pases del DATA step (MG-P1-03, parte 1)

Los constructores de `src/sgm/ir/operadores.py` existen para 13 de los 14 operadores y `lower_sql_flow.py` ya los usa (hitos 141m y 142m). Faltan `lower_data*.py` y `lower_procs.py`, más `renombrar` y `pivotar` (esta última queda como hueco declarado).

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\ir\lower_data_statements.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\ir\lower_data_grupos.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\ir\lower_procs.py`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_ir_operadores_corpus.py`

- [ ] **Step 1: Write the failing test.** Ampliar `test_ir_operadores_corpus.py` para L0 a L6: ningún operador de `filter`, `derive`, `project`, `rename`, `sort`, `dedup`, `read_file`, `write_file` queda construido directamente con `Builder.op` sin pasar por el constructor (comparar `params` y exigir el helper `_paso` de `lower_sql_flow.py` o su equivalente). Un helper común `paso_validado(chain, kind, params, constructor)` se extrae a `src/sgm/ir/pasos.py` desde `_paso` de `lower_sql_flow.py` (sin cambiar comportamiento; el golden debe quedar idéntico).
- [ ] **Step 2: Run test to verify it fails.**
- [ ] **Step 3: Implement.** Mover `_paso` a `ir/pasos.py` y usarlo en `lower_data_statements.py` (asignaciones, `WHERE`, subsetting `IF`, `KEEP`/`DROP`/`RENAME`), `lower_data_grupos.py` (`dedup` por `FIRST.`/`LAST.`) y `lower_procs.py` (`PROC SORT`, `NODUPKEY`). Si el constructor rechaza el paso se usa la forma anterior (`legado`) y se deja un contador en `Plan.resumen` para B-6.
- [ ] **Step 4: Run** la suite completa y `uv run ruff check .`. Las firmas de L0 a L3 no cambian (golden).
- [ ] **Step 5: Commit.** `hito N m: el lowering del DATA step y de PROC SORT usa los constructores`.

---

### Task B-6: `L1` a `L3` construyen su plan sin forma anterior (cierra MG-P1-03)

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\ir\lower_sql_flow.py` (agregados; extraer si pasa de 300 líneas: hoy 608)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\ir\lower_sql_agregados.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\ir\operadores.py` (`renombrar` usado; `pivotar` como hueco con `P-OPERADOR-PIVOTAR` y motivo)
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_ir_operadores_corpus.py`

- [ ] **Step 1: Write the failing test.** Para los casos `traducible` de L1 a L3, el contador de «formas anteriores usadas» (B-5) es cero. Para cada operador, una prueba de constructor + validador con una entrada inválida (por ejemplo `agregar` sin función, `ordenar` sin columnas) que lanza `ValueError` con el motivo.
- [ ] **Step 2: Run test to verify it fails** en los agregados de SQL.
- [ ] **Step 3: Implement.** Extraer el bloque de agregados de `lower_sql_flow.py` a `lower_sql_agregados.py` (sin cambio de comportamiento, commit propio) y pasarlo por `operadores.agregar`.
- [ ] **Step 4: Run** `uv run python -m pytest tests/unit/test_ir_operadores_corpus.py tests/unit/test_golden*.py -q`; luego suite completa.
- [ ] **Step 5: Commit.** `hito N m: L1 a L3 construyen su plan por constructores`.

---

### Task B-7: `SQL a plan` sin pendientes que no sean de alcance (MG-P1-04, 6 h)

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\migrar_pendientes.yaml`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\ir\lower_sql_flow.py` y los `lower_sql_*.py` que correspondan
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_corpus_pendientes_migrar.py` (el que ya vigila la lista; ubicarlo con `grep -rn "migrar_pendientes" tests`)

Hoy están listados en `migrar_pendientes.yaml` de L1 y L2 `l0_12`, `l2_12`, `l2_16` y `l3_09`. El criterio es «`L1` y `L2` generan plan sin pendientes que no sean de alcance».

- [ ] **Step 1: Write the failing test.** Clasificar cada pendiente de L1 y L2 como `alcance` (SQL fuera del dialecto soportado, con página de `sqlproc` que lo diga) o `defecto`. La prueba exige `defecto == 0`.
- [ ] **Step 2: Run test to verify it fails** (`l2_12` `P-FILTRO-SIN-TRADUCIR`, `l2_16` `P-OPERADOR-SIN-SOPORTE`).
- [ ] **Step 3: Implement.** `l2_12` (auto-join por ciudad): el filtro referencia dos alias de la misma tabla; atribuir cada columna calificada a su alias en `sql_semantics.py`. `l2_16` (SQL en la misma base) ya compiló con `tImpalaRow` (hito 164m): el pendiente restante es del plan, no del emisor; cerrar con el operador `leer` con `sql` literal. Los que dependen de tipos (`l3_09`, agregado sin esquema) quedan con su motivo si B-3 no los resuelve.
- [ ] **Step 4: Run** suite completa; quitar de `migrar_pendientes.yaml` los casos resueltos (la prueba falla si no se quitan).
- [ ] **Step 5: Commit.** `hito N m: SQL a plan sin defectos en L1 y L2`.

---

### Task B-8: `DATA step a plan` y `PROC a plan` para L4 a L6 (MG-P1-05 y MG-P1-06, 10,5 h)

Aquí se define el vocabulario de operadores que usan B-9 a B-14. No inventar operadores nuevos fuera de los 14 de la sección 4: el estado por fila y el `MERGE` son `combinar` (MERGE), `iterar`/`controlar` (control) y `calcular` con `estado` (RETAIN/FIRST/LAST/LAG), todos con parámetros declarados en `operadores.py`.

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\ir\operadores.py` (extender `calcular` con `estado: list[dict]`; `combinar` con `por`, `in_flags`, `modo`)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\ir\lower_procs.py` (`PROC FREQ`, `MEANS`, `TRANSPOSE`, `APPEND`, `FORMAT`; hoy sin regla es `unsupported` con `PROC_NO_SOPORTADO`)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\ir\lower_procs_agregados.py`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_ir_operadores.py`

**Fuentes:** `proc.pdf`: `SORT Procedure` (p. 2449), `MEANS Procedure` (p. 1521), `TRANSPOSE Procedure` (p. 2745), `APPEND Procedure` (p. 161), `FORMAT Procedure` (p. 1127), y `FREQ` (`grep -n "FREQ Procedure" docs/referencia/sas/proc.INDEX.md`). `PROC APPEND` es concatenación con destino base: operador `concatenar` con `base`. `PROC FORMAT` no cambia datos: es una declaración de formato (operador `controlar` con `kind=format_def`).

- [ ] **Step 1: Write the failing tests.** (a) `calcular` acepta `estado=[{"op":"retain","name":"acum","init":0}]`; rechaza `init` de tipo distinto al de la columna; (b) `combinar` con `por=["id"]`, `in_flags=["en_a","en_b"]`, `modo="merge"` valida que haya al menos dos fuentes y que `por` esté en el esquema de todas; (c) `PROC APPEND DATA=b BASE=a` produce `concatenar` y `PROC FREQ` simple (`TABLES x`) produce `agregar` con `count` y `percent`.
- [ ] **Step 2: Run tests to verify they fail.**
- [ ] **Step 3: Implement** los constructores y el lowering. `PROC TRANSPOSE` queda como `pivotar` hueco: `P-OPERADOR-PIVOTAR` con motivo y página, hasta que un caso lo pida.
- [ ] **Step 4: Run** `uv run python -m pytest tests/unit/test_ir_operadores.py tests/unit/test_golden*.py -q`, luego suite completa y `uv run python tools/linea_base_plan_logico.py` para comparar con B-1.
- [ ] **Step 5: Commit.** `hito N m: operadores de estado y de combinacion y PROC a plan`.

---

## Parte II. MG-P4 restante: DATA step (69 h)

Semántica común (leerla una vez antes de B-9): el DATA step compila y ejecuta por iteraciones; cada iteración lee una observación, ejecuta las sentencias en orden y escribe al final salvo que haya `OUTPUT`, `DELETE` o `RETURN` (`lrcon`, «Overview of DATA Step Processing», p. 492 a 502; «The Execution Phase», p. 494; «The Default Sequence of Execution», p. 500). Las variables viven en el vector de datos del programa (PDV): se reinician a faltante al empezar cada iteración salvo las retenidas (`RETAIN`, sentencia suma, las leídas por `SET`/`MERGE`) (`lrcon`, «Creating the Input Buffer and the Program Data Vector», p. 496). El intérprete de `src/sgm/migrar/interprete.py` ya modela el PDV para asignaciones; este plan lo extiende, no lo reescribe.

### Task B-9: Investigar `SET a b;` en Studio: ¿`tUnite` compila y ejecuta con el orden de SAS? (MG-P4-03, parte 1)

El plan maestro (sección 2 y MG-P4-03) dice que `tUnite` no compila; está desactualizado. El hito 97d lo vio fallar con `preMetadata is null` y el hito 125m (`PROGRESS.md`, «Segunda pasada completa») lo arregló escribiendo las entradas como conexión `MERGE` con `lineStyle` 10: `l0_09` **compiló**, pero **nunca se ejecutó** ni se comparó su salida, y el orden de entrada del `tUnite` quedó sin verificar. SAS concatena en el orden de la lista: todas las observaciones de `a`, luego todas las de `b` (`lestmtsref`, `SET Statement`, p. 343; `lrcon`, «Concatenating», p. 571 y 579).

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\PROGRESS.md` (sección «Decisiones» del hito)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\L6\l6_25_set_dos_datasets_orden\` (`programa.sas`, `caso.yaml`, `entradas/`, `esperado/`)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\L6\l6_26_set_columnas_distintas\`

**Interfaces:**
- Produces: una decisión escrita en `PROGRESS.md` con una de tres salidas: (a) `tUnite` con conexiones `MERGE` conserva el orden y se usa; (b) `tUnite` no garantiza el orden y se usa `APPEND` secuencial (R2-02, hito 97); (c) cada entrada pasa por un `tMap` que alinea columnas por nombre y rellena faltante, y luego (a) o (b).

- [ ] **Step 1: Escribir los dos casos de corpus.** `l6_25`: `DATA WORK.TODO; SET WORK.A WORK.B; RUN;` con `A` de 3 filas y `B` de 2, mismo esquema, valores que revelen el orden; esperado: 5 filas, las de `A` primero. `l6_26`: `A(id, x)` y `B(id, y)`; esperado: 5 filas con columnas `id, x, y`, `x` faltante en las filas de `B` y `y` faltante en las de `A` (SAS junta por nombre y rellena con faltante: `lrcon`, «Concatenating», p. 579). Los esperados se calculan con el intérprete (capa B) y se revisan a mano contra la página.
- [ ] **Step 2: Anillo A.** `uv run python -m sgm.cli migrar tests/corpus/L6/l6_25_set_dos_datasets_orden/programa.sas --muestra tests/corpus/L6/l6_25_set_dos_datasets_orden/entradas --out out/b9` y confirmar que el Job tiene un `tUnite` con dos conexiones `MERGE` en el orden `A`, `B` (`uv run python -m pytest tests/unit/test_desde_plan.py -q`).
- [ ] **Step 3: Studio, una sola vez.** `uv run python tools/validar_caso_studio.py l6_25_set_dos_datasets_orden l6_09_nodup_registros_identicos` (el segundo es testigo). Resultados: `coincide`; `difiere` (el orden es otro: opción b); error de compilación (registrar el literal del log). Si `sgm studio salud` no conecta, parar y anotar «investigación pendiente por Studio» sin cambiar el plan.
- [ ] **Step 4: Escribir la decisión** en `PROGRESS.md` y corregir en el mismo cambio las frases obsoletas del plan maestro (sección 2, tabla 5.2 fila `SET a b;` y MG-P4-03) para que no contradigan el código.
- [ ] **Step 5: Commit.** `hito N m: SET de varios datasets, orden de tUnite investigado en Studio`.

---

### Task B-10: `SET a b;` concatena por nombre con faltante (MG-P4-03, parte 2)

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\talend_item\desde_plan_union.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\interprete.py` (`_apilar`, línea 776)
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_desde_plan_union.py`

Hoy las entradas con columnas distintas dan `P-UNION-ESQUEMAS-DISTINTOS` y no se emite nada. La regla de SAS es unir por nombre y rellenar con faltante; el largo y el tipo los fija la primera aparición (`lestmtsref`, p. 343).

- [ ] **Step 1: Write the failing test.** (a) `A(id,x)` y `B(id,y)` produce un nodo de alineación por entrada (un `tMap` que emite `id,x,y` con `null` donde falta) más el `tUnite`; (b) tipos distintos para la misma columna siguen en `P-UNION-TIPO-CONFLICTO` (B-3); (c) `SET a b; BY k;` (intercalado, `lrcon` p. 583) **no** se concatena: pendiente `P-SET-INTERCALADO` con motivo.
- [ ] **Step 2: Run test to verify it fails.**
- [ ] **Step 3: Implement** según la decisión de B-9 (a, b o c). El esquema de salida es la unión ordenada de columnas, primero las de la primera tabla. `OBS=`, `FIRSTOBS=` y `WHERE=` de cada fuente se aplican **antes** de concatenar (`lestmtsref`, p. 343; ubicar `OBS=` con `grep -n "OBS=" docs/referencia/sas/ledsoptsref.INDEX.md`).
- [ ] **Step 4: Run** `uv run python -m pytest tests/unit/test_desde_plan_union.py tests/unit/test_corpus_l4l6.py -q`; `l6_26` coincide en B y pasa el validador estructural; `l0_09` sale de `migrar_pendientes.yaml` si estaba.
- [ ] **Step 5: Commit.** `hito N m: SET de varios datasets une por nombre y rellena con faltante`.

---

### Task B-11: `MERGE ... BY ... IN=` con la semántica real en el intérprete (MG-P4-04, parte 1)

Semántica (`lestmtsref`, `MERGE Statement`, p. 243; `lrcon`, «Match-Merging», p. 597 a 601; «One-to-One Merging», p. 592 a 596): las entradas deben estar ordenadas por `BY`; por cada valor de `BY` se leen las observaciones de cada entrada en paralelo, una por iteración; cuando una entrada se agota en el grupo conserva los valores de su última observación y la iteración sigue mientras alguna entrada tenga observaciones en el grupo. Con grupos de tamaños `m` y `n` salen `max(m, n)` filas, no `m*n`. `IN=` vale 1 si la entrada contribuyó con una observación a **esa iteración** (`lrcon`, «Using the IN= Data Set Option», p. 75). Sin `BY`, `MERGE` es una unión fila a fila por posición (`lrcon`, «One-to-One Merging», p. 592). Si dos entradas traen una columna con el mismo nombre, gana la de la última entrada de la lista que contribuyó (`lestmtsref`, p. 243).

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\interprete_merge.py` (extraer `_mezclar`, línea 546 de `interprete.py`, con la prueba verde antes de cambiarlo)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\interprete.py`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_interprete_merge.py`

**Interfaces:**
- Produces:
  ```python
  def mezclar(entradas: list[list[dict]], banderas: list[str | None], por: list[str]) -> list[dict]:
      """MERGE de SAS. `banderas[i]` es el nombre de IN= de la entrada i (o None).
      Sin `por`, une fila a fila por posición. Rechaza entradas desordenadas por `por`."""
  ```

- [ ] **Step 1: Write the failing test.** Tabla de comportamientos, cada uno con su página: (1) uno a uno, 2 filas por lado: 2 filas (p. 593); (2) `m=2, n=3` en un grupo: 3 filas, y la segunda y tercera repiten la última observación de la entrada corta (p. 600); (3) llave solo en un lado: la otra entrada aporta faltante y su `IN=` es 0 (p. 601); (4) tres entradas con llaves parciales (`l6_04`); (5) sin `BY` y tamaños 3 y 2: 3 filas, la tercera conserva los valores de la segunda en la entrada corta (p. 594); (6) entrada desordenada: el intérprete rechaza con el error de SAS «BY variables are not properly sorted» (`lrcon`, «Sort Requirements», p. 551), no ordena por su cuenta; (7) columnas con nombre común: gana la última (p. 243).
- [ ] **Step 2: Run test to verify it fails.**
- [ ] **Step 3: Implement** `mezclar`. Para la retención entre iteraciones del mismo grupo, la fila de salida parte de la anterior del mismo grupo y se sobrescribe solo con las columnas de las entradas que aún contribuyen; al cambiar de grupo se reinicia a faltante (`lrcon`, p. 598).
- [ ] **Step 4: Run** `uv run python -m pytest tests/unit/test_interprete_merge.py tests/unit/test_corpus_l4l6.py -q`. Casos `l6_01`, `l6_02`, `l6_03`, `l6_04` y `l6_12` coinciden con su `esperado/`. **`l6_11` está `pendiente_revision`** (su `caso.yaml` dice «regla sin fuente oficial consultada»): este paso lo cierra leyendo `lestmtsref`, `Sum Statement` (p. 360) y `lrcon` p. 598, escribe el `razonamiento` con las páginas y pasa el estado a `traducible`. Si el invariante `suma(VENTAS_ZONA.ACUM) == 42` no sale, se corrige el esperado con la página en la mano, no el intérprete a ciegas.
- [ ] **Step 5: Commit.** `hito N m: MERGE con la semantica de SAS en el interprete`.

---

### Task B-12: `MERGE` emitido como `tSortRow` + `tJavaRow`, no como JOIN (MG-P4-04, parte 2)

Hoy `l6_01` a `l6_04` y `l6_12` están en `tests/corpus/migrar_pendientes.yaml` con `P-UNION-TIPO-SIN-SOPORTE` (`talend_item/desde_plan_map.py`, línea 240) y `l6_11` con `P-OPERADOR-SIN-SOPORTE`. `lower_data.py` (`_join_type`, línea 21) deduce un tipo de JOIN de la primera condición `if` y marca «revisar» si no puede: esa deducción es el origen del error conceptual y se reemplaza por el operador `combinar` de B-8.

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\ir\lower_data.py` (extraer primero `_join_type` y `_lower_sources` a `lower_data_fuentes.py`; commit propio sin cambio de comportamiento)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\talend_item\desde_plan_merge.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\talend_item\desde_plan_map.py` (despachar `combinar` con `modo=merge`)
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_desde_plan_merge.py`

**Diseño del emisor (sin componentes inventados):** para `MERGE a b; BY k;`: `tSortRow` por `k` en cada entrada solo si el SAS ya la ordenó antes (`PROC SORT` previo demostrable); si no, `P-MERGE-SIN-ORDEN` con motivo (SAS tampoco ordena: B-11 paso 1(6)). Camino simple con `tMap` y lookup **solo** cuando la clave es única en ambos lados y está demostrada por `NODUPKEY` previo (`l6_01`). Caso general (`l6_02`, `l6_03`, `l6_04`, `l6_11`): entradas alineadas por `tUnite` (B-10) con una columna de origen, `tSortRow` por `(k, orden de entrada, secuencia)` y un `tJavaRow` con la lógica de `mezclar` y el estado entre filas en variables de clase. El Java generado se compila con `javac` suelto (MG-P10-03).

- [ ] **Step 1: Write the failing test.** `l6_01` con clave única demostrada emite `tMap` con lookup y `IN=` como columnas calculadas; `l6_02` emite el camino general con `tJavaRow`; un `MERGE` sin ordenar da `P-MERGE-SIN-ORDEN`; el Job pasa `validar_job` (MG-P10-02) y ninguna expresión Java compara `Long` boxed con `==`.
- [ ] **Step 2: Run test to verify it fails.**
- [ ] **Step 3: Implement** la plantilla Java en `desde_plan_merge.py`; probarla compilándola con el JDK de Studio (`TALEND_JAVA_BIN`), sin Studio.
- [ ] **Step 4: Run** `uv run python -m pytest tests/unit/test_desde_plan_merge.py tests/unit/test_corpus_pendientes_migrar.py -q`; quitar de `migrar_pendientes.yaml` `l6_01` a `l6_04`, `l6_11` y `l6_12` conforme dejen de tener pendientes. La ejecución en Studio de los seis va en el lote de B-Gate (anillo C), no aquí.
- [ ] **Step 5: Commit.** `hito N m: MERGE emitido con la semantica de SAS, no como JOIN`.

---

### Task B-13: `RETAIN`, sentencia suma, `FIRST.`/`LAST.`, `LAG`, `DIF` en el intérprete (MG-P4-05, parte 1)

Semántica con página:
- `RETAIN` (`lestmtsref`, p. 331): la variable conserva su valor entre iteraciones; sin valor inicial arranca en faltante; con valor, se inicializa una sola vez.
- Sentencia suma `x + expr;` (`lestmtsref`, p. 360): equivale a `RETAIN x 0; x = SUM(x, expr);`: **el faltante en `expr` cuenta como 0** y `x` nunca queda faltante.
- `FIRST.v` y `LAST.v` (`lrcon`, p. 547 y 552 a 557; `lestmtsref`, `BY Statement`, p. 51): requieren datos ordenados; con varias variables `BY`, `FIRST.v2` vale 1 también cuando cambia una variable anterior (`lrcon`, p. 553 y ejemplo 3, p. 556).
- `LAG(x)` y `DIF(x)` (`lefunctionsref`, p. 1163 y p. 663): la cola de `LAG` **se actualiza solo cuando la función se ejecuta**; dentro de un `IF` da resultados contraintuitivos. `DIF(x) = x - LAG(x)`; el primer valor es faltante.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\interprete_estado.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\interprete.py` (`_por_grupo`, línea 706; `retain`, línea 717)
- Create: casos `tests\corpus\L6\l6_27_retain_valor_inicial`, `l6_28_suma_con_faltante`, `l6_29_first_last_dos_variables_by`, `l6_30_lag_dentro_de_if`, `l6_31_dif_primer_valor_faltante`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_interprete_estado.py`

- [ ] **Step 1: Write the failing test.** Los cinco casos nuevos, cada uno con `razonamiento` y página, más `l6_05`, `l6_06`, `l6_07` y `l6_10` (hoy `P-OPERADOR-SIN-SOPORTE` en A) que ya deben coincidir en B. `l6_30` es la trampa de `LAG` dentro de `IF`: `LAG` devuelve el valor de la última vez que se *ejecutó*, no el de la fila anterior.
- [ ] **Step 2: Run test to verify it fails** (casos nuevos).
- [ ] **Step 3: Implement** el estado por fila como un diccionario por iteración: `retenidas`, `lag_colas` (una cola por llamada textual a `LAG`/`DIF`, no por columna) y banderas `first_*`/`last_*` por comparación con la fila anterior y la siguiente del grupo. Los esperados nuevos se escriben a mano desde la página; si discrepan con el intérprete, gana la página.
- [ ] **Step 4: Run** `uv run python -m pytest tests/unit/test_interprete_estado.py tests/unit/test_corpus_l4l6.py -q`.
- [ ] **Step 5: Commit.** `hito N m: estado por fila (RETAIN, suma, FIRST/LAST, LAG, DIF) en el interprete`.

---

### Task B-14: Estado por fila emitido con `tSortRow` + `tJavaRow` (MG-P4-05, parte 2)

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\talend_item\desde_plan_estado.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\ir\lower_data_grupos.py` (hoy `FIRST.`/`LAST.` solo se resuelve como `dedup` cuando es un `IF LAST.k;` puro)
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_desde_plan_estado.py`

- [ ] **Step 1: Write the failing test.** `l6_05` (`IF LAST.ciudad;`) sigue como `tSortRow` + `tUniqRow` sin `tJavaRow` (la traducción más simple); `l6_06` y `l6_07` emiten `tSortRow` + `tJavaRow` con variables de clase para el acumulado; `l6_29` emite las banderas `first_*`/`last_*` (la bandera `LAST.` necesita ver la fila siguiente: pasada por búfer del grupo). El Java compila con `javac` suelto y no compara boxed con `==`.
- [ ] **Step 2: Run test to verify it fails.**
- [ ] **Step 3: Implement.** `RETAIN` sin valor inicial usa `null`; la sentencia suma usa 0 y trata `null` como 0; `LAG` con `LinkedList` por llamada, actualizada solo si se ejecuta.
- [ ] **Step 4: Run** `uv run python -m pytest tests/unit/test_desde_plan_estado.py tests/unit/test_corpus_pendientes_migrar.py -q`; quitar de `migrar_pendientes.yaml` `l6_05`, `l6_06`, `l6_07` y `l6_10` cuando dejen de tener pendientes. Studio: lote de B-Gate.
- [ ] **Step 5: Commit.** `hito N m: estado por fila emitido con tSortRow y tJavaRow`.

---

### Task B-15: `SELECT/WHEN` y `DELETE` (MG-P4-01, resto)

Semántica: `SELECT (expr); WHEN (v1, v2) ...; OTHERWISE ...; END;` evalúa `expr` **una vez** y compara con cada `WHEN` en orden; la primera que coincide ejecuta y las demás no se evalúan; sin `OTHERWISE` y sin coincidencia SAS da error (`lestmtsref`, `SELECT Statement`, p. 338). `SELECT;` sin expresión evalúa cada `WHEN` como condición booleana. `DELETE;` detiene la iteración sin escribir la observación y sin ejecutar las sentencias siguientes (`lestmtsref`, p. 77). `IF-THEN/ELSE` está en p. 132 y el subsetting `IF`, p. 129.

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\frontend\datastep.py` (reconocer `select`, `when`, `otherwise`, `delete`)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\ir\lower_data_select.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\interprete.py` (`delete` y cadena `select`)
- Create: casos `tests\corpus\L4\l4_21_select_when_con_otherwise`, `l4_22_select_sin_expresion`, `l4_23_delete_condicional`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_lower_data_select.py`

- [ ] **Step 1: Write the failing test.** (a) `SELECT (x); WHEN (1,2) y='a'; WHEN (3) y='b'; OTHERWISE y='c'; END;` baja a la cadena `IF/ELSE IF/ELSE` que ya existe (`_conditional_assignment`, `lower_data.py` línea 461) con `x in (1,2)` y `x = 3`, y tres filas de prueba coinciden en B; (b) sin `OTHERWISE` y sin coincidencia: pendiente `P-SELECT-SIN-OTHERWISE` (SAS aborta; no se inventa un valor por omisión); (c) `DELETE` condicional produce un `filter` con la condición negada cuando solo hay asignaciones antes; si hay `OUTPUT` antes, queda el pendiente `P-DELETE-CON-OUTPUT`; (d) `WHEN` con faltante: el faltante numérico solo iguala a otro faltante.
- [ ] **Step 2: Run test to verify it fails.**
- [ ] **Step 3: Implement** por reducción a `IF` encadenado, sin operador nuevo.
- [ ] **Step 4: Run** `uv run python -m pytest tests/unit/test_lower_data_select.py tests/unit/test_corpus_l4l6.py -q`.
- [ ] **Step 5: Commit.** `hito N m: SELECT/WHEN y DELETE`.

---

### Task B-16: `ARRAY` y `DO` (MG-P4-06)

Semántica: `ARRAY a{3} x1-x3;` define un alias de variables, no almacenamiento (`lestmtsref`, `ARRAY Statement`, p. 33; referencia `a{i}`, p. 39); los índices van desde 1 salvo `{0:2}`; `DO i = 1 TO 3;` itera con el valor final inclusive y **deja `i` valiendo 4 al salir** (`lestmtsref`, `DO Statement: Iterative`, p. 84); `DO WHILE` evalúa antes (p. 90) y `DO UNTIL` después (p. 88). Un índice fuera de rango es error de ejecución.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\ir\lower_data_array.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\frontend\datastep.py` (hoy `array` guarda solo `body`, línea 138)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\interprete.py`
- Create: casos `tests\corpus\L6\l6_32_array_do_constante`, `l6_33_do_while`, `l6_34_array_indice_fuera_de_rango`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_lower_data_array.py`

- [ ] **Step 1: Write the failing test.** (a) `DO i=1 TO 3; a{i} = a{i} * 2; END;` con límites constantes se **desenrolla** a tres asignaciones (`calcular`) sin `tJavaRow`, y el intérprete coincide incluyendo `i = 4` si el programa la conserva; (b) límites no constantes o `DO WHILE`/`UNTIL`: `tJavaRow` con un bucle; si el cuerpo contiene `OUTPUT` dentro del bucle, `P-DO-OUTPUT-EN-BUCLE` (varias filas por iteración, fuera de alcance); (c) `l6_34`: índice 4 en un arreglo de 3 es `P-ARRAY-FUERA-DE-RANGO`, no un `null` silencioso; (d) `l0_13` (hoy `xfail` por `DO/END`) cambia de estado según (a).
- [ ] **Step 2: Run test to verify it fails.**
- [ ] **Step 3: Implement.** Registrar los arreglos en una tabla del paso (nombre, límites, miembros); `a{i}` con `i` constante se resuelve a la columna; no constante, a `tJavaRow`.
- [ ] **Step 4: Run** `uv run python -m pytest tests/unit/test_lower_data_array.py tests/unit/test_lower_data_do_else.py -q`.
- [ ] **Step 5: Commit.** `hito N m: ARRAY y DO con desenrollado estatico`.

---

### Task B-17: Generador de combinaciones de `OUTPUT` (cierra MG-P4-02, parte 1)

Reemplaza la serie de un hito por variante (166 a 190, casos `l6_13` a `l6_24`). La semántica (`lestmtsref`, `OUTPUT Statement`, p. 273 y 274): `OUTPUT` escribe la observación **con los valores del PDV en ese instante** al dataset nombrado, o a todos los del encabezado `DATA` si no nombra ninguno; en cuanto un paso tiene un `OUTPUT` explícito se suprime la escritura implícita del final de la iteración (`lrcon`, «Writing an Observation to the SAS Data Set», p. 498); un destino que no está en el encabezado es error de SAS. Los patrones ya cubiertos a mano son la lista de verificación del generador: si no los reproduce, el generador está mal.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\corpus_output\__init__.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\corpus_output\gramatica.py` (espacio de combinaciones)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\corpus_output\oraculo.py` (simulador del PDV escrito desde la página, **independiente** de `ir/` y de `migrar/`)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\generar_combinaciones_output.py`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_combinaciones_output.py`

**Interfaces:**
- Produces:
  ```python
  @dataclass(frozen=True)
  class Combinacion:
      ramas: tuple[str, ...]        # "if", "else_if", "else" en el orden del programa
      destinos: tuple[tuple[str, ...], ...]  # por rama: () = omitido (todos), ("a",), ("a","b")
      posicion: str                 # "terminal" | "con_continuacion"
      captura_pdv: bool             # hay una asignación entre dos OUTPUT
      def programa_sas(self) -> str: ...
  def combinaciones() -> Iterator[Combinacion]: ...
  def esperado(c: Combinacion, entradas: list[dict]) -> dict[str, list[dict]]: ...
  ```

**Espacio:** ramas ∈ {`IF`, `IF/ELSE`, `IF/ELSE IF`, `IF/ELSE IF/ELSE`, incondicional, dos `IF` independientes} × destinos por rama ∈ {omitido, uno, dos, todos} con 2 o 3 datasets declarados × posición {terminal, con continuación} × captura del PDV {sí, no}. Se acota por poda: no se generan programas con destino repetido entre ramas no excluyentes (`OUTPUT_DESTINO_REPETIDO` ya los rechaza) ni con destino fuera del encabezado; esos dos casos son **negativos** y se prueban aparte con su pendiente esperado.

- [ ] **Step 1: Write the failing test.** (a) `combinaciones()` incluye una combinación equivalente a cada uno de `l6_13` a `l6_24` (comparar por su `programa_sas` normalizado y el esperado de su carpeta); (b) para cada combinación, `esperado` coincide con el intérprete sobre el plan (capa B) con tres filas de entrada que ejerzan cada rama (`valor` < 0, = 0, > 0) y una con faltante; (c) en anillo A: la combinación se migra y pasa `validar_job`, o deja un pendiente con código estable (`OUTPUT_DESTINO_REPETIDO`, `P-OUTPUT-...`) y **ningún Job parcial**; (d) la prueba de mutación: alterar un esperado a mano y comprobar que (b) falla (MG-P10-06).
- [ ] **Step 2: Run test to verify it fails.**
- [ ] **Step 3: Implement.** El oráculo recorre las filas y mantiene un diccionario PDV; en `OUTPUT` copia el PDV al destino; al final de la iteración escribe a todos los destinos solo si no hubo `OUTPUT` explícito en ese paso; el faltante numérico de la condición es menor que cualquier número (`lrcon`, «Comparison Operators», ubicar con `grep -n "Missing Values" docs/referencia/sas/lrcon.INDEX.md`). No importa nada de `sgm.ir` ni `sgm.migrar`.
- [ ] **Step 4: Run** `uv run python -m pytest tests/unit/test_combinaciones_output.py -q` y `uv run python tools/generar_combinaciones_output.py --listar` (cuenta de combinaciones, cuántas se migran y cuántas quedan en pendiente con su código). Las que se migran y no están en el corpus se escriben en `tests/corpus/L6/` con `generar_combinaciones_output.py --escribir N`, con el `caso.yaml` marcado `origen: generado`.
- [ ] **Step 5: Commit.** `hito N m: generador de combinaciones de OUTPUT con oraculo independiente`.

---

### Task B-18: Una validación en lote en Studio de las combinaciones de `OUTPUT` (cierra MG-P4-02, parte 2)

Hoy `l6_13` a `l6_17` y `l6_19` a `l6_21` no tienen validación en Studio registrada; el hito 191 validó `l6_18`, `l6_22`, `l6_23` y `l6_24` (4 de 4 `coincide`) y el hito 185 `l6_20` y `l6_21`.

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\validar_caso_studio.py` solo si hace falta aceptar una lista larga (hoy un argumento por caso, un reintento por caso); no tocar `tools/ci.py` ni `tools/validacion.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\PROGRESS.md`

- [ ] **Step 1: Preparar la lista.** Los casos `l6_13` a `l6_17`, `l6_19`, `l6_21` y todos los generados por B-17 que se migran sin pendiente.
- [ ] **Step 2: Comprobar salud.** `uv run python -m sgm.cli studio salud`. Si no conecta: no reinstalar ni tocar `talend-mcp`; registrar los casos con `tools/corpus_studio.py lote` para que queden en `out/studio-pendientes.json` y cerrar la tarea con «validación en Studio pendiente por la salud de Studio»; no se cuenta como pasada.
- [ ] **Step 3: Una sola corrida.** `uv run python tools/validar_caso_studio.py <lista completa>`; esperado: cada caso `coincide`. Los que fallen se reintentan **de uno en uno** con nombre de Job nuevo (Studio cachea por id); un error de compilación se corrige en el emisor con una prueba nueva en B-17, no con un caso aislado.
- [ ] **Step 4: Registrar** en `PROGRESS.md` los números reales (n de m `coincide`) y en el plan maestro, sección MG-P4-02, una sola línea de estado que reemplace la lista de hitos 166 a 190 por: «cubierto por el generador (B-17) y validado en lote (B-18)». No borrar las entradas de `PROGRESS.md` (los hitos publicados no se renumeran ni se reescriben).
- [ ] **Step 5: Commit.** `hito N m: combinaciones de OUTPUT validadas en lote en Studio`.

---

### Task B-19: `UPDATE` y `MODIFY` (MG-P4-07)

Semántica de `UPDATE` (`lestmtsref`, `UPDATE Statement`, p. 362; `lrcon`, «Updating with the UPDATE and the MODIFY Statements», p. 602 a 611): un maestro y una o más transacciones, ambos ordenados por `BY`; por cada llave se aplica cada transacción sobre el maestro y se escribe **una sola observación por grupo `BY`** al terminar el grupo; los valores **faltantes de la transacción no sobrescriben** al maestro (a menos que `UPDATEMODE=NOMISSINGCHECK`); una llave nueva en la transacción se agrega (`lrcon`, «Updating with Nonmatched Observations, Missing Values, and New Variables», p. 604 y ejemplo 3, p. 609); con varias transacciones de la misma llave se aplican en orden (ejemplo 2, p. 608). `MODIFY` (`lestmtsref`, p. 252; `lrcon`, p. 605 y 606) **modifica el dataset en el sitio** sin crear uno nuevo: no tiene equivalente en un Job que lee y escribe archivos o tablas salvo `tDBOutput` con acción `UPDATE`.

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\frontend\datastep.py` (reconocer `update` y `modify`)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\ir\operadores.py` (`combinar` con `modo="update"`)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\interprete_update.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\talend_item\desde_plan_merge.py` (rama `update`, mismo `tJavaRow` que B-12 con la regla de faltantes)
- Create: casos `tests\corpus\L6\l6_35_update_basico`, `l6_36_update_faltante_no_sobrescribe`, `l6_37_update_llave_nueva`, `l6_38_update_dos_transacciones`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_interprete_update.py`

- [ ] **Step 1: Write the failing test.** Los cuatro casos con esperado escrito desde las páginas 607 a 611; el intérprete coincide; `MODIFY` produce el pendiente `P-MODIFY-EN-SITIO` con el motivo «modifica el dataset en el sitio; el Job no sobrescribe su propia entrada» y la página `lestmtsref, p. 252`, y **no** se emite ningún nodo.
- [ ] **Step 2: Run test to verify it fails.**
- [ ] **Step 3: Implement** `UPDATE` en el intérprete y el emisor; `UPDATEMODE=NOMISSINGCHECK` queda como pendiente `P-UPDATEMODE` hasta que un caso lo pida.
- [ ] **Step 4: Run** `uv run python -m pytest tests/unit/test_interprete_update.py tests/unit/test_desde_plan_merge.py -q`.
- [ ] **Step 5: Commit.** `hito N m: UPDATE con la semantica de SAS; MODIFY como pendiente con motivo`.

---

### Task B-20: `_N_`, `_ERROR_` y `CALL SYMPUT` (MG-P4-08)

Semántica: `_N_` es una variable automática que cuenta **las iteraciones del DATA step**, no las filas escritas, así que sigue contando filas que luego se descartan con `DELETE` o subsetting `IF` (`lrcon`, «Automatic Variables», p. 79; «The Default Sequence of Execution», p. 500); se evalúa **antes** del filtro. `_ERROR_` vale 0 y pasa a 1 cuando ocurre un error de datos (informat inválido, división por cero) en esa iteración (`lrcon`, p. 79). `CALL SYMPUT(nombre, valor)` crea o reemplaza una macrovariable **en la ejecución**; el valor no se recorta (con `SYMPUTX` sí, `lefunctionsref`, p. 477 y p. 482); un valor numérico se convierte con el formato `BEST12.`; la macrovariable **no se puede usar con `&nombre` dentro del mismo paso** porque `&` se resuelve al compilar el paso (`mcrolref`, «Special Cases of Scope with the CALL SYMPUT Routine», p. 93 y siguientes).

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\ir\lower_data_statements.py` (línea 193: `retain`, `lag` y `call_symput` hoy salen como pendiente)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\ir\lower_data_automaticas.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\interprete.py`
- Create: casos `tests\corpus\L5\l5_10_n_cuenta_iteraciones`, `l5_11_n_con_filtro`, `l5_12_symput_ultimo_valor`, `l5_13_symputx_recorta`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_lower_data_automaticas.py`

- [ ] **Step 1: Write the failing test.** (a) `_N_` bajo `IF x > 0;` con 4 entradas y 2 filtradas da `_N_` en las 2 filas que quedan con los números originales (por ejemplo 2 y 4, no 1 y 2); (b) `_ERROR_` usado en la lógica: `P-ERROR-AUTOMATICA` con motivo (el Job no sabe qué errores de datos habría tenido SAS) salvo que solo se **lea** como constante 0 en un `KEEP`/`DROP`; (c) `CALL SYMPUT('v', x)` en cada fila deja el valor de la **última** iteración en `v`, y un paso posterior que usa `&v` lo recibe (la resolución del `&v` es de MG-P7; aquí solo se emite la escritura); (d) `SYMPUTX` recorta blancos, `SYMPUT` no.
- [ ] **Step 2: Run test to verify it fails.**
- [ ] **Step 3: Implement.** `_N_` como `Numeric.sequence` o un contador en `tJavaRow` colocado **antes** del `tFilterRow`; `CALL SYMPUT` como `tJavaRow` que escribe en `globalMap` (y en `tSetGlobalVar` donde ya hay plantilla validada, hito 3411 de `PROGRESS.md`); el valor se convierte con `BEST12.` solo para numéricos.
- [ ] **Step 4: Run** `uv run python -m pytest tests/unit/test_lower_data_automaticas.py tests/unit/test_corpus_l4l6.py -q`.
- [ ] **Step 5: Commit.** `hito N m: _N_ y CALL SYMPUT; _ERROR_ como pendiente con motivo`.

---

### Task B-21: Hash objects: soporte mínimo o pendiente con motivo (MG-P4-09)

Semántica (`lrcon`, «Using the Hash Object», p. 628 a 641): `DECLARE HASH h(DATASET:'t'); h.DEFINEKEY('k'); h.DEFINEDATA('v'); h.DEFINEDONE(); rc = h.FIND();` carga la tabla en memoria al compilar el paso y busca por llave; `FIND` devuelve 0 si la encuentra (y llena `v`) y distinto de 0 si no. Con llaves duplicadas en la carga, el comportamiento por omisión (cuál queda, primera o última) **se fija leyendo p. 630 y p. 634 a 638 antes de escribir la prueba**; no se supone. `ADD`, `REMOVE`, `REPLACE`, iteradores (`lrcon`, «Using the Hash Iterator Object», p. 642) y `OUTPUT` (p. 639) modifican la tabla durante la ejecución.

**Decisión (por defecto, se confirma con la lectura):** soporte mínimo solo para el patrón de **búsqueda**: `DECLARE` con `DATASET:` + `DEFINEKEY` + `DEFINEDATA` + `DEFINEDONE` + `FIND` como único método. Se traduce a un `tMap` con lookup (modo de coincidencia según la regla de duplicados leída). Todo lo demás es pendiente con motivo: `P-HASH-MUTABLE` (`ADD`, `REMOVE`, `REPLACE`), `P-HASH-ITERADOR` y `P-HASH-OUTPUT`.

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\frontend\datastep.py` (`declare` ya está en `_CABECERA` de `lower_data_grupos.py`, línea 27; reconocer los métodos con punto)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\ir\lower_data_hash.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\interprete.py`
- Create: casos `tests\corpus\L9\l9_h1_hash_find`, `l9_h2_hash_llave_duplicada`, `l9_h3_hash_add_pendiente`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\rules\sas\catalogo\` (entrada `hash` con `fuente: lrcon.pdf, p. 628` y `estado: reconocida` solo para el patrón de búsqueda; el resto `no_reconocida` con nota)
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_lower_data_hash.py`

- [ ] **Step 1: Write the failing test.** (a) El patrón de búsqueda baja a un operador `unir` tipo `left` con `rc` como columna calculada (`0` si hubo coincidencia, `-1` si no; el valor exacto de `rc` se lee de la guía); (b) llave duplicada: el esperado sigue la regla leída de las páginas 630 a 638; (c) `h.ADD()` da `P-HASH-MUTABLE` y no se emite Job parcial.
- [ ] **Step 2: Run test to verify it fails.**
- [ ] **Step 3: Implement.** Si la lectura de las páginas muestra que el patrón de búsqueda no es equivalente a un lookup de `tMap` para el caso de duplicados, el soporte queda en «solo llave única demostrada» y el resto en pendiente.
- [ ] **Step 4: Run** `uv run python -m pytest tests/unit/test_lower_data_hash.py tests/unit/test_catalogo_sas.py -q`.
- [ ] **Step 5: Commit.** `hito N m: hash objects, busqueda minima y pendientes con motivo`.

---

### Task B-22: Plan maestro, catálogo y créditos al día

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\docs\plan-reescritura\plan-migrador-general.md` (secciones MG-P1, MG-P4, sección 2 «Hallazgos de Studio», tabla 5.2 y 11b)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\rules\sas\catalogo\*.yaml` (sentencias de DATA step: `MERGE`, `UPDATE`, `MODIFY`, `RETAIN`, `Sum`, `ARRAY`, `DO`, `SELECT`, `DELETE`, `OUTPUT`, `SET`, hash, `LAG`, `DIF`, `CALL SYMPUT`)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\PROGRESS.md`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_catalogo_sas.py`

- [ ] **Step 1: Catálogo.** Para cada sentencia o función cubierta, pasar `estado` a `reconocida` con su `fuente` (`lestmtsref, p. 243`, etc.) y para las parciales dejar `no_reconocida` con `nota` (`MODIFY`, `UPDATEMODE`, hash mutable, `_ERROR_`). Las páginas se toman de este plan, ya verificadas contra el índice.
- [ ] **Step 2: Plan maestro.** Corregir la sección 2 y la tabla 5.2 (`tUnite` compila con conexiones `MERGE`, ver B-9); reemplazar en MG-P4-02 la lista de hitos 166 a 190 por la línea de B-18; sustituir el estado de MG-P1 y MG-P4 por lo medido en B-1 y B-Gate. Los créditos de la 11b se calculan con el método de esa sección tarea por tarea (1 = hecha; 0,5 = parcial con ejecución; 0,25 = casos puntuales; 0 = sin evidencia), no por juicio global.
- [ ] **Step 3: Run** `uv run python -m pytest tests/unit/test_catalogo_sas.py tests/unit/test_referencia_tools.py -q`. Una página citada que no exista en el índice rompe el test: es lo que se quiere.
- [ ] **Step 4: Commit.** `hito N m: catalogo y plan maestro al dia con MG-P1 y MG-P4`.

---

### Task B-Gate: GM1 y L6 completo en B y en lote C

**Criterio de salida (compuerta GM1 del plan maestro, sección 10, más L6):**
1. **GM1:** el plan lógico se construye para todo el corpus `traducible`, sin YAML: `tools/linea_base_plan_logico.py` informa 100 % de operadores construidos por constructor en L0 a L6, y `pendientes` sin ningún código de defecto (solo los de alcance, con página).
2. **L6 completo en B:** todos los casos de `tests/corpus/L6/` (`l6_01` a `l6_38` más los generados) coinciden con su `esperado/` en el intérprete.
3. **L6 completo en A:** ninguno queda en `migrar_pendientes.yaml` salvo los que declaran pendiente de alcance con motivo y página (`MODIFY`, hash mutable, `_ERROR_`).
4. **L6 completo en lote C:** una sola corrida de Studio con todos los casos de L6 que se migran sin pendiente: `uv run python tools/corpus_studio.py lote <casos L6> --jobs <carpeta> --proyecto <proyecto>` para compilar, seguido de `uv run python tools/validar_caso_studio.py <casos>` para ejecutar y comparar. Cuenta aparte los que compilaron y los que ejecutaron y coinciden.

- [ ] **Step 1: Run** la suite completa `uv run python -m pytest -q` y `uv run ruff check .`.
- [ ] **Step 2: Run** `uv run python tools/linea_base_plan_logico.py` y comparar con B-1; pegar las dos cifras.
- [ ] **Step 3: Run** el lote C de L6 (punto 4). Si Studio no conecta, `sgm studio salud` y `docs/guia-validacion-studio.md`, sección 7; no se reinstala nada. La tarea queda con «lote C pendiente» y el motivo, y la compuerta **no** se declara cerrada.
- [ ] **Step 4: Registrar** en `PROGRESS.md` el hito de cierre con: casos por anillo (A, B, C), pendientes por código, horas acreditadas de MG-P1 y MG-P4 con el método de la 11b, y qué quedó fuera con su motivo.
- [ ] **Step 5: Commit.** `hito N m: compuerta GM1 y L6 completo en B y lote C`.

---

## Resumen de horas

| Tareas | Origen | Horas |
|---|---|---|
| B-1 a B-8 (B-1 mide; B-2 a B-4 esquemas; B-5 y B-6 constructores; B-7 SQL; B-8 DATA step y PROC) | MG-P1-02 a MG-P1-06 restantes | 32,5 |
| B-9, B-10 | MG-P4-03 | 10 |
| B-11, B-12 | MG-P4-04 | 16 |
| B-13, B-14 | MG-P4-05 | 14 |
| B-15 | MG-P4-01 resto | 4 |
| B-16 | MG-P4-06 | 8 |
| B-17, B-18 | MG-P4-02 resto | 3 |
| B-19 | MG-P4-07 | 5 |
| B-20 | MG-P4-08 | 4 |
| B-21 | MG-P4-09 | 4 |
| B-22, B-Gate | cierre (reparte el resto de MG-P4 y de GM1) | 1 |
| **Total** | | **101,5** (MG-P1 32,5 + MG-P4 69) |

Las horas por tarea son estimaciones del plan; el crédito real se mide con el método de la sección 11b del plan maestro.

## Dependencias

**Necesita de otros planes**

| De | Tarea | Para qué |
|---|---|---|
| Plan A | compilación y validación en Studio (`tools/validar_caso_studio.py`, cola de validaciones, salud con estados) | B-9, B-10 y B-Gate (lote C); sin Studio esas tareas quedan «lote C pendiente» con su motivo, no se cuentan |
| Plan D1 | MG-P3-01 (motor de expresiones y faltantes) | B-13 (`LAG`, `DIF`) y B-15 (`SELECT/WHEN`): comparan con la semántica de faltantes que fija D1 |
| Plan E | MG-P7-04 (variables de macro de ejecución) | B-20 (`CALL SYMPUT`): el contrato es que el valor llega al contexto del Job, no al código |
| Plan K | K-2 y K-3 (esquemas y datos sintéticos) | los casos nuevos de `L6` usan muestras locales; K aporta el generador cuando haga falta más de una fila por grupo |

**Entrega a otros planes**

| A | Qué |
|---|---|
| Plan C (SQL) | operadores del plan lógico con constructor (`ir/operadores.py`) para uniones y agregados |
| Plan F1 (arquitectura) | `L6` completo y la línea base `tools/linea_base_plan_logico.py` para medir la segmentación |
| Plan G (verificación) | el generador de combinaciones de `OUTPUT` (B-17 y B-18) como modelo de los demás generadores de casos |

## Self-review

- **Cobertura de la spec:** MG-P1-02 a P1-06 en B-1 a B-8; MG-P4-01 resto en B-15; P4-02 en B-17 y B-18; P4-03 en B-9 y B-10; P4-04 en B-11 y B-12; P4-05 en B-13 y B-14; P4-06 en B-16; P4-07 en B-19; P4-08 en B-20; P4-09 en B-21; corrección del plan maestro en B-22; GM1 y `L6` en B-Gate.
- **Hallazgo que cambia el plan maestro:** `tUnite` compila con conexiones `MERGE` desde el hito 125m, pero `l0_09` nunca se ejecutó: B-9 lo investiga en Studio antes de elegir mecanismo y B-22 corrige la sección 2.
- **Archivos por encima de 300 líneas:** `interprete.py`, `lower_data.py` y `desde_plan_map.py`; las tareas que los tocan extraen módulos primero.
- **Proporción:** 22 tareas más la de cierre para 101,5 h; los cuerpos de funciones los decide quien implementa.
- **Pendiente de verificar al ejecutar:** las páginas de `PROC IMPORT`, hash objects y `OBS=` en la guía se localizan en la primera tarea que las usa; si no existe página, queda `Pendiente:`.
