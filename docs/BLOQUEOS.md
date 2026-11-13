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
- **Hecho en 248m (B-13, parte):** el intérprete se detiene ante sentencias sin traducción y asignaciones condicionales sin partes (`lrcon`, p. 500). Hecho en 249m: la suma (intérprete y hueco `P-SUMA-SIN-EMISOR`). `RETAIN` con valor y sin BY queda en 250m (estado por grupo, hueco `P-POR-GRUPO-SIN-EMISOR`). Hecho en 251m: `LAG` y `DIF` en el intérprete (`lefunctionsref`, pp. 1163–1164 y 663); su emisión necesita Studio.
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

## Bloqueo 252m: memoria libre por debajo de 4 GB (ralph-loop, B-19)

- **Qué pasó:** al cerrar B-19 (`UPDATE` en el intérprete, hueco sin emisor, casos l6_35 a l6_38) la memoria libre
  era de 2,77 GB (`Get-CimInstance Win32_OperatingSystem`, `FreePhysicalMemory`). El bucle exige 4 GB antes de
  `tools/ci.py`, así que no se corrió el gate y no hay commit de 252m.
- **Estado en disco, sin commit:** `src/sgm/migrar/interprete_update.py` (nuevo), `src/sgm/ir/lower_data_update.py`
  (nuevo), `tests/unit/test_interprete_update.py` (nuevo, 9 tests), casos `tests/corpus/L6/l6_35` a `l6_38` (pendientes,
  sin `esperado/`), `src/sgm/frontend/datastep.py` (`update` y `modify`), `src/sgm/ir/lower_data.py` y
  `lower_data_recorrido.py` y `lower_data_grupos.py` (cabeceras), `src/sgm/migrar/interprete_pasos.py` (una rama de
  despacho y el import), y ajustes de tests: `test_ir_rules.py` (LAG es hueco), `test_interprete_sin_traducir.py` (se
  quitó el caso LAG en IF, cubierto en `test_interprete_lag.py`), `test_catalogo_sas.py` (`update`/`modify` son
  sentencias propias con hueco), `test_tablero.py` (254 casos, L6 144), `migrar_pendientes.yaml`.
- **Por revisar al commitear:** `interprete_pasos.py` figura como de Byron en `reparto-andres-byron.md`; se tocó solo
  para el despacho del `join` con `modo="update"`. `lower_data.py` queda en 304 líneas (sobre el límite de 300).
- **Qué falta:** `tools/ci.py` con memoria libre (o por tandas), y el commit `hito 252m: ...` con la nota anterior.
  Emisión de `UPDATE` en `desde_plan_merge.py` (tJavaRow) y validación en Studio: pendientes hasta que el puente
  responda. `operadores.combinar` con `modo="update"` no se añadió: el hueco se construye con `b.op`.
- **Segunda comprobación (iteración siguiente del bucle):** memoria libre 2,76 GB. Los mayores consumidores son
  procesos de Chrome y de Claude (no hay ejecuciones de `tools/ci.py` ni de pytest del repo). No se cerraron
  procesos ajenos. Sin commit de 252m hasta que haya 4 GB libres.
- **Tercera comprobación (tras reiniciar):** memoria libre 1,07 GB de 13,35 GB. Consumen Chrome (6,6 GB) y
  Talend Studio (1,97 GB, abierto por el usuario, no por este bucle). No se corrió `tools/ci.py` ni se commiteó.
- **Cambios hechos sin gate:** `lower_data.py` pasó de 304 a 277 líneas: `_join_type` (MERGE) se movió a
  `src/sgm/ir/lower_data_union.py` como `tipo_de_union`, sin cambio de lógica; `import re` huérfano quitado.
  El despacho de `UPDATE` sigue en `lower_data_update.py`. Finales de línea restaurados con
  `.cache/restaura_eol.py` en `datastep.py` e `interprete_pasos.py` (sin churn: diff igual con y sin ignorar CR).
  `interprete_pasos.py` (Byron): el diff contra HEAD son solo el import de `_actualizar` y la rama `elif` del
  despacho de `UPDATE` (8 líneas).
