DATA WORK.fechas;
  INFILE '.../entradas/fechas.txt' DLM=';' DSD MISSOVER;
  INPUT id :$1. d1 :YYMMDD10. d2 :DDMMYY10. d3 :DATE9. d4 :ANYDTDTE10.;
RUN;

PROC EXPORT DATA=WORK.fechas OUTFILE='/datos/fechas.csv' DBMS=CSV REPLACE;
RUN;
