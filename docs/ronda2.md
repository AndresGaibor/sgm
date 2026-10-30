# Prompt para el agente: sgm v2, ronda 2 (agrupación real)

Copia todo lo que está debajo de la línea y pégalo al mismo agente, o a uno nuevo que trabaje en el mismo repositorio.

---

## Contexto

Trabajas en `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2`. La ronda 1 terminó los hitos 0 a 11 (commits `2a45654` a `9b70d20`). Lee `AGENTS.md` y `PROGRESS.md` antes de empezar. Siguen vigentes todas las reglas de `AGENTS.md`: nada de MCP, nada de API ni web, no conectarse a bases, no inventar datos, no guardar secretos, no usar nombres de scripts de ejemplo en `src/` ni `rules/`, commits locales sin push, `PROGRESS.md` al cierre de cada hito.

El repositorio viejo ya no se toca ni se usa. No ejecutes `uv` dentro de él.

El lanzador `sgm.exe` está bloqueado por Windows; usa `uv run python -m sgm.cli ...`.

## El problema que resuelves

El objetivo de sgm es agrupar muchos pasos SAS en pocos componentes de Talend. La ronda 1 hace lo contrario:

- Corpus: 629 nodos SAS y 1.690 componentes (0,37 nodos por componente), 958 subjobs.
- `client_large.sas`: 610 nodos, 662 componentes, 49,8 % de `tJava`, 397 subjobs, 293 decisiones.

Causas probables, que debes confirmar en el hito R0:

1. **PROC SQL sobre WORK termina en `tJava`.** `client_large.sas` tiene 521 `PROC SQL` y unas 404 lecturas `FROM WORK.*`. SQL es lo más fácil de traducir; nunca debería terminar en `tJava`.
2. **Nada se ubica en la base.** Las tablas WORK nacen de archivos CSV o Excel, o de lecturas de Impala, así que la pasada 4 las deja en flujo y la pasada 5 no fusiona casi nada.
3. **La pasada 3 absorbe solo parte de la maquinaria de carga.** Los huecos 3 y 5 a 10 del top 10 (`%SYSFUNC(WORKPATH)`, `%SYSFUNC(COUNTW)`, `%SYSEVALF`, `SELECT ... INTO :`, `sessio&i`, `PROC CONTENTS ... _ALL_`) aparecen unas 30 veces cada uno: una vez por cada bloque de escritura a la LZ. Son parte de esa maquinaria y deberían haber desaparecido.
4. **Subjobs por nodo o etiqueta**, en vez de uno por componente conexo del flujo.

## Forma de trabajar

Igual que en la ronda 1: un hito a la vez, pruebas y ruff en verde, `PROGRESS.md`, commit local `ronda2 R<n>: <resumen>`. Si algo falla tres veces igual, anota el bloqueo y sigue con lo que no dependa de él.

**Regla nueva de esta ronda:** antes de cambiar una pasada, corre `sgm metrics` y guarda los números; después del cambio, vuelve a correrlo. Anota el antes y el después en `PROGRESS.md`. Un cambio que empeora la agrupación sin una razón escrita se revierte.

## Hitos

### R0. Diagnóstico (sin cambiar comportamiento)

1. Agrega a `sgm metrics` un desglose y guárdalo en `out/diagnostico.md`:
   - componentes por tipo de operador de la IR y por constructo SAS de origen (por ejemplo `proc_sql_work`, `data_step`, `proc_contents`),
   - `tJava` por constructo de origen,
   - por cada pasada: operadores creados, fusionados y quitados (sale de `PassLog`),
   - subjobs por motivo de corte,
   - decisiones por firma: total y firmas únicas.
2. Cambia la métrica principal: **pasos SAS por componente** (pasos, no nodos; un nodo de SAS Studio puede tener varios pasos). Conserva también la de nodos.
3. Escribe en `PROGRESS.md` qué causa confirmaste y con qué números. Si una de las cuatro causas de arriba no se confirma, dilo y explica la real.

### R1. Configuración de entorno y proyecto

Crea estos archivos de configuración, con su carga y validación en `src/sgm/catalog/`:

`env/engines.json`: mapea fuentes a motores.

```json
{
  "dsn": { "IMPALA": "impala", "IMPALAC": "impala", "IMPALAP": "impala" },
  "libraries": {},
  "db_schemas": {
    "proceso_vspc_finanzas": "impala",
    "resultados_vspc_clientes": "impala",
    "s_canales": "impala"
  }
}
```

Estos valores salen del propio código SAS: los DSN aparecen en `connect to impala (dsn=...)` y los esquemas en las consultas pass-through. No agregues otros que el código no muestre.

`env/project.json`: políticas del proyecto.

```json
{
  "placement_strategy": "push_to_db",
  "target_engine": "impala",
  "reports": "discard",
  "max_components_per_job": 200
}
```

`env/externals.json` y la carpeta `env/externals/`: para `%include` de archivos fuera del repositorio.

