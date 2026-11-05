/* Caso l6_07_retain_contador: RETAIN conserva el contador entre filas y FIRST.DEPTO lo reinicia.
   Entradas: entradas/EMPLEADOS.csv (ordenada por DEPTO). Salida: WORK.EMPLEADOS_NUMERADOS.
   Datos ficticios. Pendiente de revision: la pagina de RETAIN no se pudo consultar. */

PROC IMPORT DATAFILE='.../entradas/EMPLEADOS.csv' OUT=WORK.EMPLEADOS DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

/* Etiqueta: Numera empleados dentro de cada departamento */
DATA WORK.EMPLEADOS_NUMERADOS;
  SET WORK.EMPLEADOS;
  BY DEPTO;
  RETAIN CONTADOR 0;
  IF FIRST.DEPTO THEN CONTADOR=0;
  CONTADOR+1;
RUN;

PROC EXPORT DATA=WORK.EMPLEADOS_NUMERADOS OUTFILE='.../salida/EMPLEADOS_NUMERADOS.csv'
  DBMS=CSV REPLACE;
RUN;
