# Diseño: lote de `sgm migrar` y cobertura por programa

## Intención

Completar la primera rebanada de experiencia de uso de MG-P11-01: una invocación de `sgm migrar`
acepta un archivo SAS o una carpeta y cada programa produce un paquete separado con sus Jobs,
traza, pendientes y un informe `cobertura.md` legible.

## Enfoque elegido

- La carpeta se recorre de forma determinista por ruta relativa. Cada archivo conserva su propia
  carpeta de salida; la ruta relativa evita colisiones cuando hay nombres iguales en subcarpetas.
- `cobertura.md` es por programa. Enumera líneas enlazadas a nodos de Jobs, líneas con pendientes y
  pendientes sin línea. Usa solo `trace.json` y los pendientes que la migración ya produce.
- El informe no calcula porcentaje: la migración no conserva un total verificado de líneas SAS ni
  clasifica todavía todas las líneas vacías, comentarios y sentencias no reconocidas.

## Alternativas consideradas

- **Elegida: salidas por programa, bajo la ruta relativa.** Reutiliza el resultado individual ya
  determinista y evita mezclar contextos, pendientes o Jobs de programas distintos.
- **Un solo paquete para toda la carpeta.** Se descarta en este hito: mezcla archivos de contexto y
  reportes; requeriría un contrato de proyecto que MG-P11-03 todavía debe definir.
- **Ordenar por dependencias entre programas ahora.** Se pospone a MG-P11-03, que lo pide
  expresamente. Este primer lote procesa los programas por ruta relativa y no afirma que ese orden
  sea un orden de ejecución.

## Alcance y límites

- Se admite entrada individual o carpeta con archivos `.sas`; cada archivo usa el flujo de
  migración actual y sus opciones `--esquemas`, `--muestra` y `--backend`.
- Un archivo en la raíz conserva `<out>/<programa>/`; uno en subcarpeta conserva
  `<out>/<ruta relativa>/<programa>/`.
- No crea el informe global `docs/cobertura.md` ni el comando `sgm cobertura` de MG-P10-08.
- No agrega frontend, API, dependencia, conexión de base ni cambios de emisor Talend.
- No etiqueta una línea como traducida si no aparece en la traza, y no asigna porcentaje al archivo.

## Comprobación

- Pruebas de CLI para archivo existente, carpeta vacía, archivos en subcarpetas, extensión no SAS,
  rutas repetidas, resumen y determinismo.
- Pruebas del informe para traza con varias líneas, pendientes con y sin línea y ausencia de
  afirmaciones porcentuales.
- Suite completa, Ruff, `sgm rules validate` y `git diff --check`.
