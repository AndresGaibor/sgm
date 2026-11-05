/* Caso l5_04_if_then_else_macro: una macrovariable elige la rama con %IF, %THEN y %ELSE.
   Entradas: entradas/DATOS_LEALTAD.csv y entradas/DATOS_AHORRO.csv. Salida: WORK.RES_TIPO.
   Datos ficticios. */

PROC IMPORT DATAFILE='.../entradas/DATOS_LEALTAD.csv' OUT=WORK.DATOS_LEALTAD DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

PROC IMPORT DATAFILE='.../entradas/DATOS_AHORRO.csv' OUT=WORK.DATOS_AHORRO DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;



/* Etiqueta: Saldos bajos del tipo elegido */

PROC SQL;
CREATE TABLE WORK.RES_TIPO AS
SELECT ID, SALDO
FROM WORK.DATOS_AHORRO
WHERE SALDO < 500;
QUIT;

