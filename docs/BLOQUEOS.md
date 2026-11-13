# Bloqueos del carril m (Andres)

Tareas del plan `docs/superpowers/plans/2026-11-11-ruta-al-100.md` (sección 8.3) que no se intentan
porque necesitan Studio, una decisión del dueño o algo de Byron. Cada entrada dice qué falta y qué
desbloquea. Se quita la entrada cuando la tarea se cierra.

## Decisiones tomadas (13 de noviembre de 2026)

Las decisiones del dueño que cierran entradas de este archivo. Cada entrada afectada lleva una línea «Decidido».

1. **`interprete.py` se parte sin cambiar comportamiento**, con la suite como red. El defecto de mayúsculas `Z`/`z` va en
   un commit aparte. Primer corte hecho en 241m (`interprete_valores.py`).
2. **FREQ y MEANS pasan a pendiente** hasta tener página verificada en `proc.INDEX.md`. Sin equivalencia no se emite.
3. **`--escribir` añade un caso por clase de equivalencia y los de coincidencia estructural**, no los 386 combinaciones.
4. **`CALL SYMPUT` se emite como `tJavaRow`** (sobre `globalMap`), y deja de ser fontanería en `plumbing.yaml`.
5. **Un pendiente de escritura impide emitir el Job.** Se actualizan los tests que fijaban lo contrario.
6. **`rc` de `FIND` solo se traduce en comparaciones con 0.** El resto queda pendiente. Las llaves duplicadas siguen
   `lrcon` p. 632: se queda la primera observación.

## B-7: `l2_16_sql_en_misma_base` (plan de SQL, MG-P1-04)

- **Tarea:** B-7, paso 3 (`l2_16`: cerrar el `read` con `sql` literal).
- **Estado:** la prueba `tests/unit/test_pendientes_sql_l1_l2.py` pasa (ningún defecto en L1 y L2).
  `l2_12` ya no tiene pendiente. `l2_16` sigue en `migrar_pendientes.yaml` con 4 pendientes
  `P-OPERADOR-SIN-SOPORTE`, clasificados como `entorno` en esa prueba.
- **Motivo:** `LIBNAME LZ '/data/lz';` no dice qué motor sirve la biblioteca `LZ`, y
  `env/engines.json` tiene `"libraries": {}`. Sin ese dato el `read` de `LZ.origen` no se puede poner en
  `db:impala`, y cerrarlo con `sql` literal sería inventar el motor (regla 6 de `AGENTS.md`).
- **Decisión que falta (dueño):** ¿`LZ` es una biblioteca de Impala? Si sí, declararla en
  `env/engines.json` (`libraries`) con el motor que corresponda; si no, el caso se queda como `entorno`
  y el plan debe decir que `l2_16` no es parte del 100 %.
- **Lo que se hace al tener la decisión:** declarar el motor, quitar la entrada de `CLASIFICACION`,
  ajustar `lower_sql_flow.py` para que el `read` salga como pass-through con `sql` literal, y quitar
  `l2_16` de `migrar_pendientes.yaml` si la prueba lo exige.

## B-8: `PROC FREQ` y `PROC MEANS` sin página verificada (MG-P1-06)
- **Decidido (13 nov, punto 2):** FREQ y MEANS pasan a pendiente hasta tener página verificada.

- **Tarea:** B-8, paso 1 (c) (`PROC FREQ` simple → `agregar` con `count` y `percent`) y la parte de `MEANS`
  del paso 3.
- **Motivo:** `FREQ Procedure` no aparece en `docs/referencia/sas/proc.INDEX.md` (la guía indexada solo
  trae la sentencia `FREQ` de otros procedimientos). Sin página no hay equivalencia (regla 6 y el
  `AGENTS.md`). Además `rules/sas/procs/proc-freq.yaml` y `proc-means.yaml` dicen `status: soportado` y emiten
  un `aggregate` **sin** `aggregations`, que no cumple `operadores.agregar`: es una forma anterior.
- **Decisión que falta (dueño):** (a) aceptar otra fuente para FREQ y MEANS (y decir cuál), o (b) pasar las dos
  reglas a `no_verificada`/pendiente con motivo hasta que el docset esté. Con (a) se implementa `count` y
  `percent` como `aggregate` más un `derive` (el porcentaje necesita el total); con (b) quedan como `hueco`.
