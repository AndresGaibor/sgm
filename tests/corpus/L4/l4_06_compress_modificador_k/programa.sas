/* Caso l4_06_compress_modificador_k: con la K de COMPRESS solo se conservan los caracteres de la
   lista. Entradas: entradas/CLAVES_L4_06.csv. Salida: WORK.CLAVES_K. Datos ficticios. */

PROC IMPORT DATAFILE='.../entradas/CLAVES_L4_06.csv' OUT=WORK.CLAVES_L4_06 DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

/* Etiqueta: Conserva solo A, B, C y D de la clave */
DATA WORK.CLAVES_K;
  SET WORK.CLAVES_L4_06;
  CLAVE_K=compress(CLAVE, 'ABCD', 'k');
RUN;

PROC EXPORT DATA=WORK.CLAVES_K OUTFILE='.../salida/CLAVES_K.csv' DBMS=CSV REPLACE;
RUN;
