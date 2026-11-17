/* Caso l6_31_do_limite_no_constante (PENDIENTE): DO iterativo cuyo límite final es la columna N,
   no una constante. Con un límite variable el bucle no se desenrolla y necesita tJavaRow
   (lrcon, p. 671). Entradas: entradas/VALORES_L6_31.csv. Salida: WORK.REPITE_L6_31. Datos
   ficticios. */

PROC IMPORT DATAFILE='.../entradas/VALORES_L6_31.csv' OUT=WORK.VALORES_L6_31 DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

DATA WORK.REPITE_L6_31;
  SET WORK.VALORES_L6_31;
  DO I = 1 TO N;
    X1 = X1 + 1;
  END;
RUN;

PROC EXPORT DATA=WORK.REPITE_L6_31 OUTFILE='.../salida/REPITE_L6_31.csv' DBMS=CSV REPLACE;
RUN;
