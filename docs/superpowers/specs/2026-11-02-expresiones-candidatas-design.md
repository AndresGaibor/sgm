# Expresiones Talend candidatas

## Intención

Conservar en el plan JSON las expresiones que el traductor reconoce con rutinas Talend para que el equipo pueda revisarlas y probarlas en Studio. Hoy `p10_components` usa la traducción para clasificar huecos, pero descarta el Java generado.

## Alcance y límites

- Guardar por operador el texto SAS, la expresión Java candidata, sus columnas y advertencias.
- Identificar el alias `input_row` como marcador que debe sustituirse por el enlace real de fila.
- Mantener el estado parcial y `needs_review` hasta validación en Studio.
- No generar Jobs ni XML, no cambiar componentes y no afirmar equivalencia semántica.

## Enfoques

- **Añadir candidatos a `params` del plan JSON (elegido):** pequeño cambio, visible en el artefacto que ya conserva datos por operador.
- Agregar Java a las notas Markdown: legible, pero mezcla código y anotaciones y puede truncar expresiones.
- Emitir un Job Talend: excede el alcance y necesita validación de Studio no disponible todavía.

## Decisión

El compilador agregará `talend_expression_candidates` solo para traducciones del motor Talend. Cada elemento contiene `source`, `java`, `columns`, `warnings` y `row_context`. Se mantiene el proceso local de Python/CLI y no se agregan dependencias.
