# Plan del migrador general de SAS a Talend, hasta producción

Fecha: 5 de noviembre de 2026. Alcance decidido por el usuario (DC-01): **un migrador general**. Se le entrega
cualquier programa SAS y devuelve uno o varios Jobs de Talend bien hechos, con contextos, joblets, Job padre
e hijos, manejo de errores y registro. `client_large.sas` pasa a ser un caso de prueba más.

**Este es el plan maestro del repositorio (6 de noviembre de 2026).** Está escrito para que **otro agente
lo ejecute sin preguntar**. `ruta-a-produccion.md` queda subordinado: es el detalle de la pista del
programa grande y de la operación (F9), y su Fase 7 la reemplaza este documento. El corpus y el plan de
equivalencia están en `plan-corpus-y-equivalencia.md`. **Avance global: ver la sección 11b** (cerca de 20 %
de las horas de agente, con el método ahí).

## 0. Cómo usar este documento

### 0.1 Orden de lectura (30 minutos, obligatorio)
1. `AGENTS.md` del repositorio (reglas que no se negocian).
2. Esta página completa, en especial las secciones 1 a 4.
3. `docs/referencia/catalogo-sas.md` y `docs/referencia/sas/README.md` (qué guía SAS responde qué duda).
4. `C:\Users\USUARIO_BISOLUTION1\code\talend-mcp\docs\SAS-A-TALEND.md` (mapa de capacidades SAS a Talend
   ya probado en L5) y `docs\COBERTURA-POR-FAMILIA.md` (qué componentes están medidos).
5. `tools/corpus_lib/STUDIO.md` y `tools/corpus_lib/DIFERENCIAS.md` (cómo se ejecuta un Job y se compara).
6. Las entradas de `PROGRESS.md` de los hitos 60 a 101d: cada una trae un patrón que se repite aquí
   (leer una regla del SAS, traducirla a Talend, ejecutarla en Studio, compararla con un esperado
   independiente).

### 0.1b Principio de automatización total (instrucción directa del usuario)
**El migrador debe ser automático.** Se le entrega un programa SAS y devuelve los Jobs sin que nadie escriba YAML,
responda preguntas ni tome decisiones. Consecuencias que el agente debe respetar:

1. **Cero configuración obligatoria.** `sgm migrar programa.sas` (o una carpeta) funciona solo. Los YAML de
   `decisiones/` son opcionales y solo sirven para *cambiar* lo que el migrador decidió.
2. **Cada decisión la toma el migrador con una regla determinista y la deja escrita.** Si hay varias opciones
   válidas (nombre de un Job, cómo agrupar, dónde cortar un Job grande, cómo pasar datos entre Jobs, qué hacer
   ante un fallo parcial), el migrador aplica la regla por omisión de la sección 8 y registra en
   `decisiones-tomadas.md` qué eligió, por qué y cómo cambiarlo. **Nunca se detiene a preguntar.**
3. **Nada falla: se degrada con elegancia** (instrucción del usuario). El migrador **nunca aborta ni lanza una
   excepción hacia el usuario**, ni siquiera con un archivo ilegible, un operador raro o una configuración que
   falta. Cada operador se traduce en un bloque aislado: si uno falla, se omite, se documenta en `pendientes.md`
   (código, motivo, línea del SAS y, en el registro técnico, la causa) y el resto sigue. El código de salida es 0
   salvo uso incorrecto de la línea de comandos. Se llega **al máximo posible** y lo que falta lo completa después
   la persona.
4. **Lo que depende de configuración o credenciales queda listo para configurar, no bloquea.** Conexiones a bases,
   usuarios, contraseñas, servidores y rutas reales se crean como parámetros de contexto (grupos Default, DEV, QA
   y PROD, mismas claves) con valor vacío y un comentario de qué son, y el migrador escribe
   `configuracion-pendiente.md` con la lista exacta de lo que hay que rellenar y dónde. Si un Job necesita una base
   que no está, el Job se genera igual (no se ejecutará hasta configurarlo).
5. **Los valores que solo conoce una persona** (rutas reales de producción, usuarios, contraseñas, servidores) no
   se piden ni se inventan: se **deducen del SAS cuando están** (rutas de `LIBNAME`, `INFILE`, `FILENAME`,
   macrovariables) y, si no están, se generan como parámetros de contexto con nombre claro y valor vacío o de
   ejemplo, listados en `contextos/<entorno>.yaml` para completar al desplegar. El Job se genera igual.
6. **Las personas intervienen solo en tres momentos, fuera del código**: entregar los valores reales de cada
   entorno al desplegar, aceptar los resultados (UAT) y firmar el corte. Nada de eso detiene el desarrollo.

La sección 8 ya no es una lista de preguntas: es la lista de **reglas automáticas por omisión** del migrador, con la
persona opcional que podría cambiarlas.

### 0.2 Principio rector de velocidad (instrucción directa del usuario)
**Desarrollar rápido y no depender de pruebas lentas.** Talend Studio se usa cuando es rápido y sobre todo en
lote, no en cada cambio. Para eso el plan define una pirámide de pruebas (sección 6.1) con cuatro anillos:

| Anillo | Qué corre | Tiempo objetivo | Cuándo |
|---|---|---|---|
| A. Unitario y estático | `pytest -n auto`, `ruff`, validación estructural del `.item` generado, expresiones Java compiladas con `javac` suelto | menos de 90 s para todo | en cada cambio |
| B. Equivalencia sin Studio | intérprete de referencia en Python (la IR ejecutada) contra `esperado/` del corpus | menos de 3 min para 500 casos | en cada cambio de traducción |
| C. Studio en lote | un solo arranque: todos los Jobs del cambio se copian, se compilan en un lote y se ejecutan con el arnés | 10 a 20 min por lote | por hito, no por línea |
| D. Nocturno completo | todo el corpus por el traductor y por Studio, informe de regresión | 1 a 2 h | cada noche |

Reglas de velocidad: nunca ejecutar Studio para algo que se pueda probar en A o B; agrupar los Jobs de varios
casos en una sola compilación; reutilizar el mismo árbol de trabajo; no repetir corridas completas para
verificar un cambio de documentación.

### 0.3 Demos y simuladores (autorizado: créalos)
Si algo falta para probar (una base de datos, un Impala, un FTP, un SMTP, datos), **se crea un simulador local**.
Ya existen: Impala 4.5.3 y Postgres en contenedores (`tools/contenedores/`), generadores de datos
(`tools/simular_insumos.py`, `tools/simular_productos.py`, `tools/corpus_datos/`) y el servidor SMTP de pruebas
de talend-mcp (`scripts/l5/smtp-sink.ts`). Docker está disponible. Cada simulador debe levantarse con un
solo comando y documentarse en `tools/contenedores/README.md`. Un simulador nunca contiene datos reales ni
secretos.

### 0.4 Reglas de oro (resumen; la fuente es AGENTS.md)
- **MCP y CLI de Talend: permitidos, con una separación** (instrucción del usuario del 5 de noviembre de 2026,
  ver la sección 4.1 y la decisión MG-D11). El núcleo de `sgm` escribe `.item` directamente y funciona sin Studio ni
  MCP; el MCP o la CLI `talend` de `talend-mcp` se usan como **backend opcional de verificación, compilación en
  lote, construcción y ejecución**. El usuario lo autorizó sin condiciones y la regla 1 de `AGENTS.md` ya se
  actualizó (5 de noviembre de 2026).
- Sin API web ni frontend. Sin conexión a bases desde `sgm` (los contenedores son solo para probar Jobs generados).
- Nada de nombres de scripts del cliente en `src/` ni `rules/`. Las reglas se basan en estructura.
- Ninguna equivalencia sin fuente: cada regla cita guía y página (SAS) o prueba ejecutada. Si no hay
  equivalencia segura, se emite `Pendiente:` con motivo; **nunca se inventa**.
- Archivos de 300 líneas como máximo. Identificadores en inglés; comentarios y mensajes en español.
- No se guardan secretos. No se borran ni debilitan pruebas.
- Dependencias permitidas: `networkx`, `typer`, `pyyaml`, `pydantic`; dev `pytest`, `pytest-xdist`, `ruff`.
  Cualquier otra (por ejemplo `sqlglot`) requiere la decisión MG-D02 de la sección 8.
