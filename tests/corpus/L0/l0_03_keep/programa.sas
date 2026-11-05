/* Caso l0_03_keep: conserva solo id, nombre y saldo de cada cliente (sentencia KEEP).
   Entrada: entradas/clientes.csv. Salida: WORK.resumen_clientes.
   Las rutas '...' son marcadores; el ejecutor no las usa. */

PROC IMPORT DATAFILE='.../entradas/clientes.csv' OUT=WORK.clientes DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

DATA WORK.resumen_clientes;
  SET WORK.clientes;
  KEEP id_cliente nombre saldo;
RUN;

PROC EXPORT DATA=WORK.resumen_clientes OUTFILE='.../salida/resumen_clientes.csv' DBMS=CSV REPLACE;
RUN;
