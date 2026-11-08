# sgm

Compila programas SAS a una especificación revisable para construir Jobs en Talend.
No ejecuta nada: lee el texto, extrae hechos, aplica reglas y produce guías y planes.

## Instalación

Requiere Python 3.12 y `uv`.

```powershell
uv sync
uv run pytest -q
uv run ruff check .
```

### Ciclos rápidos de pruebas

Para el desarrollo local, instala las dependencias y ejecuta una primera vez:

```powershell
uv sync
uv run pytest --testmon -q -n 4
```

Esa primera ejecución corre la suite completa y registra qué archivos usa cada prueba. En ejecuciones
posteriores, el mismo comando vuelve a correr las pruebas afectadas por los cambios. La primera pasada
puede tardar lo mismo que la suite completa; el ahorro aparece en las siguientes iteraciones. Se fijan
cuatro workers porque la medición local mostró que `-n auto` tardaba más en la fase incremental. La
base local está en `.testmondata` y no se versiona.

Antes de cerrar un hito, conserva la verificación completa, sin selección incremental:

```powershell
uv run pytest -q
uv run ruff check .
```

Si cambian dependencias, configuración de pytest o el propio conjunto de pruebas, vuelve a ejecutar
la suite completa para actualizar y comprobar la selección incremental.

## Comandos

| Comando | Para qué |
|---|---|
| `uv run python -m sgm.cli intake <ruta>` | Importa un lote, quita secretos y compila |
| `uv run python -m sgm.cli facts <ruta>` | Hechos de cada programa en JSON, con fuente |
| `uv run python -m sgm.cli mapa <ruta> --out <carpeta>` | Mapa de flujo en Markdown, sin traducir |
| `uv run python -m sgm.cli compile <ruta> --out <carpeta>` | Guía y plan JSON de cada programa |
| `uv run python -m sgm.cli explain <archivo>:<línea>` | Qué operador y qué regla cubren una línea |
| `uv run python -m sgm.cli gaps list --top 20` | Huecos por firma, con dueño y arreglo |
| `uv run python -m sgm.cli rules validate` | Valida las reglas y sus casos |
| `uv run python -m sgm.cli metrics <ruta> --check` | Falla si una métrica empeora |
| `uv run sgm studio salud` | Studio por MCP o CLI: salud, lote y veredicto (`compilar`, `verificar`) |
| `uv run python tools/ci.py` | Cierra un hito: `ruff`, suite, cruces, oráculo y tablero |
| `uv run python tools/liberacion.py` | Compuerta de liberación: suite, oráculo, determinismo, secretos y versión |
| `uv run python tools/tablero.py` | La fotografía del plan: componentes, conformidad y corpus |

## Cerrar un hito

Un comando corre todo lo que `AGENTS.md` pide antes de un commit y resume el resultado:

```powershell
uv run python tools/ci.py
```

Corre `ruff check .`, la suite completa con `pytest -q`, los cruces del corpus
(`tests/unit/test_corpus_*cruce*.py` y `test_corpus_validaciones.py`), el oráculo
(`tools/corpus.py oraculo todos --verificar`) y el tablero. Sale con código distinto de 0 si algún
paso obligatorio falla, imprime la cola de la salida del que falló y deja una tabla con el tiempo
de cada paso. `--sin-suite` sirve para iterar y `--sin-tablero` cuando no hace falta la
fotografía. El tablero solo informa: nunca hace fallar el cierre.

## Compuerta de liberación

Antes de publicar una versión, un solo comando decide si el código se puede liberar:

```powershell
uv run python tools/liberacion.py
```

Corre `ruff`, la suite completa con cuatro workers, el oráculo del corpus, dos migraciones del mismo
caso para comprobar que dan los mismos bytes, el escáner de secretos sobre esa salida y la
coincidencia de versión entre `pyproject.toml`, el paquete y `CHANGELOG.md`. Sale con código distinto
de 0 si algo falla y deja la tabla de cada paso. `--sin-suite` sirve para iterar.

La compuerta en verde no significa que el migrador esté listo para producir: el avance, los bloqueos
y las condiciones humanas están en `docs/produccion.md`.

## Qué produce

- **Guía** (`*.guide.md`): por programa, operadores, joblets, huecos y pendientes, cada uno con
  su evidencia (archivo y líneas).
- **Plan** (`*.plan.json`): lo mismo en JSON, con la etiqueta de versión (`sgm_version`,
  `ruleset_hash`) y el bloque `pendientes`.
- **Mapa de flujo** (`*.md`): lo que el programa hace, en español, sin términos de Talend.

## Principios

- Ningún valor sale sin fuente: si el archivo no lo dice, es un pendiente con dueño.
- Las credenciales se enmascaran antes de cualquier análisis (`***`).
- Las reglas viven en `rules/` como datos. Cerrar un hueco no toca `src/`.
- Una decisión que no ha tomado una persona no se aplica: queda como sugerencia.

## Documentación

- `docs/automatizacion/01-automatizacion.md`: diseño de la automatización.
- `docs/automatizacion/02-mapa-de-flujo.md`: qué muestra el mapa de flujo.
- `docs/automatizacion/03-plan-produccion.md`: plan por fases y su estado.
- `docs/automatizacion/04-runbook.md`: cómo incorporar un archivo nuevo.
- `docs/produccion.md`: qué falta para producción, con la compuerta y los bloqueos.
- `PROGRESS.md`: bitácora de hitos, con pruebas y decisiones.

## Límites

- La equivalencia de datos con SAS no se demuestra aquí; se verifica con datos reales.
- La conexión con Talend Studio es opcional y vive en `src/sgm/backend_talend/`: `sgm studio` y
  `--backend mcp` usan el servidor de `talend-mcp`, y `--backend talend` su CLI; sin ninguno, el
  resultado se revisa a mano en Studio.
