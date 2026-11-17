# Cola de trabajo de Byron, sin Studio Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans. Este documento **no repite los pasos**: cada tarea ya está escrita, con su prueba, su comando y su resultado esperado, en el plan de su carril. Aquí solo se ordena la cola, se marca lo que ya hicieron los hitos y lo que pide Studio o Docker.

**Goal:** Que Byron (serie `n`) tome una tarea de unos 5 pasos, la termine en una sesión y siga con la siguiente, sin Studio mientras se pueda.

**Architecture:** Una cola por plan, dividida en pendientes sin Studio, pendientes con Studio y tareas ya citadas en `PROGRESS.md`. «Citada» sale de buscar el id de la tarea (`D1-7`, `B-13`…) en las entradas de hito de las series `m` y `n` desde el hito 190: es una pista, no una prueba de que esté terminada.

**Tech Stack:** Python 3.12 (`uv`, pytest, ruff); reglas YAML; OpenSpec 2.1.0.

**Spec:** `docs/plan-reescritura/plan-migrador-general.md` y `docs/superpowers/plans/2026-11-11-ruta-al-100.md` (§8).

## Global Constraints

- Serie `n` en `PROGRESS.md` y en el commit: `hito Nn: <resumen>`. El número es **único en todo el repositorio**: último `## Hito` de `PROGRESS.md` más uno, sea de la serie que sea (hoy el 270n es el más alto, así que el siguiente libre es el 271).
- Cada tarea nace de un change de OpenSpec, con la tarea del plan como cuerpo de `tasks.md`.
- **Pocos componentes** y **sin Studio mientras se itera** (`AGENTS.md`, 17 de noviembre de 2026): lo que no cabe queda `Pendiente:` con su motivo.
- `uv run python -m pytest -q <archivo>` al trabajar; `tools/ci.py` solo al cerrar un hito agrupado, nunca por tarea.
- Si un resultado no coincide con el «Esperado» del plan, **parar y reportar**.

## Review Focus

- **Estado real (17 de noviembre de 2026, tras integrar `origin/main` hasta el hito 270n):** Byron ya hizo `C-20`, `C-21`, `D2-2` a `D2-13`, `D2-15`, `D2-18`, `D1-7` a `D1-15` y parte de `K`. Esta cola solo debe pedirle lo que falta.
- `C-22` genera la lista de cobertura de procedimientos (`tools/cobertura_procs.py` → `docs/cobertura-procedimientos.md`, integrado por G-17 en `docs/cobertura.md`); el change `generar-cobertura-procedimientos` quedó **superado** por ella: no se hace aparte.
- `G` necesita los verificadores Q1 a Q15 de Andres (`F1-1` a `F1-5`): hasta que existan, las tareas que los integran esperan.
- Una mención de Studio suele ser «lote C»: se hace sin Studio y la validación queda en `out/studio-pendientes.json`.

## 0. Antes de la primera tarea (15 minutos)

- [ ] **0.1** `git pull --rebase`; `git status` limpio.
- [ ] **0.2** Leer `AGENTS.md` y `docs/BLOQUEOS.md` («Estado de un vistazo»).
- [ ] **0.3** Correr la prueba de cada tarea antes de empezar: si ya pasa, está hecha.

## 1. Cola por plan

### Plan C, procedimientos (C-16 a C-23) (`2026-11-11-mg-c-sql-y-procedimientos.md`)

**Pendientes sin Studio ni personas (5):**

| Tarea | Qué | Pasos | Studio o Docker |
|---|---|---:|:-:|
| `C-16` | `PROC SORT` completo: `NODUPREC` sin `_ALL_`, `DUPOUT=`, `NOEQUALS`, `DESCENDING` | 5 |  |
| `C-17` | `PROC MEANS` y `PROC SUMMARY` con `CLASS`, `VAR` y `OUTPUT OUT=` | 5 |  |
| `C-18` | `PROC FREQ`: lo que las guías demuestran y lo que no | 5 |  |
| `C-22` | Política de `PRINT`, `REPORT`, `TABULATE` y `ODS`, y lista de procedimientos fuera de alcance genera | 5 |  |
| `C-23` | `PROC FORMAT` y `PROC SQL` avanzado que falte | 5 |  |

