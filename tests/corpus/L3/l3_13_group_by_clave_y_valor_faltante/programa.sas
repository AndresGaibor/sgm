/* Caso l3_13_group_by_clave_y_valor_faltante: los faltantes de la clave forman un solo grupo;
   COUNT(col) cuenta no faltantes; AVG promedia solo los presentes. Entradas: entradas/ventas.csv.
   Salida: WORK.por_region. La ruta '...' es un marcador; el oraculo lee las entradas de la carpeta del caso. */

PROC IMPORT DATAFILE='.../entradas/ventas.csv' OUT=WORK.VENTAS DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

PROC SQL;
  CREATE TABLE WORK.por_region AS
  SELECT region, COUNT(*) AS n, COUNT(monto) AS n_monto, SUM(monto) AS total,
         AVG(monto) AS prom, MIN(monto) AS minimo, MAX(monto) AS maximo
  FROM WORK.VENTAS
  GROUP BY region;
QUIT;

PROC EXPORT DATA=WORK.por_region OUTFILE='.../salida/por_region.csv'
  DBMS=CSV REPLACE;
RUN;
