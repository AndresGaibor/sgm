/* Caso l2_06_in_subconsulta: clientes que tienen alguna venta de monto mayor que 500.
   La subconsulta IN devuelve el id de cliente. Entradas: entradas/clientes.csv y entradas/ventas.csv.
   Salida: WORK.clientes_con_compras_altas. La ruta '...' es un marcador; el oraculo lee las entradas
   de la carpeta del caso. */

PROC IMPORT DATAFILE='.../entradas/clientes.csv' OUT=WORK.CLIENTES DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

PROC IMPORT DATAFILE='.../entradas/ventas.csv' OUT=WORK.VENTAS DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

/* Etiqueta: Clientes con compras altas (IN con subconsulta) */
PROC SQL;
  CREATE TABLE WORK.clientes_con_compras_altas AS
  SELECT c.id_cliente, c.nombre
  FROM WORK.clientes c
  WHERE c.id_cliente IN (
    SELECT v.id_cliente
    FROM WORK.ventas v
    WHERE v.monto > 500
  );
QUIT;

PROC EXPORT DATA=WORK.clientes_con_compras_altas
  OUTFILE='.../salida/clientes_con_compras_altas.csv' DBMS=CSV REPLACE;
RUN;
