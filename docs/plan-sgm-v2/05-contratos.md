# Contratos

Lo de este documento no cambia sin acuerdo de los tres. Un cambio de contrato va en un commit propio, con el título `contrato: <qué cambia>`, y actualiza este archivo en el mismo commit.

## 1. Modelos de la IR

Archivo: `src/sgm/ir/models.py`. Campos mínimos que no se quitan ni se renombran:

| Modelo | Campos |
| --- | --- |
| `Evidence` | `file`, `line_start`, `line_end`, `label` |
| `Column` | `name`, `type`, `length`, `source` |
| `Operator` | `id`, `kind`, `params`, `placement`, `schema`, `evidence`, `status`, `signature`, `notes` |
| `Edge` | `src`, `dst`, `dataset`, `materialize` |

Valores cerrados:

- `status`: `soportado`, `parcial`, `reemplazado`, `hueco`. No existe "sin clasificar".
- `placement`: `db:<motor>`, `flow` o vacío antes de la pasada 4.
- `Column.source`: `catalog`, `file_header`, `code`, `derived`, `unknown`.
- `Column.type`: `String`, `Integer`, `Long`, `Double`, `BigDecimal`, `Date`, `Boolean` o vacío.

Se pueden **agregar** campos opcionales sin acuerdo, avisando en el commit.

## 2. Firma

- La firma es la llave de overrides, huecos, plantillas y caché. Nunca un id de operador.
- Se calcula sobre la forma normalizada: nombres de tablas, columnas, literales y sufijos variables se reemplazan por marcadores.
- Formato legible: `<familia>:<tipo>:<rasgos>`, por ejemplo `proc:transpose:id+var`, más un hash corto para unicidad.
- **Cambiar el algoritmo de firma es un cambio de contrato:** invalida overrides y huecos guardados. Requiere un script de migración de la base de overrides.

## 3. Motivos de hueco

Lista cerrada: `PARSE_ERROR`, `SENTENCIA_NO_SOPORTADA`, `PROC_NO_SOPORTADO`, `MACRO_DINAMICA`, `INCLUDE_EXTERNO`, `FUNCION_NO_MAPEADA`, `TIPO_DESCONOCIDO`, `COMPONENTE_NO_CATALOGADO`, `SEMANTICA_DUDOSA`, `INTRINSECO_PARCIAL`.

Agregar un motivo requiere: entrada en `rules/routing.yaml` con dueño y `fix_with`, y un caso de prueba.

## 4. Formato de reglas

- Esquemas en `schemas/rules/<tipo>.schema.json`.
- Campos comunes obligatorios: `id`, `kind`, `version`, `status`, `tests`.
- Cambiar el esquema de un tipo de forma incompatible requiere migrar todos los archivos de ese tipo en el mismo commit.

## 5. Plan de salida

`<programa>.plan.json` es lo que consumirán la web y el emisor de Studio (fase 5). Estructura mínima:

```json
{
  "sgm_version": "x.y.z",
  "ruleset_hash": "…",
  "program": { "file": "…", "hash": "…" },
  "contexts": [ { "group": "…", "variables": { "…": { "DEV": "…", "TEST": "…", "PROD": "…" } } } ],
  "jobs": [
    {
      "name": "…",
      "subjobs": [ { "label": "…", "components": [ { "id": "…", "component": "tMap", "params": {}, "evidence": [], "status": "…", "pending": [] } ], "connections": [] } ],
      "children": []
    }
  ],
  "not_migrated": [ { "evidence": [], "note": "…", "talend_equivalent": "…" } ],
  "decisions": [ { "signature": "…", "options": [], "default": "…", "chosen": "…", "scope": "…" } ],
  "gaps": [ { "signature": "…", "reason": "…", "owner": "…", "fix_with": "…", "evidence": [] } ]
}
```

Agregar campos opcionales está permitido. Quitar o renombrar es cambio de contrato.

## 6. Overrides

- Alcances: `paso`, `archivo`, `proyecto`, `global`. Gana el más específico.
- Cada override guarda autor, motivo y fecha.
- Un override nunca se borra en silencio: si una regla nueva lo vuelve inaplicable, queda como decisión pendiente con la nota "el override anterior ya no aplica".

## 7. Comandos de la CLI

Estos comandos y sus opciones principales son estables, porque los usan el equipo, los agentes y la integración continua:

`compile`, `intake`, `metrics` (`--check`), `gaps list` (`--owner`, `--file`, `--top`), `decisions list`, `decisions set`, `rules validate`, `rules new`, `case new`, `explain`, `env import-describe`, `lineage`.

## 8. Reglas de trabajo

- Nada de nombres de programas o tablas del cliente en `src/` ni `rules/`. Lo vigila `test_no_script_specific_names`.
- Ningún secreto en el repositorio, en `out/` ni en `corpus/`. Lo vigila `test_security`.
- Código en inglés; documentación y mensajes en español.
- Commits pequeños, un tema por commit. Push solo a ramas propias; a `main` solo con revisión cruzada.
- MCP, API y web quedan fuera hasta la fase 5.
