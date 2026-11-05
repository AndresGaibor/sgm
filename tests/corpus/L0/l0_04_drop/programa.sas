/* Caso l0_04_drop: quita stock y categoria del catalogo de productos (sentencia DROP).
   Entrada: entradas/productos.csv. Salida: WORK.catalogo.
   Las rutas '...' son marcadores; el ejecutor no las usa. */

PROC IMPORT DATAFILE='.../entradas/productos.csv' OUT=WORK.productos DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

DATA WORK.catalogo;
  SET WORK.productos;
  DROP stock categoria;
RUN;

PROC EXPORT DATA=WORK.catalogo OUTFILE='.../salida/catalogo.csv' DBMS=CSV REPLACE;
RUN;
