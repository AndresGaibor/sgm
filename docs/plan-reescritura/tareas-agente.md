# Tareas para el siguiente agente: acercar la salida del migrador al diseño manual

Estado a 4 de noviembre de 2026, último commit `061313f` (hito 66). Este documento se escribió para que
otro agente (o varios, por bloques) trabaje durante horas sin depender de quien lo escribió. Léelo
completo antes de empezar. La meta del usuario no cambió: que lo que genera `sgm` se parezca lo más
posible a `docs/diseno-talend-exogena-depositos.md`, sin ser una demostración. El usuario autorizó
rehacer o borrar lo que estorbe, usar subagentes (modelo `haiku` para el trabajo mecánico; quien dirige
solo decide y revisa) y validar en el Studio real.

## 1. Estado actual

### 1.1 Lo que existe y está verificado

| Capa | Qué hace | Dónde |
|---|---|---|
| Frontend SAS | Lee el programa y deja sentencias y hechos | `src/sgm/frontend/` |
| Linaje | Qué paso escribe y lee cada dataset | `src/sgm/flow/` |
| Modelo de proceso | Regiones, familias por producto, fuentes y salidas, etapas, fontanería, pendientes | `src/sgm/proceso/` |
| Documento de diseño | Markdown con secciones 1.1, 1.4, 3 y 6 (`sgm proceso`) | `proceso/diseno_doc.py`, `render_md.py` |
| Emisor de Jobs | Escribe `.item` y `.properties` de Talend 8.0.1 (`sgm talend`) | `src/sgm/talend_item/` |
| Plantillas | 24 componentes extraídos de Jobs reales de Studio, en JSON | `talend_item/plantillas/` |
| Validación | Cada Job emitido se compila, se exporta y se ejecuta en el Studio instalado | sección 3 de este documento |

Cifras: 928 pruebas pasan, 1 se salta, 132 xfail (conformidad no emitida). `ruff check .` limpio.

### 1.2 Lo que `sgm talend client_large.sas` emite hoy (4 Jobs)

1. `job_exogena_depositos` (padre, completo): Prejob con validación de entorno (`tDie` con salida de VM
   si `env_nombre` no es DEV, QA o PROD), lectura del Excel de la fecha a variables de contexto
   (`periodo_anio`, `periodo_mes`, `periodo_dia`), iteración por producto (CTE, AHO, NEQUI) con
   `tFlowToIterate` y `tRunJob`, luego `job_totales`, `job_conciliacion` y Postjob.
2. `job_producto` (parcial): lee el CSV del producto (23 columnas, esquema deducido del SAS), cuenta
   registros y suma el saldo con `tMap` y `tAggregateRow`. Imprime `registros_origen|suma_saldo_origen`.
3. `job_totales` y `job_conciliacion`: esqueletos `tJava` que imprimen "PENDIENTE" y las variables
   heredadas del periodo.

Validado ejecutando el padre exportado con datos simulados: salida 0, tres productos, totales
`3|603.00` por producto.

### 1.3 Hallazgos que cambian el diseño manual (ya medidos o probados)

- Los datos de cada producto vienen de CSV, no de tablas Impala: `DBIFTCD.csv` (CTE), `DBIFTCS.csv`
  (AHO), `F_1019.csv` (NEQUI), sin cabecera, `;`, 23 columnas. `Base_datos_Nequi.csv` (6 columnas) es
  auxiliar. Sección 1.1 del diseño manual dice "Tabla Impala, pendiente": es incorrecta.
- No hay caché compartida entre Jobs. `tHashOutput` y `tHashInput` no cruzan Jobs con ninguna
  configuración (la clave del buffer lleva el nombre del Job). Una rutina Java estática funcionaría
  en teoría, pero Studio no carga rutinas nuevas sin reiniciar y el formato del `.item` de rutina no
  tiene ejemplo real. Se descartó. Decisión vigente: los Excel pequeños se leen como lookup dentro del
  `tMap` de `job_producto`; la fecha la lee el padre y los hijos la heredan por contexto. Esto
  contradice las secciones 1.2, 3.2 y 3.4 del diseño manual (no existe `job_insumos`).
- CTE, AHO y NEQUI comparten estructura de datos (23 columnas), lo que respalda un solo
  `job_producto` (decisión D6) en la capa de datos.
- Todo el catálogo de tablas WORK del SAS (348 en el manual) son aristas, no persistencia (D1).
  El colapso mecánico da unos 364 bloques; el manual tiene unos 80 componentes porque rediseña con
  joblets y un solo archivo de rechazos (D2). Ese salto no se cierra con colapso: pide joblets
  declarados y decisiones del negocio.
- Los totales de origen del SAS son conteo y `SUM(input(left(FIN_SALDO_CTA), 20.))`.
- La validación de tipo de documento del SAS es `LEFT JOIN ... ON TIPO_DOC = CNAME WHERE CNAME IS
  MISSING` (inválidos) e `INNER JOIN` (válidos), líneas 3428 a 3462 de `client_large.sas`.

### 1.4 Reglas del proyecto que no se pueden romper (`AGENTS.md`)

