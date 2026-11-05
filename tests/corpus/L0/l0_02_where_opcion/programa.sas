/* Caso l0_02_where_opcion: lee solo los clientes activos con la opcion WHERE= de SET.
   Entrada: entradas/clientes.csv. Salida: WORK.activos.
   Las rutas '...' son marcadores; el ejecutor no las usa. */

PROC IMPORT DATAFILE='.../entradas/clientes.csv' OUT=WORK.clientes DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

DATA WORK.activos;
  SET WORK.clientes(WHERE=(estado = 'ACTIVO'));
RUN;

PROC EXPORT DATA=WORK.activos OUTFILE='.../salida/activos.csv' DBMS=CSV REPLACE;
RUN;
