# Ruta a la meta y a producción: plan completo en tareas

Escrito el 4 de noviembre de 2026, con el repositorio en el commit `a2832f4` (hito 79). Es el plan
maestro que reemplaza el orden de trabajo de `tareas-agente.md` (que queda como detalle de las tareas T)
y de `plan-corpus-y-equivalencia.md` (que queda como detalle del corpus). Cada tarea tiene un
identificador `R<fase>-<n>`, quién la hace, de qué depende, qué entrega y cómo se sabe que terminó.
Léelo completo antes de tomar una tarea.

## 0. Cómo leer este documento

- **Tipos de tarea.** **[H]** la puede hacer un subagente `haiku` con la especificación de la tarea.
  **[R]** investigación con validación ejecutada (no se da por buena sin ejecutarla). **[D]** requiere una
  decisión de diseño de quien dirige. **[P]** la tiene que hacer una persona (el agente la prepara).
- **Horas.** `h-ag` son horas de trabajo de agente (estimación gruesa; un agente haiku con revisión).
  `d-p` son días de persona.
- **Dependencias.** `dep:` lista las tareas que deben estar terminadas antes.
- **Referencias a T y K.** Las tareas `T..` son las de `tareas-agente.md`; las `K..`, las de
  `plan-corpus-y-equivalencia.md`. Aquí se reagrupan y se completan.
- **Estado.** Cada tarea trae su estado inicial: `hecho`, `parcial` o `pendiente`.

## 1. Qué significa "terminar": tres niveles

| Nivel | Nombre | Definición de terminado (medible) |
|---|---|---|
| N1 | Paridad con el diseño manual | Los Jobs de `client_large.sas` (padre, producto, totales, conciliación y sus joblets) se generan con `sgm talend`, no pasan de 20 componentes cada uno, se ejecutan en Studio con los casos L8 del corpus y dan el resultado esperado; el documento de diseño emitido tiene las 8 secciones y la conformidad contra las 168 filas del manual pasa en 100 o más, con toda diferencia explicada |
| N2 | Equivalencia verificada | Un traductor general (no a medida) genera los Jobs de los casos `traducible` del corpus, todos pasan en Studio, y al menos dos programas más de `tests/fixtures/sas` se traducen con cobertura medida y huecos listados |
| N3 | Producción | Corrida paralela con datos reales aprobada contra el SAS, operación definida (programación, alertas, runbook, promoción entre entornos), seguridad revisada y corte firmado |

N1 es la meta que pidió el usuario. N2 es lo que hace creíble el resultado y reutilizable. N3 es lo que
hay que cumplir para decir "producción 100 %". Cada nivel exige el anterior.

## 2. Punto de partida (medido el 4 de noviembre de 2026)

| Medida | Valor |
|---|---|
| Componentes emitidos por `sgm talend client_large.sas` | 26 (padre 13, producto 11, totales 1, conciliación 1); meta N1 unos 80 |
| Conformidad contra el diseño manual (`tests/conformidad`) | 42 pasan, 126 xfail (25 %) |
| Pendientes del modelo para el programa grande | 16 |
| Casos del corpus con resultado esperado | 117 (L0 a L6: 101; L8: 16) |
| Casos del corpus traducidos por un traductor automático y pasados en Studio | 0 (1 demostración con un Job escrito a mano) |
| Suite | 1529 pruebas pasan, 26 se saltan, 132 xfail; `ruff` limpio |
| Entornos de prueba | Studio 8.0.1 con el proyecto `PRJ_BANCOLOMBIA`; `talend-mcp` como validador; Docker con Impala 4.5.3 real, PostgreSQL y otras imágenes locales |

Desde el hito 80 estas cifras se miden con `uv run python tools/tablero.py` (y se cierran con
`uv run python tools/ci.py`); la instantánea de la línea base está en `metricas-base.md`.

### 2.1 Lo que ya existe y no hay que rehacer

| Pieza | Dónde | Estado |
|---|---|---|
| Frontend SAS, linaje, modelo de proceso | `src/sgm/frontend`, `flow`, `proceso` | Hecho, con huecos listados en `tests/corpus/HUECOS_FRONTEND*.md` |
| Emisor `.item` de Talend 8.0.1 con 24 plantillas, conexiones, contextos, `tMap` con lookup y rechazo | `src/sgm/talend_item/` | Hecho; ningún Job abierto aún en el editor gráfico |
| Padre completo, `job_producto` con tipo de documento (T10), totales de origen | `jobs_diseno.py`, `jobs_producto.py` | Parcial |
| Detección de validaciones por lookup, ubicación, reglas de cuenta, tablas finales (T11, T12 detección, T14 reglas, T19 análisis, T20) | `proceso/validaciones.py`, `reglas.py`, `salidas.py` | Detección hecha; falta generar los Jobs |
| Validador en Studio, prueba de humo, emulador de tablas Impala (T01, T04, T03) | `tools/validar_en_studio.py`, `tools/simular_tablas.py` | Hecho, con cuatro fallos conocidos (R0-02) |
| Corpus, oráculo SQL, vectores de semántica, ejecutor, arnés de Studio | `tests/corpus/`, `tools/corpus*.py`, `tools/corpus_lib/` | Hecho para L0 a L8; faltan L7 y L9 |
| Contenedores de prueba | `tools/contenedores/` | Impala real y PostgreSQL; falta escritura con `tPostgresqlOutput` |

## 3. Decisiones que necesita el proyecto

Estas decisiones desbloquean tareas. La columna "por omisión" es lo que el agente asume si nadie decide.

| ID | Decisión | Opciones | Por omisión | Quién | Bloquea |
|---|---|---|---|---|---|
| DC-01 | Alcance del producto | (a) migrar solo `client_large.sas`; (b) migrador general | (a) primero, (b) como fase N2 | Usuario | Fase 7 completa |
| DC-02 | Archivos de rechazo (D2) | Uno por producto con columna `motivo`; o uno por tipo de error | Uno por producto con `motivo` | Negocio | R1-17 |
| DC-03 | Un `job_producto` para NEQUI (D6, P6) | Comparte el Job; o Job propio | Comparte el Job (misma estructura de 23 columnas) | Negocio | R1-16 |
| DC-04 | Tolerancia de conciliación | Valor numérico por producto | 0, marcada "confirmar con negocio" | Negocio | R2-03 |
| DC-05 | Despliegue | Studio con programador; Talend Management Console con motor remoto; otro | Sin decidir | Plataforma | Fase 9 |
| DC-06 | Almacén de secretos | Contexto cifrado de Talend; vault corporativo; variables de entorno | Contexto sin valor, secreto externo | Seguridad | R4-05 |
| DC-07 | Rutas y tablas reales por entorno | Valores de DEV, QA y PROD | Vacíos, marcados pendientes | Plataforma | R4-06, Fase 9 |
| DC-08 | Código de fallo parcial | El proceso falla si falla un producto; o continúa con los demás | Falla todo (`DIE_ON_CHILD_ERROR`) | Negocio | R2-07 |
| DC-09 | Ventana y frecuencia de ejecución | Cinco por día, semanal, mensual, trimestral (SAS-A-TALEND) | Sin decidir | Negocio | R9-03 |
| DC-10 | Corrida paralela | Número de ciclos, quién corre el SAS, criterio de aprobación | Mínimo 3 cierres, diferencia 0 en conteos y dentro de tolerancia en sumas | Negocio y auditoría | R9-10 |
| DC-11 | Dependencias del repositorio | `sqlglot`, `jsonschema` (declaradas, fuera de la lista permitida), `pytest-testmon` | Documentar en "Decisiones" | Usuario | R0-04 |
| DC-12 | Significado de los códigos de tipo de documento | Tabla de negocio | Los del Excel de homologación | Negocio | R1-03 |

