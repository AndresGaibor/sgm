/* Caso l4_14_scan_palabra: SCAN con delimitadores por omision; los consecutivos y los del
   principio no cuentan. Entradas: entradas/FRASES_L4_14.csv. Salida: WORK.FRASES_PALABRA.
   Datos ficticios. */

PROC IMPORT DATAFILE='.../entradas/FRASES_L4_14.csv' OUT=WORK.FRASES_L4_14 DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

/* Etiqueta: Segunda palabra de cada texto */
DATA WORK.FRASES_PALABRA;
  SET WORK.FRASES_L4_14;
  PALABRA_2=scan(TEXTO, 2);
RUN;

PROC EXPORT DATA=WORK.FRASES_PALABRA OUTFILE='.../salida/FRASES_PALABRA.csv' DBMS=CSV REPLACE;
RUN;
