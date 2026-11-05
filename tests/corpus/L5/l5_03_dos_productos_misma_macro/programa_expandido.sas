/* Caso l5_03_dos_productos_misma_macro: la misma macro se llama dos veces con productos distintos.
   Entradas: entradas/DATOS_LEALTAD.csv y entradas/DATOS_AHORRO.csv. Salidas: WORK.RES_LEALTAD y
   WORK.RES_AHORRO. Datos ficticios. */

PROC IMPORT DATAFILE='.../entradas/DATOS_LEALTAD.csv' OUT=WORK.DATOS_LEALTAD DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

PROC IMPORT DATAFILE='.../entradas/DATOS_AHORRO.csv' OUT=WORK.DATOS_AHORRO DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;




/* Etiqueta: Clientes activos del producto */
PROC SQL;
CREATE TABLE WORK.RES_LEALTAD AS
SELECT ID, SALDO
FROM WORK.DATOS_LEALTAD
WHERE ESTADO = 'ACTIVO';
QUIT;


/* Etiqueta: Clientes activos del producto */
PROC SQL;
CREATE TABLE WORK.RES_AHORRO AS
SELECT ID, SALDO
FROM WORK.DATOS_AHORRO
WHERE ESTADO = 'ACTIVO';
QUIT;