## 4. Principios de ejecución

1. **Una tarea que genera Jobs termina ejecutándose en Studio** contra el caso del corpus que le corresponde,
   con la salida literal pegada en `PROGRESS.md`. Compilar no basta (varias veces compiló y falló al ejecutar).
2. **Nada se inventa.** Lo que el SAS no demuestra queda pendiente con motivo. Las cifras del manual no se
   copian al YAML para "pasar" filas de conformidad.
3. **El resultado esperado nunca lo calcula quien escribe el traductor.** Sale del generador de datos
   (anomalías plantadas), de un oráculo independiente (SQLite, referencia en Python con fuente) o de un segundo
   agente que no vio el primero.
4. **Un commit por tarea o por grupo pequeño**, `hito N: <resumen>`, con la línea de coautoría. Nunca
   `git push`. Cada commit con suite verde y `ruff` limpio.
5. **Subagentes `haiku` para el trabajo mecánico;** quien dirige decide, revisa y verifica por su cuenta (corre
   la suite, comprueba que el proyecto de Talend quedó limpio). Un informe de agente no es evidencia.
6. **Nombres de Job nuevos en cada intento de validación** (Studio guarda los Jobs por identificador).
7. **Nada de MCP en el producto** (`src/`, `rules/`); `talend-mcp` solo como validador externo desde
   `tools/`. Los contenedores solo para probar los Jobs generados, nunca desde `sgm`.
8. **Cada hito anota lo no verificado** y el riesgo, no solo lo hecho.
9. **Protocolo de Studio, hechos aprendidos y reglas de `AGENTS.md`:** ver `tareas-agente.md` secciones 1.4 y 3.

## 5. Fase 0. Estabilización y herramientas (requisito de todo lo demás)

Cerrada en el hito 80. Las tareas que el criterio solo puede cumplir con Studio o con una máquina
limpia quedan `hecho (sin verificar en Studio)` o `parcial`, con el bloqueo anotado en `PROGRESS.md`.

| ID | Tarea | Tipo | dep | Entrega y criterio | h-ag | Estado |
|---|---|---|---|---|---|---|
| R0-01 | Renumerar los hitos duplicados (69 a 77 aparecen en dos series) y fijar una regla de numeración | H | | `PROGRESS.md` y `docs/` sin números repetidos; nota "numeración" en `AGENTS.md` (qué hacer con sesiones paralelas: prefijo por serie) | 1 | hecho |
| R0-02 | Corregir `tools/validar_en_studio.py`: `exportar` busca el lanzador en subcarpetas, `renombrar` sin versión fija, `ejecutar` con comillas, borrar `build-*` de `%TEMP%` | H | | Pruebas de cada corrección con doble del cliente; demostración real | 2 | hecho (12 pruebas con doble; busqueda recursiva, comillas y borrado del build verificados en Studio en el hito 81) |
| R0-03 | Quitar la `_exportar` duplicada del arnés del corpus y usar la corregida | H | R0-02 | `tools/corpus_lib/studio_validar.py` sin código duplicado; demostración repetida (`l2_01` coincide) | 1.5 | hecho (falta repetir `l2_01` en Studio) |
| R0-04 | Decidir y anotar dependencias (DC-11) | D/P | | Sección "Decisiones" de `PROGRESS.md`; `pyproject.toml` coherente | 0.5 | hecho |
| R0-05 | Actualizar `observacion_revision` obsoletas de L8/totales 03 y 08 | H | | Texto acorde a la convención de faltantes vigente | 0.5 | hecho |
| R0-06 | `tools/ci.py`: un comando que corre `ruff`, `pytest`, `corpus oraculo --verificar`, cruces y reporta | H | | Sale con código distinto de 0 si algo falla; documentado en el README | 2 | hecho |
| R0-07 | Reproducibilidad: clonar en máquina limpia, `uv sync`, suite verde; documentar prerrequisitos (Studio, Docker, `talend-mcp`, JDK) | H | | Guía `docs/puesta-en-marcha.md` probada paso a paso | 2 | parcial (guía escrita y `uv sync` verificado aquí; falta la máquina limpia) |
| R0-08 | Higiene del repositorio: `.gitignore` (`out/`, `.commandcode/`, `%TEMP%`), tamaño de fixtures, archivos temporales | H | | `git status` limpio tras una ejecución completa | 1 | hecho |
| R0-09 | Tablero `tools/tablero.py`: componentes por Job, conformidad, casos del corpus por estado y nivel, pendientes por motivo, cobertura de construcciones SAS | H | | Un comando que imprime la tabla de la sección 2; se pega en cada hito | 3 | hecho |
| R0-10 | Registro de riesgos del oráculo: cada entrada de `DIFERENCIAS.md` con severidad, caso que la ejercita y plan | H | | `tools/corpus_lib/RIESGOS.md` | 2 | hecho |
| R0-11 | Línea base: etiqueta git `base-n1`, instantánea de métricas | H | R0-09 | Etiqueta y archivo `docs/plan-reescritura/metricas-base.md` | 0.5 | hecho |
| R0-12 | Guía ejecutable de validación en Studio (`docs/guia-validacion-studio.md`) consolidando protocolo, hechos y comandos | H | R0-02 | Un agente nuevo valida un Job siguiendo solo la guía | 1.5 | parcial (guía escrita; falta la prueba con un agente y Studio) |

## 6. Fase 1. `job_producto`: toda la lógica de validación (N1)

Cada tarea de esta fase termina con el caso del corpus ejecutado en Studio mediante
`tools/corpus_studio.py validar`. Se trabaja sobre `src/sgm/talend_item/jobs_producto.py` (dividir en módulos
`validacion_*.py` al pasar de 300 líneas) y se declara en `decisiones/client_large.jobs.yaml` solo lo que el
SAS no puede demostrar.

