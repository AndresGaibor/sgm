# MG-D2: Entrada y salida Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Que todo lo que un programa SAS lee o escribe fuera de `WORK` (archivos delimitados, posicionales y Excel, `INFILE/INPUT/FILE/PUT`, informats y formats de fecha y número, `LIBNAME` a rutas y a bases, paso directo `CONNECT TO ... FROM CONNECTION TO`, `FILENAME`, `RSUBMIT/PROC UPLOAD/PROC DOWNLOAD` y datasets permanentes) tenga semántica SAS demostrada en el intérprete (anillo B), componente de Talend en `sgm migrar` (anillo A) y validación en Studio (anillo C, lote C), cerrando MG-P2 y la parte de entrada y salida de la compuerta GM1 (`L0` completo).

**Architecture:** Cambios solo en `sgm-v2` (Python), en cinco zonas: `src/sgm/frontend/` (reconocer sentencias y opciones), `src/sgm/ir/` (lowering a `read_file`, `write_file`, `read` y `exec_sql`, más pases de plan para bibliotecas y copias), `src/sgm/migrar/` (intérprete de referencia: lectores y escritores propios, sin dependencias nuevas), `src/sgm/talend_item/` (emisor desde el plan: `desde_plan_nodos.py`, `desde_plan_nodos_escritura.py`, `desde_plan_contextos.py`) y `src/sgm/formatos/` (módulo nuevo de informats y formats de archivo; D1 es dueño de `INPUT`/`PUT` en expresiones y este plan consume su registro). Cada construcción nueva entra con un caso del corpus `L0` (`caso.yaml`, `programa.sas`, `entradas/*`, `esperado/*`) cuyo esperado se calculó a mano según la guía de SAS, con el patrón de B y C: intérprete primero, emisor después, lote de Studio al final. Lo que una página no demuestra queda como `Pendiente:` con su código, no como un valor supuesto.

**Tech Stack:** Python 3.12, pytest, ruff, `zipfile` y `xml.etree` de la biblioteca estándar (lector y escritor de XLSX sin dependencias nuevas), `sqlite3` de la biblioteca estándar (oráculo del paso directo); `uv run python -m pytest` y `uv run python -m sgm.cli` (en este Windows `uv run pytest` puede bloquearse por Control de aplicaciones).

**Spec:** `docs/plan-reescritura/plan-migrador-general.md` (MG-P2-01 a MG-P2-07, decisiones MG-D03 y MG-D05, secciones 2, 5 y 11b) y `docs/superpowers/plans/2026-11-11-ruta-al-100.md`.

**Horas del plan maestro cubiertas:** MG-P2 restante 38 h (50 h menos 12 h acreditadas por los hitos 104m, 121 y 122).

**Series de hitos:** `n` (carril de Byron, D2-1 a D2-18 y D2-Gate). La letra va en el título de la entrada de `PROGRESS.md` y en el mensaje del commit. Los planes C y K también usan `n` en carriles distintos: el número del hito es único y se toma al ejecutar (ver Global Constraints).

## Global Constraints

- Sin `git push`, sin `--amend`. Un commit local por hito: `hito N n: <resumen>`, terminado con la línea `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Antes de escribir, buscar el último `## Hito` de `PROGRESS.md` (al redactar este plan era el 198) y sumar uno; si otra sesión ya tomó el número, tomar el siguiente. No renumerar entradas publicadas.
- No tocar `tools/ci.py`, `tools/validacion.py`, `tools/instalar_ganchos.py`, `README.md` ni `.githooks/` (son del Plan A y están sin commitear).
- Nada de nombres de scripts de ejemplo (`cod1`, `cod2`, `cars_poc`, `exogena`, `split2`, `split3`, `executeBulkload`, `waitForBulkLoads`, `bulkload_generic`) en `src/` ni `rules/`; lo vigila `tests/unit/test_no_script_specific_names.py`. Los nombres de bases, esquemas y tablas del programa grande tampoco: lo que dependa del nombre del cliente va a `decisiones/<programa>.*.yaml`.
- Si el SAS no demuestra un tipo, una columna, un valor o una equivalencia: `Pendiente:` con motivo y código `P-xxx`. Nunca un valor supuesto.
- Si no hay página de la guía SAS, no hay equivalencia. Cada regla nueva cita `<guía>, p. N` con una página que exista en `docs/referencia/sas/<guía>.INDEX.md`. No leer el PDF ni el `.txt` entero: ubicar la sección en el `.INDEX.md` y la página con `grep -n "<!-- página N -->" docs/referencia/sas/<guía>.txt`. Los números de página de este plan son páginas del PDF (las del `.INDEX.md`), no las impresas al pie. **Lo que las 13 guías no cubren:** las opciones de `LIBNAME` y de `CONNECT TO` de cada motor (Impala, Postgres) son de SAS/ACCESS, que no está entre las 13. De esas opciones solo se reconoce la forma sintáctica (`sqlproc`, p. 287; `lestmtsref`, p. 233); el significado de cada opción queda `Pendiente: P-CONEXION-OPCIONES` y host, puerto y base salen del contexto del Job, nunca del texto del SAS.
- **Catálogo:** `tests/unit/test_catalogo_sas.py` exige que el literal `(p. N)` de cada `fuente` esté en el `.INDEX.md` de su guía. Si la página exacta de una opción no es una entrada del índice (por ejemplo `MISSOVER`, dentro de `INFILE`, p. 134), el campo `fuente` cita la entrada indexada que la contiene y la página exacta va en `nota`. Cada tarea que suma una construcción actualiza el YAML de `rules/sas/catalogo/` que corresponde (`procs-usados.yaml`, `sentencias-data-step.yaml`, `informats-usados.yaml`) y su `estado`.
- **Casos del corpus:** los casos de este plan van a `tests/corpus/L0/l0_16_*` a `l0_31_*` (numeración reservada a este plan; `l0_01` a `l0_15` existen). Cada uno lleva `caso.yaml`, `programa.sas` con rutas marcador `'.../entradas/x'` como `l0_15_importar_exportar`, `entradas/*` y `esperado/*`. `tests/unit/test_migrar_corpus_anillo_b.py` ya recorre `L0` (`NIVELES`), así que un caso nuevo se ejecuta en B sin tocar esa prueba. Los casos con base (D2-2 a D2-4) declaran `capa: C` y `contenedor: impala` o `postgres`: **verificar en `tools/corpus_lib/caso.py` (`cargar_caso`, línea 77) si el campo `contenedor` existe; si no, D2-2 lo agrega al cargador con su prueba** y el anillo B ejecuta esos casos con el oráculo SQLite de D2-2.
- No borrar ni debilitar pruebas. Un caso que no se puede traducir queda en `tests/corpus/migrar_pendientes.yaml` con su motivo, no se quita del corpus.
- Archivos de menos de 300 líneas. Ya pasan o rozan 300: `src/sgm/talend_item/desde_plan.py` (859), `src/sgm/migrar/interprete.py` (1103) y `src/sgm/talend_item/desde_plan_nodos.py` (299: no puede crecer, toda lógica nueva de lectura va a módulos nuevos y en ese archivo solo se agrega una llamada). `src/sgm/ir/lower_procs.py` (266) tampoco crece: `PROC IMPORT` y `PROC EXPORT` se extraen primero a `lower_procs_archivos.py` (D2-6, paso propio, sin cambio de comportamiento).
- Código e identificadores en inglés (los nombres de operadores de `operadores.py` están en español y se conservan); comentarios, docstrings y mensajes en español.
- Después de cada tarea: `uv run python -m pytest -q` y `uv run ruff check src tests tools` en verde. Para iterar se corre solo el archivo de la tarea (`-p no:cacheprovider`); la suite completa se corre al cerrar cada tarea.
- Secretos: nunca copiar a un contexto, a un `.item` ni a un pendiente la contraseña de un `SIGNON`, un `CONNECT` o un `FILENAME FTP`; se reemplaza por `'***'`. `sgm secretos` sobre el paquete migrado debe dar cero hallazgos (la única excepción vigente es el marcador `"sgm_ref"` de `tFileInputExcel`, `docs/secretos.md`).
- Studio: se usa en D2-2, D2-3, D2-6, D2-7, D2-10 y en el lote de cierre (D2-Gate), con `tools/validar_caso_studio.py <caso>` y `tools/corpus_studio.py lote ...`. Si `sgm studio salud` no conecta, no reinstalar nada ni cambiar `talend-mcp` (ver `docs/guia-validacion-studio.md`, sección 7): la tarea queda con «lote C pendiente» y su motivo, y no se cuenta como pasada. Las plantillas de componentes que faltan en `src/sgm/talend_item/plantillas/` (`tFileInputPositional`, `tFileOutputExcel`, `tPostgresqlInput`, `tFTPGet`) se extraen de un Job real de Studio con `tools/contenedores/extraer_plantillas_talend.py` (leer su `--help` antes); sin Studio la tarea deja `P-COMPONENTE-SIN-PLANTILLA` y no inventa los parámetros del `.item`.

## Review Focus

- **El tipo de una columna leída no se adivina:** `PROC IMPORT` de CSV, de DLM y de Excel decide el tipo mirando filas (`GUESSINGROWS`, p. 1388) o el formato de la celda; el SAS de un programa no lo demuestra. El esquema sale de la muestra (`--muestra`), de `LENGTH`/`INFORMAT` del programa o de la ficha de decisiones, y un tipo que ninguna de las tres fija queda `pendiente` con su motivo. Tests en D2-6 y D2-8.
- **Faltantes al leer:** con `DSD`, dos delimitadores seguidos son un faltante; con `MISSOVER` una línea corta deja faltantes los campos que faltan, y sin `MISSOVER` ni `TRUNCOVER` SAS sigue leyendo en la línea siguiente (`FLOWOVER`, por omisión). Un lector de Talend que no reproduce esto cambia el número de filas. Tests en D2-9 y D2-10.
- **Formatos de fecha y número no son `String.valueOf`:** un informat de fecha devuelve días desde el 1 de enero de 1960, un informat con `d` y sin punto decimal en el dato divide por `10**d`, y el formato de salida justifica a la derecha en un ancho fijo. Tests en D2-12 a D2-14.
- **Conexión compartida y sin secretos:** un `LIBNAME` o un `CONNECT` abre una sola conexión que reutilizan todos los pasos que la nombran; host, puerto y base viajan por contexto (`context.<motor>_host`, ...), `DEV` apunta a los contenedores y `Default`, `QA` y `PROD` quedan vacíos. Tests en D2-2 a D2-4.
- **Un Job parcial nunca se emite:** si una lectura, escritura o conexión no se puede demostrar (plantilla ausente, opción sin página, ruta dinámica), el paso queda como pendiente con código y el caso en `migrar_pendientes.yaml`; nunca un componente con parámetros supuestos.
- **Ningún pase nuevo puede cambiar la firma de los Jobs ya validados** en `L0` a `L3` (los `test_golden*.py` y `test_ir_operadores_corpus.py` deben seguir idénticos).

---

## Parte I. Bases y paso directo (prioridad: es lo que más programas desbloquea)

### Task D2-1: Línea base medida de entrada y salida (serie `n`)

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\linea_base_es.py`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_linea_base_es.py`

**Interfaces:**
- Consumes: `todos_los_casos(corpus: Path) -> list[Caso]` (`tools/corpus_lib/caso.py:216`), el campo `construcciones` de cada `caso.yaml` y `tests/corpus/migrar_pendientes.yaml`.
- Produces:
  ```python
  CONSTRUCCIONES_ES: tuple[str, ...]  # "PROC IMPORT", "PROC EXPORT", "INFILE", "INPUT", "FILE", "PUT", "LIBNAME",
                                      # "FILENAME", "CONNECT TO", "RSUBMIT", "PROC UPLOAD", "PROC DOWNLOAD",
                                      # "DBMS=XLSX", "DBMS=XLS", "GUESSINGROWS", "INFORMAT", "FORMAT"
  def medir(corpus: Path, programas: Sequence[Path] = ()) -> dict:
      """Por construccion de E/S: casos del corpus que la usan, casos pendientes con su codigo y
      usos en los `programas` dados (conteo por expresion regular sobre el texto, sin nombrar
      ningun programa). Salida JSON en `out/linea_base_es.json` (no versionada)."""
  ```

- [ ] **Step 1: Write the failing test.** Con un corpus mínimo en `tmp_path` (un `L0` con `construcciones: [PROC IMPORT, KEEP]` y otro con `[INFILE, INPUT]`) y un programa de texto `CONNECT TO impala (dsn=x); ... CONNECT TO impala (dsn=x);`, `medir(tmp_path, [programa])["construcciones"]["PROC IMPORT"] == {"casos": 1, "pendientes": {}, "usos_programas": 0}` y `["CONNECT TO"]["usos_programas"] == 2`; un caso listado en un `migrar_pendientes.yaml` mínimo con `P-FORMATO-SIN-SOPORTE` aparece en `pendientes` de su construcción.
- [ ] **Step 2: Run test to verify it fails.** `uv run python -m pytest tests/unit/test_linea_base_es.py -q -p no:cacheprovider`; esperado: no existe el módulo.
- [ ] **Step 3: Implement** `medir` leyendo los `caso.yaml` con `corpus_lib.caso`; los programas se leen solo si se pasan por línea de comandos (`uv run python tools/linea_base_es.py tests/corpus --programa tests/fixtures/sas/client/client_large.sas`). Sin dependencias nuevas.
- [ ] **Step 4: Run test to verify it passes**, correr la herramienta sobre `tests/corpus` y el programa grande, y pegar en `PROGRESS.md` la línea base de este plan: casos de `L0` por construcción de E/S, pendientes por código, y usos en el programa grande (esperado al redactar: unos 125 `CONNECT TO impala`, 116 líneas con `RSUBMIT`, 22 `PROC UPLOAD`, 22 `PROC EXPORT`, 9 `PROC IMPORT`, 4 `PROC DOWNLOAD`; si el conteo difiere, anotar el real).
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N n: linea base medida de entrada y salida` (con la línea `Co-Authored-By`).

---

### Task D2-2: Paso directo `CONNECT TO impala ... FROM CONNECTION TO` a un lector con SQL literal (MG-P2-05, parte 1; serie `n`)

El programa grande tiene unas 125 sentencias `CONNECT TO impala`. El frontend ya reconoce `select ... from connection to <motor> (...)` (`src/sgm/frontend/sql.py`, `SqlStatement(kind="select_passthrough", engine, inner_sql, target)`) y el lowering ya lo baja a un operador `read` con `params {"sql", "engine", "outputs"}` y `placement="db:impala"` (`lower_sql.py:42-51`). Lo que falta es el **emisor**: hoy `desde_plan.py` solo emite `exec_sql` (`tImpalaRow`, `_sql_impala`, línea 479) y no hay componente de lectura de base con SQL literal. Páginas (`sqlproc.pdf`): `CONNECT Statement` (p. 287), `CONNECTION TO Component` (p. 392), `DISCONNECT Statement` (p. 301), `Pass-Through Example` (p. 214). El SQL entre paréntesis no es SAS: viaja **literal** al motor (decisión: no se traduce ni se normaliza, `sqlproc`, p. 213: «What Is the Pass-Through Facility?»).

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\talend_item\desde_plan_paso_directo.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\interprete_paso_directo.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\talend_item\desde_plan.py` (solo la rama de `read` con `placement` `db:`: una llamada, en `_emitir` cerca de la línea 794; **zona del emisor del carril de Andres**: avisar antes y, si tiene cambios sin commitear en ese archivo, aplicar el cambio sobre su versión)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\interprete.py` (una línea en la rama `read` de la línea 978: delegar a `interprete_paso_directo.leer`; sin extraer nada más)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\corpus_lib\caso.py` (solo si `contenedor` no existe: campo opcional con valores `impala` o `postgres`)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\L0\l0_16_paso_directo_impala\{caso.yaml, programa.sas, entradas\sgmtest_d2.vehiculos.csv, esperado\por_marca.csv}`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\rules\sas\catalogo\sentencias-proc-sql.yaml` (entradas `connect-statement` p. 287, `connection-to` p. 392 y `disconnect-statement` p. 301, `estado: reconocida`, nota «el SQL interior viaja literal»; si ya existen, solo cambia el `estado`)
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_paso_directo.py`

**Interfaces:**
- Consumes: `nodo_desde_plantilla(componente, unico, x, y, valores, tablas, columnas, ruta_java)` (`sgm.talend_item.plantillas`; la plantilla `tImpalaInput.json` ya existe); `java(valor: str) -> str` (`sgm.talend_item.jobs_diseno`); `PendienteMigracion(codigo, mensaje, linea)` (`sgm.migrar.esquemas`); `columnas_talend(columnas: list[Column]) -> list[Columna]` (`desde_plan_nodos.py:56`); `parametros_conexion(en_contexto: bool) -> dict[str, str]` y `VARIABLES_BASE` del Plan K (K-4, `desde_plan_conexion.py`); `Operator.params` con `sql`, `engine`, `outputs`.
- Produces:
  ```python
  # desde_plan_paso_directo.py
  def nodo_paso_directo(
      op: Operator, esquema: list[Column], unico: str, x: int, y: int, ruta_java: str | None = None
  ) -> Resultado:
      """`read` de motor (`placement` `db:impala`) como `tImpalaInput` con `QUERY` = el SQL literal
      entre comillas Java y `HOST`/`PORT`/`DBNAME` desde el contexto. Sin esquema demostrado
      (el SELECT interior no dice los tipos): `P-ESQUEMA-VACIO`. Con `&` en el SQL:
      `P-PASO-DIRECTO-MACRO` (lo resuelve el expansor del Plan E). Motor distinto de impala y
      postgres: `P-MOTOR-SIN-SOPORTE` con el nombre del motor."""

  # interprete_paso_directo.py
  def leer(op: Operator, entradas: dict[str, list[dict]]) -> list[dict]:
      """Anillo B: ejecuta el SQL literal con `sqlite3` en memoria sobre las tablas
      `<base>.<tabla>` que el caso aporta en `entradas/` (nombre de archivo
      `<base>.<tabla>.csv`). Solo SQL portable (`ir/sql_portability.py`); si no lo es,
      `NoSoportadoEnInterprete('paso_directo', motivo)`."""
  ```

**Caso `L0/l0_16_paso_directo_impala` (`capa: C`, `contenedor: impala`, `estado: pendiente_revision` hasta confirmar el tipo de `n` y `total` contra Impala; razonamiento: «sqlproc, p. 287, 392 y 213: el SQL interior se evalúa en el motor»).**
```sas
PROC SQL;
  CONNECT TO IMPALA (DSN=IMPALAP);
  CREATE TABLE WORK.por_marca AS
  SELECT * FROM CONNECTION TO IMPALA
  (SELECT marca, COUNT(*) AS n, SUM(precio) AS total
     FROM sgmtest_d2.vehiculos WHERE anio = 2026 GROUP BY marca);
  DISCONNECT FROM IMPALA;
