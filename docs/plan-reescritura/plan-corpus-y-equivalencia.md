# Plan: corpus escalonado y equivalencia verificable con SAS

Propuesto por el usuario el 4 de noviembre de 2026 y adoptado como camino principal hacia la meta
(que la salida se parezca al diseño manual). Complementa `tareas-agente.md`: aquel documento lista qué
construir; este explica cómo saber que lo construido es correcto.

## 1. El problema que resuelve

Hoy se puede demostrar que un Job de Talend compila y corre con datos simulados. No se puede demostrar
que haga lo mismo que el SAS, por tres razones: no hay datos reales, no hay una corrida real del
programa para comparar y no hay un SAS para ejecutar (es software comercial). Sin esa comparación, "se
parece al diseño manual" solo mide estructura, no comportamiento.

## 2. La idea

Construir muchos programas SAS pequeños, de dificultad creciente, y de cada uno tener cuatro cosas:
el programa, datos de entrada simulados, el resultado esperado y el Job de Talend generado. Un caso pasa
si el Job, ejecutado en Studio con esas entradas, produce el resultado esperado. Se empieza por lo
trivial (un DATA step con un filtro) y se escala hasta rebanadas del programa grande.

El corpus sirve a la vez de: prueba de regresión, medida de cobertura (qué construcciones del SAS se
traducen y se verifican), y biblioteca de reglas (cada nivel enseña una).

Ya existe la materia prima: `tests/fixtures/sas/` tiene 172 programas (50 reales, 122 sintéticos, siete de
generalización, tres sets más en `tests/fixtures/`). Les faltan entradas y resultado esperado.

## 3. De dónde sale el resultado esperado (el oráculo)

No hay SAS. Se usan tres capas, de más a menos fiable. Un caso declara cuál usó.

| Capa | Qué es | Para qué | Riesgo |
|---|---|---|---|
| A. SQL ejecutable | `PROC SQL` se ejecuta en SQLite (módulo estándar de Python, ya presente) sobre las tablas de entrada | Joins, filtros, agregados, `IS MISSING`, `GROUP BY` | El SQL de SAS tiene diferencias (nulos, `MISSING`, orden, funciones); cada diferencia se traduce explícitamente |
| B. Semántica de funciones | Vectores de prueba tomados de la documentación de SAS para `input`, `left`, `compress`, `put`, `substr`, `scan`, comparación con faltantes, redondeo | Pasos DATA y conversiones | Que la implementación de referencia en Python entienda mal la documentación |
| C. Dorado a mano | Resultado escrito por una persona o por un agente y revisado por un segundo | Casos mínimos donde el cálculo es evidente | Error humano |

Defensa contra el malentendido compartido (que oráculo y traductor se equivoquen igual): los vectores de
la capa B citan su fuente en la documentación de SAS y se verifican contra ella; los casos de la capa C
los comprueba un segundo agente sin ver el primero; y al final hace falta una corrida real mínima (sección 8).

## 4. Contenedores y bases de datos

El diseño manual lee tablas de Impala. No hay Impala. Opciones, de la más simple a la más fiel:

1. Sin contenedor: las tablas Impala se simulan con CSV y una variable de contexto `modo_simulacion`
   (tarea T03 de `tareas-agente.md`). Es el punto de partida y no requiere nada instalado.
2. Contenedor PostgreSQL para probar lectura y escritura de base con `tDBInput` y `tDBOutput` reales.
3. Contenedor Hive (`apache/hive:4.0.1`, ya usado por la documentación de `talend-mcp`) para un SQL parecido
   al de Impala; con el controlador HiveServer2.
4. Impala real en contenedor: pesado y de poco valor sobre el punto 3. Solo si el usuario lo pide.

Estado: Docker 29.7.2 está instalado pero **el motor no está encendido** (Docker Desktop apagado). Para
usar los puntos 2 y 3 hay que encenderlo.

Excepción a `AGENTS.md`, regla 3 ("no conectarte a Impala ni a ninguna base"): el usuario autorizó el uso
de contenedores locales para pruebas. La regla sigue vigente para el producto: `sgm` nunca se conecta a
una base; solo los Jobs generados, ejecutados en Studio contra un contenedor local de pruebas, lo hacen.
Anotarlo en "Decisiones" de `PROGRESS.md` cuando se use por primera vez.