No MCP en el producto (`src/`, `rules/`); el MCP de `talend-mcp` solo se usa como validador desde la
línea de comandos, con permiso expreso del usuario. No API web ni frontend. No conectarse a bases.
No tocar el repo viejo. **Nada de `git push`.** Un commit local por hito, mensaje `hito N: <resumen>`
terminado en `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. No inventar datos: lo que el
SAS no demuestra queda pendiente con su motivo. Ninguna contraseña en claro. No borrar ni debilitar
pruebas. Prohibido en `src/` y `rules/` los nombres de scripts del cliente (`cod1`, `cod2`, `cars_poc`,
`exogena`, `split2`, `split3`, `executeBulkload`, `waitForBulkLoads`, `bulkload_generic`). Archivos de
300 líneas como máximo. Identificadores en inglés para la capa SAS; comentarios, docstrings y mensajes
en español (el paquete `talend_item` usa nombres en español, sigue ese estilo). Después de cada cambio:
`uv run pytest -q` y `uv run ruff check .`. Al cerrar un hito: sección nueva en `PROGRESS.md` (anexar
en bytes UTF-8: el archivo mezcla codificaciones). Dependencias permitidas: networkx, typer, pyyaml,
pydantic (dev: pytest, pytest-xdist, ruff).

## 2. Distancia contra el diseño manual

| Sección del diseño manual | Estado | Qué falta |
|---|---|---|
| 1.1 Fuentes externas | Parcial, con corrección | Emitir los CSV de producto y el auxiliar; marcar Impala solo donde el SAS lo lea de verdad |
| 1.2 Cachés | Desviación decidida | Documentar la desviación; eliminar la tabla de cachés del documento emitido |
| 1.3 Variables globales | Cambiadas a contexto | Documentar |
| 1.4 Salidas | Parcial | Emitir las salidas reales (`RESULTADO_<P>_NAL/EXT.csv`, `INCONS_DEP_<P>.csv`, totales, conciliación) |
| 2 Contextos | Parcial | `impala_*`, `ruta_resultados`, `tolerancia_conciliacion`, `log_nivel`, grupos por entorno completos |
| 3.1 Padre | Hecho | Conexión Impala compartida, tratamiento de error (OnSubjobError) |
| 3.2 `job_insumos` | Eliminado | Documentar |
| 3.3 `job_producto` | 3 de ~17 componentes | Validaciones, correcciones, salidas, totales de salida |
| 3.4 `job_totales` | Esqueleto | Mecanismo para recibir totales de los productos sin caché |
| 3.5 `job_conciliacion` | Esqueleto | Diferencias, tolerancia, falla si excede |
| 4 Joblets | No existen | Formato del `.item` de joblet y los seis joblets del diseño |
| 5 Decisiones | Documento | Reflejar las nuevas (sin caché, CSV) |
| 6 Equivalencias | Hecho por reglas | Filas estructurales |
| 7 Pendientes y riesgos | Parcial | Actualizar con lo probado (R de caché cerrado) |
| 8 Orden de construcción | No emitido | Derivarlo de las dependencias reales |

## 3. Protocolo de validación en Studio (léelo antes de la primera tarea)

El servidor de validación vive en `C:\Users\USUARIO_BISOLUTION1\code\talend-mcp`. Se arranca con
`export TALEND_PROJECT="C:/Talend/8.0.1/studio/workspace/talendbancolombia-963626413/PRJ_BANCOLOMBIA"`
y `nohup bun run start:server > /tmp/mcp.log 2>&1 &` desde ese directorio. Comprueba
`curl -s http://127.0.0.1:3927/healthz`. Se invoca con
`bun run scripts/mcp-call.ts <tool> '<json>'`.

Pasos por intento (compilar no basta: hay que ejecutar y mirar las filas):

1. Generar los Jobs con un **nombre nuevo** (sufijo `_v1`, `_v2`): Studio guarda en memoria cada Job por
   su identificador y, si reemites el mismo nombre con otro contenido, compila la versión vieja aunque
   refresques el workspace. Los ids de `sgm` son deterministas por nombre y versión.
2. Copiar los `.item` y `.properties` a `PRJ_BANCOLOMBIA/process/`.
3. `talend_bridge_refresh_workspace '{}'`.
4. `talend_job_build_batch` con los **hijos primero** y el padre en una llamada aparte (en paralelo el
   padre puede fallar porque los hijos aún no están compilados). Leer `data.result.jobs[...].ok` y el
   error de javac.
5. `talend_deliverables_build_job '{"jobName":"<padre>","destinationDir":"<carpeta>"}'`.
6. Ejecutar el lanzador con el Java de Studio en el PATH (PowerShell):
   `$env:PATH = "C:\Talend\8.0.1\zulu21.50.19-ca-jdk21.0.11-win_x64\bin;$env:PATH"` y
   `& .\<padre>_run.bat [--context=DEV] [--context_param clave=valor]`. La consola muestra mal las tildes:
   no es un error.
7. **Borrar** del proyecto los Jobs de prueba (rutas literales, o `${VAR:?}`: el sistema bloquea `rm`
   con variables sin comprobar) y refrescar el workspace.

No uses `talend_job_execute`: no carga los archivos de contexto (el grupo `DEV` no se encuentra). No uses
`talend_job_verify` ni la creación de Jobs en vivo: un diálogo "Network Issue" de Studio los bloquea y
no hay que cerrarlo. La ruta sin interfaz funciona.

Datos simulados: `tools/simular_insumos.py` (Excel) y `tools/simular_productos.py` (CSV de producto,
con `--saldo COLUMNA`). Para simular localmente se parchea el `.item` del padre emitido (rutas UNC del
cliente por carpetas locales y `env_nombre=DEV`); el script que lo hacía vive en el scratchpad de la
sesión anterior y debe reescribirse en `tools/` (tarea T01).

