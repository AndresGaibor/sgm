/* Caso l1_07_like_guion_bajo: busca productos cuyo codigo tiene 10 seguido de un digito (guion bajo
   como comodin de un caracter). Entrada: entradas/productos.csv. Salida: WORK.codigos_100.
   La ruta '...' es un marcador; el oraculo lee las entradas de la carpeta del caso. */

PROC IMPORT DATAFILE='.../entradas/productos.csv' OUT=WORK.productos DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

PROC SQL;
  CREATE TABLE WORK.codigos_100 AS
  SELECT codigo, descripcion, precio
  FROM WORK.productos
  WHERE codigo LIKE 'PRD-10_'
  ORDER BY codigo;
QUIT;
