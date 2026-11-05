/* Caso l0_15_importar_exportar: importa productos, calcula el valor de stock y exporta codigo y valor.
   Entrada: entradas/productos.csv. Salida: WORK.valor_stock.
   Las rutas '...' son marcadores; el ejecutor no las usa. */

PROC IMPORT DATAFILE='.../entradas/productos.csv' OUT=WORK.productos DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

DATA WORK.valor_stock;
  SET WORK.productos;
  valor_stock = precio * stock;
  KEEP codigo valor_stock;
RUN;

PROC EXPORT DATA=WORK.valor_stock OUTFILE='.../salida/valor_stock.csv' DBMS=CSV REPLACE;
RUN;
