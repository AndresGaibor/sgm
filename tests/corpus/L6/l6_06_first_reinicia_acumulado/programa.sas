/* Caso l6_06_first_reinicia_acumulado: el acumulado por departamento se reinicia en FIRST.DEPTO.
   Entradas: entradas/PAGOS_DEPTO.csv (ordenada por DEPTO). Salida: WORK.PAGOS_ACUMULADOS.
   Datos ficticios. Pendiente de revision: la retencion de la sentencia suma no se consulto. */

PROC IMPORT DATAFILE='.../entradas/PAGOS_DEPTO.csv' OUT=WORK.PAGOS_DEPTO DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

/* Etiqueta: Pagos acumulados por departamento */
DATA WORK.PAGOS_ACUMULADOS;
  SET WORK.PAGOS_DEPTO;
  BY DEPTO;
  IF FIRST.DEPTO THEN ACUM=0;
  ACUM+PAGO;
RUN;

PROC EXPORT DATA=WORK.PAGOS_ACUMULADOS OUTFILE='.../salida/PAGOS_ACUMULADOS.csv'
  DBMS=CSV REPLACE;
RUN;
