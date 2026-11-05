-- Tablas de Impala simuladas para el caso 07. Se cargan en un Impala de contenedor
-- con los CSV de esta carpeta (cabecera, separador ;). Nombres como en el original.
CREATE TABLE resultados_vspc_clientes.master_customer_data (
  YEAR INT,
  MONTH INT,
  ingestion_day STRING,
  cod_tipo_doc STRING,
  num_doc STRING,
  nombre_cli STRING
) STORED AS PARQUET;

CREATE TABLE proceso_vspc_finanzas.mcdq (
  cod_tipo_doc STRING,
  num_doc STRING,
  nombre_cli STRING,
  ingestion_day STRING
) STORED AS PARQUET;
