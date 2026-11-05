/* Caso l6_02_merge_muchos_a_muchos: MERGE con llaves repetidas en ambos lados. La salida no es
   un producto cartesiano (ejemplo de support.sas.com/kb/24/752.html). Entradas: entradas/ONE.csv
   y entradas/TWO.csv. Salida: WORK.BOTH. Datos ficticios con la forma del ejemplo. */

PROC IMPORT DATAFILE='.../entradas/ONE.csv' OUT=WORK.ONE DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

PROC IMPORT DATAFILE='.../entradas/TWO.csv' OUT=WORK.TWO DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

/* Etiqueta: Une frutas y colores por id */
DATA WORK.BOTH;
  MERGE WORK.ONE WORK.TWO;
  BY id;
RUN;

PROC EXPORT DATA=WORK.BOTH OUTFILE='.../salida/BOTH.csv' DBMS=CSV REPLACE;
RUN;
