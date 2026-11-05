/* Caso l5_11_macro_llama_macro: una macro llama a otra con su parametro; la segunda lee la tabla
   que creo la primera. Entradas: entradas/DATOS_LEALTAD.csv. Salidas: WORK.BASE_LEALTAD y
   WORK.DEP_LEALTAD. Datos ficticios. */

PROC IMPORT DATAFILE='.../entradas/DATOS_LEALTAD.csv' OUT=WORK.DATOS_LEALTAD DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

%macro base(producto);
PROC SQL;
CREATE TABLE WORK.BASE_&producto. AS
SELECT ID, SALDO
FROM WORK.DATOS_&producto.;
QUIT;
%mend base;

%macro depurado(producto);
%base(&producto);
/* Etiqueta: Saldos desde 100 de la base */
PROC SQL;
CREATE TABLE WORK.DEP_&producto. AS
SELECT ID
FROM WORK.BASE_&producto.
WHERE SALDO >= 100;
QUIT;
%mend depurado;

%depurado(LEALTAD);
