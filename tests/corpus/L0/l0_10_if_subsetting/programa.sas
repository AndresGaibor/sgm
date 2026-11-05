/* Caso l0_10_if_subsetting: conserva las ventas por web o con monto mayor a 700 (IF de subconjunto).
   Entrada: entradas/ventas.csv. Salida: WORK.ventas_web_o_grandes.
   Las rutas '...' son marcadores; el ejecutor no las usa. */

PROC IMPORT DATAFILE='.../entradas/ventas.csv' OUT=WORK.ventas DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

DATA WORK.ventas_web_o_grandes;
  SET WORK.ventas;
  IF canal = 'WEB' OR monto > 700;
RUN;

PROC EXPORT DATA=WORK.ventas_web_o_grandes OUTFILE='.../salida/ventas_web_o_grandes.csv'
  DBMS=CSV REPLACE;
RUN;
