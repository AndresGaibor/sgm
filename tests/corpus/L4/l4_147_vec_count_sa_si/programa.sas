/* Caso l4_147_vec_count_sa_si: vector de semántica SAS verificado por el oráculo. */
DATA WORK.ENTRADA_L4;
  INFILE '.../entradas/ENTRADA_L4.csv' DSD DLM=',' FIRSTOBS=2 TRUNCOVER;
  INPUT TEXTO : $CHAR3.;
RUN;

DATA WORK.RESULTADO_L4;
  SET WORK.ENTRADA_L4;
  RESULTADO=count(TEXTO, 'a', 'i');
RUN;

PROC EXPORT DATA=WORK.RESULTADO_L4 OUTFILE='.../salida/RESULTADO_L4.csv'
  DBMS=CSV REPLACE;
RUN;
