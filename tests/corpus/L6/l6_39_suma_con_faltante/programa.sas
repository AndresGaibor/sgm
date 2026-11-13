/* Caso l6_39_suma_con_faltante (PENDIENTE): la sentencia suma `acum + x;` (lestmtsref, p. 360).
   `acum` empieza en 0, se retiene entre filas, y un faltante en x cuenta como cero. Sin emisor en
   Talend todavía: el intérprete la calcula (tests/unit/test_interprete_suma.py). Entradas:
   entradas/VALORES_L6_39.csv. Salida: WORK.SUMA_L6_39. Datos ficticios. */

PROC IMPORT DATAFILE='.../entradas/VALORES_L6_39.csv' OUT=WORK.VALORES_L6_39 DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

DATA WORK.SUMA_L6_39;
  SET WORK.VALORES_L6_39;
  acum + x;
RUN;

PROC EXPORT DATA=WORK.SUMA_L6_39 OUTFILE='.../salida/SUMA_L6_39.csv' DBMS=CSV REPLACE;
RUN;
