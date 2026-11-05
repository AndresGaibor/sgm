# Métricas base

Instantánea de la línea base para el nivel N1, tomada el 4 de noviembre de 2026 con el repositorio
en el commit del hito 80 y la etiqueta `base-n1`. Todo lo que sigue lo miden comandos del
repositorio; nada está copiado del plan.

## 1. Tablero

Salida de `uv run python tools/tablero.py --markdown`:

| Medida | Valor |
|---|---|
| Componentes emitidos por `sgm talend client_large.sas` | 26 (job_conciliacion 1, job_exogena_depositos 13, job_producto 11, job_totales 1); meta N1 unos 80 |
| Conformidad contra el diseño manual | 12 de 118 filas y 2 de 22 secciones |
| Pendientes del modelo para el programa grande | 16, en 5 motivos |
| Casos del corpus | 117 (L0 15, L1 15, L2 15, L3 12, L4 20, L5 12, L6 12, L8 16); 116 con archivos en `esperado/` |
| Casos del corpus por estado | parcial 5, pendiente 1, pendiente_revision 17, revisado 13, traducible 81 |
| Cobertura de construcciones del SAS | 206 construcciones distintas en el corpus; 93 aparecen en casos `traducible` |
| Casos traducidos por un traductor automático y pasados en Studio | no hay traductor general: R7-01 a R7-18 del plan |

Pendientes por motivo:

| Pendientes | Motivo |
|---:|---|
| 8 | sin copia en otro producto: proceso propio, la equivalencia es decisión humana |
| 3 | el nombre depende de una macrovariable o de todos los datasets |
| 3 | se lee antes de que el programa la cree |
| 1 | el producto no distingue las copias: hay que declarar el parámetro |
| 1 | ningún patrón de `etapas` las cubre: Validar DV; Validar monetarios; Validar nombres; Validar_mes_año; tit-cot vacíos o 0 |

## 2. Suite y conformidad

`uv run pytest -q`: **1556 pasan, 26 se saltan, 132 xfail**; entre 47 y 57 segundos con `-n auto`.
`uv run ruff check .`: limpio.

`uv run pytest tests/conformidad -q -n0`: **42 pasan, 126 xfail** (168 pruebas). El desglose, que
es lo que cuenta el tablero:

| Conjunto | Pruebas | Pasan | En xfail |
|---|---:|---:|---:|
| Secciones del diseño manual | 22 | 2 | 20 |
| Filas de la referencia | 118 | 12 | 106 |
| Referencia contra el documento de origen | 28 | 28 | 0 |

`tests/conformidad/test_referencia.py` comprueba que el YAML y el documento Markdown del manual
describen lo mismo; por eso pasa entero aunque el emisor no emita esas secciones. Las cifras "42
pasan / 126 xfail / 168 filas" de la sección 2 del plan son este conteo de pytest; el tablero
cuenta solo filas y secciones de la referencia (12 de 118 y 2 de 22) para no mezclar las dos cosas.

## 3. Corpus

`uv run python tools/corpus.py oraculo todos --verificar`: **117 casos, 0 con falla**. Los casos de
`L8` capa A se omiten con motivo (entradas en formato SAS y `PROC IMPORT`/`DATA step`, que el
oráculo SQL no ejecuta); su cruce vive en `tools/corpus_datos/*cruce*.py`.

| Nivel | Casos | Traducibles | Otros estados |
|---|---:|---:|---|
| L0 | 15 | 0 | 13 `revisado`, 2 `pendiente_revision` |
| L1 | 15 | 15 | — |
| L2 | 15 | 15 | — |
| L3 | 12 | 12 | — |
| L4 | 20 | 19 | 1 `pendiente` (por `PUT` y fechas sin vector) |
| L5 | 12 | 12 | — |
| L6 | 12 | 7 | 5 `pendiente_revision` |
| L8 | 16 | 1 | 5 `parcial`, 10 `pendiente_revision` |

`L0` son los casos del original que sirven de muestra, no de equivalencia: están revisados a mano
contra el programa, por eso no cuentan como `traducible`.

## 4. Lo que esta línea base no mide

- Jobs emitidos por el emisor **ejecutados** en Studio: hoy solo están compilados, y la
  demostración del arnés (hito 79) usó un Job escrito a mano.
- Tiempo y memoria a volumen real: no hay datos ni generador a escala todavía (R8-01).
- El comportamiento de Impala real dentro de un Job del emisor: las lecturas de Impala del SAS
  siguen sin traducir (R4-04).

## 5. Cómo se reproduce

```bash
uv run python tools/tablero.py          # la tabla de la sección 1 y los motivos
uv run python tools/ci.py               # ruff, suite, cruces, oráculo y tablero, con código de salida
git rev-parse base-n1                   # el commit de esta instantánea
```
