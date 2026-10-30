# Fases y tareas

Seis fases. Cada tarea tiene un identificador (`A` Andres, `J` Joseph, `B` Byron), un entregable y un criterio de terminado. No hay fechas: se fijan al cerrar la fase 1, cuando se conozca el ritmo real.

Una fase se cierra cuando se cumplen **todos** sus criterios de salida. Las tareas de una persona dentro de una fase se pueden hacer en cualquier orden, salvo las dependencias marcadas.

---

## Fase 0. Cierre de la ronda 2

El agente está ejecutando la ronda 2 (hitos R0 a R10). Cada persona revisa los hitos de su lado cuando el agente los entregue.

| Id | Tarea | Criterio de terminado |
| --- | --- | --- |
| A0.1 | Revisar R0 (diagnóstico), R5 (ubicación en la base), R8 (partición) y R9 (decisiones agrupadas) | Las causas confirmadas coinciden con el desglose; las metas de la tabla de R10 se cumplen o están explicadas |
| A0.2 | Fijar la línea base de métricas en `metrics/baseline.json` con los números de la ronda 2 | Archivo commiteado; el trinquete lo usa desde la fase 1 |
| J0.1 | Revisar R2 (contextos de ambiente), R3 (maquinaria de carga), R4 (PROC SQL) y R7 (tipos desde el código) | Las firmas de la maquinaria de carga bajan a 0; ningún `tJava` sale de PROC SQL |
| J0.2 | Conseguir `activenodelzcode.sas`, `grid_util.sas` y `select_bucket_s3_v2.sas` del Grid | Archivos en `env/externals/`, sin secretos |
| B0.1 | Revisar R1 (configuración de entorno) y R6 (reportes) | Archivos de `env/` validados; reportes según la política |
| B0.2 | Pedir o extraer los `DESCRIBE` de las tablas de Impala usadas por los programas del cliente | Salidas guardadas como texto en `env/raw/` |

**Salida de la fase 0:** metas de la ronda 2 cumplidas o explicadas, línea base fijada, externos y esquemas pedidos.

---

## Fase 1. Herramientas para evolucionar

El objetivo es que cerrar un hueco sea crear un archivo de reglas con su caso de prueba, sin tocar el motor. Ver `04-puntos-de-extension.md` y `03-ciclo-de-huecos.md`. El prompt `07-prompt-f1-herramientas.md` cubre buena parte de esta fase.

| Id | Tarea | Depende de | Criterio de terminado |
| --- | --- | --- | --- |
| A1.1 | Agregar los motivos nuevos (`INCLUDE_EXTERNO`, `COMPONENTE_NO_CATALOGADO`, `INTRINSECO_PARCIAL`) y la prueba que prohíbe operadores sin estado | | Ningún operador del corpus queda sin estado; prueba en verde |
| A1.2 | `rules/routing.yaml` y `sgm gaps list --owner <persona>` | A1.1 | Cada hueco del corpus sale con dueño y con el punto de extensión que lo cierra |
| A1.3 | `sgm rules new <tipo> --from-gap <firma>`: crea el YAML y el caso de prueba prellenados | B1.1 | Probado con un tipo de cada punto de extensión |
| A1.4 | `sgm explain <archivo>:<línea>`: muestra el camino de esa línea hasta su componente, o el hueco que la tiene | | Funciona sobre cualquier línea de los fixtures del cliente |
| A1.5 | Trinquete: `sgm metrics --check` falla si una métrica empeora frente a `metrics/baseline.json` | A0.2 | Integrado a la suite de pruebas |
| J1.1 | `rules/sas/procs/*.yaml`: bajada declarativa de PROCs simples a la IR (ver `04`) | | `proc sort`, `proc append`, `proc means` y `proc freq` migrados del código a YAML sin cambiar la salida |
| J1.2 | `rules/sas/functions/*.yaml`: tabla de funciones SAS con SQL de Impala y expresión Java | | Las funciones que hoy traduce el código, migradas a YAML sin cambiar la salida |
| J1.3 | `rules/sas/informats.yaml`: informats y formatos a tipos | | La inferencia de R7 lee este archivo |
| J1.4 | `sgm intake <archivo-o-carpeta>`: copia a `corpus/inbox/`, redacta secretos, compila y registra huecos | | Un archivo nuevo entra y sale con su reporte de huecos en un solo comando |
| J1.5 | `sgm case new --from-gap <firma>`: extrae el fragmento SAS mínimo del hueco, anonimizado, a `tests/cases/` | J1.4 | Probado con 3 huecos reales |
| B1.1 | JSON Schema de cada punto de extensión en `schemas/rules/` y `sgm rules validate` | | Todo YAML y JSON de `rules/` y `env/` valida; un archivo mal formado da un error con ruta y línea |
| B1.2 | `rules/mapping/*.yaml`: revisar que todas las reglas de componentes estén en YAML, con alternativas | | Ningún mapeo a componente queda fijo en Python |
| B1.3 | `sgm env import-describe <archivo>`: convierte la salida de `DESCRIBE` de Impala a `env/schemas/*.json` | | Probado con una salida real de B0.2 |
| B1.4 | Convertir `env/schemas.json` en carpeta `env/schemas/` (un archivo por esquema de base) | | La pasada 9 lee la carpeta |

**Salida de la fase 1:** un hueco de cada motivo se cerró siguiendo `03-ciclo-de-huecos.md` solo con archivos de reglas y su caso, sin tocar `src/`.

---

## Fase 2. Programas del cliente al máximo

Corpus: los programas reales de Bancolombia disponibles (hoy `client_poc.sas` y `client_large.sas`, más los que se reciban).