QUIT;
```
`entradas/sgmtest_d2.vehiculos.csv` (`marca,anio,precio`): `Acura,2026,10` / `Acura,2026,30` / `Audi,2026,20` / `Audi,2025,99` / `BMW,2026,5`. Esperado a mano, `esperado/por_marca.csv` (`orden_relevante: false`): `marca,n,total` / `Acura,2,40` / `Audi,1,20` / `BMW,1,5` (la fila de `Audi` de 2025 queda fuera del `WHERE`). Invariantes: `filas(por_marca) == 3` y `sum(total) == 65`.

- [ ] **Step 1: Medir hoy.** Migrar el caso con `uv run python -m sgm.cli migrar tests/corpus/L0/l0_16_paso_directo_impala/programa.sas --out out/d2_2` y anotar en `PROGRESS.md` qué pendiente da el `read` de motor (esperado: sin componente de lectura de base) y cuántos `CONNECT TO` del programa grande son `select_passthrough` y cuántos `execute by` (`uv run python tools/linea_base_es.py ...` de D2-1): solo los primeros se resuelven aquí.
- [ ] **Step 2: Write the failing tests** en `test_paso_directo.py`: (a) `nodo_paso_directo` sobre un `read` con `sql="select marca, count(*) as n from sgmtest_d2.vehiculos group by marca"` devuelve un nodo `tImpalaInput` cuyo `QUERY` es ese texto entre comillas Java, con `"` interiores escapados, y ninguna cadena `IMPALAP` (el DSN no se copia); (b) con el esquema vacío da `P-ESQUEMA-VACIO` y `nodo is None`; (c) con `&ANIO.` en el SQL da `P-PASO-DIRECTO-MACRO`; (d) con `engine="oracle"` da `P-MOTOR-SIN-SOPORTE` con la palabra `oracle`; (e) `leer` sobre el caso devuelve las tres filas de `esperado/por_marca.csv`; (f) `leer` con una función que SQLite no tiene (`ndv(x)`) lanza `NoSoportadoEnInterprete`.
- [ ] **Step 3: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_paso_directo.py -q -p no:cacheprovider`.
- [ ] **Step 4: Implement** ambos módulos. El esquema de la lectura sale del `SELECT` interior solo cuando cada columna tiene alias o nombre simple y la tabla de origen tiene esquema conocido (`--esquemas`/`--muestra`); un `COUNT(*)` es `Long` y un `SUM` de columna `Double` es `Double`; lo demás queda sin tipo. Anotar en el catálogo (`sqlproc`, p. 287, 392, 301) y escribir en `PROGRESS.md`, «Decisiones», que el SQL interior no se normaliza (alternativa descartada: pasarlo por `sqlglot` para portarlo; qué cambia: el motor remoto es el que lo evalúa y una reescritura puede cambiar su resultado).
- [ ] **Step 5: Run** los tests, el golden (`tests/unit/test_golden*.py`, sin cambios) y `tests/unit/test_migrar_corpus_anillo_b.py -k l0_16`. `uv run ruff check src tests tools`.
- [ ] **Step 6: Contenedor y Studio (si hay Docker y Studio).** Con K-4 integrado: `uv run python tools/contenedores/cargar_tablas.py --csv tests/corpus/L0/l0_16_paso_directo_impala/entradas/sgmtest_d2.vehiculos.csv --tabla sgmtest_d2.vehiculos --ejecutar`, migrar con `--contexto-dev env/contexto_dev.json` y ejecutar con `uv run python tools/validar_caso_studio.py l0_16_paso_directo_impala`; esperado `1 casos, 1 coinciden`. Sin Docker: «contenedor pendiente»; sin Studio: «lote C pendiente», cada uno con su motivo.
- [ ] **Step 7: Commit.** `hito N n: paso directo CONNECT TO impala a lector con SQL literal`.

---

### Task D2-3: Paso directo a Postgres y conexión compartida entre `execute by` y `select from connection` (MG-P2-05, parte 2; serie `n`)

La decisión MG-D05 pone Impala, Postgres y archivos como destinos primero. Esta tarea suma Postgres al paso directo y hace que una sola sentencia `CONNECT` alimente a todos los pasos que la usan (hoy cada `exec_sql` crea su propio `tImpalaRow` con la conexión vacía). `tools/contenedores/postgres/` ya existe; su contraseña de contenedor vive en su compose y **no** se copia a ningún contexto.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\talend_item\desde_plan_conexiones.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\talend_item\desde_plan_paso_directo.py` (creado en D2-2: rama `postgres`)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\talend_item\desde_plan_contextos.py` (108 líneas; K-4 ya le suma `dev`; aquí se generaliza a un motor por conexión)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\env\contexto_dev_postgres.json`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\L0\l0_17_paso_directo_postgres\{caso.yaml, programa.sas, entradas\public.cuentas.csv, esperado\activos.csv}`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_conexiones_compartidas.py`

**Interfaces:**
- Consumes: `VARIABLES_BASE`, `parametros_conexion(en_contexto)` y `cargar_contexto_dev(ruta)` (K-4, `desde_plan_conexion.py`); `contextos_de_plan(plan: Plan, dev: dict[str, str] | None = None)`; `ParametroContexto(nombre, tipo="id_String", valor="", comentario="", pedir=False)`; `Operator.params["engine"]`.
- Produces:
  ```python
  # desde_plan_conexiones.py
  @dataclass(frozen=True)
  class Conexion:
      alias: str            # el nombre que pone el SAS (`CONNECT TO impala AS c1`) o el motor
      motor: str            # "impala" | "postgres"
      variables: tuple[str, ...]   # ("impala_host", "impala_puerto", "impala_base", "impala_jdbc_extra")
  def conexiones_de_plan(plan: Plan) -> list[Conexion]:
      """Una por cada `connect` distinto (alias y motor). Los `exec_sql` y los `read` de motor
      comparten la de su alias; sin `connect` previo, la del motor."""
  def variables_de_motor(motor: str) -> tuple[str, ...]:
      """impala -> VARIABLES_BASE; postgres -> ("pg_host", "pg_puerto", "pg_base"). Otro motor: ValueError."""
  ```
  `env/contexto_dev_postgres.json`: `{"_nota": "Contenedor sgmtest_ desechable; sin credenciales.", "pg_host": "localhost", "pg_puerto": "5432", "pg_base": "sgmtest"}`. La contraseña del contenedor entra al Job solo por el parámetro de ejecución `--context_param pg_clave=...` desde una variable de entorno, y el nombre `pg_clave` casa con la regla de secretos (se escribe vacío en el contexto).

**Caso `L0/l0_17_paso_directo_postgres` (`capa: C`, `contenedor: postgres`, `estado: pendiente_revision`; razonamiento: «sqlproc, p. 287 y 392; opciones de CONNECT: P-CONEXION-OPCIONES»).**
```sas
PROC SQL;
  CONNECT TO POSTGRES (SERVER=localhost DATABASE=sgmtest USER=sgmtest PASSWORD='***');
  CREATE TABLE WORK.activos AS
  SELECT * FROM CONNECTION TO POSTGRES
  (SELECT id, saldo FROM public.cuentas WHERE estado = 'A' ORDER BY id);
  DISCONNECT FROM POSTGRES;
QUIT;
```
`entradas/public.cuentas.csv` (`id,saldo,estado`): `1,100.5,A` / `2,0,I` / `3,40,A`. Esperado a mano, `esperado/activos.csv` (`orden_relevante: true`): `id,saldo` / `1,100.5` / `3,40` (el `ORDER BY` del SQL interior fija el orden; la fila inactiva queda fuera).

- [ ] **Step 1: Write the failing tests** en `test_conexiones_compartidas.py`: (a) un programa con un `CONNECT TO impala` seguido de un `execute by impala` y un `select from connection to impala` da **una** `Conexion` y los dos nodos usan las mismas cuatro variables de contexto; (b) con dos `CONNECT` a motores distintos da dos `Conexion` y `contextos_de_plan` suma las siete variables (`impala_*` y `pg_*`) a los cuatro grupos, con valor solo en `DEV`; (c) el `.item` migrado de `l0_17` no contiene `sgmtest`, `localhost` ni `PASSWORD` con valor, y el pendiente nombra `P-CONEXION-OPCIONES` y repite el texto de los argumentos con la contraseña ya como `'***'`; (d) `variables_de_motor("oracle")` lanza `ValueError`; (e) `sgm secretos` sobre el paquete migrado da cero hallazgos.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_conexiones_compartidas.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement.** Plantilla de `tPostgresqlInput`: si `src/sgm/talend_item/plantillas/tPostgresqlInput.json` no existe, extraerla de Studio (`tools/contenedores/extraer_plantillas_talend.py`); sin Studio, `nodo_paso_directo` devuelve `P-COMPONENTE-SIN-PLANTILLA` para el motor `postgres` y los pasos (a) a (d) se prueban con Impala. El host, el puerto y la base van a `context.pg_*`; el usuario y la contraseña no se emiten (`PASS` queda `((String)null)` como en K-4).
- [ ] **Step 4: Run** los tests, `tests/unit/test_push_db.py`, `tests/unit/test_desde_plan_contextos.py`, `tests/unit/test_contexto_dev.py` (K-4) y el golden. `uv run ruff check src tests tools`.
- [ ] **Step 5: Contenedor y Studio.** `docker compose -f tools/contenedores/postgres/docker-compose.yml up -d` (verificar el nombre del archivo en esa carpeta), cargar `public.cuentas` (según su README), migrar con `--contexto-dev env/contexto_dev_postgres.json` y ejecutar `uv run python tools/validar_caso_studio.py l0_17_paso_directo_postgres`. Sin Docker o sin Studio: «contenedor pendiente» o «lote C pendiente» con el motivo.
- [ ] **Step 6: Commit.** `hito N n: paso directo a Postgres y conexion compartida por alias`.

---

### Task D2-4: `LIBNAME` a bases (Impala y Postgres) con conexión compartida y contexto (MG-P2-04, parte 1; serie `n`)

Hoy `LIBNAME` se lowerea con `_config` (un operador de configuración que no hace nada) y el catálogo lo marca `no_reconocida` (`sentencias-data-step.yaml`, `libname-statement`, `lestmtsref`, p. 233). Una tabla `lz.cuentas` leída en un `DATA` o en un `PROC SQL` no sabe a qué base pertenece. Esta tarea reconoce la forma `LIBNAME ref motor opciones;` y resuelve cada `ref.tabla` a la conexión de D2-3. Lo que **no** se puede demostrar: el esquema de la base (`SCHEMA=` es de SAS/ACCESS, `P-CONEXION-OPCIONES`). Por eso la correspondencia `libref -> base` la declara una persona en `decisiones/<programa>.libnames.yaml` (`lz: {motor: impala, base: <nombre>}`) y, sin esa decisión, la lectura queda `Pendiente: P-LIBNAME-BASE`.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\frontend\libnames.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\ir\bibliotecas.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\ir\lower.py` (solo la rama `Libname` de la línea 157: registrar la biblioteca en el `Builder` además de `_config`)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\L0\l0_18_libname_base\{caso.yaml, programa.sas, decisiones.yaml, entradas\sgmtest_d2.vehiculos.csv, esperado\caros.csv}`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\rules\sas\catalogo\sentencias-data-step.yaml` (`libname-statement`: `reconocida`, nota con el alcance)
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_libnames.py`

**Interfaces:**
- Consumes: `Libname(name: str, value: str, line, end_line, text)` (`sgm.frontend.steps_tipos`, línea 67); `Builder` (`sgm.ir.builder`); `qualify(dataset)` (`sgm.ir.builder`); `Conexion` y `conexiones_de_plan` (D2-3).
- Produces:
  ```python
  # frontend/libnames.py
  @dataclass(frozen=True)
  class InfoLibname:
      nombre: str                 # el libref, en minusculas
      motor: str | None           # "impala" | "postgres" | None si es una ruta
      ruta: str | None           # carpeta literal si el LIBNAME apunta a una ruta
      opciones: str              # texto de las opciones, con PASSWORD=/PW=/PASS= como '***'
      linea: int
  def info_libname(item: Libname) -> InfoLibname:
      """`LIBNAME a '/ruta';` -> ruta; `LIBNAME a IMPALA DSN=x;` -> motor `impala`; un motor
      desconocido -> motor con su nombre (la resolucion lo rechaza despues). `CLEAR` y `_ALL_`
      devuelven `InfoLibname(nombre, None, None, 'clear', linea)`."""
  # ir/bibliotecas.py
  def resolver_biblioteca(tabla: str, bibliotecas: Mapping[str, InfoLibname],
                          decisiones: Mapping[str, dict]) -> tuple[str, str] | None:
      """`lz.cuentas` -> `("impala", "<base>.cuentas")` si la biblioteca es de base y la decision
      declara su base; `None` si es WORK, una ruta o no hay decision (el pendiente `P-LIBNAME-BASE`
      lo emite quien llama)."""
  ```