### Hechos de Studio ya aprendidos (no los redescubras)

- Una conexión Run if con `ACTIVATE=false` está desactivada. Studio omite el parámetro si está activa.
- Una plantilla extraída de un componente desactivado (`ACTIVATE=false`) no genera código. La
  extracción descarta `ACTIVATE`.
- `tDie` en un Prejob no detiene el flujo principal salvo con `EXIT_JVM=true`.
- `tFileInputExcel` con `VERSION_2007` no compila si `PASSWORD` está vacío o vale `***` (Studio lo toma
  como máscara): se pasa un marcador normal. Una cadena `enc:...` tampoco sirvió.
- `lineStyle` verificados: fila 0, OnSubjobOk 1, OnComponentOk 3, Run if 6, Iterate 7, lookup 8
  (FLOW_REF), merge 10, paralelizar 13. OnSubjobError y OnComponentError no tienen ejemplo real.
- La fuente de un OnSubjobOk es el nodo de inicio del subjob, no el último componente.
- El código `CODE` de `tDie` y `tWarn` es el código de salida numérico, no código Java.
- La exportación de Jobs con `tFileInputExcel` pide poms públicos de Maven que faltaban en la caché
  local de Studio (`logging-parent` 11.3.0, `log4j-bom` 2.24.2 y 2.24.3). Se descargaron a
  `C:\Talend\8.0.1\studio\configuration\.m2\repository`. Si aparece otro, el error está en
  `workspace/.metadata/.log` (busca "could not be resolved") y se descarga igual.
- El validador de `talend-mcp` rechaza salidas de `tReplicate` (toma `MAX_OUTPUT` ausente como 0); en
  Studio no tienen límite. Las conexiones se escriben directamente.
- Los archivos `.py` de `talend_item` están en CRLF en su mayoría. Al editar con Python desde Bash no
  uses `\n` ni `\b` dentro de heredocs (se corrompen): escribe el script a un archivo con la
  herramienta Write. Comprueba `git diff --stat` para no reescribir archivos enteros.

## 4. Tareas

Convenciones: **[H]** apta para un subagente `haiku` con la especificación de la tarea; **[D]** requiere
decisión de diseño de quien dirige antes o después; **[R]** investigación con validación ejecutada.
El tiempo es una estimación para un agente. Cada tarea termina con pruebas, `ruff`, una sección en
`PROGRESS.md` y un commit local. Orden recomendado: T01 a T03 primero (aceleran todo lo demás), luego
bloques A y B en paralelo, después C, D y E.

### Bloque 0. Herramientas que aceleran el resto

**T01 [H] Validador automático en `tools/` (1 h).** Convierte el protocolo de la sección 3 en
`tools/validar_en_studio.py`: recibe un programa SAS, un YAML de nombres, una carpeta de datos
simulados y un sufijo; emite, parchea, copia, compila hijos y luego padre, exporta, ejecuta con y sin
contexto y devuelve la salida y el código de salida; borra siempre los Jobs de prueba al terminar (aunque
falle). Habla con `http://127.0.0.1:3927/mcp` por HTTP (`urllib`, sin dependencias). No es parte del
producto: vive en `tools/` y se documenta como validador externo. Incluye la reescritura del parcheo de
rutas locales. Criterio: con un solo comando reproduce la validación del hito 65 (`3|603.00`).

**T02 [H] Autodescarga de poms de Maven (30 min).** Ciclo "exportar, leer el log, descargar lo que falta,
reintentar" como función de T01 (hasta 8 rondas). Criterio: exportar un Job con Excel desde una caché
vacía de los poms conocidos.

**T03 [H] Emulador de Impala (1 h).** El SAS lee tablas Impala (`resultados_vspc_clientes.master_customer_data`,
`S_CANALES.SAI_SCILIBRAMD_SCIFFIMGFR`, `proceso_vspc_finanzas.MCDQ`). No hay Impala. Escribe
`tools/simular_tablas.py` que, dado el programa, genere CSV con las columnas que el SAS usa de cada
tabla (reutiliza `columnas_usadas`) y define una convención para que un Job lea un CSV en vez de la
tabla cuando el contexto lo indica (variable `modo_simulacion`). Criterio: los Jobs que lean Impala
compilan siempre y se ejecutan contra CSV en simulación.

**T04 [H] Prueba de humo en `pytest` sin Studio (45 min).** Una prueba que recorra los cuatro Jobs
emitidos y compruebe cosas que ya fallaron antes: ningún `ACTIVATE=false`, todo `tRunJob` apunta a un
Job que existe, cada conexión referencia nodos existentes, cada `UNIQUE_NAME` es único, ningún
parámetro `PASSWORD` con valor en claro, toda variable `context.X` usada en un `tJava` o expresión está
declarada en el contexto del Job, y todos los `.item` son XML bien formado. Criterio: rompe si alguien
repite los errores del hito 61.

### Bloque A. `job_producto`: las validaciones del SAS

El detalle de las etapas y cuántos bloques tiene cada una está en `sgm proceso` (sección 3 del documento).
Las etiquetas del SAS que corresponden a cada validación están en el rango de líneas 3161 a 4290 de
`client_large.sas` (región de AHO); la de CTE es una copia con otro sufijo (familias 5 y 6).

