/* Caso l0_06_asignacion: agrega el valor de inventario de cada producto (precio por stock).
   Entrada: entradas/productos.csv. Salida: WORK.inventario.
   Las rutas '...' son marcadores; el ejecutor no las usa. */

PROC IMPORT DATAFILE='.../entradas/productos.csv' OUT=WORK.productos DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

DATA WORK.inventario;
  SET WORK.productos;
  total_valor = precio * stock;
RUN;

PROC EXPORT DATA=WORK.inventario OUTFILE='.../salida/inventario.csv' DBMS=CSV REPLACE;
RUN;
