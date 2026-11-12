# MG-D1: Expresiones y funciones Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Que toda expresión y función SAS del corpus (`L0` a `L8`) tenga una sola semántica demostrada por la guía de SAS, ejecutada por el intérprete (anillo B), traducida a Java de Talend (anillo A) y validada en Studio (anillo C): motor de expresiones con faltantes, funciones de texto, numéricas, de fecha, `INPUT`/`PUT` con informats y formats, `PRX*`, formatos propios de `PROC FORMAT`, el documento `docs/funciones.md` generado y el cierre de las brechas del oráculo de SQL. Cierra MG-P3.

**Architecture:** Hoy hay **tres implementaciones** de la misma semántica que se contradicen sin que nadie lo vea: (1) el oráculo de Python `tools/corpus_semantica_funciones.py` (el único que ejecuta `tests/corpus/semantica/vectores.yaml`), (2) el intérprete del plan `src/sgm/migrar/interprete.py` (`_funcion`, `_valor`) y (3) el traductor a Java `src/sgm/expressions/talend_tabla.py`. Este plan las ata con tres piezas: los vectores se ejecutan por el intérprete y por el oráculo y los dos deben coincidir (D1-3); cada familia de funciones entra con vectores con página, una función de intérprete en su módulo (`interprete_*.py`, menos de 300 líneas), la del oráculo y la traducción a Java; y los vectores se convierten solos en casos `L4` (D1-5), de modo que el mismo vector corre en B y en el lote C de Studio. Lo que una página no demuestra queda como `Pendiente:` con su código, no como un valor supuesto.

**Tech Stack:** Python 3.12, pytest, ruff, `sqlglot` (ya usado por el intérprete), `pyyaml`; `uv run python -m pytest` y `uv run python -m sgm.cli` (en este Windows `uv run pytest` puede bloquearse por Control de aplicaciones).

**Spec:** `docs/plan-reescritura/plan-migrador-general.md` (MG-P3-01 a MG-P3-09, sección 5.7 y sección 11b) y `docs/superpowers/plans/2026-11-11-ruta-al-100.md`.

**Horas del plan maestro cubiertas:** MG-P3 restante 65,5 h (80 h menos 14,5 h acreditadas, sección 11b). MG-P3-01 9 h, P3-02 10 h, P3-03 7,5 h, P3-04 12 h, P3-05 8 h, P3-06 6 h, P3-07 4 h, P3-08 4 h, P3-09 4 h y 1 h del cierre `D1-Gate`.

**Series de hitos:** `n` (carril de Byron, D1-1 a D1-22 y D1-Gate). La letra va en el título de la entrada de `PROGRESS.md` y en el mensaje del commit. El Plan C usa también `n` para sus tareas C-16 a C-23 (procedimientos); no es conflicto porque el número de hito es único en todo el repositorio: se toma el siguiente libre al ejecutar cada tarea.

## Global Constraints

- Sin `git push`, sin `--amend`. Un commit local por hito: `hito N n: <resumen>`, terminado con la línea `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Antes de escribir, buscar el último `## Hito` de `PROGRESS.md` (al redactar este plan era el 198) y sumar uno; si otra sesión ya tomó el número, tomar el siguiente. No renumerar entradas publicadas.
- No tocar `tools/ci.py`, `tools/validacion.py`, `tools/instalar_ganchos.py`, `README.md` ni `.githooks/` (son del Plan A y están sin commitear).
- Nada de nombres de scripts de ejemplo (`cod1`, `cod2`, `cars_poc`, `exogena`, `split2`, `split3`, `executeBulkload`, `waitForBulkLoads`, `bulkload_generic`) en `src/` ni `rules/`; lo vigila `tests/unit/test_no_script_specific_names.py`.
- **Sin página, no hay equivalencia.** Cada función cita `<guía>, p. N` con una página que exista en `docs/referencia/sas/<guía>.INDEX.md` (`lefunctionsref`, `leforinforref`, `lrcon`, `lesysoptsref`, `proc`). No leer el PDF ni el `.txt` entero: ubicar la sección en el `.INDEX.md` y la página con `grep -n "<!-- página N -->" docs/referencia/sas/<guía>.txt`. Los números de página son las del PDF (las del índice). Lo que este plan llama «esperado deducido» es un valor que sale de la regla escrita en la página pero que la página no da como ejemplo; el paso que lo fija **lee la página antes**, y si la página lo contradice se corrige el vector (con su cita), nunca el código para que coincida.
- **Vectores:** un vector nuevo va en `tests/corpus/semantica/vectores.yaml` con los campos que ya exige `tests/unit/test_corpus_semantica.py::test_cada_vector_tiene_campos_y_fuente` (`id`, `funcion`, `entrada`, `esperado`, `fuente_url`, `cita`, `confianza`). Además de la URL, el `cita` empieza con `<guía>, p. N:` para que `D1-21` pueda listar la página. `confianza: documentado` solo si la página da el resultado; `deducido` si sale de la regla; `incierto` si no hay fuente (no cuenta como fallo, y la función queda `Pendiente:` para ese caso).
- **Catálogo:** `tests/unit/test_catalogo_sas.py` exige que el literal `(p. N)` de cada `fuente` esté en el `.INDEX.md` de su guía, y que cada función `reconocida` esté en `talend_tabla._FUNCTIONS` o en una regla de `rules/sas/functions/`. Por eso una función que solo está en el intérprete queda `no_verificada` con la `nota` «intérprete y oráculo sí; Java no», y pasa a `reconocida` en la tarea que la traduce a Java. Las funciones nuevas de la guía que no aparecen en el programa grande van a `rules/sas/catalogo/funciones-guia.yaml` (archivo nuevo, creado en D1-1; `funciones-usadas.yaml` es solo de lo que usa el programa grande). El esquema `schemas/rules/catalogo.schema.json` es cerrado: cada entrada lleva solo `id`, `nombre`, `fuente`, `estado` y `nota`.
- **Casos del corpus:** los casos nuevos de este plan van a `tests/corpus/L4/` con la numeración `l4_100` a `l4_199` (reservada a este plan; `l4_21` a `l4_23` son del Plan B). Los de capa B se generan: lo que no sale de un vector se declara en `tools/corpus_lib/especificaciones_l4c.py` (módulo nuevo; `especificaciones_l4.py` y `especificaciones_l4b.py` ya van en 258 y 224 líneas) y se registra en `tools/corpus_lib/generar_entradas_l4l6.py` (línea 179, `"L4": {**ESPECIFICACIONES_L4, **ESPECIFICACIONES_L4B}`). Su esperado sale del oráculo de Python y se contrasta con el intérprete en `tests/unit/test_migrar_corpus_anillo_b.py` (`NIVELES` ya incluye `L4`).
- **Una función, cuatro lugares.** Cada función nueva se escribe en: `tests/corpus/semantica/vectores.yaml` (vectores), `tools/corpus_semantica_*.py` (oráculo), `src/sgm/migrar/interprete_*.py` (intérprete) y `src/sgm/expressions/talend_*.py` más `talend_tabla.py` (Java). Una tarea no se cierra con la función en menos de los tres primeros; el cuarto es obligatorio salvo `Pendiente:` con código `P-JAVA-xxx` y su motivo.
- No borrar ni debilitar pruebas. Un caso que no se puede traducir queda en `tests/corpus/migrar_pendientes.yaml` o en `CONOCIDOS` de `tests/unit/test_migrar_corpus_anillo_b.py` con su motivo.
- Archivos de menos de 300 líneas. Ya pasan de 300 en la zona de este plan: `src/sgm/migrar/interprete.py` (1103), `src/sgm/expressions/talend_funciones.py` (416) y `src/sgm/ir/lower_data.py` (770). `talend_parser.py` está en 300 exactos y `tools/corpus_semantica_funciones.py` en 260. D1-2 y D1-6 extraen primero, en un paso propio y sin cambio de comportamiento; ninguna tarea suma líneas a esos archivos.
- Código e identificadores en inglés (los nombres de las funciones SAS se conservan); comentarios, docstrings y mensajes en español.
- Después de cada tarea: `uv run python -m pytest -q` y `uv run ruff check src tests tools` en verde. Para iterar se corre solo el archivo de la tarea (`-p no:cacheprovider`); la suite completa se corre al cerrar cada tarea.
- Studio: se usa en un solo punto, el lote C de la tarea que lo pide y de `D1-Gate`, con `tools/validar_caso_studio.py <caso>` y `tools/corpus_studio.py lote ...`. Si `sgm studio salud` no conecta, no reinstalar nada ni cambiar `talend-mcp` (ver `docs/guia-validacion-studio.md`, sección 7): la tarea queda con «lote C pendiente» y su motivo, y no se cuenta como pasada.

## Review Focus

- **Los faltantes no son los de Java ni los de Python.** Un faltante numérico es menor que cualquier número y dos faltantes son iguales (`lrcon`, p. 125); un texto en blanco es faltante y es igual a `''`; los blancos finales no cuentan al comparar (`lrcon`, p. 144); una operación aritmética con un faltante da faltante (`lrcon`, p. 128). `SUM`, `MEAN`, `MIN`, `MAX` ignoran faltantes y `+` no (`lefunctionsref`, p. 1580). Tests en D1-3, D1-4 y D1-10.
- **Los tres motores deben dar lo mismo.** Un vector pasa si lo pasan el oráculo y el intérprete, y el caso `L4` que sale de él coincide en B y en C. Si dos motores difieren, se resuelve con la página antes de mirar Talend. Tests en D1-3 y D1-5.
- **La fecha de SAS es el número de días desde 1960-01-01**, sin horas ni zona. Los resultados se comparan como número; `TODAY()` y `DATE()` dependen del reloj y no tienen vector: se prueban con una fecha inyectada. Fin de mes y años bisiestos en D1-12 a D1-14.
- **`PUT` y `INPUT` no son `String.valueOf` ni `Double.parseDouble`:** un formato numérico justifica a la derecha con blancos a la izquierda; un informat de fecha lee un siglo según `YEARCUTOFF=` (`lesysoptsref`, p. 432); un valor que no cabe en el ancho se emite con otro formato o con asteriscos. Lo que la página no fija queda `Pendiente:`. Tests en D1-15 a D1-17.
- **Java y Perl no usan la misma sintaxis de expresiones regulares:** las diferencias se documentan en `docs/prx-diferencias-java.md` y una expresión con una construcción que Java no tiene queda `Pendiente:`, no traducida. Tests en D1-18 y D1-19.
- **Ningún pase nuevo puede cambiar la firma de los Jobs ya validados** en L0 a L4 (los `test_golden*.py` y `test_ir_operadores_corpus.py` deben seguir idénticos). Cada extracción de módulo se mide con la misma tanda antes y después.

---

## Parte I. MG-P3-01: motor de expresiones (serie `n`, 9 h)

### Task D1-1: Línea base e inventario de funciones (MG-P3-01; serie `n`)

Hoy no hay una cifra de cuántas funciones de la guía existen en cada motor ni de cuántos vectores ejecuta el intérprete (ninguno: `tests/unit/test_corpus_semantica.py` solo corre el oráculo). Esta tarea crea el inventario que usan D1-3, D1-21 y D1-Gate.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\funciones_inventario.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\rules\sas\catalogo\funciones-guia.yaml`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_funciones_inventario.py`

**Interfaces:**
- Consumes: `sgm.expressions.talend_tabla._FUNCTIONS: dict[str, Callable]`, `corpus_semantica_funciones.FUNCIONES: dict[str, Callable]` (`tools/corpus_semantica_funciones.py:231`), `corpus_semantica.cargar_vectores(ruta: Path = RUTA_VECTORES) -> list[dict]` (`tools/corpus_semantica.py:29`), el nombre de las entradas de `rules/sas/catalogo/funciones-usadas.yaml`, y `rules/sas/functions/*.yaml` (campo `sas`).
- Produces:
  ```python
  def inventario(repo: Path) -> dict[str, dict]:
      """Por función SAS (minúsculas): {"talend": bool, "oraculo": bool, "interprete": bool,
      "vectores": int, "catalogo": "reconocida"|"no_reconocida"|"no_verificada"|None,
      "pagina": "lefunctionsref.pdf, p. N"|None}. `interprete` es False hasta D1-2."""
  def resumen(inv: dict[str, dict]) -> dict:
      """{"funciones": n, "en_talend": n, "en_oraculo": n, "en_interprete": n,
      "con_vectores": n, "vectores_en_interprete": n, "sin_catalogo": [nombres]}"""
  ```
  Salida JSON en `out/linea_base_funciones.json` (no versionada) al correr `tools/funciones_inventario.py` como programa.

- [ ] **Step 1: Write the failing test.** Con un repo mínimo en `tmp_path` (una función `trim` en una tabla simulada pasada por parámetro, un vector de `trim` y una entrada de catálogo `reconocida` con `fuente: lefunctionsref.pdf, p. 1624`), `inventario` devuelve `{"trim": {"talend": True, "oraculo": True, "interprete": False, "vectores": 1, "catalogo": "reconocida", "pagina": "lefunctionsref.pdf, p. 1624"}}`; `resumen` cuenta `con_vectores == 1` y `vectores_en_interprete == 0`. Para poder simular las tablas, `inventario(repo, talend=None, oraculo=None, interprete=None)` acepta diccionarios opcionales que sustituyen a los reales.
- [ ] **Step 2: Run test to verify it fails.** `uv run python -m pytest tests/unit/test_funciones_inventario.py -q -p no:cacheprovider`; esperado: no existe el módulo.
- [ ] **Step 3: Implement** `inventario` y `resumen` con `yaml.safe_load` y las tablas reales. Crear `rules/sas/catalogo/funciones-guia.yaml` con el encabezado (`id: funciones-guia`, `kind: catalogo`, `version: 1`, `description`: «Funciones de la guía de SAS que este repo implementa o planea, con su página; las del programa grande están en funciones-usadas.yaml») y una sola entrada de arranque, `compbl-function` (`nombre: COMPBL Function`, `fuente: lefunctionsref.pdf, p. 572`, `estado: no_verificada`, `nota: 'sin oráculo, intérprete ni Java; lo cierra D1-8'`). En `tests/unit/test_catalogo_sas.py` (líneas 70 y 77) iterar también `funciones-guia` para páginas e implementación.
- [ ] **Step 4: Run** `uv run python tools/funciones_inventario.py` y pegar en `PROGRESS.md`, como línea base de este plan: funciones por motor, vectores totales (hoy 69, de los cuales cero se ejecutan por el intérprete) y las funciones de la sección 5.7 del plan maestro sin entrada de catálogo. Anotar también los `xfail` de expresiones que hay hoy y su motivo: `CONOCIDOS` de `tests/unit/test_migrar_corpus_anillo_b.py` tiene 5 entradas (`l2_12`, `l3_07`, `l3_09`, `l5_08`, `l5_09`, ninguna es de funciones) y `tests/corpus/migrar_pendientes.yaml` tiene 16, de los cuales `l0_12_bandera_numerica` (`P-FILTRO-SIN-TRADUCIR`) y `l4_20_put_fechas_pendiente` (`P-ASIGNACION-SIN-TRADUCIR`) son de expresiones; el «20 xfail» que cita el plan maestro (hito 107) está superado, y esta tarea corrige esa cifra en el plan maestro en el mismo cambio.
- [ ] **Step 5: Run** `uv run python -m pytest tests/unit/test_funciones_inventario.py tests/unit/test_catalogo_sas.py -q -p no:cacheprovider` y `uv run ruff check src tests tools`. **Commit** `hito N n: inventario de funciones por motor y linea base de MG-P3` (con la línea `Co-Authored-By`).

---

### Task D1-2: Extraer las funciones del intérprete a módulos propios (MG-P3-01; serie `n`)

`interprete.py` tiene 1103 líneas; `_funcion` y sus ayudas (líneas 108 a 239) no dependen del resto. Esta tarea no cambia comportamiento. Los Planes B y C también extraen de `interprete.py` (MERGE y estado por fila, uniones y agregados): esta tarea mueve **solo** las líneas 108 a 239 y la clase `NoSoportadoEnInterprete`; quien llegue segundo rebasea y la suite no cambia.

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\interprete.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\interprete_errores.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\interprete_funciones.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\interprete_texto.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\interprete_numerico.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\interprete_formatos.py`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_interprete_funciones.py` (nuevo) y `tests\unit\test_migrar_interprete.py` (sin cambios: debe seguir verde)

**Interfaces:**
- Consumes (de `interprete.py`, a mover sin cambiar el cuerpo): `NoSoportadoEnInterprete(kind: str, detalle: str = "")` (línea 53), `_funcion(nombre: str, argumentos: list) -> object` (108), `_texto_substr(valor: object, funcion: str) -> str` (172), `_input_wd(argumentos: list) -> float | None` (180), `_compress(argumentos: list) -> str` (198), `_scan(argumentos: list) -> str` (222), `semantica.es_faltante(valor)`, `semantica.como_numero(valor) -> float | None`, `semantica.como_texto(valor) -> str`.
- Produces:
  ```python
  # interprete_errores.py
  class NoSoportadoEnInterprete(RuntimeError): ...   # misma firma; interprete.py la reexporta
  # interprete_funciones.py
  Funcion = Callable[[list], object]
  FUNCIONES: dict[str, Funcion]        # unión de los diccionarios FUNCIONES de cada módulo de familia
  def llamar(nombre: str, argumentos: list) -> object:
      """Quita los prefijos `sgm_` y `row_`, busca en FUNCIONES y lanza
      NoSoportadoEnInterprete("funcion", nombre) si no existe."""
  # interprete_texto.py / interprete_numerico.py / interprete_formatos.py
  FUNCIONES: dict[str, Funcion]        # texto: trim, strip, upcase, lowcase, length, left, substr,
                                       # substrn, compress, scan, coalescec; numerico: mean, min, max,
                                       # sum, abs, coalesce, missing; formatos: input
  ```

