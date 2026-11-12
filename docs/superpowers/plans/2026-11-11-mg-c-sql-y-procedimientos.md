# MG-C: PROC SQL y procedimientos Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Que `PROC SQL` (uniones completas, agregados con semántica de faltantes, subconsultas, conjuntos, DDL/DML, `SELECT INTO` y `DICTIONARY`) y los procedimientos de uso común (`SORT`, `MEANS/SUMMARY`, `FREQ`, `TRANSPOSE`, `APPEND`, `DELETE/CONTENTS/DATASETS`, `PRINT/REPORT/TABULATE/ODS`, `FORMAT`) tengan semántica SAS demostrada en el intérprete (anillo B), traducción en `sgm migrar` (anillo A) y validación en Studio (anillo C), cerrando MG-P5 y MG-P6 y la compuerta GM2 (SQL) y GM3 (procedimientos).

**Architecture:** Cambios solo en `sgm-v2` (Python), en cuatro zonas: `src/sgm/frontend/sql*.py` (clasificar sentencias), `src/sgm/ir/` (lowering con los constructores de `operadores.py`), `src/sgm/migrar/` (intérprete de referencia) y `src/sgm/talend_item/` (emisor desde el plan). Cada construcción nueva entra con un caso del corpus (`caso.yaml`, `programa.sas`, `entradas/*.csv`, `esperado/*.csv`) cuyo esperado sale de la página de la guía de SAS, con el patrón de B: intérprete primero (la semántica de faltantes se prueba sin Studio), emisor después, lote de Studio al final. Lo que una página no demuestra queda como `Pendiente:` con su código, no como un valor supuesto.

**Tech Stack:** Python 3.12, pytest, ruff, `sqlglot` (ya usado por `sql_tree.py`); `uv run python -m pytest` y `uv run python -m sgm.cli` (en este Windows `uv run pytest` puede bloquearse por Control de aplicaciones).

**Spec:** `docs/plan-reescritura/plan-migrador-general.md` (MG-P5-02 a MG-P5-08, MG-P6-01 a MG-P6-07, secciones 2, 4, 5.2 y 11b) y `docs/superpowers/plans/2026-11-11-ruta-al-100.md`.

**Horas del plan maestro cubiertas:** MG-P5 restante 43 h (80 h menos 37 h acreditadas) + MG-P6 restante 46 h (50 h menos 4 h acreditadas) = 89 h.

**Series de hitos:** `m` = SQL (carril de Andres, C-1 a C-15); `n` = procedimientos (carril de Byron, C-16 a C-23). La letra va en el título de la entrada de `PROGRESS.md` y en el mensaje del commit. C-Gate lo cierra Andres (`m`) con el lote de Byron ya integrado.

## Global Constraints

- Sin `git push`, sin `--amend`. Un commit local por hito: `hito N <letra>: <resumen>`, terminado con la línea `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Antes de escribir, buscar el último `## Hito` de `PROGRESS.md` (al redactar este plan era el 198) y sumar uno; si otra sesión ya tomó el número, tomar el siguiente. No renumerar entradas publicadas.
- No tocar `tools/ci.py`, `tools/validacion.py`, `tools/instalar_ganchos.py`, `README.md` ni `.githooks/` (son del Plan A y están sin commitear).
- Nada de nombres de scripts de ejemplo (`cod1`, `cod2`, `cars_poc`, `exogena`, `split2`, `split3`, `executeBulkload`, `waitForBulkLoads`, `bulkload_generic`) en `src/` ni `rules/`; lo vigila `tests/unit/test_no_script_specific_names.py`.
- Si el SAS no demuestra un tipo, una columna, un valor o una equivalencia: `Pendiente:` con motivo y código `P-xxx`. Nunca un valor supuesto.
- Si no hay página de la guía SAS, no hay equivalencia. Cada regla nueva cita `<guía>, p. N` con una página que exista en `docs/referencia/sas/<guía>.INDEX.md`. No leer el PDF ni el `.txt` entero: ubicar la sección en el `.INDEX.md` y la página con `grep -n "<!-- página N -->" docs/referencia/sas/<guía>.txt`. Los números de página de este plan son páginas del PDF (las del `.INDEX.md`), no las impresas al pie.
- **Catálogo:** `tests/unit/test_catalogo_sas.py` exige que el literal `(p. N)` de cada `fuente` esté en el `.INDEX.md` de su guía. Si la página exacta de una opción no es una entrada del índice (por ejemplo `NOEQUALS`, p. 2471), el campo `fuente` cita la entrada indexada que la contiene (`proc.pdf, p. 2460`) y la página exacta va en `nota`. Cada tarea que suma una construcción actualiza el YAML de `rules/sas/catalogo/` que corresponde (`sentencias-proc-sql.yaml`, `sql-nulos.yaml` o `procs-usados.yaml`) y su `estado`.
- **Casos del corpus:** los casos de SQL van a `tests/corpus/L2/` (uniones), `tests/corpus/L3/` (agregados, subconsultas, conjuntos, DDL/DML) y `tests/corpus/L5/` (`INTO :macro`); los de procedimientos, a `L3/` (`FREQ`, `MEANS`, `TRANSPOSE`) y `L6/` (`SORT`, con numeración `l6_60` a `l6_79`, reservada a este plan; `l6_01` a `l6_38` son del Plan B). Los casos de capa B de L2 y L3 se escriben a mano porque el oráculo SQLite (`tools/corpus_lib/traduccion_sql.py`) no reproduce la semántica de SAS en nulos de uniones (los nulos casan, `sqlproc`, p. 102); su `caso.yaml` lleva `capa: B`, `estado: revisado` y `razonamiento` con la página. Los de `L6` se generan: la especificación va en `tools/corpus_lib/especificaciones_l6_procs.py` (módulo nuevo; `especificaciones_l6.py` ya tiene 672 líneas) y se registra en `tools/corpus_lib/generar_entradas_l4l6.py` (línea 181, `"L6": ESPECIFICACIONES_L6`).
- No borrar ni debilitar pruebas. Un caso que no se puede traducir queda en `tests/corpus/migrar_pendientes.yaml` con su motivo, no se quita del corpus.
- Archivos de menos de 300 líneas. Ya pasan de 300: `src/sgm/ir/lower_sql_flow.py` (608), `src/sgm/migrar/interprete.py` (1103), `src/sgm/talend_item/desde_plan_map.py` (815) y `src/sgm/migrar/interprete_subconsultas.py` (345). Toda tarea que los toca extrae primero el bloque a un módulo nuevo, en un paso propio y sin cambio de comportamiento (la suite y el golden deben quedar idénticos). El Plan B también extrae de `interprete.py` (MERGE y estado por fila): C-2 mueve solo uniones por llave y agregados, y quien llegue segundo hace rebase sobre el otro.
- Código e identificadores en inglés (los nombres de operadores de `operadores.py` están en español y se conservan); comentarios, docstrings y mensajes en español.
- Después de cada tarea: `uv run python -m pytest -q` y `uv run ruff check src tests tools` en verde. Para iterar se corre solo el archivo de la tarea (`-p no:cacheprovider`); la suite completa se corre al cerrar cada tarea.
- Studio: se usa en tres puntos y nada más: la investigación de nulos en `tMap` (C-4), el lote de `PROC TRANSPOSE` (C-19) y el lote de cierre (C-Gate), con `tools/validar_caso_studio.py <caso>` y `tools/corpus_studio.py lote ...`. Si `sgm studio salud` no conecta, no reinstalar nada ni cambiar `talend-mcp` (ver `docs/guia-validacion-studio.md`, sección 7): la tarea queda con «lote C pendiente» y su motivo, y no se cuenta como pasada.

## Review Focus

- **Los nulos casan en `PROC SQL`:** en un `JOIN`, un nulo se empareja con todos los nulos del mismo tipo (`sqlproc`, p. 102), al revés que en el SQL estándar y que en la comparación `=` de un `WHERE`. El intérprete y el emisor no pueden compartir el supuesto de «nulo no casa». Tests en C-3, C-5 y C-10.
- **Faltantes en agregados:** `AVG`, `SUM`, `MIN`, `MAX` y `COUNT(col)` ignoran faltantes; `COUNT(*)` cuenta filas; los faltantes de una columna de `GROUP BY` forman un solo grupo (`sqlproc`, p. 83 y 88). La suma de un grupo con todos los valores faltantes no está demostrada por ninguna página: queda `Pendiente: P-SUM-TODO-FALTANTE`. Test en C-6.
- **Un Job parcial nunca se emite:** si una construcción (unión, subconsulta, conjunto, `UPDATE`) no se puede demostrar, el paso queda como `unsupported` con código y el caso en `migrar_pendientes.yaml`. Test en C-8, C-9, C-13 y C-19.
- **Efecto sobre datos:** `PROC DELETE`, `DROP`, `DELETE FROM` y `PROC APPEND` cambian tablas persistentes. Sobre `WORK` no hay efecto observable fuera del Job; sobre otra biblioteca sí, y no se traduce sin decisión del usuario (C-20).
- **Ningún pase nuevo puede cambiar la firma de los Jobs ya validados** en L0 a L3 (los `test_golden*.py` y `test_ir_operadores_corpus.py` deben seguir idénticos).

---

## Parte I. MG-P5 restante: PROC SQL (serie `m`, 43 h)

### Task C-1: Línea base medida de SQL y procedimientos (serie `m`)

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\linea_base_sql_procs.py`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_linea_base_sql_procs.py`

**Interfaces:**
- Consumes (de `tools/corpus_lib/caso.py` y `tests/corpus/migrar_pendientes.yaml`): el campo `construcciones` de cada `caso.yaml` y el código de pendiente por caso.
- Produces:
  ```python
  def medir(corpus: Path) -> dict:
      """Por construcción de SQL y de procedimiento: casos que la usan, casos en
      `migrar_pendientes.yaml` con su código, y casos de capa A/B/C. Salida JSON en
      `out/linea_base_sql_procs.json` (no versionada)."""
  ```

- [ ] **Step 1: Write the failing test.** Con un corpus mínimo en `tmp_path` (un `L2` con `construcciones: [PROC SQL, FULL JOIN]` y un `L3` con `[PROC MEANS]`), `medir(tmp_path)` devuelve `{"FULL JOIN": {"casos": 1, "pendientes": {}}, "PROC MEANS": {"casos": 1, "pendientes": {}}}` dentro de la clave `"construcciones"`, y suma `"total_casos": 2`. Un caso listado en un `migrar_pendientes.yaml` mínimo con `P-OPERADOR-SIN-SOPORTE` aparece en `pendientes` de su construcción.
- [ ] **Step 2: Run test to verify it fails.** `uv run python -m pytest tests/unit/test_linea_base_sql_procs.py -q -p no:cacheprovider`; esperado: no existe el módulo.
- [ ] **Step 3: Implement** `medir` leyendo los `caso.yaml` con `corpus_lib.caso` (la carga que ya usa `tests/unit/test_migrar_corpus_anillo_b.py`). Sin dependencias nuevas.
- [ ] **Step 4: Run test to verify it passes**, correr `uv run python tools/linea_base_sql_procs.py tests/corpus` y pegar en `PROGRESS.md` las cifras como línea base de este plan: casos con SQL y con procedimientos, pendientes por código, y cuáles de `PROC SQL` y `PROC` no tienen ningún caso (hoy: `FULL JOIN`, `RIGHT JOIN`, `INTERSECT`, `EXCEPT`, `EXISTS`, `INSERT`, `UPDATE`, `CREATE VIEW`, `DICTIONARY`, `PROC FREQ`, `PROC MEANS`, `PROC TRANSPOSE`, `PROC APPEND`, `PROC COPY`, `PROC CONTENTS`, `PROC PRINT`, `PROC FORMAT`; salvo `PROC DELETE` y `PROC DATASETS`, que solo están en L8).
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N m: linea base medida de SQL y procedimientos` (con la línea `Co-Authored-By`).

---

### Task C-2: Extraer uniones y agregados de los módulos de más de 300 líneas (serie `m`)

Los tres módulos que las tareas siguientes tocan (`lower_sql_flow.py`, `interprete.py`, `desde_plan_map.py`) pasan de 300 líneas. Esta tarea no cambia comportamiento.

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\ir\lower_sql_flow.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\ir\lower_sql_uniones.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\interprete.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\interprete_uniones.py`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_migrar_interprete.py` (sin cambios: debe seguir verde) y `tests\unit\test_golden.py`

**Interfaces:**
- Consumes: `_unir(izquierda: list[dict], derecha: list[dict], params: dict) -> list[dict]` (interprete.py:519), `_clave(valor: object) -> tuple` (interprete.py:363), `_derecha(params: dict) -> str | None` (interprete.py:590), `_cruce_de_existencia(semi, numero, current, chain, tablas, normalized) -> Operator` (lower_sql_flow.py:257), `_branch(spec, chain, normalized) -> Operator` (lower_sql_flow.py:335).
- Produces (mismas firmas, otro módulo): `interprete_uniones.unir(izquierda, derecha, params)` y `interprete_uniones.clave(valor)`; `lower_sql_uniones.cruce_de_existencia(...)` y `lower_sql_uniones.ramas_de_union(...)` con el cuerpo que hoy está en `_branch` para `spec.joins`. `interprete.py` y `lower_sql_flow.py` las importan; ningún nombre público cambia.

- [ ] **Step 1: Medir.** `uv run python -m pytest -q -p no:cacheprovider tests/unit/test_golden.py tests/unit/test_golden_equivalencia.py tests/unit/test_migrar_interprete.py tests/unit/test_migrar_corpus_anillo_b.py`; anotar el conteo de pasadas (la referencia que no debe cambiar).
- [ ] **Step 2: Extraer** `_unir`, `_clave` y `_derecha` a `interprete_uniones.py` (importando `semantica` y `_valor` por parámetro si hay ciclo: pasar `evaluar` como argumento, como ya hace `interprete_agregados.agregar`) y los bloques de uniones y de existencia de `lower_sql_flow.py` a `lower_sql_uniones.py`. Dejar en los módulos de origen solo el `import` y la llamada.
- [ ] **Step 3: Run** la misma tanda del paso 1 más `tests/unit/test_ir_operadores_corpus.py`: mismas pasadas, cero cambios de firma en el golden. `wc -l` de los cuatro archivos: los nuevos, menos de 300; `lower_sql_flow.py` e `interprete.py` bajan (siguen sobre 300: se extrae solo lo que estas tareas necesitan; la deuda restante queda anotada en `PROGRESS.md`).
- [ ] **Step 4: Run** suite completa y `uv run ruff check src tests tools`.
- [ ] **Step 5: Commit.** `hito N m: uniones del intérprete y del lowering SQL en módulos propios, sin cambio de comportamiento`.

---

### Task C-3: `FULL JOIN` y `RIGHT JOIN` en el intérprete, con nulos que casan (MG-P5-02, parte 1; serie `m`)

Hoy `_unir` rechaza `right` y `full` con `NoSoportadoEnInterprete("join", "tipo 'full'")` (`_TIPOS_DE_UNION`). La regla viene de `sqlproc`: `Including Nonmatching Rows with the Right Outer Join` (p. 110), `Selecting All Rows with the Full Outer Join` (p. 111) y `The Effects of Null Values on Joins` (p. 102): **un nulo casa con todos los nulos del mismo tipo**.

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\interprete_uniones.py` (creado en C-2)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\L2\l2_17_full_right_join_llaves_nulas\{caso.yaml, programa.sas, entradas\a.csv, entradas\b.csv, esperado\todo.csv, esperado\derecha.csv}`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_migrar_corpus_anillo_b.py` (el caso se ejecuta solo: la prueba recorre `L2`)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\rules\sas\catalogo\sql-nulos.yaml` (entrada nueva `join-nulos-casan`, `fuente: sqlproc.pdf, p. 102`, `estado: reconocida`; `(p. 102)` es entrada del índice: «The Effects of Null Values on Joins»)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_catalogo_sas.py` (reemplazar `test_los_nulos_de_sql_no_tienen_regla_implementada`, que hoy exige `estado == "no_verificada"` en todas las entradas de `sql-nulos`, por una prueba más estricta: toda entrada `reconocida` de `sql-nulos` debe tener al menos un caso de `tests/corpus/` cuyo `razonamiento` cite su página; las `no_verificada` siguen igual. Se endurece, no se debilita; anotarlo en `PROGRESS.md`, «Decisiones»)
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_interprete_uniones.py`

**Interfaces:**
- Consumes: `unir(op_id, join_type, keys, sources, condition=None, evidence=None) -> Operator` (`ir/operadores.py:196`), `ejecutar_plan(plan, entradas) -> dict[str, list[dict]]`, `semantica.es_faltante(valor: object) -> bool`.
- Produces: `interprete_uniones.unir(izquierda: list[dict], derecha: list[dict], params: dict) -> list[dict]` ahora con `join_type in {"inner","left","right","full"}` (más sus `outer`); las filas sin pareja traen las columnas del otro lado en `None`. El orden de salida es el de la izquierda, y las sin pareja de la derecha al final, en su orden de entrada (el caso no depende del orden: `orden_relevante: false`).

**Caso `L2/l2_17_full_right_join_llaves_nulas` (`capa: B`, `estado: revisado`, razonamiento: «sqlproc, p. 102 y 111»).**
`programa.sas`:
```sas
PROC IMPORT DATAFILE='.../entradas/a.csv' OUT=WORK.A DBMS=CSV REPLACE; GETNAMES=YES; RUN;
PROC IMPORT DATAFILE='.../entradas/b.csv' OUT=WORK.B DBMS=CSV REPLACE; GETNAMES=YES; RUN;
PROC SQL;
  CREATE TABLE WORK.todo AS
  SELECT x.k AS ka, x.va, y.k AS kb, y.vb
  FROM WORK.a x FULL JOIN WORK.b y ON x.k = y.k;
  CREATE TABLE WORK.derecha AS
  SELECT x.k AS ka, x.va, y.k AS kb, y.vb
  FROM WORK.a x RIGHT JOIN WORK.b y ON x.k = y.k;
