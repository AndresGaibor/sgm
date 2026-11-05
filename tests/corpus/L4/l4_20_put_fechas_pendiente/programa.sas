/* Caso l4_20_put_fechas_pendiente (PENDIENTE): PUT y fechas con MDY e INPUT ... YYMMDD10.
   No hay vector de esas funciones en tests/corpus/semantica/vectores.yaml; el caso no tiene
   esperado hasta que la capa B las implemente. Entradas: entradas/FECHAS_L4_20.csv. Salida:
   WORK.FECHAS_TEXTO. Datos ficticios. */

PROC IMPORT DATAFILE='.../entradas/FECHAS_L4_20.csv' OUT=WORK.FECHAS_L4_20 DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

/* Etiqueta: Convierte la fecha de texto a fecha SAS y de vuelta a texto */
DATA WORK.FECHAS_TEXTO;
  SET WORK.FECHAS_L4_20;
  FECHA_SAS=input(FECHA, yymmdd10.);
  FECHA_TXT=put(FECHA_SAS, date9.);
  ANIO_FIN=mdy(12, 31, 2026);
RUN;

PROC EXPORT DATA=WORK.FECHAS_TEXTO OUTFILE='.../salida/FECHAS_TEXTO.csv' DBMS=CSV REPLACE;
RUN;
