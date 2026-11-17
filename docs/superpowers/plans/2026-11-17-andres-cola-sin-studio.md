# Cola de trabajo de Andres, sin Studio Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans. Este documento **no repite los pasos**: cada tarea ya está escrita, con su prueba, su comando y su resultado esperado, en el plan de su carril. Aquí solo se ordena la cola, se marca lo que ya hicieron los hitos y lo que pide Studio o Docker.

**Goal:** Que Andres (serie `m`) avance hoy lo que se puede cerrar sin abrir Talend Studio y deje lo demás en la cola de pendientes.

**Architecture:** Una cola por plan, dividida en pendientes sin Studio, pendientes con Studio y tareas ya citadas en `PROGRESS.md`. «Citada» sale de buscar el id de la tarea (`D1-7`, `B-13`…) en las entradas de hito de las series `m` y `n` desde el hito 190: es una pista, no una prueba de que esté terminada.

**Tech Stack:** Python 3.12 (`uv`, pytest, ruff); reglas YAML; OpenSpec 2.1.0.

**Spec:** `docs/plan-reescritura/plan-migrador-general.md` y `docs/superpowers/plans/2026-11-11-ruta-al-100.md` (§8).

## Global Constraints

- Serie `m` en `PROGRESS.md` y en el commit: `hito Nm: <resumen>`. El número es **único en todo el repositorio**: último `## Hito` de `PROGRESS.md` más uno, sea de la serie que sea (hoy el 270n es el más alto, así que el siguiente libre es el 271).
- Cada tarea nace de un change de OpenSpec, con la tarea del plan como cuerpo de `tasks.md`.
- **Pocos componentes** y **sin Studio mientras se itera** (`AGENTS.md`, 17 de noviembre de 2026): lo que no cabe queda `Pendiente:` con su motivo.
- `uv run python -m pytest -q <archivo>` al trabajar; `tools/ci.py` solo al cerrar un hito agrupado, nunca por tarea.
- Si un resultado no coincide con el «Esperado» del plan, **parar y reportar**.

## Review Focus

- **Estado real:** las tareas del plan B ya aparecen citadas en los hitos 201m a 255m (`B-1` a `B-22`); lo que queda de B es lo que dice `docs/BLOQUEOS.md` (validar en Studio, `B-16` y `B-20` en código). Lo que de verdad falta sin Studio son **C-1 a C-15 (SQL), F1 e I (empaquetado y compuerta)**: ninguna está citada en `PROGRESS.md`.
- Joblets: sin Studio no se puede confirmar que el joblet cargue; se emite el plan B (Job hijo con `tRunJob`) y la validación va a la cola de pendientes.
- Decisiones ya tomadas (`BLOQUEOS.md`): `MERGE` solo con llave única, `LAST.` pendiente, `CALL SYMPUT` como `tJavaRow`, un pendiente de escritura impide emitir el Job.
- Producción: C7 (piloto, UAT, corrida paralela y firma) es de personas y no se hace hoy.

## 0. Antes de la primera tarea (15 minutos)

- [ ] **0.1** `git status` y `uv run python tools/validacion.py estado`.
- [ ] **0.2** Hacer el plan del día (`2026-11-17-plan-del-dia.md`) primero: baja el tiempo de cada cierre.
- [ ] **0.3** Correr la prueba de cada tarea antes de empezar: si ya pasa, está hecha.

## 1. Cola por plan

### Plan C, parte SQL (C-1 a C-15 y C-Gate) (`2026-11-11-mg-c-sql-y-procedimientos.md`)

**Pendientes sin Studio ni personas (14):**

| Tarea | Qué | Pasos | Studio o Docker |
|---|---|---:|:-:|
| `C-1` | Línea base medida de SQL y procedimientos | 5 |  |
| `C-2` | Extraer uniones y agregados de los módulos de más de 300 líneas | 5 |  |
| `C-3` | `FULL JOIN` y `RIGHT JOIN` en el intérprete, con nulos que casan | 5 |  |
| `C-5` | Llaves de varias columnas con blancos y auto-JOIN con alias | 5 |  |
| `C-6` | `GROUP BY` y `HAVING` con la semántica de faltantes, en el intérprete y en el emisor | 5 |  |
| `C-7` | Remezcla de estadísticos: agregado sin `GROUP BY` junto a columnas simples | 5 |  |
| `C-8` | Subconsulta escalar y subconsulta en `FROM` | 5 |  |
| `C-9` | `EXISTS`, `NOT EXISTS` y subconsulta correlacionada | 5 |  |
| `C-10` | `UNION`, `INTERSECT` y `EXCEPT` | 5 |  |
| `C-11` | `OUTER UNION` y `OUTER UNION CORR` | 5 |  |
| `C-12` | `CREATE VIEW`, `CREATE TABLE ... LIKE` y `DROP` | 5 |  |
| `C-13` | `INSERT`, `UPDATE`, `DELETE FROM` y `ALTER TABLE` sobre tablas versionadas | 5 |  |
| `C-14` | `SELECT INTO :macro` y `DICTIONARY.*` | 5 |  |
| `C-15` | Funciones SAS dentro de `PROC SQL` y portabilidad de dialecto | 5 |  |

