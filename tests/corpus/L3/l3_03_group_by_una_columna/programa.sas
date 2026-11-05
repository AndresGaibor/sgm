/* Caso l3_03_group_by_una_columna: clientes y saldo total por ciudad. Una ciudad vacía forma su propio
   grupo, como en SAS. Entradas: entradas/clientes.csv. Salida: WORK.por_ciudad. La ruta '...' es un
   marcador; el oraculo lee las entradas de la carpeta del caso. */

PROC IMPORT DATAFILE='.../entradas/clientes.csv' OUT=WORK.CLIENTES DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

/* Etiqueta: Clientes y saldo total por ciudad */
PROC SQL;
  CREATE TABLE WORK.por_ciudad AS
  SELECT ciudad, COUNT(*) AS clientes, SUM(saldo) AS saldo_total
  FROM WORK.clientes
  GROUP BY ciudad
  ORDER BY ciudad;
QUIT;

PROC EXPORT DATA=WORK.por_ciudad OUTFILE='.../salida/por_ciudad.csv' DBMS=CSV REPLACE;
RUN;
