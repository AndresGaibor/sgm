# MG-P12-01: medir el rendimiento de `sgm migrar` — plan de implementación

> Ejecutar como hito 133. La línea base de `sgm migrar` se guarda separada de `metrics/baseline.json`.

**Objetivo:** medir y verificar tiempo y memoria al migrar `client_large.sas` y los otros 189
programas SAS de fixtures; corregir cuellos de botella solo si los resultados exceden los límites.

**Arquitectura:** un script de herramienta prepara fuentes temporales y ejecuta los dos escenarios
en procesos hijos para medir tiempo de pared y el máximo residente observado del árbol de procesos.
El reporte JSON incluye solo datos reproducibles y no incluye rutas personales.

**Tech Stack:** Python 3.12, biblioteca estándar, pytest y Ruff; sin dependencias nuevas.

**Spec:** `docs/superpowers/specs/2026-11-10-mg-p12-01-performance-design.md`.

## Global Constraints

- No conectarse a Impala ni a ninguna base; no ejecutar SAS ni Talend Studio.
- No añadir dependencias; no guardar secretos ni rutas absolutas en el artefacto de métricas.
- No cambiar `metrics/baseline.json`, que contiene el trinquete de calidad de compilación.
- Tarea completa solo si cada escenario termina con código 0, produce todos los paquetes, tarda
  menos de 120 segundos y usa menos de 1 000 000 000 bytes de memoria residente máxima.
- Actualizar `PROGRESS.md` y el estado/avance de MG-P12; commit local único `hito 133: ...`, sin push.

## Review Focus

- `client_large.sas` se mide por separado y no se duplica en el lote de 189; el total esperado es
  exacto y se recalcula antes de copiar.
- Preparar/copiar las fuentes no entra en `elapsed_seconds`, que solo mide el hijo de migración.
- El muestreo suma la memoria residente del lanzador y sus descendientes, conserva el máximo
  observado y no usa solo el consumo final. La prueba planta 32 MB en el proceso hijo.
- El JSON no contiene perfil de usuario, nombre del equipo ni rutas temporales.
- Códigos de salida, tiempo límite excedido o paquetes faltantes hacen fallar la medición y no
  acreditan la aceptación.

---

## Task 1: crear el arnés y medir los dos escenarios

**Files:**

- Create: `tools/performance/__init__.py`
- Create: `tools/performance/migrar.py`
- Create: `tools/performance/medicion.py`
- Create: `tools/performance/windows_processes.py`
- Create: `metrics/performance/mg-p12-01.json`
- Create: `metrics/performance/README.md`
- Test: `tests/unit/test_performance_benchmark.py`
- Modify: `PROGRESS.md`
- Modify: `docs/plan-reescritura/plan-migrador-general.md`

**Interfaces:**

- Produce `select_sas_files(source: Path, exclude: Path | None) -> list[Path]` ordenada por ruta
  relativa; `stage_sas_files(files: list[Path], source: Path, destination: Path) -> int`; y
  `measure_command(command: list[str], cwd: Path, timeout_seconds: float) -> dict` con duración,
  código de salida y memoria máxima.
- La herramienta se ejecuta con `uv run python tools/performance/migrar.py --output <ruta.json>`.

- [x] Escribir pruebas para selección/exclusión/rutas, medición de un hijo corto y límites estrictos;
  ejecutar y verlas fallar.
- [x] Implementar el arnés y aislar la medición en un módulo pequeño; recorrer el árbol de procesos
  (Windows `WorkingSetSize`, Linux `/proc` `VmRSS`), terminar descendientes en timeout, preparar
  entradas y comprobar los 189 SAS esperados.
- [x] Ejecutar los escenarios realistas y guardar `metrics/performance/mg-p12-01.json`; ambos
  cumplieron los límites y generaron todos los paquetes esperados.
- [x] Documentar ejecución, campos, límites y dependencia del hardware en `metrics/performance/README.md`.
- [x] Actualizar este plan, `PROGRESS.md` y el avance MG-P12 según el resultado medido.
- [x] Ejecutar pruebas focalizadas, `uv run pytest -q`, `uv run ruff check .`, rules validate y diff check.
- [x] Crear commit local `hito 133: medir rendimiento de migrar`.