| ID | Tarea | Tipo | dep | Casos y criterio | h-ag | Estado |
|---|---|---|---|---|---|---|
| R1-01 | Validar el filtro del `tMap` (`expressionFilter`) aislado en Studio; si falla, plantilla de `tFilterRow` validada ejecutando | R+H | | Job mínimo: filas que pasan y que no; resultado en `PROGRESS.md`. Desbloquea R1-04 a R1-09 | 3 | hecho (hito 81 y cierre en el 82: filtro seguro e inseguro ejecutados con filas sin pareja; `null_safe_equals` en `expresiones.py`) |
| R1-02 | Normalización inicial: `tMap` que convierte las columnas numéricas (las marcadas `numerica` por `esquema_csv`) con la semántica fiel de `input(left(x), N.)`, `compress`, mayúsculas y caracteres especiales | R+H | | `L4`, `L8/validaciones/v06`; vectores con fuente (blancos internos, signo, decimales con coma, ceros a la izquierda, no numérico a faltante) | 5 | hecho con salvedades (hito 83: 45 vectores con fuente y esperados independientes coinciden ejecutando en Studio, `normalizacion.py`; hito 84: `sgm talend` emite `tMap_normalizacion` con los 15 informats `w.d` reales y los 4 Jobs compilan en Studio). Salvedades: decimales con coma sin vector con fuente; `compress`/`UPCASE`/`COMPBL` verificadas como expresiones pero aún sin asignar a columnas del emisor (R1-05/R1-08). El hito 85 ejecutó con datos el `job_producto` emitido (v01, CTE/AHO, insumos simulados), así que retira la salvedad de "solo compilación" para ese Job; sigue pendiente la equivalencia N2 de G4 con los datos reales del cliente |
| R1-03 | Tipo de documento: cerrar T10 con el caso `v01` y `L2`; el Excel de homologación cambia por producto; documentar la comparación de texto frente a número (`01` y `1`) | H | R1-02 | `v01` coincide para CTE, AHO y NEQUI; válidos más rechazados igual al origen | 3 | parcial (hito 85: el `job_producto` **emitido** se ejecuta en Studio con datos de `v01`; 6 combinaciones, 12 corridas, invariante origen=válidos+rechazados; el lookup coincide en CTE 88/7 y AHO 60/5 cuando ambos lados de la unión tienen la misma escritura; queda documentado que `input(..., 8.)` deja faltantes los códigos de texto `TDxx` y que `01` normalizado a `1` no casa con un Excel `01`). **Bloqueos reales**: sin SAS no se demuestra el tipo de `PROC IMPORT` ni el formato de `PROC EXPORT` (`v01` y `v08` en `pendiente_revision`, DC-12 de Negocio); NEQUI no está en `v01` sino en `v08`/R1-16. No se cambia el emisor sin esa decisión |
| R1-04 | Vacíos y ceros: titulares y cotitulares, firmas autorizadas, número de documento no vacío ni cero | H | R1-01 | `v02` coincide, incluidos los conteos de anomalías plantadas | 4 | parcial (parte 1 cerrada en el emisor). Hito 86: las 3 reglas salen del propio `WHERE` del SAS (`v02` y `client_large.sas`) con `proceso/reglas_fila.py`, se traducen a `expressionFilter` nulo-seguros con `talend_item/filtros_fila.py` y un Job mínimo (`v86c`) coincide fila por fila con `esperado/`. Hito 87: **`sgm talend` ya emite los tres flujos dentro del `job_producto`**, como tercera rama de `tReplicate_1` (`talend_item/flujos_fila.py`), con la proyección de 19 columnas y los nombres de tabla leídos del `SELECT`/`CREATE TABLE` del SAS real, y 3 CSV con `context.sufijo`. `flujos_producto()` exige que los bloques CTE/AHO tengan la misma forma y publica como `Pendiente:` las 4 revalidaciones posteriores. Los 4 Jobs compilan en Studio (`v87d`) y el **Job emitido** ejecutado con datos (`v87c`, CTE 5/5/85 y AHO 3/2/70) coincide fila por fila en las columnas estables, reproduce el desglose vacío/cero y las tres invariantes, con `SUMA_SALDO_CTE_VALIDAS` = 1024505. Quedan fuera la cadena larga de `Campos vacios` (parte 2 de R1-04), `RECHAZO_NRO_DOC_*` y las tablas de conteo como salidas del Job. **Bloqueos reales**: `v02` sigue `pendiente_revision` (sin SAS no se demuestra el tipo de `PROC IMPORT`, el formato de `PROC EXPORT` ni el formato `30.` de `NRO_DOC`); la normalización R1-02 deja vacías `TIPO_DOC`/`LLAVE_NOMBRE` en ese caso (salvedad de R1-03/DC-12); la equivalencia N2 de G4 exige los insumos reales del cliente |
| R1-05 | Ubicación: país contra `Cod_pais.xlsx`, DANE contra `CODIGOS_DANE.xlsx`, dirección; motivos distintos por regla | H | R1-01 | `v03` coincide; la parte de `LENGTH`, `COMPBL` y `CONTAINS` queda con su regla de Java documentada | 4 | parcial, **`v03` coincide fila por fila en Studio** (hito 91, sufijo `v91b`: `INCONS_UBICACION_*` con 8 y 5 filas, `UBIC_VALIDA_*` con 80 y 55, 20 vectores propios con 14 rechazos y 6 válidos, invariantes OK). `proceso/reglas_ubicacion.py` lee la regla del caso y `talend_item/flujos_ubicacion.py` la cuelga del `job_producto` emitido con dos lookups Excel en `LEFT JOIN`. **`LENGTH` y `CONTAINS`** están traducidos a Java con su regla documentada. **`COMPBL`** no aparece en `v03`: no se traduce ni se demuestra. **Pendiente**: el SAS de cliente tiene otra forma (`'169'`, motivo `CAMPOS DE UBICACION INCORRECTOS` y variantes que corrigen en vez de rechazar), así que su Job no emite la rama; la unión `SABANA_UBIC` por `LLAVE_NOMBRE` no está en el Job (R1-02 deja la llave vacía); `Codigo_Pais` quita ceros con `input()` y el Job compara como texto; el truncamiento del `CASE` no lo ha ejecutado SAS. |
| R1-06 | Tipo de cuenta, GMF y Codex inválidos con las listas de valores del SAS (T14) | H | R1-01 | `v04` coincide | 4 | parcial, **las dos formas están traducidas y ejecutadas** (hito 74: `reglas.py` detecta los `NOT BETWEEN` del SAS real; hito 88: `v04` coincide fila por fila en Studio; **hito 89: la forma del SAS real está dentro del `job_producto` emitido y coincide fila por fila**). Hito 88: `proceso/reglas_cuenta.py` lee de `v04/programa.sas` `TIPO_CTA NOT IN ('1'..'5')`, `GMF IS MISSING OR NOT BETWEEN 1 AND 10`, los tres motivos del `CASE`/`OUTER UNION`, el informat `3.` y las cuatro proyecciones; `filtros_cuenta.py` los traduce a `expressionFilter` nulo-seguros (**faltante de SAS contado como menor que cualquier número**), y el Job aislado corre en Studio (`v88a`, CTE 4/5/81/9 y AHO 6/3/56/9, código 0). Hito 89: `proceso/reglas_cuenta_real.py` lee del `client_large.sas` los dos `NOT BETWEEN` con `RELACION = 1000` (`TIPO CTA INVALIDO` antes, `CODEX INVALIDO` después sobre `SABANA_TIPO_CTA_VALIDO_*`), las 19 columnas del `SELECT` y las 19+`INCONSISTENCIA` de `INCONS_PAQ_*`; `filtros_cuenta_real.py` respeta la cascada, la exención de `RELACION <> 1000` y el orden de motivos; `flujos_cuenta_real.py` cuelga la cuarta rama de `tReplicate_1` con `tMap_cuenta` y 4 CSV. El **Job emitido** ejecutado con datos (`v89a`, CTE 3 de codex, AHO 2, y 8 vectores propios para lo que `v05` no planta) coincide fila por fila en las columnas estables con las tres invariantes OK; los 4 Jobs compilan (`v89b`). **No se unifican las dos escrituras**: cada forma conserva sus motivos y su sintaxis. `job_producto` pasa de 16 a 21 nodos y el tablero de 31 a 36 componentes. **Bloqueos reales**: `v04` y `v05` siguen `pendiente_revision` (sin SAS no se demuestra el formato `3.` de `PROC EXPORT` ni el tipado de `PROC IMPORT`); se comparan las tablas de `esperado/`, no los archivos de `esperado/archivos/`; 29 reglas de rango del SAS (NEQUI, `DOC_INCORRECTOS_*`, `FINAL_VALIDAR_*`), el `INNER JOIN`/`OUTER UNION CORR` completo y R1-07 (saldos negativos) siguen fuera del Job; la equivalencia N2 de G4 exige los insumos reales del cliente y DC-12 sigue abierta |
| R1-07 | Saldos negativos y campos negativos | H | R1-01 | `v05` coincide | 2 | parcial, **el saldo negativo del caso `v05` coincide fila por fila en Studio** (hito 90, sufijo `v90a`: `INCONS_SALDO_NEG_*` con 4 y 5 filas, `SABANA_VALIDA_*` con 83 y 58, sumas 1000067 y 698117, y 15 vectores propios con faltante, `-0.00` y codex cruzado). `proceso/reglas_saldo.py` lee la regla del caso (macro `saldo_negativo`, `FIN_SALDO_CTA < 0`, motivo `SALDO NEGATIVO`, dos `NOT IN`) y `talend_item/flujos_saldo.py` la cuelga del `job_producto` emitido. **Pendiente**: el SAS de cliente pone los negativos en cero (`IFN`, `CONSOLIDADO_SIN_NEGATIVOS`) y no los rechaza, así que su saldo no se separa; `VAL_CRED_MES`, `INCONS_DEP_CAMPOS_NEGATIVOS_*` y los negativos de corriente y ahorros del bloque de exógena no están traducidos; el `NOT IN` por llave se traduce por fila, con la salvedad de llave única |
| R1-08 | Firmas autorizadas duplicadas, titulares, paquetes titular-cotitular, FA vigentes y no vigentes: leer las etiquetas del SAS, describir y traducir | R+H | R1-01 | Descripción en `PROGRESS.md`; caso nuevo en `L8/validaciones` con anomalías plantadas | 6 | pendiente |
| R1-09 | Cuentas AFC y relaciones; filtro con el maestro de clientes de Impala | R+H | R4-03 | Caso nuevo; lectura contra el Impala del contenedor | 6 | pendiente |
| R1-10 | Extranjeros: reemplazo del número de identificación (`reemplazo_nid_ext`) y separación nacional y extranjero | R+H | R1-02 | Caso `L8/totales/03` y uno nuevo con reemplazos plantados | 4 | pendiente |
| R1-11 | Dígito de verificación: leer el algoritmo en el SAS ("Calcula DV"), traducirlo a una expresión de Java dentro del `tMap` (sin rutinas de Studio) y probar con vectores | R+H | R1-02 | Vectores de DV (propios, con el cálculo de referencia en Python) coinciden | 4 | pendiente |
| R1-12 | Duplicados y frecuencias: `tUniqRow` (plantilla nueva) o agregado con grupo; qué fila se conserva en `NODUPKEY` | R+H | R6-03 | `L8/totales/01`, `L6`; la regla de qué fila se conserva se confirma ejecutando y se anota como supuesto | 4 | pendiente |
| R1-13 | Corrección de inconsistencias: corregidas y por corregir, archivo de inconsistencias | H | R1-04..R1-08 | `L8/totales/02` coincide (56 filas en la sábana) | 6 | pendiente |
| R1-14 | Sábana final y salidas: `RESULTADO_<P>_NAL.csv`, `_EXT.csv`, `INCONS_DEP_<P>.csv`, `INCONS_DEP_CORREGIDA_<P>.csv` con el orden de columnas del `SELECT` final | H | R1-13 | `L8/totales/03`, `v07`; invariante origen igual a válidos más rechazados | 5 | pendiente (análisis hecho) |
| R1-15 | Comprobación en ejecución de las invariantes del producto (conteos y sumas) con `tJava` y `tDie` si no cuadran | H | R1-14 | Un caso con diferencia plantada hace fallar el Job con mensaje claro | 2 | pendiente |
| R1-16 | NEQUI: variante de la cadena (sin tipo de cuenta validado), uso de `Base_datos_Nequi.csv` | D+H | DC-03 | `v08` coincide; el auxiliar tiene destino o queda pendiente con motivo | 4 | pendiente |
| R1-17 | Archivos de rechazo según DC-02 y columna `motivo` | D+H | DC-02 | Salida acorde con la decisión; documento de diseño lo refleja | 3 | pendiente |
| R1-18 | Completar el parámetro del producto en el padre (archivo, homologación, ubicación) desde el modelo, sin YAML repetido | H | R1-03 | `sgm talend` imprime solo pendientes reales | 2 | parcial |