**T10 [H] Validación de tipo de documento con lookup (2 h).** Hay una especificación completa de esta
tarea en el último prompt de la sesión anterior (se resume aquí). Reemplazar el cuerpo de
`jobs_producto.py` por: `tFileInputDelimited`, `tReplicate`, rama A (totales de origen, ya existe), rama
B: `tMap` con lookup (`tFileInputExcel` del Excel de homologación, `FILENAME = context.ruta_insumos +
context.arch_hom_tipo_doc`) con `union_interna` y `rechazo_union`; salida `validos` a totales válidos
(conteo y suma de saldo) y `rechazados` a `doc_incorrectos_<sufijo>.csv` con columna `motivo`
(`TIPO_DOC_INVALIDO`). El archivo del lookup cambia por producto (NEQUI usa el Excel Nequi): nueva
columna `arch_hom_tipo_doc` en la tabla de productos del padre. Declarar en
`decisiones/client_large.jobs.yaml` la sección `validaciones_producto`. Datos de prueba: CSV con
`TIPO_DOC` en {1,2,3,99}, Excel con `CNAME` en {1,2,3}, Excel Nequi con {1,2}. Esperado: CTE y AHO
rechazan el 99; NEQUI rechaza también el 3. Riesgo a documentar: en el SAS `TIPO_DOC` es numérico y
aquí se compara como texto (`01` frente a `1`).

**T11 [D+H] Detector de patrones de validación (3 h).** Declarar cada validación en YAML no escala. En
`src/sgm/proceso/validaciones.py` detecta en las sentencias de `PROC SQL` del SAS el patrón "crear
tabla con LEFT JOIN a un dataset importado de Excel y filtro `IS MISSING`" (rechazo) y su pareja con
`INNER JOIN` (válidos), y devuelve `Validacion(columna, columna_lookup, fuente_lookup, linea)`. La
columna del lookup y el dataset salen del SAS; el nombre de la fuente se une con `InsumoResuelto`. El
YAML pasa a ser solo una confirmación o un cambio de nombre. Criterio: sobre `client_large.sas` detecta la
validación de tipo de documento (y las que haya de país y DANE) sin declararlas, con pruebas sintéticas
de cada variante (`ON` con paréntesis, alias con y sin `AS`, `WHERE x.col IS MISSING` y `IS NULL`).

**T12 [R+H] Validación de ubicación: país y DANE (2 h).** Leer las etiquetas con `pais`, `dane`,
`dir` en el rango de líneas indicado, determinar qué columnas se cruzan con `Cod_pais.xlsx` y
`CODIGOS_DANE.xlsx`, y generar los `tMap` con lookup (misma técnica que T10). Los resultados de
rechazo deben llevar motivo distinto (`PAIS_INVALIDO`, `DANE_INVALIDO`). Ejecutar con Excel simulados.

**T13 [R+H] Campos vacíos o cero (2 h).** Etiquetas "tit-cot vacíos o 0", "FA vacíos o 0", "Nro doc no
vacío ni cero", "Campos vacíos". Son filtros de fila. El filtro del `tMap` (`expressionFilter`) está
modelado pero **nunca se ejecutó en Studio**: validarlo primero con un Job aislado (filas que pasan y
filas que no). Después generar los filtros del SAS. Si el filtro de `tMap` no funciona, usar
`tFilterRow` (extraer plantilla de un Job creado con el modo offline de `talend-mcp`, completar todos
los parámetros con `component-definitions.json` y validar ejecutando; es la misma técnica del hito 61).

**T14 [R+H] Tipo de cuenta, Codex y GMF inválidos (2 h).** Etiquetas "Tipo cuenta inválido", "Codex
inválido", "GMF inválido" (y sus "con relaciones"). Leer el SQL, ver si son listas de valores permitidos
(`IN (...)`) o cruces con tablas, y traducir a expresiones de `tMap` o `tFilterRow`. Los valores
permitidos salen del SAS, no se inventan. Rechazos con motivo propio.

**T15 [R+H] Duplicados y frecuencias (2 h).** Etiquetas "Frecuencia de registros", "Cuenta frecuencia",
"Firmas autorizadas duplicadas", "Eliminar reg rep", "Suma duplicados". Necesita `tUniqRow` y/o
`tAggregateRow` con agrupación (`GROUPBYS`). Extraer plantilla de `tUniqRow` con el procedimiento del
hito 61 y validar con datos que tengan duplicados conocidos.

**T16 [R] Conversiones numéricas fieles a `input(left(x), N.)` (1.5 h).** Hoy se usa
`new BigDecimal(x.trim())`. Documentar y probar la semántica de SAS (espacios internos, signo, decimales
con coma, valores no numéricos que dan faltante), leer cómo los datos reales del programa llegan (los
`COMPRESS(input(left()))`) y escribir una rutina de conversión en Java **dentro de la expresión del
`tMap`** (no como rutina de Studio) que se comporte igual en los casos relevantes. Pruebas de la
expresión extraída (puede probarse compilando una clase Java de prueba con el JDK de Studio).

**T17 [D+H] Esquema numérico tipado (1 h).** Las columnas se leen como texto. Decidir con las
conversiones de T16 qué columnas pasan a `id_BigDecimal` o `id_Long` en el `tMap` inicial de
normalización (las marcadas `numerica` por `esquema_csv`), y mover la conversión de saldo allí.

