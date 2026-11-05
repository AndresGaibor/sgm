/* Caso l2_02_left_join_con_faltantes: todos los clientes con sus ventas. Un cliente sin ventas sale
   con faltantes en las columnas de la derecha. Entradas: entradas/clientes.csv y entradas/ventas.csv.
   Salida: WORK.clientes_con_ventas. La ruta '...' es un marcador; el oraculo lee las entradas de la
   carpeta del caso. */

PROC IMPORT DATAFILE='.../entradas/clientes.csv' OUT=WORK.CLIENTES DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

PROC IMPORT DATAFILE='.../entradas/ventas.csv' OUT=WORK.VENTAS DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

/* Etiqueta: Clientes con sus ventas (LEFT JOIN) */
/* Código de query generado para SAS Studio por Common Query Services */

PROC SQL;
  CREATE TABLE WORK.clientes_con_ventas AS
  SELECT c.id_cliente, c.nombre, v.id_venta, v.monto
  FROM WORK.clientes c
  LEFT JOIN WORK.ventas v
  ON ( c.id_cliente = v.id_cliente );
QUIT;

PROC EXPORT DATA=WORK.clientes_con_ventas OUTFILE='.../salida/clientes_con_ventas.csv'
  DBMS=CSV REPLACE;
RUN;