**Caso `L0/l0_18_libname_base` (`capa: C`, `contenedor: impala`, `estado: pendiente_revision`; razonamiento: «lestmtsref, p. 233: la forma del LIBNAME; el significado de SCHEMA= no tiene página (P-CONEXION-OPCIONES), la base sale de decisiones.yaml»).**
```sas
LIBNAME lz IMPALA DSN=IMPALAP SCHEMA=sgmtest_d2;
DATA WORK.caros;
  SET lz.vehiculos;
  WHERE precio > 15;
  KEEP marca precio;
RUN;
LIBNAME lz CLEAR;
```
`decisiones.yaml`: `libnames: {lz: {motor: impala, base: sgmtest_d2}}`. Entradas: la misma `sgmtest_d2.vehiculos.csv` de D2-2. Esperado a mano, `esperado/caros.csv`: `marca,precio` / `Acura,30` / `Audi,20` / `Audi,99` (precio mayor que 15; `Acura,10` y `BMW,5` quedan fuera).

- [ ] **Step 1: Write the failing tests.** `info_libname` de `LIBNAME lz IMPALA DSN=IMPALAP SCHEMA=sgmtest_d2;` da `motor == "impala"`, `ruta is None` y `opciones` sin el texto `PASSWORD`; de `LIBNAME datos 'C:\datos';` da `ruta == "C:\\datos"` y `motor is None`; de `LIBNAME x POSTGRES PASSWORD=abc123;` el texto `abc123` no aparece en `opciones` ni en el `repr`; `resolver_biblioteca("lz.vehiculos", {"lz": ...}, {"lz": {"motor": "impala", "base": "sgmtest_d2"}}) == ("impala", "sgmtest_d2.vehiculos")` y sin decisión `None`; el caso migra el `SET lz.vehiculos` a un `tImpalaInput` con `SELECT * FROM sgmtest_d2.vehiculos` y el `WHERE` como filtro del Job, y sin `decisiones.yaml` el pendiente es `P-LIBNAME-BASE`.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_libnames.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement** `libnames.py` (expresiones regulares sobre el texto de la sentencia; sin interpretar las opciones) y `bibliotecas.py`; leer `decisiones.yaml` con el mismo mecanismo que usan las demás decisiones por programa (`grep -rn "decisiones" src/sgm/cli_migrar.py` para ubicarlo). La lectura de una tabla de base entra por el mismo `tImpalaInput` de D2-2, con el SQL que arma el emisor (`SELECT <columnas usadas> FROM <base>.<tabla>`; las columnas salen de `_columnas_usadas`, `src/sgm/migrar/esquemas.py:69`).
- [ ] **Step 4: Run** los tests, `tests/unit/test_corpus_l0*.py` si existen, el golden y `uv run ruff check src tests tools`.
- [ ] **Step 5: Contenedor y Studio.** Igual que D2-2, Step 6, con `l0_18_libname_base`. Sin ellos: «contenedor pendiente» o «lote C pendiente».
- [ ] **Step 6: Commit.** `hito N n: LIBNAME a bases con la base declarada por decision y conexion compartida`.

---

### Task D2-5: `LIBNAME` a rutas y registro de bibliotecas con variable de contexto (MG-P2-04, parte 2; serie `n`)

Cierra MG-P2-04. Una biblioteca de ruta (`LIBNAME datos '/carpeta';`) no produce datos por sí sola: su efecto aparece cuando un programa lee o escribe `datos.tabla`, que es la decisión MG-D03 de D2-18. Esta tarea deja listo el registro: cada biblioteca de ruta pasa a una **variable de contexto** `ruta_lib_<nombre>` (un solo lugar para cambiarla por ambiente, como `ruta_<tabla>` de `rutas_de_plan`) y el pendiente de una biblioteca sin ruta literal (con `&`) es `P-LIBNAME-RUTA-DINAMICA`. **No suma caso propio** (la biblioteca sola no lee ni escribe nada); su caso ejecutable es `l0_31_biblioteca_permanente` de D2-18, y esta tarea lo declara en su prueba como el consumidor.

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\ir\bibliotecas.py` (creado en D2-4)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\talend_item\desde_plan_contextos.py`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_bibliotecas_ruta.py`

**Interfaces:**
- Consumes: `InfoLibname`, `info_libname` (D2-4); `rutas_de_plan(plan: Plan) -> dict[str, str]` y `contextos_de_plan(plan, dev=None)` (`desde_plan_contextos.py:38` y `:67`); `ruta(literal: str | None) -> str` (`desde_plan_nodos.py:61`).
- Produces:
  ```python
  # ir/bibliotecas.py
  def bibliotecas_de_programa(items: Iterable) -> dict[str, InfoLibname]:
      """Todas las `LIBNAME` del programa, la ultima por libref (un `CLEAR` la quita)."""
  def rutas_de_bibliotecas(bibliotecas: Mapping[str, InfoLibname]) -> dict[str, str]:
      """libref -> nombre de la variable de contexto (`ruta_lib_<libref>`), solo las de ruta."""
  ```

- [ ] **Step 1: Write the failing tests.** (a) `bibliotecas_de_programa` de `LIBNAME a 'C:\x'; LIBNAME b IMPALA DSN=z; LIBNAME a CLEAR;` devuelve solo `b`; (b) `rutas_de_bibliotecas` de `LIBNAME datos '/d';` da `{"datos": "ruta_lib_datos"}`; (c) `contextos_de_plan` suma `ruta_lib_datos` a los cuatro grupos con el valor literal en `Default` y vacío en los demás (el mismo criterio que `ruta_<tabla>`); (d) `LIBNAME datos "&dir.";` da `P-LIBNAME-RUTA-DINAMICA`; (e) una biblioteca de ruta no cambia el golden de los casos sin `LIBNAME`.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_bibliotecas_ruta.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement** y conectar a `contextos_de_plan` (una función auxiliar nueva en `desde_plan_contextos.py`; el archivo queda bajo 150 líneas).
- [ ] **Step 4: Run** los tests, `tests/unit/test_desde_plan_contextos.py`, `tests/unit/test_talend_contextos.py`, el golden, `tests/unit/test_catalogo_sas.py` y `uv run ruff check src tests tools`.
- [ ] **Step 5: Commit.** `hito N n: bibliotecas de ruta con variable de contexto`.

---
## Parte II. Archivos: Excel, `PROC IMPORT`/`EXPORT`, `INFILE/INPUT` y `FILE/PUT`

### Task D2-6: `PROC IMPORT` de XLSX y XLS con `SHEET`, contraseña de plantilla y lector propio (MG-P2-01, parte 1; serie `n`)

**Estado hoy:** `nodo_lectura` (`desde_plan_nodos.py:162`) ya emite `tFileInputExcel` para `DBMS=XLSX` y `XLS` con `SHEETNAME`, `HEADER` y `VERSION_2007`, y `tests/unit/test_mg_p2_excel.py` fija la clasificación. Faltan tres cosas: (1) el emisor **no** pone `PASSWORD`, y el hallazgo del hito 63 (`docs/guia-validacion-studio.md`, línea 110) dice que `tFileInputExcel` con `VERSION_2007` no compila con `PASSWORD` vacío ni con `***`; el marcador vigente es `"sgm_ref"` (`docs/secretos.md`, línea 31); (2) el intérprete no lee `.xlsx`, así que ningún caso de Excel corre en B; (3) `PROC IMPORT` y `PROC EXPORT` viven en `lower_procs.py` (266 líneas, no puede crecer). Páginas: `proc.pdf`, `PROC IMPORT Statement` (p. 1380: valores de `DBMS=`, `SHEET=`) y `GETNAMES Statement` (p. 1387). **El tipo de cada columna de un Excel no tiene página** (la importación de Excel es de SAS/ACCESS Interface to PC Files, fuera de las 13 guías): las columnas salen de la muestra o quedan `P-TIPO-EXCEL`.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\ir\lower_procs_archivos.py` (extraído de `lower_procs.py`: `_opciones`, `_read_file`, `_write_file`, `_getnames`, `_dbms`, `_entero`)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\ir\lower_procs.py` (solo importa lo extraído)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\talend_item\desde_plan_excel.py` (rama Excel de `nodo_lectura` movida aquí)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\talend_item\desde_plan_nodos.py` (una llamada; baja de 299 líneas)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\lector_xlsx.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\corpus_lib\xlsx_minimo.py` (escribe un `.xlsx` mínimo y determinista: ZIP con fechas fijas, celdas de texto en línea y numéricas)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\L0\l0_19_importar_xlsx_hoja\{caso.yaml, programa.sas, entradas\ventas.xlsx, esperado\total.csv}`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\rules\sas\catalogo\procs-usados.yaml` (`import`: `estado: reconocida`, nota «CSV, DLM y XLSX; XLS emitido sin ejecución; tipos de Excel: P-TIPO-EXCEL»)
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_importar_excel.py`

**Interfaces:**
- Consumes: `nodo_desde_plantilla(...)`, `java(valor)`, `Resultado(nodo, columnas, pendientes)` y `ruta(literal)` (`desde_plan_nodos.py`); `EXCEL` (el conjunto de `dbms` de Excel de `nodo_lectura`); `lower_proc(step: Proc, ev: Evidence, b: Builder) -> None` (`lower_procs.py`).
- Produces:
  ```python
  # lector_xlsx.py
  def leer_xlsx(ruta: Path, hoja: str | None = None) -> tuple[list[str], list[list[str]]]:
      """(encabezado, filas) de una hoja, como texto. `hoja=None` = la primera del libro (el
      SAS lee la primera por omision: verificar en p. 1380). Hoja inexistente: KeyError con la
      lista de hojas. Celda numerica: el texto de su valor sin ceros de mas (`2.0` -> `2`)."""
  # xlsx_minimo.py
  def escribir_xlsx(ruta: Path, hojas: Mapping[str, Sequence[Sequence[object]]]) -> None: ...
  # desde_plan_excel.py
  def nodo_lectura_excel(op, esquema, unico, x, y, ruta_java=None) -> Resultado:
      """Igual que la rama actual, mas `PASSWORD` = `"sgm_ref"` cuando `VERSION_2007`
      (hallazgo del hito 63) y `P-TIPO-EXCEL` por cada columna sin tipo en el esquema."""
  ```

**Caso `L0/l0_19_importar_xlsx_hoja` (`capa: C`, `estado: revisado`, razonamiento: «proc, p. 1380 (DBMS=XLSX, SHEET=) y p. 1387 (GETNAMES=YES por omisión)»).**
```sas
PROC IMPORT DATAFILE='.../entradas/ventas.xlsx' OUT=WORK.ventas DBMS=XLSX REPLACE;
  SHEET='Datos';
  GETNAMES=YES;
RUN;
DATA WORK.total;
  SET WORK.ventas;
  total = unidades * precio;
  KEEP sku total;
RUN;
```
`entradas/ventas.xlsx`, generado con `escribir_xlsx` (una prueba exige los mismos bytes al regenerarlo): hoja `Datos` (`sku,unidades,precio`): `A-1,2,10` / `B-2,3,5` / `C-3,0,7`; hoja `Otra` (`sku,unidades,precio`): `Z-9,1,1` (prueba que `SHEET=` elige la hoja). Esperado a mano, `esperado/total.csv`: `sku,total` / `A-1,20` / `B-2,15` / `C-3,0`. Invariante: `filas(total) == 3`.

- [ ] **Step 1: Extraer sin cambiar comportamiento.** Mover a `lower_procs_archivos.py` las seis funciones indicadas y a `desde_plan_excel.py` la rama de Excel. Antes de mover, `uv run python -m pytest -q -p no:cacheprovider tests/unit/test_mg_p2_excel.py tests/unit/test_golden.py tests/unit/test_golden_equivalencia.py tests/unit/test_migrar_corpus_anillo_b.py` y anotar el conteo; después, mismas pasadas. `wc -l` de `lower_procs.py` y `desde_plan_nodos.py`: bajan. Commit aparte: `hito N n: PROC IMPORT/EXPORT y la rama Excel en modulos propios, sin cambio de comportamiento`.
- [ ] **Step 2: Write the failing tests** en `test_importar_excel.py`: (a) `escribir_xlsx` dos veces da los mismos bytes y `leer_xlsx(ruta, "Datos")` devuelve `(["sku","unidades","precio"], [["A-1","2","10"], ["B-2","3","5"], ["C-3","0","7"]])`; (b) `leer_xlsx(ruta)` sin hoja devuelve la primera (`Datos`) y con `"Nada"` lanza `KeyError` que nombra `Datos` y `Otra`; (c) `nodo_lectura_excel` con `dbms="xlsx"` deja `PASSWORD == '"sgm_ref"'`, y con `dbms="xls"` no pone `PASSWORD` y `VERSION_2007 == "false"`; (d) con `guessingrows` el pendiente `P-GUESSINGROWS` sigue (la guía dice que solo vale en delimitados, p. 1388); (e) una columna sin tipo en el esquema da `P-TIPO-EXCEL` con su nombre; (f) el caso coincide en el anillo B con `esperado/total.csv`; (g) `sgm secretos` sobre el paquete: cero hallazgos.
- [ ] **Step 3: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_importar_excel.py -q -p no:cacheprovider`.
- [ ] **Step 4: Implement** `leer_xlsx` con `zipfile` y `xml.etree.ElementTree` (`xl/workbook.xml` para las hojas y su `r:id`, `xl/_rels/workbook.xml.rels` para el archivo de cada hoja, `xl/sharedStrings.xml` si existe) y la rama de `read_file` del intérprete con una línea en `interprete.py` (rama `read_file`, línea 978): `dbms == "xlsx"` usa `leer_xlsx`; `xls` lanza `NoSoportadoEnInterprete("xls", "formato binario 97-2003: el intérprete no lo lee")` y se anota `Pendiente: P-XLS-SIN-EJECUCION` en el catálogo (el emisor de XLS se prueba solo con una prueba unitaria, sin caso del corpus).
- [ ] **Step 5: Run** los tests, `tests/unit/test_mg_p2_excel.py`, el golden, `tests/unit/test_catalogo_sas.py` y `uv run ruff check src tests tools`.
- [ ] **Step 6: Studio.** `uv run python tools/validar_caso_studio.py l0_19_importar_xlsx_hoja`; esperado `1 casos, 1 coinciden`. Sin Studio: «lote C pendiente».
- [ ] **Step 7: Commit.** `hito N n: PROC IMPORT de XLSX con hoja, contrasena de plantilla y lector propio`.

---

### Task D2-7: `PROC EXPORT` a XLSX con `SHEET` y `tFileOutputExcel` (MG-P2-01, parte 2; serie `n`)