**T18 [R+H] Corrección de inconsistencias (3 h).** Etiquetas "Incons corregidas", "Incons por corregir",
"Incons sin campo inco", "Campo inconsistencia". Es la etapa `corregir_inconsistencias`. Leer el SAS,
describir en el PROGRESS qué hace (qué campos corrige y con qué regla) y traducir lo que se pueda con
expresiones de `tMap`. Lo que dependa de las tablas Impala (`MCDQ`, master customer) queda pendiente con
motivo hasta que T03 exista.

**T19 [H] Sábana final y salidas del producto (2 h).** Etiquetas "Sábana final", "Organizar campos",
"Orden registros". Salidas reales del SAS: `RESULTADO_<P>_NAL.csv` y `RESULTADO_<P>_EXT.csv` (nacionales y
extranjeros), `INCONS_DEP_<P>.csv`, `INCONS_DEP_CORREGIDA_<P>.csv`. Determinar el criterio nacional o
extranjero desde el SAS (probablemente por tipo de documento), escribir cada archivo con el orden de
columnas del SAS (`SELECT` final) y `ruta_resultados` como contexto (sin valor: el SAS no lo demuestra).
Validar que la suma de válidos más rechazados es igual al origen (invariante del diseño).

**T20 [D] Presupuesto de componentes por Job (1 h).** El diseño manual fija un límite de 20 componentes
por Job. Contar los componentes de `job_producto` tras T10 a T19. Si pasa de 20, decidir qué se mueve a
joblets (bloque C) o a Jobs hijos. Documentar la cifra en el informe de conformidad.

### Bloque B. Totales y conciliación sin caché

**T30 [R] Cómo pasar totales entre Jobs (2 h).** El diseño usaba cachés. Investigar y validar ejecutando
tres mecanismos para que `job_totales` y `job_conciliacion` reciban los totales de cada producto:
(a) `tBufferOutput` en el hijo con `PROPAGATE_CHILD_RESULT` del `tRunJob` (el padre recibe filas);
(b) archivos de totales por producto en una carpeta de trabajo (`totales_origen_<sufijo>.csv`,
`totales_salida_<sufijo>.csv`) que los Jobs de totales leen; (c) variables de contexto que el padre
completa tras cada hijo. Recomendar uno con la prueba ejecutada de los tres. Criterio: Job de ejemplo
mínimo para cada mecanismo y tabla comparativa en el PROGRESS. Decisión probable (a confirmar): (b),
porque deja evidencia auditable.

**T31 [H] `job_totales` real (2 h).** Con el mecanismo elegido en T30: unir los totales de los productos
(`tUnite`, validado) y escribir `totales_exogena_<anio><mes><dia>.csv` con la fecha de
`context.periodo_*`. El SAS escribe `TOTAL_AHORROS_CONS.csv` y `TOTAL_CORRIENTE.csv`; contrastar con el
contenido que genera el SAS en las etiquetas "Total cuentas" y "Suma saldo" y que las columnas coincidan.

**T32 [H] `job_conciliacion` real (2 h).** Etiquetas "Calculo conciliación registros", "Calculo
conciliación saldos", "Conciliación final", "Inconsistencias coinciden". Diferencias entre origen y
salida por producto, comparación con `context.tolerancia_conciliacion` (valor de negocio: pendiente, queda
en 0 como en el diseño y se marca "confirmar con negocio"), archivo `conciliacion_<anio><mes><dia>.csv`,
y `tDie` si alguna diferencia supera la tolerancia. Validar con datos que concilien y con datos que no.

**T33 [R+H] Tratamiento de error y registro (2 h).** El diseño pide `OnSubjobError` a `tDie` y un joblet
`jl_registro_errores` (`tLogCatcher`, `tLogRow`). Falta el `lineStyle` de OnSubjobError y OnComponentError:
leerlo con `javap` del enum `EConnectionType` (como se hizo con el lookup, en
`org.talend.core.runtime`), validar ejecutando un Job que falle a propósito, y añadir
`conexiones.al_fallar_subjob/componente`. Luego cablear el padre.

### Bloque C. Joblets (Fase 4 del plan)

**T40 [R] Formato del `.item` de joblet (2 h).** Hay una carpeta `joblets/` en el proyecto de Talend sin
ejemplos útiles. Averiguar el formato (extensión `.joblet`, `ProcessType` con `jobletType`, entradas y
salidas `tJobletInput`/`tJobletOutput`, nodos "Trigger"), crear uno de referencia con la vía offline de
`talend-mcp` si se puede, y validar ejecutando un Job que lo use (nombre nuevo cada intento). Entregable:
`talend_item/joblet.py` con `render_joblet_item` y una prueba contra el ejemplo. Si Studio no lo carga
sin reiniciar, repórtalo con evidencia y salta el resto del bloque C.

**T41 [D+H] Detección de cadenas repetidas (3 h).** Dentro de una etapa hay secuencias idénticas
(por ejemplo ocho "Validación tipo doc"). En `proceso/joblets.py` detecta subcadenas de pasos
equivalentes tras normalizar literales y sufijos de producto (reutiliza `familias.patron_sufijos` y
`similitud`), propón candidatas con su número de apariciones y parámetros que difieren, y exige
confirmación por YAML (`decisiones/<programa>.joblets.yaml`) antes de emitir.

**T42 [H] Joblets del diseño manual (3 h).** Si T40 funcionó: `jl_normalizar`, `jl_validar_documento`,
`jl_validar_ubicacion`, `jl_conciliar`, `jl_registro_errores`, `jl_conexion_impala`. Mover a ellos las
lógicas de T10, T12 y T32. Criterio: `job_producto` queda por debajo del límite de componentes (T20) y la
salida del padre sigue siendo la misma.

