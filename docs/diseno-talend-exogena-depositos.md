# Diseño Talend: información exógena de depósitos

Estado: **borrador de diseño**. No construido ni probado en Talend Studio.
Fuente de la lógica: `tests/fixtures/sas/client/client_large.sas` (proceso SAS de origen).
Principio: un solo flujo de datos por producto, sin tablas intermedias. Las únicas
persistencias son las entradas y las salidas finales. Lo que se pasa entre subjobs
va en memoria (`tCacheOut` / `tCacheIn`).

Convenciones:
- `<sufijo>` = `cte`, `aho` o `nequi`.
- `<anio>`, `<mes>`, `<dia>` = `periodo_anio`, `periodo_mes`, `periodo_dia` (de `validacion_fecha`).
- **pendiente** = dato que no está en el SAS revisado ni en las decisiones tomadas. No se inventa.

---

## 1. Inventario de datos

### 1.1 Fuentes externas

| Fuente | Tipo | Ubicación | Uso | Estado |
|---|---|---|---|---|
| Homologación de tipo de documento | Excel | `ruta_insumos` + `arch_hom_tpo_doc` | Lookup de tipo de documento (CTE/AHO) | Ruta confirmada en SAS |
| Homologación de tipo de documento Nequi | Excel | `ruta_insumos` + `arch_hom_tpo_doc_nequi` | Lookup de tipo de documento (NEQUI) | Ruta confirmada en SAS |
| Códigos de país | Excel | `ruta_insumos` + `arch_paises` | Lookup de país | Ruta confirmada en SAS |
| Códigos DANE | Excel | `ruta_insumos` + `arch_dane` | Lookup de departamento y municipio | **pendiente** (nombre de archivo) |
| Validación de fecha | Excel | `ruta_insumos` + `arch_validacion_fecha` | Periodo (`AÑO`, `MES`, `DIA`) | Ruta confirmada en SAS |
| Depósitos corriente (origen CTE) | Tabla Impala | `impala_dsn` | Entrada de `job_producto` | **pendiente** (nombre de tabla) |
| Depósitos ahorros (origen AHO) | Tabla Impala | `impala_dsn` | Entrada de `job_producto` | **pendiente** (nombre de tabla) |
| Depósitos Nequi (origen NEQUI) | Tabla Impala | `impala_dsn` | Entrada de `job_producto` | **pendiente** (nombre de tabla) |

### 1.2 Cachés en memoria (no son tablas)

Viven durante la ejecución del Job padre. No se escriben en disco.

| Caché | Creada en | Leída en | Contenido | Clave |
|---|---|---|---|---|
| `cache_hom_doc` | `job_insumos` | `jl_validar_documento` (CTE/AHO) | Homologación de tipo de documento | código de tipo |
| `cache_hom_nequi` | `job_insumos` | `jl_validar_documento` (NEQUI) | Homologación Nequi | código de tipo |
| `cache_paises` | `job_insumos` | `jl_validar_ubicacion` | Códigos de país | código de país |
| `cache_dane` | `job_insumos` | `jl_validar_ubicacion` | Departamento y municipio | código DANE |
| `totales_origen_cte` | `job_producto` (CTE) | `job_totales`, `job_conciliacion` | Conteo y suma de saldos de origen | — |
| `totales_origen_aho` | `job_producto` (AHO) | `job_totales`, `job_conciliacion` | Idem | — |
| `totales_origen_nequi` | `job_producto` (NEQUI) | `job_totales`, `job_conciliacion` | Idem | — |
| `totales_salida_cte` | `job_producto` (CTE) | `job_totales`, `job_conciliacion` | Conteo y suma de saldos validados | — |
| `totales_salida_aho` | `job_producto` (AHO) | `job_totales`, `job_conciliacion` | Idem | — |
| `totales_salida_nequi` | `job_producto` (NEQUI) | `job_totales`, `job_conciliacion` | Idem | — |

**Riesgo:** que `tCacheIn` vea los datos escritos por un `tRunJob` hijo no está probado. Ver sección 7.

### 1.3 Variables globales

| Variable | Creada en | Origen | Uso |
|---|---|---|---|
| `periodo_anio` | `job_insumos` | Columna `AÑO` de `validacion_fecha` | Nombres de archivo de salida |
| `periodo_mes` | `job_insumos` | Columna `MES` de `validacion_fecha` | Idem |
| `periodo_dia` | `job_insumos` | Columna `DIA` de `validacion_fecha` | Idem |

