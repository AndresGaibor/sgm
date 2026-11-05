/* Caso l4_03_input_punto_y_texto_invalido: un punto solo y un texto no numerico se vuelven
   faltantes en input. Entradas: entradas/CODIGOS_L4_03.csv. Salida: WORK.CODIGOS_VALIDOS.
   Datos ficticios. */

PROC IMPORT DATAFILE='.../entradas/CODIGOS_L4_03.csv' OUT=WORK.CODIGOS_L4_03 DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

/* Etiqueta: Convierte el codigo a numero; los no numericos quedan faltantes */
DATA WORK.CODIGOS_VALIDOS;
  SET WORK.CODIGOS_L4_03;
  CODIGO_NUM=input(CODIGO, 6.2);
RUN;

PROC EXPORT DATA=WORK.CODIGOS_VALIDOS OUTFILE='.../salida/CODIGOS_VALIDOS.csv'
  DBMS=CSV REPLACE;
RUN;
