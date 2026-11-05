/* Caso l2_01_inner_join_clientes_ventas: une ventas con clientes con INNER JOIN.
   Una venta de un cliente que no existe se descarta. Entradas: entradas/clientes.csv y
   entradas/ventas.csv. Salida: WORK.ventas_con_nombre. La ruta '...' es un marcador; el oraculo
   lee las entradas de la carpeta del caso. */

PROC IMPORT DATAFILE='.../entradas/clientes.csv' OUT=WORK.CLIENTES DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

PROC IMPORT DATAFILE='.../entradas/ventas.csv' OUT=WORK.VENTAS DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

/* Etiqueta: Ventas con nombre del cliente */
PROC SQL;
  CREATE TABLE WORK.ventas_con_nombre AS
  SELECT v.id_venta, c.nombre, v.monto
  FROM WORK.ventas v
  INNER JOIN WORK.clientes c
  ON ( v.id_cliente = c.id_cliente );
QUIT;

PROC EXPORT DATA=WORK.ventas_con_nombre OUTFILE='.../salida/ventas_con_nombre.csv'
  DBMS=CSV REPLACE;
RUN;