QUIT;
```
Entradas: `a.csv` = `k,va` / `1,x1` / `2,x2` / `,x3`; `b.csv` = `k,vb` / `2,y2` / `3,y3` / `,y4` / `,y5`.
Esperado a mano. `todo.csv` (5 filas): `ka,va,kb,vb` / `1,x1,,` / `2,x2,2,y2` / `,x3,,y4` / `,x3,,y5` / `,,3,y3` (`k=2` casa; el nulo de `a` casa con los dos nulos de `b`; `1` sin pareja a la derecha; `3` sin pareja a la izquierda). `derecha.csv` (4 filas): `ka,va,kb,vb` / `2,x2,2,y2` / `,x3,,y4` / `,x3,,y5` / `,,3,y3`. Invariantes: `filas(todo) == 5`, `filas(derecha) == 4`.

- [ ] **Step 1: Write the failing tests** en `test_interprete_uniones.py`: `unir([{"k":1,"va":"x1"},{"k":None,"va":"x3"}], [{"k":None,"vb":"y4"},{"k":None,"vb":"y5"},{"k":3,"vb":"y3"}], {"join_type":"full","keys":[["x.k","y.k"]]})` devuelve 5 filas con `[("x3","y4"),("x3","y5")]` entre las que casan; con `"right"` devuelve 3 (las dos que casan y la de `k=3`); con `"semi"` lanza `NoSoportadoEnInterprete`. Agregar el caso del corpus con su `esperado/` y comprobar que `tests/unit/test_migrar_corpus_anillo_b.py` lo recoge.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_interprete_uniones.py tests/unit/test_migrar_corpus_anillo_b.py -q -p no:cacheprovider -k "full or l2_17"`; esperado: `NoSoportadoEnInterprete: join tipo 'full'`.
- [ ] **Step 3: Implement.** En `unir`: construir el índice de la derecha como hoy, y para `right`/`full` llevar el conjunto de filas de la derecha ya emparejadas; al final agregar, para `full` y `right`, las no emparejadas con las columnas de la izquierda en `None` (usar `dict.fromkeys(izquierda[0], None)` solo si hay filas; si la izquierda está vacía, las columnas salen del esquema del plan: pasar `columnas_izquierda` en `params` desde `_ejecutar`). `right` es `full` sin las filas de la izquierda sin pareja. La clave usa `_clave`, que ya trata faltante como igual a faltante: dejar un comentario con `sqlproc.pdf, p. 102`.
- [ ] **Step 4: Run** los tests del paso 2 en verde, luego `tests/unit/test_migrar_interprete.py` y el golden (no deben cambiar). Agregar la entrada del catálogo, reemplazar la prueba de `sql-nulos` como se dijo en `Files` y correr `tests/unit/test_catalogo_sas.py` (el caso `l2_17` cita «p. 102» en su `razonamiento`, que es lo que la prueba nueva busca).
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N m: FULL y RIGHT JOIN en el interprete con nulos que casan`.

---

### Task C-4: `FULL JOIN` y `RIGHT JOIN` emitidos a Talend, y qué hace `tMap` con las llaves nulas (MG-P5-02, parte 2; serie `m`)

Hoy el emisor solo conoce `inner` y `left` (`tMap` con `LOOKUP`). `RIGHT` es un `LEFT` con las entradas intercambiadas. `FULL` es un `LEFT` más las filas de la derecha sin pareja. El hallazgo de Studio de la sección 2 del plan maestro prohíbe `tUnite` (no compila): las dos mitades se unen con escritura secuencial `APPEND`, o con un segundo `tMap` cuya salida de rechazo (`Catch lookup inner join reject`) alimenta al primero. Lo que no se sabe es si `tMap` casa nulo con nulo: SAS sí (p. 102), el SQL estándar no. **Se mide en Studio antes de decidir.**

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\talend_item\desde_plan_map.py` (ya tiene 815 líneas: el bloque de uniones se extrae primero)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\talend_item\desde_plan_uniones.py`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_desde_plan_uniones.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\migrar_pendientes.yaml` (solo si Studio no casa nulos y no hay forma demostrada)

**Interfaces:**
- Consumes: `plan_a_jobs(plan: Plan, esquemas: dict[str, list[Column]], ruta_java: str | None = None) -> ResultadoMigracion` (desde_plan.py:833), `unir(...)` de `operadores.py`.
- Produces:
  ```python
  def nodos_de_union_completa(op: Operator, columnas: dict[str, list[Columna]]) -> list[Nodo | Fila | Tabla]:
      """`right` = `left` con entradas intercambiadas; `full` = `left` mas un segundo `tMap` sobre
      el rechazo del lookup interno, escritos con APPEND. Si una llave puede ser nula y la
      medicion de Studio dice que `tMap` no la casa, devuelve el paso como pendiente
      `P-UNION-LLAVE-NULA` en vez de un Job que difiere de SAS."""
  ```

- [ ] **Step 1: Investigar en Studio (un Job, una vez).** Con `l2_17` (C-3) y `sgm studio salud` conectado: compilar y ejecutar con `uv run python tools/validar_caso_studio.py l2_17_full_right_join_llaves_nulas` el `LEFT JOIN` solo (sin `FULL`) sobre `a.csv`/`b.csv` y anotar en `PROGRESS.md` si el nulo de `a` se empareja con los de `b` (`3 filas con ka vacío` si casa; `1 fila` si no). Si Studio no conecta: «lote C pendiente» y se sigue con el paso 2 suponiendo lo seguro (que **no** casa), que es lo que activa el pendiente `P-UNION-LLAVE-NULA`.
- [ ] **Step 2: Write the failing tests** en `test_desde_plan_uniones.py`: un plan con `unir(join_type="right")` genera un `tMap` cuya entrada principal es la tabla derecha; con `"full"` genera dos `tMap` y dos escrituras con `APPEND`; con una llave nula posible (columna sin `NOT NULL` en el esquema) y la medición «no casa», el resultado trae `P-UNION-LLAVE-NULA` y ningún Job parcial.
- [ ] **Step 3: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_desde_plan_uniones.py -q -p no:cacheprovider`.
- [ ] **Step 4: Implement.** Primero extraer a `desde_plan_uniones.py` el bloque de `desde_plan_map.py` que arma el `tMap` con `LOOKUP` (commit propio, golden idéntico) y después sumar `nodos_de_union_completa`. Registrar la decisión de nulos en `PROGRESS.md` («Decisiones») con la alternativa descartada y qué cambia: si Studio casa nulos, no hace falta tratamiento; si no, o se normaliza la llave con un valor centinela del mismo tipo (cambia los datos del Job y exige que el SAS demuestre que el valor no aparece: no demostrable en general) o queda pendiente. Se elige el pendiente.
- [ ] **Step 5: Run** los tests, el golden y `tests/unit/test_migrar_corpus_aceptacion.py`; si `l2_17` queda pendiente, listarlo en `migrar_pendientes.yaml` con `P-UNION-LLAVE-NULA`. `uv run ruff check src tests tools`. **Commit** `hito N m: FULL y RIGHT JOIN emitidos; llaves nulas medidas en Studio`.

---

### Task C-5: Llaves de varias columnas con blancos y auto-JOIN con alias (MG-P5-02, parte 3; serie `m`)

Cierra MG-P5-02. El filtro de `l2_12` (atribuir columnas calificadas al alias de la misma tabla) lo resuelve B-7; esta tarea cubre lo que B-7 no: llaves compuestas, el texto en blanco como faltante que casa, y un auto-JOIN con condición compuesta.

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\ir\lower_sql_uniones.py` (creado en C-2)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\L2\l2_18_llave_doble_blancos_y_auto_join\{caso.yaml, programa.sas, entradas\p.csv, entradas\q.csv, esperado\izquierda.csv, esperado\pares.csv}`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_lower_sql_uniones.py`

**Interfaces:**
- Consumes: `JoinSpec` (`ir/sql_tree.py`: `source, kind, keys, condition, on, qualified`), `unir(op_id, join_type, keys, sources, condition=None, evidence=None)`.
- Produces: `def llaves_de_union(join: JoinSpec, alias_a_tabla: dict[str, str]) -> tuple[list[tuple[str, str]], str | None]` que devuelve los pares de llaves (todos los `a.c = b.c` unidos por `AND`) y la condición residual (`a.v < b.v`) sin perder ninguna; si el `ON` mezcla `OR` con llaves, devuelve `([], condición)` y el operador queda pendiente `P-UNION-SIN-LLAVES`.

**Caso `L2/l2_18_llave_doble_blancos_y_auto_join` (`capa: B`, `estado: revisado`, razonamiento: «sqlproc, p. 102 (nulos casan, también texto en blanco) y p. 107 (auto-JOIN)»).**
```sas
PROC IMPORT DATAFILE='.../entradas/p.csv' OUT=WORK.P DBMS=CSV REPLACE; GETNAMES=YES; RUN;
PROC IMPORT DATAFILE='.../entradas/q.csv' OUT=WORK.Q DBMS=CSV REPLACE; GETNAMES=YES; RUN;
PROC SQL;
  CREATE TABLE WORK.izquierda AS
  SELECT a.a, a.b, a.v, c.w FROM WORK.p a LEFT JOIN WORK.q c ON a.a = c.a AND a.b = c.b;
  CREATE TABLE WORK.pares AS
  SELECT m.a, m.v AS v1, n.v AS v2 FROM WORK.p m INNER JOIN WORK.p n ON m.a = n.a AND m.v < n.v;
QUIT;
```
Entradas: `p.csv` = `a,b,v` / `A,,1` / `A,x,2` / `B,y,3`; `q.csv` = `a,b,w` / `A,,10` / `A,x,20` / `C,z,30`. (`a` y `b` son texto; el blanco de `b` es faltante.)
Esperado a mano. `izquierda.csv`: `a,b,v,w` / `A,,1,10` / `A,x,2,20` / `B,y,3,` (el blanco casa con el blanco; `B` no tiene pareja). `pares.csv`: `a,v1,v2` / `A,1,2` (solo `A` aparece dos veces; `1 < 2`). Invariantes: `filas(izquierda) == filas(p)`, `filas(pares) == 1`.

- [ ] **Step 1: Write the failing test.** `llaves_de_union` con `ON a.a = c.a AND a.b = c.b` da dos pares y `None`; con `ON m.a = n.a AND m.v < n.v` da un par y `"m.v < n.v"`; con `ON a.a = c.a OR a.b = c.b` da `([], ...)`. Más el caso del corpus (anillo B y anillo A).
- [ ] **Step 2: Run test to verify it fails.** `uv run python -m pytest tests/unit/test_lower_sql_uniones.py tests/unit/test_migrar_corpus_anillo_b.py -q -p no:cacheprovider -k "llaves or l2_18"`.
- [ ] **Step 3: Implement** `llaves_de_union` y usarla desde `_branch`. El texto en blanco ya es faltante en `semantica.es_faltante`; el test del intérprete lo fija con `[{"b": ""}]` frente a `[{"b": None}]`.
- [ ] **Step 4: Run** `tests/unit/test_corpus_esquemas_migrar.py` (el conteo de `P-TIPO-DESCONOCIDO` no sube) y la suite. Actualizar `rules/sas/catalogo/sentencias-proc-sql.yaml` (`from-clause`, `fuente: sqlproc.pdf, p. 96`, nota «llaves compuestas y auto-JOIN: l2_18»).
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N m: llaves compuestas, blancos y auto-JOIN con condicion residual`.

---

### Task C-6: `GROUP BY` y `HAVING` con la semántica de faltantes, en el intérprete y en el emisor (MG-P5-03, parte 1; serie `m`)

Reglas con página: `AVG` promedia solo los valores no faltantes (`sqlproc`, p. 83); los faltantes de la columna de `GROUP BY` forman **un solo grupo** (p. 88); `COUNT(col)` cuenta no faltantes y `COUNT(*)` cuenta filas (p. 82); `HAVING` filtra grupos y no filas (p. 91 y 92). **Sin página:** la suma de un grupo cuyos valores son todos faltantes no la dice ninguna de esas páginas; queda `Pendiente: P-SUM-TODO-FALTANTE` y los casos no la ejercitan.

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\interprete_agregados.py` (201 líneas)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\talend_item\desde_plan_agregado.py` (176 líneas)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\L3\l3_13_group_by_clave_y_valor_faltante\{caso.yaml, programa.sas, entradas\ventas.csv, esperado\por_region.csv}`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\L3\l3_14_having_cuenta_no_faltantes\{caso.yaml, programa.sas, entradas\ventas.csv, esperado\mayores.csv, esperado\incompletos.csv}`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\rules\sas\catalogo\sql-nulos.yaml` (`grouping-with-missing-values`, p. 88, pasa a `reconocida` cuando el intérprete y el emisor coincidan en el caso)
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_interprete_agregados.py`

**Interfaces:**
- Consumes: `agregar(filas, params, *, parsear, evaluar, columna, clave) -> list[dict]` (`interprete_agregados.py:22`), `agregar(op_id, group_by, aggregations, outputs=None, pendiente=None, status="soportado", evidence=None, group_outputs=None, output_order=None) -> Operator` (`operadores.py:249`).
- Produces: sin firma nueva. `interprete_agregados.agregar` devuelve, para `sum/avg/min/max` de un grupo con al menos un valor, el resultado de los no faltantes; para un grupo sin ningún valor, lanza `AgregadoNoSoportado("P-SUM-TODO-FALTANTE")` en `sum` y `avg` (no inventa `0`).

**Caso `L3/l3_13_group_by_clave_y_valor_faltante` (`capa: B`, `estado: revisado`, razonamiento: «sqlproc, p. 82, 83 y 88»).**
```sas
PROC IMPORT DATAFILE='.../entradas/ventas.csv' OUT=WORK.VENTAS DBMS=CSV REPLACE; GETNAMES=YES; RUN;
PROC SQL;
  CREATE TABLE WORK.por_region AS
  SELECT region, COUNT(*) AS n, COUNT(monto) AS n_monto, SUM(monto) AS total,
         AVG(monto) AS prom, MIN(monto) AS minimo, MAX(monto) AS maximo
  FROM WORK.ventas GROUP BY region;
