/* Caso l4_13_substrn_numerico: SUBSTRN sobre un numero toma sus caracteres sin blancos iniciales.
   Entradas: entradas/SALDOS_L4_13.csv. Salida: WORK.SALDOS_TEXTO. Datos ficticios. */

PROC IMPORT DATAFILE='.../entradas/SALDOS_L4_13.csv' OUT=WORK.SALDOS_L4_13 DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

/* Etiqueta: Extrae digitos del saldo numerico como texto */
DATA WORK.SALDOS_TEXTO;
  SET WORK.SALDOS_L4_13;
  SALDO_TXT=substrn(SALDO, 2, 6);
RUN;

PROC EXPORT DATA=WORK.SALDOS_TEXTO OUTFILE='.../salida/SALDOS_TEXTO.csv' DBMS=CSV REPLACE;
RUN;