`nodo_escritura` (`desde_plan_nodos_escritura.py`, 96 líneas) intenta `tFileOutputExcel` y, si la plantilla no está disponible (línea 45), deja «falta la plantilla de tFileOutputExcel, extraída de un Job real». Verificado al redactar: `src/sgm/talend_item/plantillas/` no tiene `tFileOutputExcel.json`. Páginas (`proc.pdf`): `PROC EXPORT Statement` (p. 904), `PUTNAMES Statement` (p. 910; por omisión `YES`, verificar en esa página), `DELIMITER Statement` (p. 908). Documentación del componente: `docs/referencia/talend/tfileoutputexcel.md`.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\talend_item\plantillas\tFileOutputExcel.json` (extraída de Studio; ver Step 1)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\escritor_xlsx.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\ir\lower_procs_archivos.py` (creado en D2-6: `putnames` en el `write_file`)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\talend_item\desde_plan_nodos_escritura.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\L0\l0_20_exportar_xlsx\{caso.yaml, programa.sas, entradas\ventas.csv, esperado\ventas.Resumen.csv}`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_exportar_excel.py`

**Interfaces:**
- Consumes: `nodo_escritura(...)` (`desde_plan_nodos_escritura.py:11`); `disponibles()` (plantillas); `escribir_xlsx(ruta, hojas)` y `leer_xlsx(ruta, hoja)` (D2-6); `_write_file(step, ev, b, data)` (D2-6).
- Produces:
  ```python
  # escritor_xlsx.py
  def escribir_hoja(ruta: Path, hoja: str, encabezado: list[str] | None, filas: list[list[object]]) -> None:
      """Anillo B: escribe `ruta` con una hoja. `encabezado=None` = PUTNAMES=NO."""
  # lower_procs_archivos.py: nuevo parametro del write_file
  #   params["putnames"]: bool   # PUTNAMES=YES por omision
  ```
  El esperado de un archivo Excel se guarda como `esperado/<archivo>.<hoja>.csv` y el comparador lo lee con `leer_xlsx` (**verificar en `tools/corpus_lib/caso.py` cómo se declaran las salidas de archivo; si solo admite CSV, esta tarea agrega la rama por extensión `.xlsx` con su prueba**).

**Caso `L0/l0_20_exportar_xlsx` (`capa: C`, `estado: revisado`, razonamiento: «proc, p. 904 y 910: PUTNAMES=YES escribe los nombres de variable en la fila 1»).**
```sas
PROC IMPORT DATAFILE='.../entradas/ventas.csv' OUT=WORK.ventas DBMS=CSV REPLACE; GETNAMES=YES; RUN;
PROC EXPORT DATA=WORK.ventas OUTFILE='.../salida/ventas.xlsx' DBMS=XLSX REPLACE;
  SHEET='Resumen';
RUN;
```
`ventas.csv`: `sku,unidades` / `A-1,2` / `B-2,3`. Esperado a mano, `esperado/ventas.Resumen.csv`: `sku,unidades` / `A-1,2` / `B-2,3` (fila 1 con los nombres, dos filas de datos; hoja `Resumen`). Invariante: `filas(Resumen) == 2` sin contar el encabezado.

- [ ] **Step 1: Plantilla (Studio).** Con Studio abierto y un Job de prueba con un `tFileOutputExcel` (Excel 2007, `SHEETNAME`, `INCLUDEHEADER`): `uv run python tools/contenedores/extraer_plantillas_talend.py --help` y extraer la plantilla a `src/sgm/talend_item/plantillas/tFileOutputExcel.json`. Sin Studio: se omite y el emisor sigue devolviendo `P-COMPONENTE-SIN-PLANTILLA`; los pasos 2 a 5 prueban el intérprete y la decisión, y el caso queda en `migrar_pendientes.yaml` con ese código.
- [ ] **Step 2: Write the failing tests.** (a) `escribir_hoja(ruta, "Resumen", ["sku","unidades"], [["A-1",2],["B-2",3]])` y `leer_xlsx(ruta, "Resumen")` devuelven el encabezado y las dos filas; con `encabezado=None` la fila 1 son datos; (b) `_write_file` de `PROC EXPORT ... DBMS=XLSX; SHEET='Resumen'; PUTNAMES=NO;` da `putnames == False` y `sheet == "Resumen"`; sin `PUTNAMES`, `True`; (c) con la plantilla, `nodo_escritura` da `tFileOutputExcel` con `INCLUDEHEADER == "true"` y `SHEETNAME == '"Resumen"'`; sin plantilla, `P-COMPONENTE-SIN-PLANTILLA` y ningún Job parcial; (d) el caso coincide en el anillo B.
- [ ] **Step 3: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_exportar_excel.py -q -p no:cacheprovider`.
- [ ] **Step 4: Implement** `escritor_xlsx.py` (reutiliza `escribir_xlsx`; como `tools/` importa de `src/` y nunca al revés, mover `escribir_xlsx` a `src/sgm/migrar/xlsx_minimo.py` y dejar en `tools/corpus_lib/xlsx_minimo.py` solo el reexport) y la rama del intérprete para `write_file` con `dbms == "xlsx"`.
- [ ] **Step 5: Run** los tests, `tests/unit/test_mg_p2_excel.py`, el golden, `tests/unit/test_catalogo_sas.py` (`export`, p. 901: `reconocida`) y `uv run ruff check src tests tools`.
- [ ] **Step 6: Studio.** `uv run python tools/validar_caso_studio.py l0_20_exportar_xlsx`; sin Studio, «lote C pendiente».
- [ ] **Step 7: Commit.** `hito N n: PROC EXPORT a XLSX con hoja y PUTNAMES`.

---

### Task D2-8: `GETNAMES`, `DATAROW` y `GUESSINGROWS` sobre archivos delimitados (MG-P2-01, parte 3; serie `n`)

Páginas (`proc.pdf`): `GETNAMES Statement` (p. 1387: `YES` por omisión; con `NO` los nombres son `VAR1`, `VAR2`, ...), `DATAROW Statement` (p. 1385), `GUESSINGROWS Statement` (p. 1388: por omisión 20, valor `n` o `MAX`, «valid only for delimited files»). Hoy `P-GUESSINGROWS` bloquea el Job aunque el tipo ya esté fijado por la muestra, y `DATAROW` no se lee (`_OPCION` de `lower_procs.py` solo recoge `dbms|delimiter|getnames|sheet|guessingrows`).

**Decisión (se anota en `PROGRESS.md`, «Decisiones»):** `GUESSINGROWS` solo afecta cómo SAS **infiere** tipo y largo de cada columna. Si todas las columnas del esquema tienen tipo demostrado (muestra o `esquemas:` del caso), el pendiente baja a aviso `A-GUESSINGROWS-TIPOS-FIJADOS` y el Job se emite; si alguna columna queda sin tipo, sigue `P-GUESSINGROWS` y no hay Job parcial. *Alternativa:* bloquear siempre. Qué cambia: ningún programa con `GUESSINGROWS=MAX` (muy común) podría migrar, aunque su esquema ya esté fijado por la muestra.

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\ir\lower_procs_archivos.py` (creado en D2-6: `datarow`)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\talend_item\desde_plan_cabecera.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\talend_item\desde_plan_nodos.py` (una llamada: el `HEADER` y el aviso pasan a las funciones nuevas)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\L0\l0_21_importar_sin_cabecera_datarow\{caso.yaml, programa.sas, entradas\datos.csv, esperado\s.csv}`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_importar_cabecera.py`

**Interfaces:**
- Consumes: `_cabecera(getnames: bool | int | None) -> str` (`desde_plan_nodos.py:93`); `Resultado`, `PendienteMigracion(codigo, mensaje, linea)`; `Column(name, type)` (`sgm.ir.models`).
- Produces:
  ```python
  # desde_plan_cabecera.py
  def lineas_a_saltar(getnames: bool, datarow: int | None) -> int:
      """`HEADER` de `tFileInputDelimited`: con DATAROW=n se saltan las n-1 lineas anteriores;
      sin DATAROW, 1 si GETNAMES=YES y 0 si NO. DATAROW=1 con GETNAMES=YES es un conflicto
      (la fila 1 son los nombres): ValueError con la pagina 1385."""
  def nombres_por_omision(cantidad: int) -> list[str]:
      """GETNAMES=NO: ["VAR1", ..., "VARn"] (p. 1387)."""
  def aviso_guessingrows(esquema: list[Column], guessingrows: object, linea: int | None) -> PendienteMigracion | None:
      """None si no hay GUESSINGROWS; `A-GUESSINGROWS-TIPOS-FIJADOS` si todas las columnas
      tienen tipo; `P-GUESSINGROWS` si alguna no."""
  ```

**Caso `L0/l0_21_importar_sin_cabecera_datarow` (`capa: C`, `estado: revisado`, razonamiento: «proc, p. 1385 (DATAROW), 1387 (GETNAMES=NO da VAR1, VAR2...) y 1388 (GUESSINGROWS=MAX en delimitados)»).**
```sas
PROC IMPORT DATAFILE='.../entradas/datos.csv' OUT=WORK.d DBMS=CSV REPLACE;
  GETNAMES=NO;
  DATAROW=2;
  GUESSINGROWS=MAX;
RUN;
DATA WORK.s;
  SET WORK.d;
  suma = VAR2 + VAR3;
  KEEP VAR1 suma;
RUN;
```
`entradas/datos.csv`: línea 1 `# exportado el 2026-11-11`, línea 2 `a,1,2`, línea 3 `b,3,4`. Esperado a mano, `esperado/s.csv`: `VAR1,suma` / `a,3` / `b,7` (la línea 1 no es dato porque `DATAROW=2`; los nombres son `VAR1` a `VAR3`). Antes de fijar el esperado, comprobar en p. 1385 que `DATAROW=2` salta exactamente la primera línea y en p. 1387 el nombre `VAR1`; lo que no coincida se ajusta o queda `Pendiente:`.

- [ ] **Step 1: Write the failing tests.** (a) `lineas_a_saltar(False, 2) == 1`, `lineas_a_saltar(True, None) == 1`, `lineas_a_saltar(False, None) == 0`, `lineas_a_saltar(True, 1)` lanza `ValueError` con «p. 1385»; (b) `nombres_por_omision(3) == ["VAR1","VAR2","VAR3"]`; (c) `aviso_guessingrows` con las tres columnas tipadas da `A-GUESSINGROWS-TIPOS-FIJADOS` y con una sin tipo `P-GUESSINGROWS`; (d) `_read_file` de `PROC IMPORT ... DATAROW=2;` da `datarow == 2`; (e) el caso coincide en el anillo B y el `tFileInputDelimited` migrado lleva `HEADER == "1"`.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_importar_cabecera.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement** y, en el lector CSV del intérprete, leer `datarow`. Actualizar `procs-usados.yaml` (`import`, nota con `GETNAMES`, `DATAROW` y `GUESSINGROWS`).
- [ ] **Step 4: Run** los tests, `tests/unit/test_migrar_corpus_anillo_b.py -k L0`, `tests/unit/test_mg_p2_excel.py`, el golden y `uv run ruff check src tests tools`. Los 15 casos de `L0` anteriores siguen idénticos.
- [ ] **Step 5: Studio.** `uv run python tools/validar_caso_studio.py l0_21_importar_sin_cabecera_datarow`; sin Studio, «lote C pendiente».
- [ ] **Step 6: Commit.** `hito N n: GETNAMES, DATAROW y GUESSINGROWS en PROC IMPORT delimitado`.

---

### Task D2-9: `INFILE/INPUT` en lista con `DSD`, `MISSOVER` y `TRUNCOVER` a `tFileInputDelimited` (MG-P2-02, parte 1; serie `n`)

**Estado hoy:** el frontend extrae las opciones de `INFILE` (`infile_fields`, `datastep_io.py:25`) y de `INPUT` (`input_fields`, línea 66); `nodo_lectura` las convierte con `motivo_entrada_data_step`, y todo lo que no es delimitado simple queda `P-FORMATO-SIN-SOPORTE` o `P-INFILE-SIN-EQUIVALENCIA`. Páginas (`lestmtsref.pdf`): `INFILE Statement` (p. 134; `DSD`, `MISSOVER`, `TRUNCOVER`, `FLOWOVER` y `FIRSTOBS=` están dentro de esa entrada: ubicar con `grep -n "^DSD\|^MISSOVER\|^TRUNCOVER" docs/referencia/sas/lestmtsref.txt`) e `INPUT Statement: List` (p. 204, con el modificador `:`). Reglas: con `DSD` el delimitador entre comillas es dato, las comillas se quitan y dos delimitadores seguidos son un faltante; `MISSOVER` deja faltantes los campos que no llegan y no pasa a la línea siguiente; sin `MISSOVER` ni `TRUNCOVER` rige `FLOWOVER` (sigue en la línea siguiente), que `tFileInputDelimited` no reproduce: `Pendiente: P-INFILE-FLOWOVER`.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\interprete_infile.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\talend_item\desde_plan_infile.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\talend_item\motivo_entrada_data_step.py` (deja de rechazar `DSD`, `MISSOVER` y `FIRSTOBS`; ver qué rechaza hoy con `grep -n "def motivo_entrada_data_step" src/sgm/talend_item/motivo_entrada_data_step.py`)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\talend_item\desde_plan_nodos.py` (una llamada)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\L0\l0_22_infile_lista_dsd_missover\{caso.yaml, programa.sas, entradas\clientes.txt, esperado\clientes.csv}`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\rules\sas\catalogo\sentencias-data-step.yaml` (`infile-statement` y `input-statement`: nota con las opciones cubiertas)
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_infile_lista.py`

**Interfaces:**
- Consumes: `infile_fields(text: str) -> dict` y `input_fields(text: str) -> dict` (`sgm.frontend.datastep_io`); `Operator.params` con `infile_statement`, `input_statement` y `file_format == "delimited"`; `Resultado`; `tipo_talend(tipo)`.
- Produces:
  ```python
  # interprete_infile.py
  def leer_lista(
      lineas: Sequence[str], variables: Sequence[tuple[str, str | None]],
      dlm: str, dsd: bool, missover: bool, firstobs: int = 1,
  ) -> list[dict[str, str | None]]:
      """Anillo B: lectura en lista. `variables` = (nombre, informat o None). Sin DSD los
      delimitadores consecutivos cuentan como uno; con DSD cada uno separa un campo y el vacio
      es None. Linea corta sin MISSOVER ni TRUNCOVER:
      NoSoportadoEnInterprete('infile', 'P-INFILE-FLOWOVER')."""
  # desde_plan_infile.py
  def nodo_infile_delimitado(op, esquema, unico, x, y, ruta_java=None) -> Resultado:
      """`tFileInputDelimited` con `FIELDSEPARATOR`, `TEXT_ENCLOSURE` `"` si hay DSD y
      `HEADER` = FIRSTOBS-1. Con FLOWOVER implicito: `P-INFILE-FLOWOVER`."""
  ```

**Caso `L0/l0_22_infile_lista_dsd_missover` (`capa: C`, `estado: pendiente_revision` hasta fijar en p. 134 que el último delimitador de `2;Luis;` deja `saldo` faltante; razonamiento: «lestmtsref, p. 134 (DSD, MISSOVER, FIRSTOBS) y p. 204 (lista con modificador `:`)»).**
```sas
DATA WORK.clientes;
  INFILE '.../entradas/clientes.txt' DLM=';' DSD MISSOVER FIRSTOBS=2;
  INPUT id nombre :$12. saldo;
