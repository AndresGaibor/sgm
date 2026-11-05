/* Caso l4_08_compress_ignora_mayusculas: el modificador I quita la letra en mayuscula y en
   minuscula. Entradas: entradas/CODIGOS_L4_08.csv. Salida: WORK.CODIGOS_SIN_A. Datos ficticios. */

PROC IMPORT DATAFILE='.../entradas/CODIGOS_L4_08.csv' OUT=WORK.CODIGOS_L4_08 DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

/* Etiqueta: Quita la letra a sin importar mayusculas */
DATA WORK.CODIGOS_SIN_A;
  SET WORK.CODIGOS_L4_08;
  COD_SIN_A=compress(COD, 'a', 'i');
RUN;

PROC EXPORT DATA=WORK.CODIGOS_SIN_A OUTFILE='.../salida/CODIGOS_SIN_A.csv' DBMS=CSV REPLACE;
RUN;
