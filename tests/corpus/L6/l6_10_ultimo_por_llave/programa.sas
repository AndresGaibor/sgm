/* Caso l6_10_ultimo_por_llave: IF LAST.ID conserva el ultimo movimiento de cada ID. Entradas:
   entradas/MOVIMIENTOS.csv (ordenada por ID). Salida: WORK.SALDO_FINAL. Datos ficticios. */

PROC IMPORT DATAFILE='.../entradas/MOVIMIENTOS.csv' OUT=WORK.MOVIMIENTOS DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

/* Etiqueta: Ultimo movimiento por ID */
DATA WORK.SALDO_FINAL;
  SET WORK.MOVIMIENTOS;
  BY ID;
  IF LAST.ID;
RUN;

PROC EXPORT DATA=WORK.SALDO_FINAL OUTFILE='.../salida/SALDO_FINAL.csv' DBMS=CSV REPLACE;
RUN;
