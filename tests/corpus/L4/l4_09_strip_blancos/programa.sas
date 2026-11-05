/* Caso l4_09_strip_blancos: STRIP quita blancos de ambos lados; un campo en blanco queda vacio.
   Entradas: entradas/TEXTOS_L4_09.csv. Salida: WORK.TEXTOS_LIMPIOS. Datos ficticios. */

PROC IMPORT DATAFILE='.../entradas/TEXTOS_L4_09.csv' OUT=WORK.TEXTOS_L4_09 DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

/* Etiqueta: Quita blancos del texto */
DATA WORK.TEXTOS_LIMPIOS;
  SET WORK.TEXTOS_L4_09;
  TEXTO_LIMPIO=strip(TEXTO);
RUN;

PROC EXPORT DATA=WORK.TEXTOS_LIMPIOS OUTFILE='.../salida/TEXTOS_LIMPIOS.csv' DBMS=CSV REPLACE;
RUN;
