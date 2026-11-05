/* Etiqueta: Macrovariables */
/* Caso ficticio L8 v01. Datos inventados; las rutas y servidores no son los reales. */
%let Servidor_LZ = lz_ficticia_01;
%let m_ambiente = D;

/* Etiqueta: Ambiente de la landing zone */
%macro ambiente;
%if &m_ambiente eq D %then
%do;

/* Desarrollo */
%let lz_dsn=IMPALA;
%end;
%else %if &m_ambiente eq C %then
%do;

/* Certi */
%let lz_dsn=IMPALAC;
%end;
%else %if &m_ambiente eq P %then
%do;

/* Produccion */
%let lz_dsn=IMPALAP;
%end;
%put &lz_dsn;
%mend ambiente;

%ambiente;

/* Etiqueta: Importar Homologacion TDOC */
PROC IMPORT
DATAFILE='\\servidor_ficticio\ENTRADAS_CORPUS\Homologacion_tpo_dto.xlsx'
DBMS=EXCELCS OUT=WORK.IMPORT_HOMOLOGACION_TPO_DOC REPLACE;
TEXTSIZE=32767;
PORT=9621;
SERVER='servidor_ficticio';
SHEET='';
RUN;

/* Etiqueta: Descargar detalle CTE */
%let server=servidor_ficticio 7551;
OPTIONS REMOTE=server COMAMID=TCP;
signon
user=&sysuserid pass='***';
RSUBMIT server;

/*PROCESO PARA CARGAR EL ARCHIVO DESDE PCFILE HACIA UNA RUTA TEMPORAL EN SAS*/
PROC DOWNLOAD INFILE='\\servidor_ficticio\ENTRADAS_CORPUS\DETALLE_CTE.csv'
OUTFILE='/work_sasstudio/pcfiles/DETALLE_CTE.csv';
endrsubmit;
signoff;
run;

/* Etiqueta: Descargar detalle AHO */
OPTIONS REMOTE=server COMAMID=TCP;
signon
user=&sysuserid pass='***';
RSUBMIT server;

/*PROCESO PARA CARGAR EL ARCHIVO DESDE PCFILE HACIA UNA RUTA TEMPORAL EN SAS*/
PROC DOWNLOAD INFILE='\\servidor_ficticio\ENTRADAS_CORPUS\DETALLE_AHO.csv'
OUTFILE='/work_sasstudio/pcfiles/DETALLE_AHO.csv';
endrsubmit;
signoff;
run;

/* Etiqueta: Importar detalle por producto */
%macro importa_detalle(sufijo);
proc import datafile='/work_sasstudio/pcfiles/DETALLE_&sufijo..csv'
out=WORK.DETALLE_&sufijo replace dbms=dlm;
delimiter=';';
getnames=NO;
run;
%mend importa_detalle;

%importa_detalle(CTE);
%importa_detalle(AHO);

/* Etiqueta: Nombre columnas por producto */
%macro nombres_columnas(sufijo);
%web_drop_table(WORK.SABANA_&sufijo);

/* Código de query generado para SAS Studio por Common Query Services */

PROC SQL;
CREATE TABLE WORK.SABANA_&sufijo
AS
SELECT DETALLE_&sufijo..VAR1 AS ANIO_PROCESO, DETALLE_&sufijo..VAR2 AS MES_PROCESO,
DETALLE_&sufijo..VAR4 AS RELACION, DETALLE_&sufijo..VAR6 AS TIPO_CTA,
DETALLE_&sufijo..VAR7 AS NRO_CTA, DETALLE_&sufijo..VAR8 AS LLAVE_NOMBRE,
DETALLE_&sufijo..VAR9 AS TIPO_DOC, DETALLE_&sufijo..VAR10 AS NRO_DOC,
DETALLE_&sufijo..VAR11 AS GMF, DETALLE_&sufijo..VAR12 AS VAL_CRED_MES,
DETALLE_&sufijo..VAR13 AS NRO_CRED_MES, DETALLE_&sufijo..VAR14 AS PROM_CRED_MES,
DETALLE_&sufijo..VAR15 AS MED_CRED_MES, DETALLE_&sufijo..VAR16 AS VAL_DEB_MES,
DETALLE_&sufijo..VAR17 AS NRO_DEB_MES, DETALLE_&sufijo..VAR18 AS PROM_DEB_MES,
DETALLE_&sufijo..VAR19 AS MED_SALDO_CTA, DETALLE_&sufijo..VAR20 AS PROM_SALDO_CTA,
DETALLE_&sufijo..VAR21 AS MAX_SALDO_CTA, DETALLE_&sufijo..VAR22 AS MIN_SALDO_CTA,
DETALLE_&sufijo..VAR23 AS FIN_SALDO_CTA
FROM WORK.DETALLE_&sufijo DETALLE_&sufijo;
QUIT;

%web_open_table(WORK.SABANA_&sufijo);
%mend nombres_columnas;

%nombres_columnas(CTE);
%nombres_columnas(AHO);

/* Etiqueta: Tipo doc invalido por producto */
%macro valida_tipo_doc(sufijo);
%web_drop_table(WORK.TIPO_DOC_INVALIDO_&sufijo);

