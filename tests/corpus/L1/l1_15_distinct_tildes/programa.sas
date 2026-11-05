/* Caso l1_15_distinct_tildes: combinaciones distintas de nombre y ciudad; los nombres llevan tildes y Ñ.
   Entrada: entradas/clientes.csv. Salida: WORK.combinaciones.
   La ruta '...' es un marcador; el oraculo lee las entradas de la carpeta del caso. */

PROC IMPORT DATAFILE='.../entradas/clientes.csv' OUT=WORK.clientes DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

PROC SQL;
  CREATE TABLE WORK.combinaciones AS
  SELECT DISTINCT nombre, ciudad
  FROM WORK.clientes;
QUIT;
