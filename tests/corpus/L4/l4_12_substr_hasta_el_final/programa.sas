/* Caso l4_12_substr_hasta_el_final: SUBSTR sin longitud llega hasta el final del valor.
   Entradas: entradas/PRODUCTOS_L4_12.csv. Salida: WORK.CODIGOS_NUMERO. Datos ficticios. */

PROC IMPORT DATAFILE='.../entradas/PRODUCTOS_L4_12.csv' OUT=WORK.PRODUCTOS_L4_12 DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

/* Etiqueta: Toma la parte numerica del codigo */
DATA WORK.CODIGOS_NUMERO;
  SET WORK.PRODUCTOS_L4_12;
  NUMERO=substr(CODIGO, 4);
RUN;

PROC EXPORT DATA=WORK.CODIGOS_NUMERO OUTFILE='.../salida/CODIGOS_NUMERO.csv' DBMS=CSV REPLACE;
RUN;