| Id | Tarea | Criterio de terminado |
| --- | --- | --- |
| A2.1 | Ajustar las pasadas 5 a 8 con los programas del cliente hasta cumplir las metas de agrupación | Ver metas abajo |
| A2.2 | Revisar a mano la guía de cada programa con Byron: se lee como un proceso de pocas etapas | Acta corta en `docs/revisiones/` por programa |
| J2.1 | Cerrar todos los huecos de motivo SAS de los programas del cliente | 0 huecos de `PARSE_ERROR`, `SENTENCIA_NO_SOPORTADA`, `PROC_NO_SOPORTADO`, `INTRINSECO_PARCIAL` |
| J2.2 | Reducir `MACRO_DINAMICA` al mínimo: lo que dependa de datos queda como decisión con opciones claras | Cada `MACRO_DINAMICA` restante tiene una decisión asociada |
| J2.3 | Recibir los programas nuevos del cliente por `sgm intake` | Todos pasan por el ciclo de huecos |
| B2.1 | Cargar los esquemas reales en `env/schemas/` | 0 `TIPO_DESCONOCIDO` en columnas de tablas de la base |
| B2.2 | Revisar los valores por defecto de las decisiones por firma única con Andres | Cada firma única tiene un valor por defecto revisado y justificado |
| B2.3 | Pulir la guía de salida: por job, entradas, salidas, componentes, evidencia, pendientes | Revisada con A2.2 |

Metas de la fase 2 para cada programa del cliente (se ajustan con los datos de la fase 0):

| Métrica | Meta |
| --- | --- |
| `tJava` | 10 % o menos de los componentes |
| `tJava` con origen PROC SQL | 0 |
| Componentes | menos que los pasos SAS |
| Huecos de motivo SAS | 0 |
| `TIPO_DESCONOCIDO` en tablas de la base | 0 |
| Decisiones sin valor por defecto revisado | 0 |

**Salida de la fase 2:** las metas se cumplen en todos los programas del cliente recibidos.

---

## Fase 3. Listo para cualquier archivo

| Id | Tarea | Criterio de terminado |
| --- | --- | --- |
| A3.1 | Pruebas de robustez: archivos truncados, vacíos, binarios, gigantes, macros anidadas, `%include` circular | 0 excepciones; cada caso sale con hueco o estado |
| A3.2 | Presupuesto de rendimiento: medir tiempo y memoria por archivo y por corpus; fijar límites | Límites en `06-calidad.md` y prueba que los vigila |
| A3.3 | Caché e incrementalidad: cambiar una regla recompila solo los archivos con esa firma | Medido sobre el corpus |
| J3.1 | Codificaciones: UTF-8 con y sin BOM, cp1252, latin-1, finales de línea CRLF y LF | Fixtures de cada caso pasan |
| J3.2 | Ampliar el corpus con programas SAS públicos de licencia permisiva y medir cobertura de PROCs y funciones | Lista de PROCs y funciones por frecuencia en `docs/cobertura.md` |
| J3.3 | Cubrir con YAML los PROCs y funciones más frecuentes del corpus ampliado | Los 20 PROCs y las 50 funciones más frecuentes tienen regla o hueco con decisión |
| J3.4 | Orquestación SAS Grid: `sasgsub`, `sas -sysin`, scripts shell y Control-M como jobs padre con `tRunJob` | Fixtures de Grid producen la orquestación |
| B3.1 | Motores adicionales en `env/engines.json` (Oracle, Teradata, DB2, SQL Server, Postgres) con su dialecto SQL | Un fixture por motor compila con SQL del dialecto correcto |
| B3.2 | Revisar el catálogo de Talend contra la versión de Studio que usará el cliente | Componentes fuera de la versión marcados en el catálogo |

**Salida de la fase 3:** el corpus completo, incluidos los archivos hostiles, compila sin excepciones, con 100 % de líneas cubiertas por componente, `not_migrated` o hueco, y el trinquete en verde.

---

## Fase 4. Equivalencia de datos

Requiere acceso a un ambiente con SAS y Talend, y datos de prueba.

| Id | Tarea | Criterio de terminado |
| --- | --- | --- |
| A4.1 | Diseñar la comparación: conteo de filas, suma por columna numérica y huella por fila sobre las claves | Documento en `docs/equivalencia.md` |
| A4.2 | `sgm verify`: compara salidas de SAS y de Talend exportadas a archivo | Probado con un programa del cliente |
| J4.1 | Preparar datos de prueba representativos por programa, sin datos reales de clientes | Juegos de datos en un lugar acordado fuera del repositorio |
| B4.1 | Construir a mano en Studio el Job de un programa siguiendo la guía y medir el tiempo | Tiempo y problemas anotados; ajustes a la guía |

**Salida de la fase 4:** un programa del cliente validado con datos: mismos conteos, sumas y huellas que SAS.

---

## Fase 5. Studio y portal

Se reactiva el MCP. Solo empieza con la fase 3 cerrada.

| Id | Tarea | Criterio de terminado |
| --- | --- | --- |
| B5.1 | Traer `talend-mcp` como subtree y un emisor que convierte el plan en llamadas al MCP | Un programa escrito en Studio como Job y abierto sin errores de estructura |
| B5.2 | API y web: proyectos, guía, decisiones por firma, inventario de huecos, métricas | Un usuario resuelve una decisión en la web y se aplica a todos los archivos con esa firma |
| A5.1 | Contrato entre el plan y el emisor de Studio | Agregado a `05-contratos.md` |
| J5.1 | Pruebas de extremo a extremo con los fixtures de Grid y del cliente | En verde |
