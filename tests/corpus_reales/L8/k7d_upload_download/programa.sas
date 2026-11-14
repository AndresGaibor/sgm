%let server=sbcldwpsgf01 7551;
OPTIONS REMOTE=server COMAMID=TCP;
signon
user=&sysuserid pass='***';
RSUBMIT server;

/*PROCESO PARA CARGAR EL ARCHIVO DESDE PCFILE HACIA UNA RUTA TEMPORAL EN SAS*/
PROC DOWNLOAD INFILE='\\sbcldwpsgf01\FILE_VSPC_FINANZAS\Base_datos_Nequi.csv'
OUTFILE='/work_sasstudio/pcfiles/Base_datos_Nequi.csv';
endrsubmit;
signoff;
run;

/*PROCESO PARA IMPORTAR EL ARHCIVO DESDE LA RUTA TEMPORAL HACIA UNA LIBRERIA DE SAS*/
proc import datafile='/work_sasstudio/pcfiles/Base_datos_Nequi.csv' out=WORK.BASE_CLIENTES_NEQUI
dbms=dlm replace;
delimiter=';';
getnames=NO;
run;

/* Etiqueta: Exp FA no vigentes */
proc export data=WORK.FA_NO_VIGENTES_AHO outfile="/work_sasstudio/pcfiles/FA_NO_VIGENTES_AHO.csv"
dbms=dlm replace;
delimiter=';';
run;

%let server=sbcldwpsgf01 7551;
OPTIONS REMOTE=server COMAMID=TCP;
signon
user=&sysuserid pass='***';
RSUBMIT server;
PROC UPLOAD INFILE="/work_sasstudio/pcfiles/FA_NO_VIGENTES_AHO.csv"
OUTFILE="\\sbcldwpsgf01\FILE_VSPC_FINANZAS\GST_Informacion_Exogena\RESULTADOS\FA_NO_VIGENTES_AHO.csv";
endrsubmit;
signoff;
run;