## 7. Fase 2. Totales, conciliación, errores y periodo (N1)

| ID | Tarea | Tipo | dep | Criterio | h-ag | Estado |
|---|---|---|---|---|---|---|
| R2-01 | Mecanismo para pasar totales entre Jobs sin caché: probar ejecutando `tBufferOutput` con `PROPAGATE_CHILD_RESULT`, archivos de totales en una carpeta de trabajo y variables de contexto; recomendar uno con evidencia (T30) | R | | Tres Jobs de ejemplo y tabla comparativa en `PROGRESS.md` | 3 | pendiente |
| R2-02 | `job_totales`: unir los totales de los productos (`tUnite`) y escribir `totales_exogena_<anio><mes><dia>.csv` | H | R2-01 | `L8/totales/04` coincide; columnas iguales a `TOTAL_AHORROS_CONS` y `TOTAL_CORRIENTE` | 3 | esqueleto |
| R2-03 | `job_conciliacion`: diferencias origen contra salida, tolerancia, archivo `conciliacion_<anio><mes><dia>.csv`, `tDie` si se excede | H | R2-02, DC-04 | `L8/totales/05` en sus dos variantes (concilia y no concilia) | 3 | esqueleto |
| R2-04 | Periodo en nombres de archivo y rutas (año, mes, día desde el contexto) | H | | `L8/totales/06` coincide | 2 | parcial |
| R2-05 | `OnSubjobError` y `OnComponentError`: leer el `lineStyle` del enum `EConnectionType`, validar ejecutando un fallo provocado, añadir `conexiones.al_fallar_*` (T33) | R+H | | Un Job que falla activa su rama de error | 3 | pendiente |
| R2-06 | Registro de errores (`tLogCatcher` y salida a archivo) y nivel de log por contexto | H | R2-05 | Archivo de log con componente, mensaje y hora; `log_nivel` DEBUG o INFO cambia lo escrito | 3 | pendiente |
| R2-07 | Semántica de fallo del padre (DC-08): qué pasa si falla un producto, código de salida del lanzador | D+H | DC-08 | Pruebas ejecutadas de los tres escenarios | 2 | pendiente |

