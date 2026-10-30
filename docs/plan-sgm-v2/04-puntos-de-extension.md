# Puntos de extensión

sgm crece con archivos de datos, no con código. Cada tipo de archivo tiene una carpeta, un esquema en `schemas/rules/`, un dueño y una prueba obligatoria. `sgm rules validate` revisa todos.

Reglas comunes a todos los archivos de reglas:

- Un archivo por regla. El nombre del archivo es el `id`.
- Campos obligatorios: `id`, `kind`, `version`, `status` y `tests`.
- `version` es un entero que sube con cada cambio de comportamiento.
- `tests` apunta a uno o más casos en `tests/cases/`. Una regla sin caso no valida.
- Prohibido usar nombres de programas, tablas o columnas de un cliente. Se usan marcadores (`{by}`, `{data}`, `{text}`).
- La versión del conjunto de reglas es el hash de `rules/`. Cambia sola cuando cambia cualquier archivo y obliga a recompilar los archivos afectados.

## Tabla general

| Tipo | Carpeta | Dueño | Cierra el motivo |
| --- | --- | --- | --- |
| PROC | `rules/sas/procs/` | Joseph | `PROC_NO_SOPORTADO` |
| Sentencia global | `rules/sas/statements/` | Joseph | `SENTENCIA_NO_SOPORTADA` |
| Función SAS | `rules/sas/functions/` | Joseph | `FUNCION_NO_MAPEADA` |
| Informats y formatos | `rules/sas/informats.yaml` | Joseph | `TIPO_DESCONOCIDO` (desde código) |
| Fontanería | `rules/sas/plumbing.yaml` | Joseph | Pasos que no se migran |
| Intrínseco | `rules/sas/intrinsics/` | Joseph | `INTRINSECO_PARCIAL` |
| Mapeo a componente | `rules/mapping/` | Byron | `COMPONENTE_NO_CATALOGADO` |
| Ruteo de huecos | `rules/routing.yaml` | Andres | Dueño de cada motivo |
| Motores | `env/engines.json` | Byron | Ubicación en base |
| Proyecto | `env/project.json` | Byron | Políticas del proyecto |
| Externos | `env/externals.json`, `env/externals/` | Byron | `INCLUDE_EXTERNO` |
| Esquemas | `env/schemas/` | Byron | `TIPO_DESCONOCIDO` (desde la base) |
| Caso de prueba | `tests/cases/` | Quien cierra el hueco | Todos |

## PROC

Bajada declarativa de un PROC a operaciones de la IR. Sirve para PROCs cuya semántica es una secuencia fija de operaciones. Los que necesitan lógica (por ejemplo `proc transpose` con `id` y `idlabel`) pueden empezar en YAML como `parcial` y pasar a código si hace falta.

```yaml
id: proc-sort-nodupkey
kind: proc
version: 1
status: soportado
proc: sort
match:
  options:
    nodupkey: true
bind:
  input: "{option.data}"
  output: "{option.out | option.data}"
  keys: "{statement.by}"
ops:
  - op: sort
    keys: "{keys}"
  - op: dedup
    keys: "{keys}"
    keep: first
notes:
  - "SAS conserva la primera fila de cada clave según el orden de entrada."
tests:
  - tests/cases/proc-sort-nodupkey
```

## Sentencia global

Qué hacer con sentencias que no son pasos: `title`, `footnote`, `ods`, `options`, `filename`, `dm`, etc.

```yaml
id: stmt-title
kind: statement
version: 1
status: reemplazado
statement: title
action: plumbing           # plumbing, context, set_variable, unsupported
not_migrated_note: "Título de reporte de SAS; no tiene equivalente en un Job batch."
tests:
  - tests/cases/stmt-title
```

## Función SAS

Una entrada por función, con su traducción a SQL por dialecto y a Java para `tMap`. La semántica de valores faltantes se escribe siempre.

```yaml
id: fn-substr
kind: function
version: 2
status: soportado
sas: substr
args:
  - { name: text, type: String }
  - { name: start, type: Integer }
  - { name: length, type: Integer, optional: true }
returns: String
sql:
  impala: "substr({text}, {start}, {length})"
  oracle: "substr({text}, {start}, {length})"
java: "{text} == null ? null : {text}.substring({start} - 1, {length} == null ? {text}.length() : Math.min({text}.length(), {start} - 1 + {length}))"
missing: "Si text es faltante, el resultado es faltante."
notes:
  - "SAS cuenta posiciones desde 1; Java desde 0."
tests:
  - tests/cases/fn-substr
```

Si una función no tiene forma segura en un dialecto, se omite esa clave. La pasada 10 deja la expresión pendiente y el componente sigue siendo `tMap` o el del motor.

## Informats y formatos

```yaml
id: informats
kind: informats
version: 3
status: soportado
entries:
  - pattern: "^(\\d+)\\.$"            # w.
    type: Long
    when: "w <= 18"
  - pattern: "^(\\d+)\\.(\\d+)$"      # w.d
    type: BigDecimal
  - pattern: "^yymmdd(6|8|10)\\.$"
    type: Date
    java_pattern: "yyyyMMdd"
  - pattern: "^\\$(\\d+)\\.$"         # $w.
    type: String
    length: "{1}"
tests:
  - tests/cases/informats-basicos
```

## Fontanería

Patrones de sentencias que no se migran, con lo que las reemplaza en Talend.

