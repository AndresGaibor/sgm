/* Caso l1_16_data_steps_encadenados: DATA step consecutivos y columnas aditivas. */

PROC IMPORT DATAFILE='.../entradas/ventas.csv' OUT=WORK.ventas DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

DATA WORK.calculada;
  SET WORK.ventas;
  doble = monto * 2;
RUN;

DATA WORK.final;
  SET WORK.calculada;
  total = doble + 1;
  KEEP id total;
  RENAME total=importe_final;
RUN;

PROC EXPORT DATA=WORK.final OUTFILE='.../salida/final.csv' DBMS=CSV REPLACE;
RUN;