- **Prueba dirigida (un proceso):** `test_interprete_update.py` y `test_interprete_lag.py`, 16 pasan. Ruff limpio.

- **Resuelto en 253m (B-9):** `tUnite` con conexiones `MERGE` compila y conserva el orden de SAS
  (`l6_25_set_dos_datasets_orden` coincide en Studio, 0 diferencias; testigo `l6_09` también coincide). Decisión (a).
  Queda B-10 para `l6_26` (columnas distintas, `P-UNION-ESQUEMAS-DISTINTOS`).

- **B-10 (254m, parcial):** `l6_26` coincide en Studio. Quedan (c), `SET a b; BY k;` intercalado con su pendiente
  `P-SET-INTERCALADO` (no verificado) y las entradas repartidas por `tReplicate` con alineación, que caen al camino anterior.

## B-12: `MERGE` muchos-a-muchos no cabe en un solo `tJavaRow` (decisión del dueño, diseño del plan)

- **Qué dice el plan:** `MERGE` de tres o más entradas, o con llave repetida, va como `tUnite` + `tSortRow` por
  `(k, orden de entrada, secuencia)` + un `tJavaRow` con la lógica de `mezclar` (`l6_02`, `l6_03`, `l6_04`, `l6_11`).
- **Por qué no se puede así:** según la referencia de `tJavaRow` (`docs/referencia/talend/tjavarow.md`), el código se
  aplica a cada fila del flujo: entra una fila y sale una. Un `MERGE` muchos-a-muchos puede dar más filas que entradas
  (dos filas `a` por dos filas `b` dan cuatro salidas). Un solo `tJavaRow` no emite varias filas por entrada. Esto es
  un supuesto de la referencia; Studio tiene que confirmarlo antes de cerrar la decisión.
- **Opciones (decide el dueño):**
  - (a) Emitir solo el caso de una fila por llave en cada lado (clave demostrada única con `NODUPKEY` o `PROC SORT`
    previo, `l6_01`) como `tMap` con lookup, y dejar el resto como `P-MERGE-MUCHOS-A-MUCHOS` con motivo.
  - (b) Un `tJavaRow` que acumula cada grupo y escribe el resultado en un archivo intermedio, y un segundo Job que lo
    lee. Más piezas, y el Job ya no es un solo flujo.
  - (c) Un `tJava` que lee las entradas ordenadas y produce la salida con código Java completo, sin flujo de filas.
- **Recomendación:** (a) para la fase actual, y que `l6_02` a `l6_04` y `l6_11` queden pendientes con `P-MERGE-MUCHOS-A-MUCHOS`.
  Así no se inventa un componente que no existe.
- **Lo que no bloquea:** B-14 (estado por fila, un valor por fila), y la emisión de LAG/DIF, CALL SYMPUT y DO WHILE,
  que también son una fila de salida por fila de entrada. Siguen en esta fase.

## B-14: `LAST.` necesita ver la fila siguiente (misma restricción que B-12)

- `RETAIN`, la sentencia suma, `LAG`/`DIF` y `FIRST.` (con el reinicio de acumulado) dependen solo de la fila actual y de
  su estado anterior: se emiten como `tSortRow` + `tJavaRow` con variables de clase, una fila de salida por fila de entrada.
- `LAST.v` vale 1 en la última fila de cada grupo, y para saberlo hace falta la fila siguiente. Un `tJavaRow` solo ve la
  fila actual. Opciones: un `tJavaRow` con retardo de una fila (emite la fila anterior al llegar la siguiente, y la
  última en `tJavaFlex` final, que no se ha verificado), o un `tAggregateRow` que calcule el último por grupo y una unión
  posterior. Decisión del dueño, junto con la de B-12.
- Casos afectados: `l6_07` (LAST. con acumulado) y `l6_29` (LAST. con dos variables BY). `l6_05` ya usa `tUniqRow` y no
  depende de esto.

## B-Studio (255m): Studio con diálogo modal abierto (`MODAL_BLOCKING`)