```yaml
id: plumbing
kind: plumbing
version: 4
status: reemplazado
entries:
  - match: { statement: x, background: true }
    note: "Comando de sistema de la sesión SAS."
    talend_equivalent: "Ninguno, o tSystem si se confirma que es necesario."
  - match: { proc: delete, library: WORK }
    note: "Limpieza de WORK."
    talend_equivalent: "No aplica: Talend no materializa WORK."
  - match: { call: sleep }
    note: "Espera activa."
    talend_equivalent: "Ninguno."
tests:
  - tests/cases/plumbing-basico
```

## Intrínseco

Patrones de infraestructura reconocidos por estructura, que se reemplazan por una sola operación. Los simples se describen en YAML; los complejos (como la carga externa con sesiones paralelas) viven en `src/sgm/passes/intrinsics/` y se registran aquí con `implementation`.

```yaml
id: external-load
kind: intrinsic
version: 5
status: soportado
implementation: sgm.passes.intrinsics.external_load
features_required:
  - system_command_background
  - process_wait_loop
features_absorbed:
  - parallel_sessions
  - chunking_firstobs_obs
  - workpath_lets
  - row_count_into
  - chunk_cleanup
  - log_error_scan
replaces_with:
  op: external_load
  params: { verify_count: true }
tests:
  - tests/cases/external-load-completo
  - tests/cases/external-load-renombrado
```

## Mapeo a componente

Operación de la IR a componente de Talend, con nivel en la escalera y alternativas para las decisiones.

```yaml
id: map-aggregate
kind: mapping
version: 2
status: soportado
match:
  op: aggregate
  placement: flow
level: 2                       # 1 base, 2 específico, 3 tMap, 4 tJavaRow, 5 tJava
emit:
  - component: tAggregateRow
    params:
      GROUPBYS: "{group_by}"
      OPERATIONS: "{aggregations}"
confidence: alta
alternatives:
  - id: aggregate-in-db
    when: "las entradas pueden cargarse en la base"
    emit:
      - component: "{engine.row}"
        params: { QUERY: "{sql}" }
tests:
  - tests/cases/map-aggregate
```

El componente debe existir en `rules/talend/components.json` o en `official-component-inventory.json`; si no, `validate` falla.

## Ruteo de huecos

```yaml
id: routing
kind: routing
version: 1
status: soportado
owners:
  PARSE_ERROR: joseph
  SENTENCIA_NO_SOPORTADA: joseph
  PROC_NO_SOPORTADO: joseph
  MACRO_DINAMICA: joseph
  INCLUDE_EXTERNO: byron
  FUNCION_NO_MAPEADA: joseph
  TIPO_DESCONOCIDO: byron
  COMPONENTE_NO_CATALOGADO: byron
  SEMANTICA_DUDOSA: andres
  INTRINSECO_PARCIAL: joseph
fix_with:
  PROC_NO_SOPORTADO: "rules/sas/procs/"
  SENTENCIA_NO_SOPORTADA: "rules/sas/statements/"
  FUNCION_NO_MAPEADA: "rules/sas/functions/"
  TIPO_DESCONOCIDO: "env/schemas/ o rules/sas/informats.yaml"
  INCLUDE_EXTERNO: "env/externals/ o env/externals.json"
  COMPONENTE_NO_CATALOGADO: "rules/mapping/"
  INTRINSECO_PARCIAL: "rules/sas/intrinsics/"
tests:
  - tests/cases/routing
```

## Archivos de entorno

`env/engines.json`:

```json
{
  "dsn": { "IMPALA": "impala", "IMPALAC": "impala", "IMPALAP": "impala" },
  "libraries": { "GCIDLL01": "folder" },
  "db_schemas": {
    "proceso_vspc_finanzas": "impala",
    "resultados_vspc_clientes": "impala",
    "s_canales": "impala"
  },
  "dialects": { "impala": "hive" }
}
```

`env/project.json`:

```json
{
  "placement_strategy": "push_to_db",
  "target_engine": "impala",
  "work_table_prefix": "sgm_tmp_",
  "reports": "discard",
  "max_components_per_job": 200
}
```

`env/externals.json` (solo lo que el código demuestra):

```json
{
  "activenodelzcode.sas": { "defines": ["m_ambiente"], "as_context": true }
}
```

`env/schemas/<esquema>.json` (lo genera `sgm env import-describe`):

```json
{
  "schema": "proceso_vspc_finanzas",
  "source": "DESCRIBE en Impala",
  "captured": "AAAA-MM-DD",
  "tables": {
    "<tabla>": [
      { "name": "<columna>", "type": "String", "length": null, "nullable": true }
    ]
  }
}
```

## Caso de prueba

`tests/cases/<id>/expected.yaml`:

```yaml
description: "PROC SORT con NODUPKEY por una clave"
input: input.sas
env: default                    # o una carpeta env/ propia del caso
expect:
  no_exceptions: true
  gaps: []                      # firmas de huecos esperados; vacío si se cierra
  operators:
    - { kind: sort, status: soportado }
    - { kind: dedup, status: soportado }
  components:
    - tSortRow
    - tUniqRow
  max_tjava: 0
```

Una prueba genérica recorre `tests/cases/` y compara cada `expected.yaml`. Agregar un caso no requiere escribir Python.

## Agregar un tipo nuevo de punto de extensión

Si un hueco no encaja en ningún tipo de esta lista:

1. Andres decide con el dueño del motivo si es un tipo nuevo o código.
2. Si es tipo nuevo: esquema en `schemas/rules/`, carga en `src/sgm/rules/`, entrada en `rules/routing.yaml`, sección en este documento y un caso de prueba.
3. Se anota en `05-contratos.md` porque cambia el formato de reglas.
