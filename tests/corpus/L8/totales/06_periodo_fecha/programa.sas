/* Caso L8-06: periodo y fecha de validación; nombre de salida con la fecha.               */
/* Rebanada de "Importar Validación Fecha", "Validar_mes_año", "Conv a texto fecha          */
/* validacion" y "Concatenar fecha de validación" de client_large.sas. Datos ficticios.      */
/* El periodo sale del Excel de validación, no de Impala.                                    */

/* Etiqueta: Importar Validación Fecha */
PROC IMPORT DATAFILE='/work_sasstudio/pcfiles/Validacion_fecha.xlsx'
DBMS=EXCELCS OUT=WORK.VALIDACION_FECHA REPLACE;
SHEET='';
RUN;

/* Etiqueta: Importar origen AHO */
proc import datafile='/work_sasstudio/pcfiles/origen_aho.csv' out=WORK.IMPORT_ORIGEN_AHO
dbms=dlm replace;
delimiter=';';
getnames=NO;
run;

/* Etiqueta: Nombres de columnas AHO */
PROC SQL;
CREATE TABLE WORK.ORIGEN_AHO AS
SELECT VAR1 AS ANIO_PROCESO, VAR2 AS MES_PROCESO, VAR3 AS CODIGO_OFICINA,
       VAR4 AS RELACION, VAR5 AS CODIGO_SUCURSAL, VAR6 AS TIPO_CTA,
       VAR7 AS NRO_CTA, VAR8 AS LLAVE_NOMBRE, VAR9 AS TIPO_DOC,
       VAR10 AS NRO_DOC, VAR11 AS GMF, VAR12 AS VAL_CRED_MES,
       VAR13 AS NRO_CRED_MES, VAR14 AS PROM_CRED_MES, VAR15 AS MED_CRED_MES,
       VAR16 AS VAL_DEB_MES, VAR17 AS NRO_DEB_MES, VAR18 AS PROM_DEB_MES,
       VAR19 AS MED_SALDO_CTA, VAR20 AS PROM_SALDO_CTA, VAR21 AS MAX_SALDO_CTA,
       VAR22 AS MIN_SALDO_CTA, VAR23 AS FIN_SALDO_CTA
FROM WORK.IMPORT_ORIGEN_AHO;
QUIT;

/* Etiqueta: Validar_mes_año */
/* Macrovariables de año, mes y día desde el Excel de validación. */
PROC SQL;
SELECT 'AÑO'n INTO :ANIO FROM WORK.VALIDACION_FECHA;
SELECT MES INTO :MES FROM WORK.VALIDACION_FECHA;
SELECT DIA INTO :DIA FROM WORK.VALIDACION_FECHA;
QUIT;

/* Etiqueta: Conv a texto fecha validacion */
data WORK.FORMATO_TEXTO_FECHA;
set WORK.VALIDACION_FECHA;
MES_VIG = PUT(MES, Z2.);
DIA_VIG = PUT(DIA, Z2.);
run;

/* Etiqueta: Macrovariables de texto de fecha */
PROC SQL;
SELECT MES_VIG INTO :MES_TXT FROM WORK.FORMATO_TEXTO_FECHA;
SELECT DIA_VIG INTO :DIA_TXT FROM WORK.FORMATO_TEXTO_FECHA;
QUIT;

/* Etiqueta: Concatenar fecha de validación */
%let FECHA = &ANIO.&MES_TXT.&DIA_TXT.;
%put NOTE: fecha de validacion concatenada: &FECHA.;

/* Etiqueta: Saldo numérico AHO */
data WORK.ORIGEN_AHO;
set WORK.ORIGEN_AHO;
FORM_FIN_SALDO_CTA = input(left(FIN_SALDO_CTA), 20.);
run;

/* Etiqueta: Filtro de periodo AHO */
%web_drop_table(WORK.RESULTADO_AHO_PERIODO);

PROC SQL;
CREATE TABLE WORK.RESULTADO_AHO_PERIODO AS
SELECT ANIO_PROCESO, MES_PROCESO, RELACION, TIPO_CTA, NRO_CTA,
       TIPO_DOC, NRO_DOC, GMF, FORM_FIN_SALDO_CTA
FROM WORK.ORIGEN_AHO
WHERE ANIO_PROCESO = "&ANIO." AND MES_PROCESO = "&MES_TXT."
ORDER BY NRO_CTA;
QUIT;

%web_open_table(WORK.RESULTADO_AHO_PERIODO);

/* Etiqueta: Conteo del periodo AHO */
PROC SQL;
CREATE TABLE WORK.CUENTA_PERIODO_AHO AS
SELECT COUNT(*) AS NRO_REGISTROS_PERIODO,
       SUM(FORM_FIN_SALDO_CTA) AS SUMA_SALDO_PERIODO
FROM WORK.RESULTADO_AHO_PERIODO;
QUIT;

%web_open_table(WORK.CUENTA_PERIODO_AHO);

/* Etiqueta: Exportar resultado con la fecha en el nombre */
PROC EXPORT DATA=WORK.RESULTADO_AHO_PERIODO
   OUTFILE="/work_sasstudio/pcfiles/RESULTADO_AHO_&FECHA..csv"
   DBMS=CSV REPLACE;
RUN;

/* Etiqueta: Fecha de validación en tabla de control */
data WORK.CONTROL_PERIODO;
length ANIO_TXT $ 4 MES_TXT_OUT $ 2 DIA_TXT_OUT $ 2 FECHA_CONCAT $ 8;
ANIO_TXT = "&ANIO.";
MES_TXT_OUT = "&MES_TXT.";
DIA_TXT_OUT = "&DIA_TXT.";
FECHA_CONCAT = "&FECHA.";
run;

/* Etiqueta: Limpieza de tablas auxiliares */
PROC DELETE DATA=WORK.FORMATO_TEXTO_FECHA;
RUN;

/* Etiqueta: Periodo como texto AAAA-MM */
%let PERIODO = &ANIO.-&MES_TXT.;
%put NOTE: periodo de validacion: &PERIODO.;

data WORK.PERIODO_TEXTO;
length PERIODO $ 7;
PERIODO = "&PERIODO.";
run;

/* Etiqueta: Validar mes del periodo */
%macro valida_periodo(mes=, anio=);
   %if %length(&mes.) = 2 %then %do;
      %put NOTE: mes &mes. del anio &anio. tiene dos posiciones, correcto;
   %end;
   %else %do;
      %put WARNING: mes &mes. del anio &anio. no tiene dos posiciones;
   %end;
%mend valida_periodo;

%valida_periodo(mes=&MES_TXT., anio=&ANIO.);

/* Etiqueta: Meses presentes en el origen AHO */
PROC SQL;
CREATE TABLE WORK.MESES_ORIGEN_AHO AS
SELECT MES_PROCESO, COUNT(*) AS NRO_FILAS
FROM WORK.ORIGEN_AHO
GROUP BY MES_PROCESO
ORDER BY MES_PROCESO;
QUIT;

/* Etiqueta: Filas fuera del periodo AHO */
PROC SQL;
CREATE TABLE WORK.FUERA_DEL_PERIODO_AHO AS
SELECT COUNT(*) AS NRO_FILAS_FUERA
FROM WORK.ORIGEN_AHO
WHERE MES_PROCESO <> "&MES_TXT.";
QUIT;

%web_open_table(WORK.FUERA_DEL_PERIODO_AHO);
