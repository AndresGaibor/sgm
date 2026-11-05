/* Caso l6_01_merge_by_uno_a_uno: MERGE con BY y llaves unicas en ambos lados. Entradas:
   entradas/CLIENTES.csv y entradas/SALDOS.csv (ordenadas por ID). Salida:
   WORK.CLIENTES_CON_SALDO. Datos ficticios. Esperado: capa B (referencia_datastep). */

PROC IMPORT DATAFILE='.../entradas/CLIENTES.csv' OUT=WORK.CLIENTES DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

PROC IMPORT DATAFILE='.../entradas/SALDOS.csv' OUT=WORK.SALDOS DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

/* Etiqueta: Une cliente y saldo por ID */
DATA WORK.CLIENTES_CON_SALDO;
  MERGE WORK.CLIENTES WORK.SALDOS;
  BY ID;
RUN;

PROC EXPORT DATA=WORK.CLIENTES_CON_SALDO OUTFILE='.../salida/CLIENTES_CON_SALDO.csv'
  DBMS=CSV REPLACE;
RUN;