## 8. Fase 3. Joblets y tamaño (N1)

El diseño manual fija un máximo de 20 componentes por Job. Hoy `job_producto` tiene 11 y le faltan unas diez
validaciones: pasará de 20 sin una reestructura. Hay dos caminos; se prueba el primero y, si falla, el segundo.

| ID | Tarea | Tipo | dep | Criterio | h-ag | Estado |
|---|---|---|---|---|---|---|
| R3-01 | Formato del `.item` de joblet: extensión y estructura, `tJobletInput` y `tJobletOutput`, validar que Studio lo carga (reinicio incluido si hace falta, con permiso) y que un Job lo usa y corre (T40) | R | | Joblet de ejemplo ejecutado, o evidencia de que no es viable | 3 | pendiente |
| R3-02 | Detección de cadenas repetidas dentro de una etapa con parámetros que difieren (T41) | D+H | | `proceso/joblets.py` y `decisiones/<programa>.joblets.yaml` que confirma | 3 | pendiente |
| R3-03 | Los seis joblets del diseño: `jl_normalizar`, `jl_validar_documento`, `jl_validar_ubicacion`, `jl_conciliar`, `jl_registro_errores`, `jl_conexion_impala` (T42) | H | R3-01, R1 completa | Cada uno ejecutado con su caso; `job_producto` por debajo de 20 componentes | 6 | pendiente |
| R3-04 | Plan B si R3-01 no es viable: Jobs hijos reutilizables (`job_validar_documento`, etc.) invocados con `tRunJob` por etapa | H | R3-01 | Mismo resultado en los casos; tamaño y número de Jobs documentados como desviación del diseño manual | 4 | pendiente |
| R3-05 | Reescribir `job_producto` sobre joblets o hijos y re-ejecutar todo L8 | H | R3-03 o R3-04 | Todos los casos L8 coinciden; Job por debajo de 20 | 3 | pendiente |
| R3-06 | Informe de tamaño (T20, T63): componentes por Job frente al manual | H | R3-05 | Tabla en el documento de diseño emitido | 1.5 | parcial |

## 9. Fase 4. Contextos, entornos, Impala y secretos (N1)

| ID | Tarea | Tipo | dep | Criterio | h-ag | Estado |
|---|---|---|---|---|---|---|
| R4-01 | Contextos completos: `ruta_insumos`, `ruta_resultados`, `arch_*`, `tolerancia_conciliacion`, `log_nivel`; pendientes listados (T50) | H | | Sección 2.1 del diseño emitida; `sgm talend` lista lo que falta | 2 | parcial |
| R4-02 | Grupos DEV, QA y PROD: `env_nombre`, `impala_dsn` derivado de la macro `ambiente` del SAS (D a `IMPALA`, C a `IMPALAC`, P a `IMPALAP`), host, puerto y usuario vacíos | H | | Ejecución con `--context=QA` imprime el valor de QA | 2 | parcial |
| R4-03 | Conexión Impala compartida: `tImpalaConnection` con `;auth=noSasl` en pruebas, `CONNECTION` hacia los hijos, `tImpalaClose`; plantillas corregidas (T51) | R+H | | Job que abre, consulta con dos hijos y cierra, contra el Impala del contenedor | 4 | parcial |
| R4-04 | Lecturas de Impala del SAS (`connect to IMPALA ... select ... from connection to IMPALA`) traducidas literalmente: maestro de clientes, MCDQ, canales | R+H | R4-03 | `L8/totales/07` coincide contra el Impala del contenedor con las tablas cargadas | 6 | pendiente |
| R4-05 | Secretos: nada en claro en `.item`, `.properties`, contextos ni logs; prueba automática que escanea los artefactos; método de entrega del secreto según DC-06 | H+P | DC-06 | Prueba en `pytest` que falla si aparece un valor sospechoso; documento del método | 3 | pendiente |
| R4-06 | Rutas y tablas reales por entorno | P | DC-07 | Valores entregados; el agente los carga en los contextos de cada grupo | 1 d-p | pendiente |
| R4-07 | Productos parametrizados desde la agrupación, sin tocar código para un producto nuevo | H | | Prueba con un cuarto producto sintético | 2 | parcial |
| R4-08 | Tabla de parámetros por Job emitida desde los contextos reales (T52) | H | R4-01 | Sección 2.3 del diseño | 1 | pendiente |
| R4-09 | Escritura a base (si el diseño la requiere) con `tPostgresqlOutput` o `tImpalaOutput`: resolver el fallo de `dbType` nulo con nodos escritos fuera de Studio | R+H | | Plantilla validada escribiendo y leyendo | 4 | pendiente |

## 10. Fase 5. Documento de diseño emitido y conformidad (N1)

| ID | Tarea | Tipo | dep | Criterio | h-ag | Estado |
|---|---|---|---|---|---|---|
| R5-01 | Secciones 2, 4, 5, 7 y 8 en `sgm proceso` (T60); la 5 desde un YAML `decisiones` con id, texto y motivo | H | R4-01 | Cada sección con prueba y filas de conformidad | 3 | pendiente |
| R5-02 | Corregir 1.1, 1.2, 1.3 y 3 con lo probado: CSV de producto como fuentes, "sin cachés" con su motivo, variables de contexto del periodo, Jobs reales con su número de componentes (T61) | D+H | R3-05 | El documento emitido ya no contradice al código | 2 | pendiente |
| R5-03 | `sgm conformidad <programa>`: resumen de filas derivadas, declaradas, pendientes y diferencias con motivo (T62) | H | | Reporte reproducible; es la medida de "se parece" | 1.5 | pendiente |
| R5-04 | Llevar la conformidad de 42 a 100 o más filas sin copiar valores del manual; las diferencias restantes explicadas | H | R5-01, R5-02 | `tests/conformidad` con xfail reducidos y razón por cada uno | 4 | pendiente |
| R5-05 | Comparación de Jobs emitidos con la estructura del manual (3.1 a 3.5) (T63) | H | R3-05 | Informe con la brecha por Job | 1.5 | pendiente |
| R5-06 | Corregir el diseño manual donde está equivocado (1.1 Impala, 1.2 cachés) como propuesta para el equipo, con evidencia | D | R5-02 | Documento `docs/propuesta-correcciones-diseno-manual.md` | 1.5 | pendiente |

## 11. Fase 6. Fidelidad del emisor de Talend (N1)

