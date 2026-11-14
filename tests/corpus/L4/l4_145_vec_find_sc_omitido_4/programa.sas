/* Caso l4_145_vec_find_sc_omitido_4: vector de semántica SAS verificado por el oráculo. */
DATA WORK.ENTRADA_L4;
  INFILE '.../entradas/ENTRADA_L4.csv' DSD DLM=',' FIRSTOBS=2 TRUNCOVER;
  INPUT TEXTO : $CHAR6.;
RUN;

DATA WORK.RESULTADO_L4;
  SET WORK.ENTRADA_L4;
  RESULTADO=find(TEXTO, 'c', , 4);
RUN;

PROC EXPORT DATA=WORK.RESULTADO_L4 OUTFILE='.../salida/RESULTADO_L4.csv'
  DBMS=CSV REPLACE;
RUN;
