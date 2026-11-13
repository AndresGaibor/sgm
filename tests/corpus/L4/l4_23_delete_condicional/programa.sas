/* Caso l4_23_delete_condicional: IF K > 2 THEN DELETE; quita la observación sin escribirla y
   detiene la iteración (lestmtsref, p. 77). Entradas: entradas/VALORES_L4_23.csv. Salida:
   WORK.FILTRA_L4_23. Datos ficticios. */

PROC IMPORT DATAFILE='.../entradas/VALORES_L4_23.csv' OUT=WORK.VALORES_L4_23 DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

DATA WORK.FILTRA_L4_23;
  SET WORK.VALORES_L4_23;
  Z = K * 10;
  IF K > 2 THEN DELETE;
RUN;

PROC EXPORT DATA=WORK.FILTRA_L4_23 OUTFILE='.../salida/FILTRA_L4_23.csv' DBMS=CSV REPLACE;
RUN;