QUIT;
```
`ventas.csv`: `region,monto` / `N,10` / `N,` / `S,5` / `S,7` / `,4` / `,6` (dos filas con región en blanco y una con `monto` faltante).
Esperado a mano, `por_region.csv`: `region,n,n_monto,total,prom,minimo,maximo` / `,2,2,10,5,4,6` / `N,2,1,10,10,10,10` / `S,2,2,12,6,5,7`. (`N`: 2 filas, 1 no faltante, suma 10, promedio de un solo valor = 10; `S`: 5+7=12, promedio 6; región en blanco: un solo grupo, 4+6=10, promedio 5.) Invariante: `suma(por_region.n) == filas(ventas)`.

**Caso `L3/l3_14_having_cuenta_no_faltantes` (`capa: B`, `estado: revisado`, razonamiento: «sqlproc, p. 91 y 92»).** Mismo `ventas.csv`.
```sas
PROC SQL;
  CREATE TABLE WORK.mayores AS
  SELECT region, SUM(monto) AS total FROM WORK.ventas GROUP BY region HAVING SUM(monto) > 10;
  CREATE TABLE WORK.incompletos AS
  SELECT region, COUNT(*) AS n FROM WORK.ventas GROUP BY region HAVING COUNT(monto) < COUNT(*);
QUIT;
```
Esperado: `mayores.csv` = `region,total` / `S,12` (`N` suma 10 y el grupo en blanco suma 10: ninguno es `> 10`); `incompletos.csv` = `region,n` / `N,2` (solo `N` tiene una fila con `monto` faltante).

- [ ] **Step 1: Write the failing tests** en `test_interprete_agregados.py`: la tabla de `l3_13` calculada con `ejecutar_plan` coincide con el esperado; un grupo `[None, None]` en `sum` lanza `AgregadoNoSoportado` con `P-SUM-TODO-FALTANTE`; `COUNT(*)` y `COUNT(monto)` difieren en el grupo `N`. Verificar antes en `docs/referencia/sas/sqlproc.txt` que p. 83 y p. 88 dicen lo citado (`grep -n "<!-- página 88 -->"`).
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_interprete_agregados.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement** en `interprete_agregados.py`: la clave de grupo usa `clave` (faltante igual a faltante, texto en blanco igual a faltante); `COUNT(col)` descarta faltantes; `HAVING` se evalúa sobre las filas del grupo ya agregadas. En el emisor, abrir `docs/referencia/talend/catalogo/taggregaterow.md` y confirmar qué hace `count`, `sum` y `avg` con nulos: donde la página no lo diga, el paso queda `P-AGREGADO-FALTANTES-NO-DEMOSTRADO` y se mide en el lote de C-Gate (no se supone). `tAggregateRow` con dos salidas principales entrega vacío a la segunda (hallazgo de la sección 2 del plan maestro): `l3_14` se emite como dos ramas independientes, nunca con dos salidas de un mismo `tAggregateRow`.
- [ ] **Step 4: Run** los tests, `tests/unit/test_migrar_corpus_anillo_b.py` y el golden (L3 existente no cambia). Actualizar el catálogo y correr `tests/unit/test_catalogo_sas.py`.
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N m: GROUP BY y HAVING con faltantes en el interprete y el emisor`.

---

### Task C-7: Remezcla de estadísticos: agregado sin `GROUP BY` junto a columnas simples (MG-P5-03, parte 2; serie `m`)

`sql-semantica.yaml` tiene la regla `agregado-sin-group-by` con tratamiento `pendiente` (SAS repite el agregado en cada fila; el SQL estándar lo rechaza). La página `sqlproc` p. 79 («Remerging Summary Statistics») **sí demuestra** el resultado: el agregado se calcula sobre todas las filas y se repite en cada fila de la tabla. Es un `agregar` global más una unión cruzada con la tabla base.

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\rules\sas\sql-semantica.yaml` (la regla pasa a `tratamiento: remezcla` si las columnas sin agregar son columnas simples y no hay `ORDER BY` por una columna fuera del `SELECT`; si no, sigue `pendiente`)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\ir\sql_semantics.py` (aceptar el tratamiento `remezcla`; `cargar` rechaza hoy cualquier otro)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\ir\lower_sql_remezcla.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\L3\l3_15_remezcla_maximo_global\{caso.yaml, programa.sas, entradas\ventas.csv, esperado\con_maximo.csv}`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\migrar_pendientes.yaml` (quitar `l3_09_conciliacion_diferencia_plantada` si su pendiente era esta regla; si era otra, dejarlo con su motivo)
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_lower_sql_remezcla.py`

**Interfaces:**
- Consumes: `aggregate_pendiente(params: dict[str, Any]) -> bool` (`ir/sql_semantics.py:70`), `agregar(...)`, `unir(op_id, "cross", [], sources)` (`operadores.py`: `cross` no pide llaves).
- Produces: `def remezclar(spec: SelectSpec, chain: _Chain, normalized: NormalizedSql) -> Operator | None` que devuelve el operador final (agregado global cruzado con la base y proyección de las columnas pedidas) o `None` si la regla sigue pendiente.

**Caso `L3/l3_15_remezcla_maximo_global` (`capa: B`, `estado: revisado`, razonamiento: «sqlproc, p. 79»).**
```sas
PROC IMPORT DATAFILE='.../entradas/ventas.csv' OUT=WORK.VENTAS DBMS=CSV REPLACE; GETNAMES=YES; RUN;
PROC SQL;
  CREATE TABLE WORK.con_maximo AS
  SELECT id, monto, MAX(monto) AS maximo FROM WORK.ventas;
QUIT;
```
`ventas.csv`: `id,monto` / `1,10` / `2,40` / `3,25`. Esperado a mano: `id,monto,maximo` / `1,10,40` / `2,40,40` / `3,25,40` (3 filas; el máximo global se repite). Invariante: `filas(con_maximo) == filas(ventas)`.

- [ ] **Step 1: Write the failing tests.** (a) `remezclar` sobre el árbol de `SELECT id, monto, MAX(monto) AS maximo FROM t` devuelve un operador `join` de tipo `cross` con una rama `aggregate` sin `group_by`; (b) con `ORDER BY` por una columna que no está en el `SELECT` devuelve `None` (p. 79 lista esa condición como remezcla pero no el orden de filas: queda pendiente); (c) el caso se ejecuta en el intérprete y coincide con el esperado. Leer la página en `sqlproc.txt` y citar `p. 79` en el docstring.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_lower_sql_remezcla.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement** `remezclar` y engancharla en `_branch` (antes de la rama que hoy emite `P-AGREGADO-SIN-TRADUCIR`). El agregado se calcula con el `WHERE` del `SELECT` aplicado antes (p. 79: el `WHERE` solo puede usar columnas del `SELECT`).
- [ ] **Step 4: Run** los tests, el que vigile `migrar_pendientes.yaml` (`grep -rn migrar_pendientes tests`) y el golden. Si el emisor no sabe la unión cruzada, el paso queda `P-UNION-CRUZADA-SIN-EMISOR` y el caso en `migrar_pendientes.yaml`.
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N m: remezcla de estadisticos sin GROUP BY`.

---

### Task C-8: Subconsulta escalar y subconsulta en `FROM` (MG-P5-04, parte 1; serie `m`)

`SelectSpec.subqueries: bool` marca hoy cualquier subconsulta que no sea `IN`/`NOT IN` simple y el paso queda sin traducir. Páginas: «Single-Value Subqueries» (`sqlproc`, p. 122), «Specifying In-Line Views» (p. 167), «Using a WHERE Clause with Missing Values» (p. 73: el faltante numérico es menor que cualquier número; verificar en el `.txt` antes de citar).

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\ir\sql_tree.py` (campo `sub` en `Source`; lista `scalars` en `SelectSpec`)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\ir\lower_sql_subconsultas.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\interprete_escalares.py` (`interprete_subconsultas.py` ya tiene 345 líneas: no se le suma)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\L3\l3_16_subconsulta_escalar\{caso.yaml, programa.sas, entradas\ventas.csv, esperado\mayores.csv, esperado\menores.csv}`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\L3\l3_17_subconsulta_en_from\{caso.yaml, programa.sas, entradas\pedidos.csv, esperado\grandes.csv}`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_subconsultas_sql.py`

**Interfaces:**
- Consumes: `Source(name: str, alias: str | None = None)`, `SelectSpec`, `SemiSpec` (`sql_tree.py`), `SubconsultaNoSoportada` (`interprete_subconsultas.py:21`), `agregar(...)`, `unir(...)`.
- Produces:
  ```python
  @dataclass
  class ScalarSpec:
      sub: SelectSpec        # SELECT con un solo item agregado y sin GROUP BY
      column: str            # nombre con el que el valor entra al filtro
      expression: str        # texto original, para validar sus límites en el anillo B
  def lower_scalar(spec: SelectSpec, scalar: ScalarSpec, chain, normalized) -> Operator: ...
  def lower_inline_view(source: Source, chain, normalized) -> Operator: ...
  ```
  La escalar es un `agregar` global cruzado con la tabla de afuera y filtrado después (misma forma que C-7); la vista en línea es una cadena de operadores cuyo resultado se nombra con el alias y se lee como una tabla más.

**Caso `L3/l3_16_subconsulta_escalar` (`capa: B`, `estado: revisado`, razonamiento: «sqlproc, p. 122 y p. 73»).**
```sas
PROC SQL;
  CREATE TABLE WORK.mayores AS SELECT id, monto FROM WORK.ventas WHERE monto > (SELECT AVG(monto) FROM WORK.ventas);
  CREATE TABLE WORK.menores AS SELECT id, monto FROM WORK.ventas WHERE monto < (SELECT AVG(monto) FROM WORK.ventas);
QUIT;
```
(precedido del `PROC IMPORT ... OUT=WORK.VENTAS` como en C-6). `ventas.csv`: `id,monto` / `1,10` / `2,40` / `3,25` / `4,`. `AVG(monto) = (10+40+25)/3 = 25` (el faltante no cuenta, p. 83). Esperado a mano: `mayores.csv` = `id,monto` / `2,40` (la fila 3 vale 25 y `25 > 25` es falso; la fila 4 es faltante, que no es mayor que 25); `menores.csv` = `id,monto` / `1,10` / `4,` (el faltante es menor que cualquier número, p. 73).

**Caso `L3/l3_17_subconsulta_en_from` (`capa: B`, `estado: revisado`, razonamiento: «sqlproc, p. 167»).**
```sas
PROC SQL;
  CREATE TABLE WORK.grandes AS
  SELECT t.id, t.total
  FROM (SELECT id, SUM(monto) AS total FROM WORK.pedidos GROUP BY id) AS t
  WHERE t.total > 20;
QUIT;
```
`pedidos.csv`: `id,monto` / `1,10` / `1,15` / `2,5` / `2,` / `3,30`. Totales: `1 -> 25`, `2 -> 5` (el faltante no cuenta), `3 -> 30`. Esperado: `id,total` / `1,25` / `3,30`.

- [ ] **Step 1: Write the failing tests.** (a) el árbol de `l3_16` trae `scalars` con un item `AVG`; (b) el árbol de `l3_17` trae `Source.sub`; (c) ambos casos coinciden con su esperado en `ejecutar_plan`; (d) una escalar con dos columnas, o que puede devolver más de una fila (sin agregado), queda `unsupported` con `P-SUBCONSULTA-ESCALAR-NO-DEMOSTRADA` (SAS toma la primera fila y avisa; ninguna página fija cuál: `Pendiente:`).
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_subconsultas_sql.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement** `_select` en `sql_tree.py` (rellenar `scalars` y `Source.sub`, sin tocar `semis`), el lowering y `interprete_escalares.py`; enganchar en `_branch` y en `_ejecutar`. Un `WHERE` con la escalar usa la comparación de `semantica` (faltante menor que todo).
- [ ] **Step 4: Run** los tests, `tests/unit/test_migrar_corpus_anillo_b.py`, `tests/unit/test_corpus_l4l6.py` y el golden. Actualizar `sentencias-proc-sql.yaml` (`select-statement`, p. 323) y correr `tests/unit/test_catalogo_sas.py`.
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N m: subconsulta escalar y vista en linea`.

---

### Task C-9: `EXISTS`, `NOT EXISTS` y subconsulta correlacionada (MG-P5-04, parte 2; serie `m`)

Páginas: «Correlated Subqueries» (`sqlproc`, p. 124) y «EXISTS Operator» (p. 393). `EXISTS` no multiplica filas (a diferencia del `JOIN`): es el mismo cruce de existencia que ya usa `IN` (`_cruce_de_existencia`).

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\ir\sql_tree.py` (`SemiSpec.exists: bool`; `_semi` reconoce `EXISTS (SELECT ... WHERE b.x = a.y)`)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\ir\lower_sql_subconsultas.py` (creado en C-8)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\L3\l3_18_exists_y_not_exists\{caso.yaml, programa.sas, entradas\clientes.csv, entradas\ventas.csv, esperado\con_ventas.csv, esperado\sin_ventas.csv}`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\L3\l3_19_correlacionada_maximo_por_grupo\{caso.yaml, programa.sas, entradas\ventas.csv, esperado\maximas.csv}`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_exists_sql.py`

**Interfaces:**
- Consumes: `SemiSpec(column, negate, sub, key, expression)`, `_cruce_de_existencia(semi, numero, current, chain, tablas, normalized) -> Operator`.
- Produces: `def semi_de_exists(node: exp.Exists, outer_aliases: set[str]) -> SemiSpec | None` (devuelve `None` si la correlación no es una igualdad de columnas o hay más de una condición; ese paso queda `P-SUBCONSULTA-CORRELACION-NO-IGUALDAD`) y `def lower_escalar_correlacionada(spec, scalar, chain, normalized) -> Operator` (agregar por la columna de correlación y unir por ella).

**Caso `L3/l3_18_exists_y_not_exists` (`capa: B`, `estado: revisado`, razonamiento: «sqlproc, p. 393»).**
```sas
PROC SQL;
  CREATE TABLE WORK.con_ventas AS SELECT c.id, c.nombre FROM WORK.clientes c
    WHERE EXISTS (SELECT 1 FROM WORK.ventas v WHERE v.id_cliente = c.id);
  CREATE TABLE WORK.sin_ventas AS SELECT c.id, c.nombre FROM WORK.clientes c
    WHERE NOT EXISTS (SELECT 1 FROM WORK.ventas v WHERE v.id_cliente = c.id);
QUIT;
```
`clientes.csv`: `id,nombre` / `1,Ana` / `2,Beto` / `3,Cora`. `ventas.csv`: `id_cliente,monto` / `1,5` / `1,7` / `3,9`. Esperado: `con_ventas.csv` = `id,nombre` / `1,Ana` / `3,Cora` (Ana tiene dos ventas y sale **una** vez); `sin_ventas.csv` = `id,nombre` / `2,Beto`.

**Caso `L3/l3_19_correlacionada_maximo_por_grupo` (`capa: B`, `estado: revisado`, razonamiento: «sqlproc, p. 124»).**
```sas
PROC SQL;
  CREATE TABLE WORK.maximas AS SELECT v.id_cliente, v.monto FROM WORK.ventas v
    WHERE v.monto = (SELECT MAX(w.monto) FROM WORK.ventas w WHERE w.id_cliente = v.id_cliente);
QUIT;
```
`ventas.csv`: `id_cliente,monto` / `1,5` / `1,7` / `2,3` / `2,3`. Máximos por cliente: `1 -> 7`, `2 -> 3`. Esperado: `id_cliente,monto` / `1,7` / `2,3` / `2,3` (las dos filas empatadas pasan). El caso no incluye faltantes: la comparación `faltante = faltante` dentro de una correlacionada no tiene página; `Pendiente: P-CORRELACIONADA-FALTANTE`.

- [ ] **Step 1: Write the failing tests.** (a) `semi_de_exists` sobre `EXISTS (SELECT 1 FROM v WHERE v.id_cliente = c.id)` da `column="c.id"`, `key="id_cliente"`, `negate=False`; con `NOT EXISTS`, `negate=True`; con `v.monto > c.id` da `None`; (b) los dos casos coinciden en el anillo B.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_exists_sql.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement** el reconocimiento en `sql_tree.py` y el lowering reutilizando `_cruce_de_existencia` (la subconsulta se proyecta a la columna de correlación y se deduplica: `EXISTS` es existencia, no conteo).
- [ ] **Step 4: Run** los tests, `tests/unit/test_migrar_corpus_anillo_b.py`, el golden y `tests/unit/test_mg_p13_sql_emitter_security.py`. Catálogo: entrada de `EXISTS Operator` (p. 393, `(p. 393)` está en el índice).
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N m: EXISTS, NOT EXISTS y escalar correlacionada`.

