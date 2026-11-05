/* Caso l2_13_anti_join_sin_ventas: clientes sin ventas, con LEFT JOIN y WHERE IS MISSING sobre la
   clave de la tabla de la derecha. Y los clientes con ventas, sin repetir, con INNER JOIN y DISTINCT.
   Entradas: entradas/clientes.csv y entradas/ventas.csv. Salidas: WORK.clientes_sin_ventas y
   WORK.clientes_con_ventas. La ruta '...' es un marcador; el oraculo lee las entradas de la carpeta
   del caso. */

PROC IMPORT DATAFILE='.../entradas/clientes.csv' OUT=WORK.CLIENTES DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

PROC IMPORT DATAFILE='.../entradas/ventas.csv' OUT=WORK.VENTAS DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

/* Etiqueta: Clientes sin ventas */
PROC SQL;
  CREATE TABLE WORK.clientes_sin_ventas AS
  SELECT c.id_cliente, c.nombre
  FROM WORK.clientes c
  LEFT JOIN WORK.ventas v
  ON ( c.id_cliente = v.id_cliente )
  WHERE v.id_venta IS MISSING;
QUIT;

/* Etiqueta: Clientes con al menos una venta */
PROC SQL;
  CREATE TABLE WORK.clientes_con_ventas AS
  SELECT DISTINCT c.id_cliente, c.nombre
  FROM WORK.clientes c
  INNER JOIN WORK.ventas v
  ON ( c.id_cliente = v.id_cliente );
QUIT;

PROC EXPORT DATA=WORK.clientes_sin_ventas OUTFILE='.../salida/clientes_sin_ventas.csv'
  DBMS=CSV REPLACE;
RUN;
