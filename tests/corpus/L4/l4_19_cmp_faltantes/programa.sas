/* Caso l4_19_cmp_faltantes: en una comparacion, el faltante numerico es menor que cualquier
   numero. Entradas: entradas/SALDOS_L4_19.csv. Salida: WORK.SALDOS_MARCADOS. Datos ficticios.
   Esta regla NO es la de PROC SQL (ver DIFERENCIAS.md). */

PROC IMPORT DATAFILE='.../entradas/SALDOS_L4_19.csv' OUT=WORK.SALDOS_L4_19 DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

/* Etiqueta: Marca saldos bajos y faltantes */
DATA WORK.SALDOS_MARCADOS;
  SET WORK.SALDOS_L4_19;
  BAJO_500 = (SALDO < 500);
  ES_FALTANTE = missing(SALDO);
RUN;

PROC EXPORT DATA=WORK.SALDOS_MARCADOS OUTFILE='.../salida/SALDOS_MARCADOS.csv'
  DBMS=CSV REPLACE;
RUN;
