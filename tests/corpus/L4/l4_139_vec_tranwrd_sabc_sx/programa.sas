/* Caso l4_139_vec_tranwrd_sabc_sx: vector de semántica SAS verificado por el oráculo. */
DATA WORK.ENTRADA_L4;
  INFILE '.../entradas/ENTRADA_L4.csv' DSD DLM=',' FIRSTOBS=2 TRUNCOVER;
  INPUT TEXTO : $CHAR11.;
RUN;

DATA WORK.RESULTADO_L4;
  SET WORK.ENTRADA_L4;
  RESULTADO=tranwrd(TEXTO, 'abc', 'x');
RUN;

PROC EXPORT DATA=WORK.RESULTADO_L4 OUTFILE='.../salida/RESULTADO_L4.csv'
  DBMS=CSV REPLACE;
RUN;
