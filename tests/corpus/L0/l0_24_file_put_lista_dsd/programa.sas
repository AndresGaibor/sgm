PROC IMPORT DATAFILE='.../entradas/ventas.csv' OUT=WORK.ventas DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

DATA _NULL_;
  SET WORK.ventas;
  FILE '.../salida/ventas.txt' DSD DLM='|';
  PUT id nombre monto;
RUN;
