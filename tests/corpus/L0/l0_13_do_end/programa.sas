/* Caso l0_13_do_end: pone en cero los saldos negativos y los marca para revision (bloque DO y END).
   LENGTH fija el largo de revision antes del IF. Entrada: entradas/clientes.csv.
   Salida: WORK.clientes_revisados.
   Las rutas '...' son marcadores; el ejecutor no las usa. */

PROC IMPORT DATAFILE='.../entradas/clientes.csv' OUT=WORK.clientes DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

DATA WORK.clientes_revisados;
  SET WORK.clientes;
  LENGTH revision $ 2;
  IF saldo < 0 THEN DO;
    revision = 'SI';
    saldo = 0;
  END;
  ELSE revision = 'NO';
RUN;

PROC EXPORT DATA=WORK.clientes_revisados OUTFILE='.../salida/clientes_revisados.csv'
  DBMS=CSV REPLACE;
RUN;
