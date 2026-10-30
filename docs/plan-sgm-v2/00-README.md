# Plan de equipo sgm v2

Estos archivos van en el repositorio, en `docs/plan/`. Son la referencia del equipo (Andres, Joseph, Byron) y de los agentes que trabajen en sgm. Si algo de aquí contradice el código, se corrige el documento o el código en el mismo cambio.

## Qué significa "100 %"

Traducir automáticamente cualquier programa SAS al 100 % no es posible: hay construcciones como `CALL EXECUTE` o código generado en ejecución que ninguna herramienta puede traducir sin una persona. Por eso el 100 % de sgm se define así:

1. **Nada se cae.** Cualquier archivo SAS, por raro o roto que sea, se compila sin excepción.
2. **Nada se pierde.** Cada línea del SAS de entrada aparece en la evidencia de un componente, en `not_migrated` con su motivo, o en un hueco.
3. **Nada queda sin explicar.** Cada hueco tiene firma, motivo, dueño y el archivo que hay que crear o cambiar para cerrarlo.
4. **Todo hueco tiene camino.** Cerrar un hueco es agregar o editar un archivo de reglas (YAML o JSON) con su caso de prueba, en la mayoría de los casos sin tocar el motor.
5. **Nada retrocede.** Las métricas tienen un trinquete: un cambio que las empeora no entra.

La automatización (porcentaje de pasos traducidos sin pendientes) sube con el uso: cada archivo nuevo, o se traduce, o deja huecos medidos que el equipo cierra.

## Archivos

| Archivo | Para qué |
| --- | --- |
| `01-reparto.md` | Quién es dueño de qué módulo, de qué tipo de hueco y de qué revisión |
| `02-fases.md` | Fases con tareas por persona y criterio de salida |
| `03-ciclo-de-huecos.md` | Qué pasa cuando llega un archivo nuevo y aparece un error, paso a paso |
| `04-puntos-de-extension.md` | Cada tipo de archivo de reglas: ruta, formato, ejemplo, prueba y dueño |
| `05-contratos.md` | Lo que no puede cambiar sin acuerdo de los tres: modelos, formatos, versiones |
| `06-calidad.md` | Pruebas, trinquete de métricas, definición de terminado |
| `07-prompt-f1-herramientas.md` | Prompt para un agente que construye las herramientas de la fase 1 |

## Resumen del reparto

| Persona | Lado | Es dueño de |
| --- | --- | --- |
| Andres | Núcleo | IR, pasadas del compilador, partición, métricas, herramientas del ciclo de huecos, dirección técnica |
| Joseph | SAS | Lectura de SAS: parser, macros, intrínsecos, PROCs, funciones e informats, SAS Grid, entrada de archivos nuevos |
| Byron | Talend y entorno | Reglas hacia componentes, catálogo de Talend, convenciones de Jobs, catálogo de entorno (esquemas, motores, externos), guía de salida; después web y MCP |

## Cómo empezar

1. Leer `05-contratos.md` los tres juntos y acordar cualquier cambio antes de seguir.
2. Cada uno abre su sección en `02-fases.md` y toma la primera tarea de la fase en curso.
3. Todo hueco nuevo se trabaja con `03-ciclo-de-huecos.md`.
