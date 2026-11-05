/* Caso l3_02_sum_min_max_avg_faltantes: SUM, MIN, MAX, AVG y COUNT sobre montos con faltantes. Los
   agregados ignoran los faltantes; COUNT(monto) no los cuenta. Entradas: entradas/ventas.csv. Salida:
   WORK.resumen_monto. La ruta '...' es un marcador; el oraculo lee las entradas de la carpeta del
   caso. */

PROC IMPORT DATAFILE='.../entradas/ventas.csv' OUT=WORK.VENTAS DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

/* Etiqueta: Resumen de montos con faltantes */
PROC SQL;
  CREATE TABLE WORK.resumen_monto AS
  SELECT SUM(monto) AS suma,
         MIN(monto) AS minimo,
         MAX(monto) AS maximo,
         AVG(monto) AS promedio,
         COUNT(monto) AS n
  FROM WORK.ventas;
QUIT;

PROC EXPORT DATA=WORK.resumen_monto OUTFILE='.../salida/resumen_monto.csv'
  DBMS=CSV REPLACE;
RUN;
