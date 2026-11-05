/* Caso l1_11_orden_posicional: ordena ventas por la segunda columna descendente (monto) y luego
   por la primera (canal), con posiciones en ORDER BY.
   Entrada: entradas/ventas.csv. Salida: WORK.por_monto.
   La ruta '...' es un marcador; el oraculo lee las entradas de la carpeta del caso. */

PROC IMPORT DATAFILE='.../entradas/ventas.csv' OUT=WORK.ventas DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

PROC SQL;
  CREATE TABLE WORK.por_monto AS
  SELECT canal, monto
  FROM WORK.ventas
  ORDER BY 2 DESC, 1;
QUIT;
