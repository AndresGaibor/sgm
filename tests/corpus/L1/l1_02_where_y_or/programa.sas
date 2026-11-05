/* Caso l1_02_where_y_or: filtra clientes activos con saldo alto, o los de Monte Verde.
   Entrada: entradas/clientes.csv. Salida: WORK.seleccion.
   La ruta '...' es un marcador; el oraculo lee las entradas de la carpeta del caso. */

PROC IMPORT DATAFILE='.../entradas/clientes.csv' OUT=WORK.clientes DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

PROC SQL;
  CREATE TABLE WORK.seleccion AS
  SELECT id_cliente, ciudad, saldo, estado
  FROM WORK.clientes
  WHERE (estado = 'ACTIVO' AND saldo >= 1000) OR ciudad = 'Monte Verde';
QUIT;
