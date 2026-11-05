/* Caso l3_05_having_conteo: clientes por ciudad. Se parte en grupos grandes (3 o más) y pequeños
   (menos de 3) con HAVING. La suma de los dos grupos es el total de clientes.
   Entradas: entradas/clientes.csv. Salidas: WORK.todos_grupos, WORK.grupos_grandes y
   WORK.grupos_pequenos. La ruta '...' es un marcador; el oraculo lee las entradas de la carpeta del
   caso. */

PROC IMPORT DATAFILE='.../entradas/clientes.csv' OUT=WORK.CLIENTES DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

/* Etiqueta: Clientes por ciudad, todos los grupos */
PROC SQL;
  CREATE TABLE WORK.todos_grupos AS
  SELECT ciudad, COUNT(*) AS n
  FROM WORK.clientes
  GROUP BY ciudad;
QUIT;

/* Etiqueta: Grupos grandes (HAVING 3 o más) */
PROC SQL;
  CREATE TABLE WORK.grupos_grandes AS
  SELECT ciudad, COUNT(*) AS n
  FROM WORK.clientes
  GROUP BY ciudad
  HAVING COUNT(*) >= 3;
QUIT;

/* Etiqueta: Grupos pequeños (HAVING menos de 3) */
PROC SQL;
  CREATE TABLE WORK.grupos_pequenos AS
  SELECT ciudad, COUNT(*) AS n
  FROM WORK.clientes
  GROUP BY ciudad
  HAVING COUNT(*) < 3;
QUIT;

PROC EXPORT DATA=WORK.grupos_grandes OUTFILE='.../salida/grupos_grandes.csv'
  DBMS=CSV REPLACE;
RUN;
