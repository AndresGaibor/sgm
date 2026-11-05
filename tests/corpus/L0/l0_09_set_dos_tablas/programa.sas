/* Caso l0_09_set_dos_tablas: une las ventas de enero y de febrero en una sola tabla (SET con dos datasets).
   Entradas: entradas/ventas_enero.csv y entradas/ventas_febrero.csv. Salida: WORK.ventas_todas.
   Las rutas '...' son marcadores; el ejecutor no las usa. */

PROC IMPORT DATAFILE='.../entradas/ventas_enero.csv' OUT=WORK.ventas_enero DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

PROC IMPORT DATAFILE='.../entradas/ventas_febrero.csv' OUT=WORK.ventas_febrero DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

DATA WORK.ventas_todas;
  SET WORK.ventas_enero WORK.ventas_febrero;
RUN;

PROC EXPORT DATA=WORK.ventas_todas OUTFILE='.../salida/ventas_todas.csv' DBMS=CSV REPLACE;
RUN;
