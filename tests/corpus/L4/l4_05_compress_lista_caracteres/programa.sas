/* Caso l4_05_compress_lista_caracteres: COMPRESS con lista de caracteres a quitar. Entradas:
   entradas/REFERENCIAS_L4_05.csv. Salida: WORK.REFERENCIAS_LIMPIAS. Datos ficticios. */

PROC IMPORT DATAFILE='.../entradas/REFERENCIAS_L4_05.csv' OUT=WORK.REFERENCIAS_L4_05 DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

/* Etiqueta: Quita los digitos 1 y 2 de la referencia */
DATA WORK.REFERENCIAS_LIMPIAS;
  SET WORK.REFERENCIAS_L4_05;
  REF_LIMPIA=compress(REF, '12');
RUN;

PROC EXPORT DATA=WORK.REFERENCIAS_LIMPIAS OUTFILE='.../salida/REFERENCIAS_LIMPIAS.csv'
  DBMS=CSV REPLACE;
RUN;
