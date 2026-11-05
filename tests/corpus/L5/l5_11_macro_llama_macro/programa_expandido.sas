/* Caso l5_11_macro_llama_macro: una macro llama a otra con su parametro; la segunda lee la tabla
   que creo la primera. Entradas: entradas/DATOS_LEALTAD.csv. Salidas: WORK.BASE_LEALTAD y
   WORK.DEP_LEALTAD. Datos ficticios. */

PROC IMPORT DATAFILE='.../entradas/DATOS_LEALTAD.csv' OUT=WORK.DATOS_LEALTAD DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;







PROC SQL;
CREATE TABLE WORK.BASE_LEALTAD AS
SELECT ID, SALDO
FROM WORK.DATOS_LEALTAD;
QUIT;

/* Etiqueta: Saldos desde 100 de la base */
PROC SQL;
CREATE TABLE WORK.DEP_LEALTAD AS
SELECT ID
FROM WORK.BASE_LEALTAD
WHERE SALDO >= 100;
QUIT;

