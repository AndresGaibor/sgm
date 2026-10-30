# Calidad

## Capas de prueba

| Capa | Dónde | Qué prueba | Cuándo corre |
| --- | --- | --- | --- |
| Unitarias | `tests/unit/` | Cada módulo y cada pasada por separado | Siempre |
| Casos | `tests/cases/` | Una regla o un hueco cerrado, con `expected.yaml` | Siempre |
| Golden | `tests/golden/` | Salida completa de programas de referencia | Siempre |
| Hostiles | `tests/fixtures/sas/hostile/` | Archivos rotos, vacíos, binarios, gigantes, codificaciones raras | Siempre |
| Guardias | `test_no_script_specific_names`, `test_security`, validación de reglas | Reglas de trabajo | Siempre |
| Corpus | `corpus/accepted/` y fixtures | Métricas y trinquete | Antes de cada commit a `main` |

## Trinquete de métricas

`metrics/baseline.json` guarda los valores aceptados. `sgm metrics --check` falla si alguno empeora:

| Métrica | Dirección buena |
| --- | --- |
| Pasos SAS por componente | Sube |
| Porcentaje de `tJava` | Baja |
| `tJava` con origen PROC SQL | Se mantiene en 0 |
| Subjobs por programa | Baja |
| Líneas sin cubrir (sin componente, `not_migrated` ni hueco) | Se mantiene en 0 |
| Excepciones al compilar | Se mantiene en 0 |
| Huecos por motivo | Baja |
| Firmas únicas de decisiones sin valor por defecto revisado | Baja |
| Tiempo de compilación del corpus | No sube más de 20 % |

Solo Andres actualiza la línea base, y solo con una razón escrita en el commit.

## Golden

Una diferencia en un golden no es un error en sí. Quien la produce:

1. Mira la diferencia completa.
2. Si es una mejora, actualiza el golden y explica en el commit qué mejoró.
3. Si no lo es, corrige el cambio.

## Definición de terminado

Una tarea está terminada cuando:

1. Las pruebas pasan: `uv run pytest -q`.
2. Ruff está limpio: `uv run ruff check .`.
3. Las reglas validan: `sgm rules validate`.
4. El trinquete pasa: `sgm metrics --check`.
5. Hay al menos un caso o prueba nueva que demuestra el cambio.
6. Otra persona lo revisó.
7. `PROGRESS.md` tiene una línea con qué se hizo y las métricas antes y después, si cambiaron.

## Rendimiento

Se mide en la fase 3 (tarea A3.2) y se fijan aquí los límites. Hasta entonces, solo se vigila que el tiempo del corpus no suba más de 20 % por cambio.
