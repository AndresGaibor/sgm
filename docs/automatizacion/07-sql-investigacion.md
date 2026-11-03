# 07. Investigación SQL: sqlglot, dialectos y portabilidad de PROC SQL

Estado: investigación y medición de las tareas 17 a 19. Fecha: 2026-11-03.

## 1. Qué se investigó

### 1.1 sqlglot (README del proyecto)

Fuente: repositorio público `tobymao/sqlglot`, leído el 2026-11-03. La versión instalada en el
proyecto es `sqlglot 30.27.0` (dependencia de `pyproject.toml`).

- Se presenta como "a no-dependency SQL parser, transpiler, optimizer, and engine" y declara más
  de 30 dialectos de origen y destino.
- La tabla de dialectos oficiales incluye **Hive** y **Spark**. No aparece **Impala**.
- Hive es el dialecto más cercano a Impala. La documentación no dice que cubra la sintaxis de
  Impala; esa equivalencia es una inferencia nuestra y debe probarse.
- La API de traducción pide indicar el dialecto de origen y de destino (`transpile(sql, read=..., write=...)`).
  El código del proyecto usa `write="hive"` sin `read`, y el SQL que genera ya está en sintaxis
  de sqlglot. No hay ningún caso de SAS que pase por sqlglot sin pasar antes por nuestro normalizador.
- El parser es deliberadamente permisivo: puede aceptar consultas que un motor real rechazaría.
  El propio proyecto lo dice: "a transpiler, not a validator". Por eso sqlglot no sirve como
  prueba de que una consulta funciona en Impala.
- Algunas traducciones no son posibles entre ciertos pares de dialectos. Por defecto sqlglot avisa
  y hace una traducción de mejor esfuerzo. La opción `unsupported_level` con `RAISE` o `IMMEDIATE`
  convierte el aviso en error. El proyecto no fija esa opción todavía.

Consecuencias para el proyecto:

- El SQL de base se escribe con `write="hive"` y se documenta como "dialecto Hive, equivalente
  a Impala" (ver `src/sgm/passes/db_sql.py` y `src/sgm/ir/sql_render.py`).
- Ninguna función se considera portable por el hecho de que sqlglot la lea. La portabilidad
  viene de `rules/sas/sql-functions.json` (status `portable`), y sqlglot solo sirve para
  localizar las funciones de una expresión.

### 1.2 Impala: WITH y CREATE TABLE AS SELECT

Búsqueda sobre la documentación de Apache Impala y de Cloudera:

- Impala documenta la cláusula `WITH` como una forma de definir subconsultas con nombre que
  existen solo durante la consulta. No admite `WITH` recursivo. Los nombres definidos en `WITH`
  no chocan con tablas reales.
- La referencia de `SELECT` ubica la cláusula `WITH` antes de `SELECT`.
- La referencia de `CREATE TABLE` documenta CTAS con una `select_statement` al final.
- **No se encontró** una página oficial que muestre `CREATE TABLE ... AS WITH ... SELECT`.
  La forma es plausible porque CTAS acepta una `select_statement` y `SELECT` admite `WITH` al
  inicio, pero no está confirmada.

Estado de verificación:

| Afirmación | Estado |
|---|---|
| Impala admite `WITH` en un `SELECT` | Documentado (referencia de Impala) |
| Impala admite `CREATE TABLE ... AS WITH ... SELECT` | **Pendiente**: no documentado; probar en un Impala real |
| `ORDER BY` dentro de un CTE o de una subconsulta sin `LIMIT` | **Pendiente**: el generador lo emite en un CTE; no verificado en Impala |
| Hive acepta `CREATE TABLE ... AS WITH ...` | No verificado en esta sesión; el proyecto no ejecuta Hive |

Nada de esto se puede comprobar desde el SGM: no hay conexión a bases (AGENTS.md). Por eso la
salida de `WITH` se marca como "generada, sin ejecutar" en la guía.

## 2. Qué cambió en el código (tareas 13 a 16)

- Portabilidad: `src/sgm/ir/sql_portability.py` lee `rules/sas/sql-functions.json`. Una función
  solo es portable si su `status` es `portable`. Las palabras clave `CASE`, `AND`, `OR` y `NOT`
  no cuentan como funciones.
- Generador de SQL de base: `src/sgm/passes/db_sql.py` escribe cada cadena con `WITH`
  (`sgm_paso0`, `sgm_paso1`, ...) en lugar de subconsultas anidadas. Antes, una función SAS sin
  equivalente (por ejemplo `cats`, `input`) llegaba a la base, porque el filtro solo comprobaba
  que sqlglot pudiera leer la expresión. Ahora esa cadena se queda en flujo.
- Reglas: `rules/sas/sql-semantica.yaml` define dos reglas. `src/sgm/ir/sql_semantics.py` las
  carga y valida. El lowering de PROC SQL y el generador de SQL las consultan.
  - `agregado-sin-group-by`: tratamiento `pendiente`.
  - `select-into-macrovariable`: tratamiento `programa_anfitrion`.

## 3. Medición sobre el fixture grande

Comando reproducible (no escribe archivos):

```
uv run python tools/medir_sql_portable.py tests/fixtures/sas/client/client_large.sas
```

Resultado medido el 2026-11-03 con el código de esta rama:

| Clase | Sentencias |
|---|---:|
| Total de sentencias de PROC SQL | 463 |
| Portable (se puede escribir en `WITH` de base) | 231 |
| No es consulta (pass-through, EXECUTE, CONNECT, INSERT, DELETE, DROP) | 118 |
| No se puede analizar con sqlglot (`parse_error`) | 86 |
| `SELECT ... INTO :macro` (va al programa anfitrión) | 22 |
| Con referencias a macro variables | 4 |
| Con función no portable (`compress` 2, `put` 2) | 2 |
| Agregado sin GROUP BY (pendiente) | 0 |

Del total, **231 de 463 (49,9 %)** son portables. Si solo se cuentan las consultas (sin pass-through
ni sentencias de otro tipo), son 231 de 345 (67,0 %).

Notas sobre la medición:

- La clasificación usa las mismas reglas del código; no es una estimación.
- "Portable" significa que la sentencia puede escribirse como SQL de base. No significa que el
  programa completo se ejecute en la base: el resto del flujo (cargas, macros, uniones) sigue igual.
- Las 86 sentencias con `parse_error` son la mayor fuente de pérdida. Son un trabajo pendiente
  de análisis, no un fallo de la medición: sqlglot no puede leerlas tal como las escribe SAS.
  Antes de decidir cuántas se pueden rescatar hay que clasificar sus causas.
- Los 22 `SELECT ... INTO` no se cuentan como SQL: su valor se asigna en el programa anfitrión.

## 4. Pendiente

- Probar en Impala real: `CREATE TABLE ... AS WITH ... SELECT` y `ORDER BY` dentro de un CTE.
- Clasificar las 86 sentencias con `parse_error` por causa (por ejemplo `OUTER UNION CORR`, `CASE`
  con formas que sqlglot no acepta).
- Decidir el tratamiento de `into :a - :b` (rango de variables): hoy no se reconoce y la
  sentencia queda como error de análisis.
- Decidir el tratamiento de `trimmed`: hoy se quita en el normalizador sin dejar nota. Solo
  afecta a los espacios de columnas de texto.
- Revisar el alias de agregados sin `AS`: `count(*)` sin alias produce `COUNT(*) AS COUNT(*)` en
  la base. Según la lectura del código (no comprobado con una prueba), la fusión falla al
  transpilar y la cadena no se funde. Es un defecto previo que no se corrigió en esta tarea.