---

### Task C-10: `UNION`, `INTERSECT` y `EXCEPT` (MG-P5-05, parte 1; serie `m`)

Páginas: «Working with Two or More Query Results» (`sqlproc`, p. 129; las columnas se emparejan por **posición**), `UNION` (p. 131), `EXCEPT` (p. 133), `INTERSECT` (p. 134). Sin página que lo demuestre: `INTERSECT ALL` y `EXCEPT ALL` (p. 133 y 134 los nombran, pero el resultado está en una imagen del PDF, no en el texto: `Pendiente: P-CONJUNTO-ALL-NO-DEMOSTRADO`) y el tratamiento de faltantes en la comparación de filas (`Pendiente: P-CONJUNTO-FALTANTES`): los casos no los ejercitan.

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\ir\sql_tree.py` (`SqlTree.set_op: str = "union"`, con `"intersect"` y `"except"`; `_branches` hoy solo reconoce `exp.Union`)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\ir\lower_sql_conjuntos.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\interprete_uniones.py` (operación de conjuntos sobre filas completas)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\L3\l3_20_union_interseccion_diferencia\{caso.yaml, programa.sas, entradas\a.csv, entradas\b.csv, esperado\union.csv, esperado\interseccion.csv, esperado\diferencia.csv}`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_conjuntos_sql.py`

**Interfaces:**
- Consumes: `concatenar(op_id, sources, evidence=None) -> Operator`, `deduplicar(op_id, by, keep="first", outputs=None, evidence=None) -> Operator`, `unir(...)`, `SqlTree(target, selects, union_all, identifiers_portable)`.
- Produces: `def lower_conjunto(tree: SqlTree, chain, normalized) -> Operator`: `UNION` = `concatenar` + `deduplicar` por todas las columnas; `INTERSECT` = unión interna por todas las columnas + `deduplicar`; `EXCEPT` = unión izquierda por todas las columnas, quedarse con las sin pareja + `deduplicar`. Ramas con distinto número de columnas: `P-CONJUNTO-COLUMNAS-DISTINTAS`. `tUnite` no compila (sección 2 del plan maestro): el emisor usa la forma secuencial `APPEND` que ya usa `UNION ALL`.

**Caso `L3/l3_20_union_interseccion_diferencia` (`capa: B`, `estado: revisado`, razonamiento: «sqlproc, p. 131, 133 y 134»).**
```sas
PROC SQL;
  CREATE TABLE WORK.union AS SELECT n, t FROM WORK.a UNION SELECT n, t FROM WORK.b;
  CREATE TABLE WORK.interseccion AS SELECT n, t FROM WORK.a INTERSECT SELECT n, t FROM WORK.b;
  CREATE TABLE WORK.diferencia AS SELECT n, t FROM WORK.a EXCEPT SELECT n, t FROM WORK.b;
QUIT;
```
`a.csv`: `n,t` / `1,uno` / `2,dos` / `2,dos` / `3,tres`. `b.csv`: `n,t` / `1,uno` / `2,dos` / `4,cuatro`. Esperado a mano: `union.csv` = `n,t` / `1,uno` / `2,dos` / `3,tres` / `4,cuatro` (4 filas, sin repetidas); `interseccion.csv` = `n,t` / `1,uno` / `2,dos` (en las dos, una vez cada una); `diferencia.csv` = `n,t` / `3,tres` (solo en `a`; `2,dos` está en `b`, así que no sale aunque `a` la repita). Invariantes: `filas(union) == 4`, `filas(interseccion) + filas(diferencia) == 3`.

- [ ] **Step 1: Write the failing tests.** El árbol de cada sentencia trae `set_op` correcto; `INTERSECT ALL` da `P-CONJUNTO-ALL-NO-DEMOSTRADO`; el caso coincide en el anillo B. Verificar en el `.txt` (`grep -n "<!-- página 134 -->"`) que `INTERSECT` y `EXCEPT` están descritos como se cita.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_conjuntos_sql.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement** `_branches` con `exp.Intersect` y `exp.Except` (comprobar en la versión instalada de `sqlglot` si heredan de `exp.Union`: `uv run python -c "import sqlglot.expressions as e; print(e.Except.__mro__)"`), el lowering y la operación del intérprete.
- [ ] **Step 4: Run** los tests, `tests/unit/test_migrar_corpus_anillo_b.py` y el golden; los casos de `UNION ALL` existentes no cambian.
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N m: UNION, INTERSECT y EXCEPT con su semantica`.

---

### Task C-11: `OUTER UNION` y `OUTER UNION CORR` (MG-P5-05, parte 2; serie `m`)

Página: «Concatenating Query Results (OUTER UNION)» (`sqlproc`, p. 135): `OUTER UNION` concatena las dos consultas **sin** superponer columnas; con `CORRESPONDING` (`CORR`) las columnas del mismo nombre se superponen. Hoy `lower_sql._lower_query` marca cualquier `OUTER UNION` como `SEMANTICA_DUDOSA` («requiere decisión del usuario»): con la página, `CORR` deja de ser dudoso. Los programas L8 (`02_inconsistencias_correccion`, `05_conciliacion`, `08_cadena_completa_macros`, `validaciones/v01_tipo_doc`) usan `OUTER UNION CORR`: esta tarea los puede mover de pendiente a traducido.

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\ir\lower_sql.py` (`_OUTER_UNION` en la línea 22 y su uso en la línea 90)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\ir\lower_sql_conjuntos.py` (creado en C-10)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\L3\l3_21_outer_union_corr\{caso.yaml, programa.sas, entradas\a.csv, entradas\b.csv, esperado\apilada.csv}`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_outer_union.py`

**Interfaces:**
- Consumes: `concatenar(op_id, sources, evidence=None)`, `calcular(op_id, assignments, outputs=None, modo=None, declared=None, evidence=None)`.
- Produces: `def lower_outer_union(ramas: list[SelectSpec], corr: bool, chain, normalized) -> Operator`: con `corr`, el conjunto de columnas es la unión de los nombres en orden de aparición y cada rama aporta `None` donde no tiene la columna; sin `corr` y con nombres repetidos entre ramas, el paso queda `P-OUTER-UNION-COLUMNAS-REPETIDAS` (la página no dice qué nombres lleva la tabla creada; no se supone).

**Caso `L3/l3_21_outer_union_corr` (`capa: B`, `estado: revisado`, razonamiento: «sqlproc, p. 135»).**
```sas
PROC SQL;
  CREATE TABLE WORK.apilada AS
  SELECT id, x FROM WORK.a OUTER UNION CORR SELECT id, y FROM WORK.b;
QUIT;
```
`a.csv`: `id,x` / `1,10` / `2,20`. `b.csv`: `id,y` / `3,30`. Esperado a mano: `id,x,y` / `1,10,` / `2,20,` / `3,,30` (`id` se superpone; `x` solo existe en `a` y `y` solo en `b`, y quedan faltantes en la otra mitad). Invariante: `filas(apilada) == filas(a) + filas(b)`.

- [ ] **Step 1: Write the failing tests.** `lower_outer_union` con `corr=True` da columnas `["id","x","y"]`; con `corr=False` e `id` repetido da `P-OUTER-UNION-COLUMNAS-REPETIDAS`; el caso coincide en el anillo B. Correr `uv run python tools/linea_base_sql_procs.py tests/corpus` antes y después: los casos de L8 con `OUTER UNION CORR` deben mejorar o quedar igual, nunca empeorar.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_outer_union.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement.** Quitar el bloque `SEMANTICA_DUDOSA` solo para `OUTER UNION CORR`; el sin `CORR` mantiene su motivo con la página citada en la nota.
- [ ] **Step 4: Run** los tests, `tests/unit/test_corpus_totales.py`, `tests/unit/test_corpus_validaciones.py` y el golden.
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N m: OUTER UNION CORR con la pagina que lo demuestra`.

---

### Task C-12: `CREATE VIEW`, `CREATE TABLE ... LIKE` y `DROP` (MG-P5-06, parte 1; serie `m`)

Hoy `frontend/sql.py` clasifica `create_table`, `create_like`, `insert`, `delete` y `drop_table`, y el lowering deja `create_like`, `insert`, `delete` y `drop_table` como `unsupported` (`SQL_NO_SOPORTADO`). No hay tipo para `CREATE VIEW`, `UPDATE` ni `ALTER`. Páginas: «Creating Tables like an Existing Table» (`sqlproc`, p. 144: tabla vacía con las columnas de la otra), `CREATE VIEW Statement` (p. 296: la vista es una consulta guardada que se ejecuta al usarla) y `DROP Statement` (p. 302). **Decisión (se anota en `PROGRESS.md`, «Decisiones»):** una vista no es una tabla en un Job de Talend; cada lectura de la vista se expande en línea a su cadena de operadores (la misma que una vista en línea de C-8). Alternativa descartada: materializarla como tabla al crearla; cambia el momento en que se evalúa (SAS la evalúa al leerla, con los datos de ese momento) y por tanto los resultados si la tabla de origen cambia entre medias.

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\frontend\sql.py` (86 líneas: nuevos `kind`: `create_view`, `update`, `alter`; el regex de `create_like` ya existe)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\ir\lower_sql.py` (`_lower_statement`: las ramas de `create_like`, `create_view` y `drop_table`)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\ir\lower_sql_ddl.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\L3\l3_22_vista_molde_y_drop\{caso.yaml, programa.sas, entradas\ventas.csv, esperado\copia.csv, esperado\molde.csv}`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\rules\sas\catalogo\sentencias-proc-sql.yaml` (`create-view-statement` y `drop-statement` pasan a `reconocida`; `fuente` `sqlproc.pdf, p. 296` y `p. 302`)
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_sql_ddl.py`

**Interfaces:**
- Consumes: `SqlStatement(kind, text, line, target=None, engine=None, sources=(), inner_sql=None, fields=...)` y `parse_sql_statement(text: str, line: int) -> SqlStatement` (`frontend/sql.py:28,40`), `lower_query(tree, normalized, ev, b)`, `leer(op_id, dataset, in_flag=None, incluir_bandera=False, evidence=None)`, `filtrar(...)`.
- Produces:
  ```python
  def lower_create_like(st: SqlStatement, ev: Evidence, b: Builder, columnas: list[str]) -> None:
      """Tabla vacía con `columnas` (sqlproc, p. 144). Si las columnas de la tabla modelo no se
      conocen en el plan, queda `P-LIKE-SIN-ESQUEMA`."""
  def lower_create_view(st: SqlStatement, ev: Evidence, b: Builder) -> None:
      """Registra la consulta bajo el nombre de la vista; cada lectura la expande en línea."""
  def lower_drop(st: SqlStatement, ev: Evidence, b: Builder) -> None:
      """Sobre una tabla de WORK es un aviso `A-DROP-WORK-OMITIDO` (C-20 fija la política común);
      sobre otra biblioteca, `P-DROP-PERSISTENTE`."""
  ```

**Caso `L3/l3_22_vista_molde_y_drop` (`capa: B`, `estado: revisado`, razonamiento: «sqlproc, p. 144, 296 y 302»).**
```sas
PROC IMPORT DATAFILE='.../entradas/ventas.csv' OUT=WORK.VENTAS DBMS=CSV REPLACE; GETNAMES=YES; RUN;
PROC SQL;
  CREATE VIEW WORK.v_altas AS SELECT id, monto FROM WORK.ventas WHERE monto > 20;
  CREATE TABLE WORK.copia AS SELECT id, monto FROM WORK.v_altas;
  DROP VIEW WORK.v_altas;
  CREATE TABLE WORK.molde LIKE WORK.ventas;
QUIT;
```
`ventas.csv`: `id,monto` / `1,10` / `2,40` / `3,25`. Esperado a mano: `copia.csv` = `id,monto` / `2,40` / `3,25`; `molde.csv` = solo la cabecera `id,monto` (cero filas). Invariantes: `filas(copia) == 2`, `filas(molde) == 0`.

- [ ] **Step 1: Write the failing tests.** `parse_sql_statement("create view work.v as select 1 as x from work.t", 1).kind == "create_view"`; un `UPDATE` y un `ALTER TABLE` dan `update` y `alter` (en vez de `other`); `lower_create_like` con columnas `["id","monto"]` produce un operador `read` de cero filas con esas columnas; `lower_drop` sobre `WORK.x` emite el aviso y sobre `LZ.x` el pendiente; el caso coincide en el anillo B.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_sql_ddl.py -q -p no:cacheprovider`; esperado: `kind == "other"`.
- [ ] **Step 3: Implement** los tipos nuevos en `frontend/sql.py` y `lower_sql_ddl.py`. `tests/unit/test_catalogo_sas.py::test_sentencias_proc_sql_reconocidas` exige que lo que el catálogo marca `reconocida` lo clasifique el parser: actualizar el catálogo en el mismo commit.
- [ ] **Step 4: Run** los tests, `tests/unit/test_catalogo_sas.py`, `tests/unit/test_migrar_corpus_anillo_b.py`, el golden y `tests/unit/test_corpus_totales.py` (los programas L8 usan `DROP TABLE`: no deben empeorar).
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N m: CREATE VIEW, CREATE TABLE LIKE y DROP en PROC SQL`.

---

### Task C-13: `INSERT`, `UPDATE`, `DELETE FROM` y `ALTER TABLE` sobre tablas versionadas (MG-P5-06, parte 2; serie `m`)

Páginas: `INSERT` con `SET`, `VALUES` y consulta (`sqlproc`, p. 145 a 149); «Updating Data Values in a Table» (p. 150 a 152); «Deleting Rows» (p. 153); «Altering Columns» (p. 154 a 158); `INSERT Statement` (p. 309), `UPDATE Statement` (p. 323), `DELETE Statement` (p. 299). Un Job de Talend no modifica una tabla en el sitio: cada sentencia produce una **versión nueva** de la tabla (el intérprete ya versiona dependencias con `_agregar_dependencias_versionadas`, `interprete_subconsultas.py:178`). `INSERT` = `concatenar(versión anterior, filas nuevas)`; `UPDATE ... WHERE` = `calcular` con `CASE` sobre la condición; `DELETE FROM ... WHERE` = `filtrar` por la negación de la condición **con la lógica de faltantes de SAS** (una fila con la condición desconocida no se borra solo si la condición es falsa: se usa la misma comparación que `WHERE`); `ALTER TABLE ... ADD col tipo` = `calcular` con la columna en faltante (p. 154). `UPDATE` con subconsulta, `ALTER ... MODIFY` y `ALTER ... DROP COLUMN` quedan `Pendiente: P-UPDATE-SUBCONSULTA` y `P-ALTER-MODIFICA-DROP`; sobre una biblioteca que no es `WORK`, `Pendiente: P-DML-PERSISTENTE` (decisión de C-20).

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\ir\lower_sql_dml.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\ir\lower_sql.py` (ramas `insert`, `delete`, `update`, `alter`)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\L3\l3_23_insert_update_delete_alter\{caso.yaml, programa.sas, esperado\t.csv}` (sin `entradas\`: la tabla nace de `CREATE TABLE` con columnas, `sqlproc` p. 140)
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_sql_dml.py`

