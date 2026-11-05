/* Etiqueta: Macrovariables */
/* Caso ficticio L8 v07. Cadena completa: tipo de documento, documento vacio o cero y tipo de
   cuenta, con sabana final y archivos de rechazo. Datos inventados; las rutas no son reales. */
%let Servidor_LZ = lz_ficticia_07;
%let m_ambiente = D;

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
DETALLE_&sufijo..VAR9 AS TIPO_DOC, DETALLE_&sufijo..VAR10 AS NRO_DOC_TXT,
DETALLE_&sufijo..VAR11 AS GMF_TXT, DETALLE_&sufijo..VAR23 AS FIN_SALDO_CTA
FROM WORK.DETALLE_&sufijo DETALLE_&sufijo;
QUIT;

%web_open_table(WORK.SABANA_&sufijo);
%mend nombres_columnas;

%nombres_columnas(CTE);
%nombres_columnas(AHO);

/* Etiqueta: Convierte NRO_DOC y GMF a numero */
%macro convierte_numericos(sufijo);
/* Un campo vacio queda faltante; el texto "0" queda en cero. GMF se convierte igual que NRO_DOC. */
data work.temporal;
format NRO_DOC 30.;
set WORK.SABANA_&sufijo;
NRO_DOC=input(left(NRO_DOC_TXT), 30.);
GMF=input(left(GMF_TXT), 3.);
drop NRO_DOC_TXT GMF_TXT;
run;

data WORK.SABANA_&sufijo;
set work.temporal;
run;

proc delete data=work.temporal;
run;
%mend convierte_numericos;

%convierte_numericos(CTE);
%convierte_numericos(AHO);

/* Etiqueta: Paso 1 tipo doc invalido */
%macro paso1_tipo_doc(sufijo);
%web_drop_table(WORK.PASO1_RECHAZO_&sufijo);

/* Código de query generado para SAS Studio por Common Query Services */

PROC SQL;
CREATE TABLE WORK.PASO1_RECHAZO_&sufijo
AS
SELECT SABANA_&sufijo..RELACION, SABANA_&sufijo..TIPO_CTA, SABANA_&sufijo..NRO_CTA,
SABANA_&sufijo..LLAVE_NOMBRE, SABANA_&sufijo..TIPO_DOC, SABANA_&sufijo..NRO_DOC,
SABANA_&sufijo..GMF, SABANA_&sufijo..FIN_SALDO_CTA
FROM WORK.SABANA_&sufijo SABANA_&sufijo
LEFT JOIN WORK.IMPORT_HOMOLOGACION_TPO_DOC IMPORT_HOMOLOGACION_TPO_DOC
ON
   ( SABANA_&sufijo..TIPO_DOC = IMPORT_HOMOLOGACION_TPO_DOC.CNAME )
WHERE IMPORT_HOMOLOGACION_TPO_DOC.CNAME IS MISSING ;
QUIT;

%web_open_table(WORK.PASO1_RECHAZO_&sufijo);

%web_drop_table(WORK.PASO1_VALIDO_&sufijo);

PROC SQL;
CREATE TABLE WORK.PASO1_VALIDO_&sufijo
AS
SELECT SABANA_&sufijo..*
FROM WORK.SABANA_&sufijo SABANA_&sufijo
INNER JOIN WORK.IMPORT_HOMOLOGACION_TPO_DOC IMPORT_HOMOLOGACION_TPO_DOC
ON
   ( SABANA_&sufijo..TIPO_DOC = IMPORT_HOMOLOGACION_TPO_DOC.CNAME ) ;
QUIT;

%web_open_table(WORK.PASO1_VALIDO_&sufijo);
%mend paso1_tipo_doc;

%paso1_tipo_doc(CTE);
%paso1_tipo_doc(AHO);

/* Etiqueta: Paso 2 tit-cot vacio o cero */
%macro paso2_tit_cot(sufijo);
%web_drop_table(WORK.PASO2_RECHAZO_TC_&sufijo);

/* Código de query generado para SAS Studio por Common Query Services */

PROC SQL;
CREATE TABLE WORK.PASO2_RECHAZO_TC_&sufijo
AS
SELECT PASO1_VALIDO_&sufijo..*
FROM WORK.PASO1_VALIDO_&sufijo PASO1_VALIDO_&sufijo
WHERE
   (
      ( PASO1_VALIDO_&sufijo..NRO_DOC = 0 ) OR PASO1_VALIDO_&sufijo..NRO_DOC IS MISSING
   ) AND
   ( PASO1_VALIDO_&sufijo..RELACION <> 9902 ) ;
QUIT;

%web_open_table(WORK.PASO2_RECHAZO_TC_&sufijo);
%mend paso2_tit_cot;

%paso2_tit_cot(CTE);
%paso2_tit_cot(AHO);

/* Etiqueta: Paso 2 FA vacio o cero */
%macro paso2_fa(sufijo);
%web_drop_table(WORK.PASO2_RECHAZO_FA_&sufijo);

/* Código de query generado para SAS Studio por Common Query Services */

PROC SQL;
CREATE TABLE WORK.PASO2_RECHAZO_FA_&sufijo
AS
SELECT PASO1_VALIDO_&sufijo..*
FROM WORK.PASO1_VALIDO_&sufijo PASO1_VALIDO_&sufijo
WHERE
   (
      ( PASO1_VALIDO_&sufijo..NRO_DOC = 0 ) OR PASO1_VALIDO_&sufijo..NRO_DOC IS MISSING
   ) AND
   ( PASO1_VALIDO_&sufijo..RELACION = 9902 ) ;
