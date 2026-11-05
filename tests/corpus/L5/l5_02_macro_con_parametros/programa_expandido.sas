/* Caso l5_02_macro_con_parametros: una macro con dos parametros filtra un producto con un minimo.
   Entradas: entradas/DATOS_LEALTAD.csv. Salida: WORK.RES_LEALTAD. Datos ficticios. */

PROC IMPORT DATAFILE='.../entradas/DATOS_LEALTAD.csv' OUT=WORK.DATOS_LEALTAD DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;




/* Etiqueta: Filtra saldos del producto desde el minimo */
PROC SQL;
CREATE TABLE WORK.RES_LEALTAD AS
SELECT ID, SALDO
FROM WORK.DATOS_LEALTAD
WHERE SALDO >= 200;
QUIT;

