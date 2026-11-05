/* Caso l0_12_bandera_numerica: calcula el valor de inventario y marca con 1 los de mas de 2000.
   Entrada: entradas/productos.csv. Salida: WORK.bandera.
   Las rutas '...' son marcadores; el ejecutor no las usa. */

PROC IMPORT DATAFILE='.../entradas/productos.csv' OUT=WORK.productos DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

DATA WORK.bandera;
  SET WORK.productos;
  valor = precio * stock;
  IF valor > 2000 THEN grande = 1;
  ELSE grande = 0;
RUN;

PROC EXPORT DATA=WORK.bandera OUTFILE='.../salida/bandera.csv' DBMS=CSV REPLACE;
RUN;
