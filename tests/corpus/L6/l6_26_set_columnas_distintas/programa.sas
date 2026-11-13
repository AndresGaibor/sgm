/* Caso l6_26_set_columnas_distintas: SET con columnas distintas. Las variables del resultado son las de
   todos los datasets; las filas de cada uno quedan faltantes en las variables que no tiene (lrcon, p. 579).
   Entradas: entradas/A_COLS.csv y entradas/B_COLS.csv. Salida: WORK.TODO_COLS. Datos ficticios. */

PROC IMPORT DATAFILE='.../entradas/A_COLS.csv' OUT=WORK.A_COLS DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

PROC IMPORT DATAFILE='.../entradas/B_COLS.csv' OUT=WORK.B_COLS DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

DATA WORK.TODO_COLS;
  SET WORK.A_COLS WORK.B_COLS;
RUN;

PROC EXPORT DATA=WORK.TODO_COLS OUTFILE='.../salida/TODO_COLS.csv' DBMS=CSV REPLACE;
RUN;
