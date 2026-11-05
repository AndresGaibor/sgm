/* Caso l2_09_coalesce_tras_left_join: monto y canal de cada cliente. COALESCE pone SIN_VENTA y 0 a
   quien no tiene venta, y 0 a la venta con monto faltante. Entradas: entradas/clientes.csv y
   entradas/ventas.csv. Salida: WORK.clientes_monto. La ruta '...' es un marcador; el oraculo lee las
   entradas de la carpeta del caso. */

PROC IMPORT DATAFILE='.../entradas/clientes.csv' OUT=WORK.CLIENTES DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

PROC IMPORT DATAFILE='.../entradas/ventas.csv' OUT=WORK.VENTAS DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

/* Etiqueta: Monto y canal por cliente con COALESCE */
PROC SQL;
  CREATE TABLE WORK.clientes_monto AS
  SELECT c.id_cliente, c.nombre,
         COALESCE(v.canal, 'SIN_VENTA') AS canal,
         COALESCE(v.monto, 0) AS monto
  FROM WORK.clientes c
  LEFT JOIN WORK.ventas v
  ON ( c.id_cliente = v.id_cliente );
QUIT;

PROC EXPORT DATA=WORK.clientes_monto OUTFILE='.../salida/clientes_monto.csv'
  DBMS=CSV REPLACE;
RUN;
