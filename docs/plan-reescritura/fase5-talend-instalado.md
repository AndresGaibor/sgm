# Fase 5: el Talend instalado y la decisión de cómo emitir

Revisado el 4 de noviembre de 2026 en esta máquina (solo lectura).

## Qué hay instalado

| Dato | Valor |
|---|---|
| Ubicación | `C:\Talend\8.0.1\studio` (JDK Zulu 21 en `C:\Talend\8.0.1`) |
| Producto | Talend Studio, marca "Talend Cloud Data Fabric", versión `8.0.1.20260925_1301-patch` (parches 2026-06, 2026-08 y 2026-09) |
| Características | familia `org.talend.lite.*` 8.0.3 (jobs estándar, joblets, big data); sin complementos de Job Script ni de línea de comandos (ningún plugin con `jobscript` o `commandline` entre los 1.382 de `plugins/`) |
| Proyecto de trabajo | `workspace/talendbancolombia-963626413/PRJ_BANCOLOMBIA` (almacenamiento Git, `productVersion` igual al producto) |
| Jobs existentes | decenas de `.item` guardados por Studio en `process/` (orquestadores con `tRunJob`, `tFileInput/OutputDelimited`, `tMap`, `tFixedFlowInput`, `tLogRow`, `tHashInput/Output`, `tDie`, `tJava`, conexiones Impala/HDFS/FTP) |
| Otros | una característica propia (`com.andres.talend.bridge.feature`) que no se usa: `AGENTS.md` prohíbe MCP |

## Decisión

El plan decía: confirmar la versión de Studio y probar cómo se ejecuta un Job Script, con el plan B de
parametrizar un Job exportado. Esta instalación **no trae Job Script ni línea de comandos**, así que el
plan A no es posible aquí. Se elige el plan B en su forma más directa: **escribir los archivos `.item` y
`.properties` que Studio guarda**, copiando la forma de Jobs reales de este mismo Studio.

Motivos:

- Hay ejemplos reales y recientes de la misma versión; el formato se puede comparar byte a byte.
- No se depende de un complemento ni de una función de pago que no está instalada.
- Es reproducible y revisable en Git: el resultado se copia a `process/` del proyecto.

## Qué se hizo (hito 59)

`src/sgm/talend_item/` escribe un Job con `tFixedFlowInput` y `tLogRow`. La prueba
`tests/unit/test_talend_item.py` compara nodos, conexiones y subjobs contra `tests/fixtures/talend/hijo_0.1.item`
(copia de un Job real de este Studio, sin contraseñas ni rutas locales): **son idénticos**. Los 96
parámetros base coinciden en campo y orden.

## Validación en Studio real

Procedimiento para repetir la validación con el Studio instalado (hito 60). Se usa el proyecto
`talend-mcp` solo como validador externo desde la línea de comandos, con permiso del usuario. `AGENTS.md`
prohíbe MCP dentro de `sgm`, y el producto no depende de él.

1. Arrancar el servidor de talend-mcp con el proyecto de Studio:
   `TALEND_PROJECT=C:/Talend/8.0.1/studio/workspace/talendbancolombia-963626413/PRJ_BANCOLOMBIA bun run start:server`.
   Dejarlo corriendo.
2. Emitir el `.item` y el `.properties` del Job en `PRJ_BANCOLOMBIA/process/` con un nombre nuevo
   (ver hallazgo 2).
3. Refrescar el workspace: `bun run scripts/mcp-call.ts talend_bridge_refresh_workspace '{}'`.
4. Compilar con `talend_job_build_batch` y `{"jobs":["NOMBRE"]}`, con el mismo `scripts/mcp-call.ts` del paso 3.
5. Exportar con `talend_deliverables_build_job` y `{"jobName":"NOMBRE","destinationDir":"<carpeta>"}`.
6. Ejecutar el `.bat` del launcher con el `java` del JDK de Studio en el PATH
   (`C:\Talend\8.0.1\zulu21.50.19-ca-jdk21.0.11-win_x64\bin`). La salida debe coincidir con lo esperado.
7. Borrar los dos archivos del proyecto (`.item` y `.properties`).

### Hallazgos

1. Compilar no basta. Una plantilla de tFileOutputDelimited con USESTREAM=true compilaba y fallaba al
   ejecutar con NullPointerException. Por eso la validación incluye ejecutar el Job.
2. Studio guarda en memoria cada Job por su identificador. Al reemitir el mismo nombre con otro contenido,
   build-batch regeneró el código con la versión anterior, aunque se hizo refresh del workspace. Los
   identificadores de sgm son deterministas a partir del nombre y la versión, así que para revalidar un
   cambio hay que usar un nombre nuevo.
3. Un diálogo "Network Issue Occured" de Studio bloquea `talend_job_verify` y la creación en vivo de Jobs.
   talend-mcp no sabe cerrarlo. La ruta sin interfaz (escribir el `.item`, build-batch, exportar y ejecutar)
   sí funciona.

### Lo que sigue sin verificar

- Ningún Job emitido se ha abierto en el editor gráfico de Studio. Solo se cargaron, compilaron y ejecutaron
  por la ruta de generación de código.
- tMap no está emitido todavía.
- `tFileInputExcel`, `tAggregateRow`, `tUnite` y `tReplicate` no tienen ejemplo en el proyecto.
- Los valores de rutas de trabajo de Studio en las plantillas (TEMP_DIR, BASE_FILE_PATH) vienen del Job de origen.
- Las plantillas de Impala traen USE_EXISTING_CONNECTION=true y su CONNECTION no está regenerada.

