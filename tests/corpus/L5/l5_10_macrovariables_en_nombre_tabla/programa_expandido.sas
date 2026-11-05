/* Caso l5_10_macrovariables_en_nombre_tabla: el nombre de la tabla se arma con anio, mes y dia.
   Entradas: entradas/DATOS_LEALTAD.csv. Salida: WORK.CORTE_20261104. Datos ficticios. */

PROC IMPORT DATAFILE='.../entradas/DATOS_LEALTAD.csv' OUT=WORK.DATOS_LEALTAD DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;





/* Etiqueta: Corte del dia con saldos menores que 200 */
PROC SQL;
CREATE TABLE WORK.CORTE_20261104 AS
SELECT ID, SALDO
FROM WORK.DATOS_LEALTAD
WHERE SALDO < 200;
QUIT;
