/* Etiqueta: Macrovariables */
/* Caso ficticio L8 v02. Campos de documento vacios o cero, por tit-cot y por FA. */
%let Servidor_LZ = lz_ficticia_02;
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
DETALLE_&sufijo..VAR9 AS TIPO_DOC, DETALLE_&sufijo..VAR10 AS NRO_DOC_TXT,
DETALLE_&sufijo..VAR11 AS GMF, DETALLE_&sufijo..VAR23 AS FIN_SALDO_CTA
FROM WORK.DETALLE_&sufijo DETALLE_&sufijo;
QUIT;

%web_open_table(WORK.SABANA_&sufijo);
%mend nombres_columnas;

%nombres_columnas(CTE);
%nombres_columnas(AHO);

/* Etiqueta: Convierte NRO_DOC a numero */
%macro convierte_nro_doc(sufijo);
/* Un campo vacio queda faltante; el texto "0" queda en cero. */
data work.temporal;
format NRO_DOC 30.;
set WORK.SABANA_&sufijo;
NRO_DOC=input(left(NRO_DOC_TXT), 30.);
drop NRO_DOC_TXT;
run;

data WORK.SABANA_&sufijo;
set work.temporal;
run;

proc delete data=work.temporal;
run;
%mend convierte_nro_doc;

%convierte_nro_doc(CTE);
%convierte_nro_doc(AHO);

/* Etiqueta: tit-cot vacios o 0 */
%macro tit_cot_vacio(sufijo);
%web_drop_table(WORK.NRO_DOC_VACIO_0_TIT_COT_&sufijo);

/* Código de query generado para SAS Studio por Common Query Services */

PROC SQL;
CREATE TABLE WORK.NRO_DOC_VACIO_0_TIT_COT_&sufijo
AS
SELECT SABANA_&sufijo..RELACION, SABANA_&sufijo..TIPO_CTA, SABANA_&sufijo..NRO_CTA,
SABANA_&sufijo..LLAVE_NOMBRE, SABANA_&sufijo..TIPO_DOC, SABANA_&sufijo..NRO_DOC
FROM WORK.SABANA_&sufijo SABANA_&sufijo
WHERE
   (
      (
         ( SABANA_&sufijo..NRO_DOC = 0 ) OR SABANA_&sufijo..NRO_DOC IS MISSING
      ) AND
      ( SABANA_&sufijo..RELACION <> 9902 )
   ) ;
QUIT;

%web_open_table(WORK.NRO_DOC_VACIO_0_TIT_COT_&sufijo);
%mend tit_cot_vacio;

%tit_cot_vacio(CTE);
%tit_cot_vacio(AHO);

/* Etiqueta: FA vacios o 0 */
%macro fa_vacio(sufijo);
%web_drop_table(WORK.INCONS_NRO_DOC_VACIO_0_FA_&sufijo);

/* Código de query generado para SAS Studio por Common Query Services */

PROC SQL;
CREATE TABLE WORK.INCONS_NRO_DOC_VACIO_0_FA_&sufijo
AS
SELECT SABANA_&sufijo..RELACION, SABANA_&sufijo..TIPO_CTA, SABANA_&sufijo..NRO_CTA,
SABANA_&sufijo..LLAVE_NOMBRE, SABANA_&sufijo..TIPO_DOC, SABANA_&sufijo..NRO_DOC
FROM WORK.SABANA_&sufijo SABANA_&sufijo
WHERE
   (
      (
         ( SABANA_&sufijo..NRO_DOC = 0 ) OR SABANA_&sufijo..NRO_DOC IS MISSING
      ) AND
      ( SABANA_&sufijo..RELACION = 9902 )
   ) ;
QUIT;

%web_open_table(WORK.INCONS_NRO_DOC_VACIO_0_FA_&sufijo);
%mend fa_vacio;

%fa_vacio(CTE);
%fa_vacio(AHO);

/* Etiqueta: Nro doc no vacio ni cero */
%macro doc_valido(sufijo);
/* Conserva FIN_SALDO_CTA: la suma de saldos de CTE lee esta tabla. */
%web_drop_table(WORK.NRO_DOC_NO_VACIO_NI_0_&sufijo);

/* Código de query generado para SAS Studio por Common Query Services */

