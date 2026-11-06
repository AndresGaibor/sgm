# MG-03 Expresiones SAS y DATA step básico

> Plan ejecutable: completar una capacidad por vez con pruebas unitarias y del anillo B antes de añadirla al lote C. No se modifica ni se debilita un esperado existente para hacerlo pasar.

**Meta:** ampliar `sgm migrar` desde la rebanada de `PROC SQL` de MG-02 hasta expresiones y un `DATA step` fila a fila. Para cada sentencia se genera código Java únicamente cuando la semántica está respaldada; el resto queda en `pendientes.md` con código estable, línea y motivo.

**Base existente:** el traductor legado está en `src/sgm/expressions/`; la migración ya tiene `migrar/semantica.py`, el intérprete de referencia, el enriquecimiento de esquemas y el emisor de `map` en `talend_item/desde_plan_map.py`. El lowering de DATA step existente está en `ir/lower_data.py`; no crear otra IR ni otro intérprete. Antes de implementar, trazar estas rutas con sus pruebas y conservar la salida actual de MG-02.

**Alcance de este plan:** MG-P3-01 (operadores y semántica de faltantes), el subconjunto inicial de MG-P3-02/03/05 que ejercitan los vectores y casos ya disponibles, y MG-P4-01/02/08: `SET` de una fuente, `KEEP`/`DROP`/`RENAME`, `WHERE`, subsetting `IF`, `IF/THEN/ELSE`, asignaciones y `OUTPUT` condicional/múltiple cuando el modelo y emisor lo permiten. Funciones sin fuente o sin regla completa permanecen pendientes; no se intenta cerrar toda la sección 5.7 en este plan.

**Fuentes funcionales:** `tests/corpus/semantica/vectores.yaml` y los casos L0/L4/L6; documentación SAS indicada en `docs/referencia/catalogo-sas.md` y `docs/referencia/sas/README.md`. Antes de añadir cada función, localizar su guía y página en el `.INDEX.md` y consultar solo la página correspondiente del `.txt`. No inferir semántica desde el resultado del emisor.

## Restricciones globales

- Seguir `AGENTS.md`: nada de datos inventados, nada de nombres de scripts de ejemplo en `src/` o `rules/`, sin acceso a bases, y no modificar el repositorio viejo.
- Pruebas-first: cada tarea empieza con una prueba que falla; A y B en cada cambio. Studio solo en lote C al cerrar el grupo, nunca como sustituto de pruebas rápidas.
- Ejecutar `uv run pytest -q` y `uv run ruff check .` antes del cierre. No borrar pruebas existentes. Mantener los archivos nuevos por debajo de 300 líneas.
- Una expresión no soportada no debe impedir emitir los demás operadores. Código de pendiente estable y evidencia SAS conservados.
- Mantener los nombres públicos y el formato de artefactos de MG-02 salvo necesidad demostrada y prueba de compatibilidad.

## Tarea 1: fijar el contrato semántico de expresiones

**Archivos:** `src/sgm/migrar/semantica.py`, `tests/unit/test_corpus_semantica.py`, `tests/corpus/semantica/vectores.yaml` (solo si falta un vector respaldado por guía).

1. Revisar las reglas ya existentes y escribir pruebas para faltantes numéricos (`.` menor que cualquier número), faltantes de texto equivalentes a blanco/`''`, blancos finales en comparaciones, paréntesis y precedencia lógica/arimética.
2. Para cada expectativa nueva, registrar la página SAS en el vector o comentario de regla. No copiar una implementación Java como oráculo.
3. Correr las pruebas de semántica y confirmar que los casos previos no cambian. Resolver o etiquetar como bloqueo cualquier discrepancia entre guía y esperado antes de continuar.

**Aceptación:** los vectores cubiertos por este tramo se evalúan en Python con resultado determinista; los casos no cubiertos siguen siendo pendientes identificables.

## Tarea 2: traducir operadores y comparaciones a Java

**Archivos:** localizar el traductor usado por `desde_plan_map.py`; modificarlo y sus pruebas unitarias, no el traductor legado sin verificar el call path.

1. Añadir pruebas de traducción para `+ - * /`, comparaciones, `AND`/`OR`/`NOT`, `IN`, `BETWEEN`, concatenación `||` y expresiones entre paréntesis.
2. Exigir que el código Java generado trate nulos según la regla SAS pertinente y no produzca `NullPointerException`; usar literales seguros y escapes probados.
3. Añadir una prueba negativa por forma no soportada: debe producir `P-ASIGNACION-SIN-TRADUCIR` o `P-FILTRO-SIN-TRADUCIR` y preservar texto/línea, no una expresión aproximada.
4. Comprobar cada expresión generada con el validador estructural existente y, si está disponible localmente, `javac` sobre el molde mínimo del proyecto. No invocar Studio por expresión.

**Aceptación:** pruebas de traducción y compilación Java pasan; un operador no soportado se aísla sin impedir los demás.

## Tarea 3: extender funciones SAS con evidencia

**Archivos:** `src/sgm/expressions/` o el traductor del migrador determinado en la Tarea 2; reglas/catálogo SAS solo si el esquema existente lo exige; pruebas de funciones.