## 5. La escalera de niveles

Cada nivel agrega construcciones nuevas sobre el anterior. Un nivel está terminado cuando todos sus casos
pasan de punta a punta (traducción, Job compila, Job corre, resultado igual al esperado) y el informe de
cobertura lista lo que sigue sin traducir.

| Nivel | Construcciones | Casos orientativos | Capa de oráculo |
|---|---|---|---|
| L0 | `DATA` con `SET`, `KEEP`, `DROP`, `RENAME`, `WHERE`, asignaciones simples; `PROC IMPORT` y exportación de CSV | 15 | C |
| L1 | `PROC SQL`: `SELECT`, `WHERE`, `ORDER BY`, `DISTINCT`, alias, `CREATE TABLE AS` | 15 | A |
| L2 | `JOIN` (`INNER`, `LEFT`), `IS MISSING`, `IN`, `CASE`; el patrón de validación con lookup y rechazo | 15 | A |
| L3 | Agregados: `COUNT`, `SUM`, `MIN`, `MAX`, `GROUP BY`, `HAVING`; totales de origen y de salida | 12 | A |
| L4 | Funciones de DATA step: `input`, `left`, `compress`, `put`, `substr`, `scan`, `strip`, `upcase`, fechas | 20 | B |
| L5 | Macros simples: `%let`, `%macro` con parámetros, `%if`, `%do`; macrovariables en nombres y rutas | 12 | C |
| L6 | `MERGE` con `BY`, `FIRST.` y `LAST.`, `RETAIN`, `PROC SORT` con `NODUPKEY`, duplicados | 12 | B y C |
| L7 | Varias etapas encadenadas con archivos de rechazo y conciliación (origen igual a válidos más rechazados) | 10 | A, B |
| L8 | Rebanadas del programa grande: una etapa (por ejemplo tipo de documento) con datos simulados | 12 | A, B, C |
| L9 | El programa grande completo con datos simulados | 1 | A, B, C |

Los 172 programas existentes se reparten entre niveles por las construcciones que usan (tarea K05).

## 6. Formato de un caso y ejecutor

Carpeta `tests/corpus/<nivel>/<caso>/`:

- `programa.sas`: el SAS, con su ruta de entrada y salida como en el real.
- `entradas/`: CSV y Excel de entrada (se generan con script, no a mano, y quedan en el repositorio si son
  pequeños).
- `esperado/`: resultado esperado como CSV, con el orden que corresponda.
- `caso.yaml`: nivel, construcciones que ejercita, capa de oráculo, tolerancia numérica, orden relevante o
  no, y estado (`traducible`, `parcial`, `pendiente` con motivo).

Ejecutor `tools/corpus.py` (sin Studio y con Studio):

1. `oraculo`: calcula `esperado/` a partir de `programa.sas` y `entradas/` con la capa declarada. Se
   puede volver a ejecutar y debe dar exactamente lo guardado (prueba de consistencia).
2. `traducir`: corre `sgm talend` y deja los Jobs en una carpeta.
3. `validar`: con el validador de Studio (T01) ejecuta el Job y compara su salida con `esperado/`.
4. `informe`: tabla de casos por nivel con estado y motivo; porcentaje de construcciones SAS traducidas.

La parte sin Studio (oráculo y consistencia) entra en `pytest`. La parte con Studio queda como comando
explícito, porque tarda minutos.

## 7. Fuentes para crear casos

- Los 172 programas existentes.
- Los patrones del programa grande, recortados por etapa (L8).
- La documentación pública de SAS (construcciones, funciones, ejemplos con salida documentada). Se usa
  para entender la semántica y para los vectores de la capa B con su URL. No se copian textos ni
  programas completos de terceros: se escriben programas propios inspirados en ellos.
- Repositorios públicos de ejemplos de SAS (`sassoftware` en GitHub, material de cursos universitarios)
  solo como referencia de estilo, comprobando su licencia antes de incorporar nada.
