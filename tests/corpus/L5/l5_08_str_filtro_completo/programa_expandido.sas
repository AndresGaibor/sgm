/* Caso l5_08_str_filtro_completo: %STR guarda una condicion con comillas simples y se pega en el
   WHERE. Entradas: entradas/DATOS_LEALTAD.csv. Salida: WORK.RES_FILTRO. Datos ficticios. */

PROC IMPORT DATAFILE='.../entradas/DATOS_LEALTAD.csv' OUT=WORK.DATOS_LEALTAD DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;



/* Etiqueta: Activos con saldo mayor que 100 */
PROC SQL;
CREATE TABLE WORK.RES_FILTRO AS
SELECT ID, SALDO
FROM WORK.DATOS_LEALTAD
WHERE ESTADO = 'ACTIVO' AND SALDO > 100;
QUIT;