| ID | Tarea | Tipo | dep | Criterio | h-ag | Estado |
|---|---|---|---|---|---|---|
| R6-01 | Ida y vuelta en el editor de Studio: una persona abre un Job emitido, lo guarda y se compara el `.item` (T70, `tools/comparar_item.py`) | P+H | | Informe de diferencias; si Studio "repara" algo, se corrige el emisor | 1 d-p + 3 h-ag | pendiente |
| R6-02 | Ajustar `show` y orden de las plantillas calculadas por regla (T71) | H | R6-01 | Las siete plantillas del hito 61 iguales a las guardadas por Studio | 2 | pendiente |
| R6-03 | Plantillas que faltan: `tFilterRow`, `tUniqRow`, `tNormalize`, `tJoin`, `tConvertType`, `tFileList`, `tDBClose`, `tSendMail` (T72) | H | | Cada una ejecutada con datos; procedimiento del hito 61 | 5 | pendiente |
| R6-04 | Posiciones en el lienzo por orden de flujo (T73) | H | | Jobs legibles al abrirlos | 2 | pendiente |
| R6-05 | Etiquetas con nombres significativos y notas para pendientes (T74) | H | | Ningún `tJava` que solo imprima "PENDIENTE" en un Job final | 1.5 | pendiente |
| R6-06 | `item_key` y `.screenshot` de `.properties`: investigar y generar si Studio los exige | R | R6-01 | Evidencia de si faltan o no | 2 | pendiente |
| R6-07 | Validación estática de cada `.item` contra el esquema de Talend (extraer `TalendFile.xsd` de los plugins) dentro de `tools/ci.py` | R+H | R0-06 | Todo Job emitido pasa el esquema | 3 | pendiente |
| R6-08 | Colocación en el repositorio Git del proyecto de Talend (carpetas, versión, convenciones de nombres del banco) | D+H | | Estructura acordada y escrita por `sgm talend --proyecto` | 2 | pendiente |

## 12. Fase 7. Traductor general y generalización (N2)

Esta fase convierte los patrones a medida en un traductor. Se arranca solo si DC-01 elige el migrador general.
Hasta ahora ningún caso del corpus lo ejerce de forma automática.

| ID | Tarea | Tipo | dep | Criterio | h-ag | Estado |
|---|---|---|---|---|---|---|
| R7-01 | Arquitectura del traductor: representación intermedia (tablas, pasos, expresiones) entre el modelo de proceso y el emisor; documento con la decisión sobre usar `sqlglot` para `PROC SQL` o un analizador propio | D | DC-01 | `docs/plan-reescritura/traductor-arquitectura.md` revisado | 4 | pendiente |
| R7-02 | `PROC IMPORT` y `PROC EXPORT` a lectura y escritura de archivos delimitados y Excel, generales | H | R7-01 | `L0` (15 casos) traducidos y pasados en Studio con el arnés | 8 | pendiente |
| R7-03 | Expresiones de SAS a Java: aritmética, comparaciones con faltantes (el faltante es menor que todo número), texto con blancos finales, funciones de los vectores | H | R7-01 | Vectores de `semantica` ejecutados como expresiones del `tMap` | 12 | pendiente |
| R7-04 | `DATA step` simple a `tMap`: `SET`, `KEEP`, `DROP`, `RENAME`, `WHERE`, `IF/THEN/ELSE`, asignaciones, `DO` | H | R7-03 | `L0`, `L4` | 10 | pendiente |
| R7-05 | `PROC SQL` de selección, filtro, `ORDER BY`, `DISTINCT` a `tMap`/`tSortRow`/`tUniqRow` | H | R7-03 | `L1` (15) | 10 | pendiente |
| R7-06 | Uniones (`INNER`, `LEFT`), `IS MISSING`, `IN`, `CASE` y el patrón de validación a `tMap` con lookup | H | R7-05, R1-01 | `L2` (15) y `v01` | 8 | parcial (patrón detectado) |
| R7-07 | Agregados y `GROUP BY/HAVING` a `tAggregateRow` | H | R7-05 | `L3` (12) | 8 | pendiente |
| R7-08 | Macros: expansión estática previa (`%let`, `%macro` con parámetros, `%if`, `%do`) y pendiente con motivo para lo dinámico | H | R7-01 | `L5` (12) | 8 | pendiente |
| R7-09 | `MERGE ... BY` con `IN=`, `FIRST.`, `LAST.`, `RETAIN` con la semántica documentada (no es un `JOIN`) | R+H | R7-04 | `L6` (12) con la regla de máximo de filas por grupo | 12 | pendiente |
| R7-10 | `PROC SORT` con `NODUPKEY` y `NODUP` | H | R6-03 | `L6` y `L8/totales/01` | 4 | pendiente |
| R7-11 | Arquitectura por omisión de `sgm talend` sin YAML: padre e hijos desde regiones y familias (T80) | H | R7-02..R7-10 | Los programas de `tests/fixtures/sas` producen Jobs sin YAML previo, con la lista de lo no traducido | 8 | pendiente |
| R7-12 | Huecos del analizador: `PROC DOWNLOAD` dentro de `RSUBMIT`, `%IF` en macro con parámetro, `infile` con fileref sin comillas, WORK que se leen antes de crearse, `sql_tree` con subconsultas en `FROM` (T82) | R+H | | Cada hueco con prueba; `HUECOS_FRONTEND*.md` vacíos | 8 | pendiente |
| R7-13 | Cierre de brechas del oráculo: `LENGTH`, `COMPBL`, `CONTAINS`, comparaciones con faltantes en `WHERE`, `IS MISSING` sobre expresiones | H | | Los 19 resultados sin verificar de `L8/validaciones` pasan a verificados | 8 | pendiente |
| R7-14 | Casos que faltan: L7 (varias etapas con rechazos y conciliación) y L9 (programa grande con datos simulados) | H | R1 completa | 10 casos L7 y el L9 con esperado por construcción | 10 | pendiente |
| R7-15 | Informe de complejidad y huecos por programa (T81): pasos, bloques, componentes estimados, pendientes por motivo, cobertura de construcciones | H | R7-11 | Markdown y JSON para los 172 programas | 6 | pendiente |
| R7-16 | Segundo y tercer programa: traducir programas de `real/` y `synthetic/`, medir cobertura y cerrar las brechas más frecuentes (iterativo) | H | R7-11, R7-15 | Cobertura medida y creciente; cada brecha cerrada con caso nuevo | 16 | pendiente |
| R7-17 | Validación automática nocturna: todos los casos `traducible` del corpus pasan por el traductor y por Studio con `corpus_studio.py` | H | R0-03, R7-11 | Informe diario; falla si un caso retrocede | 4 | pendiente |
| R7-18 | Informe de cobertura (K12): construcciones del SAS traducidas y verificadas sobre el total del corpus | H | R7-17 | Cifra publicada en el tablero | 3 | pendiente |

## 13. Fase 8. Rendimiento y volumen

El SAS original trocea tablas en bloques de millones de filas (`split2`, `split3`); un Job de Talend con
lookups en memoria puede quedarse sin heap. Sin datos reales, se mide con datos sintéticos de tamaño realista.