## Jobs del diseño

- El comando `sgm talend <programa.sas>` escribe los cuatro Jobs (padre y tres hijos) en `<out>/<programa>/talend/process/`.
- Intervienen tres YAML de decisiones: `decisiones/client_large.agrupacion.yaml` (productos CTE, AHO y NEQUI),
  `decisiones/client_large.jobs.yaml` (arquitectura: proyecto, entornos, nombres de Jobs y mensaje final) y
  `decisiones/client_large.diseno.yaml` (diseño del proceso).
- Hoy sale el Job padre completo, con tPrejob, tDie condicionado, periodo leído del Excel de fecha, productos por
  iteración, totales, conciliación y tPostjob. Los tres hijos (producto, totales y conciliación) son esqueletos
  (`tJava`) que declaran las variables del periodo y dicen qué les falta.
- Validado en Studio real (hito 61): los cinco Jobs compilan. El padre con `--context=DEV` corre insumos una
  vez, producto tres veces (CTE, AHO, NEQUI), totales y conciliación, con salida 0. Con el entorno vacío,
  el Prejob marca `env_valido=false`, el tDie termina la ejecución y ningún hijo corre (salida 1).
- Hallazgos principales:
  1. Un `ACTIVATE=false` en una conexión Run if significa conexión desactivada; copiarlo deja el tDie suelto.
  2. Un componente desactivado en el Job de origen no genera código en Studio; la extracción descarta `ACTIVATE`.
  3. Solo se vacía el CODE de campos Java; vaciar el código numérico de tDie y tWarn rompe la compilación.
  4. tPrejob que lanza una excepción no detiene el flujo: hace falta tDie con EXIT_JVM.
  5. build-batch compila en paralelo: compilar primero los hijos y después el padre.

## Diseño simple, sin caché

- Decisión: se eliminó `job_insumos` y el caché compartido entre Jobs. Lo pidió el usuario ("que sea simple").
  Los Excel pequeños se leen como lookup dentro del `tMap` de `job_producto`. El Job padre lee la fecha una vez
  y la deja en `context.periodo_anio`, `periodo_mes` y `periodo_dia`, que los hijos heredan.
- Motivo probado en Studio 8.0.1: `tHashOutput` y `tHashInput` no comparten datos entre Jobs distintos con ninguna
  configuración. La clave del buffer incluye el nombre del Job y un pid aleatorio, el LIST de `tHashInput` solo ve
  los `tHashOutput` del mismo Job, y el modo PERSISTENT está comentado. Por eso se descartó `tCacheIn` con `tRunJob`.
- Alternativa descartada: una rutina Java con mapa estático. Studio no carga rutinas nuevas sin reiniciar y no hay un
  `.item` de rutina real que copiar, así que no se validó.
- Cómo validar un Job con Excel:
  1. Generar los insumos simulados con `tools/simular_insumos.py`.
  2. Emitir los Jobs con `sgm talend` (cuatro Jobs) y compilarlos.
  3. Exportar el Build Job y ejecutar su lanzador. No usar `talend_job_execute`: desde Studio no se cargan los archivos de contexto.
- Si la exportación falla por poms de Maven (`logging-parent` 11.3.0, `log4j-bom` 2.24.2 y 2.24.3), bajar esos poms
  públicos a la caché de Studio con un script temporal fuera del repositorio.
- `PASSWORD` de `tFileInputExcel` no puede quedar vacío ni con `***`. Ver hallazgo 1 del hito 62 en `PROGRESS.md`.

## Origen de datos de producto

- Cómo se deduce: el SAS baja cada archivo con `PROC DOWNLOAD` y lo importa con `PROC IMPORT DBMS=DLM`, `DELIMITER=';'` y `GETNAMES=NO`. Sin cabecera, SAS nombra las columnas `VARn`; el programa las renombra (`DS.VAR1 AS NOMBRE`) o las convierte con `input()`, y eso demuestra el nombre y el carácter numérico. Lo que no se nombra queda como `VARn`.
- El producto sale de la etiqueta `/* Etiqueta: ... */` previa al import. El archivo principal de cada producto es el más ancho que importa; los demás quedan como auxiliares pendientes.
- Simulación sin datos reales: `uv run python tools/simular_productos.py <programa.sas> <carpeta> --filas 3 --saldo FIN_SALDO_CTA`. Escribe CSV con `;` y 23 columnas. La columna de saldo sale como número con punto (`100.50`, `201.00`, ...); sin `--saldo`, todas son texto `SIM_<columna>_<n>`.
- Validación en Studio: el padre exportado lee esos CSV y cada producto imprime `registros_origen|suma_saldo_origen`. Con los saldos anteriores, la salida es `3|603.00`.
- `parchear.py`, del scratchpad de la sesión (no del repositorio), prepara el `.item` del padre para correrlo localmente: fija `env_nombre` en DEV, apunta la ruta de insumos a la carpeta local y sustituye las rutas UNC de los CSV por la carpeta de productos simulados. No toca datos reales ni el repositorio.
- Sin verificar: la suma usa BigDecimal y no reproduce todavía `input(left(col), 20.)` (espacios internos, signos, decimales con coma).
