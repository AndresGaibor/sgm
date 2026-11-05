/* Caso l6_04_merge_tres_conjuntos: MERGE de tres conjuntos con BY; cada grupo sale tantas veces
   como su conjunto con mas filas. Entradas: entradas/CAFE.csv, SNACK.csv y VENDING.csv. Salida:
   WORK.CONSUMO. Datos ficticios. */

PROC IMPORT DATAFILE='.../entradas/CAFE.csv' OUT=WORK.CAFE DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

PROC IMPORT DATAFILE='.../entradas/SNACK.csv' OUT=WORK.SNACK DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

PROC IMPORT DATAFILE='.../entradas/VENDING.csv' OUT=WORK.VENDING DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

/* Etiqueta: Consumo por cliente */
DATA WORK.CONSUMO;
  MERGE WORK.CAFE WORK.SNACK WORK.VENDING;
  BY id;
RUN;

PROC EXPORT DATA=WORK.CONSUMO OUTFILE='.../salida/CONSUMO.csv' DBMS=CSV REPLACE;
RUN;
