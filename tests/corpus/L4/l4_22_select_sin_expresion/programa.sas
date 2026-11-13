/* Caso l4_22_select_sin_expresion: SELECT; sin select-expression. Cada WHEN es una condición
   booleana y gana la primera verdadera (lestmtsref, p. 340). Entradas:
   entradas/VALORES_L4_22.csv. Salida: WORK.CLASIFICA_L4_22. Datos ficticios. */

PROC IMPORT DATAFILE='.../entradas/VALORES_L4_22.csv' OUT=WORK.VALORES_L4_22 DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

DATA WORK.CLASIFICA_L4_22;
  SET WORK.VALORES_L4_22;
  SELECT;
    WHEN (X > 2) Y = 'alto';
    WHEN (X <= 2) Y = 'bajo';
    OTHERWISE Y = 'nulo';
  END;
RUN;

PROC EXPORT DATA=WORK.CLASIFICA_L4_22 OUTFILE='.../salida/CLASIFICA_L4_22.csv' DBMS=CSV REPLACE;
RUN;