### Bloque D. Contextos, entornos y conexión Impala

**T50 [H] Contextos completos (1.5 h).** Sección 2 del diseño: grupo Default con `ruta_insumos`,
`ruta_resultados`, `arch_*`, `tolerancia_conciliacion`, `log_nivel`; grupos DEV, QA y PROD con
`env_nombre`, `impala_dsn` (el SAS mapea D, C, P a `IMPALA`, `IMPALAC`, `IMPALAP`: derivarlo de la macro
`ambiente` en lugar de declararlo), `impala_host`, `impala_puerto`, `impala_usuario` (pendientes, vacíos) e
`impala_password` sin valor. Que `sgm talend` imprima la lista de pendientes de contexto.

**T51 [R+H] Conexión Impala compartida (3 h).** Plantillas `tImpalaConnection`, `tImpalaInput`,
`tImpalaRow`, `tImpalaClose` existen (de Jobs reales) pero con la conexión sin regenerar
(`USE_EXISTING_CONNECTION=true` y `CONNECTION` sin completar). Armar `jl_conexion_impala` o la conexión
del padre, pasar `CONNECTION` a los hijos, y emitir las lecturas de tablas Impala del SAS (maestro de
clientes, canales, MCDQ) con el SQL traducido de forma literal (`CONNECT TO IMPALA ... SELECT ... FROM
connection`). No hay Impala para ejecutar: valida compilando y, con T03, ejecuta contra CSV simulado.
Prohibido guardar usuario, host o contraseña: todo por contexto.

**T52 [H] Documento de contexto por Job (1 h).** Tabla 2.3 del diseño ("Parámetros por Job") emitida
desde los contextos reales de cada Job generado, con origen y valor.

### Bloque E. Documento de diseño emitido (Fase 3)

**T60 [H] Secciones nuevas en `sgm proceso` (3 h).** Emitir las secciones 2 (contextos), 4 (joblets,
vacía si T42 no se hizo), 5 (decisiones, desde un YAML `decisiones` con id, texto y motivo), 7
(pendientes y riesgos desde `pendientes.py`) y 8 (orden de construcción desde las dependencias
reales entre Jobs). Cada sección con su prueba y su fila en `tests/conformidad/`.

**T61 [D+H] Corregir 1.1, 1.2, 1.3 y 3 con lo probado (2 h).** La sección 1.1 emitida debe mostrar los CSV
de producto como fuentes (no tablas Impala), la 1.2 debe decir "sin cachés" con el motivo, la 1.3 debe
listar las variables de contexto del periodo, y la 3 debe listar los Jobs reales generados con su número de
componentes. Actualizar `diseno_doc.py`, `render_md.py` y `tests/conformidad/` (reducir xfails con
razones reales, no copiando el manual). Mantener la regla: lo que el manual declara y el SAS no
demuestra queda como "declarado", no como "derivado".

**T62 [H] Informe de conformidad medible (1.5 h).** Comando `sgm conformidad <programa>` que compare el
diseño emitido con `tests/fixtures/referencia/diseno_manual.yaml` y escriba un resumen: filas derivadas,
declaradas, pendientes, y diferencias con motivo (incluida la desviación de los cachés). Es la medida
objetiva de "se parece".

**T63 [H] Comparar Jobs emitidos con la estructura del manual (1.5 h).** Una prueba o informe que cuente,
por Job, componentes y subjobs y los ponga junto a lo que el diseño manual espera (3.1 a 3.5), con el
límite de 20 por Job. No exige igualdad: muestra la brecha.

### Bloque F. Fidelidad del emisor de Talend

**T70 [R] Round trip contra Studio (2 h, necesita una persona).** Abrir en el editor gráfico un Job
emitido por `sgm`, guardarlo y comparar el `.item` que Studio escribe con el emitido: muestra qué
parámetros, `show` y orden normaliza Studio. Hasta hoy ningún Job se abrió en el editor. Una persona
debe hacerlo (copiar a `process/`, Refresh, abrir, guardar) y dejar el resultado en una carpeta; el
agente escribe el comparador (`tools/comparar_item.py`) y documenta las diferencias. Incluye el
`item_key` y el `.screenshot` de `.properties`, que `sgm` omite.

**T71 [H] Show y orden de las plantillas calculadas (2 h).** Las siete plantillas del hito 61
(`tFileInputExcel`, `tAggregateRow`, `tUnite`, `tReplicate`, `tFileExist`, `tSetGlobalVar`,
`tLogCatcher`) se completaron por regla, no se copiaron de un Job guardado por Studio. Con T70, ajustar.

**T72 [H] Más componentes con plantilla (3 h).** Los que el diseño manual usa y faltan: `tFilterRow`,
`tUniqRow`, `tDBClose`, `tFileList`, `tFlowToIterate` (hay), `tNormalize`, `tSortRow` (hay), `tJoin`,
`tConvertType`, `tSetGlobalVar` (hay). Procedimiento del hito 61: Job de referencia por la vía offline de
`talend-mcp`, completar con `component-definitions.json`, validar ejecutando, extraer plantilla con
`tools/extraer_plantilla.py` y limpiar datos de ejemplo.