- [ ] **Step 1: Medir.** `uv run python -m pytest -q -p no:cacheprovider tests/unit/test_migrar_interprete.py tests/unit/test_migrar_corpus_anillo_b.py tests/unit/test_golden.py tests/unit/test_golden_equivalencia.py tests/unit/test_ir_operadores_corpus.py`; anotar el conteo de pasadas y de `xfailed` (la referencia que no debe cambiar).
- [ ] **Step 2: Write the failing test** en `test_interprete_funciones.py`: `llamar("sgm_trim", ["ab  "]) == "ab"`, `llamar("row_sum", [1, None, 3]) == 4.0`, `llamar("coalesce", [None, "", "x"]) == "x"`, `llamar("no_existe", [1])` lanza `NoSoportadoEnInterprete` con `kind == "funcion"` y `detalle == "no_existe"`; y `from sgm.migrar.interprete import NoSoportadoEnInterprete` sigue funcionando (es la misma clase que la de `interprete_errores`).
- [ ] **Step 3: Run test to verify it fails.** `uv run python -m pytest tests/unit/test_interprete_funciones.py -q -p no:cacheprovider`; esperado: no existe el módulo.
- [ ] **Step 4: Extraer.** Mover la clase a `interprete_errores.py`; partir el cuerpo de `_funcion` en una función por nombre dentro de cada módulo de familia (cada una de 1 a 10 líneas, con la lógica idéntica) y armar `FUNCIONES`; `interprete_funciones.llamar` hace el despacho. En `interprete.py`, `_funcion` queda como `return llamar(nombre, argumentos)` y se importan los nombres que otros módulos ya usan (`_input_wd`, `_compress`, `_scan` solo si alguien los importa: comprobar con `Grep` por `from sgm.migrar.interprete import`).
- [ ] **Step 5: Run** la tanda del paso 1 más el test nuevo: mismas pasadas y mismos `xfailed`; cero cambios en el golden. `wc -l` de los módulos nuevos: cada uno menos de 300 líneas; `interprete.py` baja unas 140 líneas y sigue sobre 300 (la deuda restante queda anotada en `PROGRESS.md`).
- [ ] **Step 6: Run** suite completa y `uv run ruff check src tests tools`. **Commit** `hito N n: funciones del interprete en modulos propios, sin cambio de comportamiento`.

---

### Task D1-3: Todos los vectores se ejecutan en el intérprete y los dos motores coinciden (MG-P3-01; serie `n`)

El aceptable de MG-P3-01 es «todos los vectores de `vectores.yaml` ejecutados en B». Hoy `tools/corpus_semantica.py` los corre solo por el oráculo. Las convenciones de los vectores no son las del intérprete: `input` lleva el informat como dos números (`["23.0", 6, 2]` es `w=6`, `d=2`), `cmp` lleva `[izquierda, operador, derecha]` y `is_missing`, `concat`, `trim_concat` y `catx` son nombres del oráculo. Un adaptador las traduce; el esperado `"faltante"` es `None` o un texto en blanco.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\interprete_vectores.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\corpus_semantica.py` (130 líneas: sigue bajo 300)
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_interprete_vectores.py`

**Interfaces:**
- Consumes: `corpus_semantica.verificar(ruta: Path = RUTA_VECTORES) -> dict` (devuelve `{"total", "por_confianza", "pasan", "fallos", "inciertos"}`), `corpus_semantica.ejecutar_vector(vector: dict) -> object`, `corpus_semantica._coincide(obtenido, esperado) -> bool`, `interprete_funciones.llamar(nombre, argumentos)` (D1-2), `semantica.comparar(izquierda, derecha) -> int`.
- Produces:
  ```python
  # interprete_vectores.py
  def evaluar_vector(funcion: str, entrada: list) -> object:
      """Ejecuta un vector con el intérprete. `None` en la entrada es un faltante; el resultado
      faltante sale como None. Adapta: input [campo, w, d] a informat 'w.d'; cmp [a, op, b] a
      semantica.comparar; is_missing a semantica.es_faltante; concat, trim_concat y catx a su
      traducción por `||`, TRIM y CATX del intérprete."""
  # tools/corpus_semantica.py
  def verificar(ruta: Path = RUTA_VECTORES, motor: str = "oraculo") -> dict: ...  # motor: "oraculo" | "interprete"
  # CLI: python tools/corpus_semantica.py verificar --motor interprete
  ```

- [ ] **Step 1: Write the failing tests** en `test_interprete_vectores.py`: (a) `evaluar_vector("scan", ["a b c", 2])` da `"b"` (ya documentado por `scan-01`); (b) `evaluar_vector("input", ["23.0", 6, 2])` da `23.0` (vector `input-01`, `leforinforref`, p. 556) y `evaluar_vector("input", ["0023", 6, 2])` da `0.23` (`input-06`, deducido); (c) `evaluar_vector("cmp", [None, "<", 500])` da `True` (`cmp-missing-01`, `lrcon`, p. 125); (d) `evaluar_vector("is_missing", ["   "])` da `True`; (e) `verificar(motor="interprete")["fallos"] == []` para todo vector `documentado` o `deducido`; (f) para cada vector no `incierto`, el resultado del oráculo y el del intérprete coinciden (`_coincide`); un vector inventado con un esperado que el oráculo cumple y el intérprete no hace que (f) falle con el `id` del vector.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_interprete_vectores.py -q -p no:cacheprovider`; esperado: no existe el módulo.
- [ ] **Step 3: Implement** `evaluar_vector` y el parámetro `motor` de `verificar` (`"oraculo"` conserva el comportamiento de hoy). Correr `uv run python tools/corpus_semantica.py verificar --motor interprete` y pegar la lista de vectores que fallan: es el trabajo del paso siguiente.
- [ ] **Step 4: Corregir el intérprete** (nunca el vector) hasta que el paso (e) pase: cada fallo se arregla en el módulo de la función (`interprete_texto.py`, `interprete_numerico.py` o `interprete_formatos.py`) con un test propio en `tests/unit/test_interprete_funciones.py`. Si un vector contradice su página, se lee la página (`grep -n "<!-- página N -->" docs/referencia/sas/<guía>.txt`) y se corrige el vector y su `cita` en el mismo commit, anotándolo en `PROGRESS.md` («Decisiones»). Un vector que ni el oráculo ni la página sostienen pasa a `confianza: incierto`, no se borra.
- [ ] **Step 5: Run** `uv run python -m pytest tests/unit/test_interprete_vectores.py tests/unit/test_corpus_semantica.py -q -p no:cacheprovider`, la tanda del golden y `uv run ruff check src tests tools`. **Commit** `hito N n: los vectores de semantica se ejecutan en el interprete y coinciden con el oraculo`.

---

### Task D1-4: Despacho universal de funciones y operadores con faltantes (MG-P3-01; serie `n`)

`_arbol` renombra a `sgm_<nombre>` solo siete funciones (`_FUNCIONES_SAS`, `interprete.py:50`: `input|left|substrn|substr|coalescec|compress|scan`); las demás pasan por los nodos propios de `sqlglot`, y `_valor` no tiene caso para `exp.Length`, `exp.Anonymous` con nombres de la guía como `PROPCASE` ni `exp.Substring`. Un `LENGTH(x)` en un `DERIVE` lanza `NoSoportadoEnInterprete`. Esta tarea hace que **toda** llamada de la tabla de funciones despache por `llamar`, y revisa los operadores (`IN`, `BETWEEN`, `LIKE`, `||`, lógicos) contra la guía.

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\interprete.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\interprete_operadores.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\semantica\vectores.yaml`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\corpus_semantica_funciones.py`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_interprete_operadores.py`

**Interfaces:**
- Consumes: `_arbol(expresion: str)` (`interprete.py:73`), `_valor(nodo, fila: dict) -> object` (268), `_verdad(valor: object) -> bool` (86), `_aritmetica(operador: str, izquierda: object, derecha: object) -> object` (241), `interprete_funciones.FUNCIONES`, `semantica.iguales / menor / mayor_igual / menor_igual`.
- Produces:
  ```python
  # interprete.py
  _FUNCIONES_SAS: re.Pattern   # se construye con los nombres de interprete_funciones.FUNCIONES,
                               # menos {"sum", "min", "max", "count", "avg"} (agregados del plan)
  # interprete_operadores.py
  def concatenar(izquierda: object, derecha: object) -> str: ...
  def pertenece(buscado: object, opciones: list[object]) -> bool: ...   # IN con la igualdad de SAS
  def entre(valor: object, bajo: object, alto: object) -> bool: ...     # BETWEEN inclusivo
  def parecido(texto: object, patron: object) -> bool: ...              # LIKE, % y _
  ```
  Los cuatro cuerpos salen de los casos `exp.DPipe`, `exp.In`, `exp.Between` y `exp.Like` de `_valor` (líneas 319 a 346), sin cambiar su lógica.

**Vectores nuevos (`confianza: deducido` salvo los marcados; la página se lee antes de fijar el esperado):**

| id | funcion | entrada | esperado | página |
|---|---|---|---|---|
| `cmp-in-01` | `in` | `[null, [1, 2]]` | `false` | `lrcon`, p. 144 (un faltante no es igual a 1 ni a 2) |
| `cmp-in-02` | `in` | `["AB ", ["AB", "CD"]]` | `true` | `lrcon`, p. 144 (blancos finales no cuentan) |
| `cmp-between-01` | `between` | `[null, 0, 10]` | `false` | `lrcon`, p. 125 (el faltante es menor que 0) |
| `cmp-between-02` | `between` | `[10, 0, 10]` | `true` | `lrcon`, p. 144 (inclusivo) |
| `cmp-like-01` | `like` | `["ABC", "A%"]` | `true` | `sqlproc`, p. 73 (verificar) |
| `ar-faltante-01` | `suma_mas` | `[1, null]` | `faltante` | `lrcon`, p. 128 (propagación) |
| `ar-faltante-02` | `sum` | `[1, null]` | `1` | `lefunctionsref`, p. 1580 |
| `cat-01` | `concat` | `["ab ", "c"]` | `"ab c"` | `lrcon`, p. 151 |

El oráculo gana las funciones `in`, `between`, `like` y `suma_mas` (de 3 a 6 líneas cada una; usa su propio `cmp` de `tools/corpus_semantica_funciones.py:211`, no `sgm.migrar.semantica`, para que sigan siendo dos implementaciones). `concatenar` usa el texto tal cual, **sin** `rstrip` (hoy `_valor` pasa por `como_texto`, que recorta blancos finales y daría `"abc"` en `cat-01`); el recorte de blancos finales es de la comparación, no de `||`. `Pendiente: P-CONCAT-LONGITUD-VARIABLE`: `||` sobre una variable con `LENGTH` mayor que su contenido añade los blancos de relleno de esa longitud (`lrcon`, p. 151), y el intérprete recibe los valores del CSV sin relleno; mientras el esquema no traiga la longitud (Plan B, B-3 y B-4), `concatenar` no rellena y lo declara en su docstring.

