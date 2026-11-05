/* Caso l1_10_dos_etapas_faltantes: dos etapas de PROC SQL; el stock vacio es faltante y se propaga.
   Entrada: entradas/productos.csv. Salida: WORK.resumen_disp (WORK.disponibles es intermedia).
   La ruta '...' es un marcador; el oraculo lee las entradas de la carpeta del caso. */

PROC IMPORT DATAFILE='.../entradas/productos.csv' OUT=WORK.productos DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

PROC SQL;
  CREATE TABLE WORK.disponibles AS
  SELECT codigo, descripcion, stock
  FROM WORK.productos
  WHERE categoria = 'A';

  CREATE TABLE WORK.resumen_disp AS
  SELECT codigo, stock * 2 AS doble_stock
  FROM WORK.disponibles
  ORDER BY codigo;
QUIT;
