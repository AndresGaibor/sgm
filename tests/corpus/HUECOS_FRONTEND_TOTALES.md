# Huecos del frontend hallados con los casos L8 de totales

Hallazgos de `tests/corpus/L8/totales/` (agente de totales). Cada hueco es una construcción SAS
válida que `sgm` no entiende. Ninguno se corrigió: el frontend no se tocó.

Verificación: `sgm proceso` termina sin excepción en los 8 programas y `build_flows` los recorre.
Los huecos salen en el modelo de flujo como `NO ENTIENDE` y `PEND` en la línea indicada.

## 05_conciliacion/programa.sas, línea 160

- Construcción: `%IF &estado. = CONCILIA %THEN %DO;` dentro de `%MACRO mensaje_final(producto=, estado=)`.
- Qué pasó: el modelo lo marca como "Macro dinámica: condición no constante: &estado. = CONCILIA"
  (dos entradas, una por cada llamada a la macro). Es una condición sobre un parámetro de macro,
  que es válida en SAS y se resuelve al llamar la macro.
- Efecto: el paso queda como `unparsed` en vez de como condición resuelta. No altera el flujo de datos.

## 06_periodo_fecha/programa.sas, línea 118

- Construcción: `%IF %LENGTH(&mes.) = 2 %THEN %DO;` dentro de `%MACRO valida_periodo(mes=, anio=)`.
- Qué pasó: "Macro dinámica: condición no constante: %length(&mes.) = 2". La función `%LENGTH`
  con parámetro de macro no se reconoce como condición constante.
- Efecto: igual que el anterior; sin efecto sobre las tablas.

## 07_impala_lectura/programa.sas, línea 108

- Construcción: `%IF %LENGTH(&dia.) = 10 %THEN %DO;` dentro de `%MACRO valida_maxdia(anio=, mes=, dia=)`.
- Qué pasó: "Macro dinámica: condición no constante: %length(&dia.) = 10".
- Efecto: igual que el anterior.

## Construcciones que sí se entendieron (para no repetirlas)

- `PROC IMPORT DBMS=DLM` con `GETNAMES=NO` y `PROC SQL` que renombra `VAR1..VAR23`.
- `PROC IMPORT DBMS=EXCELCS` (Validacion_fecha.xlsx).
- `PROC SORT ... NODUPKEY`, `PROC SORT ... NODUPREC` con `BY _ALL_`.
- `PROC SQL` con `GROUP BY ... HAVING`, `OUTER UNION CORR`, `LEFT JOIN ... IS MISSING`,
  subconsultas escalares y `SELECT ... INTO :macro`.
- `PROC EXPORT DBMS=CSV` con `OUTFILE` literal y con macro en el nombre.
- `connect to IMPALA (DSN = IMPALAP)`, `create table ... as select * from connection to IMPALA (...)`.
- `%MACRO procesa_producto(prod=, suf=)` con `PROC IMPORT` y `PROC EXPORT` dentro, y `&&ESTADO_&prod..`.
- `PROC DATASETS ... DELETE`, `PROC DELETE DATA=`.
