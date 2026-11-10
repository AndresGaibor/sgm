# MG-P10-01: subconsultas IN — Plan de implementación

> **Para agentes de implementación:** usar `superpowers:executing-plans`; los pasos usan casillas para seguir el avance.

**Objetivo:** ejecutar en el anillo B las subconsultas no correlacionadas de una columna usadas por `IN` y `NOT IN` en los tres casos pendientes L2.

**Arquitectura:** el filtro recibe el mapa local de tablas producido hasta ese punto del plan. Antes de evaluar sus filas, el intérprete resuelve cada subconsulta independiente (una tabla, una columna, `WHERE` soportado) y sustituye su resultado por una lista de valores. Rechaza expresamente cualquier forma que salga de ese contrato.

**Tecnologías:** Python 3, `sqlglot`, pytest y Ruff; sin dependencias nuevas.

**Diseño:** `docs/superpowers/specs/2026-11-09-mg-p10-01-subconsultas-in-design.md`.

## Restricciones globales

- Equivalencia basada en `docs/referencia/sas/sqlproc.pdf`, pp. 39, 99, 123–124 y 394; el caso de conjunto vacío se deriva de la definición de pertenencia de p. 394. No inferir comportamiento con faltantes ni correlación.
- No cambiar el emisor Talend ni marcar la traducción completa; `lower_sql_flow` conserva su estado parcial.
- No modificar archivos `esperado/`, ni borrar o debilitar pruebas.
- Sin conexión a bases, Talend CLI/MCP, dependencias nuevas ni cambios al repositorio viejo.
- Registrar Hito 130 y cerrar con commit local `hito 130: interpretar IN con subconsulta no correlacionada`; no hacer push.

## Enfoque elegido

Evaluación directa de la subconsulta con las tablas del intérprete. No se modifica la IR para crear un semi-join: la tarea mide equivalencia del anillo B y los tres casos no requieren cambiar el emisor.

## Revisión prioritaria

Casos adicionales identificados durante la revisión:
- Si una tabla derivada se sobrescribe antes o después del filtro, la subconsulta lee la versión anterior más reciente y no adelanta escrituras futuras; orden ambiguo se rechaza.
- Una proyección de todas las columnas de un lado vacío del LEFT JOIN sin esquema se rechaza, en lugar de emitir una fila sin columnas.

1. Subconsulta vacía: `IN` no selecciona filas y `NOT IN` las conserva; es una deducción de la definición de pertenencia de SQL Procedure p. 394.
2. Valores repetidos en la subconsulta no duplican filas externas; se prueba con `IN` booleano.
3. Referencia al alias de la consulta externa se rechaza como correlación no soportada.
4. Valor faltante en el operando externo o en la columna proyectada no produce una equivalencia inventada: se rechaza.
5. Tabla no disponible, proyección de varias columnas o consulta agregada/con varias fuentes se rechaza con `NoSoportadoEnInterprete`.

---

### Tarea 1: resolver subconsultas de pertenencia en el anillo B

**Archivos:**
- Modificar: `src/sgm/migrar/interprete.py`
- Añadir: `src/sgm/migrar/interprete_subconsultas.py`
- Modificar: `src/sgm/ir/lower_sql_flow.py`
- Modificar: `tests/unit/test_migrar_interprete.py`
- Modificar: `tests/unit/test_migrar_corpus_anillo_b.py`
- Modificar: `tests/corpus/migrar_pendientes.yaml`
- Modificar: `PROGRESS.md`
- Modificar: `docs/plan-reescritura/plan-migrador-general.md`

**Interfaces:**
- Extender `_filtrar(filas: list[dict], expresion: str, tablas: dict | None = None)`; el parámetro opcional conserva los filtros existentes sin subconsultas.
- Añadir `interprete_subconsultas.preparar(...)`, que consume la expresión `exp.Subquery`, las filas externas y `dict[str, list[dict]]`, y devuelve la expresión con listas de literales ya verificadas.
- Añadir `interprete_subconsultas.orden_de_ejecucion(...)`, que añade dependencias hacia productores de tablas referenciadas por subconsultas sin cambiar las aristas persistidas en la IR.
- Pasar `tablas` desde `_pasos` y `_ramas` al filtro.
- Producir las mismas filas que el SAS de referencia para los casos L2-06, L2-07 y L2-15.

- [x] **Paso 1: retirar los `xfail` de los tres casos y escribir pruebas de límites.** Añadidas `test_in_subconsulta_sin_coincidencias_devuelve_cero_filas`, `test_not_in_subconsulta_sin_coincidencias_conserva_las_filas`, `test_in_subconsulta_con_duplicados_no_duplica_filas`, `test_in_subconsulta_correlacionada_se_rechaza`, `test_in_subconsulta_con_faltantes_se_rechaza`, `test_in_subconsulta_de_varias_columnas_se_rechaza`, `test_in_subconsulta_con_fuente_no_verificable_se_rechaza`, `test_in_subconsulta_con_agregado_se_rechaza`, `test_in_subconsulta_con_varias_fuentes_se_rechaza` y `test_select_alias_star_en_join_proyecta_solo_el_lado_seleccionado`.
- [x] **Paso 2: confirmar RED.** Los tres casos de corpus fallaron primero por `IN con SELECT`; tras la primera implementación, `l2_15` expuso que el lowerer perdía el alias externo y que `SELECT t.*` se reducía a `{'*': None}`. La prueba específica de `alias.*` falla con esa fila ficticia.
- [x] **Paso 3: implementar el resolvedor acotado.** Valida AST `SELECT`, fuente única de tabla, columna proyectada simple, cláusulas admitidas, alias locales, existencia del dataset/columnas y ausencia de faltantes; evalúa el `WHERE` con el filtro existente.
- [x] **Paso 4: conectar preservación de alias, dependencias y proyección.** El lowerer conserva calificadores dentro de filtros con subconsultas. El intérprete ordena versiones derivadas mediante evidencia de línea, pasa el contexto a filtros normales y ramas, y resuelve `alias.*` desde el lado correspondiente del join; rechaza versiones ambiguas y lados vacíos sin esquema.
- [x] **Paso 5: confirmar GREEN.** `uv run pytest -q tests/unit/test_migrar_corpus_anillo_b.py tests/unit/test_migrar_interprete.py`: **103 pasaron y 1 xfail**. Los tres casos L2 pasan contra `esperado/` sin modificar el oráculo; el xfail restante es el alias de auto-unión.
- [x] **Paso 6: registrar estado.** `PROGRESS.md` y el plan maestro documentan alcance, límites, métricas y que el traductor Talend sigue parcial. No se suma crédito mientras falten los demás casos de aceptación de MG-P10-01.
- [x] **Paso 7: verificar cierre.** Suite completa: **2648 pasaron, 26 omitidas y 139 xfailed**; Ruff limpio; reglas válidas; `git -c core.whitespace=cr-at-eol diff --check` limpio.
- [x] **Paso 8: commit local.** `hito 130: interpretar IN con subconsulta no correlacionada`.
- [x] **Paso 9: atender revisión independiente.** Pasan las regresiones de productor anterior/futuro y `alias.*` de un lado vacío. El orden por versión de tabla y el rechazo sin esquema están implementados. Suite completa: **2650 pasaron, 26 omitidas y 139 xfailed**; Ruff, reglas y diff check limpios.