| ID | Tarea | Tipo | dep | Criterio | h-ag | Estado |
|---|---|---|---|---|---|---|
| R8-01 | Generador de datos grandes (1 a 10 millones de filas) para el CSV de producto, con proporciones de anomalías realistas | H | | `tools/simular_productos.py --filas` y `--anomalias` | 2 | parcial |
| R8-02 | Medir `job_producto` a volumen: tiempo, memoria, tamaño de lookups, `ROWS_BUFFER_SIZE` del `tMap`, directorio temporal, `-Xmx` del lanzador | R+H | R3-05, R8-01 | Tabla de tiempos y memoria; límite estimado de filas por Job | 6 | pendiente |
| R8-03 | Decidir si hace falta un equivalente del troceado de `split2` (por lotes de filas) según lo medido | D | R8-02 | Decisión escrita; si hace falta, tarea de implementación | 3 | pendiente |
| R8-04 | Presupuesto de rendimiento y prueba de regresión (umbral de tiempo en la validación nocturna) | H | R8-02 | Falla si el tiempo empeora más de un porcentaje fijado | 2 | pendiente |
| R8-05 | Ventana de ejecución estimada para DC-09 con las cifras de R8-02 | H | R8-02 | Documento con la estimación y sus supuestos | 1 | pendiente |

## 14. Fase 9. Operación y producción (N3)

Estas tareas mezclan trabajo de agente (artefactos, scripts, documentos) con trabajo de personas que el agente
no puede hacer (accesos, firmas, datos reales).

| ID | Tarea | Tipo | dep | Criterio | h-ag / d-p | Estado |
|---|---|---|---|---|---|---|
| R9-01 | Decidir el despliegue (DC-05) y registrar la arquitectura de ejecución | P | DC-05 | Documento firmado | 2 d-p | pendiente |
| R9-02 | Empaquetado: Build Job de cada padre con sus hijos, con versión y suma de verificación; guion que lo produce desde un commit | H | R9-01 | Zip reproducible; la suma coincide en dos construcciones | 4 h-ag | pendiente |
| R9-03 | Programación de ejecuciones (DC-09): especificación para el programador elegido y script de arranque con códigos de salida | H+P | R9-01, DC-09 | Especificación revisada; prueba de arranque en QA | 4 h-ag + 2 d-p | pendiente |
| R9-04 | Envoltorio de ejecución (`ejecutar_exogena.ps1` y `.sh`): contexto, parámetros, registro de salida, códigos | H | R9-02 | Pruebas con éxito, fallo de entorno y fallo de hijo | 3 | pendiente |
| R9-05 | Alertas: correos de inicio, fin correcto y error con `tSendMail`, probados contra un SMTP real | H+P | R6-03, R9-01 | Tres correos recibidos en el buzón de pruebas | 4 h-ag + 1 d-p | pendiente |
| R9-06 | Monitoreo: métricas de cada ejecución (duración, filas, totales) a un archivo o tabla de control | H | R2-06 | Una fila por ejecución, consultable | 4 | pendiente |
| R9-07 | Runbook de operación: arranque, reproceso de un producto, fallas frecuentes, qué mirar, a quién escalar, retroceso | H+P | R9-04 | Revisado por quien operará | 4 h-ag + 1 d-p | pendiente |
| R9-08 | Promoción entre entornos DEV, QA y PROD: estrategia de ramas y etiquetas del repositorio Git de Talend, contextos por entorno, aprobaciones | D+P | R6-08 | Procedimiento ejecutado una vez de DEV a QA | 3 h-ag + 2 d-p | pendiente |
| R9-09 | Seguridad: revisión de secretos en artefactos y logs, permisos de rutas UNC, cifrado en tránsito, cumplimiento de `BP-SEC-01` y de las políticas del banco | P | R4-05 | Lista de verificación firmada por Seguridad | 3 d-p | pendiente |
| R9-10 | Plan de aceptación de usuario (UAT): casos, datos, responsables y criterios de aceptación | H+P | R5-04 | Plan aprobado; casos ejecutados en QA con evidencia | 6 h-ag + 5 d-p | pendiente |
| R9-11 | Corrida paralela (DC-10): comparador `tools/comparar_paralelo.py` de totales, conteos y diferencias por producto entre el SAS y Talend con los mismos insumos | H | R2-03 | Comparador probado con corridas simuladas con diferencias plantadas | 8 h-ag | pendiente |
| R9-12 | Ejecución de la corrida paralela: mínimo 3 ciclos reales; diferencias investigadas una por una | P | R9-11, R9-04 | Informe por ciclo con diferencias cero en conteos y dentro de la tolerancia en sumas, o causas explicadas y corregidas | 15 d-p | pendiente |
| R9-13 | Comparación fila a fila en una muestra (hash por fila) entre el archivo de salida del SAS y el de Talend | H+P | R9-12 | Informe con filas distintas y su causa | 6 h-ag + 3 d-p | pendiente |
| R9-14 | Informe de evidencia automático para auditoría: versiones, hashes de artefactos, resultados de pruebas, casos del corpus ejecutados, corrida paralela | H | R9-11 | Documento generado por comando, reproducible | 6 | pendiente |
| R9-15 | Plan de corte y retroceso: congelamiento del SAS, orden de pasos, criterio de no-go, retorno al SAS | P | R9-12 | Plan firmado | 3 d-p | pendiente |
| R9-16 | Capacitación y entrega a operación: sesiones y material para operadores y desarrolladores | H+P | R9-07 | Material entregado; sesión realizada | 6 h-ag + 3 d-p | pendiente |
| R9-17 | Respaldo y recuperación: repositorio Git, contextos, artefactos; prueba de restauración | P | R9-08 | Restauración probada | 2 d-p | pendiente |
| R9-18 | Corte a producción y soporte reforzado (dos semanas) con revisión diaria de ejecuciones | P | R9-15, R9-12 | Firma de cierre | 10 d-p | pendiente |

## 15. Fase 10. Cierre

| ID | Tarea | Tipo | dep | Criterio | h-ag | Estado |
|---|---|---|---|---|---|---|
| R10-01 | Documentación final: README, guías (puesta en marcha, validación, operación), decisiones, riesgos abiertos | H | todas | Un lector nuevo puede reproducir y operar | 6 | pendiente |
| R10-02 | Actualizar la memoria del proyecto y retirar documentos superados (`tareas-agente.md` y los planes antiguos) con una nota de qué los reemplaza | H | R10-01 | `docs/` coherente | 2 | pendiente |
| R10-03 | Retrospectiva: lo que el corpus detectó, errores corregidos, riesgos residuales | H | | Documento de una página | 2 | pendiente |

## 16. Orden de ejecución, carriles y camino crítico

### 16.1 Carriles paralelos (un agente por carril, sin pisar los mismos archivos)