- Generación con agentes `haiku`, con una regla: el resultado esperado nunca lo escribe el mismo agente
  que el programa sin pasar por el oráculo ejecutable (capas A y B) o por revisión de un segundo agente
  (capa C).

## 8. Lo que seguirá haciendo falta de una persona

Una corrida real mínima: el usuario, o quien tenga SAS, ejecuta uno o dos de los programas del corpus
(L4 y L8) con datos pequeños y entrega la salida real. Con eso se comprueba que el oráculo no tiene un
malentendido compartido. También sigue en manos del equipo: D2, NEQUI, tolerancia de conciliación, rutas
y tablas reales, y el significado de los códigos de tipo de documento. El corpus mide y reduce el riesgo,
no lo elimina.

## 9. Camino hacia la meta, por hitos

| Hito | Contenido | Resultado medible |
|---|---|---|
| M1 | Formato de caso, ejecutor y oráculo A con L0 a L3 | 57 casos verificados de punta a punta |
| M2 | Vectores de semántica (B) y L4 a L6; validador de Studio automático (T01) | 44 casos más; informe de cobertura |
| M3 | `job_producto` con validaciones guiadas por el corpus (L7 y L8) | La etapa de documento, ubicación y cuenta pasa con datos simulados |
| M4 | Totales, conciliación, joblets y secciones restantes del documento de diseño | La conformidad contra las filas del manual sube de 42 a más de 100 de 168 |
| M5 | Programa grande completo (L9) y corrida real de comparación | Informe de equivalencia con las diferencias explicadas |

Estas cifras son metas de trabajo, no resultados. El hito M4 es el que más acerca la salida al diseño
manual; M1 a M3 son lo que lo hace creíble.

## 10. Tareas de este plan (para agentes)

Numeradas K para no chocar con las T de `tareas-agente.md`. Se pueden ejecutar en paralelo salvo donde se
indique.

- **K01 [H]** Formato de caso, `tools/corpus.py` (modos `oraculo` e `informe`) y pruebas del ejecutor.
- **K02 [H]** Oráculo A: traductor de `PROC SQL` a SQLite (diferencias: `IS MISSING`, `^=`, `||`, `CASE`,
  funciones, orden de nulos), con una tabla de diferencias documentada.
- **K03 [H]** Casos L0 y L1 (30) con entradas generadas por script y esperado por oráculo o dorado.
- **K04 [H]** Casos L2 y L3 (27), incluidos el patrón de validación con lookup y los totales.
- **K05 [H]** Clasificar los 172 programas existentes por nivel y por construcciones; tabla en
  `tests/corpus/inventario.md`.
- **K06 [R+H]** Vectores de semántica (capa B) con fuente citada: `input`, `left`, `compress`, `put`,
  `substr`, `scan`, comparación con faltantes, redondeo, fechas. Implementación de referencia en Python.
- **K07 [H]** Casos L4 a L6 apoyados en K06.
- **K08 [H]** Datos de entrada simulados con distribuciones realistas pero ficticias para el programa
  grande: CSV de producto con 23 columnas, Excel de homologación, país, DANE y fecha (extender
  `tools/simular_*.py`, con reglas de coherencia entre archivos: los códigos válidos del Excel aparecen en
  los datos).
- **K09 [D+H]** Rebanadas L8 del programa grande: recortar etapas (documento, ubicación, cuenta, duplicados,
  totales) en programas independientes ejecutables por el oráculo. Depende de K02, K06 y K08.
- **K10 [H]** Contenedor de pruebas (si el usuario enciende Docker): PostgreSQL y Hive con scripts de
  arranque y carga desde `entradas/`, y un caso de lectura y escritura con `tDBInput` y `tDBOutput`.
- **K11 [H]** Integración con el validador de Studio (T01): modo `validar` del ejecutor y reporte de
  diferencias fila por fila.
- **K12 [H]** Informe de cobertura: construcciones SAS traducidas y verificadas sobre el total del corpus.

Orden: K01, K02 y K06 primero (en paralelo); K03, K04 y K05 con K01 y K02; K07 después de K06; K08 y K09
después; K10 a K12 cuando existan Jobs que validar. Cada tarea cierra con pruebas, `ruff`, entrada en
`PROGRESS.md` y commit local, como siempre.
