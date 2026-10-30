# Diccionario de datos sintéticos

Todas las filas son inventadas para pruebas. Los CSV usan punto y coma como separador y encabezados en la primera fila.

| Archivo | Filas | Columnas relevantes | Uso |
|---|---:|---|---|
| `data/customers.csv` | 10 | `customer_id`, `customer_name`, `region`, `segment`, `status_code`, `annual_income`, `monthly_debt` | Clientes ficticios activos, inactivos y bloqueados |
| `data/accounts.csv` | 10 | `account_id`, `customer_id`, `product_code`, `balance`, `credit_limit`, `status_code` | Cuentas ficticias y utilización de cupo |
| `data/transactions.csv` | 10 | `transaction_id`, `account_id`, `transaction_date`, `merchant_category`, `amount`, `channel`, `status_code` | Incluye una clave repetida (`TX009`) y una reversada |
| `data/merchant_categories.csv` | 7 | `merchant_category`, `category_description` | Catálogo de categorías para el LEFT JOIN |
| `data/prior_risk_history.csv` | 3 | Esquema del reporte mensual | Histórico previo para probar APPEND |
| `data/stage/customers_active.csv` | 8 | Salida sintética del filtro y cálculo de `01_load_customers.sas` | Permite probar `03_enrich_transactions.sas` sin tener que ejecutar antes el Job 01 |
| `data/stage/accounts_active.csv` | 9 | Salida sintética del filtro, cálculo y deduplicación de `02_load_accounts.sas` | Permite probar `03_enrich_transactions.sas` sin tener que ejecutar antes el Job 02 |

## Códigos

- `status_code` de cliente/cuenta: `1` activo; `0` inactivo; `2` bloqueado.
- `status_code` de transacción: `1` contabilizada; `0` reversada.
- `risk_score`: puntos sintéticos; no representa una política financiera real.

## Variables de prueba

Los `%LET` de cada Job se proponen como variables de contexto Talend cuando el plan puede asociarlos a expresiones:

- `minimum_transaction_amount = 100`
- `minimum_customer_volume = 300`
- `high_spend_threshold = 1000`
- `high_debt_ratio = 0.25`
- `high_utilization_ratio = 0.80`
- `risk_band_threshold = 25`
- `report_month = 202610`

Son umbrales didácticos, no recomendaciones de crédito. El resto de datos de conexión no aplica: el escenario usa archivos locales.