| Carril | Tareas | Territorio |
|---|---|---|
| A. Producto | R1-01 a R1-18 | `jobs_producto.py` y módulos `validacion_*`, `decisiones/*.jobs.yaml` |
| B. Totales y errores | R2-01 a R2-07 | `jobs_totales.py`, `jobs_conciliacion.py`, `conexiones.py` |
| C. Joblets | R3-01 a R3-06 | `talend_item/joblet.py`, `proceso/joblets.py` |
| D. Contextos e Impala | R4-01 a R4-09 | `contextos`, `periodo.py`, plantillas Impala |
| E. Documento | R5-01 a R5-06 | `proceso/diseno_doc.py`, `render_md.py`, `tests/conformidad` |
| F. Emisor | R6-01 a R6-08 | `talend_item/*`, `plantillas/` |
| G. Traductor general | R7-01 a R7-18 | `src/sgm/traductor/` (nuevo), `proceso/`, `frontend/` |
| H. Rendimiento | R8-01 a R8-05 | `tools/`, medición |
| I. Operación | R9-01 a R9-18 | `docs/operacion/`, `tools/` |
| 0. Herramientas | R0-01 a R0-12 | `tools/`, `docs/` |

### 16.2 Camino crítico hacia N1

R0-02, R0-03, R1-01, R1-02, R1-03 a R1-08, R1-13, R1-14, R2-01 a R2-03, R3-01 (o su plan B), R3-03 a R3-05, R5-01 a
R5-04. Todo lo demás de N1 se puede hacer en paralelo. El riesgo mayor del camino es R3-01 (joblets): si no
es viable, R3-04 cambia el diseño de componentes por Jobs hijos y hay que informarlo como desviación.

### 16.3 Orden sugerido por semanas de trabajo de agentes (referencia, no compromiso)

| Etapa | Contenido | Horas de agente |
|---|---|---|
| 1 | Fase 0 completa; R1-01; R1-02; R2-01; R3-01; R6-01 preparado | 30 |
| 2 | Resto de la Fase 1 (validaciones y salidas) | 60 |
| 3 | Fase 2, Fase 4 y Fase 5 | 70 |
| 4 | Fase 3 (joblets o plan B) y Fase 6 | 40 |
| 5 | Cierre de N1: re-ejecución de todo L8, conformidad, informe | 10 |
| 6 | Fase 7 (traductor general), por tramos, con revisión constante contra el corpus | 150 |
| 7 | Fase 8 y preparación de la Fase 9 | 40 |
| 8 | Fase 9: artefactos de agente (R9-02, R9-04, R9-06, R9-11, R9-14) | 40 |

Total de horas de agente: unas 440 (N1 aproximadamente 210; N2 se suma con otras 150; el resto es operación y
rendimiento). Más unos 50 días de persona en la Fase 9, que dominan el calendario de producción.

## 17. Puertas de calidad

| Puerta | Condición (todas deben cumplirse) |
|---|---|
| G0 Línea base | R0-01 a R0-12 hechas; tablero con la fotografía inicial; suite verde |
| G1 Producto | R1 completa; todos los casos de `L8/validaciones` coinciden en Studio con el arnés; invariantes cumplidas |
| G2 Totales | R2 completa; `L8/totales` 04, 05, 06 y 08 coinciden; error provocado activa la rama de error |
| G3 Paridad N1 | R3, R4, R5 y R6 completas; conformidad igual o mayor a 100 de 168; Jobs de hasta 20 componentes; cero secretos en los artefactos; el documento emitido no contradice al código |
| G4 Equivalencia N2 | R7 completa; casos `traducible` del corpus traducidos y pasados de forma automática; dos programas más con cobertura medida; riesgos del oráculo cerrados o aceptados por escrito |
| G5 Operación | R8 y R9-01 a R9-10 hechas; UAT aprobado en QA; seguridad firmada |
| G6 Paralelo | R9-11 a R9-13; diferencia cero en conteos y dentro de tolerancia en sumas durante los ciclos acordados |
| G7 Corte | R9-14 a R9-18; firma de producción |

Una puerta no se cruza con pruebas pendientes ni con diferencias sin explicar.

## 18. Riesgos y mitigaciones

| Riesgo | Efecto | Mitigación |
|---|---|---|
| Sin SAS real ni datos reales, el oráculo y el traductor pueden entender mal la misma regla | Resultados equivocados que pasan las pruebas | Vectores con fuente de la documentación, esperado por construcción independiente, segunda revisión, corrida paralela (G6) |
| Los joblets no se cargan sin reiniciar Studio o no tienen formato verificable | No se cumple el límite de 20 componentes | Plan B R3-04 (Jobs hijos); informar la desviación |
| El filtro del `tMap` no funciona como se modeló | Bloquea la mayoría de las validaciones | R1-01 primero; `tFilterRow` como alternativa |
| Dos sesiones editan el mismo código | Conflictos y trabajo duplicado | Carriles con territorios; R0-01; un commit por tarea; `git status` al empezar |
| La caché local de Studio (Jobs por identificador, poms de Maven) | Resultados que no corresponden al cambio | Nombres nuevos por intento; ciclo de descarga de poms en el validador |
| Rendimiento insuficiente a volumen real | No cabe en la ventana | Fase 8 temprana; troceado según R8-03 |
| Decisiones abiertas (D2, NEQUI, tolerancia) | Rediseño tardío | DC-01 a DC-12 con valor por omisión y fecha de decisión |
| Secretos en artefactos | Incidente de seguridad | R4-05 con prueba automática en CI; revisión R9-09 |
| La corrida paralela revela diferencias de fondo | Retraso del corte | Empezarla con una rebanada pequeña lo antes posible; no esperar al final |
| Dependencia de un Studio local y de `talend-mcp` | Validación no reproducible en otra máquina | R0-07 y R0-12; documentar versión exacta |

## 19. Lo que solo puede hacer una persona

1. Decisiones DC-01 a DC-12.
2. Entregar rutas, tablas, usuarios y secretos reales por entorno.
3. Abrir en el editor gráfico de Studio un Job emitido y guardarlo (R6-01).
4. Ejecutar el SAS original y el Job nuevo con los mismos insumos reales, varios ciclos (R9-12), e investigar las
   diferencias con el equipo de negocio.
5. Revisión de seguridad y firma (R9-09), aprobación de cambios del banco, UAT y corte (R9-10, R9-15, R9-18).
6. Elegir y configurar el programador de ejecuciones y el SMTP reales (R9-03, R9-05).

## 20. Cómo medir el avance

Comando del tablero (R0-09, hecho en el hito 80):

```
uv run python tools/tablero.py            # tabla de la sección 2 y pendientes por motivo
uv run python tools/ci.py                 # ruff, suite, cruces, oráculo y tablero
```

Las medidas que el tablero no cubre se calculan con:

- Componentes por Job: `uv run sgm talend tests/fixtures/sas/client/client_large.sas --out C:/tmp/x` y contar los
  `<node>` de cada `.item`.
- Conformidad: `uv run pytest tests/conformidad -q -n0`.
- Corpus: `uv run python tools/corpus.py oraculo todos --verificar` y `uv run python tools/corpus.py informe`.
- Suite completa: `uv run pytest -q` y `uv run ruff check .`.
- Validación de un caso en Studio: `uv run python tools/corpus_studio.py validar <caso> --jobs <carpeta> --padre <job>
  --proyecto <ruta>`.

Cada hito de `PROGRESS.md` debe copiar estas cifras antes y después de la tarea.
