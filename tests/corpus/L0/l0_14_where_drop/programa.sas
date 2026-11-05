/* Caso l0_14_where_drop: ventas de monto mayor a 300, sin id_cliente ni canal, con recargo = cantidad * 10.
   Entrada: entradas/ventas.csv. Salida: WORK.ventas_grandes.
   Las rutas '...' son marcadores; el ejecutor no las usa. */

PROC IMPORT DATAFILE='.../entradas/ventas.csv' OUT=WORK.ventas DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

DATA WORK.ventas_grandes;
  SET WORK.ventas;
  WHERE monto > 300;
  DROP id_cliente canal;
  recargo = cantidad * 10;
RUN;

PROC EXPORT DATA=WORK.ventas_grandes OUTFILE='.../salida/ventas_grandes.csv' DBMS=CSV REPLACE;
RUN;
