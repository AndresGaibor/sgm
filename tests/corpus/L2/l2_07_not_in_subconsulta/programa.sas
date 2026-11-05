/* Caso l2_07_not_in_subconsulta: separa los clientes que usaron el canal TELEFONO de los que no.
   IN y NOT IN con la misma subconsulta: juntas dan todos los clientes. La clave de la subconsulta no
   tiene faltantes. Entradas: entradas/clientes.csv y entradas/ventas.csv. Salidas:
   WORK.clientes_con_telefono y WORK.clientes_sin_telefono. La ruta '...' es un marcador; el oraculo
   lee las entradas de la carpeta del caso. */

PROC IMPORT DATAFILE='.../entradas/clientes.csv' OUT=WORK.CLIENTES DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

PROC IMPORT DATAFILE='.../entradas/ventas.csv' OUT=WORK.VENTAS DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

/* Etiqueta: Clientes con telefono */
PROC SQL;
  CREATE TABLE WORK.clientes_con_telefono AS
  SELECT c.id_cliente, c.nombre
  FROM WORK.clientes c
  WHERE c.id_cliente IN (
    SELECT v.id_cliente FROM WORK.ventas v WHERE v.canal = 'TELEFONO'
  );
QUIT;

/* Etiqueta: Clientes sin telefono */
PROC SQL;
  CREATE TABLE WORK.clientes_sin_telefono AS
  SELECT c.id_cliente, c.nombre
  FROM WORK.clientes c
  WHERE c.id_cliente NOT IN (
    SELECT v.id_cliente FROM WORK.ventas v WHERE v.canal = 'TELEFONO'
  );
QUIT;

PROC EXPORT DATA=WORK.clientes_sin_telefono OUTFILE='.../salida/clientes_sin_telefono.csv'
  DBMS=CSV REPLACE;
RUN;
