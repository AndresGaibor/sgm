/* Caso l6_05_last_una_fila_por_grupo: IF LAST.CIUDAD conserva la ultima venta de cada ciudad.
   Entradas: entradas/VENTAS.csv (ordenada por CIUDAD). Salida: WORK.ULTIMA_VENTA. Datos ficticios. */

PROC IMPORT DATAFILE='.../entradas/VENTAS.csv' OUT=WORK.VENTAS DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

/* Etiqueta: Ultima venta por ciudad */
DATA WORK.ULTIMA_VENTA;
  SET WORK.VENTAS;
  BY CIUDAD;
  IF LAST.CIUDAD;
RUN;

PROC EXPORT DATA=WORK.ULTIMA_VENTA OUTFILE='.../salida/ULTIMA_VENTA.csv' DBMS=CSV REPLACE;
RUN;
