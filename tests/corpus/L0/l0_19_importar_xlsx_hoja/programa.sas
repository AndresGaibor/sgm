PROC IMPORT DATAFILE='.../entradas/ventas.xlsx' OUT=WORK.ventas DBMS=XLSX REPLACE;
  SHEET='Datos';
  GETNAMES=YES;
RUN;
DATA WORK.total;
  SET WORK.ventas;
  total = unidades * precio;
  KEEP sku total;
RUN;