- **Qué pasó:** al validar `l6_41_dif_primer_valor_faltante` (DIF como `tJavaRow`), `sgm studio salud` devolvió
  `MODAL_BLOCKING`: hay un diálogo `Confirm` abierto en Talend Studio. Dos intentos de salud, ambos con el mismo
  resultado. El caso quedó en `out/studio-pendientes.json` (motivo `MODAL_BLOCKING`, `intentos: 1`).
- **Por qué no se reinició:** la guía (docs/guia-validacion-studio.md, sección 7) dice que, con un diálogo modal, no se
  mate el proceso de Studio, porque se pierde el trabajo sin guardar. El reinicio autorizado cubre el caso de bridge
  caído, no este. Tampoco hay acceso a la ventana para cerrar el diálogo con seguridad.
- **Qué hace falta:** que el usuario mire Talend Studio, cierre el diálogo `Confirm` (guardando si lo pide) y avise.
  Después se reintenta `sgm studio salud` y se valida `l6_41`. Su esperado (lefunctionsref p. 663, DIFn(x) = x - LAGn(x), primer valor faltante) es `ID,X,D` con las filas `1,2,` `2,3,1` `3,5,2`; se escribe en `esperado/DIF_L6_41.csv` al validar, no antes (el caso queda pendiente sin esperado).
- **Resultado:** ninguna validación de Studio de esta iteración cuenta. No hay ningún resultado inventado.

## Bloqueo 255m: memoria libre por debajo de 4 GB; hito 255m sin commit

- **Qué pasó:** la comprobación de memoria dio 1,56 GB libres al lanzar `tools/ci.py`. Ese arranque fue un error: se
  inició el gate con la memoria por debajo del mínimo. Se detuvo a los pocos segundos (TaskStop) y se comprobó que no
  quedó ningún proceso de pytest ni de `ci.py`. La memoria después estaba en 2,5 GB.
- **Estado en disco, con staging y sin commit:** LAG y DIF como `tJavaRow` (`java_lag.py`, `desde_plan_lag.py`), el
  cableado en `desde_plan.py`, `tiene_hueco` con `emitidos`, `tJavaRow` en `ENTRADA_PROPIA` y las pruebas nuevas.
  Pruebas verificadas en un solo proceso antes del incidente: `test_java_lag.py` y `test_desde_plan_lag.py`
  (9 pasan) y los tests de LAG, unión, emisor y golden (367 pasan).
- **Qué falta:** correr `tools/ci.py` con 4 GB libres o más (o por tandas) y comitear `hito 255m`. Antes, subir el
  Job de LAG a validar en Studio (`l6_41`, bloqueado por `MODAL_BLOCKING`, ver la sección anterior).
- **Comprobación siguiente (iteración del bucle):** memoria libre 2,41 GB. Por la regla no se corrió la suite, no se
  comprobó Studio y no se commiteó. El hito 255m sigue en staging, sin commit, y el diálogo `Confirm` de Studio también
  sigue pendiente de cierre por el usuario.
- **Comprobación del bucle:** memoria libre 2,48 GB (< 4 GB). Sin suite, sin commit, sin consulta a Studio. Hito 255m en staging.

## B-Studio (iteración con puente caído): recuperación en dos intentos, sin READY

- **Qué se vio:** `sgm studio salud` dio `BRIDGE_DEAD` (`BRIDGE_UNAVAILABLE`). Talend Studio no estaba en ejecución: se
  había cerrado. `talend-mcp` (3927) sí respondía a `healthz`.
- **Intento 1:** se lanzó Talend Studio con el workspace de PRJ_BANCOLOMBIA. El puente 3930 no empezó a escuchar en 8 min.
- **Intento 2:** se cerró solo el proceso de Studio lanzado en este intento (PID 25916) y se relanzó. El puente 3930 escucha
  ahora, pero `sgm studio salud` da `timed out` al contactar al MCP (3927), y `healthz` responde. La guía (sección 7) apunta
  a un diálogo modal abierto o a una compilación en curso. No hay acceso a la ventana.