**T73 [H] Posiciones en el lienzo (1.5 h).** Los nodos salen en filas de 120 píxeles y columnas de 200
sin considerar el flujo. Colocar los componentes de cada subjob de izquierda a derecha por orden de flujo
y los subjobs de arriba abajo, con separación fija, para que el Job se lea al abrirlo (los `<subjob>`
llevan colores).

**T74 [H] Etiquetas y notas (1 h).** Usar el parámetro `LABEL` de los componentes con nombres
significativos (por ejemplo "Validar tipo de documento") y `<note>` para los pendientes, en vez de
componentes `tJava` que imprimen "PENDIENTE".

### Bloque G. Generalización y segundo programa (Fase 6)

**T80 [H] Ejecutar `sgm talend` sobre los demás programas de `tests/fixtures/sas` (2 h).** Ver dónde
falla (el comando exige YAML de agrupación, diseño y Jobs por programa). Hacer que el comando funcione
sin YAML: agrupación y arquitectura por omisión (un solo producto, un solo Job), con la lista de lo que
faltó. Pruebas de que no se rompe con programas sin `PROC IMPORT`, sin macros o sin regiones.

**T81 [H] Informe de complejidad y huecos (3 h).** Estilo Lakebridge (Analyzer, Converter, Reconcile):
por programa, número de pasos, de bloques, de componentes estimados, de pendientes por motivo, de
instrucciones SAS sin traducción y porcentaje de cobertura. Salida Markdown y JSON. Es el entregable de
la Fase 6.

**T82 [R+H] Pendientes de la fase 1 (3 h).** `infile`/`file` con fileref sin comillas (resolver
`FILENAME`), tres WORK que se leen antes de crearse (`SABANA_SIN_*`), nombres con macrovariable
(`&tabla_origen.`), `sql_tree` que falla con subconsultas en `FROM`. Cada uno con prueba.

### Bloque H. Calidad, deuda y documentación

**T90 [H] Código muerto y deuda (1.5 h).** Eliminar lo descartado con pruebas directas previas de lo que
se conserve: `grid.py`, `emit/conventions/{best_practices,context_rules,infra}.py` y lo que
`tests/unit` no use. Antes de borrar, escribir las pruebas directas que falten del traductor de
expresiones inline, `types_code` y `region`. Ejecutar la suite completa después de cada borrado.

**T91 [D] Dependencias (30 min).** `pyproject.toml` declara `sqlglot` y `jsonschema` (fuera de la lista
permitida) y alguien añadió `pytest-testmon`. Decidir y dejar nota en la sección "Decisiones" de
`PROGRESS.md`, o quitar. No cambiar sin avisar al usuario: es una regla de `AGENTS.md`.

**T92 [H] README y guía (1.5 h).** Documentar `sgm proceso`, `sgm talend`, los YAML de `decisiones/` (cuál
hace qué y qué es decisión del equipo frente a hecho del SAS), los simuladores y el protocolo de Studio.
Mantener el tono del README actual.

**T93 [H] Memoria del proyecto (20 min).** Actualizar
`C:\Users\USUARIO_BISOLUTION1\.claude\projects\C--Users-USUARIO-BISOLUTION1-code-sgm-v2\memory\plan-reescritura-sgm.md`
con los hitos 61 a 66 y los hallazgos de la sección 1.3 de este documento. Mantener el frontmatter.

**T94 [H] Constantes duplicadas e imports privados (45 min).** `jobs_diseno.py` importa `_id` privado de
`item.py` y varios módulos repiten `java()`/`_texto`. Exponer funciones públicas (`id_propiedad`,
`literal_java`) y unificar.

## 5. Cómo trabajar estas tareas

1. Un bloque por agente, o una tarea por subagente `haiku` con su especificación copiada de aquí.
2. Antes de cada tarea: `git status` limpio, `uv run pytest -q` verde.
3. Cada tarea que genere Jobs termina con ejecución en Studio (sección 3). Pega en el PROGRESS la salida
   literal, no una descripción.
4. Todo lo que el SAS no demuestre queda como pendiente con motivo. No se llena con valores del manual.
5. Un commit por tarea o por grupo de tareas pequeñas: `hito N: <resumen>`, y la línea de coautoría. No
   hacer `git push`.
6. Si una investigación resulta imposible (por ejemplo, joblets sin reiniciar Studio), no la rodees:
   documenta la evidencia en el PROGRESS y sigue con la siguiente.

## 6. Lo que seguirá siendo decisión humana

D2 (un archivo de rechazos por producto o uno por tipo de error), D6 en lo que toca a NEQUI, la
tolerancia de conciliación, los nombres de las tablas de salida finales, el significado exacto de los
códigos de tipo de documento y las rutas reales por entorno. El emisor las marca pendientes y las lee de un
YAML cuando el equipo las confirme.

## 7. Aceptación contra el corpus (traspaso del plan de equivalencia)

Añadido el 4 de noviembre de 2026. El corpus de `tests/corpus/` (101 casos de L0 a L6 y 16 de L8, todos
con resultado esperado; ver `plan-corpus-y-equivalencia.md`) es ahora el criterio de aceptación de las
tareas T10 a T19 y B. Una tarea que genere Jobs no está terminada cuando compila y corre con datos
simulados cualquiera, sino cuando el caso del corpus que le corresponde da el resultado esperado.

### 7.1 Qué caso valida cada tarea

