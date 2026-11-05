/* Caso l3_06_count_distinct: cuántas ventas hay, cuántos clientes distintos compraron y cuántos canales
   distintos aparecen. COUNT(DISTINCT) no cuenta dos veces el mismo valor.
   Entradas: entradas/ventas.csv y entradas/clientes.csv. Salida: WORK.resumen_ventas. La ruta '...'
   es un marcador; el oraculo lee las entradas de la carpeta del caso. */

PROC IMPORT DATAFILE='.../entradas/ventas.csv' OUT=WORK.VENTAS DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

PROC IMPORT DATAFILE='.../entradas/clientes.csv' OUT=WORK.CLIENTES DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

/* Etiqueta: Conteos distintos sobre ventas */
PROC SQL;
  CREATE TABLE WORK.resumen_ventas AS
  SELECT COUNT(*) AS ventas,
         COUNT(DISTINCT id_cliente) AS clientes_distintos,
         COUNT(DISTINCT canal) AS canales
  FROM WORK.ventas;
QUIT;

PROC EXPORT DATA=WORK.resumen_ventas OUTFILE='.../salida/resumen_ventas.csv'
  DBMS=CSV REPLACE;
RUN;
