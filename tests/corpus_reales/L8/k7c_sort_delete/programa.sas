data work.temporal;
format Codigo_Pais $10.;
set WORK.IMPORT_CODIGOS_PAIS(rename=Codigo_Pais=Codigo_Pais_old);
Codigo_Pais=COMPRESS(input(left(Codigo_Pais_old), 10.));
drop Codigo_Pais_old;
run;

data WORK.IMPORT_CODIGOS_PAIS;
set work.temporal;
run;

proc delete data=work.temporal;
run;

proc sort data=WORK.SABANA_COMPLETA_INFO_CLI_NEQUI
out=WORK.SABANA_DIR_UNICA_NEQUI nodupkey equals;
by NRO_DOC NRO_CTA;
run;
