/* Caso l6_11_merge_mas_acumulado: MERGE de zonas con ventas y acumulado por zona. Entradas:
   entradas/ZONAS.csv y entradas/VENTAS.csv (ordenadas por ZONA). Salida: WORK.VENTAS_ZONA.
   Datos ficticios. Pendiente de revision: la retencion de la sentencia suma no se consulto. */

PROC IMPORT DATAFILE='.../entradas/ZONAS.csv' OUT=WORK.ZONAS DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

PROC IMPORT DATAFILE='.../entradas/VENTAS.csv' OUT=WORK.VENTAS DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

/* Etiqueta: Ventas con el nombre de zona y acumulado por zona */
DATA WORK.VENTAS_ZONA;
  MERGE WORK.ZONAS WORK.VENTAS;
  BY ZONA;
  IF FIRST.ZONA THEN ACUM=0;
  ACUM+MONTO;
RUN;

PROC EXPORT DATA=WORK.VENTAS_ZONA OUTFILE='.../salida/VENTAS_ZONA.csv' DBMS=CSV REPLACE;
RUN;
