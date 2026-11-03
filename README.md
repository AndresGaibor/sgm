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
- `PROGRESS.md`: bitácora de hitos, con pruebas y decisiones.

## Límites

- La equivalencia de datos con SAS no se demuestra aquí; se verifica con datos reales.
- No hay conexión a bases ni a Talend Studio: el resultado se revisa a mano en Studio.
