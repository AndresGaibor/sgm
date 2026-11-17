/* MEANS NWAY: faltantes por VAR y salida con nombres explícitos; proc.pdf, pp. 1571–1573. */
PROC IMPORT DATAFILE='.../entradas/ventas.csv' OUT=WORK.ventas DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;
PROC MEANS DATA=WORK.ventas NOPRINT NWAY;
  CLASS region;
  VAR monto;
  OUTPUT OUT=WORK.res(DROP=_TYPE_ _FREQ_) SUM=total MEAN=prom N=n;
RUN;