- **Lo que ya está hecho en B-8:** `PROC APPEND` ya se traduce como `union` con `sources` [base, data] (regla
  `rules/sas/procs/proc-append.yaml`, página 161 verificada). `PROC TRANSPOSE` queda como `pivot` hueco con
  `P-OPERADOR-PIVOTAR` (página 2745).

## B-9: `SET a b;` en Studio (MG-P4-03, parte 1) y lo que depende de su decisión

- **Tarea:** B-9 (investigación de `tUnite` con dos conexiones `MERGE` en Studio). Necesita Studio abierto y
  `sgm studio salud` en `READY`. No se intenta en esta sesión.
- **Bloquea:** B-10 (`SET` que concatena por nombre: su paso 3 depende de la opción a, b o c de B-9).
- **Desbloqueo:** Studio disponible para `tools/validar_caso_studio.py l6_25_set_dos_datasets_orden
  l6_09_nodup_registros_identicos`. Si el orden de `tUnite` no coincide con SAS, la decisión (a/b/c) la toma el
  dueño antes de B-10.

## B-11 a B-14 y B-19: intérprete de referencia (`src/sgm/migrar/interprete.py`) con dueño sin decidir
- **Decidido (13 nov, punto 1):** `interprete.py` partido sin cambio de comportamiento. Hecho en 241m y 242m: todos los módulos quedan bajo 300 líneas. Falta solo el defecto `Z`/`z`, en commit aparte.

- **Tareas:** B-11 (`MERGE` con la semántica real en el intérprete), B-12 (emisión de `MERGE`), B-13 (estado
  por fila en el intérprete), B-14 (estado por fila emitido), B-19 (`UPDATE` y `MODIFY`).
- **Motivo:** `interprete.py` tiene 1 103 líneas, la tabla de zonas de `reparto-andres-byron.md` lo asigna a
  Byron, y el plan B lo cambia en casi todas sus tareas. El punto 1 de la sección 8.3 del plan de ruta al 100 %
  pide una decisión: (a) Andres lo toca y Byron revisa cada cambio, (b) el plan B pasa a Byron, (c) se parte
  el archivo antes de que ninguno lo toque. El plan recomienda (c).
- **Decisión que falta (dueño):** elegir a, b o c. Con (c) la separación sin cambio de comportamiento es un
  paso propio, y se puede hacer sin Byron; con (a) o (b) hay que coordinar con Byron.
- **Hecho en 247m (intérprete, B-11):** `IN=` por iteración (`lrcon`, p. 75) y rechazo de entrada desordenada (`lrcon`, p. 584). Lo que queda, B-12 y B-13/B-14, necesita Studio.
- **Hecho en 248m (B-13, parte):** el intérprete se detiene ante sentencias sin traducción y asignaciones condicionales sin partes (`lrcon`, p. 500). Hecho en 249m: la suma (intérprete y hueco `P-SUMA-SIN-EMISOR`). Quedan `RETAIN` con valor, `LAG` y `DIF`; la emisión de la suma necesita Studio.
- **Bloquea también:** B-18 (lote de Studio de `OUTPUT`, depende de B-17 y de Studio) y B-Gate (Studio y lote C).

## B-17: captura del PDV entre dos OUTPUT y `--escribir` (dueño e `interprete.py`)
- **Decidido (13 nov, punto 3):** `--escribir` añade un caso por clase de equivalencia y los de coincidencia estructural, no los 386.

- **Tarea:** B-17, paso 1 (patrón de captura PDV) y paso 4 (`--escribir N`, casos en `tests/corpus/L6/`).
- **Motivo (captura) — resuelto en 243m para el intérprete:** el intérprete trataba `VALOR` y `valor` como dos columnas (ver el punto siguiente). SAS no
  distingue mayúsculas en nombres de variables; con `OUTPUT S1; VALOR = VALOR + 10; OUTPUT S2;` el dataset `S2`
  queda con dos columnas de valor y la comparación con el oráculo falla. La corrección está en `interprete.py`
  (1 103 líneas, zona de Byron, con la decisión (a/b/c) pendiente, ver B-11 a B-14 y B-19). El traductor
  (`talend_item`) no se puede validar sin Studio.