**Interfaces:**
- Consumes: `concatenar(op_id, sources, evidence=None)`, `calcular(op_id, assignments, outputs=None, modo=None, declared=None, evidence=None)`, `filtrar(...)` (`operadores.py:132`), `SqlStatement`.
- Produces:
  ```python
  def lower_insert(st: SqlStatement, ev: Evidence, b: Builder, version: int) -> str: ...
  def lower_update(st: SqlStatement, ev: Evidence, b: Builder, version: int) -> str: ...
  def lower_delete(st: SqlStatement, ev: Evidence, b: Builder, version: int) -> str: ...
  def lower_alter_add(st: SqlStatement, ev: Evidence, b: Builder, version: int) -> str: ...
  ```
  Cada una devuelve el nombre de la versión nueva (`WORK.t#2`, `WORK.t#3`...) y deja el último como la tabla visible para las lecturas siguientes.

**Caso `L3/l3_23_insert_update_delete_alter` (`capa: B`, `estado: revisado`, razonamiento: «sqlproc, p. 140, 145 a 146, 150, 153 y 154»).**
```sas
PROC SQL;
  CREATE TABLE WORK.t (id NUM, estado CHAR(8));
  INSERT INTO WORK.t VALUES (1,'ACTIVO') VALUES (2,'ACTIVO') VALUES (3,'INACTIVO');
  UPDATE WORK.t SET estado = 'BAJA' WHERE id = 3;
  DELETE FROM WORK.t WHERE id = 1;
  ALTER TABLE WORK.t ADD nota CHAR(5);
QUIT;
```
Esperado a mano, `t.csv`: `id,estado,nota` / `2,ACTIVO,` / `3,BAJA,` (tras el `INSERT` hay 3 filas; el `UPDATE` pasa la 3 a `BAJA`; el `DELETE` quita la 1; `ALTER` agrega `nota` en blanco). Invariante: `filas(t) == 2`.

- [ ] **Step 1: Write the failing tests.** Verificar antes en el `.txt` que p. 146 admite varias cláusulas `VALUES` en un `INSERT` (`grep -n "<!-- página 146 -->"`); si no, el caso usa tres `INSERT` y el pendiente de varias `VALUES` queda anotado. Tests: cada `lower_*` devuelve la versión siguiente; `UPDATE` con subconsulta devuelve `P-UPDATE-SUBCONSULTA` y no emite nada; el caso coincide en el anillo B (hoy: `unsupported`).
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_sql_dml.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement.** El valor literal de `VALUES` entra con el tipo de la columna declarada en `CREATE TABLE (id NUM, ...)`; un literal que no concuerde con el tipo queda `P-INSERT-TIPO-NO-DEMOSTRADO` (SAS convierte según p. 75 de `lrcon`; no se reimplementa aquí).
- [ ] **Step 4: Run** los tests, `tests/unit/test_migrar_corpus_anillo_b.py` y el golden. Catálogo: `insert-statement` (p. 309), `update-statement` (p. 323), `delete-statement` (p. 299) y `alter-table-statement` (p. 282) a `reconocida` solo en lo que el caso demuestra, con la nota de lo pendiente.
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N m: INSERT, UPDATE, DELETE y ALTER ADD sobre versiones de tabla`.

---

### Task C-14: `SELECT INTO :macro` y `DICTIONARY.*` (MG-P5-07; serie `m`; contrato con el Plan E, MG-P7-04)

`lower_sql_flow._host_assignments` ya emite `set_variable` por cada variable de `INTO` (regla `select-into-macrovariable`, tratamiento `programa_anfitrion`); `l5_09_into_primer_fila` sigue en `migrar_pendientes.yaml` con `P-ESQUEMA-NO-PORTABLE`: **leer el motivo exacto primero** (`pendientes.md` del caso). Páginas: «Creating Macro Variables from the First Row of a Query Result» y «Creating a Macro Variable from the Result of an Aggregate Function» (`sqlproc`, p. 198 y 199), `INTO Clause` (p. 312) y `DICTIONARY Tables` (p. 187 a 195). Reglas demostradas por el texto de p. 198: con varias filas la variable toma **la primera**; **sin filas la variable no se modifica y, si no existía, no se crea**; `SQLOBS` cuenta las filas de la consulta; la referencia vale solo en la consulta externa, no en una subconsulta ni en un `CREATE`. De p. 192: los valores de carácter de `DICTIONARY` están en **mayúsculas**, y las tablas son de solo lectura (`INSERT` o `ALTER` sobre ellas es un error). De p. 194: `DICTIONARY.COLUMNS` tiene `libname`, `memname` y `name`.

**Contrato con el Plan E (MG-P7-04, variables de macro de ejecución):** esta tarea entrega el operador `set_variable` con `params = {"name": str, "expression": str, "si_sin_filas": "conservar"}`; el Plan E decide cómo llega ese valor al contexto del Job (no al código, igual que `CALL SYMPUT` en B-20). Esta tarea no escribe en `contexts/` ni toca el expansor de macros (`tools/corpus_lib/expansor_macros.py`, `src/sgm/frontend/`): si el valor se necesita para expandir el SAS antes de analizarlo, queda `P-MACRO-DE-EJECUCION` y lo resuelve el Plan E.

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\ir\lower_sql_flow.py` (`_host_assignments`, línea 536; el parámetro `si_sin_filas`)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\ir\lower_sql_diccionario.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\L5\l5_13_into_agregado_y_sin_filas\{caso.yaml, programa.sas, entradas\ventas.csv, esperado\sobre_maximo.csv, esperado\sin_cambio.csv}`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\L5\l5_14_dictionary_columns_cuenta\{caso.yaml, programa.sas, entradas\ventas.csv, esperado\con_ncol.csv}`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\rules\sas\catalogo\sentencias-proc-sql.yaml` (`into-clause`, p. 312)
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_select_into_y_diccionario.py`

**Interfaces:**
- Consumes: `_host_assignments(...)` (`lower_sql_flow.py:536`), `sql_semantics.tratamiento(rid: str) -> str`, el esquema local de `WORK.<tabla>` que sale de la cabecera del CSV del `PROC IMPORT` (`src/sgm/migrar/esquemas.py`).
- Produces: `def resolver_diccionario(consulta: SelectSpec, esquemas: dict[str, list[str]]) -> list[dict] | None`: resuelve **en tiempo de migración** `DICTIONARY.COLUMNS` (y `DICTIONARY.TABLES` para `memname`/`nobs`) desde el inventario de esquemas locales, con `libname` y `memname` en mayúsculas (p. 192); devuelve `None` si falta el esquema de esa tabla (`P-DICTIONARY-SIN-ESQUEMA`). Una consulta a `DICTIONARY.*` sobre una biblioteca que no es `WORK` ni está en `env/schemas.json` queda `P-DICTIONARY-BIBLIOTECA-DESCONOCIDA`. `sas_only`: nunca se emite contra una base.

**Caso `L5/l5_13_into_agregado_y_sin_filas` (`capa: B`, `estado: revisado`, razonamiento: «sqlproc, p. 198 y 199»).**
```sas
PROC IMPORT DATAFILE='.../entradas/ventas.csv' OUT=WORK.VENTAS DBMS=CSV REPLACE; GETNAMES=YES; RUN;
%LET x = 0;
PROC SQL NOPRINT;
  SELECT MAX(monto), COUNT(*) INTO :maximo, :filas FROM WORK.ventas;
  SELECT monto INTO :x FROM WORK.ventas WHERE monto > 100;
  CREATE TABLE WORK.sobre_maximo AS
    SELECT id, monto, &maximo AS maximo, &filas AS filas FROM WORK.ventas WHERE monto = &maximo;
  CREATE TABLE WORK.sin_cambio AS SELECT &x AS x FROM WORK.ventas WHERE id = 1;
QUIT;
```
`ventas.csv`: `id,monto` / `1,10` / `2,40` / `3,25`. Esperado a mano: `sobre_maximo.csv` = `id,monto,maximo,filas` / `2,40,40,3` (`maximo = 40`, `filas = 3`; solo la fila 2 vale el máximo); `sin_cambio.csv` = `x` / `0` (la consulta no devolvió filas, así que `&x` conserva el `0` del `%LET`, p. 198).

**Caso `L5/l5_14_dictionary_columns_cuenta` (`capa: B`, `estado: revisado`, razonamiento: «sqlproc, p. 192 y 194»).**
```sas
PROC IMPORT DATAFILE='.../entradas/ventas.csv' OUT=WORK.VENTAS DBMS=CSV REPLACE; GETNAMES=YES; RUN;
PROC SQL NOPRINT;
  SELECT COUNT(*) INTO :ncol FROM DICTIONARY.COLUMNS WHERE libname = 'WORK' AND memname = 'VENTAS';
  CREATE TABLE WORK.con_ncol AS SELECT id, &ncol AS ncol FROM WORK.ventas;
QUIT;
```
Misma `ventas.csv`. Esperado: `con_ncol.csv` = `id,ncol` / `1,2` / `2,2` / `3,2` (`ventas` tiene dos columnas: `id` y `monto`).

- [ ] **Step 1: Write the failing tests.** (a) el `set_variable` de `INTO :maximo, :filas` trae `si_sin_filas == "conservar"`; (b) `resolver_diccionario` sobre el árbol de `l5_14` con `{"WORK.VENTAS": ["id","monto"]}` da un `COUNT` de 2, y sin el esquema da `None`; (c) `INSERT INTO DICTIONARY.COLUMNS ...` queda `P-DICTIONARY-SOLO-LECTURA`; (d) los dos casos coinciden en el anillo B (el intérprete evalúa el `set_variable` y sustituye `&maximo` en la sentencia siguiente: si hoy no lo hace, esa sustitución entra aquí en `interprete_escalares.py`, no en el expansor de macros).
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_select_into_y_diccionario.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement** `si_sin_filas` en `_host_assignments` y `resolver_diccionario`. Si el motivo de `l5_09` (`P-ESQUEMA-NO-PORTABLE`) es el mismo que impide `l5_13`, resolverlo aquí y quitar `l5_09` de `migrar_pendientes.yaml`; si es otro, dejarlo con su motivo.
- [ ] **Step 4: Run** los tests, `tests/unit/test_migrar_corpus_anillo_b.py` (L5 entra en `NIVELES`), `tests/unit/test_corpus_l4l6.py` y el golden.
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N m: SELECT INTO con filas vacias y DICTIONARY.COLUMNS resuelto en migracion`.

---

### Task C-15: Funciones SAS dentro de `PROC SQL` y portabilidad de dialecto (MG-P5-08; serie `m`)

`rules/sas/sql-functions.json` clasifica 31 funciones: 14 `portable`, 1 `translated` (`substrn`) y 16 `sas_only`. `sql_portability.py` solo deja pasar a una base las sentencias cuyas funciones son `portable`. Lo que falta es que el archivo sea **consistente con la guía y con el traductor**: cada función con su página, y una función `sas_only` que aparece en una consulta sobre flujo (no empujada a una base) se traduzca con la tabla de expresiones (`src/sgm/expressions/`) en vez de dejar la sentencia sin traducir. Páginas (`lefunctionsref`): `UPCASE` (p. 1638), `SUBSTRN` (p. 1576), `COALESCE` (p. 560), `ROUND` (p. 1486), `CATX` (p. 508); en `sqlproc`, `COALESCE Function` (p. 386) y `sql-expression Component` (p. 422).

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\rules\sas\sql-functions.json` (campo `pagina` por función: `"lefunctionsref.pdf, p. N"`; las 31 funciones; la guía de `sqlproc` solo si la función es propia de `PROC SQL`)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\ir\sql_portability.py` (expone `pagina_de(nombre: str) -> str | None`)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_sql_functions_regla.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\L3\l3_24_funciones_sas_en_select\{caso.yaml, programa.sas, entradas\clientes.csv, esperado\transformada.csv}`

**Interfaces:**
- Consumes: `function_names(sql: str) -> list[str]`, `unportable_functions(sql: str) -> list[str]`, `is_portable(sql: str) -> bool`, `load_sql_portable(path: Path | None = None) -> frozenset[str]` (`sql_portability.py:29-68`).
- Produces: `def pagina_de(nombre: str) -> str | None` y la prueba de consistencia: toda función de `sql-functions.json` figura en `lefunctionsref.INDEX.md` como `<NOMBRE> Function (p. N)` (comprobarlo con `grep -n "UPCASE Function" docs/referencia/sas/lefunctionsref.INDEX.md`); una función sin página en la guía queda con `pagina: null` y `status: sas_only` con nota `Pendiente:` (por ejemplo `calculated` y `sysfunc` no son funciones, son palabras clave: su página es la de `CALCULATED Component`, `sqlproc` p. 384, y la de `%SYSFUNC` en `mcrolref`).

**Caso `L3/l3_24_funciones_sas_en_select` (`capa: B`, `estado: revisado`, razonamiento: «lefunctionsref, p. 1638, 1576, 560, 1486 y 508»).**
```sas
PROC SQL;
  CREATE TABLE WORK.transformada AS
  SELECT id, UPCASE(nombre) AS nom, SUBSTRN(nombre, 1, 2) AS ini, COALESCE(monto, 0) AS m0,
         ROUND(monto, 10) AS r, CATX('-', nombre, 'x') AS marca
  FROM WORK.clientes;
QUIT;
```
`clientes.csv`: `id,nombre,monto` / `1,ana,15` / `2,beto,` / `3,cora,24`. Esperado a mano: `id,nom,ini,m0,r,marca` / `1,ANA,an,15,20,ana-x` / `2,BETO,be,0,,beto-x` / `3,CORA,co,24,20,cora-x` (`ROUND(15,10)` es `20` porque `15/10 = 1,5` redondea a `2`; `ROUND(24,10)` es `20`; el faltante da faltante; `CATX` une con el separador y recorta blancos). Verificar en el `.txt` de cada página que la descripción coincide antes de fijar el esperado; la que no coincida se quita del caso y queda `Pendiente:`.

- [ ] **Step 1: Write the failing test.** `test_sql_functions_regla.py`: (a) toda función de `sql-functions.json` tiene `pagina` o `status: sas_only` con nota `Pendiente:`; (b) toda `portable` y `translated` está en `_funcion` del intérprete o en la tabla de `src/sgm/expressions/`; (c) `is_portable("select upcase(a) from t")` es `False` y `is_portable("select upper(a) from t")` es `True`; (d) el caso `l3_24` coincide en el anillo B y **no** se empuja a una base (`placement` de flujo, no `db:`).
- [ ] **Step 2: Run test to verify it fails.** `uv run python -m pytest tests/unit/test_sql_functions_regla.py -q -p no:cacheprovider`; esperado: sin campo `pagina`.
- [ ] **Step 3: Implement** el campo y `pagina_de`; completar páginas con `grep -n "<NOMBRE> Function" docs/referencia/sas/lefunctionsref.INDEX.md` (no inventar: sin entrada, `null`). Si una de las funciones del caso no la traduce hoy la tabla de expresiones, queda `P-FUNCION-SQL-SIN-TRADUCIR` con su nombre y el caso la omite hasta que Plan D1 (MG-P3) la cubra.
- [ ] **Step 4: Run** los tests, `uv run python tools/medir_sql_portable.py` (el conteo de sentencias portables no cambia), `tests/unit/test_catalogo_sas.py` y `tests/unit/test_mg_p13_sql_emitter_security.py`.
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N m: funciones de SQL con su pagina y consistentes con el traductor`.

---

## Parte II. MG-P6 restante: procedimientos (serie `n`, 46 h)

### Task C-16: `PROC SORT` completo: `NODUPREC` sin `_ALL_`, `DUPOUT=`, `NOEQUALS`, `DESCENDING` (MG-P6-01; serie `n`)

El catálogo (`procs-usados.yaml`, entrada `sort`) ya dice: `BY`, `NODUPKEY`, `DUPOUT=` y `NOEQUALS` reconocidos; `DESCENDING` (`proc.pdf`, p. 2479); `NODUPREC` solo con `BY _ALL_` por adyacencia (`lrcon`, p. 714); «`NODUPKEY` queda parcial hasta validar la estabilidad de `tSortRow`». Lo que falta es lo que esos casos no demuestran: `NODUPREC` con `BY` de una llave (compara cada registro con el **anterior de la salida**, no con todos), `DUPOUT=` con los registros que se quitaron, y `NOEQUALS` (el orden dentro de una llave empatada no está garantizado: el caso compara como conjunto). Páginas exactas, dentro de «PROC SORT Statement» (p. 2460, la entrada indexada): `DUPOUT=` p. 2461 y `EQUALS | NOEQUALS` p. 2471 (se verifican con `grep -n "<!-- página 2471 -->" docs/referencia/sas/proc.txt`); el `fuente` del catálogo sigue siendo `proc.pdf, p. 2460`.

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\ir\lower_procs.py` (`_sort`, línea 116; ya tiene 266 líneas: si pasa de 300, extraer `_sort*` a `lower_procs_sort.py` en un paso previo)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\interprete.py` (`_unicos`, línea 643; y `_ordenar`, línea 625)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\corpus_lib\especificaciones_l6_procs.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\corpus_lib\generar_entradas_l4l6.py` (línea 181: `"L6": {**ESPECIFICACIONES_L6, **ESPECIFICACIONES_L6_PROCS}`)
- Create (generados): `tests\corpus\L6\l6_60_noduprec_por_llave`, `l6_61_nodupkey_dupout`, `l6_62_sort_descending_noequals`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\rules\sas\catalogo\procs-usados.yaml` (`sort`: la nota separa lo demostrado de lo pendiente)
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_proc_sort_completo.py`

