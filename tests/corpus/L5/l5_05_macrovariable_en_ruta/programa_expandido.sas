/* Caso l5_05_macrovariable_en_ruta: la ruta de salida arma su nombre con producto, anio, mes y
   dia. Las comillas dobles permiten resolver las macrovariables. Entradas:
   entradas/DATOS_LEALTAD.csv. Salida: WORK.RES_LEALTAD. Datos ficticios. */

PROC IMPORT DATAFILE='.../entradas/DATOS_LEALTAD.csv' OUT=WORK.DATOS_LEALTAD DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;






/* Etiqueta: Clientes activos del producto */
PROC SQL;
CREATE TABLE WORK.RES_LEALTAD AS
SELECT ID, SALDO
FROM WORK.DATOS_LEALTAD
WHERE ESTADO = 'ACTIVO';
QUIT;

PROC EXPORT DATA=WORK.RES_LEALTAD
  OUTFILE="salida/LEALTAD_20261104.csv"
  DBMS=CSV REPLACE;
RUN;