| Tarea | Casos del corpus | Qué se compara |
|---|---|---|
| T10 tipo de documento con lookup | `L2` (patrón `LEFT JOIN ... IS MISSING` e `INNER JOIN`) y `L8/validaciones/v01_tipo_doc` | Válidos e inválidos por producto; válidos más inválidos igual al origen |
| T12 país y DANE | `L8/validaciones/v03_pais_dane` | Rechazo por país y por DANE con motivo |
| T13 vacíos y ceros | `L8/validaciones/v02_vacios_ceros` | Conteos de la tabla de anomalías plantadas |
| T14 cuenta, Codex, GMF | `L8/validaciones/v04_tipo_cta_gmf`, `v05_codex_saldos` | Rangos y listas permitidas |
| T15 duplicados | `L8/totales/01_duplicados_frecuencias`, `L6` (`NODUPKEY`, `FIRST.`/`LAST.`) | Qué fila se conserva (ojo: ver 7.3) |
| T16 conversión numérica | `L4` (`input`, `left`, `compress`) y `semantica/vectores.yaml` | Vectores con fuente |
| T18 correcciones | `L8/totales/02_inconsistencias_correccion` | Corregidas y por corregir |
| T19 sábana y salidas | `L8/totales/03_sabana_nal_ext`, `L8/validaciones/v07_cadena_completa` | `RESULTADO_<P>_NAL/EXT.csv` |
| T31 y T32 totales y conciliación | `L8/totales/04_totales_origen_salida`, `05_conciliacion` | Sumas con tolerancia, diferencia plantada |
| Periodo | `L8/totales/06_periodo_fecha` | Variables de fecha y nombres de archivo |
| Lectura de Impala | `L8/totales/07_impala_lectura` | Con el Impala del contenedor (`tools/contenedores/impala/`) |
| Cadena completa | `L8/validaciones/v08_nequi_cadena`, `L8/totales/08_cadena_completa_macros` | Las invariantes del `caso.yaml` |

### 7.2 Cómo se comprueba

1. Sin Studio: `uv run python tools/corpus.py oraculo todos --verificar` (117 casos, 0 fallas) y las pruebas
   de cruce (`tests/unit/test_corpus_validaciones.py`, `test_corpus_totales_cruce.py`) comprueban que el
   esperado es coherente.
2. Con Studio: `tools/corpus_studio.py validar <caso> --jobs <carpeta> --padre <job> --mapa mapa.yaml`
   (en construcción, tarea K11) ejecuta los Jobs emitidos con las entradas del caso y compara cada archivo
   escrito con `esperado/`, con la tolerancia y el orden que dice el `caso.yaml`. Sin el arnés, hazlo a
   mano con `tools/validar_en_studio.py` apuntando las variables de contexto a `entradas/` y comparando
   con `esperado/`.
3. Cada caso lleva `anomalias_plantadas` (conteo exacto de registros anómalos, independiente de cualquier
   SQL) e `invariantes`: compruébalos en la ejecución real, no solo el archivo.

### 7.3 Cosas que el corpus ya enseñó y que afectan a los Jobs

- `MERGE` de un DATA step no es un `JOIN`: con llaves repetidas por ambos lados sale el máximo de filas por
  grupo (caso `L6/l6_02`, ejemplo de la documentación de SAS). No traduzcas `MERGE` como unión de `tMap`
  sin comprobarlo.
- En un DATA step, `IF saldo < 500` es verdadero con saldo faltante; en SQL y en Java una comparación con
  nulo no lo es. La expresión del `tMap` debe tratar el faltante explícitamente. El oráculo SQL tampoco lo
  modela todavía.
- Un texto en blanco es faltante y también es igual a `''`; los blancos finales no cuentan en una
  comparación de texto. En Java, `String.equals` sí los cuenta: usa `trim` o una comparación propia.
- `ROUND(x, 0.01)` de SAS redondea al múltiplo de 0,01 con empates alejándose de cero; `Math.round` y
  `BigDecimal.setScale(2, HALF_UP)` coinciden en los casos normales, pero no uses el `round` por dígitos de
  una base de datos.
- `COMPRESS` sin modificadores quita blancos; `SUBSTR` sobre un número lo toma alineado a la derecha;
  `SCAN` trata delimitadores consecutivos como uno (vectores en `tests/corpus/semantica/vectores.yaml`).
- Huecos del analizador de `sgm` que los casos encontraron (`tests/corpus/HUECOS_FRONTEND.md` y
  `HUECOS_FRONTEND_TOTALES.md`): `PROC DOWNLOAD` dentro de `RSUBMIT` pierde la ruta de red; `%IF` dentro de
  una macro con parámetro no se sigue en tres programas. Son la tarea T82.
- Los casos con `estado: pendiente_revision` o `parcial` tienen detalles de formato de `PROC IMPORT` y
  `PROC EXPORT` sin demostrar sin SAS; la tolerancia del `caso.yaml` y su `observacion_revision` dicen
  cuáles. Si tu Job difiere solo en ese detalle, anótalo; no cambies el esperado sin una fuente.

### 7.4 Regla de cierre actualizada

Un hito que traduce lógica del SAS termina con: (a) la ejecución en Studio del caso del corpus que lo
cubre, con la salida literal pegada en `PROGRESS.md`; (b) el resultado (coincide, o la celda exacta que
difiere y por qué); (c) el estado del caso actualizado si pasó (`traducible` solo si el esperado no tiene
supuestos pendientes). Si el corpus no tiene un caso para lo que traduces, escribe el caso primero
(formato en `plan-corpus-y-equivalencia.md`, sección 6), con la verdad plantada en el generador.
