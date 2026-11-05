/* Caso l2_11_join_tres_tablas: cada venta con el nombre de su cliente y la zona de la ciudad del
   cliente. Tres tablas unidas con dos INNER JOIN encadenados.
   Entradas: entradas/ventas.csv, entradas/clientes.csv y entradas/zonas.csv. Salida:
   WORK.ventas_zona. La ruta '...' es un marcador; el oraculo lee las entradas de la carpeta del caso. */

PROC IMPORT DATAFILE='.../entradas/ventas.csv' OUT=WORK.VENTAS DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

PROC IMPORT DATAFILE='.../entradas/clientes.csv' OUT=WORK.CLIENTES DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

PROC IMPORT DATAFILE='.../entradas/zonas.csv' OUT=WORK.ZONAS DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

/* Etiqueta: Ventas con nombre de cliente y zona */
PROC SQL;
  CREATE TABLE WORK.ventas_zona AS
  SELECT v.id_venta, c.nombre, z.zona, v.monto
  FROM WORK.ventas v
  INNER JOIN WORK.clientes c
  ON ( v.id_cliente = c.id_cliente )
  INNER JOIN WORK.zonas z
  ON ( c.ciudad = z.ciudad );
QUIT;

PROC EXPORT DATA=WORK.ventas_zona OUTFILE='.../salida/ventas_zona.csv'
  DBMS=CSV REPLACE;
RUN;
