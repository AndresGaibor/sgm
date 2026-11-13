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
