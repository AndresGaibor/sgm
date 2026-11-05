/* Caso l6_03_merge_in_flags: MERGE con IN= para saber de que conjunto viene cada llave. Entradas:
   entradas/CLIENTES.csv y entradas/PAGOS.csv (ordenadas por ID). Salida:
   WORK.COBERTURA_PAGOS. Datos ficticios. */

PROC IMPORT DATAFILE='.../entradas/CLIENTES.csv' OUT=WORK.CLIENTES DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

PROC IMPORT DATAFILE='.../entradas/PAGOS.csv' OUT=WORK.PAGOS DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

/* Etiqueta: Marca de que tabla viene cada cliente o pago */
DATA WORK.COBERTURA_PAGOS;
  MERGE WORK.CLIENTES(IN=EN_CLIENTES) WORK.PAGOS(IN=EN_PAGOS);
  BY ID;
  KEEP ID EN_CLIENTES EN_PAGOS;
RUN;

PROC EXPORT DATA=WORK.COBERTURA_PAGOS OUTFILE='.../salida/COBERTURA_PAGOS.csv'
  DBMS=CSV REPLACE;
RUN;
