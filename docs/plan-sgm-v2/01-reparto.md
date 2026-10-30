# Reparto de responsabilidades

Cada módulo y cada tipo de hueco tiene **un** dueño. El dueño decide y responde por el resultado; los otros dos pueden contribuir con revisión.

## Módulos

| Módulo | Ruta | Dueño | Revisa |
| --- | --- | --- | --- |
| Ingesta y entrada de archivos nuevos | `src/sgm/ingest/`, `corpus/` | Joseph | Andres |
| Lexer, separador de nodos, pasos | `src/sgm/frontend/lexer.py`, `splitter.py`, `steps.py` | Joseph | Andres |
| DATA step y PROC SQL (lectura) | `src/sgm/frontend/datastep.py`, `sql.py` | Joseph | Andres |
| Expansor de macros | `src/sgm/frontend/macros.py`, `macro_index.py` | Joseph | Andres |
| SAS Grid (sasgsub, sysin, Control-M) | `src/sgm/frontend/grid.py` | Joseph | Byron |
| Modelos de la IR | `src/sgm/ir/models.py` | Andres | Los tres (es contrato) |
| Bajada a la IR | `src/sgm/ir/lower.py` | Andres | Joseph |
| Firmas | `src/sgm/ir/signature.py` | Andres | Joseph |
| Pasadas 1, 4 a 8 | `src/sgm/passes/p01`, `p04` a `p08` | Andres | Byron |
| Pasadas 2 y 3 (fontanería, intrínsecos) | `src/sgm/passes/p02`, `p03` | Joseph | Andres |
| Pasada 9 (esquemas) | `src/sgm/passes/p09_schemas.py` | Byron | Andres |
| Pasada 10 (componentes) | `src/sgm/passes/p10_components.py` | Byron | Andres |
| Traductor de expresiones | `src/sgm/expressions/` | Joseph (semántica SAS) | Byron (Java y Talend) |
| Catálogo de entorno | `src/sgm/catalog/environment.py`, `env/` | Byron | Joseph |
| Catálogo de Talend | `src/sgm/catalog/talend.py`, `rules/talend/` | Byron | Andres |
| Overrides y huecos | `src/sgm/store/` | Andres | Byron |
| Guía y plan de salida | `src/sgm/emit/` | Byron | Andres |
| Métricas y trinquete | `src/sgm/metrics.py`, `metrics/` | Andres | Joseph |
| CLI | `src/sgm/cli.py` | Andres | Los tres |
| Web, API y MCP (fase 5) | por crear | Byron | Andres |

## Huecos: quién los cierra

El motivo del hueco decide el dueño. La tabla también vive como datos en `rules/routing.yaml` para que `sgm gaps list --owner` la use.

| Motivo | Dueño | Se cierra normalmente con |
| --- | --- | --- |
| `PARSE_ERROR` | Joseph | Corrección del parser y caso de prueba |
| `SENTENCIA_NO_SOPORTADA` | Joseph | `rules/sas/statements/*.yaml` o corrección del parser |
| `PROC_NO_SOPORTADO` | Joseph | `rules/sas/procs/*.yaml` |
| `MACRO_DINAMICA` | Joseph | Mejora del expansor, o declaración en `env/externals.json`, o decisión del usuario |
| `INCLUDE_EXTERNO` | Byron | Archivo en `env/externals/` o declaración en `env/externals.json` |
| `FUNCION_NO_MAPEADA` | Joseph | `rules/sas/functions/*.yaml` (Byron revisa el Java) |
| `TIPO_DESCONOCIDO` | Byron | `env/schemas/*.json` o regla de tipos en `rules/sas/informats.yaml` |
| `COMPONENTE_NO_CATALOGADO` | Byron | `rules/mapping/*.yaml` o actualización del catálogo |
| `SEMANTICA_DUDOSA` | Andres | Alternativas en la regla y decisión del usuario |
| `INTRINSECO_PARCIAL` | Joseph | `rules/sas/intrinsics/*.yaml` o código de la pasada 3 |
| Regresión de agrupación o métricas | Andres | Corrección de la pasada |

Los motivos `INCLUDE_EXTERNO`, `COMPONENTE_NO_CATALOGADO` e `INTRINSECO_PARCIAL` son nuevos; se agregan en la fase 1.

## Revisión cruzada

Todo cambio lo revisa otra persona antes de entrar a `main`:

- Joseph revisa a Andres en lo que toca la lectura de SAS.
- Andres revisa a Joseph y a Byron en lo que toca la IR o las pasadas.
- Byron revisa a Andres en lo que cambia la salida (guía, componentes).

Un cambio en `05-contratos.md` necesita el visto bueno de los tres.

## Agentes

Cada persona puede delegar tareas a agentes (modelo Haiku). El dueño del módulo sigue siendo responsable: revisa el resultado, corre las pruebas y firma el cambio. Un agente nunca cambia un contrato ni el trinquete de métricas.