/* Código de query generado para SAS Studio por Common Query Services */

PROC SQL;
CREATE TABLE WORK.TIPO_DOC_INVALIDO_&sufijo
AS
SELECT SABANA_&sufijo..RELACION, SABANA_&sufijo..TIPO_CTA, SABANA_&sufijo..NRO_CTA,
SABANA_&sufijo..LLAVE_NOMBRE, SABANA_&sufijo..TIPO_DOC, SABANA_&sufijo..NRO_DOC
FROM WORK.SABANA_&sufijo SABANA_&sufijo
LEFT JOIN WORK.IMPORT_HOMOLOGACION_TPO_DOC IMPORT_HOMOLOGACION_TPO_DOC
ON
   ( SABANA_&sufijo..TIPO_DOC = IMPORT_HOMOLOGACION_TPO_DOC.CNAME )
WHERE IMPORT_HOMOLOGACION_TPO_DOC.CNAME IS MISSING ;
QUIT;

%web_open_table(WORK.TIPO_DOC_INVALIDO_&sufijo);
%mend valida_tipo_doc;

%valida_tipo_doc(CTE);
%valida_tipo_doc(AHO);

/* Etiqueta: Tipo doc valido por producto */
%macro valida_tipo_doc_ok(sufijo);
%web_drop_table(WORK.TIPO_DOC_VALIDO_&sufijo);

/* Código de query generado para SAS Studio por Common Query Services */

PROC SQL;
CREATE TABLE WORK.TIPO_DOC_VALIDO_&sufijo
AS
SELECT SABANA_&sufijo..RELACION, SABANA_&sufijo..TIPO_CTA, SABANA_&sufijo..NRO_CTA,
SABANA_&sufijo..LLAVE_NOMBRE, SABANA_&sufijo..TIPO_DOC, SABANA_&sufijo..NRO_DOC,
SABANA_&sufijo..GMF, SABANA_&sufijo..FIN_SALDO_CTA
FROM WORK.SABANA_&sufijo SABANA_&sufijo
INNER JOIN WORK.IMPORT_HOMOLOGACION_TPO_DOC IMPORT_HOMOLOGACION_TPO_DOC
ON
   ( SABANA_&sufijo..TIPO_DOC = IMPORT_HOMOLOGACION_TPO_DOC.CNAME ) ;
QUIT;

%web_open_table(WORK.TIPO_DOC_VALIDO_&sufijo);
%mend valida_tipo_doc_ok;

%valida_tipo_doc_ok(CTE);
%valida_tipo_doc_ok(AHO);

/* Etiqueta: Campo inconsistencia por producto */
%macro marca_rechazo(sufijo);
/*INICIA CÓDIGO*/
data work.temporal;
set WORK.TIPO_DOC_INVALIDO_&sufijo;
INCONSISTENCIA='TIPO DOC INVALIDO';
run;

data WORK.RECHAZO_TIPO_DOC_&sufijo;
set work.temporal;
run;

proc delete data=work.temporal;
run;
/*FIN CÓDIGO*/
%mend marca_rechazo;

%marca_rechazo(CTE);
%marca_rechazo(AHO);

/* Etiqueta: Conteo de rechazos por producto */
PROC SQL;
CREATE TABLE WORK.CONTEO_RECHAZO_TIPO_DOC AS
SELECT 'CTE' AS PRODUCTO, COUNT(*) AS NRO_RECHAZOS
FROM WORK.RECHAZO_TIPO_DOC_CTE
OUTER UNION CORR
SELECT 'AHO' AS PRODUCTO, COUNT(*) AS NRO_RECHAZOS
FROM WORK.RECHAZO_TIPO_DOC_AHO;
QUIT;

/* Etiqueta: Conteo de validos por producto */
PROC SQL;
CREATE TABLE WORK.CONTEO_VALIDO_TIPO_DOC AS
SELECT 'CTE' AS PRODUCTO, COUNT(*) AS NRO_VALIDOS
FROM WORK.TIPO_DOC_VALIDO_CTE
OUTER UNION CORR
SELECT 'AHO' AS PRODUCTO, COUNT(*) AS NRO_VALIDOS
FROM WORK.TIPO_DOC_VALIDO_AHO;
QUIT;

/* Etiqueta: Exportar rechazos CTE */
PROC EXPORT DATA=WORK.RECHAZO_TIPO_DOC_CTE
OUTFILE='/work_sasstudio/pcfiles/RECHAZO_TIPO_DOC_CTE.csv'
DBMS=DLM REPLACE;
DELIMITER=';';
PUTNAMES=NO;
RUN;

/* Etiqueta: Exportar rechazos AHO */
PROC EXPORT DATA=WORK.RECHAZO_TIPO_DOC_AHO
OUTFILE='/work_sasstudio/pcfiles/RECHAZO_TIPO_DOC_AHO.csv'
DBMS=DLM REPLACE;
DELIMITER=';';
PUTNAMES=NO;
RUN;

/* Etiqueta: Limpiar tablas temporales */
PROC DELETE DATA=WORK.IMPORT_HOMOLOGACION_TPO_DOC;
RUN;
