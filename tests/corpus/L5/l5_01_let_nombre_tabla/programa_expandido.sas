/* Caso l5_01_let_nombre_tabla: una macrovariable da el producto y arma el nombre del origen y
   de la tabla de salida. Entradas: entradas/DATOS_LEALTAD.csv. Salida: WORK.RES_LEALTAD.
   Datos ficticios. El oraculo usa programa_expandido.sas. */

PROC IMPORT DATAFILE='.../entradas/DATOS_LEALTAD.csv' OUT=WORK.DATOS_LEALTAD DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;



/* Etiqueta: Saldos altos del producto */
PROC SQL;
CREATE TABLE WORK.RES_LEALTAD AS
SELECT ID, SALDO
FROM WORK.DATOS_LEALTAD
WHERE SALDO >= 100;
QUIT;

PROC EXPORT DATA=WORK.RES_LEALTAD OUTFILE="salida/RES_LEALTAD.csv" DBMS=CSV REPLACE;
RUN;
