/* Caso l5_02_macro_con_parametros: una macro con dos parametros filtra un producto con un minimo.
   Entradas: entradas/DATOS_LEALTAD.csv. Salida: WORK.RES_LEALTAD. Datos ficticios. */

PROC IMPORT DATAFILE='.../entradas/DATOS_LEALTAD.csv' OUT=WORK.DATOS_LEALTAD DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

%macro filtrar(producto, minimo);
/* Etiqueta: Filtra saldos del producto desde el minimo */
PROC SQL;
CREATE TABLE WORK.RES_&producto. AS
SELECT ID, SALDO
FROM WORK.DATOS_&producto.
WHERE SALDO >= &minimo.;
QUIT;
%mend filtrar;

%filtrar(LEALTAD, 200);
