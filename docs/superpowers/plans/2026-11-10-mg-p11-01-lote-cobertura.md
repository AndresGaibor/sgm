# MG-P11-01: lote de `sgm migrar` y cobertura por programa — plan de implementación

> Ejecutar en línea como un hito. El orden por dependencias entre programas pertenece a MG-P11-03.

**Objetivo:** completar la CLI para archivo/carpeta y emitir `cobertura.md` por programa sin afirmar
cobertura de líneas que los datos no demuestran.

**Arquitectura:** la migración unitaria se mantiene en `cli_migrar.py`; el comando y el lote quedan
en un módulo CLI pequeño. El informe se compone en `migrar/informes.py` desde los nodos, la traza y
los pendientes ya existentes.

**Tech Stack:** Python, Typer, pathlib, pytest; sin dependencias nuevas.

**Spec:** `docs/superpowers/specs/2026-11-10-mg-p11-01-lote-cobertura-design.md`.

## Global Constraints

- Solo librería Python y CLI; no frontend ni API.
- No conectarse a bases; los esquemas vienen de archivos locales.
- No inventar trazas, líneas, tipos, equivalencias ni porcentajes.
- No debilitar pruebas; ejecutar `uv run pytest -q` y `uv run ruff check .`.
- Un commit local por hito, `hito 132: <resumen>`; no hacer push.

## Review Focus

- Dos programas con el mismo nombre en subcarpetas: preservar ambas salidas mediante ruta relativa.
- Archivos no `.sas` dentro de la carpeta: ignorarlos.
- Carpeta sin programas: terminar sin excepción y explicar que no hubo entradas.
- Pendiente sin línea o línea con nodo y pendiente a la vez: mostrarlos sin pérdida ni doble conteo
  de estados.
- Repetir la misma migración: conservar bytes deterministas.

---

## Task 1: Completar el lote de CLI y la cobertura del programa

**Files:**

- Modify: `src/sgm/migrar/informes.py`
- Modify: `src/sgm/cli_migrar.py` (dejar el módulo por debajo de 300 líneas)
- Create: `src/sgm/cli_migrar_comando.py`
- Modify: `src/sgm/cli.py`
- Test: `tests/unit/test_cli_migrar.py`

**Interfaces:**

- Consume: `migrar(source, out, esquemas, muestra, backend) -> ResultadoMigrar`.
- Produce: `informes.cobertura_md(programa, jobs, traza, pendientes) -> str` y el comando Typer
  `migrar_command` para archivo o carpeta. Las salidas de carpeta usan la ruta relativa sin `.sas`.

- [x] Escribir primero pruebas para cobertura de líneas trazadas, pendientes con y sin línea y
  reporte sin porcentajes.
- [x] Ejecutar esas pruebas y confirmar que fallan porque aún no existe `cobertura.md`.
- [x] Implementar el informe estable en `migrar/informes.py` y escribirlo desde `_escribir`.
- [x] Añadir pruebas de CLI para carpeta anidada, archivos no SAS, carpeta vacía, salida relativa,
  resumen, determinismo y compatibilidad de la importación previa; validar el backend antes de crear salidas.
- [x] Implementar la recogida ordenada y delegar cada `.sas` al migrador existente; mantener
  independiente cada paquete y dejar el orden por dependencias a MG-P11-03.
- [x] Actualizar este plan, `PROGRESS.md` y el estado de MG-P11 del plan maestro.
- [x] Ejecutar pruebas focalizadas (16 pasaron), `uv run pytest -q` (2665 pasaron, 26 omitidas,
  139 xfailed), Ruff, rules validate y diff check.
- [x] Crear commit local `hito 132: migrar carpetas y generar cobertura por programa`.
