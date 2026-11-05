/* Caso l3_10_suma_decimales: suma de importes con dos decimales por canal. Las sumas en coma flotante
   pueden diferir en la última cifra; la comparación usa la tolerancia del caso.
   Entradas: entradas/facturas.csv. Salida: WORK.total_por_canal. La ruta '...' es un marcador; el
   oraculo lee las entradas de la carpeta del caso. */

PROC IMPORT DATAFILE='.../entradas/facturas.csv' OUT=WORK.FACTURAS DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

/* Etiqueta: Total de importes por canal */
PROC SQL;
  CREATE TABLE WORK.total_por_canal AS
  SELECT canal, COUNT(*) AS facturas, SUM(importe) AS total
  FROM WORK.facturas
  GROUP BY canal
  ORDER BY canal;
QUIT;

PROC EXPORT DATA=WORK.total_por_canal OUTFILE='.../salida/total_por_canal.csv'
  DBMS=CSV REPLACE;
RUN;
