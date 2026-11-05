/* Caso l2_12_auto_join_misma_ciudad: pares de clientes de la misma ciudad. Es un auto-JOIN: la tabla
   clientes se une consigo misma. La primera salida toma cada par una vez (id menor con id mayor). La
   segunda toma los pares en ambos sentidos, así que tiene el doble de filas.
   Entradas: entradas/clientes.csv. Salidas: WORK.pares_misma_ciudad y WORK.pares_ordenados. La ruta
   '...' es un marcador; el oraculo lee las entradas de la carpeta del caso. */

PROC IMPORT DATAFILE='.../entradas/clientes.csv' OUT=WORK.CLIENTES DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

/* Etiqueta: Pares de clientes de la misma ciudad, sin repetir */
PROC SQL;
  CREATE TABLE WORK.pares_misma_ciudad AS
  SELECT a.id_cliente AS id_a, b.id_cliente AS id_b, a.ciudad
  FROM WORK.clientes a
  INNER JOIN WORK.clientes b
  ON ( a.ciudad = b.ciudad )
  WHERE a.id_cliente < b.id_cliente;
QUIT;

/* Etiqueta: Pares en ambos sentidos */
PROC SQL;
  CREATE TABLE WORK.pares_ordenados AS
  SELECT a.id_cliente AS id_a, b.id_cliente AS id_b, a.ciudad
  FROM WORK.clientes a
  INNER JOIN WORK.clientes b
  ON ( a.ciudad = b.ciudad )
  WHERE a.id_cliente <> b.id_cliente;
QUIT;

PROC EXPORT DATA=WORK.pares_misma_ciudad OUTFILE='.../salida/pares_misma_ciudad.csv'
  DBMS=CSV REPLACE;
RUN;
