/* Caso l0_05_rename: cambia los nombres de ciudad y saldo (sentencia RENAME).
   Entrada: entradas/clientes.csv. Salida: WORK.clientes_renombrados.
   Las rutas '...' son marcadores; el ejecutor no las usa. */

PROC IMPORT DATAFILE='.../entradas/clientes.csv' OUT=WORK.clientes DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

DATA WORK.clientes_renombrados;
  SET WORK.clientes;
  RENAME ciudad = sede saldo = saldo_actual;
RUN;

PROC EXPORT DATA=WORK.clientes_renombrados OUTFILE='.../salida/clientes_renombrados.csv'
  DBMS=CSV REPLACE;
RUN;
