/* Caso l4_21_select_when_con_otherwise: SELECT (X) con WHEN de lista y OTHERWISE. Lo que
   no coincide cae en OTHERWISE (lestmtsref, p. 340). Entradas: entradas/VALORES_L4_21.csv.
   Salida: WORK.SELECT_L4_21. Datos ficticios. */

PROC IMPORT DATAFILE='.../entradas/VALORES_L4_21.csv' OUT=WORK.VALORES_L4_21 DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

DATA WORK.SELECT_L4_21;
  SET WORK.VALORES_L4_21;
  SELECT (X);
    WHEN (1, 2) Y = 'a';
    WHEN (3) Y = 'b';
    OTHERWISE Y = 'c';
  END;
RUN;

PROC EXPORT DATA=WORK.SELECT_L4_21 OUTFILE='.../salida/SELECT_L4_21.csv' DBMS=CSV REPLACE;
RUN;