**Pendientes que mencionan Studio, Docker o personas (2):**

| Tarea | Qué | Pasos | Studio o Docker |
|---|---|---:|:-:|
| `C-4` | `FULL JOIN` y `RIGHT JOIN` emitidos a Talend, y qué hace `tMap` con las llaves nulas | 5 | sí |
| `C-Gate` | GM2 (SQL) y GM3 (procedimientos): L1 a L3 y L6 en B y en lote C | 5 | sí |

**Citadas en un hito de `PROGRESS.md` (0): verificar con la prueba de la tarea antes de darlas por hechas:**

_Ninguna._

### Plan F1, planificador y optimizador (`2026-11-11-mg-f1-planificador-y-optimizador.md`)

**Pendientes sin Studio ni personas (11):**

| Tarea | Qué | Pasos | Studio o Docker |
|---|---|---:|:-:|
| `F1-1` | Línea base medida de tamaño, regiones y cruces | 5 |  |
| `F1-2` | Modelo de calidad y criterios Q1, Q2 y Q12 (contextos y secretos; serie `m`) | 5 |  |
| `F1-3` | Criterios Q4, Q8, Q9, Q11 y Q15 (estructura y rendimiento; serie `m`) | 5 |  |
| `F1-6` | Regiones y dependencias desde el linaje | 5 |  |
| `F1-7` | Etapas por estructura: insumos, producto, totales y cierre | 5 |  |
| `F1-8` | Segmentar el plan en sub-planes por región | 5 |  |
| `F1-9` | `sgm diseno` sin YAML produce padre e hijos | 5 |  |
| `F1-10` | Política de tamaño: tramos de a lo más 20 componentes con los menos datos cruzando | 5 |  |
| `F1-12` | Padre por dependencias, hijos emitidos y `sgm migrar --arquitectura` | 6 |  |
| `F1-14` | Nombres únicos y `trace.json` completo | 6 |  |
| `F1-16` | Fundir DATA step encadenados con `KEEP`, `DROP` y `RENAME` en el productor | 5 |  |

**Pendientes que mencionan Studio, Docker o personas (9):**

| Tarea | Qué | Pasos | Studio o Docker |
|---|---|---:|:-:|
| `F1-4` | Criterios Q3, Q5, Q6, Q7, Q10, Q13 y Q14 (orquestación, errores, registro y trazabilidad; serie `m`) | 5 | sí |
| `F1-5` | Q1 a Q15 sobre el corpus, con tablero de avance | 5 | sí |
| `F1-11` | Paso de datos entre Jobs por archivos de trabajo | 5 | sí |
| `F1-13` | Errores y registro por defecto, con política de fallo parcial | 5 | sí |
| `F1-15` | Bloques repetidos a joblet, con `tRunJob` como plan B | 5 | sí |
| `F1-17` | Hermanos sobre la misma fuente: validar en Studio la ejecución | 5 | sí |
| `F1-18` | `tHashOutput` y `tHashInput` para ramas que reconvergen | 6 | sí |
| `F1-19` | Cálculo en la base con conexión por contexto, dentro de la arquitectura planificada | 5 | sí |
| `F1-Gate` | Arquitectura planificada por omisión y Q1 a Q15 al 100 % | 6 | sí |

**Citadas en un hito de `PROGRESS.md` (0): verificar con la prueba de la tarea antes de darlas por hechas:**

_Ninguna._

### Plan I, producción (`2026-11-11-mg-i-produccion.md`)

**Pendientes sin Studio ni personas (5):**

