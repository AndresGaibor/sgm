/* Caso l1_04_distinct_orden: lista las ciudades distintas de clientes, ordenadas.
   Entrada: entradas/clientes.csv. Salida: WORK.ciudades.
   La ruta '...' es un marcador; el oraculo lee las entradas de la carpeta del caso. */

PROC IMPORT DATAFILE='.../entradas/clientes.csv' OUT=WORK.clientes DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

PROC SQL;
  CREATE TABLE WORK.ciudades AS
  SELECT DISTINCT ciudad
  FROM WORK.clientes
  ORDER BY ciudad;
QUIT;
