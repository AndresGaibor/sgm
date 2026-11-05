/* Caso l4_04_compress_blancos: COMPRESS sin lista quita los blancos. Entradas:
   entradas/NOMBRES_L4_04.csv. Salida: WORK.NOMBRES_LIMPIOS. Datos ficticios. */

PROC IMPORT DATAFILE='.../entradas/NOMBRES_L4_04.csv' OUT=WORK.NOMBRES_L4_04 DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

/* Etiqueta: Clave sin blancos */
DATA WORK.NOMBRES_LIMPIOS;
  SET WORK.NOMBRES_L4_04;
  CLAVE=compress(DESCRIPCION);
RUN;

PROC EXPORT DATA=WORK.NOMBRES_LIMPIOS OUTFILE='.../salida/NOMBRES_LIMPIOS.csv'
  DBMS=CSV REPLACE;
RUN;