RUN;
```
`entradas/clientes.txt` (un encabezado y cuatro datos):
```
id;nombre;saldo
1;"Perez; Ana";100.5
2;Luis;
3;"Gomez";7
4;Mara
```
Esperado a mano, `esperado/clientes.csv`: `id,nombre,saldo` / `1,Perez; Ana,100.5` / `2,Luis,` / `3,Gomez,7` / `4,Mara,` (`FIRSTOBS=2` salta el encabezado; `DSD` conserva el `;` del nombre entre comillas y quita las comillas; `2;Luis;` deja `saldo` faltante por el delimitador final; `4;Mara` es una línea corta y `MISSOVER` deja `saldo` faltante en vez de leer la línea siguiente). Invariante: `filas(clientes) == 4`.

- [ ] **Step 1: Write the failing tests.** (a) `leer_lista(['1;"Perez; Ana";100.5'], [("id",None),("nombre","$12."),("saldo",None)], ";", True, True)` da `[{"id":"1","nombre":"Perez; Ana","saldo":"100.5"}]`; (b) `["2;Luis;"]` da `saldo` `None`; (c) `["4;Mara"]` con `missover=True` da `saldo` `None` y con `missover=False` lanza `NoSoportadoEnInterprete` con `P-INFILE-FLOWOVER`; (d) `["a;;c"]` con `dsd=False` da dos campos (`a`, `c`) y con `dsd=True` tres (`a`, `None`, `c`); (e) el caso coincide en el anillo B; (f) `nodo_infile_delimitado` sobre el caso da `HEADER == "1"` y `FIELDSEPARATOR == '";"'`, y con `DSD` el `TEXT_ENCLOSURE`; sin `DSD` no lo hay; (g) la migración del caso no deja `P-INFILE-SIN-EQUIVALENCIA` ni `P-FORMATO-SIN-SOPORTE`.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_infile_lista.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement.** `leer_lista` solo trata lo demostrado; `TRUNCOVER` con lista se comporta como `MISSOVER` solo si p. 134-137 lo dice (si no, `Pendiente: P-INFILE-TRUNCOVER-LISTA`). Tipo de cada columna: `INPUT id` sin informat es numérico (p. 204); `:$12.` es carácter de largo 12; lo no demostrado queda `pendiente` como en `l0_15`.
- [ ] **Step 4: Run** los tests, `tests/unit/test_migrar_corpus_anillo_b.py -k L0`, `tests/unit/test_input_informat.py`, el golden y `uv run ruff check src tests tools`.
- [ ] **Step 5: Studio.** `uv run python tools/validar_caso_studio.py l0_22_infile_lista_dsd_missover`; anotar si `tFileInputDelimited` deja `saldo` nulo en `4;Mara`. Sin Studio, «lote C pendiente».
- [ ] **Step 6: Commit.** `hito N n: INFILE en lista con DSD, MISSOVER y FIRSTOBS`.

---

### Task D2-10: `INFILE/INPUT` por columna y formateado a `tFileInputPositional` (MG-P2-02, parte 2; serie `n`)

Hoy una lectura posicional deja `P-COMPONENTE-SIN-PLANTILLA` (`desde_plan_nodos.py:134`) y `INPUT` con informat deja `P-INFORMAT-SIN-SOPORTE`. Páginas: `lestmtsref.pdf`, `INPUT Statement: Column` (p. 195), `INPUT Statement: Formatted` (p. 199), `INFILE Statement` (p. 134, `TRUNCOVER`); `leforinforref.pdf`, `w.d Informat` (p. 744), `$w. Informat` (p. 616), `COMMAw.d Informat` (p. 646). Reglas: `INPUT @1 cuenta $5. @6 sucursal 3. @9 monto 8.2` lee cada variable de su columna y ancho; `w.d` sin punto decimal en el dato divide por `10**d` (verificar la frase en p. 744); `TRUNCOVER` deja faltantes los campos de una línea corta.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\talend_item\plantillas\tFileInputPositional.json` (extraída de Studio; Step 1)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\talend_item\desde_plan_posicional.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\interprete_posicional.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\formatos\__init__.py` y `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\formatos\informat_archivo.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\talend_item\desde_plan_nodos.py` (una llamada en la rama `file_format == "positional"`, línea 124)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\L0\l0_23_infile_columna_formateado\{caso.yaml, programa.sas, entradas\mov.txt, esperado\mov.csv}`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_infile_posicional.py`

**Interfaces:**
- Consumes: `infile_fields`, `input_fields` (`datastep_io.py`); `informat_type(spec: str) -> CodeType | None` (`sgm.ir.types_code`, línea 113); `parsear_informat(spec: str) -> Informat` e `Informat(nombre, ancho, decimales)` del **Plan D1** (D1-15; ver Dependencias); `nodo_desde_plantilla`.
- Produces:
  ```python
  # formatos/informat_archivo.py
  def leer_campo(texto: str, informat: str) -> str | None:
      """Campo de archivo -> valor segun el informat (`$5.`, `3.`, `8.2`): None si el texto esta
      en blanco; `w.d` sin punto decimal divide por 10**d (p. 744). Con D1 integrado delega en
      `parsear_informat` + `INPUT`; antes, solo `$w.`, `w.` y `w.d`, y cualquier otro informat:
      NoSoportadoEnInterprete('informat', spec)."""
  # interprete_posicional.py
  def leer_columnas(
      lineas: Sequence[str], campos: Sequence[tuple[str, int, int, str]], truncover: bool,
  ) -> list[dict[str, str | None]]:
      """campos = (nombre, columna_inicial_1_based, ancho, informat). Linea mas corta que el
      campo: con truncover lo que haya (o None si no llega nada); sin truncover ni missover:
      NoSoportadoEnInterprete('infile', 'P-INFILE-FLOWOVER')."""
  # desde_plan_posicional.py
  def nodo_posicional(op, esquema, unico, x, y, ruta_java=None) -> Resultado:
      """`tFileInputPositional` con `PATTERN` = anchos separados por coma. Sin plantilla:
      `P-COMPONENTE-SIN-PLANTILLA`. Informat que no es `$w.`, `w.` ni `w.d`:
      `P-INFORMAT-SIN-SOPORTE`."""
  ```

**Caso `L0/l0_23_infile_columna_formateado` (`capa: C`, `estado: pendiente_revision` hasta verificar p. 744; razonamiento: «lestmtsref, p. 195, 199 y 134; leforinforref, p. 744 y 616»).**
```sas
DATA WORK.mov;
  INFILE '.../entradas/mov.txt' TRUNCOVER;
  INPUT @1 cuenta $5. @6 sucursal 3. @9 monto 8.2;
RUN;
```
`entradas/mov.txt` (columnas 1 a 16; la tercera línea termina en la columna 8):
```
A0001010  1234.5
B000202020055.25
C0003003
D0004004     750
```
Esperado a mano, `esperado/mov.csv`: `cuenta,sucursal,monto` / `A0001,10,1234.5` / `B0002,20,20055.25` / `C0003,3,` / `D0004,4,7.5` (columnas 6 a 8 son `010`, `020`, `003` y `004`, que con `3.` dan 10, 20, 3 y 4; `monto` de la línea 1 es `  1234.5` con punto decimal y se lee tal cual; el de la línea 4 es `     750` sin punto decimal y `8.2` lo divide por 100, 7.5; la línea 3 termina antes de la columna 9 y `TRUNCOVER` deja `monto` faltante en vez de leer la línea siguiente). Invariante: `filas(mov) == 4`.

- [ ] **Step 1: Plantilla (Studio).** Extraer `tFileInputPositional.json` de un Job de Studio con `tools/contenedores/extraer_plantillas_talend.py` (leer su `--help`). Sin Studio: `P-COMPONENTE-SIN-PLANTILLA` se mantiene, el caso se prueba en B y queda en `migrar_pendientes.yaml` con ese código.
- [ ] **Step 2: Write the failing tests.** (a) `leer_campo("  1234.5", "8.2") == "1234.5"`, `leer_campo("     750", "8.2") == "7.5"`, `leer_campo("010", "3.") == "10"`, `leer_campo("   ", "8.2") is None`; (b) `leer_columnas(["C0003003"], [("cuenta",1,5,"$5."),("sucursal",6,3,"3."),("monto",9,8,"8.2")], truncover=True)` da `monto` `None` y con `truncover=False` lanza `NoSoportadoEnInterprete` con `P-INFILE-FLOWOVER`; (c) un informat `comma10.2` en el `INPUT` da `P-INFORMAT-SIN-SOPORTE` hasta que D1-15 esté integrado; (d) el caso coincide en el anillo B; (e) con plantilla, `nodo_posicional` da `PATTERN == '"5,3,8"'`.
- [ ] **Step 3: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_infile_posicional.py -q -p no:cacheprovider`.
- [ ] **Step 4: Implement.** Tipo de `cuenta`: `String`; el de `sucursal` y `monto` lo fija `informat_type` (`d > 0` da `BigDecimal`, como `rules/sas/informats.yaml`). Catálogo: `input-statement` e `infile-statement` con las páginas 195 y 199 en `nota`.
- [ ] **Step 5: Run** los tests, `tests/unit/test_input_informat.py`, `tests/unit/test_mg_p2_informats.py`, el golden y `uv run ruff check src tests tools`.
- [ ] **Step 6: Studio.** `uv run python tools/validar_caso_studio.py l0_23_infile_columna_formateado`; sin Studio, «lote C pendiente».
- [ ] **Step 7: Commit.** `hito N n: INFILE/INPUT por columna y formateado a tFileInputPositional`.

---

### Task D2-11: `FILE` y `PUT` en lista con `DSD` y `DLM` a un archivo de salida (MG-P2-02, parte 3; serie `n`)

Hoy `FILE` se reconoce como palabra y la sintaxis queda pendiente (`file-statement`, `lestmtsref`, p. 97). Páginas (`lestmtsref.pdf`): `FILE Statement` (p. 97; `DSD`, `DLM=`) y `PUT Statement` (p. 277; lista). Con `DSD` un valor que contiene el delimitador se escribe entre comillas dobles y un faltante es un campo vacío (verificar ambas frases en p. 97-100 con `grep`; lo que no aparezca queda `Pendiente: P-FILE-DSD-COMILLAS`). `DATA _NULL_` no crea tabla: es una escritura pura.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\interprete_file_put.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\talend_item\desde_plan_file_put.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\frontend\datastep_io.py` (`file_fields` y `put_fields`; hoy 130 líneas)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\frontend\datastep.py` (`classify_statement`: ramas `file` y `put`, junto a `infile` e `input`, líneas 144-147)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\ir\lower_data_statements.py` (`DATA _NULL_` con `FILE`/`PUT` baja a un `write_file` con `delimiter`, `dsd` y las variables del `PUT`)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\L0\l0_24_file_put_lista_dsd\{caso.yaml, programa.sas, entradas\ventas.csv, esperado\ventas.txt}`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_file_put_lista.py`

**Interfaces:**
- Consumes: `infile_fields` (modelo de `file_fields`), `DsStatement(kind, text, line, fields)` (`sgm.frontend.datastep`), `nodo_escritura(...)`, plantilla `tFileOutputDelimited` (existe).
- Produces:
  ```python
  # datastep_io.py
  def file_fields(text: str) -> dict:   # {"destino", "es_ruta", "opciones": {"dsd": True, "dlm": "|"}, "no_reconocidas": [...]}
  def put_fields(text: str) -> dict:    # {"modo": "lista"|"columna"|"formateado"|"nombrado", "variables": [...], "formatos": [...]}
  # interprete_file_put.py
  def escribir_lista(filas: Sequence[Mapping[str, object]], variables: Sequence[str],
                     dlm: str, dsd: bool) -> list[str]:
      """Una linea por fila. Faltante (None) con DSD -> campo vacio; sin DSD -> la pagina 97 debe
      fijar el valor o NoSoportadoEnInterprete. Con DSD, el valor que contiene `dlm` o `"` va
      entre comillas dobles (`"` interior duplicado)."""
  ```

**Caso `L0/l0_24_file_put_lista_dsd` (`capa: C`, `estado: pendiente_revision` hasta verificar las comillas con DSD en p. 97; razonamiento: «lestmtsref, p. 97 (FILE: DSD, DLM) y p. 277 (PUT en lista)»).**
```sas
PROC IMPORT DATAFILE='.../entradas/ventas.csv' OUT=WORK.ventas DBMS=CSV REPLACE; GETNAMES=YES; RUN;
DATA _NULL_;
  SET WORK.ventas;
  FILE '.../salida/ventas.txt' DSD DLM='|';
  PUT id nombre monto;
RUN;
```
`ventas.csv` (`id,nombre,monto`): `1,Ana,10.5` / `2,Luis|Jr,3` / `3,Mara,`. Esperado a mano, `esperado/ventas.txt` (sin encabezado, fin de línea `\n`), tres líneas: `1|Ana|10.5`, `2|"Luis|Jr"|3` y `3|Mara|` (el nombre con `|` se comilla por `DSD`; el `monto` faltante es un campo vacío). Invariante: `lineas(ventas.txt) == 3`.

- [ ] **Step 1: Write the failing tests.** (a) `file_fields("file '/s/v.txt' dsd dlm='|'")` da `opciones == {"dsd": True, "dlm": "|"}`; (b) `put_fields("put id nombre monto")` da `modo == "lista"` y tres variables, y `put_fields("put @1 id 5.")` da `modo == "formateado"`; (c) `escribir_lista([{"id":2,"nombre":"Luis|Jr","monto":3}], ["id","nombre","monto"], "|", True) == ['2|"Luis|Jr"|3']` y con `monto` `None` termina en `|`; (d) el caso coincide en el anillo B comparando el texto; (e) el `.item` migrado tiene `tFileOutputDelimited` con `FIELDSEPARATOR == '"|"'` e `INCLUDEHEADER == "false"`; el dataset `_NULL_` no aparece en el esquema ni en `rutas_de_plan`.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_file_put_lista.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement.** Catálogo: `file-statement` (p. 97) pasa a `reconocida` con la nota «lista y DSD; columna y formateado: D2-14»; entrada `put-statement` (p. 277) si no existe.
- [ ] **Step 4: Run** los tests, `tests/unit/test_frontend.py`, el golden y `uv run ruff check src tests tools`.
- [ ] **Step 5: Studio.** `uv run python tools/validar_caso_studio.py l0_24_file_put_lista_dsd`; anotar si `tFileOutputDelimited` comilla `Luis|Jr` como el esperado (ver `docs/referencia/talend/tfileoutputdelimited.md`). Sin Studio, «lote C pendiente».
- [ ] **Step 6: Commit.** `hito N n: FILE y PUT en lista con DSD y DLM`.

---

## Parte III. Informats y formats numéricos y de fecha (MG-P2-03; contrato con el Plan D1)

**Reparto con el Plan D1 (MG-P3-05).** D1 es dueño de `INPUT(x, informat)` y `PUT(x, formato)` **como funciones dentro de expresiones** (D1-15 a D1-17: `parsear_informat`, `Informat(nombre, ancho, decimales)`, `YEARCUTOFF`). Este plan es dueño de lo mismo **en la sentencia de archivo**: el informat de `INPUT x :comma12.2;` al leer un archivo y el formato de `PUT x comma10.2;` al escribirlo. Las dos partes comparten una sola implementación: `formatos/informat_archivo.leer_campo` (D2-10) llama a `parsear_informat` cuando D1-15 está integrado y, mientras no lo esté, cubre solo `$w.`, `w.` y `w.d` y deja el resto en `P-INFORMAT-SIN-SOPORTE`. Ninguna tarea de esta parte duplica un vector de D1: los casos usan el informat desde la sentencia `INPUT`/`PUT` de un archivo, que D1 no ejecuta.

### Task D2-12: Informats numéricos en `INPUT`: `w.d`, `COMMAw.d` y `DOLLARw.d` (MG-P2-03, parte 1; serie `n`)

Páginas (`leforinforref.pdf`): `w.d Informat` (p. 744), `COMMAw.d Informat` (p. 646), `$w. Informat` (p. 616); `DOLLARw.d Informat`: el índice solo trae `DOLLARw.d Format` (p. 198); buscar con `grep -n -i "dollar" docs/referencia/sas/leforinforref.INDEX.md` y, si no hay página de informat, `Pendiente: P-INFORMAT-DOLLAR-SIN-PAGINA` y la columna `b` sale del caso. Regla que prueba el caso: un informat con `d > 0` **divide por `10**d` cuando el dato no trae punto decimal** (p. 744), así que `COMMA12.2` lee `-7` como `-0.07`; con punto decimal en el dato, `d` no cuenta.

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\formatos\informat_archivo.py` (creado en D2-10: `comma`, `dollar`)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\interprete_infile.py` (D2-9: el informat de `variables` pasa por `leer_campo`)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\rules\sas\catalogo\informats-usados.yaml` (entradas `comma` p. 646 y `w-d` p. 744: `reconocida`, con la nota de la división por `10**d`)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\L0\l0_25_informats_numericos_infile\{caso.yaml, programa.sas, entradas\crudo.txt, esperado\limpio.csv}`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_informats_archivo_num.py`