| Tarea | Qué | Pasos | Studio o Docker |
|---|---|---:|:-:|
| `I-1` | Pruebas propias de la compuerta de liberación | 5 |  |
| `I-2` | Los datos del paquete viajan en el wheel | 5 |  |
| `I-3` | Los 15 módulos dejan de adivinar la raíz del repositorio | 5 |  |
| `I-12` | Formato de entrega del oráculo de SAS, plantilla de exportación y lector | 5 |  |
| `I-13` | Comparador de la corrida paralela: conteos, sumas de control por columna y muestra de filas | 5 |  |

**Pendientes que mencionan Studio, Docker o personas (14):**

| Tarea | Qué | Pasos | Studio o Docker |
|---|---|---:|:-:|
| `I-4` | Versión semántica y registro de cambios con una sola orden | 5 |  |
| `I-5` | Instalación en entorno virgen, automatizada, y su verificación por una persona | 5 | sí |
| `I-6` | La compuerta decide con un comando y distingue «verde» de «verde sin Studio» | 5 | sí |
| `I-7` | Paso opcional de Studio: `talend_job_build_batch` de toda la salida | 5 | sí |
| `I-8` | Guía de despliegue y runbook de operación: contenido verificable | 5 | sí |
| `I-9` | Monitoreo y alertas: códigos de salida, conteos publicados, correo y escalamiento | 5 |  |
| `I-10` | Piloto: selección, hallazgos y lista cerrada | 5 | sí |
| `I-11` | Acta de aceptación: plantilla y verificador | 5 |  |
| `I-14` | Registro de diferencias y veredicto de equivalencia del ciclo | 5 |  |
| `I-15` | Plan de contingencia y reversa: SAS en paralelo hasta el corte | 5 |  |
| `I-16` | Capacitación: material verificable y evaluación práctica | 5 |  |
| `I-17` | Paquete de corte y acta de corte | 5 | sí |
| `I-18` | Estabilización de 2 a 4 semanas: defectos, parches con prueba y criterio de salida | 5 |  |
| `I-Gate` | GM7 y GM8, y quién firma qué | 5 | sí |

**Citadas en un hito de `PROGRESS.md` (0): verificar con la prueba de la tarea antes de darlas por hechas:**

_Ninguna._

### Plan B, DATA step y plan lógico (`2026-11-11-mg-b-datastep-y-plan-logico.md`)

**Pendientes sin Studio ni personas (0):**

_Ninguna._

**Pendientes que mencionan Studio, Docker o personas (0):**

_Ninguna._

**Citadas en un hito de `PROGRESS.md` (23): verificar con la prueba de la tarea antes de darlas por hechas:**

| Tarea | Qué | Pasos | Studio o Docker | Citada en |
|---|---|---:|:-:|---|
| `B-1` | Línea base medida de MG-P1 y L6 | 5 |  | 208m |
| `B-2` | Tipos de columna demostrados por `PROC IMPORT` | 5 |  | 201m |
| `B-3` | Tipos desde `INPUT`, `LENGTH`, `FORMAT`, `ATTRIB`, `CREATE TABLE`, `SELECT` y `SET` | 5 |  | 202m, 203m, 204m, 224m |
| `B-4` | Esquema de cada tabla del corpus coincide con `caso.yaml` (cierra MG-P1-02) | 5 |  | 202m, 203m, 204m |
| `B-5` | Operadores del plan lógico usados por los pases del DATA step | 5 |  | 208m, 209m, 213m, 214m, 215m, 216m, 217m, 218m, 219m, 220m |
| `B-6` | `L1` a `L3` construyen su plan sin forma anterior (cierra MG-P1-03) | 0 |  | 208m, 219m, 220m, 221m, 222m, 230m |
| `B-7` | `SQL a plan` sin pendientes que no sean de alcance | 4 |  | 223m, 230m |
| `B-8` | `DATA step a plan` y `PROC a plan` para L4 a L6 | 4 |  | 222m, 224m, 230m, 233n |
| `B-9` | Investigar `SET a b;` en Studio: ¿`tUnite` compila y ejecuta con el orden de SAS? | 5 | sí | 225m, 230m, 253m |
| `B-10` | `SET a b;` concatena por nombre con faltante | 5 | sí | 225m, 230m, 253m, 254m |
| `B-11` | `MERGE ... BY ... IN=` con la semántica real en el intérprete | 5 | sí | 225m, 230m, 247m |
| `B-12` | `MERGE` emitido como `tSortRow` + `tJavaRow`, no como JOIN | 5 | sí | 225m, 230m, 247m |
| `B-13` | `RETAIN`, sentencia suma, `FIRST.`/`LAST.`, `LAG`, `DIF` en el intérprete | 5 | sí | 225m, 230m, 247m, 248m, 249m, 250m, 251m, 255m |
| `B-14` | Estado por fila emitido con `tSortRow` + `tJavaRow` | 5 | sí | 225m, 230m, 247m |
| `B-15` | `SELECT/WHEN` y `DELETE` | 2 | sí | 225m, 226m, 230m, 231m, 239m |
| `B-16` | `ARRAY` y `DO` | 3 | sí | 226m, 230m, 232m, 233m, 234m |
| `B-17` | Generador de combinaciones de `OUTPUT` (cierra MG-P4-02, parte 1) | 3 |  | 227m, 230m, 235m, 236m, 239m, 240m, 243m, 245m |
| `B-18` | Una validación en lote en Studio de las combinaciones de `OUTPUT` (cierra MG-P4-02, parte 2) | 5 | sí | 225m, 230m, 243m, 246m |
| `B-19` | `UPDATE` y `MODIFY` | 5 | sí | 225m, 230m, 251m, 252m |
| `B-20` | `_N_`, `_ERROR_` y `CALL SYMPUT` | 4 | sí | 228m, 230m, 237m, 244m |
| `B-21` | Hash objects: soporte mínimo o pendiente con motivo | 5 |  | 229m, 230m, 238m, 246m |
| `B-22` | Plan maestro, catálogo y créditos al día | 4 | sí | 230m |
| `B-Gate` | GM1 y L6 completo en B y en lote C | 5 | sí | 225m, 230m, 231m, 239m, 246m |

