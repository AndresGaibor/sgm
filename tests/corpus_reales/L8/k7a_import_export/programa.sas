/* Etiqueta: Importar Homologacion TDOC */
PROC IMPORT 
DATAFILE='\\sbcldwpsgf01\FILE_VSPC_FINANZAS\Homologacion_tpo_dto.xlsx' 
DBMS=EXCELCS OUT=WORK.IMPORT_HOMOLOGACION_TPO_DOC REPLACE;
TEXTSIZE=32767;
PORT=9621;
SERVER='sbcldwpsgf01';
SHEET='';
RUN;

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
