/* Caso l4_141_vec_translate_sxy_sab: vector de semántica SAS verificado por el oráculo. */
DATA WORK.ENTRADA_L4;
  INFILE '.../entradas/ENTRADA_L4.csv' DSD DLM=',' FIRSTOBS=2 TRUNCOVER;
  INPUT TEXTO : $CHAR3.;
RUN;

DATA WORK.RESULTADO_L4;
  SET WORK.ENTRADA_L4;
  RESULTADO=translate(TEXTO, 'xy', 'ab');
RUN;

PROC EXPORT DATA=WORK.RESULTADO_L4 OUTFILE='.../salida/RESULTADO_L4.csv'
  DBMS=CSV REPLACE;
RUN;
