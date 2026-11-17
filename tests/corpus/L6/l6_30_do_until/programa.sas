/* Caso l6_30_do_until (PENDIENTE): DO UNTIL dentro del DATA step. El cuerpo se ejecuta al menos
   una vez y suma 3 a X1 hasta que X1 llega a 10 (lrcon, p. 675: DO WHILE y DO UNTIL). Su
   traducción necesita un bucle en tJavaRow, sin validar en Studio. Entradas:
   entradas/VALORES_L6_30.csv. Salida: WORK.ACUMULA_L6_30. Datos ficticios. */

PROC IMPORT DATAFILE='.../entradas/VALORES_L6_30.csv' OUT=WORK.VALORES_L6_30 DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

DATA WORK.ACUMULA_L6_30;
  SET WORK.VALORES_L6_30;
  DO UNTIL (X1 >= 10);
    X1 = X1 + 3;
  END;
RUN;

PROC EXPORT DATA=WORK.ACUMULA_L6_30 OUTFILE='.../salida/ACUMULA_L6_30.csv' DBMS=CSV REPLACE;
RUN;
