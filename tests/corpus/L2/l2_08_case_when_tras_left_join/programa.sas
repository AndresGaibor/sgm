/* Caso l2_08_case_when_tras_left_join: clasifica a cada cliente por su venta. Sin venta, SIN_VENTAS.
   Con venta de monto 500 o más, ALTA. En otro caso, BAJA (incluye el monto faltante, que en SAS es
   menor que cualquier número). Luego resume cuántas filas cae en cada categoría.
   Entradas: entradas/clientes.csv y entradas/ventas.csv. Salidas: WORK.clientes_categoria y
   WORK.resumen_categoria. La ruta '...' es un marcador; el oraculo lee las entradas de la carpeta
   del caso. */

PROC IMPORT DATAFILE='.../entradas/clientes.csv' OUT=WORK.CLIENTES DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

PROC IMPORT DATAFILE='.../entradas/ventas.csv' OUT=WORK.VENTAS DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

/* Etiqueta: Categoria de cliente segun su venta */
PROC SQL;
  CREATE TABLE WORK.clientes_categoria AS
  SELECT c.id_cliente, c.nombre,
         CASE WHEN v.id_venta IS MISSING THEN 'SIN_VENTAS'
              WHEN v.monto >= 500 THEN 'ALTA'
              ELSE 'BAJA'
         END AS categoria
  FROM WORK.clientes c
  LEFT JOIN WORK.ventas v
  ON ( c.id_cliente = v.id_cliente );
QUIT;

/* Etiqueta: Filas por categoria */
PROC SQL;
  CREATE TABLE WORK.resumen_categoria AS
  SELECT categoria, COUNT(*) AS filas
  FROM WORK.clientes_categoria
  GROUP BY categoria;
QUIT;

PROC EXPORT DATA=WORK.resumen_categoria OUTFILE='.../salida/resumen_categoria.csv'
  DBMS=CSV REPLACE;
RUN;