### Plan F2, emisor y joblets (`2026-11-11-mg-f2-emisor-y-joblets.md`)

**Pendientes sin Studio ni personas (1):**

| Tarea | Qué | Pasos | Studio o Docker |
|---|---|---:|:-:|
| `F2-11` | Valores por entorno desde `contextos/<grupo>.yaml` y `tContextLoad` | 5 |  |

**Pendientes que mencionan Studio, Docker o personas (19):**

| Tarea | Qué | Pasos | Studio o Docker |
|---|---|---:|:-:|
| `F2-1` | Catálogo único de plantillas con metadatos y línea base medida | 5 | sí |
| `F2-2` | Generador automatizado de plantilla nueva (agregar un componente en menos de 30 minutos) | 5 | sí |
| `F2-3` | Arnés de humo por plantilla (compila y ejecuta con datos) | 5 | sí |
| `F2-4` | Lote de plantillas de archivos (7) | 5 | sí |
| `F2-5` | Lote de plantillas de transformación (7) | 5 | sí |
| `F2-6` | Lote de plantillas de control y utilidades (6) | 5 | sí |
| `F2-7` | Lote de plantillas de bases de datos (PostgreSQL e Impala, 9) | 5 | sí |
| `F2-8` | Escritor de joblets y spike de carga en Studio 8.0.1 | 5 | sí |
| `F2-9` | Plan B con Job hijo `tRunJob` y la regla de cuándo cada uno | 5 | sí |
| `F2-10` | Un bloque reutilizable usado en dos Jobs, compilado y ejecutado | 5 | sí |
| `F2-12` | Job ejecutado con `DEV` y con `QA` (el valor de cada variable impreso) | 5 | sí |
| `F2-13` | Referencia de Studio para los disparadores y quitar sus `xfail` | 5 | sí |
| `F2-14` | `Reject`, `Filter` y orden de ejecución con `ORDER` | 5 | sí |
| `F2-15` | Disposición por subjobs sin superposición de cajas (Q11) | 5 | sí |
| `F2-16` | Propiedades del Job y notas con la línea de SAS (Q10) | 5 | sí |
| `F2-17` | Rutina de repositorio solo cuando una expresión inline no alcanza | 5 | sí |
| `F2-18` | Comparar el emisor propio con `talend_jobs_create_from_spec` | 5 | sí |
| `F2-19` | Ida y vuelta en el editor de Studio (Q14: persona y agente) | 5 | sí |
| `F2-20` | F2-Gate. Arquitectura por omisión con reutilización, contextos y límites (GM4, lote C) | 5 | sí |

**Citadas en un hito de `PROGRESS.md` (0): verificar con la prueba de la tarea antes de darlas por hechas:**

_Ninguna._

## Self-review

- El Plan A (Studio y `talend-mcp`) se excluye: todo necesita Studio. C-16 a C-23 son de Byron.
- «Citada en» sale de `PROGRESS.md`: es una pista, no una prueba.