QUIT;

%web_open_table(WORK.PASO2_RECHAZO_FA_&sufijo);
%mend paso2_fa;

%paso2_fa(CTE);
%paso2_fa(AHO);

/* Etiqueta: Paso 2 sabana sin vacios o cero */
%macro paso2_valido(sufijo);
%web_drop_table(WORK.PASO2_VALIDO_&sufijo);

/* Código de query generado para SAS Studio por Common Query Services */

PROC SQL;
CREATE TABLE WORK.PASO2_VALIDO_&sufijo
AS
SELECT PASO1_VALIDO_&sufijo..*
FROM WORK.PASO1_VALIDO_&sufijo PASO1_VALIDO_&sufijo
WHERE PASO1_VALIDO_&sufijo..NRO_DOC IS NOT MISSING
  AND PASO1_VALIDO_&sufijo..NRO_DOC <> 0 ;
QUIT;

%web_open_table(WORK.PASO2_VALIDO_&sufijo);
%mend paso2_valido;

%paso2_valido(CTE);
%paso2_valido(AHO);

/* Etiqueta: Paso 3 tipo cuenta invalido */
%macro paso3_tipo_cta(sufijo);
%web_drop_table(WORK.PASO3_RECHAZO_&sufijo);

/* Código de query generado para SAS Studio por Common Query Services */

PROC SQL;
CREATE TABLE WORK.PASO3_RECHAZO_&sufijo
AS
SELECT PASO2_VALIDO_&sufijo..*
FROM WORK.PASO2_VALIDO_&sufijo PASO2_VALIDO_&sufijo
WHERE PASO2_VALIDO_&sufijo..TIPO_CTA NOT IN ( '1', '2', '3', '4', '5' ) ;
QUIT;

%web_open_table(WORK.PASO3_RECHAZO_&sufijo);

%web_drop_table(WORK.SABANA_FINAL_&sufijo);

PROC SQL;
CREATE TABLE WORK.SABANA_FINAL_&sufijo
AS
SELECT PASO2_VALIDO_&sufijo..*
FROM WORK.PASO2_VALIDO_&sufijo PASO2_VALIDO_&sufijo
WHERE PASO2_VALIDO_&sufijo..TIPO_CTA IN ( '1', '2', '3', '4', '5' ) ;
QUIT;

%web_open_table(WORK.SABANA_FINAL_&sufijo);
%mend paso3_tipo_cta;

%paso3_tipo_cta(CTE);
%paso3_tipo_cta(AHO);

/* Etiqueta: Consolida rechazos por producto */
%macro consolida(sufijo);
/*INICIA CÓDIGO*/
PROC SQL;
CREATE TABLE WORK.RECHAZOS_&sufijo AS
SELECT RELACION, TIPO_CTA, LLAVE_NOMBRE, TIPO_DOC, NRO_DOC, 'TIPO DOC INVALIDO' AS MOTIVO
FROM WORK.PASO1_RECHAZO_&sufijo
OUTER UNION CORR
SELECT RELACION, TIPO_CTA, LLAVE_NOMBRE, TIPO_DOC, NRO_DOC, 'NRO DOC VACIO O CERO' AS MOTIVO
FROM WORK.PASO2_RECHAZO_TC_&sufijo
OUTER UNION CORR
SELECT RELACION, TIPO_CTA, LLAVE_NOMBRE, TIPO_DOC, NRO_DOC, 'NRO DOC FA VACIO O CERO' AS MOTIVO
FROM WORK.PASO2_RECHAZO_FA_&sufijo
OUTER UNION CORR
SELECT RELACION, TIPO_CTA, LLAVE_NOMBRE, TIPO_DOC, NRO_DOC, 'TIPO CTA INVALIDO' AS MOTIVO
FROM WORK.PASO3_RECHAZO_&sufijo;
QUIT;
/*FIN CÓDIGO*/
%mend consolida;

%consolida(CTE);
%consolida(AHO);

/* Etiqueta: Exportar sabana final CTE */
PROC EXPORT DATA=WORK.SABANA_FINAL_CTE
OUTFILE='/work_sasstudio/pcfiles/SABANA_FINAL_CTE.csv'
DBMS=DLM REPLACE;
DELIMITER=';';
PUTNAMES=NO;
RUN;

/* Etiqueta: Exportar sabana final AHO */
PROC EXPORT DATA=WORK.SABANA_FINAL_AHO
OUTFILE='/work_sasstudio/pcfiles/SABANA_FINAL_AHO.csv'
DBMS=DLM REPLACE;
DELIMITER=';';
PUTNAMES=NO;
RUN;

/* Etiqueta: Exportar rechazos CTE */
PROC EXPORT DATA=WORK.RECHAZOS_CTE
OUTFILE='/work_sasstudio/pcfiles/RECHAZOS_CTE.csv'
DBMS=DLM REPLACE;
DELIMITER=';';
PUTNAMES=NO;
RUN;

/* Etiqueta: Exportar rechazos AHO */
PROC EXPORT DATA=WORK.RECHAZOS_AHO
OUTFILE='/work_sasstudio/pcfiles/RECHAZOS_AHO.csv'
DBMS=DLM REPLACE;
DELIMITER=';';
PUTNAMES=NO;
RUN;
