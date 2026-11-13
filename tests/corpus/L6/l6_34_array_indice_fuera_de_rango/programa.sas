/* Caso l6_34_array_indice_fuera_de_rango (PENDIENTE): ARRAY con tres elementos y un DO que
   llega a 4. SAS da un error de ejecución (lrcon, p. 192) y detiene el paso; no se inventa
   un valor para a{4}. Entradas: entradas/VALORES_L6_34.csv. Salida: WORK.ARREGLO_L6_34.
   Datos ficticios. */

PROC IMPORT DATAFILE='.../entradas/VALORES_L6_34.csv' OUT=WORK.VALORES_L6_34 DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

DATA WORK.ARREGLO_L6_34;
  SET WORK.VALORES_L6_34;
  ARRAY A{3} X1 X2 X3;
  DO I = 1 TO 4;
    A{I} = A{I} * 2;
  END;
RUN;

PROC EXPORT DATA=WORK.ARREGLO_L6_34 OUTFILE='.../salida/ARREGLO_L6_34.csv' DBMS=CSV REPLACE;
RUN;
