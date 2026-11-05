/* Caso l4_15_scan_delimitador_fuera_de_rango: SCAN con coma como delimitador; si no hay palabra
   n, el resultado es un blanco. Entradas: entradas/CAMPOS_L4_15.csv. Salida:
   WORK.CAMPOS_EXTRAIDOS. Datos ficticios. */

PROC IMPORT DATAFILE='.../entradas/CAMPOS_L4_15.csv' OUT=WORK.CAMPOS_L4_15 DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

/* Etiqueta: Segundo campo separado por comas */
DATA WORK.CAMPOS_EXTRAIDOS;
  SET WORK.CAMPOS_L4_15;
  CAMPO_2=scan(TEXTO, 2, ',');
RUN;

PROC EXPORT DATA=WORK.CAMPOS_EXTRAIDOS OUTFILE='.../salida/CAMPOS_EXTRAIDOS.csv'
  DBMS=CSV REPLACE;
RUN;
