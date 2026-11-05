/* Caso l3_01_count_star_vs_count_col: COUNT(*) cuenta todas las filas; COUNT(saldo) cuenta solo los
   saldos presentes. La diferencia son los saldos faltantes. Entradas: entradas/clientes.csv. Salida:
   WORK.resumen_saldos. La ruta '...' es un marcador; el oraculo lee las entradas de la carpeta del
   caso. */

PROC IMPORT DATAFILE='.../entradas/clientes.csv' OUT=WORK.CLIENTES DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

/* Etiqueta: Conteo de filas y de saldos presentes */
PROC SQL;
  CREATE TABLE WORK.resumen_saldos AS
  SELECT COUNT(*) AS total,
         COUNT(saldo) AS con_saldo,
         COUNT(*) - COUNT(saldo) AS sin_saldo
  FROM WORK.clientes;
QUIT;

PROC EXPORT DATA=WORK.resumen_saldos OUTFILE='.../salida/resumen_saldos.csv'
  DBMS=CSV REPLACE;
RUN;
