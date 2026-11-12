# MG-K: Datos de prueba y bases simuladas Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Que los dos programas reales del usuario (el pequeño `client_poc.sas` y el grande `client_large.sas`) tengan un esperado reproducible sin SAS real, sin Impala real y sin `sashelp` en esta máquina: fixtures sintéticos y deterministas con ficha (`origen: sintetico`), esquemas inferidos del propio programa, un generador de datos por esquema que carga los contenedores `sgmtest_`, un contexto `DEV` que apunta a esos contenedores, `RSUBMIT`/`PROC UPLOAD`/`PROC DOWNLOAD` simulados como copias locales, el programa pequeño de punta a punta y el grande por cinco rebanadas verticales. Nada de esto se presenta nunca como dato real.

**Architecture:** Cuatro zonas. (1) `tools/datos_sinteticos/` (nuevo): fichas, generadores y requisitos de datos por rebanada; solo herramientas, no entra en `src/`. (2) `tests/fixtures/datos/` (nuevo): los CSV sintéticos con su ficha y el catálogo. (3) `src/sgm/migrar/` y `src/sgm/ir/`: inferencia de esquemas desde el programa y dos pases de plan nuevos (tablas de biblioteca local a lectura de archivo; copias remotas a alias de ruta), cada uno en un módulo nuevo para no pisar `lower_procs.py` ni `interprete.py` del Plan B. (4) `src/sgm/talend_item/desde_plan_contextos.py`: el grupo `DEV` del contexto con host, puerto y base de los contenedores; el Job queda igual en los cuatro entornos y solo cambia el valor.

**Tech Stack:** Python 3.12, pytest, ruff; `uv run python -m pytest` y `uv run python -m sgm.cli` (en este Windows `uv run pytest` puede bloquearse por Control de aplicaciones). Docker solo para los contenedores `sgmtest_` ya existentes (`tools/contenedores/impala`, `tools/contenedores/postgres`).

**Spec:** `docs/superpowers/plans/2026-11-11-ruta-al-100.md` (sección «Plan K», tareas K-1 a K-7, y la nota de `MG-P2-05`/`MG-P2-06`), `docs/plan-reescritura/plan-migrador-general.md` (MG-P2-04 a MG-P2-06, MG-P6-04, MG-P7-01, MG-P13-01) y `docs/plan-reescritura/reparto-andres-byron.md` (carril de Byron: `src/sgm/migrar/interprete.py`, `tools/`, corpus de datos).

**Horas:** 30 h (K-1 a K-13 y K-Gate; ver «Resumen de horas»).

## Global Constraints

- Sin `git push` ni `--amend`. Un commit local por tarea con el mensaje `hito N n: <resumen>` (letra `n`, serie de Byron en este plan) y, al final del mensaje, la línea `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Antes de escribir, buscar el último `## Hito` de `PROGRESS.md` (al redactar este plan era el 198) y sumar uno; si otra sesión ya tomó el número, tomar el siguiente. No renumerar entradas publicadas. `PROGRESS.md` se actualiza al cerrar cada tarea que sea un hito (fecha, qué se hizo, pruebas, métricas, bloqueos, decisiones).
- No tocar `tools/ci.py`, `tools/validacion.py`, `tools/instalar_ganchos.py`, `README.md`, `.githooks/` ni `.claude/` (son del Plan A y están sin commitear). Los archivos de `src/sgm/ir/` y `src/sgm/migrar/` que modifica el Plan B (`lower_procs.py`, `lower_data*.py`, `operadores.py`, `interprete.py`, `esquemas.py`, `esquemas_tipos.py`) **no se editan aquí**: todo lo de este plan va en módulos nuevos, con una sola línea de enganche en `cli_migrar.py`. Si una tarea necesita cambiar uno de ellos, se anota como dependencia y se pide al dueño.
- **Datos sintéticos, nunca reales.** Cada archivo de datos que genera este plan lleva una ficha `<tabla>.ficha.yaml` con `origen: sintetico`, `semilla`, `generador`, columnas con su tipo declarado y `filas`. Sin datos personales: nombres ficticios evidentes, sin correos, sin números de documento de 7 o más dígitos, sin teléfonos. El mismo `semilla` produce los mismos bytes en dos corridas. Lo vigila K-11.
- **No leer ni citar `Cod2.txt` de Descargas** (tiene una contraseña en claro en la línea 77 de su copia). Los programas reales entran solo por las copias redactadas del repositorio: `tests/fixtures/sas/client/client_poc.sas` y `tests/fixtures/sas/client/client_large.sas`. Toda salida, rebanada, ficha y `out/` pasa por `sgm secretos` (`uv run python -m sgm.cli secretos <ruta>`) y sale limpia.
- Si el SAS no demuestra un tipo, una columna, un valor o una equivalencia: `Pendiente:` con motivo y código `P-xxx`. Un tipo no demostrado queda `String` con `P-TIPO-DESCONOCIDO`. **Excepción acotada:** un catálogo de fixtures declarado (la ficha de `sashelp.cars`, por ejemplo) puede aportar el tipo; entonces la columna lleva `source="fixture"` y el informe dice que el tipo lo declara el fixture, no el SAS.
- Si no hay página de la guía SAS, no hay equivalencia. Cada regla nueva cita `<guía>, p. N` con una página que exista en `docs/referencia/sas/<guía>.INDEX.md` (`tests/unit/test_catalogo_sas.py` lo vigila). No leer el PDF ni el `.txt` entero: ubicar la sección en el `.INDEX.md` y la página con `grep -n "<!-- página N -->" docs/referencia/sas/<guía>.txt`. Páginas ya ubicadas para este plan: `proc.pdf`: `APPEND Procedure` p. 161, sintaxis p. 162; `DELETE Procedure` p. 23 del resumen y `DELETE Statement` de `DATASETS` p. 366; `SORT Procedure` p. 2449; `connref.pdf`: `SIGNON Statement` p. 151, `RSUBMIT Statement` p. 185, `ENDRSUBMIT Statement` p. 206, `UPLOAD Procedure` p. 245 (sintaxis p. 246), `DOWNLOAD Procedure` p. 285 (sintaxis p. 286).
- Nada de nombres de scripts de ejemplo (`cod1`, `cod2`, `cars_poc`, `exogena`, `split2`, `split3`, `executeBulkload`, `waitForBulkLoads`, `bulkload_generic`) en `src/` ni en `rules/`; lo vigila `tests/unit/test_no_script_specific_names.py`. En `tools/`, `tests/`, `decisiones/` y este plan sí pueden aparecer. Lo que depende del nombre del cliente va a `decisiones/<programa>.*.yaml`.
- No guardar secretos. El contexto `DEV` lleva solo host, puerto y base de los contenedores desechables (`localhost`, `21050`, `default`; la contraseña `sgmtest_pw_local` de Postgres es de un contenedor de prueba y se queda en su compose, no se copia a contextos). Una variable de contexto cuyo nombre case con `pass|pwd|secret|token|clave` se escribe vacía (regla ya vigente en `cli_migrar.py`).
- No borrar ni debilitar pruebas. Un caso que no se puede traducir queda en `tests/corpus/migrar_pendientes.yaml` con su motivo; no se quita del corpus.
- Archivos de código de menos de 300 líneas. Hoy ya pasan de 300: `src/sgm/cli_migrar.py` (331). La tarea que lo toca extrae primero el bloque a un módulo nuevo, sin cambio de comportamiento, en un paso propio. `src/sgm/cli.py` tiene 299 líneas: K-2 extrae `env_app` a `cli_env.py` antes de registrar el comando nuevo.
- Código e identificadores en inglés (los nombres de operadores del plan están en español y se conservan; las herramientas de `tools/` usan nombres en español como el resto del repositorio); comentarios, docstrings y mensajes en español.
- Después de cada tarea: `uv run python -m pytest -q` y `uv run ruff check src tests tools` en verde. En los pasos de cada tarea se corre primero solo el archivo de prueba nuevo; la suite completa se corre una vez al cierre de la tarea.
- **Docker y Studio, solo en puntos marcados.** Las pruebas que necesitan contenedores llevan la marca `contenedores` y no corren por omisión (K-3 agrega la marca a `pyproject.toml`). Studio se usa en cuatro puntos y nada más: K-4 (un Job de base), K-6 (programa pequeño), K-7 (un lote con las cinco rebanadas) y K-Gate. Si `sgm studio salud` no conecta, no reinstalar nada ni cambiar `talend-mcp` (`docs/guia-validacion-studio.md`, sección 7); la validación queda «lote C pendiente» con su motivo y no se cuenta como pasada. Si Docker no está arriba, la parte de contenedor queda «contenedor pendiente» con su motivo, y el resto de la tarea (SQL generado, anillos A y B) sí se cierra.

## Review Focus

- **Un fixture sintético nunca se presenta como real.** Cada CSV bajo `tests/fixtures/datos/` y cada `entradas/` generada por este plan tiene ficha con `origen: sintetico`; los informes de `sgm migrar` que usan una tabla local la listan como «datos de prueba sintéticos»; un `caso.yaml` que usa un fixture lo dice en `supuestos`. Test en K-11.
- **Un esquema inferido no es un catálogo.** `env/schemas/` es catálogo demostrado (`source="catalog"`). Lo que sale de `sgm esquemas --desde-programa` se escribe en `out/esquemas/` con `"_inferido": true` y `type: null` para lo no demostrado, y `esquemas_de_entrada` nunca lo recibe por sí solo. Test en K-2.
- **No se inventan tipos ni valores.** El generador de datos no deduce un tipo del nombre de una columna. Un valor que una condición del programa exige (`Make = 'Acura'`) sale del programa, no de una lista fija. Test en K-3 y K-10.
- **El esperado del intérprete no es SAS.** `esperado/` de las rebanadas de K-7 sale del intérprete (anillo B) y, donde es SQL puro, también del oráculo SQLite de `tools/corpus_lib/oraculo.py`; los dos tienen que coincidir. Los casos quedan en estado `parcial` con el motivo «esperado calculado sin SAS real» hasta que el usuario lo contraste con una corrida real. Test en K-8 y K-7a a K-7e.
- **El doble de un `PROC APPEND` sobre sí mismo no está en la guía** (`proc.pdf`, p. 161 y 162 no lo dicen). Solo lo demuestra el comentario del propio programa (14.024.704 filas son 428 x 2^15). El caso lo declara como supuesto con `Pendiente: P-APPEND-MISMA-TABLA` hasta que haya una corrida real. Test en K-6.
- **`RSUBMIT`, `PROC UPLOAD` y `PROC DOWNLOAD` no se ejecutan: se resuelven como alias de ruta.** Una copia con `DATA=`/`OUT=` (de dataset, no de archivo) o con una ruta dinámica queda `Pendiente:`. Test en K-5.
- **Las rutas de los contenedores no entran al `.item`.** Host, puerto y base viven en el contexto; el Job es idéntico en `Default`, `DEV`, `QA` y `PROD`. Test en K-4.

## Orden de ejecución

Los números K-1 a K-7 son los del plan maestro de planes y no se renumeran (los citan `ruta-al-100.md` y el Plan B). Las tareas K-8 a K-13 las pide la ampliación y se ejecutan en este orden:

`K-1` -> `K-8` (rebanador y esperado) -> `K-2` -> `K-9` (tablas locales) -> `K-3` -> `K-10` (requisitos de datos) -> `K-4` -> `K-5` -> `K-6` -> `K-13` (preparar datos de una rebanada) -> `K-7` -> `K-7a` ... `K-7e` -> `K-11` -> `K-12` -> `K-Gate`. En el archivo, K-8 está después de K-1 y K-13 después de K-6, que es el orden de ejecución.

---

## Parte I. Fixtures y esquemas

### Task K-1: Fixture sintético de `sashelp.cars` con ficha y semilla

El programa pequeño hace `set sashelp.cars;` y consulta cuatro marcas (`Acura`, `BMW`, `Chevrolet`, `Jaguar`: las citan sus `WHERE ( CARS_POC.Make = '...' )`). No hay `sashelp` en esta máquina. Si el usuario exporta el real (`proc export data=sashelp.cars outfile=... dbms=csv; run;`) se usa ese y la ficha pasa a `origen: real` con su `procedencia`; mientras no, este conjunto sintético con las mismas 15 columnas.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\datos_sinteticos\__init__.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\datos_sinteticos\ficha.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\datos_sinteticos\cars.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\fixtures\datos\sashelp\cars.csv`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\fixtures\datos\sashelp\cars.ficha.yaml`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_datos_cars.py`

**Interfaces:**
- Consumes (`tools/corpus_lib/datos_ficticios.py`, ya existe): `SEMILLA = 20261104`, `escribir_entrada(carpeta: Path, nombre: str, encabezado: list[str], filas: list[list[str]]) -> None` (CSV con `,`, comillas mínimas y fin de línea `\n`).
- Produces:
  ```python
  # tools/datos_sinteticos/ficha.py
  @dataclass(frozen=True)
  class Ficha:
      tabla: str                      # "sashelp.cars"
      origen: str                     # "sintetico" | "real"
      filas: int
      columnas: dict[str, str]        # nombre -> "String" | "Double" (tipo que declara el fixture)
      semilla: int | None = None      # obligatoria si origen == "sintetico"
      generador: str | None = None    # "tools/datos_sinteticos/cars.py:generar_cars"
      procedencia: str | None = None  # obligatoria si origen == "real"
      nota: str = ""

  def leer_ficha(ruta: Path) -> Ficha: ...
  def escribir_ficha(ficha: Ficha, ruta: Path) -> None: ...
  def validar_ficha(ficha: Ficha, csv: Path) -> list[str]:
      """Errores (vacía si está bien): origen válido; semilla y generador si es sintético;
      procedencia si es real; el encabezado del CSV es `ficha.columnas` en orden; `filas` coincide."""

  # tools/datos_sinteticos/cars.py
  SEMILLA_CARS: int = 20261111
  COLUMNAS: tuple[tuple[str, str], ...]   # las 15 en orden: Make..Length, con String/Double
  MARCAS: dict[str, int]                   # {"Acura": 4, "Audi": 3, "BMW": 6, "Chevrolet": 8,
                                           #  "Ford": 5, "Honda": 4, "Jaguar": 3, "Toyota": 7}  (40 filas)
  def generar_cars(semilla: int = SEMILLA_CARS) -> tuple[list[str], list[list[str]]]: ...
  def escribir_cars(destino: Path, semilla: int = SEMILLA_CARS) -> Path:
      """Escribe `cars.csv` y `cars.ficha.yaml` en `destino`; devuelve la ruta del CSV."""
  ```
  Reglas de valores (inventadas y declaradas como tales en la ficha, ningún valor sale de la tabla real): `Model = "<Make> SIM-<nn>"`; `Type` entre `Sedan, SUV, Sports, Wagon, Truck`; `Origin` entre `Asia, Europe, USA`; `DriveTrain` entre `Front, Rear, All`; `MSRP` entero entre 18000 y 90000; `Invoice = round(MSRP * 0.93)` (siempre menor que `MSRP`); `EngineSize` 1.4 a 5.0; `Cylinders` en `{4, 6, 8}`; `Horsepower` 110 a 450; `MPG_City` 12 a 35; `MPG_Highway = MPG_City + 5..9`; `Weight` 2400 a 5500; `Wheelbase` 96 a 125; `Length` 160 a 215. Las 40 filas salen en orden de marca fijo (el de `MARCAS`).

- [ ] **Step 1: Write the failing test.** `test_datos_cars.py` (agrega `tools` al `sys.path` como `tests/unit/test_migrar_corpus_anillo_b.py`): (a) `generar_cars()` devuelve exactamente la cabecera `["Make","Model","Type","Origin","DriveTrain","MSRP","Invoice","EngineSize","Cylinders","Horsepower","MPG_City","MPG_Highway","Weight","Wheelbase","Length"]` y 40 filas; (b) `Counter(fila[0])` es `MARCAS`; (c) dos llamadas con la misma semilla dan lo mismo y `generar_cars(1)` es distinto; (d) para todas las filas `int(Invoice) < int(MSRP)` y `int(MPG_Highway) > int(MPG_City)`; (e) **las marcas salen del programa**: con `re.findall(r"Make\s*=\s*'([^']+)'", client_poc.sas)` (cuatro marcas, `tests/fixtures/sas/client/client_poc.sas`) cada una está en la columna `Make` del CSV versionado; (f) `tests/fixtures/datos/sashelp/cars.csv` es byte a byte lo que escribe `escribir_cars(tmp_path)` (sin deriva); (g) `validar_ficha(leer_ficha(cars.ficha.yaml), cars.csv) == []`, `origen == "sintetico"` y `semilla == 20261111`; (h) una ficha sintética sin `semilla` da el error `"origen sintetico sin semilla"`.
- [ ] **Step 2: Run test to verify it fails.** `uv run python -m pytest tests/unit/test_datos_cars.py -q -p no:cacheprovider`; esperado: `ModuleNotFoundError: datos_sinteticos`.
- [ ] **Step 3: Implement.** `ficha.py` con `yaml.safe_dump(sort_keys=False)`; `cars.py` con `random.Random(f"{semilla}:sashelp.cars")` (misma convención que `datos_ficticios.generar_tabla`) y `escribir_entrada` para el CSV. Generar con `uv run python -c "import sys; sys.path.insert(0,'tools'); from datos_sinteticos.cars import escribir_cars; from pathlib import Path; escribir_cars(Path('tests/fixtures/datos/sashelp'))"`. La ficha lleva `nota: "Conjunto sintetico con las 15 columnas de sashelp.cars; los valores son inventados. Reemplazar por la exportacion real cuando el usuario la aporte."` y `columnas` con `String` para `Make, Model, Type, Origin, DriveTrain` y `Double` para las diez restantes; el tipo lo declara el fixture, no el SAS (anotarlo en `nota`).
- [ ] **Step 4: Run test to verify it passes**, luego `uv run python -m sgm.cli secretos tests/fixtures/datos` (esperado: 0 hallazgos) y `uv run ruff check src tests tools`.
- [ ] **Step 5: Commit.** `hito N n: fixture sintetico de sashelp.cars con ficha y semilla`, con la línea `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.

