PROC IMPORT DATAFILE='.../entradas/ventas.csv' OUT=WORK.ventas DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;
PROC EXPORT DATA=WORK.ventas OUTFILE='.../salida/ventas.xlsx' DBMS=XLSX REPLACE;
  SHEET='Resumen';
RUN;
