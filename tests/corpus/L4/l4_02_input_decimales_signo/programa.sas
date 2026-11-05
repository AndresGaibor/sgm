/* Caso l4_02_input_decimales_signo: importes como texto con y sin punto decimal, con signo.
   Con punto, el informat ignora d; sin punto, d=2 da los decimales. Entradas:
   entradas/IMPORTES_L4_02.csv. Salida: WORK.IMPORTES_CONVERTIDOS. Datos ficticios. */

PROC IMPORT DATAFILE='.../entradas/IMPORTES_L4_02.csv' OUT=WORK.IMPORTES_L4_02 DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

/* Etiqueta: Convierte el importe con informat 8.2 */
DATA WORK.IMPORTES_CONVERTIDOS;
  SET WORK.IMPORTES_L4_02;
  IMP_NUM=input(IMPORTE, 8.2);
RUN;

PROC EXPORT DATA=WORK.IMPORTES_CONVERTIDOS OUTFILE='.../salida/IMPORTES_CONVERTIDOS.csv'
  DBMS=CSV REPLACE;
RUN;