**Interfaces:**
- Consumes: `leer_campo(texto: str, informat: str) -> str | None` (D2-10), `leer_lista(...)` (D2-9), `informat_type(spec: str)` (`types_code.py:113`), `Informat` y `parsear_informat` (D1-15).
- Produces: `leer_campo` con `comma`, `dollar` y `w.d` completos: quita `,` y `$` del texto (p. 646), el signo `-` inicial, y aplica la división por `10**d` solo sin punto decimal; texto en blanco o solo `.`, `None`. Con `*`, `%` o paréntesis: `NoSoportadoEnInterprete('informat', ...)` hasta verificar p. 646.

**Caso `L0/l0_25_informats_numericos_infile` (`capa: C`, `estado: pendiente_revision` hasta fijar p. 646 y 744; razonamiento: «leforinforref, p. 646 y 744: división por 10**d sin punto decimal»).**
```sas
DATA WORK.limpio;
  INFILE '.../entradas/crudo.txt' DLM=';' DSD MISSOVER;
  INPUT a :COMMA12.2 b :DOLLAR10. c :8.2;
RUN;
```
`entradas/crudo.txt`: `1,234.50;$1500;12345` / `-7;$20;5` / `;;`. Esperado a mano, `esperado/limpio.csv`: `a,b,c` / `1234.5,1500,123.45` / `-0.07,20,0.05` / `,,` (`1,234.50` trae punto decimal y se lee 1234.5; `-7` no lo trae y `d=2` lo divide por 100; `12345` con `8.2` da 123.45 y `5` da 0.05; la tercera línea tiene los tres campos faltantes). Invariante: `filas(limpio) == 3`.

- [ ] **Step 1: Write the failing tests.** `leer_campo("1,234.50", "comma12.2") == "1234.5"`, `leer_campo("-7", "comma12.2") == "-0.07"`, `leer_campo("$1500", "dollar10.") == "1500"`, `leer_campo("12345", "8.2") == "123.45"`, `leer_campo("", "comma12.2") is None`, `leer_campo("1.5%", "comma12.2")` lanza `NoSoportadoEnInterprete`; el caso coincide en el anillo B; `informat_type("comma12.2")` da `BigDecimal` y el esquema del caso lo usa.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_informats_archivo_num.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement** y ajustar el esperado a lo que digan las páginas (si p. 646 dice otra cosa para el signo, se corrige el caso y se anota en `PROGRESS.md`). `tFileInputDelimited` no aplica informats: el emisor lee la columna como `String` y deja la conversión en un `tMap` con la expresión de D1 (`talend_funciones_formato._input`); sin D1, `P-INFORMAT-SIN-SOPORTE` y el caso va a `migrar_pendientes.yaml`.
- [ ] **Step 4: Run** los tests, `tests/unit/test_mg_p2_informats.py`, `tests/unit/test_informats_yaml.py`, `tests/unit/test_catalogo_sas.py`, el golden y `uv run ruff check src tests tools`.
- [ ] **Step 5: Studio.** `uv run python tools/validar_caso_studio.py l0_25_informats_numericos_infile`; sin Studio, «lote C pendiente».
- [ ] **Step 6: Commit.** `hito N n: informats numericos w.d, COMMA y DOLLAR en INPUT de archivo`.

---

### Task D2-13: Informats de fecha `YYMMDD`, `DDMMYY`, `DATE9` y `ANYDTDTE` en `INPUT` (MG-P2-03, parte 2; serie `n`)

Páginas (`leforinforref.pdf`): `YYMMDDw. Informat` (p. 755), `DDMMYYw. Informat` (p. 653), `DATEw. Informat` (p. 649), `ANYDTDTEw. Informat` (p. 617). Un informat de fecha devuelve **días desde el 1 de enero de 1960** (`lrcon`: valores de fecha de SAS; localizar con `grep -n -i "January 1, 1960" docs/referencia/sas/lrcon.txt`). `ANYDTDTE` depende de la opción `DATESTYLE`: solo se traduce con una fecha no ambigua (año primero, `2026-09-28`); una ambigua (`03/04/2026`) queda `Pendiente: P-ANYDTDTE-DATESTYLE` (página de la opción: `lesysoptsref.INDEX.md`, entrada `DATESTYLE`). El año de dos dígitos (`YEARCUTOFF`) es de D1-16 y no entra aquí.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\formatos\informat_fecha.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\formatos\informat_archivo.py` (delegar los informats de fecha)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\rules\sas\catalogo\informats-usados.yaml` (`date`: páginas 649, 653, 755 y 617)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\L0\l0_26_informats_fecha_infile\{caso.yaml, programa.sas, entradas\fechas.txt, esperado\fechas.csv}`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_informats_fecha_archivo.py`

**Interfaces:**
- Consumes: `leer_campo` (D2-10); `informat_type` (`types_code.py:113`; `yymmdd`, `ddmmyy`, `date`, `anydtdte` ya dan `Date`, `rules/sas/informats.yaml`).
- Produces:
  ```python
  # informat_fecha.py
  def dias_sas(anio: int, mes: int, dia: int) -> int:
      """Dias desde 1960-01-01 (2000-01-01 -> 14610; 2026-01-01 -> 24107)."""
  def leer_fecha(texto: str, informat: str) -> int | None:
      """`yymmdd10.` acepta `2026-09-28`, `2026/09/28` y `20260928`; `ddmmyy10.` `28/09/2026`;
      `date9.` `28SEP2026` (mes en ingles, sin distinguir mayusculas); `anydtdte10.` solo la forma
      año-mes-dia sin ambiguedad. Blanco -> None. Fecha invalida (`2026-02-30`) -> None (SAS deja
      faltante y escribe una nota en el log; verificar en p. 755)."""
  ```

**Caso `L0/l0_26_informats_fecha_infile` (`capa: C`, `estado: pendiente_revision` hasta fijar la fecha inválida en p. 755; razonamiento: «leforinforref, p. 755, 653, 649 y 617; días desde 1960»).**
```sas
DATA WORK.fechas;
  INFILE '.../entradas/fechas.txt' DLM=';' DSD MISSOVER;
  INPUT id :8. d1 :YYMMDD10. d2 :DDMMYY10. d3 :DATE9. d4 :ANYDTDTE10.;
RUN;
```
`entradas/fechas.txt`: `1;2026-09-28;28/09/2026;28SEP2026;2026-09-28` / `2;2000-01-01;01/01/2000;01JAN2000;` / `3;1960-01-01;02/01/1960;01FEB1960;` / `4;;;;`. Esperado a mano, `esperado/fechas.csv` (fechas como número de días): `id,d1,d2,d3,d4` / `1,24377,24377,24377,24377` / `2,14610,14610,14610,` / `3,0,1,31,` / `4,,,,`. Cálculo: `01JAN2000` = 14610 y 2000 a 2025 suman 26 años con 7 bisiestos (2000, 2004, 2008, 2012, 2016, 2020, 2024), luego `01JAN2026` = 14610 + 26*365 + 7 = 24107; enero a agosto suman 243 días, `01SEP2026` = 24350 y `28SEP2026` = 24377. `1960-01-01` = 0, `02/01/1960` = 1 y `01FEB1960` = 31. Invariante: `d1 == d2 == d3` en las filas 1 a 3.

- [ ] **Step 1: Write the failing tests.** `dias_sas(2000,1,1) == 14610`, `dias_sas(2026,9,28) == 24377`, `dias_sas(1960,1,1) == 0`; `leer_fecha("2026-09-28","yymmdd10.") == 24377`, `leer_fecha("28/09/2026","ddmmyy10.") == 24377`, `leer_fecha("28SEP2026","date9.") == 24377`, `leer_fecha("2026-09-28","anydtdte10.") == 24377`, `leer_fecha("03/04/2026","anydtdte10.")` lanza `NoSoportadoEnInterprete` con `P-ANYDTDTE-DATESTYLE`; `leer_fecha("","date9.") is None`; el caso coincide en el anillo B.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_informats_fecha_archivo.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement** con `datetime.date` (`(date(a,m,d) - date(1960,1,1)).days`). El emisor deja la columna como `String` y la conversión en un `tMap` con la expresión Java de D1-16; sin D1, `P-INFORMAT-SIN-SOPORTE`.
- [ ] **Step 4: Run** los tests, `tests/unit/test_mg_p2_informats.py`, `tests/unit/test_catalogo_sas.py`, el golden y `uv run ruff check src tests tools`.
- [ ] **Step 5: Studio.** `uv run python tools/validar_caso_studio.py l0_26_informats_fecha_infile`; sin Studio, «lote C pendiente».
- [ ] **Step 6: Commit.** `hito N n: informats de fecha YYMMDD, DDMMYY, DATE y ANYDTDTE en INPUT de archivo`.

---

### Task D2-14: Formats de salida en `PUT` por columna y formateado: `COMMAw.d`, `DATEw.` y `$w.` (MG-P2-03, parte 3; serie `n`)

Páginas: `lestmtsref.pdf`, `PUT Statement: Column` (p. 301; la forma formateada está dentro de `PUT Statement`, p. 277: localizar con `grep -n "^<!-- página 30[0-9] -->" docs/referencia/sas/lestmtsref.txt`); `leforinforref.pdf`, `COMMAw.d Format` (p. 181), `DATEw. Format` (p. 186), `Fw.d Format` (p. 235). Reglas: el puntero `@n` coloca la variable en la columna `n`; un formato numérico justifica a la derecha dentro de su ancho `w` con blancos a la izquierda; `COMMA10.2` de `1234.5` es `  1,234.50`; `DATE9.` de 24377 es `28SEP2026`; la línea no lleva blancos finales.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\formatos\formato_archivo.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\interprete_file_put.py` (D2-11: `escribir_columnas`)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\talend_item\desde_plan_file_put.py` (salida posicional con la plantilla `tFileOutputPositional`: extraer de Studio como en D2-10; sin Studio, `P-COMPONENTE-SIN-PLANTILLA`)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\L0\l0_27_put_formateado\{caso.yaml, programa.sas, entradas\mov.csv, esperado\mov.txt}`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_put_formateado.py`

**Interfaces:**
- Consumes: `escribir_lista` (D2-11), `put_fields` (D2-11), `dias_sas` (D2-13), `parsear_formato` del Plan D1 (D1-17; ver Dependencias).
- Produces:
  ```python
  # formato_archivo.py
  def formatear(valor: object, formato: str) -> str:
      """`comma10.2` de 1234.5 -> '  1,234.50'; `date9.` de 24377 -> '28SEP2026'; `$5.` de 'AB' ->
      'AB   ' (el texto va a la izquierda). Valor que no cabe en el ancho: NoSoportadoEnInterprete
      si la pagina del formato no fija el resultado (`best` y asteriscos son de D1-17)."""
  # interprete_file_put.py
  def escribir_columnas(filas: Sequence[Mapping[str, object]],
                        campos: Sequence[tuple[str, int, str]]) -> list[str]:
      """campos = (variable, columna_1_based, formato). Rellena con blancos hasta la columna;
      quita los blancos finales de cada linea."""
  ```

**Caso `L0/l0_27_put_formateado` (`capa: C`, `estado: pendiente_revision` hasta verificar el ancho de `COMMA` en p. 181; razonamiento: «lestmtsref, p. 277 y 301; leforinforref, p. 181 y 186»).**
```sas
PROC IMPORT DATAFILE='.../entradas/mov.csv' OUT=WORK.mov DBMS=CSV REPLACE; GETNAMES=YES; RUN;
DATA _NULL_;
  SET WORK.mov;
  FILE '.../salida/mov.txt';
  PUT @1 cuenta $5. @7 monto COMMA10.2 @19 fecha DATE9.;
RUN;
```
`mov.csv`: `cuenta,monto,fecha` / `A0001,1234.5,24377` / `B0002,20055.25,14610`. Esperado a mano, `esperado/mov.txt`, dos líneas: `A0001   1,234.50  28SEP2026` y `B0002  20,055.25  01JAN2000` (`cuenta` en las columnas 1 a 5; `monto` ocupa las columnas 7 a 16 con justificación a la derecha, `1,234.50` mide 8 y `20,055.25` mide 9; la fecha empieza en la columna 19; 24377 es `28SEP2026` y 14610 es `01JAN2000`, D2-13). Invariante: ambas líneas miden 27 caracteres.

- [ ] **Step 1: Write the failing tests.** `formatear(1234.5, "comma10.2") == "  1,234.50"`, `formatear(20055.25, "comma10.2") == " 20,055.25"`, `formatear(24377, "date9.") == "28SEP2026"`, `formatear("AB", "$5.") == "AB   "`; `escribir_columnas([{"cuenta":"A0001","monto":1234.5,"fecha":24377}], [("cuenta",1,"$5."),("monto",7,"comma10.2"),("fecha",19,"date9.")]) == ["A0001   1,234.50  28SEP2026"]`; el caso coincide en el anillo B (comparación de texto byte a byte); el `.item` no lleva `tFileOutputDelimited` para esta salida.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_put_formateado.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement.** Catálogo: `file-statement` y `put-statement` con la nota «lista, columna y formateado»; formatos `COMMA` (p. 181) y `DATE` (p. 186) en la nota de `informats-usados.yaml` si esa colección no admite formatos.
- [ ] **Step 4: Run** los tests, `tests/unit/test_file_put_lista.py`, el golden, `tests/unit/test_catalogo_sas.py` y `uv run ruff check src tests tools`.
- [ ] **Step 5: Studio.** `uv run python tools/validar_caso_studio.py l0_27_put_formateado`; sin Studio o sin plantilla de salida posicional, «lote C pendiente».
- [ ] **Step 6: Commit.** `hito N n: formats de salida en PUT por columna y formateado`.

---

## Parte IV. `FILENAME`, `RSUBMIT` y datasets permanentes

### Task D2-15: `FILENAME` a archivo y a pipe (MG-P2-06, parte 1; serie `n`)

Páginas: `lestmtsref.pdf`, `FILENAME Statement` (p. 120); `hostunx.pdf`, `Reading from and Writing to UNIX Commands (PIPE)` (p. 132). `FILENAME ref 'ruta';` asocia un nombre a un archivo: `INFILE ref`, `FILE ref` y `PROC IMPORT FILEREF=` lo usan en vez de la ruta. El operador `read_file` ya conserva `fileref` (`desde_plan_nodos.py:129`) pero no lo resuelve. **Decisión (anotar en `PROGRESS.md`):** el `fileref` se resuelve a su ruta literal en un pase de plan (`ir/pase_filerefs.py`) antes de emitir, y la ruta pasa a la variable de contexto `ruta_<tabla>` como cualquier otra. `FILENAME ref PIPE 'comando'` **no se traduce**: ejecutar un comando del sistema es un efecto fuera del Job (el frontend ya lo trata como `COMANDO_SISTEMA`); queda `Pendiente: P-FILENAME-PIPE` con el comando (sin secretos) y la página 132 de `hostunx`. *Alternativa:* `tSystem` más `tFileInputDelimited` sobre un archivo temporal. Qué cambia: el Job ejecutaría comandos arbitrarios del programa SAS en el servidor de Talend, sin que la guía demuestre que el entorno es el mismo; requiere decisión del usuario por programa.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\ir\pase_filerefs.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\preparar_plan.py` (creado en K-9: una llamada; si K-9 no está integrado, la llamada va en `cli_migrar.py` junto a `contextos_de_plan`)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\rules\sas\catalogo\sentencias-data-step.yaml` (`filename-statement`: `reconocida` para archivo; nota con `P-FILENAME-PIPE`)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\L0\l0_28_filename_archivo\{caso.yaml, programa.sas, entradas\lista.csv, esperado\copia.csv}`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_filerefs.py`

