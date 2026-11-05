/* Caso l5_12_do_iterativo: %DO con indice genera una tabla por vuelta. Entradas:
   entradas/DATOS_LEALTAD.csv. Salidas: WORK.PARTE_1 y WORK.PARTE_2. Datos ficticios. */

PROC IMPORT DATAFILE='.../entradas/DATOS_LEALTAD.csv' OUT=WORK.DATOS_LEALTAD DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;





/* Etiqueta: Parte i con los ID hasta i por 3 */
PROC SQL;
CREATE TABLE WORK.PARTE_1 AS
SELECT ID
FROM WORK.DATOS_LEALTAD
WHERE ID <= 1*3;
QUIT;

/* Etiqueta: Parte i con los ID hasta i por 3 */
PROC SQL;
CREATE TABLE WORK.PARTE_2 AS
SELECT ID
FROM WORK.DATOS_LEALTAD
WHERE ID <= 2*3;
QUIT;