**Interfaces:**
- Consumes: `ordenar(op_id, by, descending=False, outputs=None, evidence=None)`, `deduplicar(op_id, by, keep="first", outputs=None, evidence=None)` (`operadores.py:294,318`), `proc_sort(filas, by, nodupkey=False)` y `proc_sort_nodup(filas, columnas)` (`tools/corpus_lib/referencia_datastep.py:195,215`).
- Produces: `def proc_sort_noduprec_por_llave(filas: list[dict], by: list[str]) -> list[dict]` en `referencia_datastep.py` (el oráculo del caso: ordena estable por `by` y quita solo el registro idéntico al **inmediatamente anterior**) y, en el lowering, `deduplicar(op_id, by=<todas las columnas>, keep="first")` solo cuando el orden de salida hace adyacentes a los idénticos; si no lo hace, `P-NODUPREC-NO-ADYACENTE`.

**Casos (`capa: B`, generados por `especificaciones_l6_procs.py`).**
`l6_60_noduprec_por_llave` (`estado: pendiente_revision` hasta que se lea `lrcon`, p. 714 y se anote su texto en `razonamiento`; después `revisado`):
```sas
PROC SORT DATA=WORK.R OUT=WORK.R_SIN NODUPREC; BY id; RUN;
```
Entrada `R` (`id,v`): `1,a` / `1,b` / `1,a` / `2,c`. Orden estable por `id`: `1,a`, `1,b`, `1,a`, `2,c`. Ningún registro es idéntico a su **anterior**, así que no se quita ninguno. Esperado: las 4 filas en ese orden (`orden_relevante: true`). Es la prueba de que `NODUPREC` con una llave **no** equivale a `DISTINCT`: el traductor que quite la tercera fila (duplicada de la primera, pero no adyacente) falla.
`l6_61_nodupkey_dupout`:
```sas
PROC SORT DATA=WORK.R OUT=WORK.U NODUPKEY DUPOUT=WORK.D; BY id; RUN;
```
Entrada `R` (`id,v`): `2,x` / `1,a` / `2,y` / `1,b`. Esperado (conservando la primera por llave en el orden de entrada, que es el `EQUALS` por omisión): `U` = `1,a` / `2,x`; `D` = `1,b` / `2,y` (`orden_relevante: false` en `D`). Razonamiento: `proc.pdf`, p. 2461.
`l6_62_sort_descending_noequals`:
```sas
PROC SORT DATA=WORK.R OUT=WORK.S NOEQUALS; BY DESCENDING id; RUN;
```
Entrada `R` (`id,v`): `1,a` / `3,c` / `2,b` / `3,d`. Esperado como **conjunto** por llave: `3,c` y `3,d` primero (en cualquier orden entre sí, `NOEQUALS`), luego `2,b`, luego `1,a`; `orden_relevante: false` y la comparación del anillo B agrupa por llave descendente (usar el comparador por grupos de `corpus_lib.csv_tabla`; si no existe, agregarlo ahí con su prueba).

- [ ] **Step 1: Write the failing tests.** (a) `proc_sort_noduprec_por_llave` sobre `R` de `l6_60` devuelve 4 filas; con `[(1,a),(1,a),(2,c)]` devuelve 2; (b) el lowering de `NODUPREC` con `BY id` produce `P-NODUPREC-NO-ADYACENTE` (hoy lo deja pasar como `deduplicar` por `id`, que quitaría registros distintos: este es el defecto que el caso cubre); (c) `DUPOUT=` crea una segunda salida con los quitados; (d) los tres casos coinciden en el anillo B. Leer `lrcon.txt` p. 714 y `proc.txt` p. 2461 y 2471 para fijar el texto del `razonamiento`.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_proc_sort_completo.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement.** El emisor usa `tUniqRow` para `NODUPKEY` (plantilla ya validada) y no para `NODUPREC` con llave; `DESCENDING` lleva el sentido por clave a `tSortRow`. La estabilidad de `tSortRow` se mide en el lote de C-Gate con `l6_61` (si no es estable, `NODUPKEY` sigue `parcial`, como dice el catálogo, y se anota).
- [ ] **Step 4: Run** `uv run python tools/corpus.py oraculo L6` solo para los tres casos nuevos, `tests/unit/test_corpus_l4l6.py`, `tests/unit/test_proc_sort_integracion.py`, el golden y `tests/unit/test_catalogo_sas.py`.
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N n: PROC SORT con NODUPREC por llave, DUPOUT y NOEQUALS`.

---

### Task C-17: `PROC MEANS` y `PROC SUMMARY` con `CLASS`, `VAR` y `OUTPUT OUT=` (MG-P6-02, parte 1; serie `n`)

Hoy `rules/sas/procs/proc-means.yaml` y `proc-summary.yaml` emiten un `aggregate` con `class`, `var` y `outputs` sin estadísticos. Páginas (`proc.pdf`): `MEANS Procedure` (p. 1521), `PROC MEANS Statement` (p. 1534), `OUTPUT Statement` (p. 1555), «Missing Values» (p. 1571) y «Output Data Set» (p. 1572); `SUMMARY Procedure` (p. 2549, que remite a `MEANS`). `MEANS` descarta los faltantes de las variables `VAR` en cada estadístico (p. 1571); `N` cuenta los no faltantes y `_FREQ_` las observaciones del grupo.

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\rules\sas\procs\proc-means.yaml` y `proc-summary.yaml`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\ir\lower_procs.py` o `lower_procs_agregados.py` (el que cree el Plan B, tarea B-8: leer primero si existe; si no, crearlo aquí) con el reconocimiento de `OUTPUT OUT=ds STAT=nombre ...`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\L3\l3_30_means_class_nway\{caso.yaml, programa.sas, entradas\ventas.csv, esperado\res.csv}`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\L3\l3_31_summary_global\{caso.yaml, programa.sas, entradas\ventas.csv, esperado\tot.csv}`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\rules\sas\catalogo\procs-usados.yaml` (entradas nuevas `means` p. 1521 y `summary` p. 2549, `estado: reconocida`)
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_proc_means.py`

**Interfaces:**
- Consumes: `agregar(op_id, group_by, aggregations, outputs=None, pendiente=None, status="soportado", evidence=None, group_outputs=None, output_order=None) -> Operator`, `lower_declared(spec, step, ev, b, data, out) -> bool` (`proc_rules.py:79`), `names_of(clause)`.
- Produces: `def lower_means(step: Proc, ev: Evidence, b: Builder, data: str | None, out: str | None) -> None`: `STAT=nombre` para `SUM`, `MEAN`, `MIN`, `MAX`, `N` y `NMISS` (las que `proc.pdf` p. 1555 a 1563 define); con `NWAY` solo la combinación completa de `CLASS`; sin `NWAY`, `_TYPE_` y `_FREQ_` y la fila global quedan `Pendiente: P-MEANS-TYPE-NO-DEMOSTRADO` salvo que el `OUTPUT` los quite con `DROP=_TYPE_ _FREQ_` (los casos usan `NWAY` y `DROP=`); estadísticos fuera de esa lista (`STD`, `VAR`, percentiles): `P-MEANS-ESTADISTICO-SIN-SOPORTE`.

**Caso `L3/l3_30_means_class_nway` (`capa: B`, `estado: revisado`, `tolerancia: 1.0e-06`, razonamiento: «proc, p. 1534, 1555, 1571 y 1572»).**
```sas
PROC IMPORT DATAFILE='.../entradas/ventas.csv' OUT=WORK.VENTAS DBMS=CSV REPLACE; GETNAMES=YES; RUN;
PROC MEANS DATA=WORK.ventas NOPRINT NWAY;
  CLASS region; VAR monto;
  OUTPUT OUT=WORK.res(DROP=_TYPE_ _FREQ_) SUM=total MEAN=prom N=n;
RUN;
```
`ventas.csv`: `region,monto` / `N,10` / `N,` / `S,5` / `S,7`. Esperado a mano: `res.csv` = `region,total,prom,n` / `N,10,10,1` / `S,12,6,2` (`N`: el faltante no entra en ningún estadístico, `n = 1`; `S`: 5+7, media 6).
**Caso `L3/l3_31_summary_global` (`capa: B`, `estado: revisado`, razonamiento: «proc, p. 2549 y 1572»).**
```sas
PROC SUMMARY DATA=WORK.ventas;
  VAR monto; OUTPUT OUT=WORK.tot(DROP=_TYPE_ _FREQ_) SUM=total MIN=minimo MAX=maximo N=n;
RUN;
```
Mismo `ventas.csv`. Esperado: `tot.csv` = `total,minimo,maximo,n` / `22,5,10,3` (10+5+7; el faltante fuera).

- [ ] **Step 1: Write the failing tests.** Los dos casos coinciden en el anillo B (hoy: `aggregate` sin estadísticos, `P-AGREGADO-SIN-TRADUCIR`); `STD=` da `P-MEANS-ESTADISTICO-SIN-SOPORTE`; sin `NWAY` ni `DROP=` da `P-MEANS-TYPE-NO-DEMOSTRADO`. Verificar en `proc.txt` que p. 1572 describe `_TYPE_` y `_FREQ_` como se usa (`grep -n "<!-- página 1572 -->"`).
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_proc_means.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement** `lower_means` sobre `agregar` y enganchar en `lower_proc` (`elif name in {"means","summary"}`) antes de `declared(name)`. El emisor reusa `desde_plan_agregado.py` (C-6).
- [ ] **Step 4: Run** los tests, `tests/unit/test_proc_rules.py`, `tests/unit/test_migrar_corpus_anillo_b.py` y el golden; el YAML declarativo se conserva para la forma sin `OUTPUT`.
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N n: PROC MEANS y SUMMARY con CLASS, VAR y OUTPUT OUT=`.

---

### Task C-18: `PROC FREQ`: lo que las guías demuestran y lo que no (MG-P6-02, parte 2; serie `n`)

**`Pendiente:` de fuente.** `PROC FREQ` pertenece a SAS/STAT: el `proc.INDEX.md` no tiene su capítulo ni la descripción del dataset `OUT=` (`COUNT`, `PERCENT`). Las páginas de `proc.pdf` que lo mencionan son ejemplos de «Procedure Concepts» (p. 80 a 101; p. 89: `MISSPRINT` muestra los niveles faltantes pero no los usa en los estadísticos). **Decisión (se anota en `PROGRESS.md`, «Decisiones»):** sin página, no hay equivalencia. `PROC FREQ` sin `OUT=` es un reporte impreso y entra en la política de C-22 (se descarta con aviso); con `OUT=` queda `Pendiente: P-FREQ-OUT-SIN-PAGINA`. Alternativa descartada: bajar el docset de SAS/STAT (`tools/referencia/fuentes.py` solo conoce los 13 docsets de la base; SAS/STAT son miles de páginas fuera del alcance y habría que revisar su licencia de uso). Qué cambia: el traductor no produce una tabla de frecuencias hasta que alguien aporte la página; el costo es que los programas con `PROC FREQ ... OUT=` quedan parciales.

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\rules\sas\procs\proc-freq.yaml` (`status: parcial`; `fallback.reason: PROC_NO_SOPORTADO`, nota con `P-FREQ-OUT-SIN-PAGINA`; el `ops` actual, un `aggregate` sin `count` ni `percent`, se quita: declara soportado algo que no lo está)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\ir\lower_procs.py` (`REPORT_PROCS` pasa a incluir `freq` solo cuando no hay `OUT=`)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\rules\sas\catalogo\procs-usados.yaml` (entrada `freq`: `fuente: proc.pdf, p. 89`, `estado: no_verificada`, nota con el pendiente)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\L3\l3_32_freq_out_sin_pagina\{caso.yaml, programa.sas, entradas\ventas.csv}` (`estado: sin_esperado`, `motivo: P-FREQ-OUT-SIN-PAGINA`)
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_proc_freq.py`

**Interfaces:**
- Consumes: `lower_proc(step: Proc, ev: Evidence, b: Builder) -> None` (`lower_procs.py:97`), `REPORT_PROCS = frozenset({"print", "report", "contents"})`.
- Produces: `PROC FREQ DATA=d; TABLES x;` (sin `OUT=`) = `unsupported` con `reason: REPORTE` (lo decide la política `reports` de `env/project.json`, hoy `discard`); `TABLES x / OUT=ds` = `unsupported` con `reason: PROC_NO_SOPORTADO` y nota `P-FREQ-OUT-SIN-PAGINA`.

**Caso `L3/l3_32_freq_out_sin_pagina` (`estado: sin_esperado`).** `PROC FREQ DATA=WORK.ventas; TABLES region / OUT=WORK.fr; RUN;` sobre el `ventas.csv` de C-17. No lleva `esperado/`: el motivo es la falta de página, no un valor supuesto.

- [ ] **Step 1: Write the failing tests.** (a) `TABLES region;` produce `reason == "REPORTE"`; (b) `TABLES region / OUT=fr;` produce `PROC_NO_SOPORTADO` y la nota con el código; (c) el YAML ya no declara `status: soportado`; (d) el caso carga con `estado: sin_esperado`.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_proc_freq.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement.** Si durante la tarea alguien aporta la página de `PROC FREQ` (`SAS/STAT`), esta tarea se reabre con un caso nuevo; no se adivina el contrato de `OUT=` desde otras fuentes.
- [ ] **Step 4: Run** los tests, `tests/unit/test_proc_rules.py`, `tests/unit/test_catalogo_sas.py` (`(p. 89)` está en el índice: «Order Data Using Formats: Missing Values») y el golden.
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N n: PROC FREQ sin OUT= como reporte y con OUT= pendiente por falta de pagina`.

---

### Task C-19: `PROC TRANSPOSE` (MG-P6-03; serie `n`)

`operadores.pivotar` existe como hueco (`status="hueco"`, «PROC TRANSPOSE sin traducción: pendiente»). Páginas (`proc.pdf`): `TRANSPOSE Procedure` (p. 2745), «Simple Transposition» (p. 2746), «Complex Transposition Using BY Groups» (p. 2747), `PROC TRANSPOSE Statement` (p. 2752), `BY` (p. 2754), `ID` (p. 2756), `VAR` (p. 2759), «Output Data Set Variables» (p. 2760), «Names of Transposed Variables» (p. 2761). **El esquema de salida depende de los datos**: las columnas nuevas llevan los valores de la variable `ID`. Un Job de Talend tiene esquema fijo: el paso solo se emite si los valores de `ID` son demostrables (los que traen las `entradas/` del caso o un `decisiones/<programa>.transpose.yaml` con la lista explícita); si no, `P-TRANSPOSE-ESQUEMA-DINAMICO`.

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\ir\operadores.py` (`pivotar` con `id`, `prefix`, `valores_id`; `status="soportado"` solo con `valores_id` demostrados)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\ir\lower_procs_transpose.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\interprete.py` o un módulo nuevo `interprete_pivote.py` (preferible: `interprete.py` ya pasa de 300 líneas)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\talend_item\desde_plan_pivote.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\L3\l3_33_transpose_by_id_prefix\{caso.yaml, programa.sas, entradas\largo.csv, esperado\ancho.csv}`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_proc_transpose.py`

