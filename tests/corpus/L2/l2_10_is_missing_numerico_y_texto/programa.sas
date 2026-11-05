/* Caso l2_10_is_missing_numerico_y_texto: separa los clientes con algún faltante (saldo numérico o
   ciudad de texto) de los completos. Los dos grupos juntos dan todos los clientes.
   Entradas: entradas/clientes.csv. Salidas: WORK.clientes_incompletos y WORK.clientes_completos.
   La ruta '...' es un marcador; el oraculo lee las entradas de la carpeta del caso. */

PROC IMPORT DATAFILE='.../entradas/clientes.csv' OUT=WORK.CLIENTES DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

/* Etiqueta: Clientes con saldo o ciudad faltante */
PROC SQL;
  CREATE TABLE WORK.clientes_incompletos AS
  SELECT id_cliente, nombre, ciudad, saldo
  FROM WORK.clientes
  WHERE saldo IS MISSING OR ciudad IS MISSING;
QUIT;

/* Etiqueta: Clientes completos */
PROC SQL;
  CREATE TABLE WORK.clientes_completos AS
  SELECT id_cliente, nombre, ciudad, saldo
  FROM WORK.clientes
  WHERE saldo IS NOT MISSING AND ciudad IS NOT MISSING;
QUIT;

PROC EXPORT DATA=WORK.clientes_incompletos OUTFILE='.../salida/clientes_incompletos.csv'
  DBMS=CSV REPLACE;
RUN;
