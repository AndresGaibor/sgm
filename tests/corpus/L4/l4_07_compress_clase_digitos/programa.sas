/* Caso l4_07_compress_clase_digitos: el modificador D quita los digitos. Entradas:
   entradas/PLACAS_L4_07.csv. Salida: WORK.PLACAS_SIN_DIGITOS. Datos ficticios. */

PROC IMPORT DATAFILE='.../entradas/PLACAS_L4_07.csv' OUT=WORK.PLACAS_L4_07 DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

/* Etiqueta: Quita los digitos del codigo */
DATA WORK.PLACAS_SIN_DIGITOS;
  SET WORK.PLACAS_L4_07;
  SOLO_LETRAS=compress(CODIGO, '', 'd');
RUN;

PROC EXPORT DATA=WORK.PLACAS_SIN_DIGITOS OUTFILE='.../salida/PLACAS_SIN_DIGITOS.csv'
  DBMS=CSV REPLACE;
RUN;