PROC SQL;
CREATE TABLE WORK.NRO_DOC_NO_VACIO_NI_0_&sufijo
AS
SELECT SABANA_&sufijo..RELACION, SABANA_&sufijo..TIPO_CTA, SABANA_&sufijo..NRO_CTA,
SABANA_&sufijo..LLAVE_NOMBRE, SABANA_&sufijo..TIPO_DOC, SABANA_&sufijo..NRO_DOC,
SABANA_&sufijo..FIN_SALDO_CTA
FROM WORK.SABANA_&sufijo SABANA_&sufijo
WHERE
   ( SABANA_&sufijo..NRO_DOC IS NOT MISSING AND
      ( SABANA_&sufijo..NRO_DOC <> 0 )
   ) ;
QUIT;

%web_open_table(WORK.NRO_DOC_NO_VACIO_NI_0_&sufijo);
%mend doc_valido;

%doc_valido(CTE);
%doc_valido(AHO);

/* Etiqueta: Campo inconsistencia por producto */
%macro marca_inconsistencia(sufijo);
/*INICIA CÓDIGO*/
data work.temporal;
set WORK.NRO_DOC_VACIO_0_TIT_COT_&sufijo
    WORK.INCONS_NRO_DOC_VACIO_0_FA_&sufijo;
INCONSISTENCIA='NRO DOC VACIO O CERO';
run;

data WORK.RECHAZO_NRO_DOC_&sufijo;
set work.temporal;
run;

proc delete data=work.temporal;
run;
/*FIN CÓDIGO*/
%mend marca_inconsistencia;

%marca_inconsistencia(CTE);
%marca_inconsistencia(AHO);

/* Etiqueta: Conteo de rechazos por tipo de relacion */
PROC SQL;
CREATE TABLE WORK.CONTEO_NRO_DOC_TIT_COT AS
SELECT 'CTE' AS PRODUCTO, COUNT(*) AS NRO_RECHAZOS
FROM WORK.NRO_DOC_VACIO_0_TIT_COT_CTE
OUTER UNION CORR
SELECT 'AHO' AS PRODUCTO, COUNT(*) AS NRO_RECHAZOS
FROM WORK.NRO_DOC_VACIO_0_TIT_COT_AHO;
QUIT;

/* Etiqueta: Conteo de rechazos FA */
PROC SQL;
CREATE TABLE WORK.CONTEO_NRO_DOC_FA AS
SELECT 'CTE' AS PRODUCTO, COUNT(*) AS NRO_RECHAZOS
FROM WORK.INCONS_NRO_DOC_VACIO_0_FA_CTE
OUTER UNION CORR
SELECT 'AHO' AS PRODUCTO, COUNT(*) AS NRO_RECHAZOS
FROM WORK.INCONS_NRO_DOC_VACIO_0_FA_AHO;
QUIT;

/* Etiqueta: Suma saldo sabana valida */
data WORK.FORMAT_SALDO_CTE;
format FORM_FIN_SALDO_CTA 20.;
set WORK.NRO_DOC_NO_VACIO_NI_0_CTE;
FORM_FIN_SALDO_CTA=input(left(FIN_SALDO_CTA), 20.);
run;

PROC SQL;
CREATE TABLE WORK.SUMA_SALDO_CTE_VALIDAS AS
SELECT SUM(FORM_FIN_SALDO_CTA)
AS SUMA_SALDO_FINAL_CTE
FROM WORK.FORMAT_SALDO_CTE;
QUIT;

/* Etiqueta: Exportar rechazos por producto */
PROC EXPORT DATA=WORK.RECHAZO_NRO_DOC_CTE
OUTFILE='/work_sasstudio/pcfiles/RECHAZO_NRO_DOC_CTE.csv'
DBMS=DLM REPLACE;
DELIMITER=';';
PUTNAMES=NO;
RUN;

PROC EXPORT DATA=WORK.RECHAZO_NRO_DOC_AHO
OUTFILE='/work_sasstudio/pcfiles/RECHAZO_NRO_DOC_AHO.csv'
DBMS=DLM REPLACE;
DELIMITER=';';
PUTNAMES=NO;
RUN;

/* Etiqueta: Limpiar tablas de paso */
proc delete data=WORK.FORMAT_SALDO_CTE;
run;
