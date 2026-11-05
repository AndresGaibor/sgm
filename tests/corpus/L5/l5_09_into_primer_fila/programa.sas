/* Caso l5_09_into_primer_fila: SELECT ... INTO :ANIO toma el anio de la primera fila de
   VALIDACION_FECHA y lo usa en el siguiente PROC SQL. Entradas: entradas/DATOS_LEALTAD.csv y
   entradas/VALIDACION_FECHA.csv. Salida: WORK.RES_ANIO. Datos ficticios. */

PROC IMPORT DATAFILE='.../entradas/DATOS_LEALTAD.csv' OUT=WORK.DATOS_LEALTAD DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

PROC IMPORT DATAFILE='.../entradas/VALIDACION_FECHA.csv' OUT=WORK.VALIDACION_FECHA
  DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

/* Etiqueta: Toma el anio de validacion */
PROC SQL;
SELECT AÑO INTO :ANIO
FROM WORK.VALIDACION_FECHA;
QUIT;

/* Etiqueta: Saldos con el anio de corte */
PROC SQL;
CREATE TABLE WORK.RES_ANIO AS
SELECT ID, SALDO, &ANIO AS ANIO_CORTE
FROM WORK.DATOS_LEALTAD
WHERE SALDO >= 100;
QUIT;
