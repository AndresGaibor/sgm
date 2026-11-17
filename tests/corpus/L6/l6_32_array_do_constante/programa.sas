/* Caso l6_32_array_do_constante: ARRAY de tres elementos y un DO con límites constantes que
   duplica cada columna. Con límites constantes el DO se desenrolla en el DATA step. Al salir,
   I vale 4 (lestmtsref, DO Statement: Iterative, p. 84; lrcon no tiene la entrada de DO
   iterativo). Entradas: entradas/VALORES_L6_32.csv. Salida: WORK.DOBLE_L6_32. Datos ficticios. */

PROC IMPORT DATAFILE='.../entradas/VALORES_L6_32.csv' OUT=WORK.VALORES_L6_32 DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

DATA WORK.DOBLE_L6_32;
  SET WORK.VALORES_L6_32;
  ARRAY A{3} X1 X2 X3;
  DO I = 1 TO 3;
    A{I} = A{I} * 2;
  END;
RUN;

PROC EXPORT DATA=WORK.DOBLE_L6_32 OUTFILE='.../salida/DOBLE_L6_32.csv' DBMS=CSV REPLACE;
RUN;
