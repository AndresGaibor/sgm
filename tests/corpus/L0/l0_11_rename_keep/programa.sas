/* Caso l0_11_rename_keep: renombra precio a precio_lista y conserva solo codigo, precio_lista y stock.
   Entrada: entradas/productos.csv. Salida: WORK.lista.
   Las rutas '...' son marcadores; el ejecutor no las usa. */

PROC IMPORT DATAFILE='.../entradas/productos.csv' OUT=WORK.productos DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

DATA WORK.lista;
  SET WORK.productos;
  RENAME precio = precio_lista;
  KEEP codigo precio_lista stock;
RUN;

PROC EXPORT DATA=WORK.lista OUTFILE='.../salida/lista.csv' DBMS=CSV REPLACE;
RUN;