**Interfaces:**
- Consumes: `Plan.graph.operators()`, `Operator.params` con `fileref`, `datafile`, `outfile`; `ruta(literal)` (`desde_plan_nodos.py:61`); `PendienteMigracion`; la clase del frontend para `FILENAME` (**verificar con `grep -n -i "filename" src/sgm/frontend/steps.py`; si no hay clase, esta tarea agrega `Filename(ref, destino, metodo, opciones)` en `steps_tipos.py` y su rama en `steps.py` junto a `Libname`, línea 164**).
- Produces:
  ```python
  def filerefs_de_programa(items: Iterable) -> dict[str, FilenameInfo]:
      """`FilenameInfo(ref, metodo: "archivo"|"pipe"|"ftp"|"otro", destino, opciones)`; la ultima
      por ref; `FILENAME ref CLEAR` la quita. Contrasenas de FTP: nunca se guardan (`'***'`)."""
  def aplicar_filerefs(plan: Plan, filerefs: Mapping[str, FilenameInfo]) -> tuple[Plan, list[PendienteMigracion]]:
      """Todo `read_file`/`write_file` con `fileref` pasa a `datafile`/`outfile` = su ruta.
      Metodo `pipe`: `P-FILENAME-PIPE`; `otro`: `P-FILENAME-METODO`; fileref sin FILENAME:
      `P-FILEREF-SIN-DEFINIR`."""
  ```

**Caso `L0/l0_28_filename_archivo` (`capa: C`, `estado: revisado`, razonamiento: «lestmtsref, p. 120 (FILENAME), 134 (INFILE fileref) y 97 (FILE fileref)»).**
```sas
FILENAME entrada '.../entradas/lista.csv';
FILENAME salida '.../salida/copia.csv';
DATA WORK.lista;
  INFILE entrada DLM=',' DSD FIRSTOBS=2;
  INPUT codigo :$4. cantidad :8.;
RUN;
DATA _NULL_;
  SET WORK.lista;
  FILE salida DSD;
  PUT codigo cantidad;
RUN;
```
`lista.csv`: `codigo,cantidad` / `K001,5` / `K002,12`. Esperado a mano, `esperado/copia.csv` (sin encabezado: `PUT` no lo escribe): `K001,5` / `K002,12`. Invariante: `lineas(copia) == filas(lista) == 2`.

- [ ] **Step 1: Write the failing tests.** `filerefs_de_programa` de `FILENAME a 'x.csv'; FILENAME b PIPE 'ls'; FILENAME a CLEAR;` da solo `b` con `metodo == "pipe"`; `aplicar_filerefs` deja el `read_file` del caso con `datafile == "'.../entradas/lista.csv'"` y el `write_file` con `outfile` la ruta de `salida`; `FILENAME p PIPE 'ls /x'` da `P-FILENAME-PIPE` sin Job parcial; `INFILE zz;` sin `FILENAME` da `P-FILEREF-SIN-DEFINIR`; `contextos_de_plan` da `ruta_lista` y `ruta_lista_2` con las dos rutas; el caso coincide en el anillo B.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_filerefs.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement** y correr `tests/unit/test_plumbing_categorias.py` (el `plumbing.yaml` no debe volver a tratar `FILENAME` de archivo como infraestructura descartada).
- [ ] **Step 4: Run** los tests, el golden, `tests/unit/test_catalogo_sas.py` y `uv run ruff check src tests tools`.
- [ ] **Step 5: Studio.** `uv run python tools/validar_caso_studio.py l0_28_filename_archivo`; sin Studio, «lote C pendiente».
- [ ] **Step 6: Commit.** `hito N n: FILENAME a archivo resuelto por pase de plan; PIPE pendiente con motivo`.

---

### Task D2-16: `FILENAME ... FTP` a `tFTPGet` y lectura local (MG-P2-06, parte 2; serie `n`)

Páginas: `lestmtsref.pdf`, `FILENAME Statement: FTP Access Method` (p. 122; opciones `HOST=`, `USER=`, `PASS=`, `CD=`, `RCMD=`: leer la sintaxis antes de fijar nada). `rules/talend/components.json` lista `tFTPGet` (línea 693); falta su plantilla y su ficha en `docs/referencia/talend/`. Un `INFILE` sobre un `fileref` FTP baja el archivo remoto y lo lee: en Talend, `tFTPGet` a una carpeta local y después `tFileInputDelimited` sobre el archivo bajado, encadenados con `OnSubjobOk`. Host y usuario van al contexto (`ftp_host`, `ftp_usuario`), la contraseña nunca (`'***'`; el nombre `ftp_clave` casa con la regla de secretos y sale vacío); la carpeta local es `ftp_carpeta_local`.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\talend_item\desde_plan_ftp.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\talend_item\plantillas\tFTPGet.json` (extraída de Studio; sin Studio, `P-COMPONENTE-SIN-PLANTILLA`)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\ir\pase_filerefs.py` (D2-15: rama `ftp`; el `read_file` guarda `ftp: {host, usuario, cd, archivo}`)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\L0\l0_29_filename_ftp\{caso.yaml, programa.sas, entradas\ventas.csv, esperado\v.csv}`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_filename_ftp.py`

**Interfaces:**
- Consumes: `FilenameInfo` (D2-15), `nodo_desde_plantilla`, `java`, `ParametroContexto`.
- Produces:
  ```python
  def nodos_ftp(op: Operator, unico: str, x: int, y: int, ruta_java: str | None = None) -> Resultado:
      """`tFTPGet` con HOST/USERNAME/REMOTEDIR/FILEMASK desde el contexto y el archivo remoto
      literal; PASSWORD desde `context.ftp_clave` (vacia). Sin plantilla: `P-COMPONENTE-SIN-PLANTILLA`.
      Con `&` en el nombre: `P-FTP-DINAMICO`."""
  ```

**Caso `L0/l0_29_filename_ftp` (`capa: B`, `estado: pendiente_revision`; razonamiento: «lestmtsref, p. 122: el método FTP baja el archivo; el anillo B lo lee de entradas/»; lote C pendiente por falta de servidor FTP de prueba).**
```sas
FILENAME remoto FTP 'ventas.csv' HOST='ftp.ejemplo.test' USER='u' PASS='***' CD='/entrada';
DATA WORK.v;
  INFILE remoto DLM=',' DSD FIRSTOBS=2;
  INPUT sku :$4. cantidad :8.;
RUN;
```
`entradas/ventas.csv` (el archivo «remoto», que el anillo B lee como local): `sku,cantidad` / `K001,5` / `K002,12`. Esperado a mano, `esperado/v.csv`: `sku,cantidad` / `K001,5` / `K002,12`.

- [ ] **Step 1: Write the failing tests.** `nodos_ftp` con plantilla da `tFTPGet` con `HOST == "context.ftp_host"` y sin la cadena `ftp.ejemplo.test` ni `u` en el `.item`; el contexto trae `ftp_host`, `ftp_usuario`, `ftp_clave` (vacía) y `ftp_carpeta_local`; el pendiente conserva el texto de las opciones con la contraseña como `'***'`; `FILENAME f FTP '&x.'` da `P-FTP-DINAMICO`; el caso coincide en el anillo B; `sgm secretos`: cero hallazgos.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_filename_ftp.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement.** Anotar «lote C pendiente: no existe un servidor FTP de prueba en `tools/contenedores/`; agregarlo es del Plan K» y listar el caso en `migrar_pendientes.yaml` solo si falta la plantilla.
- [ ] **Step 4: Run** los tests, el golden, `tests/unit/test_catalogo_sas.py` y `uv run ruff check src tests tools`.
- [ ] **Step 5: Commit.** `hito N n: FILENAME FTP a tFTPGet con host y usuario por contexto`.

---

### Task D2-17: `RSUBMIT`, `PROC UPLOAD` y `PROC DOWNLOAD` de datasets (MG-P2-06, parte 3; serie `n`; contrato con K-5)

**Reparto con K-5.** K-5 (`pase_copias_remotas.py`) resuelve `PROC UPLOAD/DOWNLOAD` de **archivos** (`INFILE=`/`OUTFILE=`) como alias de ruta y deja `P-COPIA-REMOTA-DATASET` para `DATA=`/`OUT=`. Esta tarea resuelve esos datasets y el contenido de los bloques `RSUBMIT` **sin modificar el archivo de K-5**: módulo nuevo `pase_copias_dataset.py`, que se aplica después. Páginas: `connref.pdf`, `RSUBMIT Statement` (p. 185), `ENDRSUBMIT Statement` (p. 206), `SIGNON Statement` (p. 151), `UPLOAD Procedure` (p. 245), `DOWNLOAD Procedure` (p. 285; sintaxis p. 286); `gridref.pdf` para el `SIGNON` de Grid (buscar con `grep -n -i "signon" docs/referencia/sas/gridref.INDEX.md`). **Decisión (anotar en `PROGRESS.md`):** en el Job todo corre en un solo lugar, así que el `WORK` remoto y el local son el mismo espacio de nombres; `PROC UPLOAD DATA=WORK.a OUT=WORK.b` y `PROC DOWNLOAD DATA=WORK.a OUT=WORK.b` pasan a ser un **alias de dataset** (`b` es `a`), y los pasos dentro del bloque se emiten como cualquier otro con el aviso `A-RSUBMIT-LOCAL` (el programa los ejecutaba en el servidor remoto). *Alternativa:* un Job por bloque `RSUBMIT` con una conexión al servidor remoto. Qué cambia: exigiría un agente de Talend en el servidor y dejaría de ser un migrador de SAS a Talend; fuera de alcance. El `SIGNON` nunca copia `USER=` ni `PASSWORD=`; `RSUBMIT` con `WAIT=NO` (ejecución asíncrona con `WAITFOR`) queda `Pendiente: P-RSUBMIT-ASINCRONO`.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\ir\pase_copias_dataset.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\rules\sas\plumbing.yaml` (líneas 92-95: `rsubmit|endrsubmit|signon|signoff|waitfor` sigue siendo infraestructura; solo se agrega la nota de que el contenido del bloque se traduce)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\rules\sas\catalogo\procs-usados.yaml` (`upload` p. 245, `download` p. 285: `reconocida`; **corregir la página de `download`**: el catálogo trae `p. 287` y el índice dice `DOWNLOAD Procedure (p. 285)`)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\L0\l0_30_rsubmit_upload_download\{caso.yaml, programa.sas, entradas\base.csv, esperado\final.csv}`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_copias_dataset.py`

**Interfaces:**
- Consumes: `copias_remotas(texto: str) -> tuple[list[CopiaRemota], list[PendienteMigracion]]` y `CopiaRemota` (K-5); `Plan.graph`; `PendienteMigracion`.
- Produces:
  ```python
  @dataclass(frozen=True)
  class CopiaDataset:
      sentido: str      # "upload" | "download"
      origen: str       # dataset de DATA=, calificado y en minusculas
      destino: str      # dataset de OUT=
      linea: int
  def copias_de_dataset(texto: str) -> tuple[list[CopiaDataset], list[PendienteMigracion]]
  def aplicar_copias_dataset(plan: Plan, copias: Sequence[CopiaDataset]) -> tuple[Plan, list[PendienteMigracion]]:
      """Todo operador que consume `destino` pasa a consumir `origen`. Una copia sin consumidor
      deja `A-COPIA-REMOTA-SIN-EFECTO`; con `WAIT=NO` en el RSUBMIT, `P-RSUBMIT-ASINCRONO`."""
  ```

**Caso `L0/l0_30_rsubmit_upload_download` (`capa: C`, `estado: pendiente_revision` hasta fijar el sentido de `DATA=`/`OUT=` en p. 246 y 286; razonamiento: «connref, p. 185, 206, 245 y 285»).**
```sas
PROC IMPORT DATAFILE='.../entradas/base.csv' OUT=WORK.base DBMS=CSV REPLACE; GETNAMES=YES; RUN;
SIGNON servidor USER=u PASSWORD='***';
RSUBMIT servidor;
  PROC UPLOAD DATA=WORK.base OUT=WORK.base; RUN;
  DATA WORK.remoto;
    SET WORK.base;
    total = a + b;
  RUN;
  PROC DOWNLOAD DATA=WORK.remoto OUT=WORK.local; RUN;
ENDRSUBMIT;
SIGNOFF servidor;
DATA WORK.final;
  SET WORK.local;
  doble = total * 2;
RUN;
```
`base.csv`: `a,b` / `1,2` / `10,20`. Esperado a mano, `esperado/final.csv`: `a,b,total,doble` / `1,2,3,6` / `10,20,30,60`. Invariantes: `filas(final) == filas(base)`; el texto `'***'` es el único rastro de la contraseña en el paquete.

- [ ] **Step 1: Write the failing tests.** `copias_de_dataset` del caso da dos `CopiaDataset` (`upload base -> base`, `download remoto -> local`); `aplicar_copias_dataset` hace que `WORK.final` consuma `WORK.remoto`; `signon ... PASSWORD='***'` no aparece en ningún pendiente; `RSUBMIT servidor WAIT=NO;` da `P-RSUBMIT-ASINCRONO`; el caso coincide en el anillo B; el golden y la clasificación de `plumbing.yaml` no cambian; la prueba de K-5 (`test_copias_remotas.py`) sigue verde.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_copias_dataset.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement** y encadenar la llamada después de la de K-5 en `preparar_plan.py` (K-9); si K-5 no está integrado, `copias_de_dataset` se prueba sola y la integración queda como paso de la tarea que llegue segundo. Catálogo: corregir `download` a p. 285 y correr `tests/unit/test_catalogo_sas.py`.
- [ ] **Step 4: Run** los tests, `tests/unit/test_plumbing_categorias.py`, `tests/unit/test_plumbing_yaml.py`, el golden y `uv run ruff check src tests tools`.
- [ ] **Step 5: Studio.** `uv run python tools/validar_caso_studio.py l0_30_rsubmit_upload_download`; sin Studio, «lote C pendiente».
- [ ] **Step 6: Commit.** `hito N n: PROC UPLOAD y DOWNLOAD de datasets como alias y contenido de RSUBMIT traducido`.

---

### Task D2-18: Datasets permanentes a archivo de preparación con aviso (MG-P2-07, decisión MG-D03; serie `n`)

