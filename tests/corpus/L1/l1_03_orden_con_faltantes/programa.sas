/* Caso l1_03_orden_con_faltantes: ordena clientes por saldo; dos saldos vacios son faltantes.
   Entrada: entradas/clientes.csv. Salida: WORK.saldos_ordenados.
   La ruta '...' es un marcador; el oraculo lee las entradas de la carpeta del caso. */

PROC IMPORT DATAFILE='.../entradas/clientes.csv' OUT=WORK.clientes DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

PROC SQL;
  CREATE TABLE WORK.saldos_ordenados AS
  SELECT id_cliente, saldo
  FROM WORK.clientes
  ORDER BY saldo, id_cliente;
QUIT;
