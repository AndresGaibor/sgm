/* Caso l4_16_trim_concat_sufijo: TRIM(x)||y quita los blancos finales antes de unir. Entradas:
   entradas/CODIGOS_L4_16.csv. Salida: WORK.CODIGOS_CON_SUFIJO. Datos ficticios. */

PROC IMPORT DATAFILE='.../entradas/CODIGOS_L4_16.csv' OUT=WORK.CODIGOS_L4_16 DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

/* Etiqueta: Une el codigo sin blancos finales al sufijo */
DATA WORK.CODIGOS_CON_SUFIJO;
  SET WORK.CODIGOS_L4_16;
  CODIGO_OK=trim(CODIGO)||'-OK';
RUN;

PROC EXPORT DATA=WORK.CODIGOS_CON_SUFIJO OUTFILE='.../salida/CODIGOS_CON_SUFIJO.csv'
  DBMS=CSV REPLACE;
RUN;
