/* Caso l3_04_group_by_varias_columnas: clientes y saldo promedio por ciudad y estado. El promedio
   ignora los saldos faltantes. Entradas: entradas/clientes.csv. Salida: WORK.por_ciudad_estado. La
   ruta '...' es un marcador; el oraculo lee las entradas de la carpeta del caso. */

PROC IMPORT DATAFILE='.../entradas/clientes.csv' OUT=WORK.CLIENTES DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

/* Etiqueta: Clientes y saldo promedio por ciudad y estado */
PROC SQL;
  CREATE TABLE WORK.por_ciudad_estado AS
  SELECT ciudad, estado,
         COUNT(*) AS clientes,
         AVG(saldo) AS saldo_promedio
  FROM WORK.clientes
  GROUP BY ciudad, estado
  ORDER BY ciudad, estado;
QUIT;

PROC EXPORT DATA=WORK.por_ciudad_estado OUTFILE='.../salida/por_ciudad_estado.csv'
  DBMS=CSV REPLACE;
RUN;
