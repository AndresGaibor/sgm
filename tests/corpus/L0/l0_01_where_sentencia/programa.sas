/* Caso l0_01_where_sentencia: deja solo los clientes con saldo de al menos 1000 (sentencia WHERE).
   Entrada: entradas/clientes.csv. Salida: WORK.saldo_alto.
   Las rutas '...' son marcadores; el ejecutor no las usa. */

PROC IMPORT DATAFILE='.../entradas/clientes.csv' OUT=WORK.clientes DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

DATA WORK.saldo_alto;
  SET WORK.clientes;
  WHERE saldo >= 1000;
RUN;

PROC EXPORT DATA=WORK.saldo_alto OUTFILE='.../salida/saldo_alto.csv' DBMS=CSV REPLACE;
RUN;
