/* Caso l4_01_input_left_numerico: la cuenta llega como texto con blancos iniciales. Un DATA step
   la convierte con input(left(...), 30.). Entradas: entradas/CUENTAS_L4_01.csv. Salida: WORK.CUENTAS_CONVERTIDAS.
   Datos ficticios. Esperado: capa B (vectores left-01, input-01 y input-07). */

PROC IMPORT DATAFILE='.../entradas/CUENTAS_L4_01.csv' OUT=WORK.CUENTAS_L4_01 DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

/* Etiqueta: Convierte VAR7 a numero de cuenta */
DATA WORK.CUENTAS_CONVERTIDAS;
  SET WORK.CUENTAS_L4_01;
  NRO_CTA=input(left(VAR7), 30.);
RUN;

PROC EXPORT DATA=WORK.CUENTAS_CONVERTIDAS OUTFILE='.../salida/CUENTAS_CONVERTIDAS.csv'
  DBMS=CSV REPLACE;
RUN;