- Si el archivo existe en `env/externals/` con el mismo nombre, se lee como cualquier fuente.
- Si no existe pero está declarado en `externals.json` (por ejemplo `{"activenodelzcode.sas": {"defines": ["m_ambiente"], "as_context": true}}`), sus variables pasan a variables de contexto y **no** generan hueco.
- Si no está ni declarado ni presente, sigue siendo hueco, como ahora.

Declara en `externals.json` solo lo que el código demuestra. Por ejemplo, `m_ambiente` se usa justo después del `%include` de `activenodelzcode.sas`, así que se puede declarar. No declares el contenido interno del archivo.

Pruebas: cada archivo se valida; un `%include` declarado no genera hueco; uno no declarado sí.

### R2. Contextos desde macros de ambiente

Detecta por estructura una macro cuyo cuerpo es solo una cadena `%if &X eq <literal> %then %do; %let Y=<literal>; %end; %else %if ...`. Esa macro es un selector de ambiente: crea un grupo de contexto con una variable por cada `Y`, un contexto por cada literal de `X`, y los valores tomados del código. En `client_large.sas` y `client_poc.sas` debe salir el contexto de `lz_dsn` con sus tres valores.

La expansión de ambas ramas de un `%if` no constante (decisión de la ronda 1) **no** se aplica a esta macro: aquí cada rama es un contexto, no código.

Prueba: fixture sintético con un selector de ambiente de nombres aleatorios produce el grupo de contexto correcto.

### R3. La pasada 3 absorbe toda la maquinaria de carga

Amplía `p03_intrinsics` para que la **región de carga** incluya, por estructura:

1. La macro de carga detectada hoy (comandos de sistema en segundo plano y espera con conteo de procesos).
2. Todas las macros que esa macro invoca, de forma transitiva.
3. El troceo en sesiones paralelas: bucles con `signon`, `%syslput`, `rsubmit ... wait=no`, `endrsubmit`, `waitfor`, `signoff`, incluidas las referencias `sessio&i`.
4. Las sentencias de preparación cuyas variables de macro **solo** se consumen dentro de la región: `%let` con `%sysfunc(pathname(...))`, `WORKPATH`, `countw`, `%sysevalf`, `select count(*) into :`, `proc contents ... out=` para listar columnas.
5. El borrado de los trozos y la revisión de logs.
6. El conteo de origen y destino de la carga pasa a una sola verificación opcional en el `external_load` (`params.verify_count = true`), no a operadores separados.

Todo eso se reemplaza por un único `external_load` con evidencia de todas las líneas absorbidas.

Criterio de salida: en `client_large.sas` y `client_poc.sas`, las firmas de huecos de `WORKPATH`, `COUNTW`, `SYSEVALF`, `SELECT ... INTO :` de conteo, `sessio&i` y `PROC CONTENTS ... _ALL_` bajan a 0. Prueba obligatoria con la maquinaria completa renombrada con nombres aleatorios.

### R4. PROC SQL nunca termina en tJava

1. Agrega la dependencia `sqlglot` y anótala en "Decisiones".
2. Preprocesa las particularidades de SAS SQL antes de parsear: `calculated <col>`, operadores `eq ne gt lt ge le`, `contains`, `||`, `input()`, `put()`, `monotonic()`, `into :var`, nombres `lib.tabla` y opciones de dataset entre paréntesis.
3. Con el árbol de sqlglot:
   - Si el operador queda **en base**: genera SQL en dialecto de Impala (`sqlglot` dialecto `hive` o `impala` si existe en la versión instalada) y úsalo en las pasadas 4 y 5.
   - Si queda **en flujo**: baja a operadores lógicos: `where` a `filter`, `join ... on` a `join`, `group by` y agregados a `aggregate`, `having` a `filter` después de `aggregate`, `select` de expresiones a `derive`, `distinct` a `dedup`, `order by` a `sort`, `union` a `union`, `case` a `derive`.
   - `select ... into :var` va a `set_variable` (`tSetGlobalVar` o `tFlowToIterate`), no a `tJava`.
4. Si una función de SAS no tiene traducción, la **expresión** queda pendiente con `FUNCION_NO_MAPEADA`, pero el **componente** sigue siendo `tMap`, `tAggregateRow` o el del motor. Nunca `tJava`.
5. Solo un `PROC SQL` que no se puede parsear queda como hueco `PARSE_ERROR`.

Criterio de salida: 0 `tJava` cuyo origen sea `PROC SQL`, en todo el corpus. Pruebas: un caso por cada construcción de la lista del punto 3.

### R5. Estrategia de ubicación "cargar una vez, calcular en la base"

Con `placement_strategy = "push_to_db"`:

