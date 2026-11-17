/* SUMMARY sin CLASS: una fila global, proc.pdf, pp. 2549 y 1573. */
PROC IMPORT DATAFILE='.../entradas/ventas.csv' OUT=WORK.ventas DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;
PROC SUMMARY DATA=WORK.ventas;
  VAR monto;
  OUTPUT OUT=WORK.tot(DROP=_TYPE_ _FREQ_) SUM=total MIN=minimo MAX=maximo N=n;
RUN;
