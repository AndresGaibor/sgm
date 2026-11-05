/* Caso l2_03_join_dos_columnas_en_on: une ventas con metas por cliente y canal. La condición del ON
   tiene dos columnas. Las metas tienen un solo registro por par, así que la unión no repite filas.
   Entradas: entradas/ventas.csv y entradas/metas.csv. Salida: WORK.ventas_vs_meta. La ruta '...' es
   un marcador; el oraculo lee las entradas de la carpeta del caso. */

PROC IMPORT DATAFILE='.../entradas/ventas.csv' OUT=WORK.VENTAS DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

PROC IMPORT DATAFILE='.../entradas/metas.csv' OUT=WORK.METAS DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

/* Etiqueta: Ventas contra meta por cliente y canal */
PROC SQL;
  CREATE TABLE WORK.ventas_vs_meta AS
  SELECT v.id_venta, v.id_cliente, v.canal, v.monto, m.meta
  FROM WORK.ventas v
  INNER JOIN WORK.metas m
  ON ( v.id_cliente = m.id_cliente AND v.canal = m.canal );
QUIT;

PROC EXPORT DATA=WORK.ventas_vs_meta OUTFILE='.../salida/ventas_vs_meta.csv'
  DBMS=CSV REPLACE;
RUN;
