/* Caso l1_06_like_con_tildes: selecciona clientes cuyo nombre empieza por J, por M o por Ñ.
   Los nombres llevan tildes y Ñ. Entrada: entradas/clientes.csv. Salida: WORK.nombres_j_n.
   La ruta '...' es un marcador; el oraculo lee las entradas de la carpeta del caso. */

PROC IMPORT DATAFILE='.../entradas/clientes.csv' OUT=WORK.clientes DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

PROC SQL;
  CREATE TABLE WORK.nombres_j_n AS
  SELECT id_cliente, nombre, ciudad
  FROM WORK.clientes
  WHERE nombre LIKE 'J%' OR nombre LIKE 'M%' OR nombre LIKE 'Ñ%'
  ORDER BY id_cliente;
QUIT;
