# Prompt para el agente: fase 1, herramientas para evolucionar

Usar **después** de que la ronda 2 termine y el equipo haya revisado sus hitos (fase 0). Copia todo lo que está debajo de la línea.

---

## Contexto

Trabajas en `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2`. Antes de empezar lee, en este orden: `AGENTS.md`, `PROGRESS.md`, `docs/plan/00-README.md`, `docs/plan/03-ciclo-de-huecos.md`, `docs/plan/04-puntos-de-extension.md`, `docs/plan/05-contratos.md` y `docs/plan/06-calidad.md`.

Siguen vigentes todas las reglas de `AGENTS.md`: nada de MCP, API ni web; no conectarse a bases; no inventar datos; no guardar secretos; nada de nombres de programas del cliente en `src/` ni `rules/`; commits locales sin push; `PROGRESS.md` al cierre de cada hito. Usa `uv run python -m sgm.cli ...` porque `sgm.exe` está bloqueado.

## Objetivo

Que cerrar un hueco sea crear un archivo de reglas con su caso de prueba, sin tocar `src/`. Al terminar, el equipo podrá recibir cualquier archivo SAS nuevo, ver qué falló, saber quién lo arregla y con qué archivo.

**Regla clave:** esta fase **no cambia la salida**. Mover lógica del código a YAML debe producir exactamente los mismos golden y las mismas métricas. Si algo cambia, es un error de la migración.

## Hitos

Cada hito: pruebas y ruff en verde, golden sin cambios (salvo F1.1), trinquete en verde, `PROGRESS.md`, commit `fase1 F<n>: <resumen>`.

### F1.0. Línea base

1. Si no existe `metrics/baseline.json`, créalo con la salida actual de `sgm metrics` sobre todo el corpus.
2. Implementa `sgm metrics --check` según `06-calidad.md`: compara con la línea base y falla si una métrica empeora. Agrégalo a la suite como prueba.

### F1.1. Motivos y estados completos

1. Agrega los motivos `INCLUDE_EXTERNO`, `COMPONENTE_NO_CATALOGADO` e `INTRINSECO_PARCIAL`. Reclasifica los huecos existentes que correspondan (por ejemplo, un `%include` a un archivo que no está pasa a `INCLUDE_EXTERNO`).
2. Prueba que falla si un operador del corpus no tiene estado, o si una línea del SAS de entrada no está en la evidencia de un componente, en `not_migrated` o en un hueco.
3. Esta es la única tarea de la fase que puede cambiar golden: solo el campo de motivo de los huecos reclasificados.

### F1.2. Esquemas y validación de reglas

1. Escribe un JSON Schema por tipo en `schemas/rules/`: `proc`, `statement`, `function`, `informats`, `plumbing`, `intrinsic`, `mapping`, `routing`, y para `env/engines.json`, `env/project.json`, `env/externals.json` y `env/schemas/*.json`. Formatos en `04-puntos-de-extension.md`.
2. `sgm rules validate`: valida todos los archivos, comprueba que cada regla tenga al menos un caso en `tests/cases/` que exista, y que cada componente de `rules/mapping/` exista en los catálogos de Talend. Los errores muestran archivo, ruta del campo y línea.
3. Agrega `jsonschema` como dependencia y anótalo en "Decisiones".

### F1.3. Casos de prueba declarativos

1. Prueba genérica que recorre `tests/cases/*/expected.yaml` y compara con lo que produce `compile` (formato en `04-puntos-de-extension.md`).
2. Crea al menos un caso por cada regla que ya existe.

### F1.4. Reglas fuera del código

Mueve de Python a archivos de reglas, sin cambiar la salida:

