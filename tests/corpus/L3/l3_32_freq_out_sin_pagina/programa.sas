/* Sin esperado: falta la página que demuestra el contrato de TABLES OUT=. */
PROC IMPORT DATAFILE='.../entradas/ventas.csv' OUT=WORK.ventas DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;
PROC FREQ DATA=WORK.ventas;
  TABLES region / OUT=WORK.fr;
RUN;