- **Decidido y hecho en 245m (punto 3):** `--escribir` escribe un caso por clase de equivalencia (108), no los 386.
- **Motivo (`--escribir`, antes de la decisión):** de las 386 combinaciones positivas, las 386 migran sin pendiente (hito 240m). Escribirlas
  todas en `tests/corpus/L6/` añadiría 386 casos y cambiaría los conteos del tablero y del corpus (139 casos hoy). Cuántas
  entran (todas, o un subconjunto con las que cubren `l6_13` a `l6_24`) es una decisión del dueño.
- **Decisiones que faltan (dueño):** (1) la de `interprete.py` (B-11 a B-14, B-19); (2) cuántas combinaciones
  de `OUTPUT` entran al corpus L6.
- **Desbloqueo:** esas dos decisiones. La captura además necesita Studio para validarse en B-18.
- **Mismo defecto, otro caso (resuelto en 243m):** el intérprete escribía una columna nueva al asignar con otra mayúscula
  (`Z` contra `z`). Corregido en `interprete_filas.py` (`lrcon`, p. 49). La captura del PDV ya no depende de esto; queda su
  validación en Studio (B-18).

## B-18 y B-Gate: Studio

- **Tareas:** B-18 (validación en lote de las combinaciones de `OUTPUT` en Studio), B-Gate (compuerta GM1 y L6
  completo en B y en lote C).
- **Motivo:** necesitan `sgm studio salud` en `READY`. Si no conecta, no se reinstala nada (ver
  `docs/guia-validacion-studio.md`, sección 7).
- **Desbloqueo:** Studio arriba; B-18 además necesita B-17 y B-Gate necesita B-11 a B-14.

## B-20: `_N_` como contador y emisión de `CALL SYMPUT` (MG-P4-08)

- **Tarea:** B-20, paso 3 (`_N_` como `Numeric.sequence` o contador antes del `tFilterRow`) y el paso 1 (a) del
  intérprete (`_N_` bajo `IF x > 0;` con cuatro entradas y dos filtradas da 2 y 4).
- **Motivo:** el contador exige tocar `src/sgm/migrar/interprete.py` (decisión del dueño, ver la entrada de B-11
  a B-14 y B-19), y la emisión en Talend (`tJavaRow` sobre `globalMap`, `tSetGlobalVar`) necesita Studio para
  validarse.
- **Hecho en 244m (intérprete):** `_N_` cuenta iteraciones y no filas escritas (`lrcon`, p. 79). Falta solo la emisión
  en Talend (`tFilterRow` precedido de una secuencia), que necesita Studio para validarse.
- **Lo que ya queda seguro (hito 228m):** `_N_` y `_ERROR_` no se traducen como columnas: salen hueco con su código.
- **Desbloqueo:** decisión sobre `interprete.py` y Studio disponible.

## B-16: bucle `DO WHILE`/`DO UNTIL` en `tJavaRow` (MG-P4-06, parte pendiente)

- **Tarea:** B-16, paso 1 (b) y paso 3 para `DO WHILE`/`UNTIL`: emitir el bucle en `tJavaRow` y, con `OUTPUT`
  dentro del bucle, `P-DO-OUTPUT-EN-BUCLE`.
- **Estado:** el `DO WHILE`/`UNTIL` sale hoy como hueco con `P-DO-WHILE-UNTIL` (caso `l6_33`, pendiente). No se emite
  el bucle.
- **Motivo:** el paso 3 toca `src/sgm/migrar/interprete.py` (1 103 líneas, zona de Byron). La decisión (a, b o c) sobre
  ese archivo está pendiente (ver B-11 a B-14 y B-19). La emisión en `tJavaRow` necesita Studio para validarse.
- **Decisión que falta (dueño):** la de B-11 a B-14 sobre `interprete.py`.
- **Desbloqueo:** esa decisión y Studio en `READY` para validar `l6_30`, `l6_31` y `l6_33` (los tres quedan pendientes con su código).

## B-20 (parte CALL SYMPUT): ¿fontanería o migrar? (decisión del dueño, y Studio)
- **Decidido (13 nov, puntos 4 y 5):** `CALL SYMPUT` se emite como `tJavaRow`; un pendiente de escritura impide emitir el Job.

- **Tarea:** B-20, paso 3 (`CALL SYMPUT` como `tJavaRow` sobre `globalMap` o `tSetGlobalVar`) y la parte
  de `SYMPUTX` que recorta blancos (ya hecha en 237m como motivo de la macro dinámica).
