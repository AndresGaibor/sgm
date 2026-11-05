/* Caso l5_03_dos_productos_misma_macro: la misma macro se llama dos veces con productos distintos.
   Entradas: entradas/DATOS_LEALTAD.csv y entradas/DATOS_AHORRO.csv. Salidas: WORK.RES_LEALTAD y
   WORK.RES_AHORRO. Datos ficticios. */

PROC IMPORT DATAFILE='.../entradas/DATOS_LEALTAD.csv' OUT=WORK.DATOS_LEALTAD DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

PROC IMPORT DATAFILE='.../entradas/DATOS_AHORRO.csv' OUT=WORK.DATOS_AHORRO DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

%macro activos(producto);
/* Etiqueta: Clientes activos del producto */
PROC SQL;
CREATE TABLE WORK.RES_&producto. AS
SELECT ID, SALDO
FROM WORK.DATOS_&producto.
WHERE ESTADO = 'ACTIVO';
QUIT;
%mend activos;

%activos(LEALTAD);
%activos(AHORRO);
