> **SUPERADO (17 de noviembre de 2026, tras integrar la serie de Byron):** la tarea `C-22` de
> `docs/superpowers/plans/2026-11-11-mg-c-sql-y-procedimientos.md` (carril de Byron) crea
> `tools/cobertura_procs.py` y genera el mismo documento de cobertura con los 77 procedimientos de la guía,
> no solo con las 9 entradas de `procs-usados.yaml`. Dos herramientas escribiendo `docs/cobertura.md`
> chocarían. **No ejecutar este change**; si `C-22` queda corta, se archiva sin aplicar. Sus 8 pruebas (en
> `tasks.md`) se pueden reutilizar como punto de partida de `C-22`.

# Propuesta

## Why

El plan maestro (MG-P6-06) pide un documento de cobertura que diga qué procedimientos SAS no tiene
tratados el migrador y por qué. Hoy esa información está en `rules/sas/catalogo/procs-usados.yaml`,
pero solo se lee en el YAML: nadie la ve de un vistazo y no hay un documento que se pueda revisar.
Hacerlo a mano dejaría el documento desfasado en cuanto cambie el catálogo, así que se genera.

El plan dice «fuera de alcance». El catálogo no usa esa palabra: su estado es `no_verificada`, que
significa que la guía tiene la página y el repositorio no la trata. Eso no equivale a «fuera de
alcance». El documento debe mostrar el estado tal cual, sin reclasificarlo.

## Historias de usuario

- Como responsable del migrador, quiero un `docs/cobertura.md` generado desde el catálogo, para ver
  de un vistazo qué procedimientos no tienen tratamiento y qué dice la guía sobre cada uno.
  - Criterio: el documento lista una fila por cada entrada del catálogo cuyo estado no es `reconocida`.
  - Criterio: cada fila muestra nombre, página de la fuente, estado y motivo tomados del catálogo.
  - Criterio: el documento no inventa motivos ni estados: lo que no está en el catálogo no aparece.
- Como revisor, quiero saber si `docs/cobertura.md` está al día con el catálogo, para no revisar un
  documento viejo.
  - Criterio: la herramienta tiene un modo de verificación que termina con error si el archivo no
    coincide con lo que generaría ahora.

## What Changes

- Nueva herramienta `tools/generar_cobertura.py` que lee `rules/sas/catalogo/procs-usados.yaml`
  y escribe `docs/cobertura.md`.
- Nuevo documento generado `docs/cobertura.md` con una tabla: procedimiento, página, estado y motivo.
- Modo `--verificar` de la misma herramienta: sale con código distinto de cero si el documento está
  desactualizado. No se conecta a `tools/ci.py` en este cambio.
- Prueba unitaria de la herramienta en `tests/unit/`.
- No cambia el traductor, ni `rules/`, ni el catálogo.

**Fuera de alcance de este cambio:**
- Cubrir procedimientos de todo el corpus. El catálogo solo tiene los que aparecen en
  `client_large.sas`. Ampliarlo al resto de los 189 programas es otra tarea del plan.
- Conectar la verificación a `tools/ci.py`. Lo decide quien revise el cierre del hito.

## Capabilities

### New Capabilities
- `cobertura-procedimientos-sas`: documento generado que muestra qué procedimientos SAS no tienen
  tratamiento en el migrador, con su página de la guía y su motivo, y un modo para comprobar que el
  documento está al día.

### Modified Capabilities
<!-- Ninguna: el traductor y los catálogos no cambian. -->

## Impact

- Archivos nuevos: `tools/generar_cobertura.py`, `docs/cobertura.md`,
  `tests/unit/test_generar_cobertura.py`, y la carpeta de este change.
- Lee: `rules/sas/catalogo/procs-usados.yaml`, con el esquema `schemas/rules/catalogo.schema.json`.
- Dependencias: ninguna nueva. `pyyaml` ya está permitido.
- Riesgo: ninguno sobre el traductor. El único riesgo es que el documento quede desfasado, y el modo
  `--verificar` lo detecta.
