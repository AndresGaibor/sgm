/* Caso l3_07_total_origen_y_salida: total de origen, total de la salida filtrada y total del resto.
   Es la conciliación de totales del programa grande: el total de origen debe ser igual a la suma de
   la salida y del resto. Entradas: entradas/ventas.csv. Salidas: WORK.total_origen, WORK.total_web y
   WORK.total_resto. La ruta '...' es un marcador; el oraculo lee las entradas de la carpeta del caso. */

PROC IMPORT DATAFILE='.../entradas/ventas.csv' OUT=WORK.VENTAS DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

/* Etiqueta: Total de origen */
PROC SQL;
  CREATE TABLE WORK.total_origen AS
  SELECT SUM(monto) AS suma_origen
  FROM WORK.ventas;
QUIT;

/* Etiqueta: Total de salida (canal WEB) */
PROC SQL;
  CREATE TABLE WORK.total_web AS
  SELECT SUM(monto) AS suma_salida
  FROM WORK.ventas
  WHERE canal = 'WEB';
QUIT;

/* Etiqueta: Total del resto */
PROC SQL;
  CREATE TABLE WORK.total_resto AS
  SELECT SUM(monto) AS suma_resto
  FROM WORK.ventas
  WHERE canal <> 'WEB';
QUIT;

PROC EXPORT DATA=WORK.total_origen OUTFILE='.../salida/total_origen.csv' DBMS=CSV REPLACE;
RUN;