---

### Task K-8: Rebanador de programas reales y esperado del intérprete

Los dos programas reales no se migran enteros: cada rebanada es un fragmento literal del programa con sus entradas. Este rebanador corta por rangos de línea, comprueba que el fragmento sigue siendo el del original (hash) y calcula el `esperado/` con el intérprete de referencia.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\rebanar_programa.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\corpus_lib\esperado_interprete.py`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_rebanar_programa.py`

**Interfaces:**
- Consumes: `analyze_program(files: dict[str, str])` (`sgm.frontend.program`), `compile_file(analysis, name: str, base)` y `project_base()` (`sgm.compile`), `ejecutar_plan(plan: Plan, entradas: dict[str, list[dict[str, str | None]]]) -> dict[str, list[dict[str, str | None]]]` (`sgm.migrar.interprete`); `Tabla(columnas: list[str], filas: list[tuple], tipos: list[str])`, `leer_entradas(carpeta: Path) -> dict[str, Tabla]`, `escribir_csv(ruta: Path, tabla: Tabla) -> None` (`corpus_lib.csv_tabla`); `Caso` y `cargar_caso(directorio: Path) -> Caso` (`corpus_lib.caso`).
- Produces:
  ```python
  # tools/rebanar_programa.py
  @dataclass(frozen=True)
  class Rebanada:
      fuente: str                   # "tests/fixtures/sas/client/client_large.sas"
      rangos: tuple[tuple[int, int], ...]   # líneas 1-based, inclusivas, en orden
      sha256: str                   # del texto ORIGINAL de los rangos, unidos por "\n\n"
      prologo: str = ""             # líneas que se anteponen (por ejemplo `%let repeticiones = 15;`)
      sustituciones: tuple[tuple[str, str], ...] = ()   # (de, a): cada `de` aparece una sola vez

  def rebanar(texto: str, rangos: Sequence[tuple[int, int]]) -> str:
      """Une los rangos (línea inicial y final inclusivas) separados por una línea en blanco.
      Un rango fuera del texto o invertido lanza ValueError con el rango."""

  def huella(texto_rebanado: str) -> str: ...
  def armar(rebanada: Rebanada, texto_fuente: str) -> str:
      """`prologo` + el texto de los rangos con las `sustituciones` aplicadas. Una sustitución
      cuyo `de` no aparece exactamente una vez lanza ValueError. Es la única edición permitida
      sobre el programa real y queda escrita en `rebanada.yaml`."""
  def verificar(rebanada: Rebanada, raiz: Path) -> list[str]:
      """Errores: la fuente no existe, o el texto de los rangos ya no tiene la huella guardada."""
  def escribir_rebanada(destino: Path, rebanada: Rebanada, texto_fuente: str) -> list[Path]:
      """Escribe `destino/programa.sas` (salida de `armar`) y `destino/rebanada.yaml`."""
  def leer_rebanada(ruta: Path) -> Rebanada: ...

  # tools/corpus_lib/esperado_interprete.py
  def calcular(caso: Caso, repeticiones: dict[str, int] | None = None) -> dict[str, Tabla]:
      """Ejecuta `caso.programa` en el intérprete con las `entradas/` del caso; devuelve las tablas
      de `caso.salidas`, en el orden de ejecución. `repeticiones` reemplaza el número de la línea
      `%let <nombre> = <número>;` del programa (por ejemplo {"repeticiones": 3}); si el programa
      no tiene esa línea lanza ValueError."""
  def escribir(caso: Caso, tablas: dict[str, Tabla]) -> list[Path]:
      """Escribe `esperado/<tabla>.csv` con `escribir_csv`; devuelve las rutas."""
  ```
  Cada rebanada guarda `rebanada.yaml` junto a su `caso.yaml` con `fuente`, `rangos` y `sha256`.

- [ ] **Step 1: Write the failing test.** (a) `rebanar("a\nb\nc\nd\ne\n", [(2, 3), (5, 5)]) == "b\nc\n\ne\n"`; (b) `rebanar("a\nb", [(3, 3)])` y `rebanar("a\nb", [(2, 1)])` lanzan `ValueError`; (c) `verificar` con una `Rebanada` cuya huella no coincide devuelve un error que nombra la fuente; (d) con un caso mínimo en `tmp_path/L8/c1` (el cargador exige una carpeta de nivel; `programa.sas` con `data WORK.s; set WORK.e; where x > 1; run;`, `entradas/e.csv` con `x` = `1,2,3`, `caso.yaml` válido de nivel L8 con `salidas: [s]`), `calcular(caso)["s"].filas == [(2,), (3,)]` y `escribir` crea `esperado/s.csv` con tres líneas (cabecera y dos filas); (e) `armar` con `prologo="%let n = 15;"` y `sustituciones=(("%to 15", "%to &n."),)` sobre un texto con `%do i=1 %to 15;` da `%let n = 15;` en la primera línea y `%to &n.`, y con un `de` repetido o ausente lanza `ValueError`; (f) `calcular(caso, {"n": 3})` sobre un programa con `%let n = 15;` cambia el 15 por 3 y sin ese `%let` lanza `ValueError`; (g) `tests/fixtures/sas/client/client_large.sas`: `rebanar(texto, [(160, 164)])` empieza con `proc import datafile='/work_sasstudio/pcfiles/Base_datos_Nequi.csv'` (la línea 160 al redactar este plan).
- [ ] **Step 2: Run test to verify it fails.** `uv run python -m pytest tests/unit/test_rebanar_programa.py -q -p no:cacheprovider`; esperado: módulo no existe.
- [ ] **Step 3: Implement** las funciones. `calcular` usa la ruta de `tests/unit/test_migrar_corpus_anillo_b.py` (analizar, compilar a plan, `ejecutar_plan`) y convierte `Tabla` a `list[dict]` con `dict(zip(columnas, fila, strict=True))`. No escribe en el repositorio por sí solo: `escribir` lo hace quien lo llama.
- [ ] **Step 4: Run test to verify it passes** y `uv run ruff check src tests tools`.
- [ ] **Step 5: Commit.** `hito N n: rebanador de programas reales y esperado del interprete`, con la línea `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.

---

### Task K-2: `sgm esquemas --desde-programa`

Hoy `esquemas_de_entrada` (`src/sgm/migrar/esquemas.py`) deduce columnas solo de los `PROC IMPORT` del plan, y la lista de columnas que usa cada tabla de base sale de `tools/contenedores/fuentes_sas.py` (fuera de `src/`). Esta tarea sube esa lógica a `src/` y la expone como comando, sin tocar `esquemas.py` ni `esquemas_tipos.py` (Plan B las modifica en B-2 a B-4).

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\esquemas_programa.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\cli_esquemas.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\cli_env.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\cli.py` (hoy 299 líneas: extraer `env_app` a `cli_env.py`, líneas 201 a 217, y registrar `esquemas`)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\contenedores\fuentes_sas.py` (delegar en `esquemas_programa`, misma API pública)
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_esquemas_programa.py`

**Interfaces:**
- Consumes: `Column(name: str, type: str | None = None, length: int | None = None, source: str = "unknown")` (`sgm.ir.models`); `PendienteMigracion(codigo, motivo, linea)` y `esquemas_de_entrada(plan: Plan, catalogo: dict[str, list[Column]], muestra: Path | None = None) -> tuple[dict[str, list[Column]], list[PendienteMigracion]]` (`sgm.migrar.esquemas`); `columnas_usadas(texto: str, dataset: str) -> list[str]` (`sgm.proceso.columnas_fuente`); `build_flows(files: dict[str, str])` (`sgm.flow.model`); `entradas_y_salidas(modelo, {}).fuentes` con `fuente.tipo == "tabla_base"` y `fuente.ubicacion` (`sgm.proceso.entradas_salidas`); `load_schemas(directory: Path) -> dict[str, list[Column]]` (`sgm.catalog.schemas`).
- Produces:
  ```python
  # src/sgm/migrar/esquemas_programa.py
  def esquemas_desde_programa(
      texto: str,
      nombre: str = "programa",
      fixtures: dict[str, list[Column]] | None = None,
  ) -> tuple[dict[str, list[Column]], list[PendienteMigracion]]:
      """Esquema inferido de cada tabla que el programa lee: nombres de las listas de `SELECT`,
      de `INPUT` y de `PROC IMPORT`; el tipo, solo si el programa lo demuestra (aritmética, SUM,
      MEAN) o si `fixtures` lo declara (entonces `source="fixture"`). Lo demás es `String` con
      `P-TIPO-DESCONOCIDO` y la línea del paso. Las tablas con nombre no literal (macrovariable)
      no se infieren: `P-TABLA-DINAMICA` con el nombre."""

  def tablas_base_del_programa(
      texto: str, nombre: str = "programa", atribuir_copias: bool = True
  ) -> dict[str, list[str]]:
      """`biblioteca.tabla` (minúsculas) -> columnas que el programa usa; las dinámicas se omiten.
      Con `atribuir_copias=False` no se suman las columnas de las copias (conducta anterior)."""

  def a_json(
      esquemas: dict[str, list[Column]], programa: str
  ) -> dict[str, dict]:
      """Un dict por esquema de base (`resultados_vspc_clientes`, `work`, ...): `{"schema": ...,
      "source": "inferido del programa <programa>", "_inferido": True, "tables": {tabla: [{"name": ...,
      "type": <tipo|None>, "source": ...}]}}`. El tipo no demostrado sale `None`, no `String`."""

  # src/sgm/cli_esquemas.py
  def esquemas_command(
      desde_programa: Annotated[Path, typer.Option("--desde-programa", help="Programa SAS.")],
      fixtures: Annotated[Path | None, typer.Option("--fixtures", help="Carpeta con fichas de fixtures.")] = None,
      salida: Annotated[Path, typer.Option("--salida", help="Carpeta de salida.")] = Path("out/esquemas"),
  ) -> None: ...
  ```
  El comando imprime, por tabla, `tabla: N columnas, M sin tipo demostrado` y escribe `<salida>/<esquema>.json`. Sale con 0 aunque haya pendientes; con 2 si el programa no existe.

