# MG-P10-01: columnas exactas en el anillo B — plan de implementación

> **Para agentes de implementación:** SUBHABILIDAD OBLIGATORIA: usar `superpowers:executing-plans` para implementar este plan tarea por tarea. Los pasos usan casillas (`- [ ]`) para seguir el avance.

**Objetivo:** hacer que la verificación B detecte diferencias en el esquema de columnas de cada fila producida frente a `esperado/`.

**Arquitectura:** `tests/unit/test_migrar_corpus_anillo_b.py` valida las claves de las filas reales antes de construir la tabla que compara los valores. La comparación de valores existente sigue a cargo de `comparar_con_guardado`.

**Tecnologías:** Python 3, pytest y Ruff; sin dependencias nuevas.

**Diseño:** `docs/superpowers/specs/2026-11-09-mg-p10-01-anillo-b-columnas-design.md`

## Restricciones globales

- No inventar equivalencias SAS: los valores de `esperado/` permanecen sin cambios.
- No borrar ni debilitar pruebas existentes ni modificar los `xfail`.
- Mantener código e identificadores en inglés; documentación y mensajes en español.
- Cerrar el hito solo con `uv run python -m pytest -q` y `uv run ruff check .` en verde.
- Registrar hito 126 en `PROGRESS.md` y hacer un commit local `hito 126: <resumen>`; no hacer push.

## Revisión prioritaria

1. Una columna extra en cualquier fila, incluida una fila posterior, debe ser reportada; se fija con `test_anillo_b_detecta_columnas_extra_en_cualquier_fila`, que además verifica nombres con distinto uso de mayúsculas.
2. Una columna esperada ausente debe reportarse incluso cuando su valor esperado está vacío; se fija con `test_anillo_b_detecta_columna_esperada_ausente_con_valor_vacio`.
3. Cero filas no revela las columnas del resultado; la verificación no debe inventar un esquema ni generar una diferencia estructural; se fija con `test_anillo_b_no_infiere_esquema_de_salida_vacia`.
4. La corrección debe quedar dentro del arnés B y conservar la validación previa de valores del comparador; lo verifica la suite del anillo B y la suite completa.

---

### Tarea 1: comparar el esquema observable de cada fila del anillo B

**Archivos:**
- Modificar: `tests/unit/test_migrar_corpus_anillo_b.py`
- Modificar: `docs/plan-reescritura/plan-migrador-general.md`
- Modificar: `PROGRESS.md`

**Interfaces:**
- Consume: `_esperado(caso, tabla, filas) -> list[str]` y el encabezado de `esperado/<tabla>.csv`.
- Produce: diferencias estructurales legibles para columnas extra o ausentes; las compara sin distinguir mayúsculas.

- [x] **Paso 1: escribir pruebas de regresión.** Se agregaron tres pruebas para columna extra en una fila posterior (con distinto uso de mayúsculas), columna esperada ausente con celda vacía y salida sin filas.
- [x] **Paso 2: confirmar RED.** La suite focal mostró los dos fallos esperados: la columna adicional y la ausente pasaban inadvertidas. La suite completa tuvo únicamente esos dos fallos: 2602 pasaron, 26 se omitieron y 144 quedaron `xfail`.
- [x] **Paso 3: implementar la verificación mínima.** `_esperado` compara el conjunto normalizado de columnas de cada fila con el encabezado esperado y luego conserva la comparación de valores existente. Una salida vacía no permite inferir esquema.
- [x] **Paso 4: confirmar GREEN.** `uv run python -m pytest -n 0 tests/unit/test_migrar_corpus_anillo_b.py -q`: 59 pasaron y 6 quedaron `xfail`, incluidas las tres regresiones nuevas.
- [x] **Paso 5: actualizar estado y métricas.** MG-P10-01 sigue parcial; el anillo B queda en 56/62 casos, y el crédito P10 y global no cambia. La limitación de salidas vacías queda explícita.
- [x] **Paso 6: verificar cierre.** `uv run python -m pytest -q`: 2604 pasaron, 26 se omitieron y 144 quedaron `xfail`; `uv run ruff check .`: limpio.
- [x] **Paso 7: commit local.** Se creó el commit local `hito 126: validar columnas del anillo B`; sin push.

## Autorrevisión

- Cobertura: el contrato nuevo se fija con tres pruebas y los resultados previos siguen en manos del comparador actual.
- Límites: los nombres se comparan sin distinguir mayúsculas; no se usa tipo ni contenido de valores para adivinar esquema.
- Salidas vacías: el intérprete devuelve filas como diccionarios, sin metadatos cuando no hay filas; no se declara validada esa parte del esquema.
- Alcance: no se modifica el comparador compartido ni se afirma que MG-P10-01 o MG-P10 estén completos.