- Un commit por hito: `hito N<letra>: resumen`, con `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.
  Numeración: cada serie lleva su letra. Esta usa la letra `m`. No se usa `--amend` ni `rebase` sobre commits ajenos.

## 1. Definición de "100 %" (criterios medibles)

Ningún migrador de SAS traduce el 100 % de todos los programas posibles (hay `CALL EXECUTE`, `DS2`, modelos
estadísticos, código generado en tiempo de ejecución). Lo que sí se puede exigir, y es lo que se mide aquí:

| Criterio | Definición | Cómo se mide | Meta de producción |
|---|---|---|---|
| C1 Cobertura declarada | Existe una lista pública y generada automáticamente de construcciones SAS soportadas, parciales y no soportadas, cada una con su motivo | `sgm cobertura` genera `docs/cobertura.md` desde las reglas y el corpus | 100 % de las construcciones que aparecen en el corpus y en los programas reales están clasificadas |
| C2 Traducción completa o explícita, y sin fallos | Para cualquier programa, cada paso queda traducido o aparece en el informe de pendientes con su motivo; **nunca se omite en silencio** | propiedad: pasos del SAS igual a pasos traducidos más pasos pendientes; y robustez: `sgm migrar` termina con código 0 y escribe sus archivos sobre **cada** programa del repositorio (189) y sobre entradas basura (archivo vacío, binario, SAS truncado) | 100 % |
| C3 Equivalencia verificada | Cada construcción soportada tiene casos del corpus cuyo resultado en Talend coincide con un esperado independiente | arnés de Studio y anillo B | 100 % de los casos `traducible` pasan; cero regresiones |
| C4 Calidad de los Jobs | Jobs legibles y mantenibles: padre e hijos, joblets para repetidos, contextos DEV/QA/PROD, nada fijo en el código, errores y registro, sin secretos | lista de verificación automática (sección 7) sobre cada salida | 100 % de la lista en cada programa del corpus |
| C5 Reproducible | La misma entrada da exactamente los mismos bytes | prueba de determinismo | 100 % |
| C6 Operable | Instalable en una máquina limpia, con CLI estable, versión, registro de cambios, guía y soporte | paquete, guía y prueba en máquina limpia | cumplido |
| C7 Producción | Piloto con programas reales del cliente, corrida paralela con SAS, corte firmado | protocolo de la fase P14 | firmado por Negocio y Tecnología |

**Definición de "listo para producción":** C1 a C6 cumplidos por la máquina y C7 firmado por personas.

## 2. Estado actual medido (5 de noviembre de 2026)

> Foto de partida, antes de `sgm migrar`. Varias filas (`sgm talend` sobre otro programa, joblets,
> «0 traducidas por un traductor automático») están superadas por los hitos 103m a 107; el estado de
> hoy es el de las secciones «Estado» de cada fase y el de la sección 11b.

| Área | Estado | Evidencia |
|---|---|---|
| Analizador de SAS (frontend) | Existe: tokens, pasos, DATA step, `PROC SQL`, macros, `RSUBMIT`; analiza 189 programas del repositorio | `src/sgm/frontend/`, `out/metrics.json` |
| Modelo de flujo y linaje | Existe | `src/sgm/flow/`, `lineage.py` |
| IR y pases (grafo, fusión SQL, plantillas, esquemas, componentes) | Existe, con 10 pases; origen de la guía de migración en Markdown, no de Jobs | `src/sgm/ir/`, `src/sgm/passes/` |
| Expresiones SAS a Java | Parcial: 4 archivos y 23 funciones en la tabla | `src/sgm/expressions/talend_*.py` |
| Escritor de `.item` y `.properties` | Existe, con 25 plantillas sacadas de Jobs guardados por Studio | `src/sgm/talend_item/` |
| Traductor de reglas a Jobs | **Solo para `client_large.sas`**, con módulos y YAML específicos del programa | `proceso/reglas_*.py`, `decisiones/` |
| `sgm talend` sobre otro programa | **Falla** (exige `decisiones/<programa>.agrupacion.yaml`) | probado sobre `l2_01` |
| `sgm diseno` sobre otro programa | Corre y da 0 joblets, 0 nodos | probado sobre `l2_01` |
| Joblets | **No se generan**; nunca se validó crearlos ni usarlos en Studio 8.0.1 | plan R3-01 |
| Contextos | Parciales: grupos Default y periodo; DEV/QA/PROD sin cerrar | R4 |
| Corpus de equivalencia | 117 casos (L0 a L6 y L8), 3 mecanismos independientes de esperado | `tests/corpus/` |
| Arnés de ejecución en Studio | Existe y funciona | `tools/corpus_studio.py` |
| Cobertura del corpus | 206 construcciones distintas, 93 en casos `traducible`, 0 traducidas por un traductor automático | `tools/tablero.py` |
| Producción | No iniciada | F9 |

Hallazgos de Studio 8.0.1 que condicionan el diseño (todos ejecutados): `tUnite` no compila (usar `APPEND`
secuencial u otra unión); `tHashOutput` no se comparte entre Jobs; `DIE_ON_ERROR` vale `false` por omisión en
los lectores; un `tAggregateRow` con dos salidas principales entrega vacío a la segunda; `tUniqRow` exige el
esquema también en el bloque FLOW; `tFileInputExcel` exige PASSWORD no vacío en formato 2007; `tDie` en un
Prejob necesita `EXIT_JVM=true`; Studio cachea Jobs por id (usar nombre nuevo por intento); `talend_job_execute`
no carga contextos (exportar el Build Job y ejecutar el lanzador); un diálogo modal "Network Issue" bloquea el
puente.

## 3. Fuentes de conocimiento (qué consultar para cada duda)

### 3.1 SAS (`docs/referencia/sas/`, texto buscable con `Grep` y páginas en `.INDEX.md`)

| Duda | Guía | Archivo |
|---|---|---|
| Qué hace una sentencia del DATA step | Statements Reference | `lestmtsref.txt` |
| Cómo se ejecuta el DATA step (PDV, ciclo, `BY`, `FIRST.`/`LAST.`, `MERGE`, `RETAIN`, arrays) | Programmer's Guide: Essentials | `lepg.txt` |
| Reglas del lenguaje: faltantes, comparación de texto, fechas, `WHERE`, `BY` | Language Reference: Concepts | `lrcon.txt` |
| Qué hace una función y qué devuelve con faltantes | Functions and CALL Routines | `lefunctionsref.txt` |
| Formatos e informats | Formats and Informats | `leforinforref.txt` |
| Opciones de dataset (`KEEP=`, `DROP=`, `RENAME=`, `WHERE=`, `OBS=`, `FIRSTOBS=`) | Data Set Options | `ledsoptsref.txt` |
| Opciones del sistema que cambian resultados (`MISSING=`, `MERGENOBY`, `VALIDVARNAME`, `YEARCUTOFF`) | System Options | `lesysoptsref.txt` |
| `PROC SQL`: joins, subconsultas, agregados, conjuntos, vistas, `INTO :macro` | SQL Procedure User's Guide | `sqlproc.txt` |
| Macros: `%let`, `%macro`, `%if`, `%do`, funciones de macro, citado | Macro Language Reference | `mcrolref.txt` |
| `PROC SORT`, `FREQ`, `MEANS`, `TRANSPOSE`, `IMPORT`, `EXPORT`, `FORMAT`, `DATASETS` | Procedures Guide | `proc.txt` |
| `RSUBMIT`, `SIGNON`, `PROC UPLOAD`/`DOWNLOAD` | SAS/CONNECT | `connref.txt` |
| Rutas, filerefs, ejecución en UNIX | Companion for UNIX | `hostunx.txt` |
| Grid, envío por lotes | Grid Computing | `gridref.txt` |

Método de consulta: `Grep` del término en el `.txt` correspondiente, luego leer el rango de líneas; la
página se cita en el comentario de la regla (`rules/sas/*`) y en el caso del corpus que la prueba.

### 3.2 Talend (en `C:\Users\USUARIO_BISOLUTION1\code\talend-mcp\docs\` y `sgm-v2\docs\referencia\talend\`)

| Duda | Dónde |
|---|---|
| Parámetros y esquema de un componente (35 familias, 1215 componentes) | `talend-mcp\docs\catalogo-componentes\<familia>.md` (por ejemplo `file.md`, `databases.md`, `custom-code.md`, `logs-errors.md`, `orchestration`) |
| Página oficial de 41 componentes de Studio 8.0 | `sgm-v2\docs\referencia\talend\catalogo\*.md` (verificada contra el catálogo en `VERIFICACION.md`) |
| Qué componente está medido a L4 (compila) y L5 (ejecuta) | `talend-mcp\docs\COBERTURA-POR-FAMILIA.md` y `testdata\cobertura-l4-*.csv` |
| Plan de componentes por prioridad | `talend-mcp\docs\plan-componentes\P01` a `P08`, `EXCEPCIONES.md`, `EMULADORES.md` |
| Cómo generar la plantilla XML de cualquier componente (855 de 1215 generan) | `talend-mcp\docs\component-template-generation.md` y la herramienta `talend_components_generate_template` |
| Reglas de configuración, errores y límites al crear Jobs | `talend-mcp\docs\guia-agente\02-reglas-de-configuracion.md`, `05-errores-limites-y-referencias.md` |
| Cómo verificar un Job (compila, ejecuta, busca `[WARN]`/`[ERROR]` aunque el código sea 0) | `talend-mcp\docs\guia-agente\04-verificacion-y-diagnostico.md`, herramienta `talend_job_verify` |
| Arnés de ejecución | `talend-mcp\docs\guia-agente\03-arnes-de-ejecucion.md` |
| Cómo funciona Studio por dentro (API, `.item`, builds, joblets) | `talend-mcp\docs\TALEND-STUDIO-INTERNALS.md`, `studio-internals\` |
| Diseño de Jobs, contextos y joblets (guía oficial R2026-09) | `sgm-v2\docs\referencia\talend\studio-guia-jobs-contextos.md` |
| Mapa de capacidades SAS a Talend ya probado (23 filas: `WORK`, recrear tabla, conciliación, paralelismo, correo, S3, reintentos, scheduler, macros a joblets) | `talend-mcp\docs\SAS-A-TALEND.md` |
| Brechas conocidas de Talend (joblets sin crear, rutinas, librerías) | `talend-mcp\docs\ROADMAP-DOMINIO-TALEND.md` |

### 3.3 El propio repositorio
`rules/sas/{functions,intrinsics,procs,catalogo,informats.yaml,sql-functions.json,sql-semantica.yaml}` ya
contienen reglas por función, informat y procedimiento; `rules/talend/` y `rules/mapping/` el mapeo a
componentes. **Antes de escribir una regla nueva, buscar si existe.**

## 4. Arquitectura objetivo

```text
programa.sas
  1. frontend         tokens, pasos, DATA step, PROC SQL, macros          (existe)
  2. expansión        macros estáticas, %include, constantes, parámetros  (nuevo, MG-P7)
  3. modelo semántico tablas, esquemas, tipos, columnas, librerías        (nuevo, MG-P1)
  4. plan lógico (IR) lectura, transformación, unión, agregado, orden,
                      duplicados, escritura, control                      (extiende ir/, MG-P1)
  5. traductor        por operador a subgrafo de componentes Talend       (nuevo, MG-P2 a P7)
  6. planificador     agrupa en Jobs, joblets, padre, contextos, límites  (nuevo, MG-P8)
  7. emisor           .item y .properties, contextos, layout, notas       (extiende talend_item/, MG-P9)
  8. informe          traza SAS a componente, pendientes, cobertura       (nuevo, MG-P11)
```

**Se reutiliza lo que ya existe.** `sgm compile` ya produce un `Plan` (`ir/models.py`) con operadores (`read_file`, `write_file`, `map`, `sort`...), candidatos de componente por reglas YAML (`rules/mapping/`), subjobs, joblets detectados y contextos (`compile.compile_file`). Hoy sus parámetros son de nivel de guía (por ejemplo `read_file` solo trae la ruta y el `derive` de un `SELECT` trae `assignments: []`) y no hay emisor de `Plan` a `.item`. El trabajo es **enriquecer los parámetros** y **escribir ese emisor**, no crear un IR nuevo. El plan ejecutable de esta primera parte es `docs/superpowers/plans/2026-11-05-mg-02-rebanada-vertical.md`.

Contratos entre capas (cada contrato tiene un `dataclass` o modelo `pydantic` y una prueba de forma):

- **Modelo semántico:** `Tabla(nombre, libref, origen, columnas[Columna(nombre, tipo_sas, tipo_talend, longitud, formato, informat, anulable)])`, `Libreria`, `Parametro` (macrovariable resuelta o por resolver). Cada columna lleva `fuente` (línea del SAS) para trazabilidad.
- **IR lógica:** operadores `Leer`, `Escribir`, `Filtrar`, `Proyectar`, `Calcular`, `Unir` (tipo y condición), `Combinar` (MERGE), `Agregar`, `Ordenar`, `Deduplicar`, `Concatenar`, `Pivotar`, `Iterar`, `Controlar`. Cada uno con su semántica SAS explícita (cómo trata faltantes, blancos y orden).
- **Plan de componentes:** grafo de nodos Talend con parámetros, esquemas y conexiones, **independiente del formato `.item`** (así se prueba sin Studio).
- **Plan de Jobs:** asignación de nodos a Jobs, joblets y subjobs, con el contexto requerido por cada uno.
- **Traza:** `programa.trace.json` con, por cada componente, las líneas de SAS que lo originan.

Decisión de diseño: **no exigir YAML por programa.** Los YAML de `decisiones/` pasan a ser *sobreescrituras
opcionales* (nombres de Jobs, agrupación forzada, valores de contexto). Sin ellos el migrador produce una
arquitectura por omisión (MG-P8) y una lista de decisiones abiertas.

### 4.1 Cómo se usa `talend-mcp` (herramientas y CLI)

`talend-mcp` ya ofrece lo que un migrador de producción necesita y que no conviene reescribir. Se usa por la **CLI
`talend`** (`bun run cli ...`, o el binario compilado con `bun run cli:build`) con `--json` para scripts, y por MCP
cuando la ejecuta un agente. Reglas de uso:

| Capacidad | Herramienta de talend-mcp | Uso en el migrador |
|---|---|---|
| Crear Jobs sin abrir Studio, en bloque, con validación y `dryRun` | `talend_jobs_create_from_spec`, `talend_jobs_create_batch`, `talend_job_edit_offline`, `talend_jobs_edit_batch` | Respaldo del emisor propio: el emisor `.item` de `sgm` sigue siendo la fuente por defecto (determinista, sin dependencias externas); estas herramientas sirven para comparar y como segundo camino |
| Compilar muchos Jobs sin editor (unos 0,2 s por Job) | `talend_job_build_batch` | Anillo C rápido: reemplaza compilar uno por uno; `noCompilan` debe quedar vacío |
| Ejecutar y buscar avisos aunque el código de salida sea 0 | `talend_job_verify` | Sobre una muestra; obligatorio en el piloto |
| Plantilla XML de cualquier componente (855 de 1215 generan) | `talend_components_generate_template` | Alimenta la biblioteca de plantillas (MG-P9-01) |
| Definición y parámetros de un componente | `talend_components_definition`, `docs/catalogo-componentes/` | Reglas de configuración sin abrir Studio |
| Construir y ejecutar fuera de Studio | `talend_deliverables_build_job`, `talend_runs_start_exported` | Entregable y prueba de ejecución con contextos |
| Contextos y metadatos del repositorio | `talend_list_repository_contexts` y afines | Verificar que los grupos de contexto existen |
| Diagnóstico | `talend_errors_explain`, `talend_analyze_logs`, `talend_bridge_log_tail` | Informe de fallos del lote |

Lo que **no** se delega al MCP: el análisis de SAS, el plan lógico, el planificador de arquitectura y la lógica de
traducción.

Estrategia mixta de la propia documentación de talend-mcp (`docs/MODO-OFFLINE.md`): crear y editar **offline** en
bloque (sin Studio abierto, unos 1 ms por Job), reservar Studio abierto para los componentes que solo Studio
resuelve (por ejemplo `tMap` con metadatos) y para ejecutar una muestra. Esto hace viable el desarrollo rápido que
pidió el usuario: un lote de 100 Jobs compila en segundos o pocos minutos, no en horas.

Contrato de la interfaz: un único módulo `src/sgm/backend_talend/` con una interfaz (`escribir`, `compilar_lote`,
`refrescar`, `verificar`) y tres implementaciones: `archivos` (por omisión, sin dependencias), `talend_cli` (llama a
la CLI con `--json` y con tiempo máximo) y `mcp` (habla con el servidor ya arrancado por HTTP JSON-RPC). Si Studio
no está disponible, los backends que lo necesitan fallan con un mensaje claro y `sgm migrar` sigue produciendo los
archivos.

## 5. Catálogo de traducciones SAS a Talend

Es el contrato funcional. Cada fila es una tarea de traducción o está cubierta por una. La columna
"Trampa" es lo que más suele estar mal. "Nivel" es el nivel del corpus que debe probarla.

### 5.1 Entrada y salida

| SAS | Talend | Trampa | Nivel |
|---|---|---|---|
| `LIBNAME x 'ruta'` | Variable de contexto `x_ruta` por entorno | Las rutas no se escriben dentro del Job | L0 |
| `LIBNAME` a base (Oracle, Teradata, ODBC, Impala) | `t<DB>Connection` compartida y `CONNECTION` hacia los hijos | Credenciales: contexto vacío, nunca en claro | L8 |
| `PROC IMPORT` (CSV, DLM, XLSX) | `tFileInputDelimited`, `tFileInputExcel` | `GETNAMES`, `GUESSINGROWS` (tipado), delimitador, cabecera, hoja | L0 |
| `INFILE` / `INPUT` (lista, columna, formateado, `DSD`, `MISSOVER`, `TRUNCOVER`, `FIRSTOBS`) | `tFileInputDelimited`, `tFileInputPositional`, `tFileInputRegex` | Informats `w.d` con decimales implícitos | L0, L4 |
| `FILE` / `PUT` | `tFileOutputDelimited`, `tFileOutputPositional` | Formatos de salida | L0 |
| `PROC EXPORT`, `ODS CSV` | `tFileOutputDelimited`, `tFileOutputExcel` | Formato de números (`3.`, `20.`), cabecera | L0 |
| Dataset permanente `lib.tabla` | Tabla de base o archivo de preparación según decisión MG-D05 | `.sas7bdat` no se lee en Talend | L1 |
| `FILENAME` (archivo, pipe, FTP, URL, correo) | `tFileList`, `tSystem`, `tFTPGet`, `tFileFetch`, `tSendMail` | Seguridad y rutas | L8 |
| `PROC DOWNLOAD`/`UPLOAD`, `RSUBMIT` | Copia de archivos y contexto de ruta | Hueco conocido del analizador (R7-12) | L8 |
| `CONNECT TO` y `SELECT FROM CONNECTION TO` (paso directo) | `t<DB>Input` con SQL literal | Dialecto de la base | L8 |
| `%INCLUDE` | Expansión en línea o Job hijo | Rutas relativas | L5 |

### 5.2 DATA step

| SAS | Talend | Trampa | Nivel |
|---|---|---|---|
| `SET a;` | Entrada del flujo | `OBS=`, `FIRSTOBS=`, `WHERE=` como opciones | L1 |
| `SET a b;` (concatenar) | Unión de flujos; `tUnite` no compila en 8.0.1, usar la alternativa validada | Columnas con distinto tipo o longitud | L1 |
| `MERGE a b; BY k;` | **No es un `JOIN`.** Con claves repetidas en ambos lados, el resultado es el máximo de filas por grupo. Implementar con `tSortRow` y `tJavaRow` o `tMap` más reglas, y validar con `L6/l6_02` | `IN=`, orden previo, columnas sobrescritas | L6 |
| `UPDATE` | `tMap` con lookup y reglas | Faltantes no sobrescriben | L6 |
| `IF c THEN ...; ELSE ...;`, `SELECT/WHEN` | Expresión ternaria en `tMap` | **En SAS el faltante numérico es menor que cualquier número**; en Java una comparación con `null` lanza o es falsa | L4 |
| `IF c;` (subsetting), `DELETE`, `WHERE` | `tFilterRow` o filtro del `tMap` | `WHERE` y `IF` difieren en cuándo se evalúan | L1 |
| `OUTPUT` (varias tablas de salida) | Varias salidas del `tMap` | Ciclo implícito | L6 |
| `KEEP`/`DROP`/`RENAME` | Esquema de salida | Orden de columnas | L1 |
| Asignación, `LENGTH`, `FORMAT`, `INFORMAT`, `ATTRIB` | Esquema tipado y expresión | `FORMAT` no cambia el valor, solo la presentación | L4 |
| `RETAIN`, sentencia suma (`x+1`), `FIRST.`/`LAST.` con `BY`, `LAG`, `DIF` | `tSortRow` y `tJavaRow` con estado, o `tAggregateRow` y unión | Reinicio por grupo, valor inicial en faltante | L6 |
| `ARRAY` y `DO` | `tJavaRow` o expansión estática si los límites son constantes | Índices desde 1 | L6 |
| `_N_`, `_ERROR_` | Contador en `tJavaRow` | — | L6 |
| `CALL SYMPUT`/`SYMPUTX` | `tSetGlobalVar` o variable de contexto en tiempo de ejecución | Alcance, momento de resolución | L5 |
| Objetos `hash` | `tMap` con lookup, o pendiente con motivo | — | L9 |
| `STOP`, `ABORT`, `RETURN` | `tDie` o fin de subjob | Código de salida | L8 |

### 5.3 `PROC SQL`

| SAS | Talend | Trampa | Nivel |
|---|---|---|---|
| `SELECT`, `DISTINCT`, `WHERE`, `ORDER BY` | `tMap`, `tFilterRow`, `tSortRow`, `tUniqRow` | `ORDER BY` por número de columna | L1 |
| `INNER`/`LEFT`/`RIGHT`/`FULL JOIN` | `tMap` con lookup y tipo de unión | Llaves nulas, blancos finales, mayúsculas; lookup recargado | L2 |
| Unión implícita en `WHERE` | `tMap` | Producto cartesiano accidental | L2 |
| `IS [NOT] MISSING`, `IN`, `BETWEEN`, `LIKE`, `CONTAINS`, `CASE` | Expresión Java | `IS MISSING` por tipo (texto: vacío; número: nulo) | L2, L4 |
| `GROUP BY`, `HAVING`, `COUNT`, `SUM`, `AVG`, `MIN`, `MAX` | `tAggregateRow` más `tMap` | `COUNT(col)` no cuenta faltantes; `SUM` ignora faltantes | L3 |
| Subconsultas (`IN`, `EXISTS`, escalar, en `FROM`) | Subflujo y lookup, o Job hijo | Correlacionadas | L3 |
| `UNION`, `UNION ALL`, `INTERSECT`, `EXCEPT`, `OUTER UNION CORR` | Unión y deduplicación | Orden y tipos de columna | L3 |
| `CREATE TABLE AS`, `CREATE VIEW`, `INSERT INTO`, `UPDATE`, `DELETE`, `ALTER`, `DROP` | Salida del flujo o `t<DB>Row` | Vistas: evaluación diferida | L1, L8 |
| `SELECT ... INTO :macro` | `tFlowToIterate` o `tSetGlobalVar` | Un valor frente a lista | L5 |
| `DICTIONARY.TABLES/COLUMNS` | Metadatos del modelo semántico | Solo en tiempo de generación | L5 |
| Funciones SAS dentro del SQL | Tabla de funciones (5.7) | Fechas | L4 |

### 5.4 Procedimientos

| SAS | Talend | Trampa | Nivel |
|---|---|---|---|
| `PROC SORT` (`BY`, `DESCENDING`, `NODUPKEY`, `NODUPREC`, `DUPOUT=`) | `tSortRow`, `tUniqRow` | Qué fila se conserva: **la primera** (confirmado en Studio, hito 95); `NOEQUALS` | L6 |
| `PROC FREQ` y `PROC MEANS/SUMMARY` (`OUTPUT OUT=`) | `tAggregateRow` | Estadísticos disponibles, tratamiento de faltantes | L3 |
| `PROC TRANSPOSE` | `tDenormalize`, `tNormalize` o `tJavaRow` | Nombres de columnas dinámicos | L6 |
| `PROC APPEND` | Salida en modo append | — | L1 |
| `PROC FORMAT` (formatos propios) | Mapa de búsqueda en `tMap` o expresión | Rangos y `other` | L4 |
| `PROC DATASETS`, `COPY`, `DELETE`, `CONTENTS` | `tFileCopy`, `tFileDelete`, metadatos | Solo borrado de salidas propias | L8 |
| `PROC PRINT/REPORT/TABULATE`, `ODS` | Sin equivalente de datos: pendiente documentado o `tLogRow` | Salida solo visual | L9 |
| `PROC REG/GLM/LOGISTIC`, `DS2`, `FedSQL`, `IML` | **Fuera de alcance**, con motivo en el informe | — | — |

### 5.5 Macros (expansión estática primero)

| SAS | Traducción | Trampa |
|---|---|---|
| `%LET`, `&var`, `&&var&i` | Constante resuelta; si depende de algo en ejecución, variable de contexto | Resolución en múltiples pasadas |
| `%MACRO` con parámetros y `%MEND` | Expansión por cada llamada; **joblet con parámetros cuando la expansión se repite** (MG-P8) | Parámetros posicionales y por nombre |
| `%IF/%THEN/%ELSE`, `%DO`/`%END`, `%DO %WHILE/%UNTIL` | Evaluación en generación; el bucle se desenrolla si los límites son constantes, si no `tLoop` o `tFlowToIterate` | `%if` dentro de macro con parámetro (hueco del analizador) |
| `%EVAL`, `%SYSEVALF`, `%SYSFUNC`, `%STR`, `%NRSTR`, `%BQUOTE`, `%SCAN`, `%UPCASE` | Evaluación en generación | Citado |
| `%GLOBAL`/`%LOCAL` | Alcance del contexto | — |
| `CALL EXECUTE`, macros que generan código a partir de datos | **Pendiente con motivo** (no determinable en generación); se documenta la forma | — |

### 5.6 Control y operación

| SAS | Talend |
|---|---|
| Comprobación de errores (`&SYSERR`, `&SQLRC`, `%ABORT`) | `OnSubjobError`, `tDie`, `tWarn`, `tLogCatcher` |
| `sleep`, `wait`, reintentos | `tSleep`, `tWaitForFile`, `SUBJOB_ERROR` con `tRunJob` |
| `x`/`systask`/`pipe` | `tSystem` |
| Medir tiempo (`sys timer`) | `tChronometerStart` y `tChronometerStop` |
| Correo de inicio, fin y error | `tSendMail` en `SUBJOB_OK` y `SUBJOB_ERROR` |
| Programación (lotes, `SASGSUB`) | Build Job más el programador de la plataforma; **no** se generan los horarios |
| Paralelismo (dividir y escribir en partes) | `tParallelize`, `tFlowToIterate` y `tRunJob` |

### 5.7 Funciones, formatos e informats (tabla viva)

La tabla maestra es `rules/sas/functions/` y `src/sgm/expressions/`. Meta: **toda función que aparezca en el
corpus o en los programas reales tiene traducción, vectores con fuente y prueba.** Orden de trabajo:

| Familia | Funciones (empezar por las que ya aparecen: `input`, `left`, `compress`, `put`, `missing`, `catx`, `cats`, `intnx`, `scan`, `substr`, `length`, `strip`, `round`, `sum`, `ifn`, `ifc`, `mod`, `abs`, `sqrt`, `log`, `exp`, `month`, `mean`) |
|---|---|
| Texto | `TRIM`, `STRIP`, `LEFT`, `RIGHT`, `COMPRESS`, `COMPBL`, `CAT*`, `SCAN`, `SUBSTR` (incluida como pseudovariable), `INDEX`, `FIND`, `TRANWRD`, `TRANSLATE`, `UPCASE`, `LOWCASE`, `PROPCASE`, `LENGTH*`, `REVERSE`, `REPEAT`, `PRXMATCH/PRXCHANGE` (mapeo a expresiones regulares de Java con las diferencias documentadas) |
| Numéricas | `ROUND` (al múltiplo, empates alejándose de cero), `INT`, `CEIL`, `FLOOR`, `MOD`, `ABS`, `MIN`, `MAX`, `SUM`, `MEAN`, `N`, `NMISS`, `COALESCE`, `IFN`, `IFC` |
| Fecha | `TODAY`, `DATE`, `MDY`, `YEAR`, `MONTH`, `DAY`, `INTNX`, `INTCK`, `DATDIF`, `YRDIF`, `WEEKDAY`; **la fecha de SAS es el número de días desde 1960-01-01** |
| Conversión | `INPUT`, `PUT` con informats y formats; ver `leforinforref.txt` |
| Faltantes | `MISSING`, valores especiales `.A` a `.Z` (pendiente si aparecen) |

Cada función: ficha en `rules/sas/functions/<nombre>.yaml` con firma, semántica con faltantes, traducción Java,
vectores con fuente (guía y página) y casos de borde. **Los vectores salen de la guía, no de la intuición.**

## 6. Estrategia de pruebas rápida

### 6.1 Pirámide (detalle del principio de la sección 0.2)

1. **Anillo A, estático (segundos).** Para cada programa traducido: el plan de componentes es válido (conexiones
   sin huérfanos, esquemas consistentes entre origen y destino de cada conexión, tipos compatibles), el `.item`
   generado pasa un validador estructural (XML bien formado, referencias `xmi:id` resueltas, nombres únicos de
   `UNIQUE_NAME`, `lineStyle` conocidos), las expresiones Java generadas compilan con `javac` suelto sobre un
   molde mínimo. Nada de esto toca Studio.
2. **Anillo B, intérprete de referencia (segundos a minutos).** Un intérprete en Python de la IR lógica con la
   semántica SAS documentada. Se ejecuta con las entradas del caso y se compara con `esperado/`. Si el
   intérprete y el esperado difieren, el error es del intérprete o del esperado, se resuelve con la guía antes de
   mirar Talend. Este anillo prueba el 90 % de los cambios.
3. **Anillo C, Studio en lote (minutos).** Se añaden los Jobs de todos los casos nuevos a una sola compilación
   y se ejecuta una sola vez el arnés `tools/corpus_studio.py`. Mejorar el arnés para: compilar varios Jobs por
   lote, ejecutar en paralelo los que no comparten carpeta, reutilizar el JDK y el repositorio Maven local,
   salir pronto en el primer fallo y limpiar siempre.
4. **Anillo D, nocturno.** Todo el corpus por el traductor y por Studio; informe de regresión; falla si un caso
   que pasaba deja de pasar.

**Regla:** una tarea de traducción termina cuando pasa A y B y su lote en C. D la protege después.

### 6.2 Fuentes independientes del esperado (ya existen; seguir usándolas)
1. Capa A: SQLite sobre las entradas (oráculo de `PROC SQL`).
2. Capa B: referencia en Python con vectores documentados (DATA step, funciones).
3. Capa C: esperado revisado a mano con cita de la guía.
4. Anomalías plantadas: el generador de datos escribe la verdad por construcción (conteos de errores
   conocidos), independiente de cualquier traducción.

### 6.3 Generación de programas SAS para probar (nuevo)
Un generador de programas a partir de una gramática pequeña (`tools/generador_sas/`): combina operadores
(filtro, cálculo, unión, agregado, orden, duplicados) con datos aleatorios con semilla fija, produce el SAS y
su esperado con el intérprete del anillo B, y verifica el Job. Sirve para encontrar errores de composición que
los casos escritos a mano no ven. Los fallos se reducen automáticamente (menor programa que falla) y se
convierten en casos permanentes del corpus.

### 6.4 Simuladores
Postgres, Impala y SMTP ya existen. Faltan: FTP/SFTP (contenedor), Oracle y Teradata (solo se simulan por
Postgres con dialecto declarado y se documenta la diferencia), un S3 local (Moto, ya usado en talend-mcp).
Regla: lo que no se pueda simular se documenta como **no verificado** en `sgm cobertura`.

## 7. Calidad de los Jobs ("bien hechos"): lista de verificación automática

Cada salida de `sgm migrar` pasa estos controles; un control que falle rompe la prueba.

| # | Control | Cómo se mide |
|---|---|---|
| Q1 | Nada fijo en el Job: rutas, servidores, usuarios, fechas, nombres de tablas por entorno | escáner de literales sospechosos contra el contexto |
| Q2 | Contextos DEV, QA y PROD con las mismas claves; contraseñas vacías o `***`; tipos correctos (`id_String`, `id_Integer`, `id_Date`, `id_Password`) | validación del grupo de contexto |
| Q3 | Job padre que orquesta por dependencias reales (linaje), con `OnSubjobOk`, paso de parámetros por `tRunJob` y propagación de errores | validación del grafo |
| Q4 | Tamaño: un Job no pasa de 20 componentes (configurable); lo repetido se extrae a joblet | `sgm cobertura` y pase de tamaño |
| Q5 | Joblets para bloques repetidos (por similitud estructural) con parámetros de contexto | el pase de agrupación, con prueba |
| Q6 | Errores: cada subjob crítico tiene `OnSubjobError`, `tDie` con código y mensaje claro, y `tLogCatcher` o registro | validación de conexiones |
| Q7 | Registro: nivel configurable (`log_nivel`), conteos por etapa (`NB_LINE`) escritos | validación |
| Q8 | Esquemas tipados (no todo `String`); decimales con `BigDecimal` y la longitud/precisión que dice el SAS | validación de esquema |
| Q9 | Lectores con `DIE_ON_ERROR=true` y rechazos a archivo cuando el SAS los separa | validación |
| Q10 | Nombres legibles y únicos (`sgm`: convención documentada), etiquetas y notas con la línea de SAS origen | validación y `trace.json` |
| Q11 | Disposición en el lienzo por orden de flujo, sin superposición | validación geométrica |
| Q12 | Sin secretos en `.item`, `.properties`, contextos ni registros | `sgm secretos` |
| Q13 | Determinismo: dos corridas dan los mismos bytes | prueba de determinismo |
| Q14 | Abre en Studio sin que Studio "repare" el Job (ida y vuelta) | `tools/comparar_item.py` (persona, una vez, y luego automatizado donde se pueda) |
| Q15 | Rendimiento razonable: lookups en `LOAD_ONCE` o `RELOAD` justificados, sin productos cartesianos, `tMap` en memoria acotada | revisión estática más prueba de volumen |

## 8. Reglas automáticas por omisión (el migrador decide solo; una persona puede cambiarlas después)

Ninguna de estas filas bloquea el desarrollo ni la ejecución del migrador. La columna "Valor por omisión" es lo
que el migrador hace sin preguntar; cualquier otra opción se activa después con una sobreescritura opcional (`decisiones/<programa>.*.yaml` o una opción de `sgm migrar`).

| Id | Regla | Opciones posibles | Valor por omisión (lo que hace el migrador solo) | Afecta a |
|---|---|---|---|---|
| MG-D01 | Versión de SAS del cliente (9.3, 9.4M3...) | confirmar | 9.4 (edición 3.5), lo de las guías | casos de borde de funciones |
| MG-D02 | Dependencias nuevas | `sqlglot` y `jsonschema` | **Decidida en el hito 80 (R0-04, DC-11): ya aprobadas y en `pyproject.toml`.** `ir/sql_tree.py` usa `sqlglot`; no hay analizador propio. Cualquier otra dependencia se anota en `PROGRESS.md` | ninguna |
| MG-D03 | Qué hacer con datasets `.sas7bdat` permanentes | tabla de base, archivo de preparación, fuera de alcance | archivo de preparación con aviso | MG-P2 |
| MG-D04 | Paso a producción de código dinámico (`CALL EXECUTE`) | pendiente con motivo, o reescribir a mano | pendiente con motivo | MG-P7 |
| MG-D05 | Destino de bases (Impala, Oracle, Teradata, Postgres) | cuáles se soportan primero | Impala, Postgres y archivos | MG-P2 |
| MG-D06 | Almacén de secretos (DC-06) | variable de entorno del lanzador, gestor corporativo | variable de entorno y contexto vacío | MG-P13 |
| MG-D07 | Tolerancia numérica de comparación y de conciliación | por columna | `0.005` o la del caso | MG-P10 |
| MG-D08 | Quién da programas reales del cliente (aunque sea uno) y cuándo | Tecnología | sin programas reales: solo corpus | MG-P14 |
| MG-D09 | Quién valida en un SAS real el comportamiento de `PROC IMPORT`/`EXPORT` (DC-12) | Negocio | casos marcados `pendiente_revision` | cierre de C3 |
| MG-D10 | Plataforma de despliegue (TMC, Remote Engine, servidor propio, solo Build Job) | Tecnología | Build Job exportado | MG-P14 |
| MG-D11 | Uso de `talend-mcp` dentro del producto | (a) prohibido; (b) backend opcional por CLI o MCP; (c) obligatorio | **Decidida: (b)**, autorizada por el usuario el 5 de noviembre de 2026 | ninguna |

## 9. Plan de trabajo por fases

Notación de tareas: `MG-Pn-mm`. Tipo: **H** agente haiku (mecánico, con revisión), **S** agente con criterio de diseño,
**P** persona. Horas son de agente. "Aceptación" es lo que debe ser verdad para cerrarla. Cada tarea cierra con
hito, `PROGRESS.md` y commit.

### MG-P0. Preparación (37 h)
| Id | Tarea | Tipo | Aceptación | Horas |
|---|---|---|---|---|
| MG-P0-01 | Renumerar y ordenar `PROGRESS.md` (series paralelas con letra) y vincular este plan desde `plan.md` | H | Sin números duplicados; enlace presente | 2 |
| MG-P0-02 | Arreglar el estado de Studio: documentar cómo detectar y cerrar el diálogo "Network Issue" y añadir una comprobación de salud rápida (`tools/studio_salud.py`) que falle en menos de 10 s | H | Salud en 10 s; el arnés la llama antes de empezar | 3 |
| MG-P0-03 | Arnés en lote: `tools/corpus_studio.py lote <casos...>` compila los Jobs de varios casos en una sola pasada y los ejecuta; reutiliza el JDK y Maven; limpia siempre | S | 10 casos en menos de 10 min; mismo resultado que uno por uno | 8 |
| MG-P0-04 | `tools/ciclo_rapido.py`: corre A y B sobre los casos tocados por el cambio (por diferencias de git) | H | Menos de 90 s con 20 casos | 3 |
| MG-P0-05 | Tablero único: cobertura del corpus, traducidos, verificados, regresiones | H | `uv run python tools/tablero.py` incluye las cifras de la sección 1 | 3 |
| MG-P0-06 | Dejar escrito en `docs/arquitectura/ir-logica.md` cómo se **reutiliza** el IR que ya existe (`ir/models.py`: `Operator`, `Graph`, `Plan`; candidatos de componente por `rules/mapping/*.yaml`) y qué parámetros hay que enriquecer; no se crea un IR paralelo | S | Documento revisado con ejemplos de cada operador | 5 |
| MG-P0-07 | Regla 1 de `AGENTS.md` actualizada (hecho el 5 de noviembre de 2026); queda por añadir una prueba que impida que `src/sgm/` fuera de `backend_talend/` importe o llame al MCP | H | prueba en `tests/unit/` | 1 |
| MG-P0-08 | `src/sgm/backend_talend/`: interfaz y las implementaciones (`archivos`, `talend_cli` y `mcp`), con pruebas con un doble de la CLI y del transporte MCP; tiempo máximo y salida `--json`; sin secretos en la línea de comandos ni en el registro | S | `corpus_studio.py lote` compila un lote con `talend_job_build_batch` por CLI o MCP; sin Studio el error es claro y `sgm migrar` conserva la salida de archivos | 8 |
| MG-P0-09 | Aprovechar el modo offline de talend-mcp en el anillo C: `corpus_studio.py lote` usa `talend_job_build_batch` (unos 0,2 s por Job) y `talend_job_verify` solo para la muestra; medir y documentar el tiempo | H | 50 Jobs compilados en menos de 2 min | 4 |

**Estado (hito 103m, 5 de noviembre de 2026).** Hechos MG-P0-02, MG-P0-03, MG-P0-04, MG-P0-07,
MG-P0-08 y MG-P0-09: `src/sgm/backend_talend/` (interfaz, archivos, CLI, salud),
`tools/studio_salud.py`, `tools/corpus_lib/studio_lote.py`, `corpus_studio.py lote`,
`tools/ciclo_rapido.py` y `tests/unit/test_backend_aislado.py`. MG-P0-01, MG-P0-05 y MG-P0-06 pasan
al plan MG-02, que es quien los usa.

**Ampliación (hito 127m, 8 de noviembre de 2026).** MG-P0-08 y MG-D11 quedan completos con el
backend `mcp`: `McpBackend` usa el mismo contrato que la CLI, lee JSON o SSE, negocia sesión solo si
el servidor la pide y comparte con la CLI el mapeo de respuestas de `comun.py`.

Dos criterios de aceptación **no se pudieron comprobar** porque Talend Studio tenía dos modales
abiertos («Network Issue Occured» y «Talend Cloud Data Fabric»): la compilación en lote real
(MG-P0-03 y MG-P0-09) y el tiempo de 50 Jobs. La comprobación de salud los detecta y el arnés se
detiene antes de copiar nada; falta la medición cuando se cierren. El ciclo rápido mide 94 s de
suite más 2 s por caso tocado (133 s con veinte), por encima de los 90 s pedidos: el cuello de
botella es la suite completa, no la herramienta.

Las respuestas reales de la CLI de `talend-mcp` no coincidían con lo que suponía este plan y se
corrigieron contra ellas: `talend_job_build_batch` devuelve un mapa `result.jobs` (no listas
`compilan`/`noCompilan`), `talend_job_verify` no acepta `context` y sus `findings` son un mapa de
`errors` y `warnings`. Las respuestas quedan guardadas en `tests/fixtures/talend_cli/`.

### MG-P1. Modelo semántico y plan lógico (70 h)
| Id | Tarea | Tipo | Aceptación | Horas |
|---|---|---|---|---|
| MG-P1-01 | Tabla de símbolos: `LIBNAME`, `WORK`, datasets, vistas, alias, tablas temporales, `FILENAME`; resolución de la tabla que lee cada paso | S | `L0` y `L1` resuelven todas las tablas sin YAML | 8 |
| MG-P1-02 | Inferencia de esquemas: columnas y tipos desde `PROC IMPORT`, `INFILE/INPUT`, `LENGTH`, `FORMAT`, `CREATE TABLE`, `SELECT`, `SET`; con tipos SAS (carácter y numérico) y tipo Talend | S | Esquema de cada tabla del corpus coincide con el declarado en `caso.yaml` | 12 |
| MG-P1-03 | Plan lógico (IR): los 14 operadores de la sección 4, con la semántica SAS en el modelo; ampliar `ir/` sin romper los pases existentes | S | Cada operador tiene constructor, validador y prueba; `L1` a `L3` construyen su plan | 14 |
| MG-P1-04 | Pase `SQL a plan`: `PROC SQL` a operadores (sobre `sql_tree.py`) | S | `L1` y `L2` generan plan sin pendientes que no sean de alcance | 12 |
| MG-P1-05 | Pase `DATA step a plan` (sobre `datastep.py`) | S | `L4` a `L6` generan plan | 12 |
| MG-P1-06 | Pase `PROC a plan` (`SORT`, `FREQ`, `MEANS`, `TRANSPOSE`, `APPEND`, `FORMAT`) | H | `L3` y `L6` | 6 |
| MG-P1-07 | Informe de pendientes con motivo estable (códigos `P-xxx`), usado en todas las capas | H | Cada pendiente tiene código, motivo y línea | 3 |
| MG-P1-08 | Propiedad: pasos del SAS igual a pasos del plan más pendientes (sin pérdidas) | H | Prueba que recorre los 189 programas del repositorio | 3 |

**Estado (hito 104m, 5 de noviembre de 2026).** Hechos MG-P1-07 y MG-P1-08. Los pendientes
llevan código, motivo y línea del SAS en las tres capas (`PendienteMigracion` en `migrar/`, los
códigos `P-xxx` en el emisor y en los informes), y la propiedad «pasos del SAS = pasos del plan +
pendientes» se comprueba sobre los 190 programas de `tests/fixtures/sas` y sobre los 45 del corpus:
`ResultadoMigracion.visitados` tiene todos los operadores del plan y cada uno dejó su línea en la
traza o en un pendiente. MG-P1-02 está a medias: `esquemas_de_entrada` deduce las tablas de
`PROC IMPORT` sin YAML (catálogo, cabecera de la muestra, columnas usadas) pero **sin tipos**: lo que
no está en el catálogo sale `String` con su `P-TIPO-DESCONOCIDO`. MG-P1-01 y MG-P1-04 resuelven `L0`
a `L2` sin YAML; MG-P1-03, MG-P1-05 y MG-P1-06 son de los planes siguientes.

**Avance posterior (hitos 130m a 138m, 9 de noviembre de 2026).** MG-P1-02 a medias: bloque `esquemas` en los 45 casos de L0 a L2 (3 tipos demostrados por `LENGTH`, 273 columnas pendientes con motivo); el largo de `LENGTH` llega a la salida del `tMap`; `sgm migrar` todavía no infiere tipos de `PROC IMPORT`. MG-P1-03 a medias: los 14 operadores tienen constructor validado y prueba (`ir/operadores.py`, `pivotar` queda como hueco); los constructores reproducen la firma del lowering en L1 a L3 para todos los kinds que tienen constructor salvo `rename` (no aparece en esos planes). El criterio «L1 a L3 construyen su plan» no se cumple porque ningún pase usa los constructores: migrar el lowering es una tarea aparte que cambia la forma de las uniones del emisor. Verificación en Studio pendiente: el MCP en 127.0.0.1:3927 no responde.

### MG-P2. Entrada y salida (50 h)
| Id | Tarea | Tipo | Aceptación | Horas |
|---|---|---|---|---|
| MG-P2-01 | `PROC IMPORT` y `PROC EXPORT` generales (CSV, DLM, XLSX, XLS) a lectores y escritores, con tipos y cabecera; `GUESSINGROWS` y `GETNAMES` | S | `L0` (15 casos) pasan en B y en lote C | 10 |
| MG-P2-02 | `INFILE/INPUT/FILE/PUT` (lista, columna, formateado, `DSD`, `MISSOVER`, `TRUNCOVER`) | S | casos nuevos de `L0` con archivos posicionales y delimitados | 12 |
| MG-P2-03 | Informats y formats numéricos y de fecha: `w.d`, `COMMAw.d`, `DOLLAR`, `YYMMDD`, `DDMMYY`, `DATE9`, `ANYDTDTE` con vectores de `leforinforref.txt` | H | los informats que aparecen en el corpus tienen prueba ejecutada | 8 |
| MG-P2-04 | `LIBNAME` a rutas y a bases (Impala, Postgres primero) con conexión compartida y contexto | S | `L8/totales/07` pasa contra el Impala del contenedor | 8 |
| MG-P2-05 | Paso directo (`CONNECT TO ... FROM CONNECTION TO`) a lector con SQL literal | H | prueba con Postgres del contenedor | 4 |
| MG-P2-06 | `FILENAME` (archivo, pipe, FTP) y `PROC DOWNLOAD/UPLOAD/RSUBMIT` (cierra el hueco R7-12) | S | caso del corpus con `RSUBMIT` | 6 |
| MG-P2-07 | Decisión MG-D03 aplicada: datasets permanentes a archivo de preparación con aviso | H | casos con `lib.tabla` generan lectura y escritura coherentes | 2 |

**Estado (hito 104m, 5 de noviembre de 2026).** MG-P2-01 a medias: `PROC IMPORT` y `PROC EXPORT`
de CSV y DLM generan `tFileInputDelimited` y `tFileOutputDelimited` con cabecera y delimitador, y los
15 casos de `L0` se migran enteros —7 de ellos completos, sin un pendiente que no sea de tipo—. El
`DBMS=XLSX` y `GUESSINGROWS` todavía no tienen emisor, y los tipos de columna esperan a MG-P1-02.

### MG-P3. Expresiones y funciones (80 h)
| Id | Tarea | Tipo | Aceptación | Horas |
|---|---|---|---|---|
| MG-P3-01 | Motor de expresiones: aritmética, comparaciones, lógicos, `IN`, `BETWEEN`, `LIKE`, concatenación `||`; **el faltante numérico es menor que cualquier número; el texto en blanco es faltante y es igual a `''`; blancos finales no cuentan** | S | todos los vectores de `semantica/vectores.yaml` ejecutados en B y en lote C | 12 |
| MG-P3-02 | Funciones de texto (lista de la sección 5.7) con ficha por función | H | cada una con vectores con fuente y prueba | 14 |
| MG-P3-03 | Funciones numéricas y de agregación por fila (`SUM`, `MEAN`, `N`, `NMISS`, `COALESCE`, `IFN`, `IFC`, `ROUND`) | H | idem | 10 |
| MG-P3-04 | Funciones de fecha y hora (días desde 1960, `INTNX`, `INTCK`, `DATDIF`, `YRDIF`) | S | idem, con casos de fin de mes y bisiestos | 12 |
| MG-P3-05 | `INPUT`/`PUT` con informats y formats generales | S | las 15 formas `w.d` del cliente más las de la guía | 10 |
| MG-P3-06 | Expresiones regulares (`PRX*`) y diferencias con Java documentadas | S | casos con límites | 6 |
| MG-P3-07 | Formatos propios (`PROC FORMAT`) como mapas | H | `L4` | 6 |
| MG-P3-08 | Generador automático de la tabla de funciones soportadas y de `docs/funciones.md` | H | documento generado, sin edición manual | 4 |
| MG-P3-09 | Cierre de brechas del oráculo (`LENGTH`, `COMPBL`, `CONTAINS`, `IS MISSING` sobre expresión) | H | los 19 resultados sin verificar de `L8/validaciones` pasan a verificados | 6 |

**Estado (hito 107, 6 de noviembre de 2026).** MG-P3-01 sigue parcial: el intérprete ejecuta el
subconjunto de expresiones ejercido por los vectores y casos L0/L4; quedan 20 `xfail` con motivo y no
se ejecutaron todos los vectores de `semantica/vectores.yaml`. MG-P3-02, 03 y 05 avanzan solo en
funciones concretas respaldadas por evidencia (`INPUT`, `LEFT`, `SUBSTR`/`SUBSTRN`, `COALESCEC`,
`COMPRESS`, `SCAN`, `ROUND` y funciones ya cubiertas), no como catálogos completos. `COMPRESS` cubre
los modificadores `K`, `D` e `I` usados en L4; `SCAN` usa los delimitadores ASCII documentados para
la plataforma SAS del corpus (CALL SCAN, `lefunctionsref`, p. 442) y devuelve blanco si no existe la
palabra solicitada (SCAN, p. 1505). Los 20 casos L4 pasan el anillo A; el anillo B conserva sus
resultados previos. En Studio compilaron juntos 17 Jobs completos L0–L2 y siete casos L4 de
`COMPRESS`/`SCAN`; `l4_06` y `l4_14` se ejecutaron y coincidieron con sus CSV esperados. Un intento
de ampliar el lote a los 20 casos L4 encontró cinco incompatibilidades Java en `INPUT`, `ROUND`,
comparaciones y `PUT` de fechas; se mantienen fuera del lote validado, no se cuentan como soporte.
MG-P3-04 y 06 a 09 siguen pendientes.

**Actualización (hito 111n, 6 de noviembre de 2026).** Se corrigió la emisión de `INPUT w.d` a
`BigDecimal` (con decimales implícitos solo si el texto no contiene punto), `ROUND` como `Double` con
empates alejándose de cero, y predicados DATA step como `Long` 1/0. A/B queda verde para el conjunto
L4 revisado (suite completa: 2361 passed, 27 skipped, 149 xfailed; Ruff limpio). La compilación C
ampliada no se ejecutó: el bridge de Studio no estaba disponible (`ECONNREFUSED` en
`127.0.0.1:3930`). No se declara C validado para estos cambios; queda por reintentar con Studio abierto.

### MG-P4. DATA step (90 h)
| Id | Tarea | Tipo | Aceptación | Horas |
|---|---|---|---|---|
| MG-P4-01 | `SET`, `KEEP`, `DROP`, `RENAME`, `WHERE`, `IF/THEN/ELSE`, `SELECT/WHEN`, asignaciones, `DELETE`, subsetting IF, a `tMap` | S | `L0`, `L4` | 14 |
| MG-P4-02 | Múltiples `OUTPUT` y salidas | S | `L6` | 8 |
| MG-P4-03 | `SET` de varios datasets (concatenar) con el mecanismo validado, dado que `tUnite` no compila | S | primero una prueba de investigación en Studio y luego la implementación | 10 |
| MG-P4-04 | `MERGE ... BY ... IN=` con la semántica real (máximo de filas por grupo; no es `JOIN`) | S | `L6/l6_02` y los casos de la guía | 16 |
| MG-P4-05 | `RETAIN`, sentencia suma, `FIRST.`/`LAST.`, `LAG`, `DIF` | S | `L6` | 14 |
| MG-P4-06 | `ARRAY` y `DO` (desenrollado estático o `tJavaRow`) | S | casos nuevos | 10 |
| MG-P4-07 | `UPDATE`, `MODIFY` (si aparecen) | S | casos nuevos | 6 |
| MG-P4-08 | `_N_`, `_ERROR_`, `CALL SYMPUT` | H | `L5` | 6 |
| MG-P4-09 | Hash objects: soporte mínimo o pendiente con motivo | S | decisión documentada | 6 |

**Estado (hito 107, 6 de noviembre de 2026).** MG-P4-01 parcial: el frontend y lowering conservan
`WHERE=` en fuente `SET`, y el plan/emisor representan `WHERE`, subsetting `IF`, asignaciones,
`KEEP`, `DROP`, `RENAME` y asignaciones `IF/THEN/ELSE`, incluso cadenas `ELSE IF` con destino común.
Cada sentencia transformada lleva evidencia de su propia línea. `OUTPUT` explícito conserva el
destino en el plan; como el emisor aún no implementa ramas múltiples, queda como pendiente y no se
simula una salida parcial.
El intérprete evalúa las asignaciones del DATA step en orden, por lo que una asignación posterior
puede usar una columna calculada antes; el emisor sustituye esa referencia por la expresión previa
en el mismo `tMap`. `l0_07` y `l0_12` coinciden en B; `l0_07` sigue
pendiente en A porque `sgm migrar` no dispone de un esquema de entrada demostrable para resolver
`saldo`, no por el ELSE. `SELECT/WHEN` y `DELETE` no se declaran cubiertos. MG-P4-02 a 09 siguen
pendientes; en particular no se extiende la semántica de `MERGE`, estado por fila ni macros. En
Studio compilaron en lote 17 Jobs completos de L0–L2 y siete casos L4 enfocados; `l4_06` y `l4_14`,
con esquemas basados en cabeceras de muestra, se ejecutaron y coincidieron con sus CSV esperados. La
cabecera solo prueba nombres; los tipos no demostrados siguen explícitos como pendientes.

**Actualización (hito 111n, 6 de noviembre de 2026).** Los predicados emitidos en columnas de DATA
step se convierten a valores numéricos `Long` 1/0, manteniendo la semántica SAS en la salida. `OUTPUT`
condicional/múltiple sigue pendiente: el modelo/emisor no representa todavía todas las ramas y
destinos, por lo que no se emite parcialmente. La compilación Studio de esta ampliación está bloqueada
por bridge no disponible; no se contabiliza como pasada.

### MG-P5. `PROC SQL` (80 h)
| Id | Tarea | Tipo | Aceptación | Horas |
|---|---|---|---|---|
| MG-P5-01 | `SELECT/DISTINCT/WHERE/ORDER BY/CASE/COALESCE/calculated` | S | `L1` (15) | 10 |
| MG-P5-02 | Uniones `INNER/LEFT/RIGHT/FULL` e implícitas, con llaves de varias columnas, nulas y con blancos | S | `L2` (15) | 14 |
| MG-P5-03 | Agregados `GROUP BY/HAVING` y funciones de agregación con la semántica de faltantes | S | `L3` (12) | 12 |
| MG-P5-04 | Subconsultas (`IN`, `EXISTS`, escalar, en `FROM`, correlacionadas) | S | casos nuevos en `L3` | 14 |
| MG-P5-05 | `UNION/INTERSECT/EXCEPT/OUTER UNION CORR` | H | casos nuevos | 6 |
| MG-P5-06 | `CREATE TABLE/VIEW`, `INSERT`, `UPDATE`, `DELETE`, `ALTER`, `DROP` | H | casos nuevos | 8 |
| MG-P5-07 | `SELECT INTO :macro` y `DICTIONARY.*` | S | `L5` | 8 |
| MG-P5-08 | Funciones SAS dentro de SQL y portabilidad de dialecto | H | consistente con `rules/sas/sql-functions.json` | 8 |

**Estado (hito 104m, 5 de noviembre de 2026).** MG-P5-01 y MG-P5-02 a medias: `filter`, `derive`
y `join` se emiten como `tMap` —con conexión `LOOKUP` para las búsquedas— y el intérprete los ejecuta
con la semántica de SAS. De los 15 casos de `L1` quedan completos 3, y de los 15 de `L2`, 5; el resto
está en `tests/corpus/migrar_pendientes.yaml` por `P-FILTRO-SIN-TRADUCIR` (11), 
`P-ASIGNACION-SIN-TRADUCIR` (6) y los pasos que el emisor no cubre (`sort`, `dedup`, subconsultas).
MG-P5-03 en adelante, sin empezar.

### MG-P6. Procedimientos (50 h)
| Id | Tarea | Tipo | Aceptación | Horas |
|---|---|---|---|---|
| MG-P6-01 | `PROC SORT` completo (`NODUPKEY`, `NODUPREC`, `DUPOUT=`, `NOEQUALS`, `DESCENDING`) con `tUniqRow` (plantilla ya validada) | S | `L6`, `L8/totales/01` más los casos de `NOEQUALS` y `NODUPREC` | 10 |
| MG-P6-02 | `PROC FREQ` y `PROC MEANS/SUMMARY` | S | `L3` | 10 |
| MG-P6-03 | `PROC TRANSPOSE` | S | casos nuevos | 8 |
| MG-P6-04 | `PROC APPEND`, `COPY`, `DATASETS`, `DELETE`, `CONTENTS` | H | casos nuevos | 6 |
| MG-P6-05 | `PROC PRINT/REPORT/TABULATE/ODS`: política (omitir con aviso o `tLogRow`) | H | decisión documentada | 4 |
| MG-P6-06 | Lista de procedimientos fuera de alcance con motivo en `docs/cobertura.md` | H | generada | 2 |
| MG-P6-07 | `PROC FORMAT` y `PROC SQL` avanzadas que falten | S | según corpus real | 10 |

### MG-P7. Macros (60 h)
| Id | Tarea | Tipo | Aceptación | Horas |
|---|---|---|---|---|
| MG-P7-01 | Expansor estático completo: `%LET`, `&var`, `&&var&i`, `%MACRO` con parámetros, `%IF`, `%DO` (con y sin límites constantes), `%EVAL`, `%SYSFUNC`, citado | S | `L5` (12) más casos del anexo | 16 |
| MG-P7-02 | Macros que se repiten: detección de bloques idénticos con distinto parámetro para convertirlos en joblet (alimenta MG-P8) | S | informe de repeticiones en los programas del repositorio | 10 |
| MG-P7-03 | `%INCLUDE` y autollamadas | H | `L5` | 4 |
| MG-P7-04 | Variables de macro de tiempo de ejecución (`CALL SYMPUT`, `SELECT INTO`) a contexto o variable global | S | casos nuevos | 8 |
| MG-P7-05 | Huecos del analizador: `%IF` en macro con parámetro, `PROC DOWNLOAD` en `RSUBMIT`, WORK leída antes de crearse, `sql_tree` con subconsultas en `FROM` | S | los 3 programas del hueco ya analizan | 12 |
| MG-P7-06 | `CALL EXECUTE` y código dinámico: pendiente con motivo y forma documentada (MG-D04) | H | pendientes con código estable | 4 |
| MG-P7-07 | Opciones del sistema que cambian resultados (`MISSING=`, `YEARCUTOFF`, `VALIDVARNAME`, `MERGENOBY`): detección y aviso | H | `lesysoptsref` citada | 6 |

### MG-P8. Planificador de arquitectura (70 h)
Convierte el plan lógico en la organización de Jobs. Es el paso que hoy no existe para un programa nuevo.

| Id | Tarea | Tipo | Aceptación | Horas |
|---|---|---|---|---|
| MG-P8-01 | Segmentación en Jobs desde el linaje: etapas (insumos, producto, totales, cierre), regiones y dependencias por tablas permanentes y archivos | S | `sgm diseno` sobre `L1`–`L8` y `tests/fixtures/sas` produce padre e hijos sin YAML | 14 |
| MG-P8-02 | Política de tamaño: un Job no pasa del límite (20 por omisión); se corta en hijos por subgrafo coherente, minimizando datos que cruzan Jobs | S | ningún Job del corpus pasa del límite | 12 |
| MG-P8-03 | Extracción a joblets de bloques repetidos o de utilidad (normalizar, validar documento, validar ubicación, conciliar, registro de errores, conexión) con parámetros de contexto | S | requiere MG-P9-03; el corpus con repeticiones genera joblets | 14 |
| MG-P8-04 | Contextos por programa: parámetros deducidos (rutas de `LIBNAME`/`INFILE`/`FILENAME`, macrovariables que cambian entre entornos, fechas, umbrales) con grupos DEV, QA y PROD | S | cada programa del corpus trae su grupo de contextos y su tabla de parámetros | 10 |
| MG-P8-05 | Paso de datos entre Jobs: archivos de trabajo (mecanismo (b) validado), `tBufferOutput` o conexión compartida según el caso; nunca `tHash*` entre Jobs | S | prueba de dos Jobs que se pasan una tabla | 8 |
| MG-P8-06 | Errores y registro por defecto: `OnSubjobError`, `tDie` con código, `tLogCatcher`, política de fallo parcial (DC-08) configurable | S | cada Job emitido pasa Q6 y Q7 | 6 |
| MG-P8-07 | Nombres, etiquetas, notas y trazabilidad (`trace.json`) | H | Q10 | 6 |

**Estado (hito 104m, 5 de noviembre de 2026).** MG-P8-04 hecho: cada Job sale con los cuatro
grupos `Default`, `DEV`, `QA` y `PROD` con las mismas claves, una variable `ruta_<tabla>` por ruta
literal del SAS, el valor solo en `Default` y los demás vacíos, más un `contextos/<grupo>.yaml` por
grupo; ninguna ruta queda dentro del `.item`. MG-P8-07 a medias: `trace.json` da las líneas del SAS
de cada nodo. MG-P8-01, MG-P8-02, MG-P8-03, MG-P8-05 y MG-P8-06 son de los planes siguientes.

### MG-P9. Emisor de Talend: plantillas, joblets, contextos, disposición (108 h)
| Id | Tarea | Tipo | Aceptación | Horas |
|---|---|---|---|---|
| MG-P9-01 | **Biblioteca de plantillas de componentes**: priorizar los 40 componentes que usa el catálogo de la sección 5 y generar su plantilla desde Studio (o con `talend_components_generate_template` y comprobación de que compila y ejecuta). Lista mínima: `tFileInputDelimited/Positional/Excel/Regex`, `tFileOutputDelimited/Excel/Positional`, `tMap`, `tFilterRow`, `tAggregateRow`, `tSortRow`, `tUniqRow`, `tJoin`, `tNormalize`, `tDenormalize`, `tReplicate`, `tJavaRow`, `tJava`, `tConvertType`, `tFlowToIterate`, `tIterateToFlow`, `tLoop`, `tRunJob`, `tPrejob`, `tPostjob`, `tDie`, `tWarn`, `tLogCatcher`, `tStatCatcher`, `tSetGlobalVar`, `tContextLoad`, `tFileList`, `tFileCopy`, `tFileDelete`, `tFileExist`, `tSleep`, `tWaitForFile`, `tSendMail`, `tSystem`, `t<DB>Connection/Input/Output/Row/Close/Commit` para Impala y Postgres, `tHashOutput/Input` (solo dentro de un Job), `tBufferOutput` | S | 40 plantillas con prueba: compilan y ejecutan con datos; procedimiento del hito 61 | 30 |
| MG-P9-02 | Catálogo único de plantillas con metadatos (qué parámetros son obligatorios, qué se neutraliza, qué es sensible) y generador de plantilla nueva automatizado | S | agregar un componente cuesta menos de 30 minutos | 10 |
| MG-P9-03 | **Joblets**: investigar y validar en Studio 8.0.1 cómo se crea, se guarda (`.item` de joblet, carpeta `joblets/`) y se usa uno (`tJobletInput`, `tJobletOutput`, nodo `joblet`, parámetros de contexto del joblet, triggers); escribir el emisor | S | un joblet con parámetros usado en dos Jobs, compilado y ejecutado; si Studio no lo permite desde archivos, plan B documentado con el equivalente (Job hijo con `tRunJob`) y la regla de cuándo cada uno | 20 |
| MG-P9-04 | **Contextos**: grupos Default, DEV, QA y PROD en el `.item` y en los archivos `.properties` de contexto; tipos; valores por entorno cargados desde `contextos/<entorno>.yaml` (sin secretos); `tContextLoad` cuando aplique | S | Job ejecutado con `--context=DEV` y `--context=QA` imprime el valor de cada uno | 10 |
| MG-P9-05 | Conexiones: `OnSubjobOk`, `OnComponentOk`, `Run if`, `OnSubjobError`, `Iterate`, `Lookup`, `Reject`, `Main`, `Filter`, orden de ejecución con `ORDER` | H | cada tipo con una prueba | 6 |
| MG-P9-06 | Disposición en el lienzo (`posX/posY`) por orden de flujo, subjobs agrupados, sin superposición | H | Q11 | 6 |
| MG-P9-07 | Propiedades del Job (propósito, descripción, versión, autor), anotaciones y notas con la línea de SAS | H | Q10 | 4 |
| MG-P9-08 | Rutinas Java compartidas (si hacen falta funciones de SAS sin equivalente) como rutina de repositorio con prueba; **solo cuando una expresión inline no alcance** | S | decisión y prueba | 8 |
| MG-P9-10 | Comparar el emisor propio con `talend_jobs_create_from_spec` para los mismos planes: diferencias de `.item` explicadas; adoptar del MCP lo que Studio acepte y el emisor propio no (por ejemplo componentes con modelo que solo Studio resuelve, como `tMap` con metadatos) | S | informe de diferencias; los componentes difíciles tienen un camino probado | 8 |
| MG-P9-09 | Ida y vuelta en el editor de Studio (Q14): **una persona** abre un Job emitido y lo guarda; el agente compara y corrige el emisor hasta que Studio no cambie nada | P+S | informe de diferencias en cero | 6 + 1 día-persona |

### MG-P10. Verificación y equivalencia (80 h)
| Id | Tarea | Tipo | Aceptación | Horas |
|---|---|---|---|---|
| MG-P10-01 | Intérprete de referencia en Python de la IR lógica (anillo B) con la semántica SAS documentada | S | todos los casos `traducible` del corpus dan su `esperado/` | 20 |
| MG-P10-02 | Validador estructural del `.item` (anillo A) | H | rechaza Jobs con conexiones huérfanas, esquemas incompatibles, nombres repetidos | 8 |
| MG-P10-03 | Compilación de las expresiones Java generadas con `javac` suelto | H | cada expresión generada compila sola | 6 |
| MG-P10-04 | Casos que faltan: L7 (varias etapas con rechazos y conciliación) y L9 (programa grande con datos simulados), 10 casos más por nivel con esperado por construcción | H | 40 casos nuevos con anomalías plantadas | 14 |
| MG-P10-05 | Generador de programas SAS (sección 6.3) con reducción automática de fallos | S | encuentra y reduce al menos un error real; los fallos pasan al corpus | 12 |
| MG-P10-06 | Prueba de mutación del arnés: alterar un esperado y comprobar que el arnés falla | H | 100 % detectado | 3 |
| MG-P10-07 | Corrida nocturna (anillo D) con informe y alerta de regresión | H | informe diario en `out/` | 6 |
| MG-P10-08 | Informe de cobertura `sgm cobertura` (C1) generado desde reglas y corpus | H | `docs/cobertura.md` y JSON | 6 |
| MG-P10-09 | Segundo y tercer programa del cliente (los de `tests/fixtures/sas/real` y `synthetic`): medir cobertura y cerrar las brechas más frecuentes de forma iterativa | S | cobertura medida y creciente | 15 |

**Estado (hito 104m, 5 de noviembre de 2026).** MG-P10-02 hecho: `validar_job` aplica las seis
reglas de Studio sobre el modelo y los 45 Jobs de `L0` a `L2` salen limpios; encontró un defecto real
del emisor —dos salidas `row1` del mismo nodo cuando la tabla se lee dos veces—. MG-P10-01 a medias: el
intérprete ejecuta `read_file`, `write_file` y `map` con `join`, `filter` y `derive`, y 14 de los 43
casos `traducible` o `revisado` dan su `esperado/`; los otros 29 son `xfail(strict=True)` con el
motivo escrito. La semántica vive en `migrar/semantica.py` y sale de `semantica/vectores.yaml`.

### MG-P11. Experiencia de uso (30 h)
| Id | Tarea | Tipo | Aceptación | Horas |
|---|---|---|---|---|
| MG-P11-01 | Comando único `sgm migrar <programa o carpeta> --out <carpeta>`: corre todas las capas, escribe los Jobs, `trace.json`, `pendientes.md`, `cobertura.md` y `contextos/` | S | un comando de entrada y salida sin YAML | 8 |
| MG-P11-02 | Sobreescrituras opcionales por YAML (nombres, agrupación, valores de contexto) y validación con mensajes claros | H | un YAML erróneo da un mensaje con archivo y línea | 4 |
| MG-P11-03 | Programa de varios archivos y carpetas completas (orden por dependencias entre programas) | S | una carpeta con 5 programas se migra a un proyecto coherente | 8 |
| MG-P11-04 | `sgm explicar <línea>` (qué se tradujo y a qué componente) y `sgm comparar` (SAS contra Talend) integrados | H | usan `trace.json` | 4 |
| MG-P11-05 | Mensajes de error y de pendiente claros, en español, con código estable y sugerencia | H | todos los códigos tienen texto | 4 |
| MG-P11-06 | Documentación: guía de usuario, guía de operación, catálogo de construcciones soportadas | H | generada y revisada | 2 |

**Estado (hito 104m, 5 de noviembre de 2026).** MG-P11-01 a medias: `sgm migrar <programa.sas>
--out <carpeta>` corre todas las capas sin ningún YAML y escribe `process/`, `contextos/`,
`pendientes.md`, `configuracion-pendiente.md`, `decisiones-tomadas.md`, `trace.json` y
`migracion.log`, con salida determinista y código 0 siempre. Falta la carpeta completa (MG-P11-03),
`cobertura.md` y las sobreescrituras por YAML (MG-P11-02).

### MG-P12. Rendimiento y escala (30 h)
| Id | Tarea | Tipo | Aceptación | Horas |
|---|---|---|---|---|
| MG-P12-01 | El migrador procesa el programa de 800 KB y la carpeta de 189 en tiempo razonable (meta: menos de 2 min y menos de 1 GB) | S | medido en `metrics` | 8 |
| MG-P12-02 | Rendimiento de los Jobs generados con volumen (millones de filas): lookups, `tMap` en memoria, paralelización, `tSortRow` externo, tamaño de búfer | S | prueba con 5 a 50 millones de filas en contenedor; límites documentados | 14 |
| MG-P12-03 | Plantillas de configuración de la JVM y de Talend para volumen (`-Xmx`, paginación) | H | documento y pruebas | 4 |
| MG-P12-04 | Caché del análisis (`.sgm-cache/`) para repetir corridas | H | segunda corrida más rápida y con la misma salida | 4 |

### MG-P13. Seguridad y cumplimiento (20 h)
| Id | Tarea | Tipo | Aceptación | Horas |
|---|---|---|---|---|
| MG-P13-01 | `sgm secretos` como compuerta (existe) integrada en `sgm migrar` y en la corrida nocturna | H | falla si algo se filtra | 3 |
| MG-P13-02 | Revisar el `{SAS002}` de `tests/fixtures/sas/real/ci360-download-client/macros/dsc_download.sas:55` y el adjunto sin versionar con `pwencode` | P | confirmado público o rotado | 0,5 día-persona |
| MG-P13-03 | Datos personales: los registros y archivos de rechazo no copian columnas sensibles si no se pidió (lista configurable) | S | prueba | 5 |
| MG-P13-04 | Auditoría de dependencias y licencias; SBOM | H | `docs/sbom.md` | 3 |
| MG-P13-05 | Revisión de seguridad de la generación (inyección en literales SQL y en expresiones Java generadas, escapes) | S | pruebas con entradas hostiles | 9 |

### MG-P14. Producción (agente 40 h, personas unos 40 días)
| Id | Tarea | Tipo | Aceptación |
|---|---|---|---|
| MG-P14-01 | Empaquetado: `uv tool install` o paquete `wheel`, versión semántica, registro de cambios, comando `sgm --version` | H | instala en una máquina limpia (persona verifica una vez) |
| MG-P14-02 | Compuerta de liberación: CI local que corre A, B, D, `ruff`, `sgm secretos`, determinismo y, con Studio disponible, `talend_job_build_batch` de toda la salida | H | un comando decide si se libera |
| MG-P14-03 | Guía de despliegue según MG-D10 y runbook de operación (usar la habilidad `qlik-documentos` para el Word) | S | documento firmado |
| MG-P14-04 | Piloto: 3 programas reales del cliente (MG-D08) migrados; revisión de los Jobs con el equipo de Talend | P+S | lista de hallazgos cerrada |
| MG-P14-05 | UAT de Negocio sobre los resultados del piloto | P | acta de aceptación |
| MG-P14-06 | Corrida paralela: SAS y Talend con los mismos datos durante un ciclo completo; comparar con `sgm comparar` y la tolerancia MG-D07 | P+H | diferencias explicadas o cero |
| MG-P14-07 | Monitoreo y alertas: correo, códigos de salida, conteos publicados, ruta de escalamiento | S+P | pruebas de alerta |
| MG-P14-08 | Plan de contingencia y reversa: mantener SAS en paralelo hasta el corte | P | documento |
| MG-P14-09 | Capacitación al equipo operador | P | sesión y material |
| MG-P14-10 | Corte a producción y firma | P | acta firmada por Negocio y Tecnología |
| MG-P14-11 | Soporte de estabilización (2 a 4 semanas): lista de defectos, correcciones, parches con prueba | S+P | cero defectos críticos abiertos |

## 10. Compuertas y ruta crítica

| Compuerta | Condición | Fases |
|---|---|---|
| GM0 | Entorno rápido: anillos A y B funcionando; Studio con salud en 10 s; lote C funcionando | P0 |
| GM1 | El plan lógico se construye para todo el corpus `traducible`; sin YAML | P1 |
| GM2 | `L0` a `L3` traducidos y verificados (B y C) | P2, P3 (motor), P5 (01 a 03) |
| GM3 | `L4` a `L6` traducidos y verificados | P3, P4, P6, P7 |
| GM4 | Arquitectura por omisión: padre, hijos, joblets o su plan B, contextos y límites; lista Q1 a Q15 al 100 % sobre el corpus | P8, P9 |
| GM5 | Corpus completo (L0 a L9) en verde y corrida nocturna estable 14 días | P10 |
| GM6 | `sgm migrar` con documentación, mensajes y rendimiento | P11, P12, P13 |
| GM7 | Piloto y corrida paralela con diferencias explicadas | P14-04 a P14-06 |
| GM8 | Corte firmado | P14-10 |

Ruta crítica: P0 hasta P1, luego P2 y P3 en paralelo, luego P4, P5 y P6, luego P8 con P9 (el joblet MG-P9-03 es el
mayor riesgo técnico: empezar su investigación en la primera semana, en paralelo), luego P10 y P14.

Carriles en paralelo (con la restricción de que Studio es un solo recurso compartido y se usa por lotes):
1. Núcleo semántico y expresiones: P1, P3.
2. Traducción: P2, P4, P5, P6, P7.
3. Emisión y arquitectura: P8, P9 (incluida la investigación temprana de joblets).
4. Verificación: P10.
5. Producto y operación: P11, P12, P13, P14.

## 11. Esfuerzo y calendario

| Fase | Horas de agente |
|---|---|
| P0 | 37 |
| P1 | 70 |
| P2 | 50 |
| P3 | 80 |
| P4 | 90 |
| P5 | 80 |
| P6 | 50 |
| P7 | 60 |
| P8 | 70 |
| P9 | 108 |
| P10 | 80 |
| P11 | 30 |
| P12 | 30 |
| P13 | 20 |
| P14 | 40 |
| **Total** | **895** |

Con cuatro carriles de agentes y el lote de Studio como cuello de botella, el calendario realista es de 8 a 10
semanas de trabajo de agentes hasta GM6, más el calendario de personas de P14 (piloto, UAT, corrida paralela de
un ciclo completo del negocio, estabilización), que depende de los ciclos del cliente y no del código.

## 11b. Avance medido (7 de noviembre de 2026, hito 126m)

**Avance global: 27,1 % de las 895 horas de agente (242,75 h), es decir, cerca de 27 %** (era 19,6 % en el
hito 107). C7 (producción con personas) está en 0 %; ningún criterio C1 a C6 está cumplido todavía. Ojo:
los hitos 108m a 126m se apoyan en los anillos A y B; **el hito 125m compiló 85 de 85 Jobs de L0 a L6
en Studio, pero ninguno se ejecutó**, y por eso el crédito de P9 y P5 se cuenta con 0,25 y no con 0,5 en
lo que solo tiene Job escrito y validado por `validar_job`.

**Método (reproducible a mano).** Cada tarea `MG-Pn-mm` aporta sus horas multiplicadas por un crédito:
1 = hecha y su aceptación comprobada; 0,5 = parcial con evidencia de ejecución (corpus pasa en A o B, o
Studio); 0,25 = solo casos o funciones puntuales, sin el alcance de la aceptación; 0 = sin empezar o sin
evidencia. Los créditos salen de las secciones «Estado» de cada fase y de `PROGRESS.md`. Lo heredado de
la pista del programa grande que nadie midió contra el corpus (por ejemplo, el expansor de macros de
`MG-P7`) cuenta 0 hasta que un caso lo demuestre. **Al cerrar un hito, recalcula la fila de su fase.**

| Fase | Horas | Crédito | % de la fase | Qué sostiene la cifra |
|---|---|---|---|---|
| MG-P0 Preparación | 37 | 25,0 | 68 % | Backend, salud, lote, ciclo rápido hechos; faltan MG-P0-01 y 06, y las mediciones de tiempo |
| MG-P1 Modelo y plan lógico | 70 | 43,0 | 61 % | Pendientes y propiedad hechos; tabla de símbolos L0 a L2; tipos deducidos de comparaciones y agregados; sin tipos desde la muestra |
| MG-P2 Entrada y salida | 50 | 12,0 | 24 % | CSV y DLM; sin XLSX, bases, `FILENAME` ni `RSUBMIT` |
| MG-P3 Expresiones y funciones | 80 | 14,5 | 18 % | Funciones puntuales con evidencia; sin fechas, PRX ni `PROC FORMAT` |
| MG-P4 DATA step | 90 | 21,0 | 23 % | `IF/ELSE` con `DO/END`, `SET` de varias tablas, `MERGE` (intérprete; emisor solo `inner`/`left`), `BY` con `FIRST.`/`LAST.`/`RETAIN`/suma (plan e intérprete, sin emisor); sin `OUTPUT` múltiple ni `ARRAY` |
| MG-P5 `PROC SQL` | 80 | 37,0 | 46 % | `ORDER BY`, `DISTINCT`, `GROUP BY` y agregados (también compuestos), `UNION ALL`, `IN`/`NOT IN` con subconsulta simple, cruces de tres tablas; sin auto-`JOIN`, subconsulta escalar ni `full`/`right` |
| MG-P6 Procedimientos | 50 | 4,0 | 8 % | `PROC SORT` con `NODUP`/`NODUPKEY` y `BY _ALL_`; sin `FREQ`, `MEANS`, `TRANSPOSE` |
| MG-P7 Macros | 60 | 8,0 | 13 % | `L5`: 8 de 12 casos pasan en el anillo B (`%let`, macro con parámetros, `%eval`); sin `%sysfunc` ni `SELECT INTO` |
| MG-P8 Planificador | 70 | 15,0 | 21 % | Contextos DEV/QA/PROD; `trace.json` parcial; plantillas repetidas desplegadas en línea (provisional); sin segmentación ni límite de tamaño |
| MG-P9 Emisor | 108 | 34,5 | 32 % | 29 de 40 plantillas con nodo emitido (`tSortRow`, `tUniqRow`, `tAggregateRow`, `tUnite` nuevos, sin Studio), contextos y conexiones; joblets sin validar |
| MG-P10 Verificación | 80 | 24,0 | 30 % | Validador del `.item` hecho; intérprete B: 86 de 93 casos elegibles pasan (L0 a L6), 7 `xfail`; el comparador sigue sin ser estricto con columnas de más |
| MG-P11 Experiencia de uso | 30 | 4,0 | 13 % | `sgm migrar` de un programa sin YAML; falta carpeta y `cobertura.md` |
| MG-P12 Rendimiento | 30 | 0,0 | 0 % | Sin empezar |
| MG-P13 Seguridad | 20 | 0,75 | 4 % | `sgm secretos` existe, sin integrar en `sgm migrar` |
| MG-P14 Producción | 40 | 0,0 | 0 % | La compuerta de liberación quedó verde en el hito 126m, pero no se acredita: su aceptación incluye el lote de Studio sobre toda la salida y eso sigue pendiente; la parte de personas tampoco cuenta aquí |
| **Total** | **895** | **242,75** | **27,1 %** | |

**Reparto del trabajo restante (719,25 h) entre Andres y Byron:** `reparto-andres-byron.md`
(359,0 h y 360,25 h).

**Termómetros directos del corpus** (más honestos que las horas, porque no dependen de mi crédito):anillo B, 86 de 93 casos elegibles pasan (92 %; hito 123m); anillo A, 84 de los 101 casos de `L0` a `L6` migran sin pendientes de traducción (83 %; hito 123m); Studio, 85 de 85 Jobs de `L0` a `L6` compilan tras los arreglos del hito 125m y **ninguno se ejecutó** ni se comparó con su esperado.

**Qué mueve más el número.** La ruta crítica pide P4, P5 y P6 antes que P8 y P9; ahí hoy hay 9,8 %
de crédito (21,5 de 220 horas). Lo que más sube el porcentaje por hora es `MG-P5-02` a `P5-04`,
`MG-P4-03` a `P4-05` y `MG-P9-03` (joblets, el mayor riesgo técnico, sin validar en Studio).

## 12. Riesgos y mitigaciones

| Riesgo | Efecto | Mitigación |
|---|---|---|
| Los joblets no se pueden generar desde archivos en Studio 8.0.1 | No hay reutilización real | investigar primero (MG-P9-03); plan B documentado: Job hijo con `tRunJob` y regla clara; no bloquea GM4 si el plan B queda validado |
| `MERGE` mal traducido a `JOIN` | Resultados distintos sin aviso | semántica en el intérprete, casos de la guía de SAS y de `L6` |
| Faltantes y blancos mal tratados | Diferencias sutiles | vectores con fuente y generador de programas; revisión por pares de cada función |
| Código dinámico (`CALL EXECUTE`, macros generadoras) | No se puede traducir | pendiente con motivo y forma documentada; no se omite |
| Sin SAS real, el esperado puede tener un supuesto equivocado | Falsa confianza | tres mecanismos independientes; marcar `pendiente_revision`; MG-D09; corrida paralela |
| Studio lento o bloqueado | Desarrollo lento | pirámide de pruebas; lote; salud de 10 s; simuladores |
| Plantillas de Talend dependen de la versión 8.0.1 | Roturas con otra versión | plantillas versionadas; prueba que lee la versión de Studio; regenerar con el procedimiento automatizado |
| Crecimiento del código | Mantenimiento | archivos pequeños, una responsabilidad; `ruff`; pruebas de propiedad |
| Dependencias nuevas | Seguridad y mantenimiento | MG-D02 con valor por omisión sin dependencias |
| El cliente cambia de versión de SAS | Casos de borde | MG-D01, guía por versión en `rules/sas/` |

## 13. Cierre de cada tarea (protocolo, siempre igual)
1. Escribir primero el caso del corpus o el vector que prueba la tarea, con esperado independiente.
2. Implementar la regla leyendo la guía; citar guía y página en el comentario y en la ficha.
3. Anillos A y B en verde. Después, un lote C con los Jobs del cambio.
4. `uv run pytest -q -n auto` y `uv run ruff check .` en verde.
5. Anexar la entrada del hito a `PROGRESS.md` con un script que añade bytes UTF-8 (el archivo mezcla
   codificaciones; no pegar Python con `\n` en `heredoc` de shell), con la salida literal de Studio y las
   salvedades honestas.
6. Actualizar el estado de la tarea en esta página y en el tablero.
7. Commit local `hito N<letra>: <resumen>` con la línea de coautoría; `git add` solo de los archivos propios; sin
   `--amend` ni `rebase` sobre commits ajenos; sin `git push`.

## 14. Qué entregar al agente que lo implemente
- Este documento y los de la sección 0.1.
- Acceso a Docker, a Talend Studio 8.0.1 (`C:\Talend\8.0.1\studio`, proyecto `PRJ_BANCOLOMBIA`) y a
  `C:\Users\USUARIO_BISOLUTION1\code\talend-mcp` (solo desde `tools/` y `tests/`).
- Instrucción de empezar por MG-P0 y, en paralelo, la investigación de joblets (MG-P9-03) y el intérprete de
  referencia (MG-P10-01), porque son lo que más riesgo y valor concentra.
- Recordar: usar agentes haiku para el trabajo mecánico y reservar el criterio de diseño para quien coordina.