**Interfaces:**
- Consumes: `pivotar(op_id, by, var, evidence=None) -> Operator` (`operadores.py:340`), `ordenar(...)`.
- Produces:
  ```python
  def pivotar(op_id: str, by: list[str], var: str, id: str | None = None, prefix: str = "",
              valores_id: list[str] | None = None, evidence=None) -> Operator: ...
  def lower_transpose(step: Proc, ev: Evidence, b: Builder, data: str | None, out: str | None) -> None: ...
  def nodo_pivote(op: Operator, columnas: dict[str, list[Columna]]) -> list[Nodo | Fila | Tabla]:
      """tSortRow por `by` + tJavaFlex que acumula el grupo y emite una fila por grupo."""
  ```

**Caso `L3/l3_33_transpose_by_id_prefix` (`capa: B`, `estado: revisado`, razonamiento: «proc, p. 2746, 2747, 2756, 2760 y 2761»).**
```sas
PROC IMPORT DATAFILE='.../entradas/largo.csv' OUT=WORK.LARGO DBMS=CSV REPLACE; GETNAMES=YES; RUN;
PROC SORT DATA=WORK.largo; BY id; RUN;
PROC TRANSPOSE DATA=WORK.largo OUT=WORK.ancho PREFIX=q; BY id; ID mes; VAR monto; RUN;
```
`largo.csv`: `id,mes,monto` / `1,1,10` / `1,2,20` / `2,1,5`. Esperado a mano: `ancho.csv` = `id,_NAME_,q1,q2` / `1,monto,10,20` / `2,monto,5,` (una fila por `id` y por variable de `VAR`; `_NAME_` lleva el nombre de la variable transpuesta; el valor de `mes` forma el nombre de columna con el prefijo; el grupo `2` no tiene `mes = 2` y queda faltante). Antes de fijar el esperado, comprobar en p. 2760 y 2761 que `_NAME_` es la columna que se agrega y cómo se nombran las columnas con `PREFIX=` e `ID` numérico; lo que no coincida se ajusta o queda `Pendiente:`.

- [ ] **Step 1: Write the failing tests.** (a) `pivotar` con `id="mes"`, `valores_id=["1","2"]` da columnas `["id","_NAME_","q1","q2"]`; (b) sin `valores_id` el operador es `hueco` con `P-TRANSPOSE-ESQUEMA-DINAMICO`; (c) el caso coincide en el anillo B; (d) `PROC TRANSPOSE` sin `VAR` (todas las numéricas) queda `P-TRANSPOSE-SIN-VAR` (hace falta el tipo de cada columna, que el SAS no demuestra si el `PROC IMPORT` no lo fija).
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_proc_transpose.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement** constructor, lowering, intérprete y emisor. La lista de valores de `ID` sale de las `entradas/` del caso con `--muestra`, como los esquemas; en un programa real sin muestra, del YAML de decisión.
- [ ] **Step 4: Studio (punto 2 de 3).** Compilar y ejecutar con `uv run python tools/validar_caso_studio.py l3_33_transpose_by_id_prefix`; anotar si el `tJavaFlex` acumula el grupo con las filas ya ordenadas. Si Studio no conecta: «lote C pendiente» con su motivo.
- [ ] **Step 5: Run** los tests, `tests/unit/test_ir_operadores_corpus.py`, el golden y `uv run ruff check src tests tools`. **Commit** `hito N n: PROC TRANSPOSE con esquema demostrado por los valores de ID`.

---

### Task C-20: Política de `PROC DELETE`, `CONTENTS`, `DATASETS` y `COPY` (MG-P6-04, parte 1; serie `n`)

El programa real grande tiene 216 `PROC DELETE`, 30 `PROC CONTENTS` y 31 `PROC SORT`, más un bucle de `PROC APPEND`. Páginas (`proc.pdf`): `DELETE Procedure` (p. 837), `CONTENTS Procedure` (p. 541), `COPY Procedure` (p. 573), `DATASETS Procedure` (p. 613). Hoy `PROC DELETE` y `PROC DATASETS` caen en `PROC_NO_SOPORTADO` y `PROC CONTENTS` en `REPORTE` (política `reports: discard`).

**Decisión (se escribe en `docs/politica-procedimientos.md` y en `PROGRESS.md`, «Decisiones», sin esperar al usuario):**
- *Opción elegida:* `PROC DELETE`, el `DELETE` de `PROC DATASETS` y `PROC CONTENTS` **sobre `WORK` o sin biblioteca** se omiten con aviso `A-PROC-LIMPIEZA-OMITIDO` (un operador `unsupported` con `reason: LIMPIEZA`, que la pasada 2 trata como el reporte descartado). Razón: las tablas de `WORK` de un programa SAS son intermedias de un solo programa y en un Job de Talend viven en el flujo; borrarlas antes de recrearlas (los 216 usos) no tiene efecto observable. Sobre cualquier otra biblioteca borran datos persistentes: queda `Pendiente: P-DELETE-PERSISTENTE`, sin traducir.
- *Alternativa:* traducir a `tFileDelete` (archivos) o a `DROP TABLE IF EXISTS` (base). Qué cambia: el Job destruiría datos de producción por una sentencia de limpieza cuyo efecto el SAS no demuestra que sea intencional; requiere una decisión del usuario por programa (`decisiones/<programa>.*.yaml`, nunca en `src/`).
- `PROC COPY IN=a OUT=b` sin `SELECT`: `P-COPY-SIN-LISTA` (copia todos los datasets de la biblioteca: hace falta enumerarla en ejecución); con `SELECT x y`: una lectura y una escritura por tabla, si `b` no es persistente; si lo es, `P-COPY-PERSISTENTE`.
- Esto fija también lo que hace `DROP` y `DELETE FROM` de C-12 y C-13: mismo criterio (`WORK` omite o versiona; otra biblioteca, pendiente).

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\docs\politica-procedimientos.md`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\ir\lower_procs_limpieza.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\ir\lower_procs.py` (`lower_proc`: ramas `delete`, `datasets`, `copy`, `contents`)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\motivos.py` (línea 55, lista de motivos: agregar `LIMPIEZA`)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\passes\p02_plumbing.py` (`_report`, línea 75: `LIMPIEZA` se descarta igual que `REPORTE` cuando la biblioteca es `WORK`)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\rules\sas\catalogo\procs-usados.yaml` (`delete`, `contents`: `estado: reconocida`, nota con la política; `datasets` y `copy`: entradas nuevas con p. 613 y p. 573)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\L6\l6_63_limpieza_work\{caso.yaml, programa.sas, entradas\ventas.csv, esperado\salida.csv}` (generado: especificación en `especificaciones_l6_procs.py`)
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_proc_limpieza.py`

**Interfaces:**
- Consumes: `lower_proc(step: Proc, ev: Evidence, b: Builder) -> None`, `_unsupported(step, ev, b, note)` (`lower_procs.py:258`), `qualify(dataset)`.
- Produces: `def lower_limpieza(step: Proc, ev: Evidence, b: Builder) -> None` y `def es_work(dataset: str | None) -> bool` (`WORK.x` o `x` sin biblioteca; no distingue mayúsculas).

**Caso `L6/l6_63_limpieza_work` (`capa: B`, `estado: revisado`, razonamiento: «proc, p. 837, 541 y 613: limpieza de WORK sin efecto observable»).**
```sas
PROC IMPORT DATAFILE='.../entradas/ventas.csv' OUT=WORK.VENTAS DBMS=CSV REPLACE; GETNAMES=YES; RUN;
DATA WORK.tmp; SET WORK.ventas; RUN;
PROC CONTENTS DATA=WORK.tmp; RUN;
PROC DELETE DATA=WORK.tmp; RUN;
PROC DATASETS LIBRARY=WORK NOLIST; DELETE ventas2; QUIT;
DATA WORK.salida; SET WORK.ventas; RUN;
```
`ventas.csv`: `id,monto` / `1,10` / `2,40`. Esperado: `salida.csv` = `id,monto` / `1,10` / `2,40`. El programa migra **sin ningún pendiente** y con tres avisos `A-PROC-LIMPIEZA-OMITIDO` (`CONTENTS`, `DELETE`, `DATASETS DELETE`); `ventas2` no existe en el programa: `PROC DATASETS ... DELETE` de un miembro inexistente es un aviso de SAS, no un error (verificar en p. 613 a 620 con `grep`; si la página dice otra cosa, quitar esa línea del caso y dejar `Pendiente:`).

- [ ] **Step 1: Write the failing tests.** `lower_limpieza` sobre `PROC DELETE DATA=WORK.tmp` da un `unsupported` con `reason == "LIMPIEZA"` y nota `A-PROC-LIMPIEZA-OMITIDO`; sobre `PROC DELETE DATA=LZ.tmp` da `P-DELETE-PERSISTENTE`; `PROC COPY` sin `SELECT` da `P-COPY-SIN-LISTA`; el caso migra sin pendientes (hoy `PROC_NO_SOPORTADO` por `DELETE` y `DATASETS`).
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_proc_limpieza.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement** y escribir `docs/politica-procedimientos.md` con las tres decisiones (limpieza, `COPY`, y la de C-22 cuando esté), cada una con su alternativa y lo que cambia.
- [ ] **Step 4: Run** los tests, los casos de L8 que tienen `PROC DELETE` y `PROC DATASETS` (`tests/unit/test_corpus_totales.py`, `tests/unit/test_corpus_validaciones.py`: sus pendientes bajan o quedan igual), `tests/unit/test_proceso_*` y el golden.
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N n: politica de limpieza: PROC DELETE, CONTENTS y DATASETS en WORK se omiten con aviso`.

---

### Task C-21: `PROC APPEND` con base nueva, repetido y en bucle (MG-P6-04, parte 2; serie `n`)

Páginas (`proc.pdf`): `APPEND Procedure` (p. 161), `Syntax` (p. 162), `Usage` (p. 163) y `Example 1: Concatenating Two SAS Data Sets` (p. 163). `proc-append.yaml` emite hoy `union` con `sources: [base, data]`, sin decir que el **resultado es la propia base** (cambia el dataset `BASE=`). Verificar en p. 162 y 163: qué pasa si `BASE=` no existe (SAS lo crea como copia de `DATA=`) y si `DATA=` trae una columna que `BASE=` no tiene (sin `FORCE` es un error); lo que no esté en el texto queda `Pendiente: P-APPEND-BASE-NUEVA` o `P-APPEND-COLUMNAS-DISTINTAS`.

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\rules\sas\procs\proc-append.yaml` (`outputs: ["{qualified:base}"]`: la salida es la base, en versión nueva)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\ir\lower_procs_append.py`
- Create (generado): `tests\corpus\L6\l6_64_append_repetido_y_base_nueva`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\corpus_lib\especificaciones_l6_procs.py`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_proc_append.py`

**Interfaces:**
- Consumes: `concatenar(op_id, sources, evidence=None) -> Operator`, `lower_declared(...)`, la versión de tabla de C-13 (`WORK.t#2`).
- Produces: `def lower_append(step: Proc, ev: Evidence, b: Builder, version: int) -> str`: devuelve el nombre de la nueva versión de `BASE=`. En un bucle (`%DO ... %END` ya expandido por el expansor de macros), cada vuelta es una versión: el Plan E entrega las vueltas expandidas y esta tarea las encadena; si el bucle no está expandido, `P-APPEND-EN-BUCLE-SIN-EXPANDIR`.

**Caso `L6/l6_64_append_repetido_y_base_nueva` (`capa: B`, `estado: revisado`, razonamiento: «proc, p. 162 y 163»).**
```sas
PROC APPEND BASE=WORK.acum DATA=WORK.n1; RUN;
PROC APPEND BASE=WORK.acum DATA=WORK.n2; RUN;
PROC APPEND BASE=WORK.otra DATA=WORK.n1; RUN;
```
Entradas: `acum` (`id,v`): `1,a` / `2,b`; `n1`: `3,c`; `n2`: `4,d` / `5,e`. Esperado a mano: `acum` = `1,a` / `2,b` / `3,c` / `4,d` / `5,e` (las dos adiciones se acumulan en orden); `otra` = `3,c` (base nueva: copia de `n1`, si p. 162-163 lo dice; si no, el tercer `PROC APPEND` se quita del caso y queda `P-APPEND-BASE-NUEVA`). Invariante: `filas(acum) == 5`.

