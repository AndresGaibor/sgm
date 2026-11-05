# Propuesta de correcciones al diseño manual de la exógena de depósitos

Fecha: 5 de noviembre de 2026. Tarea R5-06 de `docs/plan-reescritura/ruta-a-produccion.md`.
Documento de origen: `docs/diseno-talend-exogena-depositos.md`, sin cambios en esta propuesta.
Programa de referencia: `tests/fixtures/sas/client/client_large.sas`.

## Objeto

El diseño manual se escribió antes de probar nada en Talend Studio 8.0.1 y antes de leer el SAS con
detalle. Varios de sus supuestos ya no se sostienen con lo probado. Esta propuesta lista cada punto,
la evidencia que lo contradice o lo actualiza, y la corrección recomendada. No se aplica al manual
sin revisión del equipo: la decisión es suya.

El documento de diseño que emite `sgm proceso` ya recoge
las correcciones de las secciones 1.1, 1.2, 1.3 y 3 que el código sostiene. Las filas que siguen
diferentes del manual están en `src/sgm/conformidad/estado.py` (`DIFERENCIAS_CONOCIDAS`), con su motivo.

## Puntos

| Nº | Sección del manual | Lo que dice el manual | Lo probado o leído | Evidencia | Recomendación |
|---|---|---|---|---|---|
| 1 | 1.1 Fuentes externas | Depósitos CTE, AHO y NEQUI son "Tabla Impala" con nombre de tabla pendiente. | Son archivos CSV con `;` y sin cabecera, de 23 columnas. Se bajan con `PROC DOWNLOAD` y se leen con `PROC IMPORT DBMS=DLM`. | Hito 64. `client_large.sas`: líneas 284-294 (`DBIFTCD.csv`), 871-881 (`DBIFTCS.csv`), 1510-1517 (`F_1019.csv`). | Cambiar el tipo a CSV y la ubicación a la ruta de origen del producto. Las tablas Impala quedan solo para las lecturas que el SAS demuestra (punto 2). |
| 2 | 1.1 Fuentes externas | El manual no lista las lecturas de Impala del SAS. | El SAS lee `resultados_vspc_clientes.master_customer_data` (maestro de clientes), `S_CANALES.SAI_SCILIBRAMD_SCIFFIMGFR` (firmas) y `proceso_vspc_finanzas.MCDQ`. El DSN depende de `%ambiente`: D a IMPALA, C a IMPALAC, P a IMPALAP. | `client_large.sas`: líneas 167, 215 y 2071; macro `ambiente` en la línea 1770 y siguientes. Sección 1.1 emitida (hito 99d). | Añadir estas tres lecturas al manual con su DSN por ambiente. Su traducción a Jobs aún no está hecha (R4-03 y R4-04). |
| 3 | 1.1 Fuentes externas | Códigos DANE: nombre de archivo pendiente. | El SAS nombra `CODIGOS_DANE.xlsx` y lo importa con `PROC IMPORT`. | `client_large.sas`: línea 81. Conformidad, fila F04 (hito 94). | Dar el nombre del archivo y marcar la fila como confirmada en el SAS. |
| 4 | 1.2 Cachés en memoria | Las cachés `cache_*` y `totales_*` se crean con `tCacheOut` y se leen con `tCacheIn` entre Jobs. | Un `tHashOutput` de un Job no lo ve otro Job, con ninguna configuración. El modo PERSISTENT está comentado en el componente (hito 63). La clave del buffer lleva el nombre del Job y un pid aleatorio. | Hito 63 (prueba en Studio 8.0.1). El manual no prueba `tCacheIn`; la prueba del hito 63 es sobre `tHash*`. | Eliminar las cachés entre Jobs. Los lookups de Excel se leen dentro de `job_producto`. Los totales viajan en archivos por producto (punto 5). |
| 5 | 1.2 y 3.4 y 3.5 | Los totales de origen y de salida se pasan por caché a `job_totales` y `job_conciliacion`. | Mecanismo recomendado: archivos por producto en la carpeta de trabajo. Las variables de contexto no sirven: el `globalMap` del hijo llega vacío al padre (`SIN_VALOR`). Un `tBufferOutput` con `PROPAGATE_CHILD_RESULT` funciona, pero no se probó en paralelo. | Hito 97d, tabla comparativa de los tres mecanismos (corridas v97i y v97j). | Adoptar el mecanismo (b). Anotar que `job_producto` aún no escribe estos archivos (R2-02). |
| 6 | 1.3 Variables globales | `periodo_*` las crea `job_insumos`. | `job_insumos` se eliminó. El padre lee el Excel de la fecha una vez, deja `periodo_anio`, `periodo_mes` y `periodo_dia` en el contexto y los hijos las heredan. | Hito 63 (el padre con Excel simulado; los hijos imprimen las tres variables). | Pasar la creación de las variables al padre `job_exogena_depositos`. |
| 7 | 3.1, 3.2 | El padre tiene un subjob `job_insumos` que lee los cinco Excel y los pasa a cachés. | No existe `job_insumos`. Los Excel pequeños son lookups dentro de `job_producto`. | Hito 63 (decisión y desviación respecto de la sección 3.2). | Retirar `job_insumos` del diseño. Documentar la desviación. |
| 8 | 3.3 job_producto | Conteo aproximado de 17 componentes, con límite de 20. | `sgm talend` emite `job_producto` con 21 componentes, por encima del límite. Sin ejecutar en Studio con este programa. | Sección 3 del documento emitido (`sgm proceso`), que cuenta los componentes con el propio emisor. | Reconocer que el Job supera el límite. El plan de joblets (R3) queda como la vía de corrección. |
| 9 | 3.3 job_producto | La lectura es `tDBInput` con SQL y `WITH`. | La lectura es `tFileInputDelimited` sobre los CSV, con su esquema de 23 columnas deducido del SAS. | Hito 64 (`fuentes_csv.py` y `esquema_csv.py`). | Cambiar el componente de lectura y su esquema. |
| 10 | 3.4 job_totales | Seis `tCacheIn` alimentan un `tUnite`. | `tUnite` no compila en Studio 8.0.1 con este Job: el generador falla con un `NullPointerException` en `TUniteMainJava.generate`. La unión se hace con `APPEND` secuencial. | Hito 97d, hallazgo 1 (variantes v97a, v97b y v97c). | Sustituir `tUnite` por `APPEND` mientras no se resuelva el fallo. |
| 11 | 3.4 job_totales | Las columnas de `totales_exogena` son las de `TOTAL_AHORROS_CONS` y `TOTAL_CORRIENTE`. | El SAS escribe esos dos archivos con 13 sumas sobre `CORRIENTE` y `AHORROS`, no con totales de origen y salida por producto. El esquema del caso de prueba es otro. | Hito 97d, sección de columnas de la exógena. `client_large.sas`: líneas 24693 a 24800. | Decidir con el SAS y con negocio cuál es la exógena real. Mientras tanto, dejar el nombre del archivo como decisión pendiente. |
| 12 | 3.1 padre y 3.4 | Los errores se propagan porque el Job falla. | `DIE_ON_ERROR` vale `false` por omisión en `tFileInputDelimited`. Con un archivo faltante el hijo termina bien y el padre sale con código 0. Con `DIE_ON_ERROR=true` el padre sale con código 1. | Hito 97d, hallazgo 2 (corridas v97e y v97f). | Poner `DIE_ON_ERROR=true` en todas las entradas de archivo. Relacionar el código de salida con DC-08. |
| 13 | 3.1 padre | `tRunJob` hijo sin tratamiento de error explícito. | Con `DIE_ON_CHILD_ERROR=true`, el padre se detiene cuando el hijo muere. Confirmado con los tres mecanismos. | Hito 97d, hallazgo 3. | Dejar `DIE_ON_CHILD_ERROR=true` como valor de la plantilla y documentarlo. |
| 14 | 3.2 job_insumos (lectura de Excel) | Lectura de Excel sin mención de contraseña. | Con `VERSION_2007` y `PASSWORD` vacío, `tFileInputExcel` genera un `Optional.ofNullable()` vacío y no compila. Un valor que no sea vacío ni `***` compila, y Excel lo ignora porque el archivo no tiene clave. | Hito 63, hallazgo 1. | Anotar el valor de `PASSWORD` en la plantilla de lectura de Excel. |
| 15 | 3.1 y 2 (contexto) | Los contextos se cargan al ejecutar. | Ejecutar un Job desde Studio con `talend_job_execute` no carga los archivos de contexto. Para Jobs con contexto hay que exportar el Build Job y ejecutar su lanzador. | Hito 63, hallazgo 2. | Documentar el método de prueba; no cambia la lógica del diseño. |
| 16 | Cabecera del documento | "Estado: borrador de diseño. No construido ni probado en Talend Studio." | Hay Jobs emitidos y ejecutados en Studio 8.0.1: validación de filtros, normalización, tipo de documento, ubicación, saldos y totales, con datos de prueba. El Job del programa grande no se ha ejecutado. | Hitos 81 a 97d en `PROGRESS.md`. | Actualizar el estado y separar lo probado de lo que no lo está. |
| 17 | Principio del documento | "Lo que se pasa entre subjobs va en memoria (`tCacheOut` / `tCacheIn`)." | Ver puntos 4 y 5. El paso en memoria entre Jobs no funciona con `tHash*`; los totales se pasan en archivos. | Hitos 63 y 97d. | Cambiar el principio: lo que pasa entre Jobs se escribe en archivos de trabajo. |

## Lo que no se ha verificado

- `tCacheIn` y `tCacheOut` entre Jobs no se han probado. Lo que se sabe es del modo `tHash*` (punto 4).
- El paralelismo de los tres mecanismos de totales no se ha probado (punto 5).
- La conexión Impala compartida entre padre e hijos (`jl_conexion_impala`, `tImpalaConnection`) no se ha probado (R4-03).
- La tolerancia de conciliación (DC-04) es decisión de negocio.
- El orden y los tipos reales de las columnas de los CSV de producto no los ha visto el equipo; se leen como texto.

## Pasos propuestos

1. Revisar los puntos 1 a 17 con el equipo y aprobar, rechazar o matizar cada uno.
2. Aplicar en el manual los puntos aprobados. Este documento no modifica el manual.
3. Confirmar con el SAS y con negocio las decisiones de los puntos 11 y 3.