- **Límite:** se agotaron los dos intentos de esta iteración. No se reinició de nuevo ni se cerraron procesos ajenos.
  Ninguna validación de Studio de esta iteración cuenta. Nada se marcó como validado.
- **Siguiente paso (la persona usuaria):** mirar la ventana de Talend Studio, cerrar cualquier diálogo (`Confirm` u otro) y
  avisar. Después, en la siguiente iteración, reiniciar solo `talend-mcp` (3927) y comprobar `sgm studio salud`. Ese reinicio
  cuenta como un intento de recuperación.
- **Lo que sigue bloqueado por Studio:** validar `l6_41` y `l6_40` (255m); B-9 ya está validado; B-10 validado en 254m.
  El commit de 255m necesita gate (4 GB libres) y no depende de Studio.
- **Comprobación del bucle:** memoria libre 1,63 GB (< 4 GB). Sin suite, sin commit, sin intento de Studio. Hito 255m en staging.
- **Comprobación del bucle:** memoria libre 1,7 GB (< 4 GB). Sin suite, sin commit, sin intento de Studio. Hito 255m en staging.
- **Comprobación del bucle:** memoria libre 1,7 GB (< 4 GB), sin cambio desde la anterior. Sin suite, sin commit, sin intento de Studio.

## Studio sin puente tras 255m (dos intentos de recuperación agotados)

- **Qué se vio:** `sgm studio salud` → `BRIDGE_UNAVAILABLE` (`BRIDGE_DEAD`). Talend Studio se había cerrado.
  `talend-mcp` (3927) respondía a `healthz` (263 herramientas).
- **Intento 1:** se lanzó Talend Studio con el workspace de PRJ_BANCOLOMBIA. El puente 3930 no escuchó en 8 min.
- **Intento 2:** se intentó cerrar el proceso lanzado en el intento 1 (PID 19632) y relanzar Studio. `taskkill` no lo
  cerró: quedan **dos instancias de Talend Studio** en ejecución (PID 19632 y la del segundo arranque). Ninguna expone el
  puente 3930 hasta ahora. La guía (sección 7) apunta a un diálogo modal o a una compilación en curso, que no puedo ver.
- **Límite:** agotados los dos intentos de esta iteración. Sin resultados de Studio. `l6_40` y `l6_41` siguen sin
  validar; `out/studio-pendientes.json` lo registra como pendiente.
- **Qué hace falta:** que la persona usuaria cierre las ventanas de Talend Studio (las dos instancias), guarde si lo pide,
  y avise. Después se arranca Studio una sola vez, se espera el puerto 3930 y se reinicia `talend-mcp` (3927).
- **Iteración posterior:** `sgm studio salud --recuperar` (un intento) sigue en `MODAL_BLOCKING` con el diálogo `Confirm`. El puerto 3930 ya escucha (una sola instancia de Studio, PID 19632). No se reinició Studio: la guía (sección 7) prohíbe matar un proceso con diálogo modal, por el trabajo sin guardar. Hace falta que cierres el diálogo `Confirm` en Talend Studio y avises.

## Decisiones tomadas por el agente (256m), a revisar por el dueño

- **B-12, `MERGE` muchos-a-muchos: opción (a).** Solo se emite el `MERGE` con llave única demostrada (ver la tarea
  B-12 del plan). Todo lo demás queda como pendiente de unión (`P-UNION-TIPO-SIN-SOPORTE`, ya en el código). No hay
  cambio de código: el `MERGE` con `IF` ya queda pendiente y no sale como `tMap`.
- **B-14, `LAST.`: queda como pendiente sin emisor (`P-POR-GRUPO-SIN-EMISOR`).** Un `tAggregateRow` para el último por
  grupo requiere un diseño que no he verificado, así que no lo invento. `RETAIN`, la suma, `LAG`/`DIF` y `FIRST.` se
  emiten donde ya se emiten; el resto sigue como está.
- Estas decisiones no necesitan Studio. Se validarán cuando Studio esté disponible.
