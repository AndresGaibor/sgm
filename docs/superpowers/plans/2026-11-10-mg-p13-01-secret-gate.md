# Plan de implementación: compuerta MG-P13-01

## Alcance

Integrar el escáner en `sgm migrar` para archivo y carpeta, mantener la salida existente intacta
cuando la revisión no sea limpia y agregar la corrida nocturna sobre una fuente controlada y
`decisiones/`.

## Pasos

1. Añadir pruebas de regresión primero: hallazgo en salida generada, credencial oculta en el mensaje,
   salida previa con hallazgo intacta, conservación de archivos manuales, enlace/junction de salida,
   fallo del escáner cerrado y migración por carpeta con código de salida global 1.
2. Añadir un helper pequeño de seguridad que valide destino, cree staging temporal, escanee staging
   y destino, publique solo archivos revisados y devuelva hallazgos enmascarados.
3. Envolver la escritura de `sgm migrar`; propagar hallazgos seguros al resultado y fijar código 1
   si un paquete no se publica por seguridad.
4. Agregar workflow nocturno y manual, con permisos mínimos y acciones fijadas a SHA.
5. Actualizar `docs/secretos.md`, el plan maestro, el porcentaje medido y `PROGRESS.md`.
6. Ejecutar pruebas enfocadas y las compuertas completas requeridas; revisar el diff y crear el
   commit local `hito 134: integrar compuerta de secretos`.

## Aceptación

- Un artefacto con hallazgo no aparece en la ruta de salida.
- Un paquete previo con hallazgo no se altera.
- El escáner no puede revelar el valor completo ni al bloquear ni al fallar.
- La migración limpia conserva el conjunto y los bytes de los artefactos.
- Los paquetes limpios de un lote se publican aunque otro paquete sea bloqueado; el lote termina
  con código 1.
- El workflow puede correr por cron y manualmente, sin secretos ni servicios externos.
- `uv run pytest -q`, `uv run ruff check .`, `uv run python -m sgm.cli rules validate` y
  `git -c core.whitespace=cr-at-eol diff --check` terminan correctamente.

## Fuera de alcance

No se cambia la detección del escáner, no se clasifica PII, no se generan SBOM y no se modifican
escapes del emisor; esos son MG-P13-03, 04 y 05. La confirmación de credenciales de MG-P13-02
requiere revisión de una persona.