1. Inventariar funciones llamadas por expresiones del corpus L0/L4 y vectores ya declarados, evitando duplicar `rules/sas/functions` o tablas existentes.
2. Implementar únicamente el conjunto mínimo que desbloquea esos casos (prioridad: `MISSING`, `COALESCE`, `SUM`, `ABS`, `ROUND`, `LEFT`/`TRIM`/`STRIP`, `UPCASE`, `SUBSTR`, `INPUT`/`PUT` cuando su informat o formato esté catalogado).
3. Por función, añadir valores ordinarios, faltantes y límites relevantes a Python y Java. Citar la guía y página. Si falta evidencia, conservar `Pendiente:` en vez de escoger una equivalencia.
4. Ejecutar los vectores del oráculo contra la traducción Java con el mecanismo de pruebas disponible; nunca comparar el intérprete consigo mismo como única evidencia.

**Aceptación:** cada función incorporada tiene prueba de borde y fuente; la cobertura publicada no incluye como soportada una función que solo haya sido parseada.

## Tarea 4: completar el plan lógico para DATA step básico

**Archivos:** `src/sgm/frontend/datastep.py`, `src/sgm/ir/lower_data.py`, `src/sgm/migrar/esquemas.py` y pruebas localizadas por símbolos antes de editar.

1. Añadir casos pequeños para `SET` de una fuente, `KEEP`, `DROP`, `RENAME`, `WHERE` como opción y sentencia, subsetting `IF`, asignaciones y `IF/THEN/ELSE`.
2. Verificar para cada caso que el plan conserva orden de operadores, tablas de entrada/salida y evidencia de línea. No convertir `MERGE`, `RETAIN`, `FIRST.`/`LAST.`, `LAG`, `ARRAY` ni `DO` en este plan: pertenecen a MG-05 o quedan pendientes.
3. Añadir el mínimo de inferencia de esquema necesario solo cuando el SAS demuestre columna y tipo. La cabecera de un archivo prueba nombres, no necesariamente tipos.
4. Asegurar la propiedad de no pérdida: cada paso queda representado o produce un pendiente con línea; no se permite `visitado` sin traza ni pendiente.

**Aceptación:** pruebas unitarias del frontend y lowering; la propiedad de aceptación de MG-02 sigue verde en los programas del repositorio.

## Tarea 5: emitir `tMap` de DATA step y salidas

**Archivos:** `src/sgm/talend_item/desde_plan_map.py` y módulos auxiliares de `talend_item/`; pruebas de emisor y validador.

1. Traducir asignaciones compatibles a expresiones de salida y filtros a condición de flujo, reutilizando las Tareas 2 y 3.
2. Preservar columnas del `SET` que no se reasignan; aplicar `KEEP`/`DROP`/`RENAME` al esquema de salida en el orden SAS demostrado.
3. Para `IF/THEN/ELSE` y `OUTPUT`, no fabricar ramas parciales: emitirlas solo cuando el plan representa explícitamente condiciones y destinos. Si una rama no se puede representar, generar pendiente para esa sentencia y continuar con operadores independientes.
4. Validar conexiones, nombres únicos, esquemas de entrada/salida y tipos mediante `validar_job`; agregar regresiones específicas para defectos encontrados.

**Aceptación:** Jobs válidos sin errores estructurales; `sgm migrar` conserva la degradación elegante ante cada forma no soportada.

## Tarea 6: integrar el anillo B y fijar regresiones del corpus

**Archivos:** intérprete existente en `src/sgm/migrar/interprete.py`, pruebas de `tests/unit/test_migrar_interprete.py` y `tests/unit/test_migrar_corpus_anillo_b.py`; corpus solo con caso independiente justificable.

1. Ejecutar el plan lógico con las mismas operaciones y semántica ya fijadas en Tareas 1–4; no reutilizar el Java emitido.
2. Convertir `xfail` a prueba normal solo cuando el esperado independiente y la implementación están contrastados. No quitar ni rebajar xfails de casos fuera de alcance; conservar motivo y crear pruebas nuevas si el caso expone una diferencia.
3. Ejecutar los casos candidatos de L0 y L4, registrar traducidos, pendientes y equivalentes, y actualizar únicamente la lista viva si la evidencia cambió.
4. Añadir una prueba de determinismo para que dos migraciones produzcan los mismos bytes.

**Aceptación:** cero regresiones en casos previamente verdes; cada caso recién soportado coincide con `esperado/` en B y todo el resto tiene pendiente explícito.

## Tarea 7: lote C y cierre

1. Ejecutar `uv run pytest -q` y `uv run ruff check .`.
2. Preparar en una sola tanda los Jobs nuevos del plan y compilarlos con `tests/studio/`/backend de lote. Si la comprobación de salud falla, conservar el resultado como bloqueado; no marcar C como pasado ni cambiar la prueba para ocultarlo.
3. Si Studio está disponible, ejecutar con datos los casos representativos que cubran cálculo y filtro, capturar la salida literal y compararla con el esperado independiente.
4. Anexar un hito nuevo a `PROGRESS.md`: alcance, cifras B/C, pruebas, páginas SAS consultadas, decisiones y bloqueos. Actualizar el estado de MG-P3-01, MG-P3-02/03/05 y MG-P4-01/02/08 en el plan maestro. El README de planes solo se marca hecho cuando se cumpla la aceptación realmente comprobada.
5. Commit de cierre: `hito 106m: MG-03 <resumen>` (usar el siguiente número libre si ya existe un hito posterior al iniciar la ejecución).

## Revisión de consistencia

- Este plan no crea un IR paralelo, un traductor adicional desconectado del emisor, ni un oráculo derivado del Java.
- Los `DATA step` con estado o cardinalidad especial (`MERGE`, `RETAIN`, `LAG`, `ARRAY`, bucles) no se declaran soportados por accidente.
- Lote C solo se afirma cuando la salud y la corrida real lo permiten; el anillo A/B se informa por separado.