- [ ] **Step 1: Extraer `env_app` sin cambiar comportamiento.** Mover `env_app` y `env_import_describe` de `cli.py` (líneas 201 a 217) a `cli_env.py` (`env_app = typer.Typer(help="Entorno: esquemas de las bases.", no_args_is_help=True)` y el comando tal cual); en `cli.py` importar `from sgm.cli_env import env_app` junto a las otras importaciones de `sgm.cli_*` y dejar `app.add_typer(env_app, name="env")`. Quitar de `cli.py` el import de `describe_mod` si ya no se usa. Correr `uv run python -m pytest tests/unit -q -k "env or describe or cli" -p no:cacheprovider`; debe seguir igual. Commit propio: `hito N n: sgm env sale de cli.py a cli_env.py`.
- [ ] **Step 2: Write the failing test.** `test_esquemas_programa.py`: (a) con el programa pequeño (`client_poc.sas`), `tablas_base_del_programa(texto)["sashelp.cars"]` es exactamente las 15 columnas que lista el `SELECT` de la primera consulta por marca (`Make, Model, Type, Origin, DriveTrain, MSRP, Invoice, EngineSize, Cylinders, Horsepower, MPG_City, MPG_Highway, Weight, Wheelbase, Length`, línea 45 al redactar este plan). El `SELECT` nombra `WORK.CARS_POC`, no `sashelp.cars`: las columnas se atribuyen a la tabla de origen porque `data WORK.cars_poc; set sashelp.cars; run;` es una copia sin `KEEP`, `DROP`, `RENAME` ni asignaciones, y el `PROC APPEND base=WORK.cars_poc data=WORK.cars_poc` no cambia las columnas; una copia con `KEEP`/`DROP`/`RENAME` o con asignaciones **no** se atribuye y deja `P-COLUMNAS-NO-ATRIBUIDAS` con la tabla de origen; (b) `esquemas_desde_programa(texto)` sin `fixtures`: todas las columnas de `sashelp.cars` salen `String` (o `Double` si la aritmética lo demuestra) y hay un `P-TIPO-DESCONOCIDO` con el nombre de la tabla; **ninguna columna sale con tipo que no esté demostrado**; (c) con `fixtures={"sashelp.cars": [Column("MSRP", "Double", None, "fixture"), ...]}` esas columnas salen `Double` con `source == "fixture"` y no hay `P-TIPO-DESCONOCIDO` para ellas; (d) un programa mínimo `proc import datafile='x.csv' out=WORK.t dbms=dlm replace; getnames=yes; run; data WORK.u; set WORK.t; y = a * 2; run;` da `a` `Double` y `P-TIPO-DESCONOCIDO` para el resto; (e) `select a from &lib..t` da el pendiente `P-TABLA-DINAMICA`; (f) `a_json(...)` escribe `type: None` para lo no demostrado y `"_inferido": True`; (g) con `CliRunner`, `sgm esquemas --desde-programa <programa pequeño> --salida <tmp>` escribe `<tmp>/sashelp.json`; el archivo **no** lo carga `load_schemas` como catálogo con tipos inventados (su `source` es `inferido`); (h) `tools/contenedores/fuentes_sas.tablas_base(Path(client_large.sas))` devuelve las mismas tablas que antes (`tests/unit/test_contenedores.py` sigue en verde).
- [ ] **Step 3: Run test to verify it fails.** `uv run python -m pytest tests/unit/test_esquemas_programa.py -q -p no:cacheprovider`.
- [ ] **Step 4: Implement.** `tablas_base_del_programa` mueve el cuerpo de `tablas_base` (`fuentes_sas.py`) a `src/` devolviendo el mapa; `fuentes_sas.tablas_base` pasa a construir sus `TablaBase`/`Omitida` desde `tablas_base_del_programa(..., atribuir_copias=False)` y de una segunda función `_omitidas` (las dinámicas y las sin columnas), manteniendo la firma y el resultado. Atribución por copia: una pasada previa recorre los `DATA` con un único `SET` y sin sentencias que cambien columnas, y suma las columnas usadas de la tabla copiada a la tabla de origen (con el mismo nombre en mayúsculas o minúsculas); es una regla de lectura del programa, no semántica de SAS, y por eso no cita página. `esquemas_desde_programa` une: columnas de `tablas_base_del_programa`, el plan (`analyze_program` + `compile_file(...).plan`, como `cli_migrar._plan`) y `esquemas_de_entrada(plan, {}, None)` para los `PROC IMPORT` y los `INPUT`; el tipo numérico sale de `esquemas_de_entrada`; lo no demostrado, `String` con `P-TIPO-DESCONOCIDO` por tabla. Registrar en `cli.py`: `from sgm.cli_esquemas import esquemas_command` y `app.command("esquemas")(esquemas_command)`.
- [ ] **Step 5: Run test to verify it passes**, luego `uv run python -m sgm.cli esquemas --desde-programa tests/fixtures/sas/client/client_large.sas --salida out/esquemas` y pegar en `PROGRESS.md` cuántas tablas y cuántas columnas quedan sin tipo (línea base de K-3), y `uv run ruff check src tests tools`.
- [ ] **Step 6: Commit.** `hito N n: sgm esquemas --desde-programa infiere tablas y columnas sin inventar tipos`, con la línea `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.

---

### Task K-9: Tablas de biblioteca local como lectura de archivo (`sashelp.cars` en el Job)

Hoy `data WORK.cars_poc; set sashelp.cars; run;` migra con `P-OPERADOR-SIN-SOPORTE` («el operador 'read' no tiene componente», medido al redactar este plan con un programa de tres líneas): una lectura de tabla de biblioteca no tiene lector. Para las bibliotecas que no son una base (`sashelp`) el fixture es un CSV; este pase convierte el `read` de esa tabla en un `read_file` del CSV, y todo lo de abajo (esquema, contexto `ruta_<tabla>`, `tFileInputDelimited`, intérprete) funciona sin cambios.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\tablas_locales.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\ir\pase_tablas_locales.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\preparar_plan.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\cli_migrar_contexto.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\env\tablas_locales.json`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\cli_migrar.py` (331 líneas: extraer `_SECRETO` y `_contexto_yaml`, líneas 59 y 170 a 192, a `cli_migrar_contexto.py`; después, un solo enganche)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\cli_migrar_comando.py` (opción `--tablas-locales`)
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_tablas_locales.py`

**Interfaces:**
- Consumes: `Operator(id, kind, params, ...)` y `Plan.graph.operators()` (`sgm.ir.models`; `Operator` es mutable); el `read` del plan lleva `params["dataset"]` (`qualify(nombre)`) y el `read_file` los parámetros que arma `_read_file` en `src/sgm/ir/lower_procs.py`: `datafile`, `outputs`, `dbms`, `delimiter`, `getnames`, `sheet`, `guessingrows` (más `input_names` cuando viene de un `INPUT`); `leer_ficha(ruta: Path) -> Ficha` (K-1); `PendienteMigracion(codigo, motivo, linea)` (`sgm.migrar.esquemas`).
- Produces:
  ```python
  # src/sgm/migrar/tablas_locales.py
  @dataclass(frozen=True)
  class TablaLocal:
      nombre: str                    # "sashelp.cars" (minúsculas)
      archivo: str                   # ruta del CSV relativa a la raíz del repositorio
      delimitador: str               # ","
      columnas: tuple[Column, ...]   # de la ficha, con source="fixture"
      origen: str                    # "sintetico" | "real", de la ficha

  def cargar_tablas_locales(ruta: Path, raiz: Path) -> dict[str, TablaLocal]:
      """Lee `env/tablas_locales.json` (`{"sashelp.cars": {"archivo": "...", "delimitador": ","}}`)
      y la ficha `<archivo sin .csv>.ficha.yaml` de cada una. Una tabla sin ficha lanza ValueError."""

  # src/sgm/ir/pase_tablas_locales.py
  def tablas_locales_a_archivos(
      plan: Plan, locales: dict[str, TablaLocal]
  ) -> tuple[Plan, list[PendienteMigracion]]:
      """Cada operador `read` cuyo `dataset` está en `locales` pasa a `read_file` con
      `datafile=<archivo>`, `dbms` el que usa `_read_file` para un CSV, `delimiter`,
      `getnames=True`, `outputs=[dataset]` y `input_names` con las columnas de la ficha.
      Devuelve un pendiente `P-DATOS-SINTETICOS` por tabla cuyo `origen` sea `sintetico`
      (informativo: lista la ruta del archivo) y nunca toca otro operador."""

  # src/sgm/migrar/preparar_plan.py
  def preparar_plan(
      plan: Plan, locales: dict[str, TablaLocal] | None = None
  ) -> tuple[Plan, list[PendienteMigracion]]:
      """Cadena de pases previos a la emisión. Hoy: tablas locales (K-9); K-5 añade las copias remotas."""
  ```
  `env/tablas_locales.json`: `{"_nota": "Bibliotecas locales sin base: el fixture es un CSV con ficha.", "sashelp.cars": {"archivo": "tests/fixtures/datos/sashelp/cars.csv", "delimitador": ","}}`.

- [ ] **Step 1: Extraer sin cambio de comportamiento.** Mover `_SECRETO` y `_contexto_yaml` de `cli_migrar.py` a `cli_migrar_contexto.py` (sin tocar el texto que escriben) e importarlos en `cli_migrar.py`. `uv run python -m pytest tests/unit/test_cli_migrar.py tests/unit/test_talend_contextos.py -q -p no:cacheprovider` debe seguir igual. Commit propio: `hito N n: contexto yaml de migrar sale a cli_migrar_contexto.py`.
- [ ] **Step 2: Write the failing test.** `test_tablas_locales.py`: (a) con el programa `data WORK.c; set sashelp.cars; run; proc sql; create table WORK.a as select Make, MSRP from WORK.c where Make = 'Acura'; quit;`, `migrar(programa, out, ...)` **sin** tablas locales deja `P-OPERADOR-SIN-SOPORTE` en la línea 1 (conducta de hoy, no cambia) y **con** `--tablas-locales env/tablas_locales.json` ese pendiente desaparece, existe `contextos/Default.yaml` con una variable `ruta_cars` cuyo valor es `tests/fixtures/datos/sashelp/cars.csv`, y el Job tiene un `tFileInputDelimited`; (b) `pendientes.md` lista `P-DATOS-SINTETICOS` con la ruta del CSV; (c) `tablas_locales_a_archivos` no toca un `read` de `WORK.otra` ni un `read_file` existente; (d) `cargar_tablas_locales` con una tabla sin `.ficha.yaml` lanza `ValueError` que nombra la tabla; (e) el intérprete: `ejecutar_plan(plan_con_pase, {"sashelp.cars": filas_del_csv})` devuelve `a` con las filas cuya `Make` es `Acura` (4 con la semilla de K-1).
- [ ] **Step 3: Run test to verify it fails.** `uv run python -m pytest tests/unit/test_tablas_locales.py -q -p no:cacheprovider`.
- [ ] **Step 4: Implement** los tres módulos y el enganche: en `migrar()` (`cli_migrar.py`), después de `plan, desplegados = plan_desplegado(plan)` y antes de `contextos_de_plan(plan)`, `plan, previos = preparar_plan(plan, locales)` y sumar `previos` a `resultado.pendientes`; `migrar(..., tablas_locales: Path | None = None)` carga con `cargar_tablas_locales(tablas_locales, raiz=Path.cwd())`. En `cli_migrar_comando.py`, `--tablas-locales` (`Path | None`, valida que exista). `informes.py` ya imprime los pendientes: `P-DATOS-SINTETICOS` aparece en `pendientes.md` con el motivo «tabla local `sashelp.cars` leída del fixture `<ruta>`, datos sintéticos; no son datos reales».
- [ ] **Step 5: Run** `uv run python -m pytest tests/unit/test_tablas_locales.py tests/unit/test_cli_migrar.py tests/unit/test_golden*.py -q -p no:cacheprovider`. Sin `--tablas-locales` los golden no cambian. Luego `uv run ruff check src tests tools`.
- [ ] **Step 6: Commit.** `hito N n: las tablas de biblioteca local se leen como archivo de fixture`, con la línea `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.

---

### Task K-3: Generador de datos por esquema y carga tipada a los contenedores

