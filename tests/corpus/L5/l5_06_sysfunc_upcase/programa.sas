/* Caso l5_06_sysfunc_upcase: %SYSFUNC con UPCASE pone en mayusculas una macrovariable.
   Entradas: entradas/DATOS_LEALTAD.csv. Salida: WORK.RES_LEALTAD. Datos ficticios. */

PROC IMPORT DATAFILE='.../entradas/DATOS_LEALTAD.csv' OUT=WORK.DATOS_LEALTAD DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

%let PRODUCTO_MIN=lealtad;
%let PRODUCTO=%sysfunc(upcase(&PRODUCTO_MIN));

/* Etiqueta: Clientes activos del producto en mayusculas */
PROC SQL;
CREATE TABLE WORK.RES_&PRODUCTO. AS
SELECT ID
FROM WORK.DATOS_&PRODUCTO.
WHERE ESTADO = 'ACTIVO';
QUIT;
