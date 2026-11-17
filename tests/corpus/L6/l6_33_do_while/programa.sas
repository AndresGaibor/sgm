/* Caso l6_33_do_while (PENDIENTE): DO WHILE dentro del DATA step. El bucle repite el cuerpo
   mientras X1 sea menor que 10. Su traducción necesita un bucle en tJavaRow, que no está
   validado en Studio. Entradas: entradas/VALORES_L6_33.csv. Salida: WORK.DUPLICA_L6_33.
   Datos ficticios. */

PROC IMPORT DATAFILE='.../entradas/VALORES_L6_33.csv' OUT=WORK.VALORES_L6_33 DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

DATA WORK.DUPLICA_L6_33;
  SET WORK.VALORES_L6_33;
  DO WHILE (X1 < 10);
    X1 = X1 * 2;
  END;
RUN;

PROC EXPORT DATA=WORK.DUPLICA_L6_33 OUTFILE='.../salida/DUPLICA_L6_33.csv' DBMS=CSV REPLACE;
RUN;
