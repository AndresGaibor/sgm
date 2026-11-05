/* Caso l3_12_having_suma: existencias por categoría. La primera salida suma todas las categorías; la
   segunda conserva solo las de existencias mayores que 150, con HAVING sobre una suma. Entradas:
   entradas/productos.csv. Salidas: WORK.stock_por_categoria y WORK.categorias_altas. La ruta '...' es
   un marcador; el oraculo lee las entradas de la carpeta del caso. */

PROC IMPORT DATAFILE='.../entradas/productos.csv' OUT=WORK.PRODUCTOS DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

/* Etiqueta: Existencias por categoria */
PROC SQL;
  CREATE TABLE WORK.stock_por_categoria AS
  SELECT categoria, COUNT(*) AS productos, SUM(stock) AS stock_total
  FROM WORK.productos
  GROUP BY categoria
  ORDER BY categoria;
QUIT;

/* Etiqueta: Categorias con existencias altas (HAVING sobre SUM) */
PROC SQL;
  CREATE TABLE WORK.categorias_altas AS
  SELECT categoria, SUM(stock) AS stock_total
  FROM WORK.productos
  GROUP BY categoria
  HAVING SUM(stock) > 150
  ORDER BY stock_total DESC, categoria;
QUIT;

PROC EXPORT DATA=WORK.categorias_altas OUTFILE='.../salida/categorias_altas.csv'
  DBMS=CSV REPLACE;
RUN;