1. Cada fuente de archivo (CSV, Excel) cuyos datos terminan unidos con datos de la base, o escritos en la base, recibe **un solo** `external_load` al inicio, hacia una tabla de trabajo en el motor destino. Nombre de la tabla: prefijo configurable más una firma corta, nunca el nombre del script.
2. Desde ahí, toda operación expresable en SQL se ubica en la base, incluidas las que en SAS leen `WORK.*`.
3. Lo que no es expresable en SQL (lógica con estado, `retain`, `first.`/`last.` complejos) queda en flujo, y la pasada 4 agrega los cruces necesarios.
4. Las salidas a archivo (exportaciones CSV) se leen de la base al final con un `read` y un `write_file`.

Con `placement_strategy = "flow"`, se comporta como hoy.

Después corre la pasada 5. En `client_large.sas` deberían quedar cadenas largas de SQL fusionado.

Pruebas: fixture con CSV, unión con tabla de la base y exportación: con `push_to_db` sale un `external_load`, un `exec_sql` fusionado y un `write_file`; con `flow` sale el equivalente en componentes de flujo.

### R6. Reportes y PROC CONTENTS

1. `PROC CONTENTS` cuyo resultado solo alimenta variables de macro ya quedó absorbido en R3 o es fontanería. Si se imprime, aplica la política de reportes.
2. `PROC PRINT`, `PROC REPORT` y `PROC CONTENTS` impresos siguen `reports` de `env/project.json`: `discard` (por defecto) los manda a `not_migrated` con la nota "reporte de diagnóstico, no se migra"; `log` usa `tLogRow`; `csv` usa `tFileOutputDelimited` con ruta como contexto.

Criterio: con `discard`, las firmas de `PROC PRINT` y `PROC CONTENTS` desaparecen del top de huecos.

### R7. Tipos desde el propio código

Amplía `p09_schemas` con una fuente nueva, `source = "code"`:

- `input(x, w.)` y `input(x, w.d)`: numérico (`Long` si `d` no existe y `w <= 18`, `BigDecimal` si hay decimales, `Double` en otro caso).
- `input(x, yymmdd8.)` y otros informats de fecha: `Date`.
- `format`, `length` e `informat` en DATA step: tipo y longitud.
- `put(x, w.)`: `String` de largo `w`.
- `cast(... as ...)` en SQL: el tipo del cast.
- Literales y operaciones aritméticas: numérico.

Prioridad: catálogo de entorno, luego encabezado de archivo, luego código, luego derivado. Un tipo que no sale de ninguna fuente sigue siendo `TIPO_DESCONOCIDO`.

Prueba: el DATA step de tipado de columnas `VARn` del fixture grande produce tipos para todas las columnas que convierte.

### R8. Partición por componente conexo

1. Un subjob es un componente conexo de conexiones de filas (`row`). Ya no se crea un subjob por nodo ni por etiqueta.
2. Los `exec_sql` sin conexión de filas se encadenan con `OnSubjobOk` dentro del mismo job; cuentan como subjobs, pero ya fusionados por la pasada 5.
3. La etiqueta de SAS Studio pasa a ser la **etiqueta del componente**, no un límite.

Criterio: en `client_large.sas`, los subjobs bajan al menos a la mitad de 397.

### R9. Decisiones agrupadas

1. `sgm decisions list` agrupa por firma y muestra cuántos operadores y archivos la comparten.
2. Las métricas reportan decisiones totales y **firmas únicas**. La que importa para el usuario es la segunda: es el número de veces que tiene que elegir.

### R10. Verificación y entrega

1. Pruebas y ruff en verde. Corre `sgm compile` y `sgm metrics` sobre todo el corpus.
2. Abre la guía de `client_large.sas` y comprueba a mano que el flujo se lee como un proceso de pocas etapas, no como una lista de cientos de pasos.
3. Busca secretos en `out/` y `tests/`: cero `pwencode` o `pass=` en claro.

Metas para `client_large.sas`. Si no se alcanzan, explica por qué con el diagnóstico de R0:

| Métrica | Ronda 1 | Meta ronda 2 |
|---|---|---|
| `tJava` | 49,8 % | 10 % o menos |
| `tJava` con origen `PROC SQL` | sin medir | 0 |
| Componentes frente a pasos SAS | más componentes que nodos | menos componentes que pasos SAS |
| Subjobs | 397 | 198 o menos |
| Huecos de la maquinaria de carga | 6 firmas en el top 10 | 0 |
| Decisiones | 293 totales | reportar firmas únicas |

## Entrega final

Reporte breve en español:

1. Hitos terminados y los que no, con el motivo.
2. Pruebas que pasan y estado de ruff.
3. Tabla de metas con el valor alcanzado en `client_large.sas`, `client_poc.sas` y el corpus completo.
4. Desglose de R0 antes y después: de dónde salen hoy los componentes y los `tJava` que quedan.
5. Top 10 de huecos nuevo.
6. Decisiones de diseño tomadas por tu cuenta.
7. Lo que necesitas del usuario.
8. Commits locales.

No hagas push. No actives MCP.
