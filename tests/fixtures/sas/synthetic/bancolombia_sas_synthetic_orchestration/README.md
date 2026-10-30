# Demo sintético SAS: cartera bancaria y orquestación

Proyecto ficticio para probar la carga ZIP del portal, el análisis SAS, el grafo de dependencias, la propuesta Talend y la creación por lote con MCP. No contiene información real ni credenciales.

## Qué incluye

- 8 programas `.sas`: siete Jobs de procesamiento y un Job padre que los orquesta en orden.
- `BatchJobs/submit_daily_grid.sh`: ejemplo opcional de envío a SAS Grid para que el portal analice opciones y secuencia. **No lo ejecutes en Windows local**; requiere `sasgsub` en un entorno SAS Grid.
- Datos CSV sintéticos y diccionario de columnas.
- Semillas de las dos salidas intermedias (`customers_active.csv` y `accounts_active.csv`) para probar Jobs dependientes de forma individual. Los Jobs 01 y 02 vuelven a generar esos archivos al ejecutarse.
- Resultados y conteos esperados para revisar la prueba.

## Flujo de los Jobs

1. `01_load_customers.sas`: carga 10 clientes, filtra los activos y calcula ingreso neto anual.
2. `02_load_accounts.sas`: carga 10 cuentas, filtra cuentas activas, calcula utilización y quita claves duplicadas.
3. `03_enrich_transactions.sas`: elimina la transacción repetida, filtra estado y monto, hace joins INNER y LEFT con cuentas, clientes y categorías.
4. `04_customer_metrics.sas`: agrupa por cliente, suma y cuenta transacciones, y aplica `HAVING`.
5. `05_credit_risk_scoring.sas`: une métricas con clientes y cuentas, calcula razones y asigna una banda de riesgo con reglas condicionales.
6. `06_monthly_report.sas`: ordena el reporte, añade el mes de proceso y exporta el resultado del mes.
7. `07_append_risk_history.sas`: importa un histórico pequeño, anexa el mes actual, ordena y exporta el histórico actualizado.
8. `run_daily_portfolio.sas`: Job padre; usa una macro de despacho con `%include` para invocar los siete Jobs de procesamiento secuencialmente.

Los archivos intermedios se escriben en `data/stage/`. El resultado final se escribe en `output/`. Ejecuta SAS desde la raíz del proyecto para que las rutas relativas funcionen. Los Jobs no conectan con bases de datos ni servicios externos.

## Cómo probarlo en el portal

1. Sube `bancolombia_sas_synthetic_orchestration.zip` como un proyecto nuevo.
2. Revisa inventario, dependencias, orden, guías y propuestas de Talend.
3. Comprueba que las condiciones del filtro provengan de las sentencias SAS, que el padre resuelva los Jobs hijos y que aparezcan variables de contexto para umbrales y mes de proceso.
4. Implementa el lote solo cuando quieras escribir los Jobs en Talend Studio. El análisis del ZIP no ejecuta SAS ni crea Jobs por sí mismo.
5. En Talend, revisa y compila antes de ejecutar. Los archivos de datos y las salidas intermedias de prueba vienen en el ZIP; esto no reemplaza la configuración de esquemas y del mapper que cada Job necesita en Talend.

## Resultado esperado

Consulta `expected/expected-results.md` para los conteos y agregados que deben salir de los datos ficticios. Se espera que el filtro de volumen descarte el cliente 1001, la deduplicación conserve una sola fila de `TX009`, y el histórico final tenga 8 filas.

## Seguridad y límites

Todo el dataset es sintético. Los códigos de contexto tienen valores seguros de prueba. Los `.sh` y `.sas` se importan como texto: el portal no debe ejecutarlos durante la carga. El archivo `.sh` documenta una llamada SAS Grid y solo sirve para analizar ese patrón.
