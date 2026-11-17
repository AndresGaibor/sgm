/* Caso l6_25_set_dos_datasets_orden: SET de dos datasets concatena en el orden de la lista:
   todas las observaciones de A y luego las de B (lestmtsref, SET, p. 343; lrcon, p. 579).
   Entradas: entradas/A_ORDEN.csv y entradas/B_ORDEN.csv. Salida: WORK.TODO_ORDEN. Datos ficticios. */

PROC IMPORT DATAFILE='.../entradas/A_ORDEN.csv' OUT=WORK.A_ORDEN DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

PROC IMPORT DATAFILE='.../entradas/B_ORDEN.csv' OUT=WORK.B_ORDEN DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

DATA WORK.TODO_ORDEN;
  SET WORK.A_ORDEN WORK.B_ORDEN;
RUN;

PROC EXPORT DATA=WORK.TODO_ORDEN OUTFILE='.../salida/TODO_ORDEN.csv' DBMS=CSV REPLACE;
RUN;