- [ ] **Step 1: Write the failing tests.** Dos `PROC APPEND` seguidos sobre la misma base dan dos versiones encadenadas (`acum#2`, `acum#3`) y el último es el visible; el caso coincide en el anillo B; `DATA=` con una columna que no está en `BASE=` da `P-APPEND-COLUMNAS-DISTINTAS`.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_proc_append.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement.** La escritura final de la base usa el mecanismo `APPEND` secuencial (no `tUnite`).
- [ ] **Step 4: Run** los tests, `tests/unit/test_proc_rules.py`, `tests/unit/test_corpus_l4l6.py` y el golden. Catálogo: `append`, p. 161.
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N n: PROC APPEND con versiones de base y base nueva`.

---

### Task C-22: Política de `PRINT`, `REPORT`, `TABULATE` y `ODS`, y lista de procedimientos fuera de alcance generada (MG-P6-05 y MG-P6-06; serie `n`)

**Estado hoy:** `REPORT_PROCS = {print, report, contents}` genera `unsupported` con `reason: REPORTE`, y la pasada 2 (`p02_plumbing._report`, línea 75) aplica `env/project.json`, `"reports": "discard"`. Ya hay una política; falta lo que la rodea. **Decisión (anotar en `docs/politica-procedimientos.md` y `PROGRESS.md`, «Decisiones»):** se **omite con aviso** `A-REPORTE-OMITIDO` (la política `discard` vigente) y no se traduce a `tLogRow`. Páginas: `PRINT Procedure` (`proc.pdf`, p. 1809), `REPORT Procedure` (p. 2139), `TABULATE Procedure` (p. 2553). Alternativa: `tLogRow` por reporte. Qué cambia: escribe en el log del Job miles de filas por ejecución (el programa real tiene decenas de `PROC PRINT` de diagnóstico), ralentiza y hace que el log deje de servir; se deja disponible solo con `"reports": "log"` por proyecto, ya previsto en la política. `ODS ...` (sentencias globales de salida de resultados) y `TITLE`/`FOOTNOTE`/`OPTIONS` no cambian datos: aviso, no pendiente; un `ODS OUTPUT` que **sí** crea un dataset (`ODS OUTPUT tabla=ds`) queda `Pendiente: P-ODS-OUTPUT-DATASET` (el contenido depende del procedimiento).

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\ir\lower_procs.py` (`REPORT_PROCS`: agregar `tabulate`; `freq` sin `OUT=` ya entra por C-18)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\docs\politica-procedimientos.md` (creado en C-20)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\cobertura_procs.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\docs\cobertura.md` (generado; el plan maestro lo nombra así)
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_cobertura_procs.py`

**Interfaces:**
- Consumes: `docs/referencia/sas/proc.INDEX.md` (las 77 entradas `<NOMBRE> Procedure (p. N)`), `rules/sas/catalogo/procs-usados.yaml`, `rules/sas/procs/*.yaml` y `PROCS_DIR`/`load(directory)` de `ir/proc_rules.py`.
- Produces:
  ```python
  def clasificar(indice: Path, catalogo: Path, reglas: Path) -> list[dict]:
      """Por cada procedimiento de la guía: `traducido` (regla o rama en lower_procs), `reporte`
      (política reports), `limpieza`, `pendiente` (con su código P-) o `fuera_de_alcance` (con
      motivo y página). Sin motivo ni página no se clasifica como fuera de alcance."""
  def escribir(destino: Path, filas: list[dict]) -> None: ...
  ```

- [ ] **Step 1: Write the failing tests.** (a) `clasificar` sobre un índice y un catálogo mínimos en `tmp_path` pone `PRINT` como `reporte`, `SORT` como `traducido` y un procedimiento sin regla (`CALENDAR`) como `fuera_de_alcance` con su página; (b) toda fila `fuera_de_alcance` trae motivo y página que existe en `proc.INDEX.md` (el mismo criterio de `test_catalogo_sas.py`); (c) `docs/cobertura-procedimientos.md` está al día: `escribir` sobre una carpeta temporal produce el mismo texto que el archivo versionado (si un hito cambia un procedimiento y no regenera el documento, la prueba falla); (d) `PROC TABULATE` genera `REPORTE` y un programa con `ODS OUTPUT` genera `P-ODS-OUTPUT-DATASET`.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_cobertura_procs.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement** `tools/cobertura_procs.py` y generar `docs/cobertura-procedimientos.md` con `uv run python tools/cobertura_procs.py`. El motivo de «fuera de alcance» sale de una tabla de la herramienta, por familia (infraestructura de SAS, gráficos, SAS/ACCESS, administración de la sesión), no de una frase por procedimiento; un procedimiento sin familia asignada se lista como `no_verificado`.
- [ ] **Step 4: Run** los tests, `tests/unit/test_catalogo_sas.py`, `tests/unit/test_proceso_*` y el golden.
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N n: politica de reportes y lista generada de procedimientos fuera de alcance`.

---

### Task C-23: `PROC FORMAT` y `PROC SQL` avanzado que falte (MG-P6-07; serie `n`; contrato con el Plan D1, MG-P3-07)

**`PROC FORMAT`.** Páginas (`proc.pdf`): `FORMAT Procedure` (p. 1127); el uso del formato en `PUT(x, fmt.)` es de `lefunctionsref` (`PUT Function`, buscar con `grep -n "PUT Function" docs/referencia/sas/lefunctionsref.INDEX.md`) y de `leforinforref`. **Contrato con el Plan D1 (MG-P3-07, formatos e informats):** esta tarea reconoce `VALUE nombre (rangos) = 'etiqueta'` y produce un registro de formatos de usuario (`src/sgm/ir/formatos_usuario.py`) con `FormatoUsuario(nombre, rangos, otro)`; el Plan D1 es quien resuelve `PUT`/`INPUT` con ese registro. Sin D1, el caso se ejecuta en el anillo B con la tabla de formatos que carga esta tarea, y el emisor deja el `PUT` con formato de usuario en `P-FORMATO-USUARIO-SIN-EMISOR`.

**`PROC SQL` avanzado que falte.** No se enumera a ciegas: se mide. `uv run python tools/linea_base_sql_procs.py tests/corpus` más `uv run python tools/medir_sql_portable.py` sobre los programas reales del repositorio dan las construcciones de `PROC SQL` que siguen sin traducir. Criterio: se implementa la que aparezca en **5 programas o más** y tenga página en `sqlproc`; las demás quedan en `docs/cobertura-procedimientos.md` con su código `P-` y su página.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\ir\formatos_usuario.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\ir\lower_procs_format.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\ir\lower_procs.py` (rama `format`)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\L3\l3_34_format_value_y_put\{caso.yaml, programa.sas, entradas\clientes.csv, esperado\con_estado.csv}`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\rules\sas\catalogo\procs-usados.yaml` (`format`, p. 1127)
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_proc_format.py`

**Interfaces:**
- Consumes: `controlar(op_id, reason, evidence=None) -> Operator` y el kind `report`/`unsupported` de `ir/models.py`.
- Produces:
  ```python
  @dataclass(frozen=True)
  class FormatoUsuario:
      nombre: str                          # '$estf' (con $ si es de carácter)
      rangos: tuple[tuple[str, str], ...]  # (valor, etiqueta)
      otro: str | None                     # etiqueta de OTHER, si la hay
  def lower_format(step: Proc, ev: Evidence, b: Builder) -> list[FormatoUsuario]: ...
  ```

**Caso `L3/l3_34_format_value_y_put` (`capa: B`, `estado: pendiente_revision` hasta verificar en la guía el comportamiento de un valor sin rango y sin `OTHER`; después `revisado`; razonamiento: «proc, p. 1127; PUT en lefunctionsref»).**
```sas
PROC IMPORT DATAFILE='.../entradas/clientes.csv' OUT=WORK.CLIENTES DBMS=CSV REPLACE; GETNAMES=YES; RUN;
PROC FORMAT; VALUE $estf 'A'='Activo' 'I'='Inactivo' OTHER='Otro'; RUN;
DATA WORK.con_estado; SET WORK.clientes; desc = PUT(estado, $estf.); RUN;
```
`clientes.csv`: `id,estado` / `1,A` / `2,I` / `3,X`. Esperado a mano: `id,estado,desc` / `1,A,Activo` / `2,I,Inactivo` / `3,X,Otro`.

- [ ] **Step 1: Write the failing tests.** `lower_format` sobre `VALUE $estf 'A'='Activo' 'I'='Inactivo' OTHER='Otro'` devuelve un `FormatoUsuario` con dos rangos y `otro == "Otro"`; un rango numérico con `-` (`1-5='bajo'`) queda `P-FORMATO-RANGO-SIN-SOPORTE` hasta que D1 lo cubra; el caso coincide en el anillo B. Medir las construcciones de SQL con las dos herramientas y escribir en `PROGRESS.md` la lista ordenada por programas, con las que se implementan y las que no.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_proc_format.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement** el registro y el reconocimiento. Por cada construcción de SQL que cumpla el criterio de 5 programas: un caso nuevo de `L3` con el mismo formato de las tareas C-6 a C-13 (SAS completo, entradas y esperado a mano con su página) y su fila en el catálogo; en un commit aparte por construcción (`hito N n: SQL avanzado: <construcción>`).
- [ ] **Step 4: Run** los tests, `tests/unit/test_catalogo_sas.py`, `tests/unit/test_corpus_l4l6.py` y el golden.
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N n: PROC FORMAT reconocido con contrato para el Plan D1`.

---

### Task C-Gate: GM2 (SQL) y GM3 (procedimientos): L1 a L3 y L6 en B y en lote C (serie `m`, la cierra Andres)

**Criterio de salida** (compuertas GM2 y GM3 de la sección 10 del plan maestro: leer sus textos con `grep -n "GM2\|GM3" docs/plan-reescritura/plan-migrador-general.md` antes de empezar; lo siguiente es lo que este plan se compromete a probar):
1. **GM2, SQL en B:** los casos de `L1`, `L2` y `L3` con `estado` `traducible` o `revisado`, más `l2_17`, `l2_18`, `l3_13` a `l3_24` y `l5_13`, `l5_14`, coinciden con su `esperado/` en el intérprete (`tests/unit/test_migrar_corpus_anillo_b.py`, con `L3` y `L5` en sus `NIVELES`), y `CONOCIDOS` solo contiene casos con pendiente de alcance con motivo y página.
2. **GM2, SQL en A:** en `migrar_pendientes.yaml` no queda ningún caso de `L1` a `L3` salvo los que declaran `P-` de alcance (`P-SUM-TODO-FALTANTE`, `P-CONJUNTO-ALL-NO-DEMOSTRADO`, `P-UNION-LLAVE-NULA` si Studio no casa nulos, etc.), cada uno con su página.
3. **GM3, procedimientos:** `l3_30`, `l3_31`, `l3_33`, `l6_60` a `l6_64` coinciden en B; `L6` de `PROC SORT` (`l6_08`, `l6_09`, `l6_60` a `l6_62`) y `L8/totales/01` migran sin pendientes de defecto; `docs/cobertura-procedimientos.md` al día.
4. **Lote C:** una sola corrida de Studio con todos los casos de los puntos 1 a 3 que migran sin pendiente: `uv run python tools/corpus_studio.py lote <casos> --jobs <carpeta> --proyecto <proyecto>` para compilar y `uv run python tools/validar_caso_studio.py <casos>` para ejecutar y comparar. Cuenta aparte compilaron y ejecutaron-y-coinciden. Se miden ahí tres cosas que las tareas dejaron abiertas: nulos en `tMap` (C-4), conteos y promedios de `tAggregateRow` con faltantes (C-6) y estabilidad de `tSortRow` con `NODUPKEY` (C-16).

- [ ] **Step 1: Run** la suite completa `uv run python -m pytest -q` y `uv run ruff check src tests tools`.
- [ ] **Step 2: Run** `uv run python tools/linea_base_sql_procs.py tests/corpus` y comparar con C-1; pegar las dos cifras en `PROGRESS.md`.
- [ ] **Step 3: Run** el lote C (punto 4). Si Studio no conecta: `sgm studio salud` y `docs/guia-validacion-studio.md`, sección 7; no se reinstala nada ni se cambia `talend-mcp`. El resultado es «lote C pendiente» con el motivo y las compuertas **no** se declaran cerradas.
- [ ] **Step 4: Registrar** en `PROGRESS.md` el hito de cierre: casos por anillo (A, B, C), pendientes por código, horas acreditadas de MG-P5 y MG-P6 con el método de la sección 11b, y qué quedó fuera con su motivo. Actualizar las tablas MG-P5 y MG-P6 y el «Estado» de ambas fases en `plan-migrador-general.md` en el mismo cambio (si el plan contradice el código, se corrige uno de los dos).
- [ ] **Step 5: Commit.** `hito N m: compuertas GM2 y GM3 y lote C de SQL y procedimientos`.

---

## Resumen de horas

| Tareas | Origen | Serie | Horas |
|---|---|---|---|
| C-1, C-2 | línea base y módulos (reparte P5-02) | m | 2 |
| C-3, C-4, C-5 | MG-P5-02 | m | 8 |
| C-6, C-7 | MG-P5-03 | m | 5 |
| C-8, C-9 | MG-P5-04 | m | 6 |
| C-10, C-11 | MG-P5-05 | m | 5 |
| C-12, C-13 | MG-P5-06 | m | 7 |
| C-14 | MG-P5-07 | m | 4 |
| C-15 | MG-P5-08 | m | 3 |
| C-Gate | cierre (parte SQL) | m | 3 |
| **Subtotal MG-P5** | | | **43** |
| C-16 | MG-P6-01 | n | 6 |
| C-17, C-18 | MG-P6-02 | n | 14 |
| C-19 | MG-P6-03 | n | 8 |
| C-20, C-21 | MG-P6-04 | n | 6 |
| C-22 | MG-P6-05 y MG-P6-06 | n | 5 |
| C-23 | MG-P6-07 | n | 6 |
| C-Gate | cierre (parte procedimientos) | n | 1 |
| **Subtotal MG-P6** | | | **46** |
| **Total** | | | **89** (MG-P5 43 + MG-P6 46) |

Las horas por tarea son estimaciones del plan; el crédito real se mide con el método de la sección 11b del plan maestro.

## Dependencias

**Necesita de otros planes**

| De | Tarea | Para qué |
|---|---|---|
| Plan A | compilación y validación en Studio (`tools/validar_caso_studio.py`, `tools/corpus_studio.py lote`, salud con estados) | C-4, C-19 y C-Gate (lote C); sin Studio esas partes quedan «lote C pendiente» con su motivo, no se cuentan |
| Plan B | B-3 y B-4 (esquemas propagados y declarados), B-5 a B-8 (constructores en el lowering y `lower_procs_agregados.py`), B-7 (cierra el filtro de `l2_12`) | C-3 a C-9 (tipos de las columnas de salida), C-17 (`lower_procs_agregados.py`); B y C extraen ambos de `interprete.py`: el que llegue segundo rebasea y el golden no cambia |
| Plan B | B-11 y B-13 (`MERGE` y estado por fila) | C-Gate (L6 de B y de C comparten el comparador por grupos de `corpus_lib.csv_tabla`) |
| Plan D1 | MG-P3-01 (faltantes) y MG-P3-07 (formatos e informats) | C-6 (comparación con faltantes), C-15 (funciones en la tabla de expresiones), C-23 (`PUT` con formato de usuario) |
| Plan E | MG-P7-04 (variables de macro de ejecución) y expansor de bucles | C-14 (el `set_variable` llega al contexto del Job), C-21 (bucle de `PROC APPEND` expandido) |
| Plan K | K-2 y K-3 (esquemas y datos sintéticos) | C-3 a C-9: casos con más de una fila por grupo si hace falta más volumen que las muestras a mano |

**Entrega a otros planes**

| A | Qué |
|---|---|
| Plan F1 (arquitectura) | `unir` completo (inner/left/right/full/cross), `agregar` con faltantes, `pivotar` con esquema demostrado y las versiones de tabla (`WORK.t#n`) para segmentar |
| Plan F2 (emisor y joblets) | `desde_plan_uniones.py`, `desde_plan_pivote.py` y la decisión de nulos en `tMap` (C-4) |
| Plan G (verificación) | `docs/cobertura-procedimientos.md` generado, `tools/linea_base_sql_procs.py` y la numeración `l6_60` a `l6_79` / `l3_13` a `l3_34` reservada a este plan |
| Plan E | el contrato `set_variable` con `si_sin_filas` (C-14) |

## Self-review

- **Cobertura de la spec:** MG-P5-02 en C-3 a C-5; P5-03 en C-6 y C-7; P5-04 en C-8 y C-9; P5-05 en C-10 y C-11; P5-06 en C-12 y C-13; P5-07 en C-14; P5-08 en C-15; MG-P6-01 en C-16; P6-02 en C-17 y C-18; P6-03 en C-19; P6-04 en C-20 y C-21 (con la política, su alternativa y lo que cambia); P6-05 y P6-06 en C-22; P6-07 en C-23; GM2 y GM3 en C-Gate.
- **Páginas verificadas al redactar** (existen en el índice o en el `.txt`): `sqlproc` p. 73, 79, 83, 88, 91, 96, 102, 107, 111, 122, 124, 129, 131, 133, 134, 135, 140, 144, 145, 150, 153, 154, 167, 187, 192, 194, 198, 199, 282, 296, 299, 302, 309, 312, 323, 393; `proc` p. 89, 161, 541, 573, 613, 837, 1127, 1521, 1534, 1555, 1571, 1572, 1809, 2139, 2460, 2461, 2471, 2479, 2549, 2553, 2745 a 2761; `lefunctionsref` p. 508, 560, 1486, 1576, 1638. Las que se marcan «verificar» en un paso no se pudieron leer completas al redactar y la tarea las lee antes de fijar el esperado.
- **Lo que no tiene página y queda `Pendiente:`:** suma de grupo con todos faltantes (`P-SUM-TODO-FALTANTE`), `INTERSECT ALL` y `EXCEPT ALL` (`P-CONJUNTO-ALL-NO-DEMOSTRADO`), faltantes en operaciones de conjuntos (`P-CONJUNTO-FALTANTES`), `OUTER UNION` sin `CORR` con nombres repetidos, `PROC FREQ ... OUT=` (`P-FREQ-OUT-SIN-PAGINA`, SAS/STAT no está entre las 13 guías), `PROC MEANS` sin `NWAY` ni `DROP=` (`P-MEANS-TYPE-NO-DEMOSTRADO`), `TRANSPOSE` con esquema dinámico, `UPDATE` con subconsulta y `ODS OUTPUT` a dataset.
- **Decisiones documentadas con alternativa:** nulos en `tMap` (C-4), vistas expandidas en línea (C-12), `PROC FREQ` sin página (C-18), limpieza de `WORK` (C-20) y reportes descartados (C-22).
- **Archivos por encima de 300 líneas:** `lower_sql_flow.py`, `interprete.py`, `interprete_subconsultas.py`, `desde_plan_map.py` y `especificaciones_l6.py`; ninguna tarea les suma líneas: C-2 y C-4 extraen primero, y C-8, C-16 y C-19 crean módulos nuevos.
- **Prueba que se modifica:** solo `test_los_nulos_de_sql_no_tienen_regla_implementada` (C-3), y se endurece, no se debilita.
- **Riesgo de coordinación:** `interprete.py` lo extraen B y C; `lower_sql.py` lo toca C-20 (limpieza) además de C-12 y C-13 (misma serie `m` salvo C-20: su cambio se limita a la rama `drop_table` llamando a `lower_limpieza`, y se avisa a Andres en el commit).
- **Proporción:** 23 tareas más la de cierre para 89 h; los cuerpos de funciones los decide quien implementa.
