/* Caso l6_40_lag_dentro_de_if (PENDIENTE): LAG dentro de IF. La cola de LAG solo avanza cuando
   la función se ejecuta (lefunctionsref, p. 1164): la fila con X = -1 no cumple la condición y no
   entra en la cola, así que la tercera fila recibe 2 y no -1. Entradas:
   entradas/VALORES_L6_40.csv. Salida: WORK.LAG_L6_40. Datos ficticios. */

PROC IMPORT DATAFILE='.../entradas/VALORES_L6_40.csv' OUT=WORK.VALORES_L6_40 DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

DATA WORK.LAG_L6_40;
  SET WORK.VALORES_L6_40;
  IF X > 0 THEN PREV = LAG(X);
RUN;

PROC EXPORT DATA=WORK.LAG_L6_40 OUTFILE='.../salida/LAG_L6_40.csv' DBMS=CSV REPLACE;
RUN;