Un dataset `lib.tabla` de una biblioteca de ruta (D2-5) es un `.sas7bdat`: Talend no lo escribe ni lo lee. **Decisión MG-D03 aplicada** (`plan-migrador-general.md`, línea 431: «archivo de preparación con aviso»): `DATA lib.t;` escribe `<ruta>/t.csv` (`tFileOutputDelimited`) y toda lectura posterior de `lib.t` lee ese mismo archivo (`tFileInputDelimited`), con la ruta en la variable de contexto `ruta_lib_<lib>` de D2-5. Aviso `A-DATASET-PERMANENTE-A-ARCHIVO`: el CSV **no conserva** tipos, largos, formatos ni etiquetas del `.sas7bdat`, así que un tipo que el SAS no demuestra sigue `pendiente`. *Alternativas descartadas:* tabla en una base (exige una base destino y credenciales que el SAS no demuestra; es la decisión de D2-4, no de esta) y fuera de alcance (deja sin migrar casi todo programa con bibliotecas permanentes). Qué cambia con la elegida: el archivo de preparación es un artefacto nuevo que el programa original no tenía.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\ir\pase_permanentes.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\preparar_plan.py` (K-9: una llamada tras `aplicar_filerefs`)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\talend_item\desde_plan_contextos.py` (la ruta de un permanente es `${ruta_lib_<lib>}/<tabla>.csv`)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus\L0\l0_31_biblioteca_permanente\{caso.yaml, programa.sas, entradas\nuevos.csv, esperado\leido.csv, esperado\clientes.csv}`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_pase_permanentes.py`

**Interfaces:**
- Consumes: `bibliotecas_de_programa`, `rutas_de_bibliotecas` (D2-5); `qualify(dataset)` (`sgm.ir.builder`); `Operator.params` (`outputs`, `inputs`); `Plan`; `PendienteMigracion`.
- Produces:
  ```python
  def aplicar_permanentes(
      plan: Plan, bibliotecas: Mapping[str, InfoLibname]
  ) -> tuple[Plan, list[PendienteMigracion]]:
      """Toda escritura a `lib.t` de una biblioteca de ruta se vuelve un `write_file` a
      `<ruta>/t.csv` (delimitado, con cabecera) y toda lectura de `lib.t`, un `read_file` del mismo
      archivo. Aviso `A-DATASET-PERMANENTE-A-ARCHIVO` por tabla. Biblioteca de base:
      `P-LIBNAME-BASE` (D2-4); sin LIBNAME: `P-BIBLIOTECA-SIN-DEFINIR`."""
  ```

**Caso `L0/l0_31_biblioteca_permanente` (`capa: C`, `estado: revisado`, razonamiento: «MG-D03: archivo de preparación; lestmtsref, p. 233 (LIBNAME) y 134/97 (INFILE y FILE)»).**
```sas
LIBNAME dat '.../datos_permanentes';
PROC IMPORT DATAFILE='.../entradas/nuevos.csv' OUT=WORK.nuevos DBMS=CSV REPLACE; GETNAMES=YES; RUN;
DATA dat.clientes;
  SET WORK.nuevos;
  KEEP id nombre;
RUN;
DATA WORK.leido;
  SET dat.clientes;
  activo = 1;
RUN;
```
`nuevos.csv`: `id,nombre,otro` / `1,Ana,x` / `2,Luis,y`. Esperado a mano: `esperado/clientes.csv` (el archivo de preparación): `id,nombre` / `1,Ana` / `2,Luis`; `esperado/leido.csv`: `id,nombre,activo` / `1,Ana,1` / `2,Luis,1`. El programa migra con un aviso `A-DATASET-PERMANENTE-A-ARCHIVO` y `contextos/Default.yaml` trae `ruta_lib_dat`. Invariante: `filas(clientes) == filas(leido) == 2`.

- [ ] **Step 1: Write the failing tests.** `aplicar_permanentes` del caso: el `write_file` de `dat.clientes` y el `read_file` de `dat.clientes` comparten la ruta `<ruta_lib_dat>/clientes.csv`; el aviso aparece una vez por tabla; una lectura de `dat.otra` que ningún paso escribe conserva la ruta y no inventa columnas (`P-ESQUEMA-VACIO`); sin `LIBNAME dat` da `P-BIBLIOTECA-SIN-DEFINIR`; el caso coincide en el anillo B con los dos esperados.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_pase_permanentes.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement** y anotar en `PROGRESS.md`, «Decisiones», la aplicación de MG-D03 con la alternativa y lo que cambia.
- [ ] **Step 4: Run** los tests, `tests/unit/test_bibliotecas_ruta.py`, el golden y `uv run ruff check src tests tools`.
- [ ] **Step 5: Studio.** `uv run python tools/validar_caso_studio.py l0_31_biblioteca_permanente`; sin Studio, «lote C pendiente».
- [ ] **Step 6: Commit.** `hito N n: datasets permanentes a archivo de preparacion con aviso (MG-D03)`.

---

### Task D2-Gate: `L0` completo y casos de base en lote C (serie `n`)

**Criterio de salida** (MG-P2 y la parte de entrada y salida de la compuerta GM1; leer su texto con `grep -n "GM1" docs/plan-reescritura/plan-migrador-general.md` antes de empezar; lo siguiente es lo que este plan se compromete a probar):
1. **Anillo B:** los 15 casos de `L0` anteriores y `l0_16` a `l0_31` coinciden con su `esperado/` en el intérprete (`tests/unit/test_migrar_corpus_anillo_b.py`); `CONOCIDOS` solo contiene casos con pendiente de alcance con motivo y página.
2. **Anillo A:** en `migrar_pendientes.yaml` no queda ningún caso de `L0` salvo los que declaran `P-` de alcance (`P-COMPONENTE-SIN-PLANTILLA` si falta Studio, `P-FILENAME-PIPE`, `P-CONEXION-OPCIONES`, `P-XLS-SIN-EJECUCION`), cada uno con su página o su motivo.
3. **Lote C de archivos:** una sola corrida de Studio con `l0_19` a `l0_28`, `l0_30` y `l0_31`: `uv run python tools/corpus_studio.py lote <casos> --jobs <carpeta> --proyecto <proyecto>` para compilar y `uv run python tools/validar_caso_studio.py <casos>` para ejecutar y comparar. Se miden tres cosas que las tareas dejaron abiertas: el nulo de `tFileInputDelimited` en línea corta (D2-9), las comillas de `tFileOutputDelimited` con `|` (D2-11) y el ancho de `tFileInputPositional` (D2-10).
4. **Lote C de bases** (con Docker y los contenedores arriba, K-4): `l0_16`, `l0_17` y `l0_18` con `--contexto-dev env/contexto_dev.json` y `env/contexto_dev_postgres.json`. Sin Docker: «contenedor pendiente».
5. **Programa grande:** repetir `uv run python tools/linea_base_es.py tests/corpus --programa tests/fixtures/sas/client/client_large.sas` y comparar con D2-1: los `CONNECT TO` resueltos como lector (D2-2) y los `PROC UPLOAD/DOWNLOAD` resueltos (K-5 y D2-17).

- [ ] **Step 1: Run** la suite completa `uv run python -m pytest -q` y `uv run ruff check src tests tools`.
- [ ] **Step 2: Run** `tools/linea_base_es.py` y comparar con D2-1; pegar las dos cifras en `PROGRESS.md`.
- [ ] **Step 3: Run** los lotes C (puntos 3 y 4). Si Studio no conecta: `sgm studio salud` y `docs/guia-validacion-studio.md`, sección 7; no se reinstala nada ni se cambia `talend-mcp`. El resultado es «lote C pendiente» con el motivo y la compuerta **no** se declara cerrada.
- [ ] **Step 4: Registrar** en `PROGRESS.md` el hito de cierre: casos por anillo (A, B, C), pendientes por código, horas acreditadas de MG-P2 con el método de la sección 11b, y qué quedó fuera con su motivo. Actualizar la tabla MG-P2 y su «Estado» (líneas 506-520 del plan maestro) y la fila `MG-P2` de la tabla de avance (línea 887) en el mismo cambio.
- [ ] **Step 5: Commit.** `hito N n: MG-P2 cerrado: L0 completo en B y lote C de entrada y salida`.

---

## Resumen de horas

| Tareas | Origen | Serie | Horas |
|---|---|---|---|
| D2-1 | línea base | n | 1 |
| D2-2, D2-3 | MG-P2-05 | n | 4 |
| D2-4, D2-5 | MG-P2-04 | n | 5 |
| D2-6, D2-7, D2-8 | MG-P2-01 | n | 7 |
| D2-9, D2-10, D2-11 | MG-P2-02 | n | 10 |
| D2-12, D2-13, D2-14 | MG-P2-03 | n | 6 |
| D2-15, D2-16, D2-17 | MG-P2-06 | n | 3 |
| D2-18 | MG-P2-07 | n | 1 |
| D2-Gate | cierre | n | 1 |
| **Total** | | | **38** (MG-P2 restante) |

Las horas por tarea son estimaciones del plan; el crédito real se mide con el método de la sección 11b del plan maestro. Orden recomendado: D2-1, **D2-2** (lo que más programas desbloquea: unos 125 `CONNECT TO impala`), D2-3, D2-4, D2-5, luego la Parte II y la Parte III en orden (D2-12 y D2-13 necesitan D2-9), y la Parte IV (D2-18 necesita D2-5 y D2-15).

## Dependencias

**Necesita de otros planes**

| De | Tarea | Para qué |
|---|---|---|
| Plan K | K-4 (`desde_plan_conexion.py`, `env/contexto_dev.json`, `consultar`, `conexion_en_contexto`) | D2-2 a D2-4: host, puerto y base por contexto; sin K-4 D2-2 deja la conexión vacía como hoy (`P-CONEXION-BASE`) y los pasos de Studio quedan «lote C pendiente» |
| Plan K | K-3 (carga tipada a los contenedores) y los contenedores `tools/contenedores/impala` y `postgres` | D2-2 Step 6, D2-3 Step 5 y D2-4 Step 5 |
| Plan K | K-5 (`pase_copias_remotas.py`) y K-9 (`preparar_plan.py`) | D2-17 (no modifica K-5: módulo propio) y D2-15 y D2-18 (una llamada en `preparar_plan.py`; si K-9 no está integrado, la llamada va en `cli_migrar.py`) |
| Plan D1 | D1-15 a D1-17 (`parsear_informat`, `Informat`, `YEARCUTOFF`, `PUT` con formatos) | D2-10, D2-12, D2-13 y D2-14 (el emisor deja la conversión de informats a las expresiones de D1; antes, `P-INFORMAT-SIN-SOPORTE`) |
| Plan A | compilación y validación en Studio (`tools/validar_caso_studio.py`, `tools/corpus_studio.py lote`, salud con estados) | todos los pasos de Studio y el lote C de D2-Gate |
| Plan C | C-2 (extrae `interprete.py`) | D2-2, D2-6 y D2-7 agregan una línea cada una en `interprete.py` (rama `read`/`read_file`/`write_file`); quien llegue segundo hace rebase y el golden no cambia |
| Plan E | MG-P7-04 (macrovariables) | D2-2: un SQL con `&ANIO.` deja `P-PASO-DIRECTO-MACRO` hasta que el expansor lo resuelva (`L8/totales/07` lo necesita) |
| Plan F2 / Studio | extracción de plantillas | `tFileOutputExcel` (D2-7), `tFileInputPositional` (D2-10), `tFileOutputPositional` (D2-14), `tPostgresqlInput` (D2-3) y `tFTPGet` (D2-16): F2-4 extrae los de archivos; sin Studio quedan `P-COMPONENTE-SIN-PLANTILLA` |

**Entrega a otros planes**

| A | Qué |
|---|---|
| Plan F2 (emisor y joblets) | `desde_plan_paso_directo.py`, `desde_plan_conexiones.py`, `desde_plan_excel.py`, `desde_plan_infile.py`, `desde_plan_posicional.py` y `desde_plan_file_put.py` (nodos de entrada y salida, para segmentar en joblets) |
| Plan G (verificación) | los casos `l0_16` a `l0_31` y `tools/linea_base_es.py`; la numeración `l0_16` a `l0_39` queda reservada a este plan |
| Plan E | `filerefs_de_programa` y `bibliotecas_de_programa` (variables de contexto de ruta) |
| Plan D1 | `formatos/informat_archivo.py` y `formato_archivo.py` como consumidores de `parsear_informat` y de `parsear_formato` |

## Self-review

- **Cobertura de la spec:** MG-P2-01 en D2-6 a D2-8 (XLSX, XLS, `GUESSINGROWS`, `GETNAMES`, hallazgo de `PASSWORD`); MG-P2-02 en D2-9 a D2-11 (lista, columna, formateado, `DSD`, `MISSOVER`, `TRUNCOVER`, `FILE`, `PUT`); MG-P2-03 en D2-12 a D2-14 (`w.d`, `COMMAw.d`, `DOLLAR`, `YYMMDD`, `DDMMYY`, `DATE9`, `ANYDTDTE`, contrato con D1); MG-P2-04 en D2-4 y D2-5; MG-P2-05 en D2-2 y D2-3 (prioridad); MG-P2-06 en D2-15 a D2-17 (archivo, pipe, FTP, `RSUBMIT`, `UPLOAD`, `DOWNLOAD`, contrato con K-5); MG-P2-07 en D2-18; el cierre en D2-Gate.
- **Páginas verificadas al redactar** (existen en el `.INDEX.md`): `proc` p. 901, 904, 908, 910, 1373, 1380, 1385, 1387, 1388; `lestmtsref` p. 97, 120, 122, 134, 177, 195, 199, 204, 233, 277, 301; `leforinforref` p. 181, 186, 235, 616, 617, 646, 649, 653, 744, 755; `sqlproc` p. 213, 214, 287, 301, 392; `connref` p. 151, 185, 206, 245, 285, 286; `hostunx` p. 132. Las que se marcan «verificar» en un paso no se pudieron leer completas al redactar y la tarea las lee antes de fijar el esperado (en especial: la frase de `DSD` en `FILE`, la división por `10**d` en p. 744, `DATAROW` en p. 1385 y las páginas de `PUT` formateado).
- **Lo que no tiene página y queda `Pendiente:`:** opciones de `LIBNAME` y `CONNECT` por motor (`P-CONEXION-OPCIONES`, `P-LIBNAME-BASE`), tipos de columna de Excel (`P-TIPO-EXCEL`), lectura de XLS en el intérprete (`P-XLS-SIN-EJECUCION`), `FLOWOVER` (`P-INFILE-FLOWOVER`), `FILENAME PIPE` (`P-FILENAME-PIPE`), `ANYDTDTE` ambiguo (`P-ANYDTDTE-DATESTYLE`), `DOLLAR` como informat si el índice no lo trae (`P-INFORMAT-DOLLAR-SIN-PAGINA`), `RSUBMIT` asíncrono (`P-RSUBMIT-ASINCRONO`), SQL de paso directo con macrovariables (`P-PASO-DIRECTO-MACRO`).
- **Decisiones documentadas con alternativa:** SQL interior sin normalizar (D2-2), `GUESSINGROWS` como aviso con tipos fijados (D2-8), `fileref` resuelto por pase y `PIPE` pendiente (D2-15), `RSUBMIT` como alias local (D2-17) y datasets permanentes a archivo (D2-18).
- **Archivos por encima de 300 líneas:** `desde_plan.py`, `interprete.py` y `desde_plan_nodos.py` (299): ninguna tarea les suma más de una llamada; D2-6 extrae primero `lower_procs_archivos.py` y `desde_plan_excel.py`.
- **Prueba que se modifica:** ninguna; solo se agregan. Los 15 casos de `L0` anteriores y el golden deben quedar idénticos tras cada tarea.
- **Riesgo de coordinación:** `desde_plan.py` y `interprete.py` son zonas de Andres (emisor) y de C/B (intérprete): D2-2, D2-6 y D2-7 avisan antes y aplican el cambio sobre la versión sin commitear si la hay. La serie `n` la comparten C (procedimientos) y K (datos): el número de hito es único y se toma al ejecutar.
- **Proporción:** 18 tareas más la de cierre para 38 h; los cuerpos de funciones los decide quien implementa.
