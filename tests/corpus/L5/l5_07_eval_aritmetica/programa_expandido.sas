/* Caso l5_07_eval_aritmetica: %EVAL calcula un limite con enteros. Entradas:
   entradas/DATOS_LEALTAD.csv. Salida: WORK.RES_LIMITE. Datos ficticios. */

PROC IMPORT DATAFILE='.../entradas/DATOS_LEALTAD.csv' OUT=WORK.DATOS_LEALTAD DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;




/* Etiqueta: Saldos por encima del limite calculado */
PROC SQL;
CREATE TABLE WORK.RES_LIMITE AS
SELECT ID, SALDO
FROM WORK.DATOS_LEALTAD
WHERE SALDO > 250;
QUIT;
