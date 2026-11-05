/* Caso l1_12_filtro_tildes: filtra productos por descripciones con tilde o Ñ, con IN.
   Entrada: entradas/productos.csv. Salida: WORK.lapices.
   La ruta '...' es un marcador; el oraculo lee las entradas de la carpeta del caso. */

PROC IMPORT DATAFILE='.../entradas/productos.csv' OUT=WORK.productos DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

PROC SQL;
  CREATE TABLE WORK.lapices AS
  SELECT codigo, descripcion, precio
  FROM WORK.productos
  WHERE descripcion IN ('Lápiz', 'Ñandú escolar')
  ORDER BY codigo;
QUIT;