1. Mapeos a componentes a `rules/mapping/*.yaml`.
2. Funciones SAS del traductor de expresiones a `rules/sas/functions/*.yaml`. El código del traductor queda como motor que lee esas entradas.
3. Informats y formatos (inferencia de tipos desde el código) a `rules/sas/informats.yaml`.
4. Patrones de fontanería a `rules/sas/plumbing.yaml`.
5. Sentencias globales (`title`, `footnote`, `ods`, `options`, etc.) a `rules/sas/statements/*.yaml`.
6. Bajada de `proc sort`, `proc append`, `proc means`, `proc summary` y `proc freq` a `rules/sas/procs/*.yaml`, con un cargador que interpreta `bind` y `ops`.
7. Registro de los intrínsecos existentes en `rules/sas/intrinsics/*.yaml` con su `implementation`.

Después de cada punto: golden iguales y trinquete en verde.

### F1.5. Ruteo y lista de huecos

1. `rules/routing.yaml` con dueños y `fix_with` (contenido en `04-puntos-de-extension.md`).
2. `sgm gaps list` con `--owner`, `--file` y `--top`, ordenado por archivos afectados y luego por ocurrencias. Cada fila muestra firma, motivo, dueño, archivos, ocurrencias, un ejemplo con archivo, líneas y etiqueta, `fix_with` y el comando sugerido.

### F1.6. Generadores

1. `sgm case new --from-gap <firma>`: crea `tests/cases/<firma-normalizada>/` con `input.sas` (el fragmento mínimo que reproduce el hueco, con tablas y columnas renombradas a `t1`, `c1`, etc., y sin secretos), `expected.yaml` con el estado actual y `README.md`.
2. `sgm rules new <tipo> --from-gap <firma>`: crea el archivo de reglas prellenado en la carpeta del tipo, con `status: parcial`, `version: 1` y `tests` apuntando al caso.
3. Prueba: para un hueco sintético de cada motivo, los dos comandos producen archivos que validan.

### F1.7. Entrada de archivos nuevos

`sgm intake <archivo-o-carpeta>` según `03-ciclo-de-huecos.md`: copia a `corpus/inbox/<fecha>-<hash>/`, normaliza codificación a UTF-8 (detecta UTF-8 con y sin BOM, cp1252 y latin-1), redacta secretos, compila, guarda guía, plan y huecos en esa carpeta, y registra los huecos. `corpus/` va en `.gitignore` salvo `corpus/README.md`.

### F1.8. Explicar una línea

`sgm explain <archivo>:<línea>`: muestra el nodo y el paso SAS de esa línea, los operadores de la IR que la contienen, qué pasada los fusionó o quitó, y el componente final, o el hueco o la entrada de `not_migrated` donde quedó.

### F1.9. Esquemas desde Impala

1. `sgm env import-describe <archivo> --schema <nombre>`: lee la salida de texto de `DESCRIBE <tabla>` (una o varias tablas en el mismo archivo, separadas por el nombre de la tabla) y escribe `env/schemas/<nombre>.json`. Mapea tipos de Impala a tipos de la IR: `string` y `varchar` a `String`, `int` a `Integer`, `bigint` a `Long`, `double` y `float` a `Double`, `decimal(p,s)` a `BigDecimal`, `timestamp` y `date` a `Date`, `boolean` a `Boolean`.
2. Convierte `env/schemas.json` en la carpeta `env/schemas/` y adapta la pasada 9.
3. Prueba con una salida de `DESCRIBE` sintética.

### F1.10. Verificación final

1. Ciclo completo con un hueco de cada motivo, siguiendo `03-ciclo-de-huecos.md` y tocando solo `rules/`, `env/` y `tests/cases/`. Documenta cada uno en `PROGRESS.md`.
2. Pruebas, ruff, `rules validate` y `metrics --check` en verde.

## Entrega final

Reporte breve en español:

1. Hitos terminados y los que no, con el motivo.
2. Pruebas que pasan, ruff, `rules validate` y `metrics --check`.
3. Confirmación de que los golden no cambiaron, salvo la reclasificación de F1.1, con la lista de cambios.
4. Los huecos cerrados en F1.10, con el archivo que se creó para cada uno.
5. Top 10 de huecos por dueño.
6. Decisiones de diseño tomadas por tu cuenta.
7. Commits locales.

No hagas push. No actives MCP.