- **Conflicto de diseño:** `rules/sas/plumbing.yaml` clasifica `call symputx` como `variables_control`:
  «no transforma filas», con equivalente «variable de contexto del Job». El plan B-20 dice que se emita como
  `tJavaRow`. Son dos decisiones distintas y el dueño tiene que elegir cuál vale.
- **Hallazgo que hay que decidir:** el expansor de macros saca `CALL SYMPUT(X)` del programa y lo guarda como
  macro dinámica. Esa macro dinámica nunca llega a los pendientes de `sgm migrar`, así que la migración no
  informa que el paso perdió esa sentencia.
- **Otro hallazgo:** un paso que escribe un dataset sin columnas demostradas (`P-ESCRITURA-SIN-COLUMNAS`) sale
  como Job con solo la lectura. Los tests actuales esperan que un pendiente no impida el Job (operador que
  falla, `MERGE` con `IF`), así que cambiarlo es una decisión de diseño. Ver también `tests/unit/test_desde_plan.py`.
- **Decisiones que faltan (dueño):** (1) fontanería o migrar `CALL SYMPUT`; (2) si un pendiente de escritura
  impide emitir el Job.
- **Desbloqueo:** esas decisiones, y Studio en `READY` para validar el `tJavaRow`.

## B-21: el lookup `FIND` con tMap y su valor de `rc` (decisión del dueño)
- **Decidido (13 nov, punto 6):** `rc` de `FIND` solo se traduce en comparaciones con 0; el resto queda pendiente. Llaves duplicadas: se queda la primera (`lrcon` p. 632).

- **Tarea:** B-21, paso (a) (`FIND` como `unir` izquierdo con `rc` como columna) y paso (b) (llave duplicada).
- **Hecho en 238m:** todo objeto hash e iterador es un hueco con su código (`P-HASH-LOOKUP-SIN-SOPORTE`,
  `P-HASH-MUTABLE`, `P-HASH-OUTPUT`, `P-HASH-ITERADOR`). No sale Job con ellos.
- **Motivo:** `lrcon` (p. 633 y 634) solo dice que `FIND` devuelve 0 si encuentra la llave y distinto de 0 si no.
  El valor exacto que devuelve cuando no encuentra no está en la guía. El plan dice `-1`, pero eso sería inventarlo
  (regla 6 de `AGENTS.md`). El tMap que el paso (a) describe necesita ese valor para la columna `rc`.
- **Duplicados (paso b):** `lrcon` p. 632 dice que, al cargar un dataset, por omisión se queda la primera
  observación y las siguientes se ignoran (`DUPLICATE` guarda la última; `MULTIDATA` guarda todas). Eso sí está
  demostrado. Falta el operador que descarte duplicados quedándose con el primero para el lado de la búsqueda.
- **Decisión que falta (dueño):** (1) ¿la columna `rc` se traduce solo cuando el programa compara `rc = 0` o `rc ne 0`
  (sin inventar el valor no encontrado), o no se traduce nunca? (2) ¿el lado de búsqueda se deduplica con el
  primero (regla de `lrcon` p. 632) en un operador nuevo, o el paso queda pendiente?
- **Decidido (13 nov, punto 6) y hecho en 246m:** el `FIND` con `rc` en comparaciones con 0 y `DROP rc` se traduce como
  `unir` izquierdo con la tabla de búsqueda sin llaves repetidas (`lrcon`, p. 632). Falta solo la validación en Studio
  (B-18/B-Gate). El resto de usos de `rc` queda pendiente (`P-HASH-RC-SIN-SOPORTE`).

## B-22: catálogo y plan maestro al día (depende de Studio)

- **Tarea:** B-22, pasos 1 y 2. El paso 2 corrige la tabla 5.2 (`tUnite` con conexiones `MERGE`, según B-9), reemplaza
  la lista de hitos 166 a 190 en MG-P4-02 por la línea de B-18 y pone el estado de MG-P1 y MG-P4 con lo medido en B-1 y
  B-Gate. Todo eso espera resultados de Studio.
- **Motivo:** las frases del plan maestro dependen de B-9, B-18 y B-Gate. El paso 1 (estados del catálogo con su
  página) sí puede hacerse, pero cada estado hay que contrastarlo con la guía antes de cambiarlo, y se hará con el
  resto del cierre.
- **Desbloqueo:** Studio en `READY` y el lote de B-18 y B-Gate ejecutados.
