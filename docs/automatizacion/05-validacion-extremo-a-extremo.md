# Validación extremo a extremo (fase 5.8)

Objetivo: comprobar, con datos de prueba, que un Job construido a mano en Talend Studio desde la
guía produce los mismos datos que el programa SAS de origen.

Esta validación **no** la hace el repositorio solo. Necesita un ambiente con SAS, Talend Studio y
datos de prueba. El repositorio aporta la comparación (`sgm comparar`) y este procedimiento.

## Requisitos

- Un programa SAS de referencia y su guía generada (`sgm compile` o `sgm intake`).
- Datos de prueba representativos, fuera del repositorio. No se usan datos reales de clientes.
- Talend Studio con los componentes que la guía marca como necesarios. Un componente marcado como
  opcional debe instalarse antes con Feature Manager.

## Procedimiento

1. **Preparar los datos de prueba.** Un juego por programa, con las mismas tablas de entrada que
   usa el programa. Guardar la copia que usará SAS y la que usará Talend.
2. **Ejecutar el programa SAS** sobre el juego de prueba y exportar la salida principal a CSV
   (separador `;`, encabezado en la primera fila). Anotar la ruta exacta del archivo.
3. **Construir el Job en Studio a mano**, siguiendo la guía en este orden: contextos, jobs y
   subjobs, joblets, componentes con su regla. Cada componente se revisa contra su evidencia
   (archivo y líneas). Los pendientes de la guía se resuelven antes de ejecutar; si no se pueden
   resolver, se anota el motivo.
4. **Medir el tiempo de construcción** y anotar los problemas que aparezcan. Son insumo para
   mejorar la guía.
5. **Ejecutar el Job** sobre el mismo juego de prueba y exportar su salida a CSV con el mismo
   separador y el mismo encabezado.
6. **Comparar:**

   ```powershell
   uv run python -m sgm.cli comparar ruta\sas.csv ruta\talend.csv
   ```

   El comando compara tres cosas:
   - Número de filas.
   - Suma de cada columna numérica.
   - Huella del contenido, sin importar el orden de las filas.

   Sale con código 0 si todo coincide y con código 1 si algo no coincide.
7. **Registrar el resultado** en `PROGRESS.md`: programa, juego de prueba, tiempo de construcción,
   resultado de la comparación y los problemas encontrados.

## Criterio de aceptación

- `sgm comparar` termina con código 0 sobre la salida principal.
- Ningún pendiente de la guía quedó sin resolver en el Job construido.
- Los problemas encontrados están anotados, con su causa.

Si la comparación falla, no se acepta el Job: se revisa primero la guía y luego el Job.

## Lo que la comparación no demuestra

- Que el Job sea correcto para otros datos distintos del juego de prueba.
- Que las columnas no numéricas coincidan fila a fila: la huella lo dice en conjunto, no por campo.
- Que el programa sea correcto desde el punto de vista del negocio. Eso lo decide quien conoce el
  proceso.