`tools/contenedores/cargar_tablas.py` ya crea en Impala las tablas que lee un programa, pero todas las columnas son `STRING` con `SIM_<columna>_<n>`. Con tipos demostrados (K-2) o declarados por una ficha, las columnas numéricas deben ser numéricas: una consulta con `SUM` o `WHERE YEAR = 2026` no corre bien sobre `STRING` sin conversión.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\datos_sinteticos\por_esquema.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\contenedores\sql_carga.py` (63 líneas)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\contenedores\cargar_tablas.py` (89 líneas)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\pyproject.toml` (marca `contenedores`)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\contenedores\test_carga_impala.py`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_datos_por_esquema.py`

**Interfaces:**
- Consumes (`tools/corpus_lib/datos_ficticios.py`): `Columna`, `Entrada(filas: int, columnas: tuple[Columna, ...])`, `col(nombre, tipo, *args, vacios=0)` con los tipos `secuencia`, `codigo`, `entero`, `decimal`, `texto_blancos`, `fecha`, `elige`, y `generar_tabla(semilla: str, entrada: Entrada) -> tuple[list[str], list[list[str]]]`; `Column` (`sgm.ir.models`); `tablas_base_del_programa` (K-2); `_literal(valor: str) -> str` e `_identificador(nombre: str) -> str` de `tools/contenedores/sql_carga.py`.
- Produces:
  ```python
  # tools/datos_sinteticos/por_esquema.py
  def entrada_desde_esquema(
      columnas: Sequence[Column], filas: int
  ) -> Entrada:
      """Double -> `decimal` 1 a 1000 (dos decimales); Integer y Long -> `entero` 1 a 1000;
      String y `None` -> `codigo` con prefijo `SIM_<columna>`; cualquier otro tipo -> String
      (el aviso `P-TIPO-GENERADOR` lo recoge `generar_filas`)."""

  def generar_filas(
      tabla: str,
      columnas: Sequence[Column],
      filas: int,
      semilla: int = 20261104,
      exigidos: Mapping[str, Sequence[str]] | None = None,
  ) -> tuple[list[str], list[list[str]], list[str]]:
      """(encabezado, filas, avisos). Misma semilla y tabla, mismos bytes. `exigidos` fija los
      valores de las primeras filas de una columna (`{"Make": ["Acura"]}`): cada valor exigido
      aparece al menos una vez; con menos filas que valores lanza ValueError."""

  # tools/contenedores/sql_carga.py
  def sentencias_tipadas(
      biblioteca: str, tabla: str, columnas: Sequence[Column], filas: Sequence[Sequence[str]]
  ) -> list[str]: ...
  def sql_conteos(tablas: Sequence[tuple[str, str]]) -> str:
      """Un `select '<b>.<t>' as tabla, count(*) as filas from <b>.<t>` por tabla, unidos con
      `union all`."""
  ```
  Tipos de Impala: `Double` -> `DOUBLE`; `Integer` -> `INT`; `Long` -> `BIGINT`; todo lo demás -> `STRING`. Los números salen sin comillas y el texto entre comillas con `''` para el apóstrofo. `cargar_tablas.py` gana `--esquemas CARPETA` (esquemas de `load_schemas`, también los inferidos de K-2), `--semilla N` (por omisión 20261104) y `--verificar` (imprime el SQL de `sql_conteos`; con `--ejecutar` lo corre y compara cada conteo con `--filas`).

- [ ] **Step 1: Write the failing test.** `test_datos_por_esquema.py`: (a) con `[Column("id","Integer"), Column("nombre","String"), Column("saldo","Double"), Column("f","Date")]`, `generar_filas("b.t", cols, 3)` da 3 filas, `id` enteros entre 1 y 1000, `nombre` de `SIM_nombre-001` a `SIM_nombre-003`, `saldo` con dos decimales, y un aviso `P-TIPO-GENERADOR` que nombra `f` (`Date`); (b) dos llamadas iguales dan lo mismo y con otra semilla cambian `id` y `saldo`; (c) `exigidos={"nombre": ["Acura", "BMW"]}` pone esos dos valores en las filas 1 y 2 y con `filas=1` lanza `ValueError`; (d) una columna con `type=None` sale `String` y no lleva aviso de tipo inventado; (e) `sentencias_tipadas("b", "t", cols[:3], [["1","SIM_nombre-001","10.50"]])` da exactamente `["CREATE DATABASE IF NOT EXISTS b;", "DROP TABLE IF EXISTS b.t;", "CREATE TABLE b.t (\n  `id` INT,\n  `nombre` STRING,\n  `saldo` DOUBLE\n);", "INSERT INTO b.t VALUES\n  (1, 'SIM_nombre-001', 10.50);"]`; (f) `sql_conteos([("b","t"),("b","u")])` contiene `union all` una vez y `from b.u`; (g) `construir_sql` de `cargar_tablas.py` con `--sas` el programa pequeño y `--esquemas` apuntando a un esquema con tipos genera `DOUBLE` para las columnas numéricas y sigue generando `STRING` (ruta anterior) para las tablas sin tipos; `tests/unit/test_contenedores.py` sigue en verde sin cambios.
- [ ] **Step 2: Run test to verify it fails.** `uv run python -m pytest tests/unit/test_datos_por_esquema.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement.** `por_esquema.py` construye la `Entrada` y llama a `generar_tabla(f"{semilla}:{tabla}", entrada)`; para `exigidos`, sobrescribe después de generar las primeras filas de esa columna (la generación del resto no cambia). `sql_carga.sentencias_tipadas` reutiliza `_literal` y `_identificador`. En `pyproject.toml`: `addopts = "-n auto -m 'not studio and not contenedores'"` y `markers = ["studio: ...", "contenedores: necesita Docker con los contenedores sgmtest_ arriba; no corre por omisión"]` (dejar el texto de `studio` como está; si el Plan A ya cambió esa línea, sumar la marca sobre su versión).
- [ ] **Step 4: Run test to verify it passes**; `uv run ruff check src tests tools`.
- [ ] **Step 5: Contenedor (si Docker está arriba).** `powershell -File tools\contenedores\impala\arrancar.ps1`; `uv run python -m sgm.cli esquemas --desde-programa tests/fixtures/sas/client/client_large.sas --salida out/esquemas`; `uv run python tools/contenedores/cargar_tablas.py --sas tests/fixtures/sas/client/client_large.sas --esquemas out/esquemas --filas 20 --ejecutar --verificar`. Esperado: cada tabla de `resultados_vspc_clientes`, `proceso_vspc_finanzas` y `s_canales` con 20 filas. `tests/contenedores/test_carga_impala.py` (marca `contenedores`; se salta si `docker ps` no lista `sgmtest_impalad`) crea una tabla tipada de 3 filas y comprueba `select sum(saldo)` contra la suma en Python con tolerancia 0. Si Docker no está arriba: «contenedor pendiente» con el motivo, y se cierra el resto.
- [ ] **Step 6: Commit.** `hito N n: generador de datos por esquema y carga tipada a Impala`, con la línea `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.

---

### Task K-10: Requisitos de datos de cada rebanada y manifiesto

Para cada rebanada hay que saber qué tablas y columnas necesita, cuáles produce ella misma y cuáles entran como dato, y qué valores exigen sus filtros. Lo que el programa no demuestra (el valor de `&ANIO`, que sale de otra tabla) lo declara una persona en el manifiesto, no lo adivina la herramienta.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\datos_sinteticos\requisitos.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\datos_sinteticos\manifiesto.py`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_datos_requisitos.py`

**Interfaces:**
- Consumes: `tablas_base_del_programa(texto: str, nombre: str = "programa", atribuir_copias: bool = True) -> dict[str, list[str]]` (K-2); `generar_filas(...)` (K-3); `escribir_entrada(carpeta, nombre, encabezado, filas)` (`datos_ficticios`); `columnas_usadas(texto: str, dataset: str) -> list[str]` y `columnas_por_importacion(texto: str) -> dict[str, list[str]]` (`sgm.proceso.columnas_fuente`).
- Produces:
  ```python
  # tools/datos_sinteticos/requisitos.py
  @dataclass(frozen=True)
  class Requisitos:
      tablas_locales: dict[str, list[str]]          # sashelp.cars -> columnas
      tablas_base: dict[str, list[str]]             # biblioteca.tabla de Impala -> columnas
      tablas_work_externas: dict[str, list[str]]    # WORK.x leída y no producida en la rebanada
      archivos: list[str]                           # DATAFILE= literales de los PROC IMPORT
      exigidos: dict[str, dict[str, list[str]]]     # tabla -> columna -> literales de WHERE
      dinamicos: list[str]                          # "resultados...master_customer_data.year = &ANIO" (sin valor)

  def requisitos_de_rebanada(texto: str, nombre: str = "rebanada") -> Requisitos: ...
  def valores_exigidos(texto: str) -> tuple[dict[str, dict[str, list[str]]], list[str]]:
      """`col = 'lit'`, `col = 123` y `col in ('a','b')` en `WHERE`/`ON`, con el alias resuelto al
      `FROM`. Una comparación con macrovariable no resuelta no da valor: va a la segunda lista.
      Solo igualdad y `IN` con literal; no interpreta nada más (sin semántica SAS: no cita página)."""

  # tools/datos_sinteticos/manifiesto.py
  @dataclass(frozen=True)
  class TablaDeDatos:
      filas: int
      fijos: dict[str, str] = field(default_factory=dict)   # columna -> valor constante, decidido por una persona
      columnas: tuple[str, ...] = ()   # solo si el programa no las demuestra; las declara una persona
  @dataclass(frozen=True)
  class Manifiesto:
      semilla: int
      tablas: dict[str, TablaDeDatos]
  def leer_manifiesto(ruta: Path) -> Manifiesto: ...
  def generar_entradas(
      req: Requisitos, esquemas: Mapping[str, Sequence[Column]], manifiesto: Manifiesto, destino: Path
  ) -> list[Path]:
      """Escribe en `destino` un CSV por tabla de `tablas_work_externas` y `tablas_base` (nombre
      `<biblioteca>.<tabla>.csv` o `<TABLA>.csv`) y su `.ficha.yaml` con `origen: sintetico`.
      Falta una tabla en el manifiesto -> ValueError con el nombre. Una tabla sin columnas demostradas ni declaradas -> ValueError("<tabla>: el programa no demuestra sus columnas; declararlas en datos.yaml"). Los `exigidos` del programa se
      pasan al generador; los `fijos` del manifiesto mandan sobre ellos."""
  ```
  Formato de `datos.yaml` (uno por caso): `semilla: 20261111` y `tablas: {WORK.VALIDACION_FECHA: {filas: 1, fijos: {AÑO: "2026", MES: "9", DIA: "28"}}}`.

- [ ] **Step 1: Write the failing test.** `test_datos_requisitos.py`: (a) con el texto de la primera consulta por marca de `client_poc.sas` (`CREATE TABLE WORK.ACURA AS SELECT ... FROM WORK.CARS_POC CARS_POC WHERE ( CARS_POC.Make = 'Acura' )`), `valores_exigidos` devuelve `{"work.cars_poc": {"make": ["Acura"]}}` y ninguna dinámica; (b) con `select max(ingestion_day) from resultados_vspc_clientes.master_customer_data as b where b.year=&ANIO. and b.month=&MES.` devuelve `exigidos == {}` y `dinamicos == ["resultados_vspc_clientes.master_customer_data.year = &ANIO", "resultados_vspc_clientes.master_customer_data.month = &MES"]`; (c) `col in ('A','B')` da `["A", "B"]`; (d) `requisitos_de_rebanada` de un programa con `proc import datafile='/x/a.csv' out=WORK.a dbms=dlm replace; run; data WORK.b; set WORK.a; run; proc sql; create table WORK.c as select k from WORK.z; quit;` da `archivos == ["/x/a.csv"]` y `tablas_work_externas == {"work.z": ["k"]}` (`WORK.a` y `WORK.b` las produce la rebanada, `WORK.z` no); (e) `generar_entradas` con manifiesto `{work.z: filas 3, fijos {k: "7"}}` escribe `WORK.z.csv` con tres filas de `7` y `work.z.ficha.yaml` con `origen: sintetico` y la semilla; dos corridas dan los mismos bytes; (f) falta la tabla en el manifiesto: `ValueError` con `work.z`.
- [ ] **Step 2: Run test to verify it fails.** `uv run python -m pytest tests/unit/test_datos_requisitos.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement.** `valores_exigidos` con expresiones regulares sobre cada sentencia SQL (`FROM <tabla> [AS] <alias>` para resolver alias; los nombres se comparan sin distinguir mayúsculas y se devuelven en minúsculas, los literales tal como están). `requisitos_de_rebanada` combina `tablas_base_del_programa`, los `read` del plan (`work.*` leídas y no producidas por ningún `create table`, `data` ni `proc import` de la rebanada) y los `DATAFILE=`. No escribe nada. `generar_entradas` fija la semilla de cada tabla con el nombre de la tabla.
- [ ] **Step 4: Run test to verify it passes**; `uv run ruff check src tests tools`.
- [ ] **Step 5: Commit.** `hito N n: requisitos de datos por rebanada y manifiesto de datos sinteticos`, con la línea `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.

---

## Parte II. Bases simuladas y ejecución

### Task K-4: Contexto `DEV` apuntando a los contenedores (`tImpalaRow` ejecutable sin credenciales reales)

Hoy el emisor escribe `tImpalaRow` con `HOST`, `PORT` y `DBNAME` vacíos y deja `P-CONEXION-BASE` (hitos 162m a 164m en `PROGRESS.md`). El Job debe leer esos tres valores del contexto, y el grupo `DEV` debe traer los del Impala del contenedor (`localhost`, `21050`, `default`, más `;auth=noSasl`, que `tools/contenedores/impala/README.md` exige para JDBC). `Default`, `QA` y `PROD` quedan vacíos: el valor de producción no está en el SAS y no se inventa.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\talend_item\desde_plan_conexion.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\env\contexto_dev.json`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\contenedores\consultar.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\talend_item\desde_plan.py` (859 líneas; solo tres cambios mínimos: el indicador en `plan_a_jobs`/`_Job` y la llamada en `_sql_impala`; **zona del emisor del carril de Andres**: avisar antes y, si tiene cambios sin commitear en ese archivo, aplicar el cambio sobre su versión)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\talend_item\desde_plan_contextos.py` (108 líneas)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\cli_migrar.py` y `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\cli_migrar_comando.py` (`--contexto-dev`)
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_contexto_dev.py`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_contenedores_consultar.py`

**Interfaces:**
- Consumes: `nodo_desde_plantilla(componente, unico, x, y, valores, tablas, columnas, ruta_java)` (`sgm.talend_item.plantillas`); `java(valor: str) -> str` (`sgm.talend_item.jobs_diseno`; el literal Java que ya usa `_sql_impala`); `ParametroContexto(nombre, tipo="id_String", valor="", comentario="", pedir=False)` y `GRUPOS = ("Default", "DEV", "QA", "PROD")` (`sgm.talend_item.modelo`, `desde_plan_contextos`); `contextos_de_plan(plan: Plan) -> dict[str, list[ParametroContexto]]`; `plan_a_jobs(plan: Plan, esquemas: dict[str, list[Column]], ruta_java: str | None = None) -> ResultadoMigracion`; `ejecutar_sql(sql: str) -> subprocess.CompletedProcess[str]` de `tools/contenedores/cargar_tablas.py`. Parámetros de la plantilla `tImpalaRow` (verificados en `src/sgm/talend_item/plantillas/tImpalaRow.json`): `HOST`, `PORT`, `DBNAME`, `IMPALA_ADDITIONAL_JDBC`, `USER`, `PASS`, `QUERY`.
- Produces:
  ```python
  # src/sgm/talend_item/desde_plan_conexion.py
  VARIABLES_BASE: tuple[str, ...] = ("impala_host", "impala_puerto", "impala_base", "impala_jdbc_extra")

  def parametros_conexion(en_contexto: bool) -> dict[str, str]:
      """Con `en_contexto=False` (conducta de hoy): `HOST`, `PORT`, `DBNAME` -> `java("")`.
      Con True: `HOST` -> `context.impala_host`, `PORT` -> `context.impala_puerto` (entero con
      `Integer.parseInt`), `DBNAME` -> `context.impala_base`, `IMPALA_ADDITIONAL_JDBC` ->
      `context.impala_jdbc_extra`. `PASS` y `USER` no se tocan (siguen `((String)null)` y vacío)."""

  def cargar_contexto_dev(ruta: Path) -> dict[str, str]:
      """Lee `env/contexto_dev.json` y valida que las claves sean `VARIABLES_BASE` y que ninguna
      cuyo nombre case con `pass|pwd|secret|token|clave` esté presente (ValueError)."""

  # src/sgm/talend_item/desde_plan_contextos.py
  def contextos_de_plan(plan: Plan, dev: dict[str, str] | None = None) -> dict[str, list[ParametroContexto]]:
      """Igual que hoy; si `dev` no es None y el plan tiene un `exec_sql`, suma las cuatro
      variables de `VARIABLES_BASE` a los cuatro grupos, con el valor de `dev` solo en `DEV`."""

  # tools/contenedores/consultar.py
  def filas_de_salida(texto: str) -> list[list[str]]:
      """Filas de la salida de `impala-shell -B --output_delimiter=,` (sin cabecera ni filas vacías)."""
  def consultar(sql: str) -> list[list[str]]:
      """Ejecuta `sql` en el Impala del contenedor y devuelve sus filas; RuntimeError con el stderr si falla."""
  ```
  `env/contexto_dev.json`: `{"_nota": "Contenedor sgmtest_ desechable; sin credenciales.", "impala_host": "localhost", "impala_puerto": "21050", "impala_base": "default", "impala_jdbc_extra": ";auth=noSasl"}`. Sin `--contexto-dev` el Job y el contexto quedan como en el hito 162m (los golden y `tests/unit/test_push_db.py` no cambian). Con `--contexto-dev`, `P-CONEXION-BASE` se mantiene con el motivo «el Job lee host, puerto y base de `context.impala_*`; `DEV` apunta al contenedor, `QA` y `PROD` están vacíos hasta que los configure quien los conozca».

- [ ] **Step 1: Write the failing test.** `test_contexto_dev.py` con el programa de `tests/unit/test_push_db.py` (el de `l2_16_sql_en_misma_base`): (a) `plan_a_jobs(plan, {}, conexion_en_contexto=True)` deja en `tImpalaRow` `HOST == "context.impala_host"`, `DBNAME == "context.impala_base"`, `PASS == "((String)null)"` y ninguna cadena `sgmtest_pw_local` ni `localhost` en el `.item`; con `False` sigue `HOST == PORT == DBNAME == '""'` (aserción actual de `test_push_db.py`, línea 137); (b) `contextos_de_plan(plan, dev={...})` da cuatro grupos con las mismas claves en el mismo orden, `DEV["impala_host"] == "localhost"` y `Default`, `QA`, `PROD` vacíos; (c) `cargar_contexto_dev` rechaza un JSON con `impala_clave` o con una clave desconocida; (d) con `migrar(programa, out, contexto_dev=Path("env/contexto_dev.json"))` existe `contextos/DEV.yaml` con `localhost` y `contextos/PROD.yaml` con `valor: ""`, y `sgm secretos` sobre el paquete no da hallazgos; (e) `test_contenedores_consultar.py`: `filas_de_salida("a,1\nb,2\n\n") == [["a", "1"], ["b", "2"]]`.
- [ ] **Step 2: Run test to verify it fails.** `uv run python -m pytest tests/unit/test_contexto_dev.py tests/unit/test_contenedores_consultar.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement.** `parametros_conexion` devuelve el diccionario que hoy escribe `_sql_impala` y lo reemplaza en una línea (`**parametros_conexion(self._conexion_en_contexto)`); `plan_a_jobs(..., conexion_en_contexto: bool = False)` lo pasa a `_Job`. `contextos_de_plan` recibe `dev` sin cambiar su comportamiento cuando es `None` (el nombre de la variable `impala_*` no casa con `_SECRETO`). `consultar` usa `impala-shell -B --output_delimiter=,` por el mismo contenedor efímero que `ejecutar_sql`. En `cli_migrar.py`, `migrar(..., contexto_dev: Path | None = None)` carga el JSON, pasa `dev` a `contextos_de_plan` y `conexion_en_contexto=dev is not None` a `plan_a_jobs`.
- [ ] **Step 4: Run test to verify it passes**; luego `uv run python -m pytest tests/unit/test_push_db.py tests/unit/test_desde_plan_contextos.py tests/unit/test_talend_contextos.py tests/unit/test_golden*.py -q -p no:cacheprovider` (sin cambios) y `uv run ruff check src tests tools`.
- [ ] **Step 5: Un Job de base contra el contenedor (Docker y Studio).** Programa mínimo `tests/corpus_reales/L8/k4_impala_row/programa.sas`: `proc sql; connect to impala (DSN=IMPALAP); execute by impala (drop table if exists sgmtest_k.k4_destino); execute by impala (create table sgmtest_k.k4_destino stored as parquet as select make, count(*) as n from sgmtest_k.k4_origen group by make); disconnect from impala; quit;`. Con el contenedor arriba: `uv run python tools/contenedores/cargar_tablas.py --csv tests/fixtures/datos/sashelp/cars.csv --tabla sgmtest_k.k4_origen --ejecutar` (carga las 40 filas; todo `STRING`, por eso el conteo no depende de tipos), `uv run python -m sgm.cli migrar tests/corpus_reales/L8/k4_impala_row/programa.sas --out out/k4 --contexto-dev env/contexto_dev.json`, y ejecutar el Job en Studio con `--grupo-contexto DEV` (`uv run python tools/corpus_studio.py validar k4_impala_row --corpus tests/corpus_reales --jobs out/k4/programa/process --padre job_programa --proyecto <proyecto> --grupo-contexto DEV`; el caso declara `salidas: []`, así que el código de salida solo dice que el Job corrió). Comprobar con `consultar("select make, n from sgmtest_k.k4_destino order by make")`: debe dar `Acura,4`, `Audi,3`, `BMW,6`, `Chevrolet,8`, `Ford,5`, `Honda,4`, `Jaguar,3`, `Toyota,7`. **Esperado independiente:** el intérprete no ejecuta SQL de motor remoto (`exec_sql` no está en `SOPORTADOS`), así que el esperado sale de SQLite (`sqlite3`, la misma técnica del oráculo `tools/corpus_lib/oraculo_sql.py`) con `select make, count(*) as n from cars group by make` sobre `cars.csv`; el test `tests/contenedores/test_k4_impala_row.py` (marca `contenedores`) compara ambos. Sin Docker o sin Studio queda «contenedor pendiente» o «lote C pendiente» con el motivo.
- [ ] **Step 6: Commit.** `hito N n: contexto DEV de los contenedores para tImpalaRow`, con la línea `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.

---

### Task K-5: `RSUBMIT`, `PROC UPLOAD` y `PROC DOWNLOAD` como copias locales

Los 26 usos de `PROC UPLOAD`/`PROC DOWNLOAD` del programa grande (22 y 4) llevan rutas literales (ninguno usa macrovariables en `INFILE=`/`OUTFILE=`, medido al redactar este plan) y van entre `signon`/`RSUBMIT`/`endrsubmit`/`signoff`. `rules/sas/plumbing.yaml` ya clasifica esas cuatro sentencias como infraestructura («el Job se ejecuta en Talend»). Lo que falta es el efecto de la copia: un `PROC DOWNLOAD` deja el archivo remoto en una ruta local que un `PROC IMPORT` lee después, y un `PROC EXPORT` escribe un archivo local que un `PROC UPLOAD` envía a su destino. Este pase lo resuelve como **alias de ruta**: el `read_file` de la ruta local lee la ruta de origen, y el `write_file` a la ruta local escribe en la ruta de destino. La copia intermedia no se materializa (decisión documentada; no es SAS).

**Fuente SAS:** `connref.pdf`: `DOWNLOAD Procedure` (p. 285, sintaxis p. 286): trae un archivo del host remoto al local; `UPLOAD Procedure` (p. 245, sintaxis p. 246): lo envía del local al remoto; `RSUBMIT Statement` (p. 185), `SIGNON Statement` (p. 151). Leer solo la sección de sintaxis de cada una y confirmar que `INFILE=` es el origen y `OUTFILE=` el destino en ambas antes de implementar; si la guía dice otra cosa, el sentido de la regla se corrige en este plan.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\ir\pase_copias_remotas.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\migrar\preparar_plan.py` (creado en K-9: se añade el parámetro `texto` y la llamada)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\cli_migrar.py` (una línea: pasar `texto` a `preparar_plan`)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\rules\sas\catalogo\procs-usados.yaml` (`upload` y `download`: `estado: reconocida` con nota; la `fuente` no cambia)
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_copias_remotas.py`

**Interfaces:**
- Consumes: `Plan.graph.operators()` y `Operator.params` con `read_file` (`datafile`) y `write_file` (`outfile`) (`src/sgm/talend_item/desde_plan_contextos.py::rutas_de_plan` los lee igual); `ruta(literal: str) -> str` de `sgm.talend_item.desde_plan_nodos` (quita comillas y normaliza); `PendienteMigracion`.
- Produces:
  ```python
  @dataclass(frozen=True)
  class CopiaRemota:
      sentido: str      # "download" | "upload"
      infile: str       # origen, sin comillas
      outfile: str      # destino, sin comillas
      linea: int        # línea del `PROC` en el programa

  def copias_remotas(texto: str) -> tuple[list[CopiaRemota], list[PendienteMigracion]]:
      """Cada `PROC UPLOAD|DOWNLOAD` con `INFILE=` y `OUTFILE=` literales. Con `&` en una ruta:
      `P-COPIA-REMOTA-DINAMICA`; con `DATA=`/`OUT=` (copia de dataset): `P-COPIA-REMOTA-DATASET`.
      Nunca copia `USER=`/`PASS=` de un `SIGNON`: la función ni los lee."""

  def aplicar_copias(
      plan: Plan, copias: Sequence[CopiaRemota]
  ) -> tuple[Plan, list[PendienteMigracion]]:
      """download: todo `read_file` cuyo `datafile` es `outfile` pasa a leer `infile`.
      upload: todo `write_file` cuyo `outfile` es `infile` pasa a escribir en `outfile`.
      Una copia que no cambia ningún paso deja `P-COPIA-REMOTA-SIN-EFECTO` con su línea."""
  ```
  `preparar_plan(plan, locales=None, texto: str = "")` encadena: tablas locales (K-9), `copias_remotas(texto)` y `aplicar_copias`.

- [ ] **Step 1: Write the failing test.** `test_copias_remotas.py`: (a) con el trozo real de las líneas 146 a 164 de `client_large.sas` (`signon`, `RSUBMIT server;`, `PROC DOWNLOAD INFILE='\\sbcldwpsgf01\FILE_VSPC_FINANZAS\Base_datos_Nequi.csv' OUTFILE='/work_sasstudio/pcfiles/Base_datos_Nequi.csv';`, `endrsubmit;`, `signoff;`, y el `proc import datafile='/work_sasstudio/pcfiles/Base_datos_Nequi.csv' out=WORK.BASE_CLIENTES_NEQUI dbms=dlm replace; delimiter=';'; getnames=NO; run;`; con la contraseña ya como `'***'`), `copias_remotas` devuelve una `CopiaRemota("download", "\\\\sbcldwpsgf01\\FILE_VSPC_FINANZAS\\Base_datos_Nequi.csv", "/work_sasstudio/pcfiles/Base_datos_Nequi.csv", <línea>)` y `aplicar_copias` deja el `read_file` leyendo la ruta `\\sbcldwpsgf01\...`; (b) con las líneas 24263 a 24278 (`proc export data=WORK.FA_NO_VIGENTES_AHO outfile="/work_sasstudio/pcfiles/FA_NO_VIGENTES_AHO.csv" dbms=dlm replace; delimiter=';'; run;` y el `PROC UPLOAD` siguiente) el `write_file` escribe en `\\sbcldwpsgf01\FILE_VSPC_FINANZAS\GST_Informacion_Exogena\RESULTADOS\FA_NO_VIGENTES_AHO.csv`; (c) `PROC UPLOAD INFILE="&dir./a.csv" OUTFILE="/x/a.csv";` da `P-COPIA-REMOTA-DINAMICA`; `PROC DOWNLOAD DATA=a OUT=b;` da `P-COPIA-REMOTA-DATASET`; una copia sin `read_file`/`write_file` que coincida da `P-COPIA-REMOTA-SIN-EFECTO`; (d) un `signon user=u pass='***'` no aparece en ningún pendiente ni en la salida; (e) el contexto: tras el pase, `rutas_de_plan(plan)` da la ruta final como valor de `ruta_<tabla>`, y `sgm migrar` de (a) con `--tablas-locales` omitido produce un `contextos/Default.yaml` cuya variable `ruta_base_clientes_nequi` vale la ruta `\\sbcldwpsgf01\...`; (f) los casos de L0 a L6 no cambian: `uv run python -m pytest tests/unit/test_golden*.py -q`.
- [ ] **Step 2: Run test to verify it fails.** `uv run python -m pytest tests/unit/test_copias_remotas.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement.** Expresión regular sobre cada sentencia `proc (upload|download) ... ;` (las opciones `clave = "valor"|'valor'|valor`, sin distinguir mayúsculas); número de línea contando saltos hasta el inicio del `PROC`. `aplicar_copias` compara rutas con `ruta()` y sin distinguir mayúsculas ni barras. Es un pase de plan puro: no cambia el número de operadores.
- [ ] **Step 4: Catálogo.** En `procs-usados.yaml`, `upload` y `download` pasan a `reconocida` con la nota «se resuelve como alias de ruta (`ir/pase_copias_remotas.py`); la copia intermedia no se materializa; copia de datasets queda pendiente». `uv run python -m pytest tests/unit/test_catalogo_sas.py -q -p no:cacheprovider`.
- [ ] **Step 5: Run test to verify it passes**; `uv run python -m sgm.cli secretos tests/fixtures/sas/client` (los fixtures ya redactados: 0 hallazgos) y `uv run ruff check src tests tools`.
- [ ] **Step 6: Commit.** `hito N n: copias remotas de SAS/CONNECT como alias de ruta`, con la línea `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.

---

### Task K-6: Programa pequeño de punta a punta (anillos A, B y C)

La rebanada es el tramo del programa pequeño que lee `sashelp.cars`, lo copia a `WORK`, lo duplica con un bucle de 15 `PROC APPEND` sobre la misma tabla, consulta cuatro marcas y cuenta: las líneas 12 a 120 de `client_poc.sas`. Lo que sigue (líneas 121 en adelante: escritura a la zona de aterrizaje, S3, temporizador) no es de datos y queda fuera, con su motivo.

**El corpus de datos reales va fuera de `tests/corpus/`:** `tests/unit/test_tablero.py` fija 16 casos en L8 y otras pruebas recorren todo L8; agregar casos ahí las rompe. Los casos de este plan viven en `tests/corpus_reales/L8/<caso>/` (el cargador `corpus_lib.caso` exige una carpeta de nivel, y esta lo es) y se pasan con `--corpus tests/corpus_reales` a `tools/corpus_studio.py` y a `tools/corpus.py`.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus_reales\L8\k6_cars_ciclo_append\programa.sas` (salida de `armar`, no se escribe a mano)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus_reales\L8\k6_cars_ciclo_append\rebanada.yaml`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus_reales\L8\k6_cars_ciclo_append\caso.yaml`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus_reales\L8\k6_cars_ciclo_append\entradas\cars.csv` (copia byte a byte de `tests/fixtures/datos/sashelp/cars.csv`)
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus_reales\L8\k6_cars_ciclo_append\esperado\` (`ACURA.csv`, `JAGUAR.csv`, `BMW.csv`, `CHEVROLET.csv`, con `repeticiones = 3`)
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\validar_caso_studio.py` (111 líneas; `_caso` busca también en `tests/corpus_reales` y pasa `--corpus`; **archivo del Plan A**: si hay cambios sin commitear de Plan A, hacerlo después de su commit)
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_k6_programa_pequeno.py`

**Interfaces:**
- Consumes: `Rebanada`, `rebanar`, `armar`, `verificar` (K-8); `calcular(caso, repeticiones)` y `escribir(caso, tablas)` (K-8); `tablas_locales_a_archivos` (K-9); `migrar(source, out, esquemas=None, muestra=None, backend="archivos", tablas_locales=None, contexto_dev=None)` (`sgm.cli_migrar`, K-9 y K-4); `cargar_caso(directorio)`; `Tabla`, `leer_csv`.
- Produces: el caso `k6_cars_ciclo_append` con `rebanada.yaml` = `fuente: tests/fixtures/sas/client/client_poc.sas`, `rangos: [[12, 120]]`, `sha256: <huella>`, `prologo: "%let repeticiones = 15;"` y `sustituciones: [["%do i=1 %to 15;", "%do i=1 %to &repeticiones.;"]]` (única edición del programa real: parametrizar el límite del bucle; con 15 el programa es el original), y `caso.yaml` con `nivel: L8`, `estado: parcial`, `salidas: [ACURA, JAGUAR, BMW, CHEVROLET]`, `capa: C`, `tolerancia: 0`, `orden_relevante: false`, `supuestos` que incluyen: «datos sinteticos: entradas/cars.csv sustituye a sashelp.cars (tests/fixtures/datos/sashelp/cars.ficha.yaml, semilla 20261111)», «Pendiente: P-APPEND-MISMA-TABLA: la guia (proc.pdf, p. 161 y 162) no dice que BASE= y DATA= puedan ser la misma tabla; el doble por vuelta sale del comentario del programa (14.024.704 filas = 428 x 2^15) y no esta demostrado con SAS real», «%web_drop_table y %web_open_table son macros de SAS Studio sin definicion en el programa; no se asume que hacen mas que borrar y mostrar la tabla (sin pagina de la guia)». `motivo`: «esperado calculado por el intérprete sin SAS real, con repeticiones = 3». Esperado con `repeticiones = 3`: `cars` 40 x 2^3 = 320 filas; `ACURA` 32, `BMW` 48, `CHEVROLET` 64, `JAGUAR` 24. Con 15 (supuesto, solo aritmética): 131.072, 196.608, 262.144 y 98.304.

**Dependencias de otros planes (no se implementan aquí):** el `PROC APPEND` como operador (Plan B, B-8, `lower_procs.py`; `proc.pdf`, p. 161 y 162), la expansión estática del `%DO` (Plan E, MG-P7-01) y el `%let repeticiones` como variable de contexto del Job (Plan E, MG-P7-04). Hasta que existan, el anillo B y el anillo C de este caso quedan con el motivo en `migrar_pendientes`-estilo de `caso.yaml` (`motivo`) y no se cuentan como pasados; lo que sí se cierra aquí es lo que no depende de ellos.

- [ ] **Step 1: Medir hoy.** Generar la rebanada con `armar` y migrarla: `uv run python -m sgm.cli migrar tests/corpus_reales/L8/k6_cars_ciclo_append/programa.sas --out out/k6 --tablas-locales env/tablas_locales.json`. Pegar en `PROGRESS.md` los pendientes por código (esperado hoy: `P-OPERADOR-SIN-SOPORTE` para `PROC APPEND`, y los de `%web_*`) y cuántos `PROC APPEND` salen del bucle (15 si el expansor del frontend desenrolla el `%DO`; si salen menos, anotar el número y la causa).
- [ ] **Step 2: Write the failing test.** `test_k6_programa_pequeno.py`: (a) `verificar(rebanada_de_rebanada_yaml, REPO) == []` y `armar(...)` es byte a byte `programa.sas`; (b) `entradas/cars.csv` es byte a byte `tests/fixtures/datos/sashelp/cars.csv`; (c) anillo A: `migrar(..., tablas_locales=...)` no deja `P-OPERADOR-SIN-SOPORTE` para la lectura de `sashelp.cars` ni para las cuatro consultas `CREATE TABLE ... AS SELECT ... WHERE ( CARS_POC.Make = '...' )`; (d) anillo B, **marcado `xfail(strict=True)` con el motivo «PROC APPEND sin operador (Plan B, B-8)» mientras B-8 no exista** (al llegar B-8 la prueba falla y obliga a quitar la marca): `calcular(caso, {"repeticiones": 3})` da `len(ACURA) == 32`, `len(BMW) == 48`, `len(CHEVROLET) == 64`, `len(JAGUAR) == 24` y las filas de `ACURA` tienen todas `Make == "Acura"`; con `{"repeticiones": 0}` dan 4, 6, 8 y 3 (sin vueltas, la tabla no crece); (e) los conteos por marca de la entrada salen de `MARCAS` de K-1, no de números escritos a mano; (f) `sgm secretos tests/corpus_reales` limpio.
- [ ] **Step 3: Run test to verify it fails.** `uv run python -m pytest tests/unit/test_k6_programa_pequeno.py -q -p no:cacheprovider`.
- [ ] **Step 4: Implement el caso.** Generar `programa.sas` y `rebanada.yaml` con `escribir_rebanada(destino, rebanada, texto_fuente)` de `tools/rebanar_programa.py` (K-8), copiar `cars.csv`, escribir `caso.yaml` y, cuando el anillo B funcione, `esperado/*.csv` con `esperado_interprete.escribir`. Mientras B-8 no exista, `esperado/` se escribe con el cálculo directo (`Counter` de `Make` por 2^3, **sin pasar por el intérprete**) y el caso lo dice en `motivo`; al llegar B-8 se regenera con el intérprete y debe coincidir.
- [ ] **Step 5: Run test to verify it passes** y `uv run ruff check src tests tools`.
- [ ] **Step 6: Anillo C (Studio), solo si las dependencias existen.** `uv run python tools/validar_caso_studio.py k6_cars_ciclo_append` (con el cambio de `_caso`); esperado `1 casos, 1 coinciden`. Si el Job desenrolla 15 vueltas fijas (el límite no llega al contexto), correr la variante con `repeticiones = 3` generada con `armar` y declarar `Pendiente: P-REPETICIONES-ESTATICAS` (el Job no lee `repeticiones` del contexto). Si no hay Studio: «lote C pendiente».
- [ ] **Step 7: Commit.** `hito N n: programa pequeno de punta a punta, ciclo de APPEND parametrizado`, con la línea `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.

---

### Task K-13: Preparar los datos de una rebanada (manifiesto a `entradas/` y a contenedor)

Une K-10 y K-3: dado un caso con `programa.sas` y `datos.yaml`, escribe `entradas/` y, si se pide, crea en Impala las tablas de base con sus tipos y verifica los conteos. Es el comando que usan K-7a a K-7e.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\contenedores\preparar_rebanada.py`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_preparar_rebanada.py`

**Interfaces:**
- Consumes: `esquemas_desde_programa(texto: str, nombre: str = "programa", fixtures: dict[str, list[Column]] | None = None)` (K-2); `requisitos_de_rebanada(texto: str, nombre: str = "rebanada") -> Requisitos`, `leer_manifiesto(ruta: Path) -> Manifiesto`, `generar_entradas(req, esquemas, manifiesto, destino) -> list[Path]` (K-10); `generar_filas` y `sentencias_tipadas`, `sql_conteos` (K-3); `ejecutar_sql(sql)` y `sql_completo(bloques)` de `tools/contenedores/cargar_tablas.py` y `sql_carga.py`.
- Produces:
  ```python
  def preparar(caso: Path, cargar: bool = False) -> list[Path]:
      """Lee `<caso>/programa.sas` y `<caso>/datos.yaml`; escribe `<caso>/entradas/` con
      `generar_entradas`; devuelve los CSV escritos. Con `cargar=True` crea en Impala cada tabla
      de `Requisitos.tablas_base` (SQL tipado con los tipos del esquema inferido) y verifica con
      `sql_conteos` que cada conteo es el `filas` del manifiesto; RuntimeError si no coincide.
      Sin Docker, `cargar=True` lanza RuntimeError con el motivo (no se salta en silencio)."""
  def main(argv: list[str] | None = None) -> int:
      """`uv run python tools/contenedores/preparar_rebanada.py <caso> [--cargar]`."""
  ```

- [ ] **Step 1: Write the failing test.** `test_preparar_rebanada.py` con un caso en `tmp_path` (`programa.sas`: `proc sql; create table WORK.t as select k, sum(v) as s from WORK.z group by k; quit;`; `datos.yaml`: `semilla: 7`, `tablas: {work.z: {filas: 4, columnas: [k, v], fijos: {k: "a"}}}`): (a) `preparar(caso)` escribe `entradas/work.z.csv` con cabecera `k,v` y cuatro filas con `k == "a"`, y `work.z.ficha.yaml` con `origen: sintetico` y `semilla: 7`; (b) dos corridas dan los mismos bytes; (c) `v` sale `Double` porque `SUM` lo demuestra (valores con dos decimales), `k` queda `String`; (d) con una tabla de base (`proceso.t` leída con `connect to impala`) y `cargar=False`, el SQL de carga se puede obtener con `sql_de_carga(caso)` (función pública) y contiene `CREATE TABLE proceso.t (` con `DOUBLE` solo para columnas demostradas numéricas; (e) `cargar=True` sin contenedor arriba lanza `RuntimeError` que menciona `sgmtest_impalad`.
- [ ] **Step 2: Run test to verify it fails.** `uv run python -m pytest tests/unit/test_preparar_rebanada.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement** `preparar`, `sql_de_carga(caso: Path) -> str` y `main`, sobre `TablaDeDatos.columnas` de K-10 (si el programa no demuestra las columnas de una tabla y el manifiesto tampoco las declara, `generar_entradas` ya lanza `ValueError`).
- [ ] **Step 4: Run test to verify it passes**; `uv run ruff check src tests tools`.
- [ ] **Step 5: Commit.** `hito N n: preparar los datos de una rebanada desde su manifiesto`, con la línea `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.

---

## Parte III. El programa grande por rebanadas

### Task K-7: Mapa de rebanadas del programa grande y compuerta de secretos

El programa grande tiene unas 24.800 líneas, 521 `PROC SQL`, 216 `PROC DELETE`, 31 `PROC SORT`, 30 `PROC CONTENTS`, 22 `PROC UPLOAD`, 22 `PROC EXPORT`, 9 `PROC IMPORT`, 4 `PROC DOWNLOAD` y unos 125 `CONNECT TO impala`. **30 de los 31 `PROC SORT` y los 30 `PROC CONTENTS` son una introspección de `WORK`** (`proc contents data=work._all_ noprint out=contents; proc sort data=contents out=members nodupkey; by memname;`, dentro de macros de partición): dependen de la sesión de SAS, no de datos, y no entran en ninguna rebanada; quedan `Pendiente: P-WORK-INTROSPECCION` (motivo: el contenido de `WORK` es estado de la sesión, no un dato que un fixture pueda aportar). Esta tarea fija las cinco rebanadas con líneas verificadas contra la copia redactada del repositorio y la compuerta de secretos.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\decisiones\client_large.rebanadas.yaml`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_k7_rebanadas.py`

**Interfaces:**
- Consumes: `Rebanada`, `rebanar`, `huella`, `verificar` (K-8); `escanear_ruta(ruta: Path) -> Escaneo` con `Escaneo.hallazgos` (`sgm.seguridad.escaner_secretos`); `region_de_linea(regiones, linea)` y `dividir_regiones(texto, marcador)` (`sgm.flow.regiones`); `cargar_declaracion(ruta).marcador` (`sgm.agrupacion`).
- Produces: `decisiones/client_large.rebanadas.yaml` con cinco entradas (`id`, `tipo`, `fuente: tests/fixtures/sas/client/client_large.sas`, `rangos`, `sha256`, `depende_de`), con estos rangos (líneas de la copia redactada, verificadas al redactar este plan):

  | id | tipo | rangos | qué contiene |
  |---|---|---|---|
  | `k7a_import_export` | IMPORT/EXPORT | `[5, 13]`, `[160, 164]`, `[24263, 24267]` | `PROC IMPORT ... DBMS=EXCELCS` de la homologación, `proc import ... dbms=dlm` con `delimiter=';'` y `getnames=NO`, `proc export ... dbms=dlm` de `WORK.FA_NO_VIGENTES_AHO` |
  | `k7b_sql_impala` | SQL a Impala | `[166, 181]`, `[183, 212]` | `SELECT ... INTO :ANIO/:MES/:DIA FROM WORK.VALIDACION_FECHA`, `connect to IMPALA ... select * from connection to IMPALA (select MAX(ingestion_day) ... where B.YEAR=&ANIO. AND B.MONTH=&MES.)` y el `EXECUTE BY IMPALA (create table proceso_vspc_finanzas.mcdq stored as parquet as select ...)` |
  | `k7c_sort_delete` | SORT/DELETE | `[45, 57]`, `[15816, 15819]` | el `DATA` con `RENAME=`, `COMPRESS(input(left(...), 10.))` y `proc delete data=work.temporal;`, y el `proc sort ... nodupkey equals; by NRO_DOC NRO_CTA;` |
  | `k7d_upload_download` | UPLOAD/DOWNLOAD | `[146, 164]`, `[24263, 24278]` | `signon`/`RSUBMIT`/`PROC DOWNLOAD`/`endrsubmit`/`signoff` y el `proc import` que lee la copia; `proc export` y `PROC UPLOAD` que la envía |
  | `k7e_totales` | totales | `[24615, 24653]` | los dos `CREATE TABLE ... AS SELECT SUM(...) FORMAT=BEST20. AS ...` (12 sumas cada uno) sobre `WORK.RESULTADO_AHO_EXT` y `WORK.RESULTADO_AHO_NAL` |

- [ ] **Step 1: Verificar las líneas hoy.** Con `Grep`/`sed -n` sobre `tests/fixtures/sas/client/client_large.sas` confirmar cada rango de la tabla (primera y última línea de cada uno); si el archivo cambió, corregir la tabla y este plan. Medir la región de cada rango: `uv run python tools/medir_regiones.py --sas tests/fixtures/sas/client/client_large.sas --agrupacion decisiones/client_large.agrupacion.yaml` y anotar en `PROGRESS.md` en qué región del linaje cae cada rebanada (las cinco están fuera de `%macro ambiente`, en el cuerpo principal).
- [ ] **Step 2: Write the failing test.** `test_k7_rebanadas.py`: (a) `decisiones/client_large.rebanadas.yaml` tiene exactamente cinco entradas con los `id` de la tabla; (b) para cada una `verificar(rebanada, REPO) == []`; (c) el texto de cada rebanada no contiene `pass='` seguido de algo distinto de `***'`, ni `pwencode in='` con algo distinto de `'***'`; (d) `escanear_ruta(tests/fixtures/sas/client).hallazgos == []`; (e) ninguna rebanada incluye una línea con `proc contents data=work._all_` (la introspección queda fuera); (f) el texto de `k7d_upload_download` contiene `RSUBMIT server;` y `PROC UPLOAD INFILE="/work_sasstudio/pcfiles/FA_NO_VIGENTES_AHO.csv"`.
- [ ] **Step 3: Run test to verify it fails.** `uv run python -m pytest tests/unit/test_k7_rebanadas.py -q -p no:cacheprovider`.
- [ ] **Step 4: Implement.** Escribir el YAML con las huellas que calcula `huella(rebanar(texto, rangos))` (no copiarlas a mano) y `depende_de` por rebanada: a: K-1/K-8/K-10; b: K-3/K-4/K-13 y Plan D (MG-P2-05); c: Plan B (B-3, B-8); d: K-5; e: K-10.
- [ ] **Step 5: Run test to verify it passes**; `uv run ruff check src tests tools`.
- [ ] **Step 6: Commit.** `hito N n: mapa de cinco rebanadas verticales del programa grande`, con la línea `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.

---

### Task K-7a: Rebanada IMPORT/EXPORT

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus_reales\L8\k7a_import_export\` con `programa.sas`, `rebanada.yaml`, `caso.yaml`, `datos.yaml`, `entradas\`, `esperado\`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_k7a_import_export.py`

**Interfaces:**
- Consumes: `escribir_rebanada`, `calcular`, `escribir` (K-8); `preparar(caso: Path, cargar: bool = False)` (K-13); `migrar(...)` (K-9); `cargar_caso`.
- Produces: el caso con `salidas: [BASE_CLIENTES_NEQUI, FA_NO_VIGENTES_AHO]`, `estado: parcial`, `capa: C`, `tolerancia: 0`, `orden_relevante: true`. `datos.yaml`: `Base_datos_Nequi.csv` (archivo sin cabecera, `;`, 3 columnas `VAR1`, `VAR2`, `VAR3`, 6 filas) y `WORK.FA_NO_VIGENTES_AHO` (columnas declaradas `NRO_DOC, NRO_CTA`, 6 filas). **Pendiente:** el programa no demuestra cuántas columnas tiene el archivo de Nequi ni las de `FA_NO_VIGENTES_AHO`; las declara el manifiesto y el `caso.yaml` lo dice en `supuestos` («columnas decididas por el fixture, no demostradas por el SAS»). Los nombres `VAR1` a `VAR3` son los que SAS da con `GETNAMES=NO` (`proc.pdf`, p. 1387, la misma página que cita `lower_procs.py`).

- [ ] **Step 1: Write the failing test.** (a) la rebanada verifica (`verificar == []`) y `programa.sas` es `armar`; (b) `preparar(caso)` es determinista y `entradas/Base_datos_Nequi.csv` no tiene cabecera ni comas, solo `;`; (c) anillo A: `migrar(programa, out, muestra=caso/"entradas")` produce `ruta_base_clientes_nequi` y `ruta_fa_no_vigentes_aho` en el contexto; el `DBMS=EXCELCS` queda como pendiente con su código (no se inventa una lectura de Excel: registrar el código que salga y el motivo en `caso.yaml`); (d) anillo B: el intérprete da `BASE_CLIENTES_NEQUI` con `VAR1..VAR3` y las 6 filas, y `FA_NO_VIGENTES_AHO` es la tabla de entrada sin cambios (`PROC EXPORT` escribe lo que lee); (e) `sgm secretos` sobre `out/k7a` y sobre el caso: limpio.
- [ ] **Step 2: Run test to verify it fails.** `uv run python -m pytest tests/unit/test_k7a_import_export.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement el caso** con `escribir_rebanada`, `preparar` y `esperado_interprete.escribir`; el `PROC EXPORT` con `PUTNAMES` por omisión (cabecera) se confirma en `proc.INDEX.md` («EXPORT Procedure», p. 901 según el catálogo) antes de escribir `esperado/FA_NO_VIGENTES_AHO.csv`; si la página no lo demuestra, `Pendiente: P-EXPORT-CABECERA` y el esperado no incluye la cabecera como hecho.
- [ ] **Step 4: Run test to verify it passes**; anillo C: `uv run python tools/validar_caso_studio.py k7a_import_export` (con el `--corpus` de K-6). Sin Studio: «lote C pendiente».
- [ ] **Step 5: Commit.** `hito N n: rebanada de IMPORT y EXPORT del programa grande`, con la línea `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.

---

### Task K-7b: Rebanada SQL a Impala (con el contenedor)

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus_reales\L8\k7b_sql_impala\` con `programa.sas`, `rebanada.yaml`, `caso.yaml`, `datos.yaml`, `entradas\`, `esperado\`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_k7b_sql_impala.py`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\contenedores\test_k7b_sql_impala.py`

**Interfaces:**
- Consumes: `preparar(caso, cargar=True)` (K-13); `consultar(sql: str) -> list[list[str]]` (K-4); `migrar(..., contexto_dev=Path("env/contexto_dev.json"))` (K-4); `calcular`; el cálculo de referencia de `tests/corpus/L8/totales/07_impala_lectura` (mismo patrón: `MAX(ingestion_day)` con `YEAR` y `MONTH`).
- Produces: el caso con `salidas: [MAXDIA]` (la tabla de `WORK`) y la tabla `proceso_vspc_finanzas.mcdq` en el contenedor, `estado: parcial`. `datos.yaml`: `WORK.VALIDACION_FECHA` con 1 fila (`fijos: {AÑO: "2026", MES: "9", DIA: "28"}`), y `resultados_vspc_clientes.master_customer_data` con 12 filas (`fijos` de `YEAR: "2026"` y `MONTH: "9"` en 9 de ellas, y `YEAR: "2026"`, `MONTH: "8"` en 3; `ingestion_day` con tres días distintos de septiembre, el mayor `2026-09-28` en 4 filas). **Las ligas entre tablas las decide el manifiesto:** el programa no demuestra que `&ANIO.` valga lo de `VALIDACION_FECHA.AÑO` por más que lo parezca; `requisitos` lo lista en `dinamicos` y el `caso.yaml` lo declara en `supuestos`. Esperado: `MAXDIA` tiene una fila con `Mday = 2026-09-28` y `mcdq` en el contenedor tiene 4 filas (las del último día de septiembre).
- **Dependencias:** el lector `select * from connection to IMPALA (...)` a `tImpalaInput` es Plan D (MG-P2-05); `&MDAY.` dentro del `EXECUTE BY IMPALA` viene de `SELECT MDAY INTO :MDAY FROM WORK.MAXDIA` (SQL dinámico con un valor de datos): hasta que Plan D/E lo resuelvan, el anillo C de esta rebanada se limita a la parte que no lo necesita y el resto queda `Pendiente: P-SQL-DINAMICO` con la línea (el programa sí demuestra la dependencia: `&MDAY.` aparece en el `WHERE` de la línea 209).

- [ ] **Step 1: Write the failing test.** `tests/unit/test_k7b_sql_impala.py` (sin Docker): (a) la rebanada verifica; (b) `requisitos_de_rebanada(programa)` da `tablas_work_externas == {"work.validacion_fecha": [...]}` con `año`, `mes` y `dia`, `tablas_base` con `resultados_vspc_clientes.master_customer_data` y sus columnas (`cod_tipo_doc`, `num_doc`, `nombre_cli`, `long_nombre1`, `long_nombre2`, `long_apellido1`, `long_apellido2`, `dir_p`, `cod_ciudad_dirp`, `cod_pais_dirp`, `year`, `month`, `ingestion_day`, `llave_sistema`, `cod_tipo_dirp`), y `dinamicos` con los tres (`year = &ANIO`, `month = &MES`, `ingestion_day = &MDAY`); (c) `sql_de_carga(caso)` crea `resultados_vspc_clientes.master_customer_data` con `year` y `month` numéricos solo si algún filtro o aritmética lo demuestra (`B.YEAR=&ANIO.` compara con un número, pero el programa no dice que sea numérico: **queda `STRING` y el caso lo anota**; el SQL de Impala compara `STRING` con número con conversión implícita: si Impala la rechaza, el caso se reduce y se anota); (d) anillo A: `migrar(..., contexto_dev=...)` deja `tImpalaRow` con `context.impala_host` y `DEV.yaml` con `localhost`; (e) esperado de `MAXDIA` por SQLite sobre las 12 filas: `2026-09-28`.
- [ ] **Step 2: Run test to verify it fails.** `uv run python -m pytest tests/unit/test_k7b_sql_impala.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement el caso**; `preparar(caso, cargar=True)` con el contenedor arriba crea `resultados_vspc_clientes.master_customer_data` (12 filas) y `consultar("select max(ingestion_day) from resultados_vspc_clientes.master_customer_data where year = 2026 and month = 9")` debe dar `2026-09-28`.
- [ ] **Step 4: Contenedor y Studio.** `tests/contenedores/test_k7b_sql_impala.py` (marca `contenedores`) migra con `--contexto-dev`, ejecuta el Job en Studio con `--grupo-contexto DEV` y compara `consultar("select count(*) from proceso_vspc_finanzas.mcdq")` con 4. «contenedor pendiente» o «lote C pendiente» si falta Docker, Studio o el lector de Plan D.
- [ ] **Step 5: Run test to verify it passes**, `sgm secretos` sobre el caso y sobre `out/k7b`; `uv run ruff check src tests tools`.
- [ ] **Step 6: Commit.** `hito N n: rebanada de SQL a Impala del programa grande con contenedor`, con la línea `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.

---

### Task K-7c: Rebanada SORT/DELETE

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus_reales\L8\k7c_sort_delete\` con `programa.sas`, `rebanada.yaml`, `caso.yaml`, `datos.yaml`, `entradas\`, `esperado\`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_k7c_sort_delete.py`

**Interfaces:**
- Consumes: igual que K-7a. Páginas: `SORT Procedure` (`proc.pdf`, p. 2449; localizar `NODUPKEY` y `EQUALS` en `proc.INDEX.md` y citar la página de cada opción en `caso.yaml`); `DELETE Procedure` (`proc.INDEX.md`, resumen p. 23 y el capítulo de la guía); conversión de tipo (`lrcon.pdf`, p. 75).
- Produces: `salidas: [IMPORT_CODIGOS_PAIS, SABANA_DIR_UNICA_NEQUI]`, `estado: parcial`. `WORK.IMPORT_CODIGOS_PAIS` es a la vez entrada (`entradas/IMPORT_CODIGOS_PAIS.csv`) y salida (el `DATA` la reescribe): `esperado/IMPORT_CODIGOS_PAIS.csv` es la salida final, y la prueba comprueba que el intérprete no confunde las dos. `datos.yaml`: `WORK.IMPORT_CODIGOS_PAIS` con la columna `Codigo_Pais` (texto con blancos a la izquierda: `"  57"`, `" 169"`, `"  57"`, 5 filas) y `WORK.SABANA_COMPLETA_INFO_CLI_NEQUI` con las columnas `NRO_DOC`, `NRO_CTA` y `ORDEN_FILA` (esta última **la agrega el fixture** para distinguir qué fila sobrevive a `NODUPKEY EQUALS`; el SAS no la demuestra y el caso lo declara), 8 filas con 3 pares `(NRO_DOC, NRO_CTA)` repetidos. Esperado de `SABANA_DIR_UNICA_NEQUI`: un registro por par, el de menor `ORDEN_FILA` (el primero en el orden de entrada, que es lo que dice `EQUALS`: confirmar con la página), ordenados por `NRO_DOC`, `NRO_CTA`. `WORK.temporal` no existe al final (`proc delete`): el intérprete devuelve las tablas de `WORK` que produce y `temporal` no debe estar entre ellas.
- **Riesgo declarado:** `Codigo_Pais=COMPRESS(input(left(Codigo_Pais_old), 10.))` asigna un número a una variable de texto (`format Codigo_Pais $10.`): SAS convierte número a texto con aviso (`lrcon.pdf`, p. 75). Si el intérprete no ejecuta esa conversión, esa parte queda `Pendiente: P-CONVERSION-NUM-TEXTO` en `caso.yaml` y la prueba la marca `xfail(strict=True)` con ese motivo; **no se escribe un esperado supuesto**.

- [ ] **Step 1: Write the failing test.** (a) la rebanada verifica; (b) `preparar(caso)` escribe las dos tablas con las columnas declaradas; (c) anillo B de `SABANA_DIR_UNICA_NEQUI`: 5 filas únicas (8 menos 3 repetidas), en orden de llave, con el `ORDEN_FILA` mínimo por par; (d) `proc delete data=work.temporal;` no deja la tabla en la salida; (e) la conversión número a texto: `xfail(strict=True)` o prueba normal según lo que haga el intérprete al medir (Step 3); (f) anillo A: el `NODUPKEY` sale como `tSortRow` con `P-NODUPKEY-ESTABILIDAD` si el catálogo sigue diciendo «parcial hasta validar la estabilidad de `tSortRow`» (`rules/sas/catalogo/procs-usados.yaml`, `sort`).
- [ ] **Step 2: Run test to verify it fails.** `uv run python -m pytest tests/unit/test_k7c_sort_delete.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement el caso** y medir qué hace hoy el intérprete con el `DATA` de `COMPRESS(input(...))`; pegar el resultado en `PROGRESS.md`.
- [ ] **Step 4: Run test to verify it passes**; anillo C: `uv run python tools/validar_caso_studio.py k7c_sort_delete` (compara `SABANA_DIR_UNICA_NEQUI`, y es el caso que decide si `tSortRow` con `NODUPKEY` conserva la primera fila). Sin Studio: «lote C pendiente».
- [ ] **Step 5: Commit.** `hito N n: rebanada de SORT y DELETE del programa grande`, con la línea `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.

---

### Task K-7d: Rebanada UPLOAD/DOWNLOAD

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus_reales\L8\k7d_upload_download\` con `programa.sas`, `rebanada.yaml`, `caso.yaml`, `datos.yaml`, `entradas\`, `esperado\`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_k7d_upload_download.py`

**Interfaces:**
- Consumes: `copias_remotas`, `aplicar_copias` (K-5); `mapa_de_contexto(variables, entradas, salidas)` de `tools/validar_caso_studio.py`; K-8 y K-13.
- Produces: `salidas: [BASE_CLIENTES_NEQUI, FA_NO_VIGENTES_AHO]`; `datos.yaml` como K-7a. La diferencia con K-7a es la cadena de copias: el `PROC IMPORT` lee la ruta local que dejó el `PROC DOWNLOAD`, y el `PROC EXPORT` escribe la ruta local que envía el `PROC UPLOAD`. Tras el pase de K-5, el Job lee la ruta `\\sbcldwpsgf01\FILE_VSPC_FINANZAS\Base_datos_Nequi.csv` y escribe `\\sbcldwpsgf01\FILE_VSPC_FINANZAS\GST_Informacion_Exogena\RESULTADOS\FA_NO_VIGENTES_AHO.csv`; el contexto `DEV` las lleva a carpetas locales (`entradas/` y `salida/`) con `mapa_de_contexto`.

- [ ] **Step 1: Write the failing test.** (a) la rebanada verifica y contiene `RSUBMIT server;` y `PROC UPLOAD`; (b) anillo A: `migrar` con la rebanada da `contextos/Default.yaml` con las dos rutas de red y **ninguna** ruta `/work_sasstudio/pcfiles/`; `pendientes.md` no menciona `signon`, `pass`, ni `'***'`; (c) `copias_remotas` da dos copias (una `download` y una `upload`) sin pendientes; (d) anillo B: igual que K-7a (las copias no cambian los datos); (e) `mapa_de_contexto(["ruta_base_clientes_nequi", "ruta_fa_no_vigentes_aho"], ["Base_datos_Nequi.csv"], ["FA_NO_VIGENTES_AHO"])` falla (la variable lleva el nombre de la tabla, no del archivo): **el caso trae su propio `mapa.yaml`** en su carpeta y la prueba comprueba que cada variable del contexto está en él; (f) `sgm secretos` sobre `out/k7d` y el caso: limpio (la contraseña ya está como `'***'` en el fixture).
- [ ] **Step 2: Run test to verify it fails.** `uv run python -m pytest tests/unit/test_k7d_upload_download.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement el caso** con `caso/mapa.yaml` y la corrida de Studio (`corpus_studio.py validar ... --mapa caso/mapa.yaml --grupo-contexto DEV`).
- [ ] **Step 4: Run test to verify it passes**; anillo C: el Job escribe la «ruta de red» de `DEV` en `salida/` y el resultado coincide con `esperado/`; sin Studio: «lote C pendiente».
- [ ] **Step 5: Commit.** `hito N n: rebanada de UPLOAD y DOWNLOAD del programa grande`, con la línea `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.

---

### Task K-7e: Rebanada de totales

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\corpus_reales\L8\k7e_totales\` con `programa.sas`, `rebanada.yaml`, `caso.yaml`, `datos.yaml`, `entradas\`, `esperado\`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_k7e_totales.py`

**Interfaces:**
- Consumes: K-8, K-10, K-13; `ejecutar_proc_sql(sentencias, entradas, salidas)` de `tools/corpus_lib/oraculo_sql.py` y `calcular(caso)` de `tools/corpus_lib/oraculo.py` (el oráculo SQLite).
- Produces: `salidas: [TOTAL_EXTERIOR, TOTAL_NACIONAL]`, `tolerancia: 0.01`, `orden_relevante: false`. `datos.yaml`: `WORK.RESULTADO_AHO_EXT` y `WORK.RESULTADO_AHO_NAL` con 25 y 30 filas y las 12 columnas que suma el programa (`FIN_SALDO_CTA`, `PROM_SALDO_CTA`, `MED_SALDO_CTA`, `MAX_SALDO_CTA`, `MIN_SALDO_CTA`, `VAL_CRED_MES`, `NRO_CRED_MES`, `PROM_CRED_MES`, `MED_CRED_MES`, `VAL_DEB_MES`, `NRO_DEB_MES`, `PROM_DEB_MES`), todas `Double` **demostradas por `SUM`** (la regla de `esquemas_tipos.py`: una columna pasada a `SUM` es numérica). Un fixture con valores de dos decimales. Esperado doble: el intérprete y el oráculo SQLite deben dar la misma fila de 12 sumas por tabla, dentro de la tolerancia (las sumas de reales no son exactas; la tolerancia está declarada, no escondida). **Pendiente:** `FORMAT=BEST20.` dentro del `SELECT` es presentación (`lestmtsref`/`leforinforref`: localizar `BEST` en `leforinforref.INDEX.md` y citar la página); el esperado compara el número, no su texto formateado, y el caso lo declara.

- [ ] **Step 1: Write the failing test.** (a) la rebanada verifica; (b) `requisitos_de_rebanada` da las dos tablas externas con exactamente las 12 columnas y ninguna dinámica; (c) `sql_de_carga`-equivalente: las 12 columnas salen `Double`; (d) el intérprete y el oráculo SQLite dan el mismo resultado para `TOTAL_EXTERIOR` y `TOTAL_NACIONAL` (`abs(a - b) <= 0.01` en las 24 sumas) y ese resultado es lo que hay en `esperado/`; (e) la suma de `FIN_SALDO_CTA` de `WORK.RESULTADO_AHO_EXT` se verifica también con `sum(float(x))` de Python sobre `entradas/` (tercera cuenta, independiente); (f) anillo A: `migrar` da dos Jobs con `tAggregateRow` y los pendientes que sean (anotarlos); (g) `sgm secretos` limpio.
- [ ] **Step 2: Run test to verify it fails.** `uv run python -m pytest tests/unit/test_k7e_totales.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement el caso.**
- [ ] **Step 4: Run test to verify it passes**; anillo C: `uv run python tools/validar_caso_studio.py k7e_totales` con la tolerancia del caso. Sin Studio: «lote C pendiente».
- [ ] **Step 5: Commit.** `hito N n: rebanada de totales del programa grande`, con la línea `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.

---

## Parte IV. Control de calidad de los datos

### Task K-11: Catálogo de fixtures y auditoría «sintético nunca real»

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\fixtures\datos\catalogo.yaml`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\datos_sinteticos\auditar.py`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_datos_auditoria.py`

**Interfaces:**
- Consumes: `leer_ficha(ruta: Path) -> Ficha` y `validar_ficha(ficha, csv) -> list[str]` (K-1); `cargar_caso(directorio) -> Caso` con `Caso.extra["supuestos"]` (`corpus_lib.caso`); `migrar(...)` (K-9).
- Produces:
  ```python
  def auditar(raiz: Path) -> list[str]:
      """Errores (vacía si todo está bien). Revisa `raiz/tests/fixtures/datos/**` y
      `raiz/tests/corpus_reales/**/entradas/*.csv`:
      1. cada CSV tiene su `.ficha.yaml` y `validar_ficha` no da errores;
      2. `origen` es `sintetico` o `real`; `sintetico` exige `semilla` y `generador`; `real` exige `procedencia`
         y no puede estar bajo `entradas/` de `tests/corpus_reales` sin una nota de autorización;
      3. cada caso de `tests/corpus_reales` con un CSV en `entradas/` tiene en `supuestos` un texto que empieza
         por `datos sinteticos:` si alguna de sus fichas es `sintetico`;
      4. ningún CSV contiene un correo (`\S+@\S+\.\S+`), una racha de 7 o más dígitos seguidos o un
         teléfono (`\+?\d[\d\s-]{8,}`);
      5. `catalogo.yaml` lista cada ficha del repositorio y no lista ninguna que no exista."""
  ```
  `catalogo.yaml`: lista de `{tabla, ficha, csv, origen, generador}`; una entrada por cada ficha.

- [ ] **Step 1: Write the failing test.** `test_datos_auditoria.py`: (a) `auditar(REPO) == []` (el repositorio real); (b) un árbol en `tmp_path` con un CSV sin ficha da un error que nombra el archivo; (c) una ficha `sintetico` sin `semilla` da `"origen sintetico sin semilla"`; (d) una ficha `real` sin `procedencia` da error; (e) un caso con ficha `sintetico` y `supuestos` sin «datos sinteticos:» da error que nombra el caso; (f) un CSV con `ana@example.com` o con `1234567` da error; (g) una ficha que no está en `catalogo.yaml` da error; (h) **el informe de migración no lo oculta:** `migrar` de K-6 con `--tablas-locales` deja `P-DATOS-SINTETICOS` en `pendientes.md` y la palabra «sintéticos» en el motivo.
- [ ] **Step 2: Run test to verify it fails.** `uv run python -m pytest tests/unit/test_datos_auditoria.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement** `auditar` (una función por regla, para que un error diga cuál) y escribir `catalogo.yaml` con lo que haya hasta este punto (K-1 y los casos que ya existan); se actualiza cada vez que una tarea agrega una ficha.
- [ ] **Step 4: Run test to verify it passes**; `uv run ruff check src tests tools`. Si se agrega al CI del Plan A, hacerlo en una tarea suya, no aquí (`tools/ci.py` no se toca).
- [ ] **Step 5: Commit.** `hito N n: catalogo de fixtures y auditoria de que lo sintetico no se presenta como real`, con la línea `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.

---

### Task K-12: Regeneración y deriva de los fixtures

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\datos_sinteticos\regenerar.py`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_datos_regenerar.py`

**Interfaces:**
- Consumes: `escribir_cars(destino: Path, semilla: int = 20261111) -> Path` (K-1); `preparar(caso: Path, cargar: bool = False)` (K-13); `catalogo.yaml` (K-11).
- Produces:
  ```python
  def regenerar(raiz: Path, verificar: bool = True) -> list[str]:
      """Regenera cada fixture del catálogo en una carpeta temporal y lo compara byte a byte con el
      versionado. Con `verificar=True` solo informa las diferencias (lista de archivos); con False
      reescribe los que difieren. `cars` usa `escribir_cars`; una entrada `manifiesto:<caso>` usa
      `preparar`. Un `generador` desconocido es un error, no se salta."""
  def main(argv: list[str] | None = None) -> int:
      """`uv run python tools/datos_sinteticos/regenerar.py [--verificar|--escribir]`; sale con 1 si hay deriva."""
  ```

- [ ] **Step 1: Write the failing test.** (a) `regenerar(REPO, verificar=True) == []`; (b) con una copia del árbol en `tmp_path` y un byte cambiado en `cars.csv`, devuelve una lista con esa ruta y `main(["--verificar"])` sale con 1; con `--escribir` lo deja igual al original y una segunda corrida da lista vacía; (c) un `generador` inventado en `catalogo.yaml` da error que lo nombra.
- [ ] **Step 2: Run test to verify it fails.** `uv run python -m pytest tests/unit/test_datos_regenerar.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run test to verify it passes**; `uv run ruff check src tests tools`.
- [ ] **Step 5: Commit.** `hito N n: regeneracion y deteccion de deriva de los fixtures`, con la línea `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.

---

### Task K-Gate: Los dos programas reales tienen esperado reproducible

**Criterio de salida (Plan K de `ruta-al-100.md`, más lo pedido en la ampliación):**
1. **K-1 a K-6 y K-13:** cada tarea cerrada con sus pruebas; `sgm esquemas --desde-programa` corre sobre los dos programas reales y no inventa tipos; el programa pequeño migra con `--tablas-locales` sin el pendiente de `read`.
2. **Programa pequeño:** `k6_cars_ciclo_append` con rebanada verificada, anillo A migrado, anillo B (cuando exista B-8) con los conteos `32`, `48`, `64` y `24` con `repeticiones = 3`, y anillo C `1 casos, 1 coinciden` o «lote C pendiente» con su motivo.
3. **Programa grande:** las cinco rebanadas `k7a` a `k7e` con anillo A migrado y sin secretos, anillo B con `esperado/` calculado por el intérprete (y por el oráculo SQLite donde es SQL puro) y anillo C ejecutado o «lote C pendiente» con su motivo.
4. **Contenedores:** `cargar_tablas.py --sas client_large.sas --esquemas out/esquemas --filas 20 --ejecutar --verificar` con 20 filas por tabla; `k4` y `k7b` ejecutados contra el Impala del contenedor o «contenedor pendiente».
5. **Calidad:** `uv run python tools/datos_sinteticos/regenerar.py --verificar` sin deriva; `auditar(REPO) == []`; `uv run python -m sgm.cli secretos tests/corpus_reales tests/fixtures out` sin hallazgos.

- [ ] **Step 1: Run** `uv run python -m pytest -q` y `uv run ruff check .`.
- [ ] **Step 2: Run** `uv run python tools/datos_sinteticos/regenerar.py --verificar` y `uv run python -c "import sys; sys.path.insert(0,'tools'); from datos_sinteticos.auditar import auditar; from pathlib import Path; print(auditar(Path('.')))"`; esperado `[]`.
- [ ] **Step 3: Run** el lote C con los seis casos (`k6_cars_ciclo_append`, `k7a_import_export`, `k7b_sql_impala`, `k7c_sort_delete`, `k7d_upload_download`, `k7e_totales`): `uv run python tools/validar_caso_studio.py k6_cars_ciclo_append k7a_import_export k7b_sql_impala k7c_sort_delete k7d_upload_download k7e_totales`. Si Studio no conecta, `sgm studio salud` y `docs/guia-validacion-studio.md`, sección 7; no se reinstala nada. La compuerta **no** se declara cerrada con «lote C pendiente».
- [ ] **Step 4: Registrar** en `PROGRESS.md` el hito de cierre: casos por anillo (A, B, C) de los seis, pendientes por código (`P-TIPO-DESCONOCIDO`, `P-APPEND-MISMA-TABLA`, `P-SQL-DINAMICO`, `P-REPETICIONES-ESTATICAS`, `P-WORK-INTROSPECCION`, `P-CONVERSION-NUM-TEXTO`, `P-DATOS-SINTETICOS` informativo), horas reales frente a las 30 estimadas y qué quedó fuera con su motivo. En `ruta-al-100.md`, la tabla del Plan K pasa a «hecho» solo para las tareas cuyos tres anillos pasaron.
- [ ] **Step 5: Commit.** `hito N n: compuerta del plan K, dos programas reales con esperado reproducible`, con la línea `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.

---

## Resumen de horas

| Tareas | Qué | Horas |
|---|---|---|
| K-1 | fixture `sashelp.cars` con ficha y semilla | 2,0 |
| K-8 | rebanador y esperado del intérprete | 1,5 |
| K-2 | `sgm esquemas --desde-programa` | 3,0 |
| K-9 | tablas locales como lectura de archivo | 1,5 |
| K-3 | generador por esquema y carga tipada | 2,5 |
| K-10 | requisitos de datos y manifiesto | 1,2 |
| K-4 | contexto `DEV` y `tImpalaRow` contra el contenedor | 2,3 |
| K-5 | `RSUBMIT`/`UPLOAD`/`DOWNLOAD` como alias de ruta | 2,0 |
| K-6 | programa pequeño de punta a punta | 2,8 |
| K-13 | preparar los datos de una rebanada | 1,0 |
| K-7 | mapa de rebanadas y secretos | 1,0 |
| K-7a, K-7b, K-7c, K-7d, K-7e | las cinco rebanadas | 1,2 + 1,8 + 1,2 + 1,2 + 1,2 = 6,6 |
| K-11 | catálogo y auditoría | 1,2 |
| K-12 | regeneración y deriva | 0,7 |
| K-Gate | cierre | 0,7 |
| **Total** | | **30,0** |

Las horas por tarea son estimaciones del plan; el crédito real se mide con el método de la sección 11b del plan maestro. Las partes que necesitan Studio o Docker cuentan solo cuando se ejecutan: «lote C pendiente» y «contenedor pendiente» no suman.

## Dependencias

**Necesita de otros planes**

| De | Tarea | Para qué |
|---|---|---|
| Plan A | `tools/validar_caso_studio.py`, cola de validaciones, `sgm studio salud` con estados | K-4 (paso 5), K-6, K-7a a K-7e y K-Gate (lote C); sin Studio quedan «lote C pendiente», no se cuentan |
| Plan B | B-8 (`PROC APPEND` como operador), B-2 a B-4 (tipos de `PROC IMPORT` y propagación) | K-6 anillos B y C (el `xfail(strict=True)` de K-6 obliga a quitarlo al llegar B-8); K-2 convive con `esquemas.py` y `esquemas_tipos.py` sin editarlos |
| Plan C | MG-P6-04 y MG-P6-05 (`APPEND`, `DELETE`, política de `PRINT`/`REPORT`) | K-6 (los `select count(*)` sin `INTO` son impresión) y K-7c (`PROC DELETE`) |
| Plan D | MG-P2-04, MG-P2-05, MG-P2-06 (`LIBNAME` a rutas y bases, paso directo `CONNECT TO ... FROM CONNECTION TO` a lector); MG-P3 (informats y funciones) | K-4 y K-7b (lector `tImpalaInput` y SQL con macrovariables de datos); K-7c (`COMPRESS`, `INPUT`) |
| Plan E | MG-P7-01 (expansor `%DO`), MG-P7-04 (variables de macro de ejecución a contexto) | K-6 (`repeticiones` llega al contexto del Job) |
| Plan H | MG-P13-01 (compuerta de secretos) | K-7 y K-Gate usan `sgm secretos`; el plan H lo extiende a `out/` |

**Entrega a otros planes**

| A | Qué |
|---|---|
| Plan B | K-2 y K-3: esquemas inferidos y datos sintéticos con varias filas por grupo para los casos nuevos de `L6` (B-11, B-13) |
| Plan D | K-3, K-4 y K-13: tablas tipadas en el Impala del contenedor y el contexto `DEV` para ejecutar `L8/totales/07_impala_lectura` y el lector de MG-P2-05 |
| Plan G (verificación) | K-11 y K-12: catálogo y auditoría de fixtures sintéticos, como modelo de los demás generadores de casos |
| Plan H | K-7: los cinco casos reales como entradas de la prueba de secretos y del rendimiento |

## Self-review

- **Cobertura de la spec (`ruta-al-100.md`, Plan K):** K-1 en K-1 (más la ficha y la auditoría en K-11 y K-12); K-2 en K-2 (con K-9 para que el Job lea el fixture); K-3 en K-3, K-10 y K-13; K-4 en K-4; K-5 en K-5; K-6 en K-6; K-7 en K-7 y K-7a a K-7e. Las tareas K-8 a K-13 son las que pide la ampliación: rebanador y esperado del intérprete, tablas locales, requisitos por rebanada, preparación de datos, catálogo y auditoría, regeneración.
- **Hallazgos que cambian el plan maestro de planes:** (1) el programa pequeño consulta `WORK.CARS_POC`, no `sashelp.cars`: las columnas de `sashelp.cars` solo se infieren atribuyendo las de la copia (K-2); (2) un `read` de tabla de biblioteca no tiene componente hoy (`P-OPERADOR-SIN-SOPORTE`): K-9 lo resuelve con un pase y no con una regla nueva en el emisor; (3) `ruta-al-100.md` dice «de 478 filas a 14 M», pero 14.024.704 es 428 x 2^15: el `sashelp.cars` real tiene 428 filas y el bucle duplica la tabla 15 veces; (4) la guía (`proc.pdf`, p. 161 y 162) no demuestra el `PROC APPEND` de una tabla sobre sí misma: queda `P-APPEND-MISMA-TABLA`; (5) 30 de los 31 `PROC SORT` y los 30 `PROC CONTENTS` del programa grande son introspección de `WORK`, no datos: fuera de las rebanadas; (6) `tests/unit/test_tablero.py` fija 16 casos en L8, así que los casos de este plan viven en `tests/corpus_reales/`; (7) `src/sgm/cli.py` tiene 299 líneas: K-2 extrae `env_app` antes de registrar `esquemas`.
- **Archivos por encima de 300 líneas:** `src/sgm/cli_migrar.py` (331; K-9 extrae `_contexto_yaml` primero) y `src/sgm/talend_item/desde_plan.py` (859; K-4 hace tres cambios mínimos y pone la lógica en `desde_plan_conexion.py`). Todos los archivos nuevos de este plan están por debajo de 300 líneas.
- **Archivos de otros planes que se tocan con cuidado:** `tools/validar_caso_studio.py` (Plan A, K-6), `desde_plan.py` (emisor, carril de Andres, K-4), `pyproject.toml` (marca `contenedores`, K-3). Ninguno de `lower_procs.py`, `lower_data*.py`, `operadores.py`, `interprete.py`, `esquemas.py` ni `esquemas_tipos.py`.
- **Proporción:** 19 tareas (K-1 a K-13, K-7a a K-7e y la compuerta) para 30 h; los cuerpos de funciones los decide quien implementa, las firmas y los valores esperados están fijados.
- **Pendiente de verificar al ejecutar:** las páginas de `NODUPKEY`/`EQUALS` (`proc.pdf`), `PUTNAMES` de `PROC EXPORT`, `BEST` (`leforinforref`) y la conversión de tipo (`lrcon`, p. 75) se localizan en la primera tarea que las usa; sin página, queda `Pendiente:`. Que `INFILE=` sea el origen y `OUTFILE=` el destino en `PROC UPLOAD` y `PROC DOWNLOAD` se confirma en `connref` antes de implementar K-5.
