/* Caso l1_08_in_lista: clientes de dos ciudades concretas, con IN, ordenados por ciudad e id.
   Entrada: entradas/clientes.csv. Salida: WORK.clientes_seleccion.
   La ruta '...' es un marcador; el oraculo lee las entradas de la carpeta del caso. */

PROC IMPORT DATAFILE='.../entradas/clientes.csv' OUT=WORK.clientes DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

PROC SQL;
  CREATE TABLE WORK.clientes_seleccion AS
  SELECT id_cliente, nombre, ciudad
  FROM WORK.clientes
  WHERE ciudad IN ('Villa Norte', 'Lago Azul')
  ORDER BY ciudad, id_cliente;
QUIT;