- [ ] **Step 1: Write the failing tests** en `test_interprete_operadores.py`: `_valor(_arbol("length(a)"), {"a": "abc   "}) == 3` (`LENGTH` ignora los blancos finales, `lefunctionsref`, p. 1180; hoy lanza `NoSoportadoEnInterprete` porque `sqlglot` lo lee como `exp.Length`); `_valor(_arbol("UPCASE(a)"), {"a": "ab"}) == "AB"` por el camino `sgm_upcase`; `_valor(_arbol("no_es_funcion_sas(a)"), {"a": 1})` sigue lanzando `NoSoportadoEnInterprete` (una función fuera de la tabla no se adivina); los ocho vectores de la tabla pasan con `verificar(motor="interprete")`; `pertenece(None, [1, 2]) is False`, `entre(None, 0, 10) is False`.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_interprete_operadores.py -q -p no:cacheprovider`; esperado: `NoSoportadoEnInterprete: expresion: Length: ...`.
- [ ] **Step 3: Implement.** Construir `_FUNCIONES_SAS` a partir de las claves de `FUNCIONES` (ordenadas de la más larga a la más corta, con `\b` y `(?=\()`), de modo que `substrn` no quede cortado por `substr`; mover los cuatro operadores a `interprete_operadores.py`; agregar los vectores y las cuatro funciones del oráculo.
- [ ] **Step 4: Run** los tests del paso 1, `tests/unit/test_corpus_semantica.py`, `tests/unit/test_migrar_interprete.py` y la tanda del golden; mismas pasadas que en D1-2.
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N n: despacho universal de funciones y operadores con faltantes en el interprete`.

---

### Task D1-5: Los vectores se vuelven casos `L4` y corren en el lote C (MG-P3-01; serie `n`)

El segundo aceptable de MG-P3-01 es «en lote C». Un vector no es un Job: esta tarea lo convierte en un caso `L4` mínimo (`DATA` con una asignación) para que el mismo vector corra en B (`test_migrar_corpus_anillo_b.py`) y en Studio. El esperado sale del oráculo y se compara con el `esperado` del vector: si difieren, el generador se detiene.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\corpus_lib\especificaciones_l4_vectores.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\corpus_lib\generar_entradas_l4l6.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\L4\l4_100_vec_scan_2\` y sucesivos (`caso.yaml`, `programa.sas`, `entradas\*.csv`, `esperado\*.csv`; los escribe el generador)
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_corpus_l4_vectores.py`

**Interfaces:**
- Consumes: `corpus_semantica.cargar_vectores(ruta) -> list[dict]`, `corpus_semantica_funciones.evaluar(funcion: str, *args) -> object`, el formato de especificación de `especificaciones_l4.py` (`entrada = (nombre, columnas, filas, numericas)`, `asignaciones = [(variable, columna, pasos, texto_sas)]`, `salida`, `fuentes`, `invariantes`, `razonamiento`, `construcciones`), `generar_caso(nivel: str, nombre: str, spec: dict, corpus: Path = CORPUS) -> list[Path]` (`generar_entradas_l4l6.py:140`).
- Produces:
  ```python
  # especificaciones_l4_vectores.py
  FUNCIONES_CON_CASO: dict[str, dict]
  # {"scan": {"literales": [1], "columnas": ["TEXTO"], "sas": "scan({texto}, {1})"}, ...}
  # `literales`: posiciones de `entrada` que van como literales en el programa (el informat de INPUT,
  # la longitud de SUBSTR); el resto son columnas.
  def especificaciones_de_vectores(vectores: list[dict]) -> dict[str, dict]:
      """Un caso por (función, tupla de literales): una fila por vector, la columna de entrada, la
      columna R con el resultado y el texto SAS de la asignación. Nombre `l4_<n>_vec_<funcion>_<k>`
      con `n` desde 100, estable: el orden es el de FUNCIONES_CON_CASO y el del archivo de vectores.
      Si el oráculo y el `esperado` del vector difieren lanza ValueError con el id del vector."""
  ESPECIFICACIONES_L4V: dict[str, dict]
  ```

- [ ] **Step 1: Write the failing test** en `test_corpus_l4_vectores.py`: con dos vectores de `scan` (`["a b c", 2]` esperado `"b"` y `["a b c", 5]` esperado `" "`, como `scan-01` y `scan-02`; `lefunctionsref`, p. 1504) devuelve **dos** casos, uno por cada tupla de literales (`l4_100_vec_scan_2` y `l4_101_vec_scan_5`), cada uno con su fila; un vector con `esperado` distinto del oráculo lanza `ValueError` con el id. Con el archivo real, la regeneración de `tests/corpus/L4` da los mismos bytes dos veces seguidas (reproducible).
- [ ] **Step 2: Run test to verify it fails.** `uv run python -m pytest tests/unit/test_corpus_l4_vectores.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement** el módulo y registrar `ESPECIFICACIONES_L4V` en `ESPECIFICACIONES["L4"]`; `generar_caso` escribe también `programa.sas` cuando la especificación trae `programa` (campo nuevo opcional: el texto con `PROC IMPORT`, el `DATA` y el `PROC EXPORT`). Arrancar con las funciones que ya tienen vector y oráculo: `input`, `left`, `compress`, `strip`, `trim`, `upcase`, `lowcase`, `substr`, `substrn`, `scan`, `coalescec`, `round`. Las demás entran con su tarea (cada tarea de familia agrega su fila a `FUNCIONES_CON_CASO`).
- [ ] **Step 4: Run** `uv run python tools/corpus.py generar` (o el subcomando que regenera `L4`; comprobar con `uv run python tools/corpus.py --help`), `tests/unit/test_corpus_l4l6.py`, `tests/unit/test_migrar_corpus_anillo_b.py -k L4` y `tests/unit/test_migrar_corpus_l4_a.py`. Los casos nuevos que el anillo A no traduzca (por ejemplo un informat sin tipo) se anotan en `tests/corpus/migrar_pendientes.yaml` con su código; los que el anillo B no ejecute, en `CONOCIDOS` con el motivo. Ninguno se borra.
- [ ] **Step 5: Lote C.** `uv run python tools/corpus_studio.py lote <casos l4_1xx> --jobs <carpeta> --proyecto <proyecto>` y después `uv run python tools/validar_caso_studio.py <casos>`. Cuenta aparte compilaron y ejecutaron-y-coinciden. Si Studio no conecta: «lote C pendiente» con el motivo, el criterio de MG-P3-01 queda sin cerrar y `D1-Gate` lo reintenta.
- [ ] **Step 6: Run** `uv run ruff check src tests tools`. **Commit** `hito N n: vectores de semantica convertidos en casos L4 de B y C`.

---

## Parte II. MG-P3-02: funciones de texto (serie `n`, 10 h)

### Task D1-6: Una sola definición de cada función Java de Talend (MG-P3-02; serie `n`)

`talend_funciones.py` (416 líneas) define `_strfn`, `_cat`, `_substr`, `_scan`, `_compress`, `_intnx` e `_intck`, que **también** están en `talend_funciones_texto.py` y `talend_funciones_fecha.py`; `talend_tabla.py` importa las fechas de la copia nueva y todo lo demás de la vieja. Además, `talend_functions.py`, `talend_functions_dates.py`, `talend_functions_numeric.py`, `talend_functions_strings.py` y `talend_core.py` no los importa nadie fuera de ellos (al redactar, `Grep` de `talend_functions` y `talend_core` en `src`, `tests` y `tools` solo da coincidencias entre esos mismos archivos). Dos copias de `_scan` que se pueden desviar son el origen exacto de los errores que este plan quiere evitar. Esta tarea no cambia comportamiento.

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\expressions\talend_funciones.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\expressions\talend_tabla.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\expressions\talend_funciones_texto.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\expressions\talend_funciones_numerico.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\expressions\talend_funciones_formato.py`
- Delete (solo si el `Grep` del paso 2 sigue dando cero referencias externas): `src\sgm\expressions\talend_functions.py`, `talend_functions_dates.py`, `talend_functions_numeric.py`, `talend_functions_strings.py`, `talend_core.py`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_talend_modulos.py`

**Interfaces:**
- Consumes: el constructor `build(_p: _P, args: list[E]) -> E` de cada función (`_routine(routine: str, method: str, arity: int | None = None)`, `_strfn(template: str, arity: int = 1)`, `_cat(trim: bool, sep: bool = False)`), `E(java: str, kind: str = "any", literal: str | None = None)`, `Unsupported` y `_need(args: list[E], low: int, high: int | None = None, name: str = "")` de `talend_base.py`.
- Produces: ninguna firma nueva. `talend_funciones_numerico.py` recibe `_round`, `_unary_math`, `_int`, `_coalesce`, `_ifv` y `_aggregate` (líneas 199 a 266 de `talend_funciones.py`); `talend_funciones_formato.py` recibe `_input`, `_put` y `_clean` (268 a 343 y 404 en adelante). Cada uno con menos de 300 líneas; `talend_funciones.py` queda con lo que no tiene copia o desaparece si queda vacío.

- [ ] **Step 1: Write the failing test** en `test_talend_modulos.py` con `ast`: (a) ninguna función de nivel de módulo se define en dos archivos `src/sgm/expressions/talend_*.py`; (b) cada `talend_*.py` tiene a lo sumo 300 líneas (hoy `talend_funciones.py` falla con 416; `talend_parser.py` está en 300 y pasa); (c) los nombres de `talend_tabla._FUNCTIONS` son los mismos que antes (lista congelada en la prueba, sacada con `sorted(talend_tabla._FUNCTIONS)` al empezar).
- [ ] **Step 2: Medir.** `uv run python -m pytest -q -p no:cacheprovider tests/unit/test_talend_expresiones.py tests/unit/test_talend_scan.py tests/unit/test_talend_compress.py tests/unit/test_talend_like.py tests/unit/test_talend_translator.py tests/unit/test_input_informat.py tests/unit/test_catalogo_sas.py` y anotar las pasadas. Repetir el `Grep` de referencias de los cinco módulos huérfanos.
- [ ] **Step 3: Run test to verify it fails.** `uv run python -m pytest tests/unit/test_talend_modulos.py -q -p no:cacheprovider`; esperado: `_scan` definido en dos archivos y `talend_funciones.py` con 416 líneas.
- [ ] **Step 4: Implement.** Comparar con `diff` las copias de `_strfn`, `_cat`, `_substr`, `_scan`, `_compress`, `_intnx` e `_intck`; si una difiere, gana la que usa `talend_tabla` hoy (es la que pasan los tests y el lote C de L4) y la otra se descarta. Borrar las copias de `talend_funciones.py`, mover el resto a los dos módulos nuevos y actualizar los `import` de `talend_tabla.py`. Borrar los cinco huérfanos solo si el `Grep` sigue dando cero.
- [ ] **Step 5: Run** la tanda del paso 2: mismas pasadas; el golden y `tests/unit/test_talend_*.py` sin cambios. `uv run ruff check src tests tools`. **Commit** `hito N n: una sola definicion de cada funcion Java de Talend y modulos bajo 300 lineas`.

---

### Task D1-7: Texto A: `PROPCASE`, `REVERSE`, `REPEAT`, `RIGHT`, `TRIMN` y el arreglo de `LENGTH` (MG-P3-02; serie `n`)

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\interprete_texto.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\corpus_semantica_texto.py` (las funciones nuevas del oráculo; `tools\corpus_semantica_funciones.py` está en 260 líneas y solo suma el `import` y las claves de `FUNCIONES`)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\corpus_semantica_funciones.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\semantica\vectores.yaml`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\expressions\talend_tabla.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\expressions\talend_funciones_texto.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\corpus_lib\especificaciones_l4_vectores.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\rules\sas\catalogo\funciones-guia.yaml`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_interprete_funciones.py` y `tests\unit\test_talend_expresiones.py`

**Interfaces:**
- Consumes: `FUNCIONES: dict[str, Funcion]` de `interprete_texto.py` (D1-2), `semantica.como_texto(valor: object) -> str`, `corpus_semantica_funciones.FUNCIONES`, `talend_tabla._FUNCTIONS` y `_strfn(template: str, arity: int = 1)`.
- Produces: `interprete_texto.FUNCIONES` gana `propcase`, `reverse`, `repeat`, `right`, `trimn`; el oráculo gana las mismas cinco con las firmas `def propcase(texto: str, delimitadores: object = None) -> str`, `def reverse(texto: str) -> str`, `def repeat(texto: str, veces: int) -> str`, `def right(texto: str) -> str`, `def trimn(texto: str) -> str`; `talend_tabla._FUNCTIONS` gana `repeat` y `right`.

**Vectores (cada uno con su página; el esperado deducido se confirma leyendo la página antes):**

| id | funcion | entrada | esperado | página |
|---|---|---|---|---|
| `propcase-01` | `propcase` | `["hELLO wORLD"]` | `"Hello World"` | `lefunctionsref`, p. 1395 |
| `propcase-02` | `propcase` | `["mc-donald"]` | `"Mc-Donald"` (el guion es delimitador por omisión; deducido) | p. 1395 |
| `reverse-01` | `reverse` | `["abc"]` | `"cba"` | p. 1480 |
| `reverse-02` | `reverse` | `["ab  "]` | `"  ba"` (los blancos finales pasan al inicio; deducido) | p. 1480 |
| `repeat-01` | `repeat` | `["ab", 2]` | `"ababab"` (n copias más la original) | p. 1478 |
| `repeat-02` | `repeat` | `["ab", 0]` | `"ab"` | p. 1478 |
| `right-01` | `right` | `["ab  "]` | `"  ab"` | p. 1483 |
| `trim-02` | `trim` | `[" "]` | `" "` (un blanco; deducido) | p. 1624 |
| `trimn-01` | `trimn` | `[" "]` | `""` | p. 1627 |
| `length-01` | `length` | `["abc   "]` | `3` | p. 1180 |
| `length-02` | `length` | `[" "]` | `1` (un valor en blanco tiene longitud 1; deducido) | p. 1180 |

`length-02` revela un error del intérprete: `length` devuelve 0 para un blanco (`len(como_texto(...))`); la corrección va en `interprete_texto.length`. Java: `repeat` = `(new String(new char[n + 1]).replace("\0", s))` y `right` = `StringHandling.LPAD(StringHandling.TRIM(s), StringHandling.LEN(s), " ")`. `Pendiente: P-JAVA-PROPCASE`: Talend no trae una rutina de mayúscula inicial por palabra y una expresión de una línea no puede recorrer delimitadores; la función queda `Unsupported` con ese código. `Pendiente: P-LONGITUD-VARIABLE` para `RIGHT` y `REVERSE` con blancos finales sobre una columna: el resultado depende del `LENGTH` declarado, que el CSV no trae; no se genera caso `L4` de esos dos con blancos.

- [ ] **Step 1: Write the failing tests.** Un test por vector de la tabla en `test_interprete_funciones.py` (llama a `llamar(...)`); `verificar()` y `verificar(motor="interprete")` en cero fallos; `translate_to_talend("repeat(a, 2)").java` contiene `new String(new char[2 + 1])`; `translate_to_talend("propcase(a)")` lanza `Unsupported` con `P-JAVA-PROPCASE` en el mensaje.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_interprete_funciones.py tests/unit/test_corpus_semantica.py tests/unit/test_talend_expresiones.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement** las cinco funciones en el intérprete y en el oráculo (de 3 a 10 líneas cada una), corregir `length`, agregar los vectores y los traductores de Java de `repeat` y `right`. Agregar a `FUNCIONES_CON_CASO` (D1-5) `propcase`, `reverse`, `repeat`, `trimn` y `length` (sin blancos finales en la columna) y regenerar los casos `L4`.
- [ ] **Step 4: Catálogo.** En `funciones-guia.yaml`, una entrada por función con `fuente: lefunctionsref.pdf, p. N` y `estado: reconocida` para `repeat` y `right` (están en `_FUNCTIONS`), `no_verificada` para `propcase` y `reverse`/`trimn` hasta que estén en Java (`nota`: «intérprete y oráculo sí; Java no»). `uv run python -m pytest tests/unit/test_catalogo_sas.py -q -p no:cacheprovider`.
- [ ] **Step 5: Run** `uv run python -m pytest tests/unit/test_migrar_corpus_anillo_b.py -q -p no:cacheprovider -k L4`, la tanda del golden y `uv run ruff check src tests tools`. Lote C de los casos `l4_1xx` nuevos si Studio responde (como en D1-5, paso 5). **Commit** `hito N n: texto A (PROPCASE, REVERSE, REPEAT, RIGHT, TRIMN) y LENGTH de un blanco`.

---

### Task D1-8: Texto B: `COMPBL`, `TRANWRD`, `TRANSLATE`, `INDEX`, `FIND`, `COUNT`, `LENGTHC` y `LENGTHN` (MG-P3-02; serie `n`)

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\interprete_texto.py` (si pasa de 300 líneas, las de búsqueda van a `src\sgm\migrar\interprete_busqueda.py`, módulo nuevo que `interprete_funciones.py` suma)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\corpus_semantica_texto.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\semantica\vectores.yaml`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\expressions\talend_funciones_texto.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\expressions\talend_tabla.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\corpus_lib\especificaciones_l4_vectores.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\rules\sas\catalogo\funciones-guia.yaml`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_interprete_funciones.py` y `tests\unit\test_talend_expresiones.py`

**Interfaces:**
- Consumes: `interprete_texto.FUNCIONES`, `talend_tabla._FUNCTIONS` (ya trae `compbl`, `tranwrd`, `index`, `count`, `length`, `lengthc`, `lengthn`), `_strfn(template: str, arity: int = 1)`, `_need(args, low, high=None, name="")`.
- Produces: intérprete y oráculo con `compbl(texto)`, `tranwrd(texto, buscar, reemplazo)`, `translate(texto, a, de)`, `index(texto, subcadena)`, `find(texto, subcadena, modificadores_o_inicio=None)`, `count(texto, subcadena, modificadores=None)`, `lengthc(texto)`, `lengthn(texto)`; `talend_tabla._FUNCTIONS` gana `find` y `translate`; las plantillas Java de `length` y `lengthn` se corrigen.

**Vectores:**

| id | funcion | entrada | esperado | página |
|---|---|---|---|---|
| `compbl-01` | `compbl` | `["a   b  c"]` | `"a b c"` | `lefunctionsref`, p. 572 |
| `compbl-02` | `compbl` | `["  a  b"]` | `" a b"` (un blanco inicial; deducido) | p. 572 |
| `tranwrd-01` | `tranwrd` | `["abc def abc", "abc", "x"]` | `"x def x"` | p. 1619 |
| `tranwrd-02` | `tranwrd` | `["abc", "z", "y"]` | `"abc"` | p. 1619 |
| `translate-01` | `translate` | `["abc", "xy", "ab"]` | `"xyc"` (el orden es **a, de**, inverso al de `TRANWRD`) | p. 1613 |
| `index-01` | `index` | `["abcabc", "c"]` | `3` | p. 1071 |
| `index-02` | `index` | `["ABC", "b"]` | `0` (distingue mayúsculas) | p. 1071 |
| `find-01` | `find` | `["ABC", "b", "i"]` | `2` | p. 807 |
| `find-02` | `find` | `["abcabc", "c", 4]` | `6` (empieza en la posición 4; deducido) | p. 807 |
| `count-01` | `count` | `["banana", "an"]` | `2` | p. 608 |
| `count-02` | `count` | `["aAa", "a", "i"]` | `3` | p. 608 |
| `lengthc-01` | `lengthc` | `["abc   "]` | `6` | p. 1181 |
| `lengthn-01` | `lengthn` | `[""]` | `0` | p. 1185 |

Java: hoy `length` es `StringHandling.LEN(StringHandling.RTRIM(x))`, que da 0 para el texto en blanco y `null` para un faltante; SAS da 1 (`length-02`, D1-7): la plantilla pasa a `(x == null ? 1 : Math.max(1, StringHandling.LEN(StringHandling.RTRIM(x))))`. `lengthn` da 0 para blanco y para faltante: `(x == null ? 0 : StringHandling.LEN(StringHandling.RTRIM(x)))`. `translate` solo se emite con listas literales y sin caracteres de `de` dentro de `a` (la traducción es simultánea: encadenar `.replace` cambia el resultado cuando un destino es origen de otro par); si no, `Unsupported` con `P-JAVA-TRANSLATE-SOLAPADO`. `find` solo con el modificador literal `i` o sin modificador; `t` y `k` quedan `Unsupported` con `P-JAVA-FIND-MODIFICADOR` hasta que una página los demuestre con un caso.

- [ ] **Step 1: Write the failing tests:** un test por vector (intérprete; `verificar()` y `verificar(motor="interprete")` en cero fallos); `translate_to_talend("length(a)").java` contiene `Math.max(1,`; `translate_to_talend("translate(a, 'ab', 'ba')")` lanza `Unsupported` con `P-JAVA-TRANSLATE-SOLAPADO`; `translate_to_talend("find(a, 'x', 'i')").java` contiene `toLowerCase`.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_interprete_funciones.py tests/unit/test_corpus_semantica.py tests/unit/test_talend_expresiones.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement** las funciones en los tres motores. Agregar a `FUNCIONES_CON_CASO` `compbl`, `tranwrd`, `index`, `find`, `count` y `lengthn`, y regenerar `L4`.
- [ ] **Step 4: Catálogo:** entradas en `funciones-guia.yaml` (`compbl-function` pasa a `reconocida`: ya está en `_FUNCTIONS`) y correr `tests/unit/test_catalogo_sas.py`.
- [ ] **Step 5: Run** `uv run python -m pytest tests/unit/test_migrar_corpus_anillo_b.py -q -p no:cacheprovider -k L4`, la tanda del golden, `uv run ruff check src tests tools` y el lote C de los casos nuevos (si Studio no conecta, «lote C pendiente» con motivo). **Commit** `hito N n: texto B (COMPBL, TRANWRD, TRANSLATE, INDEX, FIND, COUNT) y LENGTH como lo define SAS`.

---

### Task D1-9: `SUBSTR` como pseudovariable y la familia `CAT` con faltantes (MG-P3-02; serie `n`)

El catálogo (`funciones-usadas.yaml`, entrada `substr-right-of-function`) dice que el programa grande usa `SUBSTR` a la izquierda del `=` 182 veces y que hoy el parser la clasifica como asignación sin que nadie escriba el reemplazo. La regla está en `lefunctionsref`, p. 1572 (`SUBSTR (left of =)`): reemplaza los caracteres desde la posición con el valor del lado derecho, rellenando con blancos si es más corto y truncando si es más largo, sin cambiar la longitud de la variable.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\ir\lower_data_substr.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\ir\lower_data.py` (solo una llamada en el punto donde se baja una asignación; el archivo tiene 770 líneas y su extracción es de los Planes B y F1, no de este)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\corpus_semantica_texto.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\interprete_texto.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\semantica\vectores.yaml`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\rules\sas\catalogo\funciones-usadas.yaml`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\rules\sas\catalogo\funciones-guia.yaml`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\corpus_lib\especificaciones_l4c.py` (con el caso `l4_150_substr_pseudovariable`; lo registra `generar_entradas_l4l6.py`, línea 179, y el generador escribe `caso.yaml`, `programa.sas`, `entradas\codigos.csv` y `esperado\codigos_fix.csv` en `tests\corpus\L4\l4_150_substr_pseudovariable\`)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\corpus_lib\generar_entradas_l4l6.py`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_lower_data_substr.py`

**Interfaces:**
- Consumes: `classify_statement` de `sgm.frontend.datastep` (la sentencia `substr(x, p, l) = valor;` sale hoy con `kind="assign"` y el texto íntegro; el test del paso 1 lo comprueba), `interprete_texto.FUNCIONES`, las funciones `cat`, `cats`, `catt`, `catx` del oráculo (`corpus_semantica_funciones.py:166-181`).
- Produces:
  ```python
  # lower_data_substr.py
  def reescribir_substr_izquierda(objetivo: str, valor: str) -> tuple[str, str] | None:
      """`substr(x, p, l)` con `valor` a la derecha del `=` se vuelve la asignación `(x, expresion)`
      con `expresion = substr(x,1,p-1) || substr(valor || <l blancos>, 1, l) || substr(x, p+l)`.
      Sin `l`, `l` es `lengthc(x) - p + 1`. Devuelve None si `objetivo` no es una llamada a SUBSTR."""
  # oráculo e intérprete
  def substr_asignar(texto: str, posicion: int, longitud: int | None, valor: str) -> str
  ```

**Vectores:**

| id | funcion | entrada | esperado | página |
|---|---|---|---|---|
| `substr-asig-01` | `substr_asignar` | `["abcdef", 2, 3, "XY"]` | `"aXY ef"` (relleno con blanco dentro de la longitud) | `lefunctionsref`, p. 1572 |
| `substr-asig-02` | `substr_asignar` | `["abcdef", 2, 3, "XYZW"]` | `"aXYZef"` (trunca) | p. 1572 |
| `substr-asig-03` | `substr_asignar` | `["abcdef", 4, null, "Z"]` | `"abcZ  "` (sin longitud: hasta el final de la variable; deducido) | p. 1572 |
| `cat-02` | `cat` | `["a ", " b"]` | `"a  b"` (no recorta) | p. 495 |
| `cats-01` | `cats` | `["a ", " b"]` | `"ab"` | p. 503 |
| `catt-01` | `catt` | `["a ", " b"]` | `"a b"` (recorta solo los blancos finales) | p. 506 |
| `catx-04` | `catx` | `[",", "a", "", "b"]` | `"a,b"` (los blancos no ponen separador) | p. 508 |
| `catx-05` | `catx` | `[",", "", ""]` | `""` | p. 508 |

`Pendiente: P-LONGITUD-VARIABLE`: el relleno final de `substr-asig-03` depende del `LENGTH` de la variable; con una columna de CSV (sin relleno) el caso `L4` fija la longitud en el propio programa con `LENGTH CODIGO $6;` y su esquema la declara. El caso `l4_150_substr_pseudovariable` (`capa: B`, `estado: traducible`): entrada `codigos.csv` = `ID,CODIGO` / `1,ABCDEF` / `2,GHIJKL`; sentencia `SUBSTR(CODIGO, 2, 3) = 'XY';`; el esperado lo calcula el oráculo con `substr_asignar` (`AXY EF` y `GXY KL`), no se escribe a mano.

- [ ] **Step 1: Write the failing tests.** `reescribir_substr_izquierda("substr(a, 2, 3)", "'XY'")` devuelve `("a", "substr(a,1,1) || substr('XY' || '   ', 1, 3) || substr(a, 5)")`; `reescribir_substr_izquierda("a", "1")` devuelve `None`; los tres vectores de `substr_asignar` y los cinco de `cat*` pasan en el oráculo y en el intérprete.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_lower_data_substr.py tests/unit/test_corpus_semantica.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement** `reescribir_substr_izquierda` y llamarla desde `lower_data.py` en el punto donde hoy una asignación con destino que no es identificador queda sin traducir (localizarlo con `Grep` de `assign` y `Pendiente` en `src/sgm/ir/lower_data.py`); implementar `substr_asignar` y los vectores; escribir la especificación del caso y regenerar `L4`.
- [ ] **Step 4: Catálogo.** `substr-right-of-function` de `funciones-usadas.yaml` es la forma de la derecha; la forma de la izquierda se agrega a `funciones-guia.yaml` como `substr-left-of-function` (`lefunctionsref.pdf, p. 1572`) con `estado: reconocida` solo si el paso 3 cierra el emisor (en otro caso `no_verificada` y la nota con el motivo). `uv run python -m pytest tests/unit/test_catalogo_sas.py -q -p no:cacheprovider`.
- [ ] **Step 5: Run** `uv run python -m pytest tests/unit/test_migrar_corpus_anillo_b.py tests/unit/test_migrar_corpus_l4_a.py -q -p no:cacheprovider -k L4`, la tanda del golden, `uv run ruff check src tests tools`; lote C del caso nuevo y de los `cat*`. **Commit** `hito N n: SUBSTR a la izquierda del igual y CAT con faltantes`.

---

## Parte III. MG-P3-03: funciones numéricas y de agregación por fila (serie `n`, 7,5 h)

### Task D1-10: Numéricas: `INT`, `CEIL`, `FLOOR`, `MOD`, `ABS`, `SQRT`, `LOG`, `EXP`, `SIGN` y `ROUND` (MG-P3-03; serie `n`)

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\interprete_numerico.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\corpus_semantica_numerico.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\corpus_semantica_funciones.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\semantica\vectores.yaml`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\expressions\talend_funciones_numerico.py` (creado en D1-6)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\expressions\talend_tabla.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\corpus_lib\especificaciones_l4_vectores.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\rules\sas\catalogo\funciones-guia.yaml`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_interprete_funciones.py` y `tests\unit\test_talend_expresiones.py`

**Interfaces:**
- Consumes: `interprete_numerico.FUNCIONES` (D1-2; ya trae `abs`), `corpus_semantica_funciones.round_sas(valor: float, unidad: float = 1) -> float`, `talend_funciones_numerico._unary_math(fn: str)`, `_int(_p, args)`, `_round(_p, args)`, `talend_tabla._FUNCTIONS` (ya trae `abs`, `ceil`, `floor`, `sqrt`, `exp`, `log`, `mod`, `round`, `int`).
- Produces: intérprete y oráculo con `int_`, `ceil`, `floor`, `mod`, `sqrt`, `log`, `exp`, `sign` (el nombre SAS `int` se registra como `"int"` en `FUNCIONES`; `int_` es el nombre Python); `talend_tabla._FUNCTIONS` gana `sign`; `mod` cambia su Java.

**Vectores** (el esperado «faltante» de `sqrt(-1)`, `log(0)` y `mod(x, 0)` se confirma leyendo la página: SAS devuelve faltante y escribe una nota en el log; si la página no lo dice, el vector queda `incierto` y la función `Pendiente: P-NUMERICA-DOMINIO`):

| id | funcion | entrada | esperado | página (`lefunctionsref`) |
|---|---|---|---|---|
| `int-01` | `int` | `[-2.7]` | `-2` | p. 1087 |
| `ceil-01` | `ceil` | `[-2.1]` | `-2` | p. 545 |
| `floor-01` | `floor` | `[-2.1]` | `-3` | p. 841 |
| `mod-01` | `mod` | `[-7, 3]` | `-1` (el signo es el del primer argumento) | p. 1240 |
| `mod-02` | `mod` | `[7, -3]` | `1` | p. 1240 |
| `mod-03` | `mod` | `[7.5, 2]` | `1.5` | p. 1240 |
| `mod-04` | `mod` | `[10, null]` | `faltante` | p. 1240 |
| `abs-01` | `abs` | `[-3]` | `3` | p. 230 |
| `abs-02` | `abs` | `[null]` | `faltante` | p. 230 |
| `sqrt-01` | `sqrt` | `[16]` | `4` | p. 1555 |
| `log-01` | `log` | `[1]` | `0` | p. 1206 |
| `exp-01` | `exp` | `[0]` | `1` | p. 712 |
| `sign-01` | `sign` | `[-5]` | `-1` | p. 1528 |
| `round-07` | `round` | `[-2.5]` | `-3` (empate: se aleja de cero) | p. 1486 |
| `round-08` | `round` | `[2.675, 0.01]` | `2.68` (SAS aplica un fuzz a la comparación, `lrcon`, p. 116) | p. 1486 |

Java: `mod` hoy usa `Mathematical.MOD(a, b)`, que opera con enteros y pierde `mod-03`; pasa a `((a) % (b))` con `Double`, que tiene el signo del dividendo como SAS, con la guarda de nulo de `_unary_math`. Los tres casos de dominio (`sqrt` de negativo, `log` de cero, `mod` por cero) en Java dan `NaN`/`Infinity`, no faltante: la plantilla envuelve el resultado con `(Double.isNaN(r) || Double.isInfinite(r) ? null : r)`.

- [ ] **Step 1: Write the failing tests:** un test por vector (intérprete); `verificar()` y `verificar(motor="interprete")` en cero fallos; `translate_to_talend("mod(a, b)").java` contiene `%` y no contiene `Mathematical.MOD`; `translate_to_talend("sign(a)").java` contiene `Math.signum`.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_interprete_funciones.py tests/unit/test_corpus_semantica.py tests/unit/test_talend_expresiones.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement** en los tres motores; agregar a `FUNCIONES_CON_CASO` `int`, `ceil`, `floor`, `mod`, `abs`, `sqrt`, `log`, `exp`, `sign` y `round` (con unidad como literal), y regenerar `L4`.
- [ ] **Step 4: Catálogo** (`funciones-guia.yaml`: una entrada por función con su página; `sign` y las que estén en `_FUNCTIONS` como `reconocida`) y `tests/unit/test_catalogo_sas.py`.
- [ ] **Step 5: Run** `uv run python -m pytest tests/unit/test_migrar_corpus_anillo_b.py -q -p no:cacheprovider -k L4`, la tanda del golden, `uv run ruff check src tests tools` y el lote C de los casos nuevos. **Commit** `hito N n: funciones numericas con faltantes (INT, CEIL, FLOOR, MOD, SQRT, LOG, EXP, SIGN, ROUND)`.

---

### Task D1-11: Agregación por fila y condicionales: `SUM`, `MEAN`, `MIN`, `MAX`, `N`, `NMISS`, `CMISS`, `COALESCE`, `IFN`, `IFC`, `MISSING` (MG-P3-03; serie `n`)

`SUM(a, b)` ignora faltantes y `a + b` no (`lefunctionsref`, p. 1580 y `lrcon`, p. 128); en SQL, `SUM(x)` con un argumento es el agregado del plan y lo ejecuta `interprete_agregados.agregar`, no esta tabla (por eso D1-4 excluye `sum`, `min`, `max`, `count` y `avg` del renombrado `sgm_`).

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\interprete_numerico.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\corpus_semantica_numerico.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\semantica\vectores.yaml`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\expressions\talend_funciones_numerico.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\expressions\talend_tabla.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\corpus_lib\especificaciones_l4_vectores.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\rules\sas\catalogo\funciones-guia.yaml`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_interprete_funciones.py` y `tests\unit\test_talend_expresiones.py`

**Interfaces:**
- Consumes: `interprete_numerico.FUNCIONES` (`mean`, `min`, `max`, `sum`, `coalesce`, `missing`), `talend_funciones_numerico._aggregate(kind: str)`, `_coalesce(_p, args)`, `_ifv(_p, args)`, `semantica.es_faltante(valor)`.
- Produces: intérprete y oráculo con `n`, `nmiss`, `cmiss`, `ifn`, `ifc` y los vectores de las otras; `talend_tabla._FUNCTIONS` gana `cmiss`; `_ifv` acepta el cuarto argumento (valor para faltante).

**Vectores:**

| id | funcion | entrada | esperado | página (`lefunctionsref`) |
|---|---|---|---|---|
| `sum-01` | `sum` | `[1, null, 3]` | `4` | p. 1580 |
| `sum-02` | `sum` | `[null, null]` | `faltante` (la suma de argumentos todos faltantes es faltante; la de un **grupo** de `PROC SQL` es el `P-SUM-TODO-FALTANTE` del Plan C y no se mezcla) | p. 1580 |
| `mean-01` | `mean` | `[1, null, 3]` | `2` | p. 1233 |
| `mean-02` | `mean` | `[null]` | `faltante` | p. 1233 |
| `min-01` | `min` | `[null, 2, 5]` | `2` | p. 1236 |
| `max-01` | `max` | `[null, null]` | `faltante` | p. 1230 |
| `n-01` | `n` | `[1, null, 3]` | `2` | p. 1264 |
| `nmiss-01` | `nmiss` | `[1, null, 3]` | `1` | p. 1269 |
| `cmiss-01` | `cmiss` | `["", null, "a"]` | `2` (cuenta faltantes de texto y numéricos) | p. 557 |
| `ifn-01` | `ifn` | `[1, 10, 20]` | `10` | p. 1067 |
| `ifn-02` | `ifn` | `[0, 10, 20]` | `20` | p. 1067 |
| `ifn-03` | `ifn` | `[null, 10, 20, 30]` | `30` (el cuarto argumento es para el faltante; deducido) | p. 1067 |
| `ifn-04` | `ifn` | `[null, 10, 20]` | `faltante` (sin cuarto argumento; deducido) | p. 1067 |
| `ifc-01` | `ifc` | `[1, "a", "b"]` | `"a"` | p. 1065 |
| `ifc-02` | `ifc` | `[null, "a", "b", "c"]` | `"c"` | p. 1065 |
| `missing-01` | `missing` | `["  "]` | `true` | p. 1238 |
| `missing-02` | `missing` | `[0]` | `false` | p. 1238 |

`MIN`/`MAX` de texto con dos o más argumentos de carácter no están demostrados por el vector: el intérprete lanza `NoSoportadoEnInterprete("funcion", "MIN/MAX de texto")` en lugar de devolver un valor (hoy `_numero` los vuelve `None` y devuelve faltante en silencio; ese comportamiento es el error que corrige esta tarea). `Pendiente: P-ESPECIALES-FALTANTE`: los valores especiales `.A` a `.Z` y `._` (`lrcon`, p. 124) no se modelan; si un programa los usa, el paso queda sin traducir con ese código.

- [ ] **Step 1: Write the failing tests:** un test por vector (intérprete); `verificar()` y `verificar(motor="interprete")` en cero fallos; `llamar("min", ["a", "b"])` lanza `NoSoportadoEnInterprete`; `translate_to_talend("ifn(a, 10, 20, 30)").java` contiene `30` y la guarda de `null`.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_interprete_funciones.py tests/unit/test_corpus_semantica.py tests/unit/test_talend_expresiones.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement** en los tres motores; agregar a `FUNCIONES_CON_CASO` `sum`, `mean`, `min`, `max`, `n`, `nmiss`, `ifn`, `ifc` (como llamadas por fila con varias columnas) y regenerar `L4`.
- [ ] **Step 4: Catálogo** y `tests/unit/test_catalogo_sas.py`.
- [ ] **Step 5: Run** `uv run python -m pytest tests/unit/test_migrar_corpus_anillo_b.py tests/unit/test_migrar_corpus_l4_a.py -q -p no:cacheprovider -k L4`, la tanda del golden y `uv run ruff check src tests tools`. Lote C. **Commit** `hito N n: SUM, MEAN, MIN, MAX, N, NMISS, CMISS, IFN, IFC con faltantes`.

---

## Parte IV. MG-P3-04: fechas y horas (serie `n`, 12 h)

La fecha de SAS es el número de días desde el 1 de enero de 1960 (`lrcon`, p. 155 y 157). Todas las funciones de esta parte trabajan sobre ese número entero; el intérprete y el oráculo no usan `datetime` para guardar el valor, solo para convertir. Cifras de referencia que usan los vectores (calculadas con el calendario gregoriano): 1960-01-01 = 0; 2000-01-01 = 14610; 2023-01-01 = 23011; 2024-01-01 = 23376; 2024-01-31 = 23406; 2024-02-01 = 23407; 2024-02-29 = 23435; 2024-03-01 = 23436; 2024-04-01 = 23467; 2024-06-15 = 23542; 2025-01-01 = 23742.

### Task D1-12: Base de fechas: `MDY`, `YEAR`, `MONTH`, `DAY`, `WEEKDAY`, `QTR`, `DATEPART`, `TODAY`, `DATE` (MG-P3-04; serie `n`)

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\interprete_fechas.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\corpus_semantica_fechas.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\corpus_semantica_funciones.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\interprete_funciones.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\semantica\vectores.yaml`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\expressions\talend_funciones_fecha.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\expressions\talend_tabla.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\corpus_lib\especificaciones_l4_vectores.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\rules\sas\catalogo\funciones-guia.yaml`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_interprete_fechas.py`

**Interfaces:**
- Consumes: `talend_funciones._part(name: str)`, `_mdy(_p, args)`, `_datepart(_p, args)` (hoy en `talend_funciones.py` y movidos en D1-6 a `talend_funciones_fecha.py` o `_formato.py`: seguir el módulo donde quedaron), `talend_tabla._FUNCTIONS` (ya trae `today`, `date`, `datetime`, `datepart`, `mdy`, `year`, `month`, `day`, `weekday`), `semantica.como_numero(valor) -> float | None`.
- Produces:
  ```python
  # interprete_fechas.py
  EPOCA_SAS = date(1960, 1, 1)
  RELOJ: Callable[[], date]                      # inyectable; por omisión, date.today
  def dias_a_fecha(dias: int) -> date: ...
  def fecha_a_dias(fecha: date) -> int: ...
  FUNCIONES: dict[str, Funcion]                  # mdy, year, month, day, weekday, qtr, datepart, today, date
  ```
  Una fecha inválida (`mdy(2, 29, 2023)`, mes 13) o un argumento faltante da faltante (`None`), nunca una excepción.

**Vectores:**

| id | funcion | entrada | esperado | página |
|---|---|---|---|---|
| `mdy-01` | `mdy` | `[1, 1, 1960]` | `0` | `lrcon`, p. 157 |
| `mdy-02` | `mdy` | `[12, 31, 1959]` | `-1` | `lrcon`, p. 157 |
| `mdy-03` | `mdy` | `[1, 1, 2000]` | `14610` | `lefunctionsref`, p. 1232 |
| `mdy-04` | `mdy` | `[2, 29, 2024]` | `23435` (año bisiesto) | p. 1232 |
| `mdy-05` | `mdy` | `[2, 29, 2023]` | `faltante` (2023 no es bisiesto; deducido) | p. 1232 |
| `mdy-06` | `mdy` | `[13, 1, 2024]` | `faltante` (deducido) | p. 1232 |
| `year-01` | `year` | `[23435]` | `2024` | p. 1729 |
| `month-01` | `month` | `[23435]` | `2` | p. 1251 |
| `day-01` | `day` | `[23435]` | `29` | p. 642 |
| `weekday-01` | `weekday` | `[0]` | `6` (1960-01-01 fue viernes; domingo = 1) | p. 1724 |
| `weekday-02` | `weekday` | `[23435]` | `5` (jueves) | p. 1724 |
| `qtr-01` | `qtr` | `[23435]` | `1` | p. 1428 |
| `datepart-01` | `datepart` | `[2024787661]` | `23435` (23435 días × 86400 s + 3661 s; la parte de hora se descarta) | p. 639 |

`TODAY()` y `DATE()` no tienen vector (dependen del reloj): se prueban inyectando `RELOJ` (`RELOJ = lambda: date(2024, 2, 29)` da `23435`). **Representación en Java:** hoy `_mdy` y `_datepart` emiten `java.util.Date` (`kind="date"`), pero un `DATA` sin formato escribe la fecha SAS como número de días. Cuando el destino es numérico, la plantilla agrega `TalendDate.diffDate(<fecha>, TalendDate.parseDate("yyyy-MM-dd", "1960-01-01"), "dd")` (comprobar la firma con `Grep` en las rutinas de Talend que `src/sgm/talend_item/` ya usa) y, cuando el destino es `PUT` con un formato de fecha, queda como `Date`. Decisión a anotar en `PROGRESS.md` («Decisiones»).

- [ ] **Step 1: Write the failing tests:** un test por vector con `llamar(...)`; `interprete_fechas.RELOJ` inyectado para `today`; `verificar()` y `verificar(motor="interprete")` en cero fallos; `translate_to_talend("mdy(a, b, c)").java` contiene `diffDate` cuando se pide como número.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_interprete_fechas.py tests/unit/test_corpus_semantica.py -q -p no:cacheprovider`; esperado: no existe el módulo.
- [ ] **Step 3: Implement** el módulo del intérprete, el del oráculo (independiente: usa `datetime.date.toordinal()` con la época `date(1960,1,1).toordinal()`, no el módulo del intérprete) y los traductores a Java; agregar a `FUNCIONES_CON_CASO` `mdy`, `year`, `month`, `day`, `weekday`, `qtr` y regenerar `L4`.
- [ ] **Step 4: Catálogo.** `date-function` de `funciones-usadas.yaml` ya es `reconocida`; `time-function` (p. 1604) y `datetime-function` (p. 640) siguen `no_verificada` salvo que se agreguen aquí; las nuevas van a `funciones-guia.yaml`. `tests/unit/test_catalogo_sas.py`.
- [ ] **Step 5: Run** `uv run python -m pytest tests/unit/test_migrar_corpus_anillo_b.py -q -p no:cacheprovider -k L4`, la tanda del golden, `uv run ruff check src tests tools`, lote C. **Commit** `hito N n: fechas SAS como dias desde 1960 (MDY, YEAR, MONTH, DAY, WEEKDAY, QTR, DATEPART)`.

---

### Task D1-13: `INTNX` con fin de mes y bisiestos (MG-P3-04; serie `n`)

`INTNX(intervalo, fecha, n, alineación)` mueve la fecha `n` intervalos (`lefunctionsref`, p. 1131). Sin alineación, devuelve el **inicio** del intervalo (`B`). `S` conserva el día dentro del intervalo (y si el mes de llegada es más corto, queda en su último día), `E` el final. Los intervalos de este plan: `day`, `week` (empieza en domingo), `month`, `qtr`, `year`; las fronteras están en `lrcon`, p. 176 y 177.

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\interprete_fechas.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\interprete_intervalos.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\corpus_semantica_fechas.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\semantica\vectores.yaml`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\expressions\talend_funciones_fecha.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\corpus_lib\especificaciones_l4_vectores.py`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_interprete_intervalos.py`

**Interfaces:**
- Consumes: `interprete_fechas.dias_a_fecha(dias: int) -> date`, `fecha_a_dias(fecha: date) -> int`, `talend_funciones_fecha._intnx(_p: _P, args: list[E]) -> E` (línea 25 del archivo; ya valida enteros literales con `_literal_increment_is_integer`).
- Produces:
  ```python
  # interprete_intervalos.py
  def intnx(intervalo: str, fecha: int | None, n: int | None, alineacion: str = "b") -> int | None:
      """Intervalos day, week, month, qtr, year (y sus formas `quarter`, `semiyear` no incluidas).
      Alineación b, e, s. Faltante en fecha o en n da None. Intervalo desconocido: NoSoportadoEnInterprete."""
  ```

**Vectores:**

| id | funcion | entrada | esperado | página |
|---|---|---|---|---|
| `intnx-01` | `intnx` | `["month", 23406, 1]` | `23407` (31-ene a 1-feb) | `lefunctionsref`, p. 1131 |
| `intnx-02` | `intnx` | `["month", 23435, 1]` | `23436` | p. 1131 |
| `intnx-03` | `intnx` | `["month", 23406, 1, "same"]` | `23435` (31-ene mas un mes: queda en el 29-feb, no pasa a marzo) | p. 1131 |
| `intnx-04` | `intnx` | `["month", 23406, 1, "end"]` | `23435` | p. 1131 |
| `intnx-05` | `intnx` | `["month", 23406, 0]` | `23376` | p. 1131 |
| `intnx-06` | `intnx` | `["month", 23406, -1]` | `23345` (1-dic-2023) | p. 1131 |
| `intnx-07` | `intnx` | `["year", 23176, 0]` | `23011` | p. 1131 |
| `intnx-08` | `intnx` | `["year", 23176, 1]` | `23376` | p. 1131 |
| `intnx-09` | `intnx` | `["year", 23176, 1, "same"]` | `23542` (15-jun-2023 a 15-jun-2024) | p. 1131 |
| `intnx-10` | `intnx` | `["week", 23435, 0]` | `23431` (el domingo 25-feb) | p. 1131 |
| `intnx-11` | `intnx` | `["week", 23435, 1]` | `23438` | p. 1131 |
| `intnx-12` | `intnx` | `["qtr", 23435, 1]` | `23467` | p. 1131 |
| `intnx-13` | `intnx` | `["day", 23435, 3]` | `23438` | p. 1131 |
| `intnx-14` | `intnx` | `["month", null, 1]` | `faltante` | p. 1131 |

Fin de año bisiesto: `["month", 23375, 2, "same"]` (31-dic-2023 más 2 meses) da `23435`. `Pendiente: P-INTNX-ALINEACION-M` (alineación `M`, mitad del intervalo), `P-INTNX-INTERVALO` (`semimonth`, `tenday`, `hour` y los demás de `lrcon`, p. 173), `P-INTNX-MULTIUNIDAD` (`month2`, `lrcon`, p. 178) y `P-INTNX-DESPLAZADO` (`month.2`, `lrcon`, p. 180): se leen las páginas citadas y, si una da la regla con un ejemplo, se agrega su vector en otra tarea; aquí lanzan `NoSoportadoEnInterprete` con ese código.

- [ ] **Step 1: Write the failing tests:** un test por vector; el caso de fin de año bisiesto; `intnx("month2", 23406, 1)` lanza `NoSoportadoEnInterprete` con `P-INTNX-MULTIUNIDAD`; `verificar()` y `verificar(motor="interprete")` en cero fallos.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_interprete_intervalos.py tests/unit/test_corpus_semantica.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement** `intnx` en el intérprete y su gemelo en el oráculo (otra implementación: con aritmética de meses `anio*12 + mes - 1`, sin `dateutil`), y revisar que el Java de `_intnx` produce el mismo resultado para los vectores de mes con `S` y `E` (`TalendDate.addDate` con `"MM"` recorta al fin de mes; si no, el Java queda `Unsupported` con `P-JAVA-INTNX-FIN-DE-MES`). Agregar `intnx` a `FUNCIONES_CON_CASO` con el intervalo y la alineación como literales y regenerar `L4`.
- [ ] **Step 4: Run** `uv run python -m pytest tests/unit/test_migrar_corpus_anillo_b.py -q -p no:cacheprovider -k L4`, la tanda del golden, `uv run ruff check src tests tools`, lote C de los casos nuevos. **Commit** `hito N n: INTNX con alineacion, fin de mes y bisiestos`.

---

### Task D1-14: `INTCK`, `DATDIF` y `YRDIF` (MG-P3-04; serie `n`)

`INTCK` cuenta **fronteras** de intervalo, no intervalos completos (`lefunctionsref`, p. 1092; `lrcon`, p. 176): del 31 de enero al 1 de febrero hay una frontera de mes. `DATDIF(inicio, fin, base)` y `YRDIF(inicio, fin, base)` usan una convención de conteo de días: `'30/360'` (un mes siempre de 30 días; si una fecha cae en fin de mes se trata como el día 30), `'ACT/ACT'`, y, para `YRDIF`, `'ACT/360'`, `'ACT/365'` y `'AGE'` (`lefunctionsref`, p. 634 a 636 y 1731 a 1733).

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\interprete_intervalos.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\interprete_diferencias.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\corpus_semantica_fechas.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\semantica\vectores.yaml`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\expressions\talend_funciones_fecha.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\expressions\talend_tabla.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\corpus_lib\especificaciones_l4_vectores.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\rules\sas\catalogo\funciones-guia.yaml`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_interprete_diferencias.py`

**Interfaces:**
- Consumes: `interprete_fechas.dias_a_fecha`, `talend_funciones_fecha._intck(_p: _P, args: list[E]) -> E` (línea 112), `talend_tabla._FUNCTIONS` (ya trae `intck`; `datdif` y `yrdif` no).
- Produces:
  ```python
  # interprete_intervalos.py
  def intck(intervalo: str, inicio: int | None, fin: int | None) -> int | None: ...   # método discreto
  # interprete_diferencias.py
  def datdif(inicio: int | None, fin: int | None, base: str) -> int | None: ...
  def yrdif(inicio: int | None, fin: int | None, base: str = "age") -> float | None: ...
  ```
  `talend_tabla._FUNCTIONS` gana `datdif` (solo `'ACT/ACT'` y `'30/360'` literales) y `yrdif` (solo `'30/360'`, `'ACT/360'` y `'ACT/365'` literales).

**Vectores:**

| id | funcion | entrada | esperado | página |
|---|---|---|---|---|
| `intck-01` | `intck` | `["month", 23406, 23407]` | `1` (una frontera de mes entre el 31-ene y el 1-feb) | `lefunctionsref`, p. 1092 |
| `intck-02` | `intck` | `["month", 23406, 23435]` | `1` | p. 1092 |
| `intck-03` | `intck` | `["year", 23375, 23376]` | `1` (31-dic-2023 a 1-ene-2024) | p. 1092 |
| `intck-04` | `intck` | `["year", 23375, 23375]` | `0` | p. 1092 |
| `intck-05` | `intck` | `["day", 23435, 23438]` | `3` | p. 1092 |
| `intck-06` | `intck` | `["week", 23430, 23431]` | `1` (sábado 24 a domingo 25: la semana empieza en domingo) | p. 1092 |
| `intck-07` | `intck` | `["week", 23431, 23437]` | `0` | p. 1092 |
| `intck-08` | `intck` | `["month", 23407, 23406]` | `-1` (orden inverso: negativo) | p. 1092 |
| `datdif-01` | `datdif` | `[23406, 23436, "ACT/ACT"]` | `30` | p. 634 |
| `datdif-02` | `datdif` | `[23406, 23436, "30/360"]` | `31` (el 31 se trata como 30: 2 meses × 30 + (1 − 30); deducido, se lee p. 635 antes) | p. 635 |
| `datdif-03` | `datdif` | `[23376, 23742, "ACT/ACT"]` | `366` | p. 634 |
| `datdif-04` | `datdif` | `[23376, 23742, "30/360"]` | `360` | p. 635 |
| `yrdif-01` | `yrdif` | `[14610, 23376, "ACT/ACT"]` | `24` (6 bisiestos: 18 + 6 años exactos) | p. 1732 |
| `yrdif-02` | `yrdif` | `[14610, 23376, "30/360"]` | `24` | p. 1732 |
| `yrdif-03` | `yrdif` | `[14610, 23376, "AGE"]` | `24` | p. 1732 |
| `yrdif-04` | `yrdif` | `[23376, 23742, "ACT/360"]` | `1.0166666667` (366 / 360) | p. 1732 |
| `yrdif-05` | `yrdif` | `[23192, 23558, "ACT/ACT"]` | `1.0013773486` (184/365 + 182/366; fórmula de p. 1733; tolerancia 1e-9) | p. 1733 |

El cumpleaños de un 29 de febrero con base `AGE` (`yrdif(21974, 22339, "AGE")`, del 29-feb-2020 al 28-feb-2021) no tiene ejemplo en la guía: vector `yrdif-06` con `confianza: incierto` y la función queda `Pendiente: P-YRDIF-AGE-29FEB` solo para ese caso. `INTCK` con el método continuo (quinto argumento `'C'`) queda `Pendiente: P-INTCK-CONTINUO` hasta leer p. 1092 y fijar un ejemplo. Java: `YRDIF` con `'ACT/ACT'` y `'AGE'` requiere partir los días por año o comparar cumpleaños, que no cabe en una expresión de una línea sin rutina propia: `Unsupported` con `P-JAVA-YRDIF-ACTACT` y `P-JAVA-YRDIF-AGE`.

- [ ] **Step 1: Write the failing tests:** un test por vector (el intérprete, con `pytest.approx(abs=1e-9)` para los decimales); `intck("month", 23406, 23407, "c")` lanza `NoSoportadoEnInterprete` con `P-INTCK-CONTINUO`; `verificar()` y `verificar(motor="interprete")` en cero fallos; `translate_to_talend("yrdif(a, b, 'AGE')")` lanza `Unsupported` con `P-JAVA-YRDIF-AGE`.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_interprete_diferencias.py tests/unit/test_corpus_semantica.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement** en los tres motores (en el oráculo, `yrdif` y `datdif` calculados con `datetime.date` y con la fórmula de la página, sin reutilizar `interprete_diferencias`). Agregar a `FUNCIONES_CON_CASO` `intck`, `datdif` y `yrdif` (con el intervalo y la base como literales).
- [ ] **Step 4: Catálogo** (`intck-function` p. 1092, `datdif-function` p. 634, `yrdif-function` p. 1731) y `tests/unit/test_catalogo_sas.py`.
- [ ] **Step 5: Run** `uv run python -m pytest tests/unit/test_migrar_corpus_anillo_b.py -q -p no:cacheprovider -k L4`, la tanda del golden, `uv run ruff check src tests tools`, lote C. **Commit** `hito N n: INTCK por fronteras, DATDIF y YRDIF con sus bases de conteo`.

---

## Parte V. MG-P3-05: `INPUT` y `PUT` con informats y formats generales (serie `n`, 8 h)

Hoy el informat de un vector de `input` se escribe como dos números (`["23.0", 6, 2]` es `w=6`, `d=2`) y el intérprete lo recompone como `6.2` (`_input_wd`, que decodifica `d` de la parte fraccionaria: `8.10` se leería como `8.1`). `sqlglot` ni siquiera lee `comma8.2` ni `date9.` como argumento: son identificadores con punto. Esta parte cambia la convención: el informat o formato viaja como **texto** (`"comma8.2"`) y un preprocesador lo entrecomilla antes de que `sqlglot` lo vea. El adaptador de vectores de D1-3 acepta las dos formas (la vieja `[campo, w, d]` sigue valiendo).

### Task D1-15: Informats numéricos y las formas `w.d` del programa grande (MG-P3-05; serie `n`)

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\interprete_formatos.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\interprete.py` (solo `_arbol`: una llamada a `preparar_formatos`)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\interprete_vectores.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\corpus_semantica_formatos.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\corpus_semantica_funciones.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\semantica\vectores.yaml`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\semantica\informats-programa-grande.yaml`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\expressions\talend_funciones_formato.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\corpus_lib\especificaciones_l4_vectores.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\rules\sas\catalogo\informats-usados.yaml`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_interprete_formatos.py`

**Interfaces:**
- Consumes: `interprete_formatos.FUNCIONES["input"]` (D1-2), `sgm.ir.types_code.informat_type(spec: str) -> CodeType | None` (`types_code.py:113`), `talend_funciones_formato._input(p: _P, args: list[E]) -> E` (ya maneja `comma`, `dollar` y `w.d` con `BigDecimal`), el catálogo `informats-usados.yaml` (19 entradas; la `nota` de `numerico-entero` ya lista 20., 30., 1., 3., 6., 15., 32., 10.).
- Produces:
  ```python
  # interprete_formatos.py
  @dataclass(frozen=True)
  class Informat:
      nombre: str          # "w", "comma", "percent", "date", "yymmdd", "$" ...
      ancho: int | None
      decimales: int
  def parsear_informat(spec: str) -> Informat:
      """'comma8.2' -> Informat('comma', 8, 2); '20.' -> Informat('w', 20, 0); '$5.' -> Informat('$', 5, 0).
      Una forma desconocida lanza NoSoportadoEnInterprete('informat', spec)."""
  def preparar_formatos(expresion: str) -> str:
      """Entrecomilla el segundo argumento de INPUT/PUT: `input(a, comma8.2)` -> `input(a, 'comma8.2')`."""
  ```

**Paso previo, inventario de las formas del programa grande.** El plan maestro habla de 15 formas `w.d`. Al redactar, `Grep` de `input(...,\s*<w>.<d>)` sobre `tests/fixtures/sas/client/client_large.sas` da 11 (`20.` 27 veces, `30.` 26, `1.` 12, `8.` 6, `6.` 4, `15.` 4, `32.` 3, `3.` 2, `10.` 1, más `8.2` y `6.2` del catálogo): las otras salen de `format` y `put`. El paso 1 vuelve a contarlas incluyendo `format`, `informat` y `put` y escribe la lista **real** en `informats-programa-grande.yaml` (`forma`, `usos`); la prueba exige un vector por cada forma. No se escribe el nombre del programa en `src/` ni en `rules/` (el yaml vive en `tests/`).

**Vectores** (`input` con el informat como texto; la página es de `leforinforref`):

| id | entrada | esperado | página |
|---|---|---|---|
| `inputf-01` | `["1,234.5", "comma8.1"]` | `1234.5` (`COMMA` quita comas, blancos, `$` y `%`) | p. 646 |
| `inputf-02` | `["(12)", "comma5."]` | `-12` (paréntesis = negativo; deducido) | p. 646 |
| `inputf-03` | `["$1,234", "comma8."]` | `1234` | p. 646 |
| `inputf-04` | `["12%", "percent5."]` | `0.12` (deducido; se lee p. 696 antes) | p. 696 |
| `inputf-05` | `["abc", "8."]` | `faltante` (dato inválido: faltante, sin error) | p. 744 |
| `inputf-06` | `[" 12 ", "8."]` | `12` | p. 744 |
| `inputf-07` | `[".", "8."]` | `faltante` | p. 744 |
| `inputf-08` | `["1234", "8.2"]` | `12.34` (sin punto, `d` son decimales implícitos) | p. 744 |
| `inputf-09` | `["12.5", "8.2"]` | `12.5` (con punto, `d` se ignora) | p. 744 |
| `inputf-10` | `["ab ", "$5."]` | `"ab"` (deducido; se lee p. 616 antes) | p. 616 |

Más un vector por cada forma del yaml del paso previo que no esté cubierta (`20.`, `30.`, `1.`, `15.`, `32.`, `3.`, `10.`, `8.2`, `6.2`...), con una entrada que cabe y una que no cabe en el ancho (un valor más ancho que `w` se trunca a los primeros `w` caracteres, `p. 744`; se lee antes). `Pendiente: P-INFORMAT-ANCHO-EXCEDIDO` para lo que la página no fije. `DOLLARw.d` como informat no aparece en el índice de `leforinforref`: se trata con `COMMAw.d` (p. 646) solo si la página de `COMMA` lo dice, y si no, `Pendiente: P-INFORMAT-DOLLAR-SIN-PAGINA`.

- [ ] **Step 1: Write the failing tests** en `test_interprete_formatos.py`: `parsear_informat("comma8.2") == Informat("comma", 8, 2)` y `parsear_informat("8.10").decimales == 10`; `preparar_formatos("input(a, comma8.2)") == "input(a, 'comma8.2')"`; `_valor(_arbol("input(a, 8.2)"), {"a": "1234"}) == 12.34`; un test por vector; `verificar()` y `verificar(motor="interprete")` en cero fallos; el yaml del programa grande y los vectores cubren las mismas formas.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_interprete_formatos.py tests/unit/test_corpus_semantica.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement** `Informat`, `parsear_informat`, `preparar_formatos` (usada por `_arbol` antes del renombrado `sgm_`) y el `input` general; en el oráculo, `input_wd` pasa a `input_formato(campo, spec)` manteniendo `input_wd` como envoltura de la forma vieja. Revisar `talend_funciones_formato._input` contra cada vector: `percent` y `$w.` que no tengan Java quedan `Unsupported` con `P-JAVA-INFORMAT-<nombre>`.
- [ ] **Step 4: Catálogo.** Una entrada de `informats-usados.yaml` por forma nueva (`fuente: leforinforref.pdf, p. N`); correr `tests/unit/test_catalogo_sas.py` (incluye `test_los_informats_del_catalogo_coinciden_con_la_regla`: si agrega un informat, `rules/sas/informats.yaml` lo tipa también).
- [ ] **Step 5: Run** `uv run python -m pytest tests/unit/test_migrar_corpus_anillo_b.py tests/unit/test_input_informat.py -q -p no:cacheprovider`, la tanda del golden, `uv run ruff check src tests tools`, lote C de los casos `l4_1xx` de `input`. **Commit** `hito N n: informats numericos generales y las formas w.d del programa grande`.

---

### Task D1-16: Informats y formats de fecha con `YEARCUTOFF`; cierra `l4_20` (MG-P3-05; serie `n`)

El caso `l4_20_put_fechas_pendiente` (`estado: pendiente`, en `migrar_pendientes.yaml` con `P-ASIGNACION-SIN-TRADUCIR`) dice «no hay vector de `PUT`, `MDY` ni de `yymmdd10.`». Con D1-12 (`MDY`) y esta tarea lo tiene. Un año de dos dígitos se interpreta según `YEARCUTOFF=` (`lesysoptsref`, p. 432); el valor por omisión de SAS 9.4 es 1926 (la guía lo dice al describir el cambio de 1920 a 1926). El intérprete lo toma de una constante `YEARCUTOFF = 1926` con esa cita; una opción `OPTIONS YEARCUTOFF=` del programa la cambia (el reconocimiento de opciones es de `docs/opciones-de-sistema.md`; si no está, `Pendiente: P-YEARCUTOFF-EXPLICITO`).

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\interprete_formatos.py` (si pasa de 300 líneas, el formato de salida va a `src\sgm\migrar\interprete_put.py`, módulo nuevo)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\corpus_semantica_formatos.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\semantica\vectores.yaml`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\expressions\talend_funciones_formato.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\corpus_lib\especificaciones_l4b.py` (la entrada `l4_20_put_fechas_pendiente` deja de ser `pendiente`)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\migrar_pendientes.yaml` (se quita `l4_20_put_fechas_pendiente`; la prueba `test_la_lista_no_tiene_casos_resueltos` lo exige)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\rules\sas\catalogo\informats-usados.yaml`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_interprete_formatos.py` y `tests\unit\test_talend_expresiones.py`

**Interfaces:**
- Consumes: `parsear_informat(spec: str) -> Informat` (D1-15), `interprete_fechas.dias_a_fecha(dias: int) -> date` y `fecha_a_dias(fecha: date) -> int` (D1-12), `talend_funciones_formato._put(p, args)` y `_input(p, args)`, `talend_base._date_pattern(fmt: str) -> str | None`.
- Produces:
  ```python
  YEARCUTOFF = 1926   # lesysoptsref, p. 432
  def leer_fecha(texto: str, informat: Informat) -> int | None: ...    # días SAS o faltante
  def escribir_formato(valor: float | None, formato: str) -> str: ...  # PUT con date, yymmdd, mmddyy, ddmmyy, monyy, year
  ```

**Vectores:**

| id | funcion | entrada | esperado | página (`leforinforref`) |
|---|---|---|---|---|
| `inputd-01` | `input` | `["2024-02-29", "yymmdd10."]` | `23435` | p. 755 |
| `inputd-02` | `input` | `["20240229", "yymmdd8."]` | `23435` | p. 755 |
| `inputd-03` | `input` | `["29FEB2024", "date9."]` | `23435` | p. 649 |
| `inputd-04` | `input` | `["12/31/1959", "mmddyy10."]` | `-1` | p. 682 |
| `inputd-05` | `input` | `["31/12/1959", "ddmmyy10."]` | `-1` | p. 653 |
| `inputd-06` | `input` | `["2023-02-29", "yymmdd10."]` | `faltante` (fecha inexistente) | p. 755 |
| `inputd-07` | `input` | `["29FEB24", "date7."]` | `23435` (año de dos dígitos con `YEARCUTOFF=1926`: 24 → 2024) | p. 649 y `lesysoptsref`, p. 432 |
| `inputd-08` | `input` | `["01JAN30", "date7."]` | `25568` (con `YEARCUTOFF=1926`, 30 es 2030: 70 años × 365 + 18 bisiestos de 1960 a 2028; se comprueba con `datetime.date(2030,1,1).toordinal() - datetime.date(1960,1,1).toordinal()`) | p. 649 |
| `put-01` | `put` | `[0, "date9."]` | `"01JAN1960"` | p. 186 |
| `put-02` | `put` | `[-1, "date9."]` | `"31DEC1959"` | p. 186 |
| `put-03` | `put` | `[23435, "yymmdd10."]` | `"2024-02-29"` | p. 525 |
| `put-04` | `put` | `[23435, "mmddyy10."]` | `"02/29/2024"` | p. 255 |
| `put-05` | `put` | `[23435, "ddmmyy10."]` | `"29/02/2024"` | p. 194 |
| `put-06` | `put` | `[23435, "monyy7."]` | `"FEB2024"` | p. 267 |
| `put-07` | `put` | `[23435, "year4."]` | `"2024"` | p. 522 |
| `put-08` | `put` | `[null, "date9."]` | `"        ."` (un faltante sale como `.` alineado a la derecha; deducido) | p. 186 |

Java: `TalendDate.formatDate("ddMMMyyyy", d)` da `01Jan1960`, no `01JAN1960`, y depende del idioma del equipo; la plantilla pasa a `new java.text.SimpleDateFormat("ddMMMyyyy", java.util.Locale.ENGLISH).format(d).toUpperCase()`. Los informats con año de dos dígitos (`date7.`, `yymmdd8.` con `yy`) quedan `Unsupported` con `P-JAVA-ANIO-DOS-DIGITOS`: el Java no puede aplicar `YEARCUTOFF` sin una rutina propia.

- [ ] **Step 1: Write the failing tests:** un test por vector; `leer_fecha("29FEB24", parsear_informat("date7."))` da `23435` y con `YEARCUTOFF` inyectado a 1900 da el 29-feb-1924, que es `datetime.date(1924,2,29).toordinal() - datetime.date(1960,1,1).toordinal()`; `translate_to_talend("put(a, date9.)").java` contiene `Locale.ENGLISH` y `toUpperCase`; `verificar()` y `verificar(motor="interprete")` en cero fallos.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_interprete_formatos.py tests/unit/test_corpus_semantica.py tests/unit/test_talend_expresiones.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement** en los tres motores. Cerrar `l4_20`: escribir en `especificaciones_l4b.py` su asignación con las funciones reales (`input(FECHA, yymmdd10.)`, `put(FECHA_SAS, date9.)`, `mdy(12, 31, 2026)`), cambiar `estado` a `traducible`, regenerar `L4` (el esperado sale del oráculo) y quitar la línea de `migrar_pendientes.yaml`. Si el anillo A todavía no traduce alguna de las tres sentencias, el caso se queda en `migrar_pendientes.yaml` con el código real y el motivo nuevo, y esta tarea lo anota.
- [ ] **Step 4: Catálogo:** entradas `date`, `datetime`, `yymmdd`, `mmddyy`, `ddmmyy` de `informats-usados.yaml` con su página y estado real. `tests/unit/test_catalogo_sas.py`.
- [ ] **Step 5: Run** `uv run python -m pytest tests/unit/test_migrar_corpus_anillo_b.py tests/unit/test_migrar_corpus_l4_a.py -q -p no:cacheprovider -k L4`, la tanda del golden, `uv run ruff check src tests tools`, lote C. **Commit** `hito N n: informats y formats de fecha con YEARCUTOFF; l4_20 deja de ser pendiente`.

---

### Task D1-17: `PUT` con formatos numéricos y de texto (MG-P3-05; serie `n`)

Un formato numérico justifica a la derecha dentro del ancho `w` (`leforinforref`, `w.d Format`, p. 503): `put(3.14159, 8.2)` es `"    3.14"`, con cuatro blancos delante. Hoy `_put` (`talend_funciones_formato.py`) devuelve `String.valueOf(x)` para `8.2`, `z5.` o cualquier numérico con ancho, sin justificar ni redondear.

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\interprete_formatos.py` (o `interprete_put.py` si D1-16 lo creó)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\corpus_semantica_formatos.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\semantica\vectores.yaml`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\expressions\talend_funciones_formato.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\corpus_lib\especificaciones_l4_vectores.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\rules\sas\catalogo\funciones-guia.yaml`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_interprete_formatos.py`

**Interfaces:**
- Consumes: `escribir_formato(valor: float | None, formato: str) -> str` (D1-16), `parsear_informat(spec: str) -> Informat`.
- Produces: `escribir_formato` extendida a `w.d`, `zw.d`, `commaw.d`, `dollarw.d`, `percentw.d`, `bestw.` y `$w.`; `talend_funciones_formato._put` emite Java para `w.d`, `z` y `comma`, y `Unsupported` con `P-JAVA-FORMATO-<nombre>` para `dollar`, `percent` y `best` hasta que sus vectores pasen en Studio.

**Vectores** (`put`; páginas de `leforinforref`; lo deducido se confirma leyendo la página):

| id | entrada | esperado | página |
|---|---|---|---|
| `putn-01` | `[3.14159, "8.2"]` | `"    3.14"` | p. 503 |
| `putn-02` | `[5, "z3."]` | `"005"` | p. 548 |
| `putn-03` | `[-5, "z3."]` | `"-05"` (deducido) | p. 548 |
| `putn-04` | `[1234.5, "comma10.2"]` | `"  1,234.50"` | p. 181 |
| `putn-05` | `[1234.5, "dollar10.2"]` | `"  $1,234.50"` | p. 198 |
| `putn-06` | `[0.5, "percent8."]` | `"     50%"` (deducido) | p. 454 |
| `putn-07` | `[null, "8.2"]` | `"       ."` | p. 503 |
| `putn-08` | `[123456, "3."]` | `"***"` o el formato `BEST` que la página fije (se lee p. 503 antes; si no lo fija, `incierto` y `Pendiente: P-FORMATO-ANCHO-EXCEDIDO`) | p. 503 |
| `putc-01` | `["abc", "$5."]` | `"abc  "` (el formato de texto rellena a la derecha; se lee la página de `$w.` con `grep -n "w. Format" docs/referencia/sas/leforinforref.INDEX.md` y, si no está indexada, `Pendiente: P-FORMATO-CARACTER-SIN-PAGINA`) | por confirmar |

- [ ] **Step 1: Write the failing tests:** un test por vector; `verificar()` y `verificar(motor="interprete")` en cero fallos; `translate_to_talend("put(a, 8.2)").java` contiene `String.format` con el ancho 8 y 2 decimales y justifica a la derecha; `translate_to_talend("put(a, percent8.)")` lanza `Unsupported` con `P-JAVA-FORMATO-percent`.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_interprete_formatos.py tests/unit/test_corpus_semantica.py tests/unit/test_talend_expresiones.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement** los tres motores; agregar `put` con formato literal a `FUNCIONES_CON_CASO` y regenerar `L4`.
- [ ] **Step 4: Catálogo** (`put-function`, `lefunctionsref.pdf, p. 1417`, en `funciones-guia.yaml` o en `funciones-usadas.yaml` si ya está) y `tests/unit/test_catalogo_sas.py`.
- [ ] **Step 5: Run** `uv run python -m pytest tests/unit/test_migrar_corpus_anillo_b.py -q -p no:cacheprovider -k L4`, la tanda del golden, `uv run ruff check src tests tools`, lote C. **Commit** `hito N n: PUT con formatos numericos y de texto, justificados como en SAS`.

---

## Parte VI. MG-P3-06: expresiones regulares `PRX*` (serie `n`, 6 h)

### Task D1-18: `PRXMATCH`, `PRXPARSE` y `PRXCHANGE` en el intérprete, y las diferencias con Java (MG-P3-06; serie `n`)

Las expresiones regulares de SAS son de tipo Perl (`lefunctionsref`, p. 68 a 79, «Pattern Matching Using Perl Regular Expressions (PRX)»): llevan delimitadores y banderas dentro del texto (`/\d+/i`, `s/a/b/`), y `PRXMATCH` devuelve la **posición** de la primera coincidencia (0 si no hay), no un lógico. Java usa `java.util.regex`, con otra forma de pasar banderas y sin delimitadores. `PRXPOSN`, `PRXPAREN` y `CALL PRXSUBSTR` dependen del estado de la última coincidencia de ese identificador de patrón (`lefunctionsref`, p. 1408 y 1412): quedan `Pendiente: P-PRX-ESTADO`.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\interprete_prx.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\interprete_funciones.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\corpus_semantica_prx.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\corpus_semantica_funciones.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\semantica\vectores.yaml`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\docs\prx-diferencias-java.md`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\corpus_lib\especificaciones_l4_vectores.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\rules\sas\catalogo\funciones-guia.yaml`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_interprete_prx.py`

**Interfaces:**
- Consumes: `interprete_funciones.FUNCIONES`, `semantica.es_faltante(valor)`, `semantica.como_texto(valor)`.
- Produces:
  ```python
  # interprete_prx.py
  def compilar(patron: str) -> tuple[re.Pattern[str], str | None]:
      """`/regex/flags` -> (patrón de Python, None); `s/regex/reemplazo/flags` -> (patrón, reemplazo).
      Banderas i, s, m, x; cualquier otra lanza NoSoportadoEnInterprete('prx', bandera)."""
  def prxmatch(patron: str, texto: object) -> int: ...                  # posición 1-based o 0
  def prxchange(patron: str, veces: int, texto: object) -> str: ...     # veces = -1: todas
  FUNCIONES: dict[str, Funcion]    # prxmatch, prxchange; prxparse devuelve el texto del patrón
  ```

**Vectores** (las barras invertidas del JSON van duplicadas; páginas de `lefunctionsref`):

| id | funcion | entrada | esperado | página |
|---|---|---|---|---|
| `prx-01` | `prxmatch` | `["/\\d{3}/", "ab1234"]` | `3` | p. 1403 |
| `prx-02` | `prxmatch` | `["/z/", "abc"]` | `0` | p. 1403 |
| `prx-03` | `prxmatch` | `["/ABC/i", "xabc"]` | `2` (bandera `i`) | p. 1403 |
| `prx-04` | `prxmatch` | `["/^a/", "ba"]` | `0` (el ancla `^` es del texto completo) | p. 1403 |
| `prx-05` | `prxchange` | `["s/(\\d+)/<$1>/", -1, "a12b345"]` | `"a<12>b<345>"` | p. 1398 |
| `prx-06` | `prxchange` | `["s/a/x/", 1, "aaa"]` | `"xaa"` | p. 1398 |
| `prx-07` | `prxchange` | `["s/\\s+/ /", -1, "a   b  c"]` | `"a b c"` | p. 1398 |
| `prx-08` | `prxmatch` | `["/a/", null]` | `faltante` | `confianza: incierto`: la página no dice el resultado con un argumento faltante; `Pendiente: P-PRX-FALTANTE` |

`docs/prx-diferencias-java.md` (escrito a mano; es la única excepción a «documento generado» de este plan, porque es una comparación, no un inventario) trae una tabla `construcción SAS | equivalente Java | estado` con, como mínimo: delimitadores `/.../` (se quitan), banderas `i s m x` (a `Pattern.CASE_INSENSITIVE`, `DOTALL`, `MULTILINE`, `COMMENTS`), resultado de `PRXMATCH` (posición 1-based frente a `find()` booleano), `PRXCHANGE` con `-1` (`replaceAll`) y con `1` (`replaceFirst`), y el reemplazo `$1`. Cada fila del documento cita su página (`lefunctionsref`, p. 68 a 79) y su vector, y **toda construcción de esas páginas que no se haya comparado con un vector** se lista como `Pendiente:` con el nombre de la construcción (por ejemplo las clases POSIX `[[:alpha:]]`, `\Z`, `\G` y los modificadores de la bandera `o`): se leen las páginas y se anota cada una; ninguna se declara equivalente sin vector. Una prueba (`test_interprete_prx.py`) exige que cada función `prx*` de `talend_tabla._FUNCTIONS` y del intérprete tenga fila en el documento.

- [ ] **Step 1: Write the failing tests:** un test por vector con `llamar(...)`; `compilar("/a/x")` y `compilar("/a/q")` (esta lanza `NoSoportadoEnInterprete('prx', 'q')`); `llamar("prxposn", [1, 1, "a"])` lanza con `P-PRX-ESTADO`; la prueba del documento; `verificar()` y `verificar(motor="interprete")` en cero fallos.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_interprete_prx.py tests/unit/test_corpus_semantica.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement** el módulo, el oráculo (otra implementación: `re` con la conversión de delimitadores escrita por separado) y el documento. Agregar `prxmatch` y `prxchange` a `FUNCIONES_CON_CASO` con el patrón como literal y regenerar `L4`.
- [ ] **Step 4: Catálogo:** `prxmatch-function` (p. 1403), `prxchange-function` (p. 1398), `prxparse-function` (p. 1410) y `prxposn-function` (p. 1412, `no_verificada`, nota `Pendiente: P-PRX-ESTADO`). `tests/unit/test_catalogo_sas.py`.
- [ ] **Step 5: Run** `uv run python -m pytest tests/unit/test_migrar_corpus_anillo_b.py -q -p no:cacheprovider -k L4`, la tanda del golden y `uv run ruff check src tests tools`. **Commit** `hito N n: PRXMATCH, PRXPARSE y PRXCHANGE en el interprete, con las diferencias con Java documentadas`.

---

### Task D1-19: `PRX*` a Java de Talend (MG-P3-06; serie `n`)

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\expressions\talend_funciones_prx.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\expressions\talend_tabla.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\docs\prx-diferencias-java.md`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\rules\sas\catalogo\funciones-guia.yaml`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_talend_prx.py`

**Interfaces:**
- Consumes: `E(java: str, kind: str = "any", literal: str | None = None)`, `Unsupported`, `_need(args, low, high=None, name="")`, `_jstr(raw: str) -> str` de `talend_base.py`, `interprete_prx.compilar(patron: str)` (para validar el patrón literal al traducir).
- Produces: `talend_tabla._FUNCTIONS` gana `prxmatch` y `prxchange`.
  ```python
  def _prxmatch(p: _P, args: list[E]) -> E: ...
  def _prxchange(p: _P, args: list[E]) -> E: ...
  ```
  Solo con el patrón **literal** (`args[0].literal is not None`); un patrón en una columna queda `Unsupported` con `P-JAVA-PRX-DINAMICO`. Una expresión de una línea no puede guardar el `Matcher`, así que `PRXMATCH` se emite como `(texto.matches("(?s)(?:banderas)^(.*?)(?:regex)(?s:.*)$") ? texto.replaceFirst("(?s)^(.*?)(?:regex)(?s:.*)$", "$1").length() + 1 : 0)` (el grupo 1 es el prefijo; la posición es su largo más uno), con la bandera `i` como `(?i)` y la guarda de nulo de `_strfn`. `PRXCHANGE` con `-1` es `texto.replaceAll(regex, reemplazo)` y con `1` es `replaceFirst`; otro conteo, `Unsupported` con `P-JAVA-PRXCHANGE-CONTEO`.

- [ ] **Step 1: Write the failing tests:** `translate_to_talend("prxmatch('/\\d{3}/', a)").java` contiene `replaceFirst` y `.length() + 1`; `translate_to_talend("prxchange('s/a/x/', -1, a)").java` contiene `replaceAll`; con patrón en columna lanza `Unsupported` con `P-JAVA-PRX-DINAMICO`; con conteo 3, `P-JAVA-PRXCHANGE-CONTEO`; el Java emitido compila con `javac` suelto sobre el molde del anillo A (`tests/unit/test_talend_humo.py` muestra cómo se corre).
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_talend_prx.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement** los dos constructores y actualizar el documento con la columna «Java emitido». Catálogo: `prxmatch-function` y `prxchange-function` pasan a `reconocida`.
- [ ] **Step 4: Run** `uv run python -m pytest tests/unit/test_talend_prx.py tests/unit/test_catalogo_sas.py tests/unit/test_migrar_corpus_l4_a.py -q -p no:cacheprovider`, la tanda del golden y `uv run ruff check src tests tools`.
- [ ] **Step 5: Lote C** de los casos `l4_1xx` de `prx*` (`tools/validar_caso_studio.py <casos>`): el Java de una expresión regular se comprueba en Studio, no se da por bueno por compilar. Si Studio no conecta, «lote C pendiente» con motivo. **Commit** `hito N n: PRXMATCH y PRXCHANGE emitidos a Java con patron literal`.

---

## Parte VII. MG-P3-07: `PROC FORMAT` como mapas (serie `n`, 4 h)

### Task D1-20: Formatos de usuario: rangos, `OTHER` y `PUT` con mapa (MG-P3-07; serie `n`)

**Contrato con el Plan C (C-23, MG-P6-07).** C-23 reconoce `VALUE nombre (rangos) = 'etiqueta'` y entrega `FormatoUsuario(nombre, rangos, otro)` en `src/sgm/ir/formatos_usuario.py` más `lower_format` en `src/sgm/ir/lower_procs_format.py`; deja los rangos con `-` como `P-FORMATO-RANGO-SIN-SOPORTE` «hasta que D1 lo cubra». Esta tarea es D1: da la **semántica** (cómo se evalúa un valor contra los rangos) y la traducción de `PUT(x, $fmt.)`. Si C-23 todavía no está integrada al empezar, esta tarea crea `formatos_usuario.py` con exactamente esa firma y C-23 rebasea sobre ella.

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\ir\formatos_usuario.py` (de C-23)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\ir\formatos_rangos.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\interprete_formatos.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\corpus_semantica_formato_usuario.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\corpus_semantica_funciones.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\semantica\vectores.yaml`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\expressions\talend_funciones_formato.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\corpus_lib\especificaciones_l4c.py` (si no la creó D1-9, se crea aquí; si ya existe, se agrega el caso)
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_formatos_rangos.py`

**Interfaces:**
- Consumes: `FormatoUsuario(nombre: str, rangos: tuple[tuple[str, str], ...], otro: str | None)` (C-23), `parsear_informat(spec: str) -> Informat` (D1-15), `semantica.comparar(izquierda, derecha) -> int`, `Plan.formatos: list[FormatoUsuario]` (C-23 los deja en el plan; si usa otro nombre, se usa el suyo y se anota en `PROGRESS.md`).
- Produces:
  ```python
  # formatos_rangos.py
  @dataclass(frozen=True)
  class Rango:
      bajo: float | str | None       # None = LOW
      alto: float | str | None       # None = HIGH
      bajo_excluido: bool            # 1-<5: el 1 entra
      alto_excluido: bool            # 1-<5: el 5 no entra
  def parsear_rango(texto: str) -> Rango: ...        # "1-5", "low-0", "100-high", "1-<5", "A", "."
  def aplicar_formato(formato: FormatoUsuario, valor: object) -> str: ...
  ```
  `aplicar_formato`: busca el primer rango que contiene al valor, en el orden del `VALUE`; si ninguno y hay `OTHER`, su etiqueta; si ninguno y no hay `OTHER`, **`Pendiente: P-FORMATO-SIN-RANGO`** (la página de `VALUE`, `proc`, p. 1173, se lee antes: si dice que el valor se muestra tal cual, el vector `fmtu-05` pasa a `deducido` con ese resultado; si no lo dice, queda `incierto` y el intérprete lanza `NoSoportadoEnInterprete`).

**Vectores** (`put_usuario`; `entrada` = `[valor, formato]` con `formato` un objeto JSON `{"rangos": [[rango, etiqueta], ...], "otro": etiqueta|null}`; páginas de `proc`):

| id | entrada | esperado | página |
|---|---|---|---|
| `fmtu-01` | `["A", {"rangos": [["A","Activo"],["I","Inactivo"]], "otro": "Otro"}]` | `"Activo"` | p. 1173 |
| `fmtu-02` | `["X", {"rangos": [["A","Activo"],["I","Inactivo"]], "otro": "Otro"}]` | `"Otro"` | p. 1173 |
| `fmtu-03` | `[3, {"rangos": [["1-5","bajo"],["6-high","alto"]], "otro": null}]` | `"bajo"` | p. 1173 |
| `fmtu-04` | `[5, {"rangos": [["1-<5","bajo"],["5-high","alto"]], "otro": null}]` | `"alto"` (el `<` excluye el extremo) | p. 1173 |
| `fmtu-05` | `[5.5, {"rangos": [["1-5","bajo"],["6-high","alto"]], "otro": null}]` | `incierto` (sin rango ni `OTHER`; ver arriba) | p. 1173 |
| `fmtu-06` | `[null, {"rangos": [[".","sin dato"],["low-0","neg"]], "otro": null}]` | `"sin dato"` (un faltante coincide con `.`) | p. 1173 |
| `fmtu-07` | `[-2, {"rangos": [["low-0","neg"]], "otro": null}]` | `"neg"` (`LOW` no incluye al faltante; `lrcon`, p. 125) | p. 1173 |

Java: un formato con 30 rangos o menos se emite como una cadena de ternarios en el `tMap` (`(x >= 1 && x <= 5) ? "bajo" : ...`, con la comparación de faltantes de `_compare`); uno de más de 30, `Pendiente: P-FORMATO-GRANDE` (la forma correcta es una tabla de búsqueda `tMap` con `LOOKUP`, que es del Plan F2). `INVALUE` y `PICTURE` (`proc`, p. 1144 y 1150) quedan `Pendiente: P-FORMATO-INVALUE` y `P-FORMATO-PICTURE`.

**Caso `l4_160_format_usuario` (`capa: B`, `estado: traducible`):** el mismo del Plan C (`PROC FORMAT; VALUE $estf 'A'='Activo' 'I'='Inactivo' OTHER='Otro'; RUN;` y `desc = PUT(estado, $estf.)`) con la fila extra `4,` (estado en blanco) cuyo esperado sale del oráculo; el de C (`l3_34_format_value_y_put`) prueba el reconocimiento de la sentencia y este, la evaluación.

- [ ] **Step 1: Write the failing tests** en `test_formatos_rangos.py`: `parsear_rango("1-<5") == Rango(1.0, 5.0, False, True)`, `parsear_rango("low-0") == Rango(None, 0.0, False, False)`; los siete vectores con `aplicar_formato`; `verificar()` y `verificar(motor="interprete")` en cero fallos.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_formatos_rangos.py tests/unit/test_corpus_semantica.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement** `formatos_rangos.py`, la evaluación en el intérprete (que lee `plan.formatos`), el oráculo (otra implementación, sobre cadenas de rango) y el Java. En C-23 se cambia el `P-FORMATO-RANGO-SIN-SOPORTE` por una llamada a `parsear_rango` (aviso a quien lleve C en el commit).
- [ ] **Step 4: Run** `uv run python -m pytest tests/unit/test_migrar_corpus_anillo_b.py tests/unit/test_migrar_corpus_l4_a.py tests/unit/test_catalogo_sas.py -q -p no:cacheprovider`, la tanda del golden, `uv run ruff check src tests tools`, lote C del caso `l4_160`. **Commit** `hito N n: formatos de usuario con rangos y OTHER evaluados como mapa`.

---

## Parte VIII. MG-P3-08: documento de funciones generado (serie `n`, 4 h)

### Task D1-21: `docs/funciones.md` generado desde las tablas, sin edición manual (MG-P3-08; serie `n`)

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\generar_docs_funciones.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\docs\funciones.md` (lo escribe la herramienta; empieza con `<!-- GENERADO por tools/generar_docs_funciones.py: no editar a mano -->`)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\interprete_texto.py`, `interprete_numerico.py`, `interprete_formatos.py`, `interprete_fechas.py`, `interprete_intervalos.py`, `interprete_diferencias.py`, `interprete_prx.py` (solo docstrings: la primera línea es la firma y una línea `Faltantes: ...` dice qué hace con un faltante)
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_docs_funciones.py`

**Interfaces:**
- Consumes: `funciones_inventario.inventario(repo: Path, talend=None, oraculo=None, interprete=None) -> dict[str, dict]` (D1-1), `corpus_semantica.cargar_vectores(ruta) -> list[dict]`, `translate_to_talend(sas: str, entrada: str = "input_row") -> Result` (su `.java`), `interprete_funciones.FUNCIONES: dict[str, Funcion]`.
- Produces:
  ```python
  def generar(repo: Path) -> str:
      """Markdown de `docs/funciones.md`: un índice por familia (texto, numéricas, fechas, conversión,
      regulares, formatos) y, por función: firma y `Faltantes:` (docstring del intérprete), página
      (`fuente` del catálogo), motores (intérprete, oráculo, Java), ejemplo de Java (el de
      `translate_to_talend` sobre los argumentos del primer vector no `incierto`), vectores (ids y
      confianza) y los `Pendiente: P-...` de la `nota` del catálogo."""
  # CLI: python tools/generar_docs_funciones.py [--comprobar]
  ```
  `--comprobar` sale con 1 si `docs/funciones.md` difiere de `generar(repo)`. La herramienta **no** se engancha a `tools/ci.py` ni a `tools/validacion.py` (son del Plan A); la prueba cumple esa función.

La «ficha por función» que pide la sección 5.7 del plan maestro es esta entrada generada: el esquema de `rules/sas/functions/` y el del catálogo son cerrados o de un argumento, y una ficha escrita a mano se desvía del código; la ficha generada no puede.

- [ ] **Step 1: Write the failing tests** en `test_docs_funciones.py`: (a) `generar(repo)` con un repo mínimo (una función, un vector) produce el encabezado `GENERADO`, la sección de su familia y el vector; (b) `docs/funciones.md` igual a `generar(REPO)` byte a byte (falla si alguien lo edita a mano); (c) cada función de `interprete_funciones.FUNCIONES` tiene al menos un vector `documentado` o `deducido`, una entrada de catálogo con página y una línea `Faltantes:` en su docstring; las que no, están en una lista `SIN_FICHA` de la prueba con su motivo (`Pendiente:`), y la lista **no puede crecer** (la prueba compara su largo con el de la línea base de D1-1).
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_docs_funciones.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement** `generar` y la CLI; completar los docstrings que falten (mecánico: la firma y `Faltantes:` de cada función ya escrita en D1-7 a D1-20); correr `uv run python tools/generar_docs_funciones.py` para escribir el documento.
- [ ] **Step 4: Run** `uv run python tools/generar_docs_funciones.py --comprobar`, `uv run python -m pytest tests/unit/test_docs_funciones.py tests/unit/test_no_script_specific_names.py -q -p no:cacheprovider` (el documento no puede nombrar scripts del cliente) y `uv run ruff check src tests tools`. **Commit** `hito N n: docs/funciones.md generado desde las tablas de funciones`.

---

## Parte IX. MG-P3-09: brechas del oráculo de SQL (serie `n`, 4 h)

### Task D1-22: `LENGTH`, `COMPBL`, `CONTAINS` e `IS MISSING` sobre expresión en el oráculo de `PROC SQL` (MG-P3-09; serie `n`)

Al redactar, `uv run python tools/corpus_datos/validaciones_cruce.py` da **19 resultados sin verificar** en `L8/validaciones`: 8 en `v03_pais_dane` (por `LENGTH()`: `INCONS_UBICACION_CTE`/`_AHO`, sus dependientes y sus archivos) y 11 en `v06_normalizacion` (por `COMPBL()`: `SABANA_NORM_*`, `MOTIVO_NORM_*` y dependientes). Los otros seis casos están en cero. Además, `v03` y `v06` usan `CONTAINS` (p. ej. `UPPER(t1.DIRECCION) CONTAINS UPPER('sin dir')`, `v03/programa.sas:216`) e `IS MISSING` se rechaza cuando el operando no es una columna (`traduccion_sql.py:101`).

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\corpus_lib\traduccion_sql.py` (146 líneas)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\corpus_lib\traduccion_sql_sas.py` (las funciones de SQLite con semántica de SAS y la reescritura de `CONTAINS` y de `IS MISSING` sobre expresión)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\corpus_lib\oraculo_sql.py` (registrar las funciones en la conexión: `con.create_function`)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\corpus_lib\DIFERENCIAS.md`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\semantica\vectores.yaml` (los vectores de `length`, `compbl` y `is_missing` de D1-7 y D1-8 son los que usa el oráculo)
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_corpus_oraculo_sql.py` y `tests\unit\test_corpus_validaciones.py`

**Interfaces:**
- Consumes: `a_sqlite(sql_sas: str, esquema: Esquema | None = None) -> str` (`traduccion_sql.py:47`), `RENOMBRES_FUNCION: dict[str, str]` (línea 26), `FUNCIONES: frozenset[str]` (línea 22), `ejecutar_proc_sql(sentencias, entradas, salidas)` (`oraculo_sql.py:24`), `corpus_semantica_funciones.evaluar(funcion: str, *args)` (las funciones de SAS del oráculo de funciones: una sola fuente de verdad para `length`, `compbl` y `is_missing`), `NoSoportado`.
- Produces:
  ```python
  # traduccion_sql_sas.py
  FUNCIONES_SAS: dict[str, tuple[str, int]]
  # {"length": ("sas_length", 1), "compbl": ("sas_compbl", 1), "contains": ("sas_contains", 2),
  #  "missing": ("sas_falta", 1)}
  def registrar(con: sqlite3.Connection) -> None:
      """Crea en SQLite sas_length (blancos finales fuera; mínimo 1), sas_compbl, sas_contains
      (distingue mayúsculas) y sas_falta (None o texto en blanco), todas con `evaluar`."""
  def reescribir_contains(texto: str) -> str:
      """`a CONTAINS b` -> `sas_contains(a, b)`, con operandos de la forma `[t.]col`, literal
      protegido o llamada con un nivel de paréntesis; otro operando lanza NoSoportado."""
  ```
  `CONTAINS` está en `sqlproc`, p. 67 («Using Other Conditional Operators»; se lee antes de fijar si distingue mayúsculas: SAS sí, por eso `v06` usa `UPPER`). `IS MISSING` sobre una expresión pasa a `sas_falta(expresión)` (un texto en blanco y un `NULL` son faltante; el faltante numérico es `NULL`), y la rama de columna con tipo no cambia.

- [ ] **Step 1: Write the failing tests** en `test_corpus_oraculo_sql.py`: (a) una consulta `SELECT LENGTH(x) AS n FROM t` con filas `"abc   "`, `" "` y `NULL` devuelve `3`, `1` y `1` (`lefunctionsref`, p. 1180; vectores `length-01` y `length-02`); (b) `COMPBL("a   b")` devuelve `"a b"` (`compbl-01`); (c) `WHERE UPPER(d) CONTAINS UPPER('sin dir')` filtra bien y `WHERE (a || b) CONTAINS 'x'` lanza `NoSoportado` (operando que no es de la forma admitida; no se adivina); (d) `WHERE COMPBL(n) IS MISSING` sobre una expresión funciona; (e) en `test_corpus_validaciones.py`: `cruzar("v03_pais_dane")` y `cruzar("v06_normalizacion")` dan `no_verificadas == {}` y `diferencias == {}`.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_corpus_oraculo_sql.py tests/unit/test_corpus_validaciones.py -q -p no:cacheprovider`; esperado: `Construcción SAS no soportada por el oráculo: función LENGTH()`.
- [ ] **Step 3: Implement** `traduccion_sql_sas.py`; en `traduccion_sql.py`, agregar los nombres de `FUNCIONES_SAS` a `RENOMBRES_FUNCION` y llamar a `reescribir_contains` antes de `_rechazar_construcciones`; reemplazar el `raise NoSoportado("IS MISSING sobre una expresión ...")` por la reescritura a `sas_falta`; en `oraculo_sql.py`, llamar a `registrar(con)` tras abrir la conexión.
- [ ] **Step 4: Cruce.** `uv run python tools/corpus_datos/validaciones_cruce.py`: las 8 corridas con `no verificadas 0`. Si aparece una `diferencia`, **no se toca el esperado**: se investiga con la página (puede ser un error del programa SAS plantado o del oráculo) y se anota en `PROGRESS.md`; un resultado que no se puede decidir queda `no verificada` con motivo y la tarea no se declara cerrada para ese caso.
- [ ] **Step 5: Run** `uv run python -m pytest tests/unit/test_corpus_oraculo_sql.py tests/unit/test_corpus_validaciones.py tests/unit/test_sql_semantica.py -q -p no:cacheprovider` y `uv run ruff check src tests tools`. Actualizar `DIFERENCIAS.md` (las cuatro construcciones dejan de ser brechas). **Commit** `hito N n: oraculo SQL con LENGTH, COMPBL, CONTAINS e IS MISSING sobre expresion; 19 resultados verificados`.

---

## D1-Gate: compuerta de MG-P3 (serie `n`, 1 h)

### Task D1-Gate: todos los vectores en B y en lote C; `L4` completo; `xfail` con su motivo

**Criterio de salida** (aceptables de MG-P3-01 a MG-P3-09 de la sección 5.7 y de la fase del plan maestro; lo que este plan se compromete a probar):
1. **Vectores:** `uv run python tools/corpus_semantica.py verificar` y `... verificar --motor interprete` dan cero fallos, y los dos motores coinciden en cada vector no `incierto` (`test_interprete_vectores.py`). Los `incierto` están listados con su `Pendiente:`.
2. **`L4` completo en B:** todos los casos de `tests/corpus/L4/` con `estado` `traducible` o `revisado` (los 19 de antes, `l4_20` incluido, más los `l4_100` a `l4_199` de este plan) coinciden con su `esperado/` en `test_migrar_corpus_anillo_b.py`.
3. **`L4` completo en A:** en `migrar_pendientes.yaml` no queda ningún caso de `L4` salvo los que declaran un `P-` de alcance (`P-JAVA-...`, `P-LONGITUD-VARIABLE`, `P-INTCK-CONTINUO`, `P-YRDIF-AGE-29FEB`, ...), cada uno con su página.
4. **Lote C:** una sola corrida con todos los casos `L4` que migran sin pendiente: `uv run python tools/corpus_studio.py lote <casos> --jobs <carpeta> --proyecto <proyecto>` para compilar y `uv run python tools/validar_caso_studio.py <casos>` para ejecutar y comparar; cuenta aparte compilaron y ejecutaron-y-coinciden. Se miden ahí las tres cosas abiertas: `LENGTH` de un blanco (D1-7), fin de mes de `INTNX` en `TalendDate.addDate` (D1-13) y `PRXMATCH` inline (D1-19).
5. **`L8/validaciones`:** `validaciones_cruce.py` sin `no verificadas` (D1-22).
6. **`xfail` de expresiones:** al empezar había dos casos de expresiones en `migrar_pendientes.yaml` (`l0_12_bandera_numerica`, `P-FILTRO-SIN-TRADUCIR`, que es de Plan B por el filtro numérico; `l4_20_put_fechas_pendiente`, `P-ASIGNACION-SIN-TRADUCIR`) y ninguno de funciones en `CONOCIDOS`. El cierre deja `l4_20` fuera (D1-16) y registra el motivo de cualquier otro que haya aparecido; `l0_12` sigue del Plan B. La cifra de `PROGRESS.md` pasa de «dos de expresiones, uno de ellos pendiente de D1» a «uno, de Plan B».

- [ ] **Step 1: Run** la suite completa `uv run python -m pytest -q` y `uv run ruff check src tests tools`; `uv run python tools/funciones_inventario.py` y comparar con la línea base de D1-1; `uv run python tools/generar_docs_funciones.py --comprobar`.
- [ ] **Step 2: Run** el lote C (punto 4). Si Studio no conecta: `sgm studio salud` y `docs/guia-validacion-studio.md`, sección 7; no se reinstala nada ni se cambia `talend-mcp`. El resultado es «lote C pendiente» con el motivo y la compuerta **no** se declara cerrada.
- [ ] **Step 3: Recalcular la fila de MG-P3 de la sección 11b** del plan maestro (`docs/plan-reescritura/plan-migrador-general.md`, hoy `| MG-P3 Expresiones y funciones | 80 | 14,5 | 18 % | ... |`) con el método de esa sección: horas acreditadas = las de las tareas cerradas con A, B y C; las que cierran solo A y B se acreditan sin el lote C y se anota «lote C pendiente». Actualizar la tabla de MG-P3 y su «Estado» en el mismo cambio, y corregir la cifra «20 `xfail`» del hito 107 (D1-1 ya la había marcado).
- [ ] **Step 4: Registrar** en `PROGRESS.md` el hito de cierre: vectores por motor y por confianza, casos `L4` por anillo, funciones por motor (inventario antes y después), pendientes por código, horas acreditadas, y qué quedó fuera con su motivo.
- [ ] **Step 5: Commit.** `hito N n: compuerta de MG-P3, vectores y L4 en B y en lote C`.

---

## Resumen de horas

| Tareas | Origen | Serie | Horas |
|---|---|---|---|
| D1-1 a D1-5 | MG-P3-01 | n | 9 |
| D1-6 a D1-9 | MG-P3-02 | n | 10 |
| D1-10, D1-11 | MG-P3-03 | n | 7,5 |
| D1-12, D1-13, D1-14 | MG-P3-04 | n | 12 |
| D1-15, D1-16, D1-17 | MG-P3-05 | n | 8 |
| D1-18, D1-19 | MG-P3-06 | n | 6 |
| D1-20 | MG-P3-07 | n | 4 |
| D1-21 | MG-P3-08 | n | 4 |
| D1-22 | MG-P3-09 | n | 4 |
| D1-Gate | cierre de MG-P3 (la hora restante de MG-P3-09; el plan maestro asigna 6 h a P3-09 y 80 h a la fase, con 14,5 h ya acreditadas, de modo que el reparto por tarea de este plan es una estimación que suma 65,5) | n | 1 |
| **Total** | | | **65,5** |

Detalle de D1-1 a D1-5: 1,5 + 1,5 + 1,5 + 2,5 + 2 = 9. D1-6 a D1-9: 1,5 + 2,5 + 3 + 3 = 10. D1-10 y D1-11: 3 + 4,5 = 7,5. D1-12 a D1-14: 3 + 3,5 + 5,5 = 12. D1-15 a D1-17: 3 + 2,5 + 2,5 = 8. D1-18 y D1-19: 3,5 + 2,5 = 6. La suma es 9 + 10 + 7,5 + 12 + 8 + 6 + 4 + 4 + 4 + 1 = 65,5 h, igual a MG-P3 restante (80 h menos 14,5 h acreditadas). Las horas por tarea son estimaciones del plan; el crédito real se mide con el método de la sección 11b.

## Dependencias

**Necesita de otros planes**

| De | Tarea | Para qué |
|---|---|---|
| Plan A | compilación y validación en Studio (`tools/validar_caso_studio.py`, `tools/corpus_studio.py lote`, salud con estados) | el lote C de D1-5, D1-7 a D1-19 y D1-Gate; sin Studio esas partes quedan «lote C pendiente» con su motivo y no se cuentan |
| Plan B | B-3 y B-4 (esquemas con longitud de `CHAR`) | `P-LONGITUD-VARIABLE` y `P-CONCAT-LONGITUD-VARIABLE` (D1-4, D1-7, D1-9): con la longitud declarada, `||`, `RIGHT` y `REVERSE` pueden rellenar |
| Plan B | B-5 a B-8 (constructores del lowering) y la extracción de `lower_data.py` | D1-9 solo agrega una llamada en `lower_data.py` (770 líneas); la extracción es de B |
| Plan B | `LAG`, `DIF` y estado por fila (B-13), `SELECT/WHEN` (`l4_21` a `l4_23`) | no son de este plan: `LAG`/`DIF` usan la tabla de funciones de D1-2 solo como llamadas por fila y `SELECT/WHEN` usa los operadores de D1-4; la numeración `l4_21` a `l4_23` es de B y la de D1 empieza en `l4_100` |
| Plan C | C-23 (`FormatoUsuario`, `lower_format`, `plan.formatos`) | D1-20 (la evaluación de rangos y `PUT` con mapa); C-23 reemplaza `P-FORMATO-RANGO-SIN-SOPORTE` por `parsear_rango` |
| Plan K | K-2 y K-3 (datos sintéticos) | más filas por caso de fechas si hacen falta casos de fin de mes con volumen |

**Entrega a otros planes**

| A | Qué |
|---|---|
| Plan C | funciones dentro de `PROC SQL` (C-15): `interprete_funciones.llamar` y `FUNCIONES` (D1-2 y D1-4) para evaluar `LENGTH`, `COMPBL`, `COALESCE`, fechas y `PUT` en un `SELECT` o en un `WHERE`; el oráculo con `sas_length`, `sas_compbl`, `sas_contains` y `sas_falta` (D1-22) para las pruebas de capa A de SQL; la semántica de faltantes de `sum`/`mean` por fila (D1-11) separada de la de grupo (`P-SUM-TODO-FALTANTE`, de C-6) |
| Plan E | `%SYSFUNC`: la misma tabla de funciones y el mismo adaptador `evaluar_vector`, de modo que `%SYSFUNC(UPCASE(...))` y `%SYSFUNC(INTNX(...))` se evalúan con la semántica de D1-7 a D1-14; `%SYSFUNC(PUTN(...))` con `escribir_formato` (D1-16, D1-17); `P-ESPECIALES-FALTANTE` y `P-PRX-ESTADO` como límites conocidos |
| Plan F1 y F2 | `interprete_funciones.FUNCIONES` como la tabla única de funciones; la decisión de representación de fechas en Java (días desde 1960 frente a `Date`, D1-12) |
| Plan G | `docs/funciones.md` generado (D1-21) y `tools/funciones_inventario.py` (D1-1) como fuente de la cobertura de funciones en `docs/cobertura.md`; la numeración `l4_100` a `l4_199` reservada a este plan |

## Self-review

- **Cobertura de la spec:** MG-P3-01 en D1-1 a D1-5 (más D1-Gate, puntos 1 y 4); P3-02 en D1-6 a D1-9; P3-03 en D1-10 y D1-11; P3-04 en D1-12 a D1-14; P3-05 en D1-15 a D1-17 (las formas `w.d` del programa grande en D1-15, paso previo); P3-06 en D1-18 y D1-19; P3-07 en D1-20 (con el contrato con C-23); P3-08 en D1-21; P3-09 en D1-22 (los 19 resultados: 8 de `v03` y 11 de `v06`); aceptación de la fase en D1-Gate.
- **Páginas citadas** (todas son entradas de los índices en `docs/referencia/sas/`, comprobadas al redactar): `lefunctionsref` p. 68, 230, 495, 503, 506, 508, 545, 557, 560, 561, 572, 587, 608, 634, 639, 642, 712, 807, 841, 1065, 1067, 1071, 1080, 1087, 1092, 1131, 1180, 1181, 1185, 1206, 1230, 1232, 1233, 1236, 1238, 1240, 1251, 1264, 1269, 1395, 1398, 1403, 1408, 1410, 1412, 1417, 1428, 1478, 1480, 1483, 1486, 1504, 1528, 1555, 1568, 1572, 1574, 1576, 1580, 1613, 1619, 1624, 1627, 1724, 1729, 1731; `leforinforref` p. 181, 186, 194, 198, 255, 267, 454, 503, 522, 525, 548, 556, 616, 646, 649, 653, 682, 696, 744, 755; `lrcon` p. 116, 123 a 129, 143, 144, 149, 151, 155, 157, 172, 176 a 180; `lesysoptsref` p. 432; `proc` p. 1127, 1144, 1150, 1173; `sqlproc` p. 67. Las páginas 635 y 636 (`DATDIF`, base `30/360`) y 1732 y 1733 (`YRDIF`) son páginas del texto, no entradas del índice: se citan en los vectores, nunca en el campo `fuente` de un catálogo (allí va la entrada indexada, p. 634 y p. 1731).
- **Lo que no tiene página y queda `Pendiente:`:** `PROPCASE` en Java (`P-JAVA-PROPCASE`), `||` y `RIGHT` con la longitud de la variable (`P-LONGITUD-VARIABLE`), valores especiales `.A` a `.Z` (`P-ESPECIALES-FALTANTE`), alineación `M`, intervalos múltiples y desplazados de `INTNX`, `INTCK` continuo, `YRDIF` `AGE` en el 29 de febrero, ancho excedido en `PUT`, `PRXPOSN`/`PRXPAREN` (`P-PRX-ESTADO`), formato sin rango ni `OTHER`, `INVALUE` y `PICTURE`, y los `P-JAVA-...` de `YRDIF`, `TRANSLATE`, `FIND`, `PRXCHANGE` con conteo distinto de 1 y -1, y `PUT` con `dollar`, `percent` y `best`.
- **Decisiones con alternativa:** los vectores se ejecutan por el intérprete y por el oráculo, y deben coincidir (alternativa descartada: reemplazar el oráculo por el intérprete, que dejaría una sola implementación sin contraste); la ficha por función es una entrada generada y no un YAML por función (los esquemas de `rules/sas/functions/` y del catálogo no admiten la ficha completa); las fechas se guardan como entero de días en los motores y como `Date` en Java con conversión explícita (D1-12).
- **Archivos por encima de 300 líneas:** `interprete.py` (1103), `talend_funciones.py` (416, D1-6 lo parte) y `lower_data.py` (770). D1-2 y D1-6 extraen antes de tocar; D1-9 solo agrega una llamada a `lower_data.py`.
- **Pruebas que se tocan:** `tests/unit/test_catalogo_sas.py` (D1-1: también itera `funciones-guia`; no se debilita) y `tests/corpus/migrar_pendientes.yaml` (D1-16 quita `l4_20`, que la prueba exige quitar). Ninguna se borra ni se relaja.
- **Riesgo de coordinación:** `interprete.py` lo extraen también B y C; D1-2 mueve solo las líneas 108 a 239 y la excepción, y quien llegue segundo rebasea con el golden sin cambios. La numeración de casos `L4` reservada: `l4_21` a `l4_23` (B) y `l4_100` a `l4_199` (este plan).
- **Proporción:** 22 tareas más la compuerta para 65,5 h; los cuerpos de las funciones los decide quien implementa, a partir de la página y del vector.
