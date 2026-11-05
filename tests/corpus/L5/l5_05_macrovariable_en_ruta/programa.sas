/* Caso l5_05_macrovariable_en_ruta: la ruta de salida arma su nombre con producto, anio, mes y
   dia. Las comillas dobles permiten resolver las macrovariables. Entradas:
   entradas/DATOS_LEALTAD.csv. Salida: WORK.RES_LEALTAD. Datos ficticios. */

PROC IMPORT DATAFILE='.../entradas/DATOS_LEALTAD.csv' OUT=WORK.DATOS_LEALTAD DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

%let PRODUCTO=LEALTAD;
%let ANIO=2026;
%let MES=11;
%let DIA=04;

/* Etiqueta: Clientes activos del producto */
PROC SQL;
CREATE TABLE WORK.RES_&PRODUCTO. AS
SELECT ID, SALDO
FROM WORK.DATOS_&PRODUCTO.
WHERE ESTADO = 'ACTIVO';
QUIT;

PROC EXPORT DATA=WORK.RES_&PRODUCTO.
  OUTFILE="salida/&PRODUCTO._&ANIO&MES&DIA..csv"
  DBMS=CSV REPLACE;
RUN;
