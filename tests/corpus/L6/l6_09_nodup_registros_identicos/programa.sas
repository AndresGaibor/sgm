/* Caso l6_09_nodup_registros_identicos: PROC SORT con NODUP quita los registros identicos.
   Entradas: entradas/VENTAS_DUP.csv. Salida: WORK.VENTAS_SIN_REPETIR. Datos ficticios.
   Pendiente de revision: la regla viene de fuentes secundarias. */

PROC IMPORT DATAFILE='.../entradas/VENTAS_DUP.csv' OUT=WORK.VENTAS_DUP DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

/* Etiqueta: Quita registros repetidos comparando todas las variables */
PROC SORT DATA=WORK.VENTAS_DUP OUT=WORK.VENTAS_SIN_REPETIR NODUP;
  BY _ALL_;
RUN;

PROC EXPORT DATA=WORK.VENTAS_SIN_REPETIR OUTFILE='.../salida/VENTAS_SIN_REPETIR.csv'
  DBMS=CSV REPLACE;
RUN;
