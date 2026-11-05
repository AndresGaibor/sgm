/* Caso l1_14_expresion_compuesta: ventas por canal T* con cantidad de 2 a 5; neto = (monto - 50) * cantidad.
   Ordena por el alias neto, descendente. Entrada: entradas/ventas.csv. Salida: WORK.netos.
   La ruta '...' es un marcador; el oraculo lee las entradas de la carpeta del caso. */

PROC IMPORT DATAFILE='.../entradas/ventas.csv' OUT=WORK.ventas DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

PROC SQL;
  CREATE TABLE WORK.netos AS
  SELECT id_venta,
         canal,
         (monto - 50) * cantidad AS neto
  FROM WORK.ventas
  WHERE canal LIKE 'T%' AND cantidad BETWEEN 2 AND 5
  ORDER BY neto DESC, id_venta;
QUIT;
