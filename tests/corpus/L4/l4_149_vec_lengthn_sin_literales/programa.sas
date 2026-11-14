/* Caso l4_149_vec_lengthn_sin_literales: vector de semántica SAS verificado por el oráculo. */
DATA WORK.ENTRADA_L4;
  INFILE '.../entradas/ENTRADA_L4.csv' DSD DLM=',' FIRSTOBS=2 TRUNCOVER;
  INPUT TEXTO : $CHAR1.;
RUN;

DATA WORK.RESULTADO_L4;
  SET WORK.ENTRADA_L4;
  RESULTADO=lengthn(TEXTO);
RUN;

PROC EXPORT DATA=WORK.RESULTADO_L4 OUTFILE='.../salida/RESULTADO_L4.csv'
  DBMS=CSV REPLACE;
RUN;
