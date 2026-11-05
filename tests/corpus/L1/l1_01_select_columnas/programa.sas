/* Caso l1_01_select_columnas: proyecta tres columnas de clientes con PROC SQL.
   Entrada: entradas/clientes.csv. Salida: WORK.basico.
   La ruta '...' es un marcador; el oraculo lee las entradas de la carpeta del caso. */

PROC IMPORT DATAFILE='.../entradas/clientes.csv' OUT=WORK.clientes DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

PROC SQL;
  CREATE TABLE WORK.basico AS
  SELECT id_cliente, nombre, saldo
  FROM WORK.clientes;
QUIT;
