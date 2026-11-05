/* Caso l3_11_agregado_con_join: agregados sobre un LEFT JOIN. Cada cliente cuenta una fila por cada
   venta; un cliente sin ventas cuenta una fila con faltantes. Por eso las filas del cruce son las
   ventas más los clientes sin ventas. Entradas: entradas/clientes.csv y entradas/ventas.csv.
   Salidas: WORK.por_ciudad y WORK.sin_ventas. La ruta '...' es un marcador; el oraculo lee las
   entradas de la carpeta del caso. */

PROC IMPORT DATAFILE='.../entradas/clientes.csv' OUT=WORK.CLIENTES DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

PROC IMPORT DATAFILE='.../entradas/ventas.csv' OUT=WORK.VENTAS DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

/* Etiqueta: Agregados por ciudad sobre el cruce */
PROC SQL;
  CREATE TABLE WORK.por_ciudad AS
  SELECT c.ciudad,
         COUNT(*) AS filas_cruce,
         COUNT(v.id_venta) AS ventas,
         SUM(v.monto) AS monto_total
  FROM WORK.clientes c
  LEFT JOIN WORK.ventas v
  ON ( c.id_cliente = v.id_cliente )
  GROUP BY c.ciudad
  ORDER BY c.ciudad;
QUIT;

/* Etiqueta: Clientes sin ventas */
PROC SQL;
  CREATE TABLE WORK.sin_ventas AS
  SELECT c.id_cliente
  FROM WORK.clientes c
  LEFT JOIN WORK.ventas v
  ON ( c.id_cliente = v.id_cliente )
  WHERE v.id_venta IS MISSING;
QUIT;

PROC EXPORT DATA=WORK.por_ciudad OUTFILE='.../salida/por_ciudad_cruce.csv' DBMS=CSV REPLACE;
RUN;
