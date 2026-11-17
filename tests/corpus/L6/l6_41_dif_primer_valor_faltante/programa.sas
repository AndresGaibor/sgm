/* Caso l6_41_dif_primer_valor_faltante (PENDIENTE): DIF(x) = x - LAG(x) (lefunctionsref, p. 663).
   El primer valor falta porque LAG empieza con un faltante. Entradas:
   entradas/VALORES_L6_41.csv. Salida: WORK.DIF_L6_41. Datos ficticios. */

PROC IMPORT DATAFILE='.../entradas/VALORES_L6_41.csv' OUT=WORK.VALORES_L6_41 DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

DATA WORK.DIF_L6_41;
  SET WORK.VALORES_L6_41;
  D = DIF(X);
RUN;

PROC EXPORT DATA=WORK.DIF_L6_41 OUTFILE='.../salida/DIF_L6_41.csv' DBMS=CSV REPLACE;
RUN;
