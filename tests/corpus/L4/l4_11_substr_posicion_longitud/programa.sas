/* Caso l4_11_substr_posicion_longitud: SUBSTR con posicion y longitud; si la longitud pasa el
   final, llega al final. Entradas: entradas/CODIGOS_L4_11.csv. Salida: WORK.CODIGOS_PARTIDOS.
   Datos ficticios. */

PROC IMPORT DATAFILE='.../entradas/CODIGOS_L4_11.csv' OUT=WORK.CODIGOS_L4_11 DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

/* Etiqueta: Parte el codigo en subcodigo y sufijo */
DATA WORK.CODIGOS_PARTIDOS;
  SET WORK.CODIGOS_L4_11;
  SUBCODIGO=substr(CODIGO, 2, 3);
  SUFIJO=substr(CODIGO, 4, 2);
RUN;

PROC EXPORT DATA=WORK.CODIGOS_PARTIDOS OUTFILE='.../salida/CODIGOS_PARTIDOS.csv'
  DBMS=CSV REPLACE;
RUN;
