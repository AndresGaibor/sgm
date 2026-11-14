DATA WORK.limpio;
  INFILE '.../entradas/crudo.txt' DLM=';' DSD MISSOVER;
  INPUT a :COMMA12.2 b :DOLLAR10. c :8.2;
RUN;

PROC EXPORT DATA=WORK.limpio OUTFILE='/datos/limpio.csv' DBMS=CSV REPLACE;
RUN;