**Pendientes que mencionan Studio, Docker o personas (1):**

| Tarea | Qué | Pasos | Studio o Docker |
|---|---|---:|:-:|
| `C-19` | `PROC TRANSPOSE` | 5 | sí |

**Citadas en un hito de `PROGRESS.md` (2): verificar con la prueba de la tarea antes de darlas por hechas:**

| Tarea | Qué | Pasos | Studio o Docker | Citada en |
|---|---|---:|:-:|---|
| `C-20` | Política de `PROC DELETE`, `CONTENTS`, `DATASETS` y `COPY` | 0 |  | 245n |
| `C-21` | `PROC APPEND` con base nueva, repetido y en bucle | 0 |  | 246n |

### Plan D1, expresiones y funciones (`2026-11-11-mg-d1-expresiones-y-funciones.md`)

**Pendientes sin Studio ni personas (8):**

| Tarea | Qué | Pasos | Studio o Docker |
|---|---|---:|:-:|
| `D1-1` | Línea base e inventario de funciones | 0 |  |
| `D1-2` | Extraer las funciones del intérprete a módulos propios | 0 |  |
| `D1-4` | Despacho universal de funciones y operadores con faltantes | 0 |  |
| `D1-16` | Informats y formats de fecha con `YEARCUTOFF`; cierra `l4_20` | 5 |  |
| `D1-18` | `PRXMATCH`, `PRXPARSE` y `PRXCHANGE` en el intérprete, y las diferencias con Java | 5 |  |
| `D1-20` | Formatos de usuario: rangos, `OTHER` y `PUT` con mapa | 4 |  |
| `D1-21` | `docs/funciones.md` generado desde las tablas, sin edición manual | 4 |  |
| `D1-22` | `LENGTH`, `COMPBL`, `CONTAINS` e `IS MISSING` sobre expresión en el oráculo de `PROC SQL` | 5 |  |

**Pendientes que mencionan Studio, Docker o personas (2):**

| Tarea | Qué | Pasos | Studio o Docker |
|---|---|---:|:-:|
| `D1-17` | `PUT` con formatos numéricos y de texto | 5 | sí |
| `D1-19` | `PRX*` a Java de Talend | 5 | sí |

**Citadas en un hito de `PROGRESS.md` (13): verificar con la prueba de la tarea antes de darlas por hechas:**

| Tarea | Qué | Pasos | Studio o Docker | Citada en |
|---|---|---:|:-:|---|
| `D1-3` | Todos los vectores se ejecutan en el intérprete y los dos motores coinciden | 0 |  | 209n |
| `D1-5` | Los vectores se vuelven casos `L4` y corren en el lote C | 0 | sí | 212n |
| `D1-6` | Una sola definición de cada función Java de Talend | 0 |  | 214n |
| `D1-7` | Texto A: `PROPCASE`, `REVERSE`, `REPEAT`, `RIGHT`, `TRIMN` y el arreglo de `LENGTH` | 0 |  | 261n |
| `D1-8` | Texto B: `COMPBL`, `TRANWRD`, `TRANSLATE`, `INDEX`, `FIND`, `COUNT`, `LENGTHC` y `LENGTHN` | 0 | sí | 262n |
| `D1-9` | `SUBSTR` como pseudovariable y la familia `CAT` con faltantes | 0 | sí | 263n |
| `D1-10` | Numéricas: `INT`, `CEIL`, `FLOOR`, `MOD`, `ABS`, `SQRT`, `LOG`, `EXP`, `SIGN` y `ROUND` | 0 | sí | 264n |
| `D1-11` | Agregación por fila y condicionales: `SUM`, `MEAN`, `MIN`, `MAX`, `N`, `NMISS`, `CMISS`, `COALESCE`, | 0 | sí | 264n, 265n |
| `D1-12` | Base de fechas: `MDY`, `YEAR`, `MONTH`, `DAY`, `WEEKDAY`, `QTR`, `DATEPART`, `TODAY`, `DATE` | 0 | sí | 265n, 266n |
| `D1-13` | `INTNX` con fin de mes y bisiestos | 0 | sí | 266n, 267n, 268n |
| `D1-14` | `INTCK`, `DATDIF` y `YRDIF` | 0 | sí | 268n, 269n |
| `D1-15` | Informats numéricos y las formas `w.d` del programa grande | 5 |  | 269n |
| `D1-Gate` | todos los vectores en B y en lote C; `L4` completo; `xfail` con su motivo | 5 | sí | 213n, 261n, 263n |

