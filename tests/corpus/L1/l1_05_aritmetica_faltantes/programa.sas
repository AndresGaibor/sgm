/* Caso l1_05_aritmetica_faltantes: calcula totales por linea de venta; hay monto y cantidad vacios.
   Entrada: entradas/ventas.csv. Salida: WORK.totales.
   La ruta '...' es un marcador; el oraculo lee las entradas de la carpeta del caso. */

PROC IMPORT DATAFILE='.../entradas/ventas.csv' OUT=WORK.ventas DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

PROC SQL;
  CREATE TABLE WORK.totales AS
  SELECT id_venta,
         monto * cantidad AS total_linea,
         monto + 10 AS monto_mas_diez
  FROM WORK.ventas
  ORDER BY id_venta;
QUIT;
