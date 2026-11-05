/* Caso l2_14_inner_join_where_orden: ventas por el canal WEB de clientes activos, ordenadas por monto
   de mayor a menor y, en empate, por id de venta. El monto faltante queda al final en orden
   descendente, igual que en SAS. Entradas: entradas/ventas.csv y entradas/clientes.csv. Salida:
   WORK.ventas_web_activas. La ruta '...' es un marcador; el oraculo lee las entradas de la carpeta
   del caso. */

PROC IMPORT DATAFILE='.../entradas/ventas.csv' OUT=WORK.VENTAS DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

PROC IMPORT DATAFILE='.../entradas/clientes.csv' OUT=WORK.CLIENTES DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

/* Etiqueta: Ventas WEB de clientes activos */
PROC SQL;
  CREATE TABLE WORK.ventas_web_activas AS
  SELECT v.id_venta, c.nombre, v.monto
  FROM WORK.ventas v
  INNER JOIN WORK.clientes c
  ON ( v.id_cliente = c.id_cliente )
  WHERE v.canal = 'WEB' AND c.estado = 'ACTIVO'
  ORDER BY v.monto DESC, v.id_venta;
QUIT;

PROC EXPORT DATA=WORK.ventas_web_activas OUTFILE='.../salida/ventas_web_activas.csv'
  DBMS=CSV REPLACE;
RUN;
