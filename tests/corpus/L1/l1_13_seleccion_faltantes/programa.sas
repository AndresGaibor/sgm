/* Caso l1_13_seleccion_faltantes: clientes que no estan inactivos; hay ciudad y saldo vacios.
   Entrada: entradas/clientes.csv. Salida: WORK.no_inactivos.
   La ruta '...' es un marcador; el oraculo lee las entradas de la carpeta del caso. */

PROC IMPORT DATAFILE='.../entradas/clientes.csv' OUT=WORK.clientes DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

PROC SQL;
  CREATE TABLE WORK.no_inactivos AS
  SELECT id_cliente, ciudad, saldo
  FROM WORK.clientes
  WHERE NOT (estado = 'INACTIVO');
QUIT;