### 1.4 Salidas (archivos)

Todas van a `ruta_resultados`.

| Archivo | Creado en | Contenido | Equivalente SAS |
|---|---|---|---|
| `sabana_validada_<sufijo>.csv` | `job_producto` | Registros válidos del producto | Sábanas `SABANA_FINAL_REPORTAR_*` |
| `doc_incorrectos_<sufijo>.csv` | `job_producto` | Registros rechazados, con columna `motivo` | `DOC_INCORRECTOS_TPO*_NEQUI` (ver decisión D2) |
| `totales_exogena_<anio><mes><dia>.csv` | `job_totales` | Total global de cuentas y saldos | `TOTAL_AHORROS_CONS.csv`, `TOTAL_CORRIENTE.csv` |
| `conciliacion_<anio><mes><dia>.csv` | `job_conciliacion` | Diferencias origen vs salida por producto | "Conciliacion final" |
| Log de errores | `jl_registro_errores` | Fallos por componente | — (SAS no tenía registro estructurado) |

---

## 2. Variables de contexto

### 2.1 Grupo `Default` (claves; sin valor de entorno)

| Variable | Tipo | Valor | Nota |
|---|---|---|---|
| `ruta_insumos` | String | `\\sbcldwpsgf01\FILE_VSPC_FINANZAS\` | Ruta del SAS; confirmar por entorno |
| `ruta_resultados` | String | `\\sbcldwpsgf01\FILE_VSPC_FINANZAS\GST_Informacion_Exogena\RESULTADOS\` | Ruta del SAS; confirmar por entorno |
| `arch_hom_tpo_doc` | String | `Homologacion_tpo_dto.xlsx` | |
| `arch_hom_tpo_doc_nequi` | String | `Homologacion_tpo_dto_Nequi.xlsx` | |
| `arch_paises` | String | `Cod_pais.xlsx` | |
| `arch_dane` | String | **pendiente** | |
| `arch_validacion_fecha` | String | `Validacion_fecha.xlsx` | |
| `tolerancia_conciliacion` | BigDecimal | `0` | Confirmar con negocio |
| `log_nivel` | String | `INFO` | `DEBUG` solo en pruebas |

### 2.2 Grupos de entorno (`DEV`, `QA`, `PROD`)

Solo sobrescriben las claves de esta tabla.

| Variable | DEV | QA | PROD | Origen |
|---|---|---|---|---|
| `env_nombre` | `DEV` | `QA` | `PROD` | Validado en `tPrejob` |
| `impala_dsn` | `IMPALA` | `IMPALAC` | `IMPALAP` | Mapeo `D`/`C`/`P` del SAS (`m_ambiente`). Confirmar |
| `impala_host` | pendiente | pendiente | pendiente | No está en el SAS |
| `impala_puerto` | pendiente | pendiente | pendiente | No está en el SAS |
| `impala_usuario` | pendiente | pendiente | pendiente | Usuario de servicio |
| `impala_password` | **sin valor** | **sin valor** | **sin valor** | Vault o metadato cifrado. Nunca en claro |

### 2.3 Parámetros por Job

| Job | Parámetro | Tipo | Origen | Valor |
|---|---|---|---|---|
| `job_producto` | `producto` | String | `tFixedFlowInput` del padre | `CTE`, `AHO`, `NEQUI` |
| `job_producto` | `tabla_origen` | String | `tFixedFlowInput` del padre | **pendiente** por producto |
| `job_producto` | `sufijo` | String | `tFixedFlowInput` del padre | `cte`, `aho`, `nequi` |

### 2.4 Reglas de contexto

- El Job no se edita para cambiar de entorno; solo cambia el grupo de contexto.
- `tPrejob` falla si `env_nombre` no es `DEV`, `QA` o `PROD`, o si una clave de entorno está vacía.
- Ninguna contraseña en claro. `impala_password` se resuelve desde vault o metadato cifrado.
- Los Jobs hijos heredan el contexto del padre (`Transmit whole context`).

---

## 3. Jobs

### 3.1 `job_exogena_depositos` (padre)

| Subjob | Hijo / componentes | Orden | Error |
|---|---|---|---|
| `tPrejob` | `tJava` (validar entorno), `tFileExist` ×5 (insumos) | Inicio | `tDie` |
| A | `tRunJob` → `job_insumos` | `OnSubjobOk` de `tPrejob` | `OnSubjobError` → `tDie` |
| B | `tFixedFlowInput` (productos) → `tFlowToIterate` → `tRunJob` → `job_producto` | `OnSubjobOk` de A | Idem |
| C | `tRunJob` → `job_totales` | `OnSubjobOk` de B (tras los 3 productos) | Idem |
| D | `tRunJob` → `job_conciliacion` | `OnSubjobOk` de C | Idem |
| `tPostjob` | `tLogRow` ("Proceso terminado"), `tDBClose` | Fin | — |

Conexión: `jl_conexion_impala` al inicio, compartida con los hijos.

### 3.2 `job_insumos`

| Componente | Entrada | Salida |
|---|---|---|
| `tFileInputExcel` (hom_tpo_doc) | `arch_hom_tpo_doc` | `jl_normalizar` → `tCacheOut` `cache_hom_doc` |
| `tFileInputExcel` (hom_tpo_doc_nequi) | `arch_hom_tpo_doc_nequi` | `jl_normalizar` → `tCacheOut` `cache_hom_nequi` |
| `tFileInputExcel` (paises) | `arch_paises` | `jl_normalizar` → `tCacheOut` `cache_paises` |
| `tFileInputExcel` (dane) | `arch_dane` | `jl_normalizar` → `tCacheOut` `cache_dane` |
| `tFileInputExcel` (validacion_fecha) | `arch_validacion_fecha` | `tJavaRow` → `tSetGlobalVar` `periodo_*` |
| Error | — | `jl_registro_errores` |

Contexto nuevo: ninguno. Crea las globales `periodo_*`.

### 3.3 `job_producto` (×3, uno por producto)

| Subjob | Componentes | Salida |
|---|---|---|
| Lectura | `tDBInput` (SQL con `WHERE` por producto y `WITH` para pasos intermedios), `jl_normalizar`, `tReplicate` | Flujo a dos ramas |
| Rama A (totales origen) | `tAggregateRow` (conteo, suma de saldos), `tCacheOut` `totales_origen_<sufijo>` | Caché |
| Rama B (validación) | `tMap` (lookups `cache_hom_*`, `cache_paises`, `cache_dane`), `jl_validar_documento`, `jl_validar_ubicacion`, `tMap` (valid/reject) | Dos flujos |
| Valid | `tFileOutputDelimited` → `sabana_validada_<sufijo>.csv`; `tAggregateRow` → `tCacheOut` `totales_salida_<sufijo>` | Archivo y caché |
| Reject | `tFileOutputDelimited` → `doc_incorrectos_<sufijo>.csv` | Archivo |
| Error | `tLogCatcher`, `tLogRow`, `tDie` | — |

Conteo aproximado: 17 componentes (límite del proyecto: 20).

### 3.4 `job_totales`

| Componente | Entrada | Salida |
|---|---|---|
| `tCacheIn` ×6 | `totales_origen_*` (3), `totales_salida_*` (3) | `tUnite` |
| `tUnite` | 6 flujos | `tAggregateRow` (total global) |
| `tAggregateRow` | Flujo unido | `tFileOutputDelimited` → `totales_exogena_<anio><mes><dia>.csv` |
| Error | — | `jl_registro_errores` |

### 3.5 `job_conciliacion`

| Componente | Entrada | Salida |
|---|---|---|
| `tCacheIn` ×6 | Totales origen y salida | `tUnite` → `jl_conciliar` |
| `jl_conciliar` | Totales | Diferencias y marca por producto |
| `tFileOutputDelimited` | Diferencias | `conciliacion_<anio><mes><dia>.csv` |
| `tJavaRow` | Diferencias | `tLogRow` ("Conciliación OK") si ninguna supera `tolerancia_conciliacion`; `tDie` si alguna la supera |
| Error | — | `jl_registro_errores` |

---

## 4. Joblets

| Joblet | Entrada | Salida | Componentes | Usado en |
|---|---|---|---|---|
| `jl_conexion_impala` | Contexto `impala_*` | Conexión compartida | `tDBConnection` | Padre |
| `jl_normalizar` | Fila genérica | Fila limpia (mismo esquema) | `tMap` (trim, mayúsculas, texto/número) | `job_insumos`, `job_producto` |
| `jl_validar_documento` | `tipo_doc`, `nro_doc`, `nombres`, `apellidos`, `dv` | `valid` / `reject` con `motivo` | `tMap` + rutina `DV.calcular` | `job_producto` |
| `jl_validar_ubicacion` | `codigo_pais`, `departamento`, `municipio`, `codigo_dane` | `valid` / `reject` con `motivo` | `tMap` (lookups) | `job_producto` |
| `jl_conciliar` | Totales origen y salida | Diferencia y marca por producto | `tMap` (join por producto, comparación) | `job_conciliacion` |
| `jl_registro_errores` | `OnComponentError` | Fila de log | `tLogCatcher`, `tLogRow` | Todos los Jobs |

**Rutina:** `DV.calcular` (rutina Java reutilizable). Algoritmo **pendiente** de copiarse del SAS.

---

## 5. Decisiones tomadas

| ID | Decisión | Motivo |
|---|---|---|
| D1 | Sin tablas intermedias. Entradas y salidas finales son las únicas persistencias | El SAS tiene 348 tablas WORK; la mayoría son pasos encadenados |
| D2 | Un solo archivo de rechazos por producto, con columna `motivo` | Más simple que ocho archivos para NEQUI; **por confirmar con negocio** |
| D3 | Un solo `job_producto` parametrizado en lugar de 30 copias | Las copias del SAS difieren; hay que verificar equivalencia |
| D4 | `tReplicate` para totales de origen y validación en una sola lectura | Conciliación compara la misma ejecución |
| D5 | Credenciales fuera del contexto plano | `BP-SEC-01` |
| D6 | Un `job_producto` por producto, con el producto como parámetro | Límite de 20 componentes por Job |

---

## 6. Equivalencias con el SAS

| Concepto SAS | Equivalente Talend |
|---|---|
| 30 bloques de macros (`%macro ambiente` ×30) | `job_producto` parametrizado |
| `%split2`, `sessio&i`, `rsubmit`, `waitfor` | No necesario: Impala paraleliza el SQL |
| `PROC SQL` sobre WORK (348 tablas) | SQL con `WITH` en `tDBInput` |
| `PROC EXPORT` + `PROC UPLOAD` remoto | `tFileOutputDelimited` directo a `ruta_resultados` |
| `signon` con contraseña en claro | `jl_conexion_impala` con vault o metadato cifrado |
| `%web_open_table`, `%web_drop_table`, `options mprint` | Eliminados (ruido de Studio) |
| `%put` de depuración | `tLogRow` y `log_nivel` |
| Macros `%ambiente` (D/C/P) | Grupos `DEV` / `QA` / `PROD` |

---

## 7. Pendientes y riesgos

| # | Tema | Tipo | Bloquea |
|---|---|---|---|
| P1 | Nombre de archivo DANE (`arch_dane`) | Dato | `job_insumos` |
| P2 | Nombres de tablas de origen por producto (`tabla_origen`) | Dato | `job_producto` |
| P3 | `impala_host`, `impala_puerto`, `impala_usuario` por entorno | Dato | Todo |
| P4 | Confirmar `impala_dsn` (`IMPALA`, `IMPALAC`, `IMPALAP`) | Dato | Todo |
| P5 | Algoritmo de DV (copiar del SAS) | Lógica | `jl_validar_documento` |
| P6 | Confirmar que las 30 copias del SAS son equivalentes | Verificación | `job_producto` (D3) |
| P7 | Confirmar D2 (un archivo de rechazos o ocho) | Decisión | `job_producto` |
| P8 | Confirmar `tolerancia_conciliacion` (`0`) | Decisión | `job_conciliacion` |
| R1 | `tCacheIn` ve datos de `tRunJob` hijos | Riesgo técnico | Diseño de cachés (sección 1.2) |
| R2 | Memoria para cachés y `tMap` con el volumen real | Riesgo | `job_producto` |
| R3 | `tUniqRow` y `tImpala*` no vienen instalados por defecto | Riesgo | Si se usan |
| R4 | Pushdown de `WHERE` y `WITH` en `tDBInput` | Riesgo técnico | `job_producto` |

---

## 8. Orden de construcción propuesto

1. Prueba mínima de `tCacheOut` / `tCacheIn` entre `tRunJob` (R1).
2. Conexión `jl_conexion_impala` y prueba de lectura de una tabla de origen (P2, P3, P4).
3. `job_insumos` con las cinco lecturas de Excel.
4. `job_producto` para un solo producto (CTE) con sus joblets.
5. Extender a AHO y NEQUI tras comparar contra el SAS (P6).
6. `job_totales` y `job_conciliacion`.
7. Padre `job_exogena_depositos` con su `tPrejob` y `tPostjob`.
