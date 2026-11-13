# Bloqueos del carril m (Andres)

Tareas del plan `docs/superpowers/plans/2026-11-11-ruta-al-100.md` (sección 8.3) que no se intentan
porque necesitan Studio, una decisión del dueño o algo de Byron. Cada entrada dice qué falta y qué
desbloquea. Se quita la entrada cuando la tarea se cierra.

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

- **Tareas:** B-11 (`MERGE` con la semántica real en el intérprete), B-12 (emisión de `MERGE`), B-13 (estado
  por fila en el intérprete), B-14 (estado por fila emitido), B-19 (`UPDATE` y `MODIFY`).
- **Motivo:** `interprete.py` tiene 1 103 líneas, la tabla de zonas de `reparto-andres-byron.md` lo asigna a
  Byron, y el plan B lo cambia en casi todas sus tareas. El punto 1 de la sección 8.3 del plan de ruta al 100 %
  pide una decisión: (a) Andres lo toca y Byron revisa cada cambio, (b) el plan B pasa a Byron, (c) se parte
  el archivo antes de que ninguno lo toque. El plan recomienda (c).
- **Decisión que falta (dueño):** elegir a, b o c. Con (c) la separación sin cambio de comportamiento es un
  paso propio, y se puede hacer sin Byron; con (a) o (b) hay que coordinar con Byron.
- **Bloquea también:** B-18 (lote de Studio de `OUTPUT`, depende de B-17 y de Studio) y B-Gate (Studio y lote C).

## B-18 y B-Gate: Studio

- **Tareas:** B-18 (validación en lote de las combinaciones de `OUTPUT` en Studio), B-Gate (compuerta GM1 y L6
  completo en B y en lote C).
- **Motivo:** necesitan `sgm studio salud` en `READY`. Si no conecta, no se reinstala nada (ver
  `docs/guia-validacion-studio.md`, sección 7).
- **Desbloqueo:** Studio arriba; B-18 además necesita B-17 y B-Gate necesita B-11 a B-14.
