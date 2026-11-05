/* Caso l1_09_between_fechas: ventas de marzo de 2026, con BETWEEN sobre la fecha en texto ISO.
   Entrada: entradas/ventas.csv. Salida: WORK.marzo.
   La ruta '...' es un marcador; el oraculo lee las entradas de la carpeta del caso. */

PROC IMPORT DATAFILE='.../entradas/ventas.csv' OUT=WORK.ventas DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

PROC SQL;
  CREATE TABLE WORK.marzo AS
  SELECT id_venta, fecha, monto
  FROM WORK.ventas
  WHERE fecha BETWEEN '2026-03-01' AND '2026-03-31'
  ORDER BY fecha, id_venta;
QUIT;
