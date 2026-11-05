/* Caso l0_07_if_then_else: clasifica el saldo en ALTO, MEDIO o BAJO (IF, THEN y ELSE IF).
   LENGTH fija el largo de nivel antes del primer IF; sin el, SAS cortaria MEDIO a MEDI.
   Entrada: entradas/clientes.csv. Salida: WORK.clientes_nivel.
   Las rutas '...' son marcadores; el ejecutor no las usa. */

PROC IMPORT DATAFILE='.../entradas/clientes.csv' OUT=WORK.clientes DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

DATA WORK.clientes_nivel;
  SET WORK.clientes;
  LENGTH nivel $ 5;
  IF saldo >= 2000 THEN nivel = 'ALTO';
  ELSE IF saldo >= 500 THEN nivel = 'MEDIO';
  ELSE nivel = 'BAJO';
RUN;

PROC EXPORT DATA=WORK.clientes_nivel OUTFILE='.../salida/clientes_nivel.csv' DBMS=CSV REPLACE;
RUN;