### Plan D2, entrada y salida (`2026-11-11-mg-d2-entrada-y-salida.md`)

**Pendientes sin Studio ni personas (1):**

| Tarea | Qué | Pasos | Studio o Docker |
|---|---|---:|:-:|
| `D2-1` | Línea base medida de entrada y salida | 0 |  |

**Pendientes que mencionan Studio, Docker o personas (4):**

| Tarea | Qué | Pasos | Studio o Docker |
|---|---|---:|:-:|
| `D2-14` | Formats de salida en `PUT` por columna y formateado: `COMMAw.d`, `DATEw.` y `$w.` | 6 | sí |
| `D2-16` | `FILENAME ... FTP` a `tFTPGet` y lectura local | 5 | sí |
| `D2-17` | `RSUBMIT`, `PROC UPLOAD` y `PROC DOWNLOAD` de datasets | 6 | sí |
| `D2-Gate` | `L0` completo y casos de base en lote C | 5 | sí |

**Citadas en un hito de `PROGRESS.md` (14): verificar con la prueba de la tarea antes de darlas por hechas:**

| Tarea | Qué | Pasos | Studio o Docker | Citada en |
|---|---|---:|:-:|---|
| `D2-2` | Paso directo `CONNECT TO impala ... FROM CONNECTION TO` a un lector con SQL literal | 1 | sí | 248n |
| `D2-3` | Paso directo a Postgres y conexión compartida entre `execute by` y `select from connection` | 1 | sí | 249n |
| `D2-4` | `LIBNAME` a bases (Impala y Postgres) con conexión compartida y contexto | 1 | sí | 250n |
| `D2-5` | `LIBNAME` a rutas y registro de bibliotecas con variable de contexto | 0 |  | 251n |
| `D2-6` | `PROC IMPORT` de XLSX y XLS con `SHEET`, contraseña de plantilla y lector propio | 0 | sí | 252n, 253n |
| `D2-7` | `PROC EXPORT` a XLSX con `SHEET` y salida conservadora | 0 | sí | 254n |
| `D2-8` | `GETNAMES`, `DATAROW` y `GUESSINGROWS` sobre archivos delimitados | 0 | sí | 255n |
| `D2-9` | `INFILE/INPUT` en lista con `DSD`, `MISSOVER` y `FIRSTOBS` a `tFileInputDelimited` | 0 | sí | 256n |
| `D2-10` | `INFILE/INPUT` por columna y formateado a `tFileInputPositional` | 3 | sí | 257n, 259n |
| `D2-11` | `FILE` y `PUT` en lista con `DSD` y `DLM` a un archivo de salida | 0 | sí | 258n, 267n |
| `D2-12` | Informats numéricos en `INPUT`: `w.d`, `COMMAw.d` y `DOLLARw.d` | 0 | sí | 259n |
| `D2-13` | Informats de fecha `YYMMDD`, `DDMMYY`, `DATE9` y `ANYDTDTE` en `INPUT` | 0 | sí | 260n |
| `D2-15` | `FILENAME` a archivo y a pipe | 0 | sí | 267n |
| `D2-18` | Datasets permanentes a archivo de preparación con aviso | 6 | sí | 251n |

### Plan E, macros (`2026-11-11-mg-e-macros.md`)

**Pendientes sin Studio ni personas (16):**

| Tarea | Qué | Pasos | Studio o Docker |
|---|---|---:|:-:|
| `E-1` | Línea base medida de L5, paridad de expansores y catálogo de sentencias de macro | 5 |  |
| `E-2` | `%STR` y `%NRSTR` en `%LET` | 5 |  |
| `E-3` | `%SYSFUNC` con funciones de texto deterministas | 5 |  |
| `E-4` | `&&var&i` y referencias indirectas | 5 |  |
| `E-5` | `%IF` con condiciones compuestas, parámetros y `%LENGTH` | 5 |  |
| `E-6` | `%EVAL` entero completo | 5 |  |
| `E-7` | `%DO %WHILE`, `%DO %UNTIL` con condición constante | 5 |  |
| `E-8` | Alcance de variables: `%LOCAL`, `%GLOBAL` y `%LET` dentro de una macro | 5 |  |
| `E-9` | Autollamada con fin constante y `%INCLUDE` sin resolver | 5 |  |
| `E-10` | Registro de invocaciones y informe de bloques repetidos (contrato con el Plan F1; serie `n`) | 5 |  |
| `E-12` | Informe de repeticiones sobre los programas del repositorio | 5 |  |
| `E-13` | Registro de variables de macro de ejecución y candidatas a contexto (contratos con Plan B, MG-P4-08, | 5 |  |
| `E-14` | Intérprete: `set_variable` y referencias `&var` en el anillo B (cierra `l5_09`; serie `n`) | 5 |  |
| `E-15` | `CALL EXECUTE` y código dinámico como pendiente con código estable | 5 |  |
| `E-16` | Detección y aviso de `MISSING=`, `YEARCUTOFF=`, `VALIDVARNAME=` y `MERGENOBY=` | 5 |  |
| `E-17` | `PROC DOWNLOAD` dentro de `RSUBMIT` con lectura y escritura | 5 |  |

**Pendientes que mencionan Studio, Docker o personas (3):**

| Tarea | Qué | Pasos | Studio o Docker |
|---|---|---:|:-:|
| `E-11` | Bucles `%DO` como bloque repetido y el patrón de `PROC APPEND` en bucle (contrato con el Plan K, K-6 | 5 | sí |
| `E-18` | Tablas de `WORK` «leídas antes de crearse» y macros de SAS Studio sin definición (contrato con K-6;  | 5 | sí |
| `E-19` | `sql_tree` con subconsultas en `FROM` | 10 | sí |

**Citadas en un hito de `PROGRESS.md` (0): verificar con la prueba de la tarea antes de darlas por hechas:**

_Ninguna._

### Plan G, verificación y cobertura (`2026-11-11-mg-g-verificacion-y-cobertura.md`)

**Pendientes sin Studio ni personas (14):**

| Tarea | Qué | Pasos | Studio o Docker |
|---|---|---:|:-:|
| `G-1` | Auditor de `PROGRESS.md` | 5 |  |
| `G-2` | Número siguiente por serie y procedimiento seguro de ordenado | 5 |  |
| `G-3` | Prueba de determinismo con `PYTHONHASHSEED` de 0 a 9 sobre todo el corpus (criterio C5; MG-P10-01, p | 6 |  |
| `G-5` | Termómetro por regiones del programa real grande | 5 |  |
| `G-7` | `docs/arquitectura/ir-logica.md`: cómo se reutiliza el IR que ya existe | 5 |  |
| `G-8` | Medidor del anillo B, lista de `xfail` con dueño y trinquete | 5 |  |
| `G-10` | Biblioteca de etapas y generador de casos L7 y L9 con anomalías plantadas | 5 |  |
| `G-11` | 20 casos L7 (varias etapas con rechazos y conciliación) | 5 |  |
| `G-12` | 20 casos L9 (programa grande con datos simulados) | 6 |  |
| `G-13` | Generador de programas SAS con oráculo independiente | 6 |  |
| `G-14` | Reducción automática de fallos y promoción al corpus | 5 |  |
| `G-15` | Robustez de `sgm migrar` (criterio C2): entradas basura y todo el repositorio | 5 |  |
| `G-17` | `sgm cobertura` genera `docs/cobertura.md` y su JSON desde las reglas y el corpus | 6 |  |
| `G-20` | Segundo y tercer programa del cliente: cobertura medida, creciente y con dueño por brecha | 5 |  |

**Pendientes que mencionan Studio, Docker o personas (6):**

| Tarea | Qué | Pasos | Studio o Docker |
|---|---|---:|:-:|
| `G-6` | Tablero único de criterios C1 a C6 y tiempos del ciclo rápido | 5 | sí |
| `G-9` | Cada expresión Java generada compila sola con `javac` | 6 | sí |
| `G-16` | Prueba de mutación del arnés de comparación | 5 | sí |
| `G-18` | Corrida nocturna (anillo D) con informe diario y alerta de regresión | 5 | sí |
| `G-19` | «Estable 14 días»: cómo se mide para GM5 | 5 | sí |
| `G-Gate` | GM5 y criterios C1, C3 y C5 medidos | 5 | sí |

**Citadas en un hito de `PROGRESS.md` (1): verificar con la prueba de la tarea antes de darlas por hechas:**

| Tarea | Qué | Pasos | Studio o Docker | Citada en |
|---|---|---:|:-:|---|
| `G-4` | Un comando recalcula la tabla 11b desde un YAML de créditos | 6 |  | 200n |

### Plan H, producto, rendimiento y seguridad (`2026-11-11-mg-h-producto-rendimiento-seguridad.md`)

**Pendientes sin Studio ni personas (16):**

| Tarea | Qué | Pasos | Studio o Docker |
|---|---|---:|:-:|
| `H-1` | Partir `cli.py` y mover `explain` a su módulo | 5 |  |
| `H-2` | Registro de códigos de pendiente con texto y sugerencia | 5 |  |
| `H-3` | `pendientes.md` y la consola muestran la sugerencia | 5 |  |
| `H-4` | Cargador y validador del YAML de ajustes con archivo y línea | 5 |  |
| `H-5` | `sgm migrar --ajustes` aplica nombres y valores de contexto | 5 |  |
| `H-6` | Dependencias entre programas y orden de ejecución | 5 |  |
| `H-7` | El lote escribe `proyecto.md` y `proyecto.json` | 5 |  |
| `H-8` | `sgm explicar` sobre `trace.json` | 5 |  |
| `H-9` | `sgm comparar --paquete` apunta a las líneas del SAS | 5 |  |
| `H-11` | Decisión del código de salida ante un secreto, informe de bloqueo y su prueba | 6 |  |
| `H-12` | Lista configurable de columnas sensibles | 5 |  |
| `H-14` | Los informes de `sgm migrar` no copian valores de la muestra | 5 |  |
| `H-15` | Valores hostiles dentro de literales SQL y Java | 5 |  |
| `H-17` | La caché en la CLI y la segunda corrida medida | 5 |  |
| `H-19` | Opciones de volumen en el emisor: lookups en disco y tamaño de búfer | 5 |  |
| `H-21` | Lista de verificación de persona: secretos del fixture viejo y de la copia externa | 4 |  |

**Pendientes que mencionan Studio, Docker o personas (6):**

| Tarea | Qué | Pasos | Studio o Docker |
|---|---|---:|:-:|
| `H-10` | Guía de usuario, guía de operación y catálogo de construcciones generados | 5 | sí |
| `H-13` | El `tLogRow` de cierre enmascara las columnas sensibles | 5 | sí |
| `H-16` | Caché por programa para `sgm migrar` | 5 | sí |
| `H-18` | Banco de volumen: datos sintéticos, escenarios y corredor en contenedor | 5 | sí |
| `H-20` | Plantillas de JVM, lote de volumen en contenedor y límites documentados | 6 | sí |
| `H-Gate` | Compuerta GM6 y criterios C2, C4 y C6 | 0 | sí |

**Citadas en un hito de `PROGRESS.md` (0): verificar con la prueba de la tarea antes de darlas por hechas:**

_Ninguna._

### Plan K, datos de prueba (`2026-11-11-mg-k-datos-de-prueba-y-bases.md`)

**Pendientes sin Studio ni personas (3):**

| Tarea | Qué | Pasos | Studio o Docker |
|---|---|---:|:-:|
| `K-7c` | Rebanada SORT/DELETE | 0 |  |
| `K-11` | Catálogo de fixtures y auditoría «sintético nunca real» | 5 |  |
| `K-12` | Regeneración y deriva de los fixtures | 5 |  |

**Pendientes que mencionan Studio, Docker o personas (5):**

| Tarea | Qué | Pasos | Studio o Docker |
|---|---|---:|:-:|
| `K-7a` | Rebanada IMPORT/EXPORT | 1 | sí |
| `K-7b` | Rebanada SQL a Impala (con el contenedor) | 2 | sí |
| `K-7d` | Rebanada UPLOAD/DOWNLOAD | 5 | sí |
| `K-7e` | Rebanada de totales | 5 | sí |
| `K-Gate` | Los dos programas reales tienen esperado reproducible | 5 | sí |

**Citadas en un hito de `PROGRESS.md` (11): verificar con la prueba de la tarea antes de darlas por hechas:**

| Tarea | Qué | Pasos | Studio o Docker | Citada en |
|---|---|---:|:-:|---|
| `K-1` | Fixture sintético de `sashelp.cars` con ficha y semilla | 0 |  | 215n |
| `K-8` | Rebanador de programas reales y esperado del intérprete | 0 | sí | 216n, 217n, 218n |
| `K-2` | `sgm esquemas --desde-programa` | 0 |  | 216n, 217n, 219n, 220n, 221n, 222n, 223n, 229n, 230n |
| `K-9` | Tablas de biblioteca local como lectura de archivo (`sashelp.cars` en el Job) | 0 |  | 224n, 225n, 226n, 227n |
| `K-3` | Generador de datos por esquema y carga tipada a los contenedores | 1 | sí | 220n, 228n, 229n, 231n |
| `K-10` | Requisitos de datos de cada rebanada y manifiesto | 0 |  | 230n, 234n |
| `K-4` | Contexto `DEV` apuntando a los contenedores (`tImpalaRow` ejecutable sin credenciales reales) | 1 | sí | 231n, 249n |
| `K-5` | `RSUBMIT`, `PROC UPLOAD` y `PROC DOWNLOAD` como copias locales | 0 | sí | 232n |
| `K-6` | Programa pequeño de punta a punta (anillos A, B y C) | 2 | sí | 232n, 233n, 234n, 236n, 241n, 243n, 244n |
| `K-13` | Preparar los datos de una rebanada (manifiesto a `entradas/` y a contenedor) | 0 | sí | 234n, 237n |
| `K-7` | Mapa de rebanadas del programa grande y compuerta de secretos | 0 |  | 234n, 235n |

## Self-review

- Las tareas C-1 a C-15 y C-Gate (SQL) son de Andres y no están aquí.
- «Studio o Docker» sale de buscar esas palabras en el bloque de la tarea: es un aviso, no un veredicto.
- «Citada en» sale de `PROGRESS.md`: una tarea citada en varios hitos suele estar a medias.
