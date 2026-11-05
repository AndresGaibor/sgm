/* Etiqueta: Macrovariables */
/* Caso ficticio L8 v05. Codex invalido y saldos negativos por producto. Datos inventados. */
%let Servidor_LZ = lz_ficticia_05;
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
DETALLE_&sufijo..VAR9 AS TIPO_DOC, DETALLE_&sufijo..VAR10 AS NRO_DOC,
DETALLE_&sufijo..VAR11 AS GMF_TXT, DETALLE_&sufijo..VAR12 AS VAL_CRED_MES,
DETALLE_&sufijo..VAR23 AS FIN_SALDO_TXT
FROM WORK.DETALLE_&sufijo DETALLE_&sufijo;
QUIT;

%web_open_table(WORK.SABANA_&sufijo);
%mend nombres_columnas;

%nombres_columnas(CTE);
%nombres_columnas(AHO);

/* Etiqueta: Convierte GMF a numero */
%macro convierte_gmf(sufijo);
data work.temporal;
format GMF 3.;
set WORK.SABANA_&sufijo;
GMF=input(left(GMF_TXT), 3.);
drop GMF_TXT;
run;

data WORK.SABANA_&sufijo;
set work.temporal;
run;

proc delete data=work.temporal;
run;
%mend convierte_gmf;

%convierte_gmf(CTE);
%convierte_gmf(AHO);

/* Etiqueta: Convierte FIN_SALDO_CTA a numero */
%macro convierte_saldo(sufijo);
/* El texto con signo menos se lee como negativo; el valor queda en el mismo nombre. */
data work.temporal;
format FIN_SALDO_CTA 20.;
set WORK.SABANA_&sufijo;
FIN_SALDO_CTA=input(left(FIN_SALDO_TXT), 20.);
drop FIN_SALDO_TXT;
run;

data WORK.SABANA_&sufijo;
set work.temporal;
run;

proc delete data=work.temporal;
run;
%mend convierte_saldo;

%convierte_saldo(CTE);
%convierte_saldo(AHO);

/* Etiqueta: Codex invalido por producto */
%macro codex_invalido(sufijo);
%web_drop_table(WORK.INCONS_CODEX_INVALIDO_&sufijo);

/* Código de query generado para SAS Studio por Common Query Services */

PROC SQL;
CREATE TABLE WORK.INCONS_CODEX_INVALIDO_&sufijo
AS
SELECT SABANA_&sufijo..RELACION, SABANA_&sufijo..TIPO_CTA, SABANA_&sufijo..NRO_CTA,
SABANA_&sufijo..LLAVE_NOMBRE, SABANA_&sufijo..TIPO_DOC, SABANA_&sufijo..NRO_DOC,
SABANA_&sufijo..GMF, SABANA_&sufijo..FIN_SALDO_CTA
FROM WORK.SABANA_&sufijo SABANA_&sufijo
WHERE
   (
      ( SABANA_&sufijo..GMF NOT BETWEEN 1 AND 10 ) AND
      ( SABANA_&sufijo..RELACION = 1000 )
   ) ;
QUIT;

%web_open_table(WORK.INCONS_CODEX_INVALIDO_&sufijo);
%mend codex_invalido;

%codex_invalido(CTE);
%codex_invalido(AHO);

/* Etiqueta: Campos neg por producto */
%macro saldo_negativo(sufijo);
%web_drop_table(WORK.INCONS_SALDO_NEG_&sufijo);

/* Código de query generado para SAS Studio por Common Query Services */

PROC SQL;
CREATE TABLE WORK.INCONS_SALDO_NEG_&sufijo
AS
SELECT SABANA_&sufijo..RELACION, SABANA_&sufijo..TIPO_CTA, SABANA_&sufijo..NRO_CTA,
SABANA_&sufijo..LLAVE_NOMBRE, SABANA_&sufijo..TIPO_DOC, SABANA_&sufijo..NRO_DOC,
SABANA_&sufijo..GMF, SABANA_&sufijo..FIN_SALDO_CTA
FROM WORK.SABANA_&sufijo SABANA_&sufijo
WHERE SABANA_&sufijo..FIN_SALDO_CTA < 0 ;
QUIT;

%web_open_table(WORK.INCONS_SALDO_NEG_&sufijo);
%mend saldo_negativo;

%saldo_negativo(CTE);
%saldo_negativo(AHO);

/* Etiqueta: Sabana sin codex ni saldo negativo */
%macro sabana_valida(sufijo);
%web_drop_table(WORK.SABANA_VALIDA_&sufijo);

/* Código de query generado para SAS Studio por Common Query Services */

PROC SQL;
CREATE TABLE WORK.SABANA_VALIDA_&sufijo
AS
SELECT SABANA_&sufijo..RELACION, SABANA_&sufijo..TIPO_CTA, SABANA_&sufijo..NRO_CTA,
SABANA_&sufijo..LLAVE_NOMBRE, SABANA_&sufijo..TIPO_DOC, SABANA_&sufijo..NRO_DOC,
SABANA_&sufijo..GMF, SABANA_&sufijo..VAL_CRED_MES, SABANA_&sufijo..FIN_SALDO_CTA
FROM WORK.SABANA_&sufijo SABANA_&sufijo
WHERE SABANA_&sufijo..LLAVE_NOMBRE NOT IN
   ( SELECT CODEX.LLAVE_NOMBRE FROM WORK.INCONS_CODEX_INVALIDO_&sufijo CODEX )
  AND SABANA_&sufijo..LLAVE_NOMBRE NOT IN
   ( SELECT NEG.LLAVE_NOMBRE FROM WORK.INCONS_SALDO_NEG_&sufijo NEG ) ;
QUIT;

%web_open_table(WORK.SABANA_VALIDA_&sufijo);
%mend sabana_valida;

%sabana_valida(CTE);
%sabana_valida(AHO);

/* Etiqueta: Suma saldo sabana valida por producto */
%macro suma_saldo(sufijo);
%web_drop_table(WORK.SUMA_SALDO_VALIDA_&sufijo);

/* Código de query generado para SAS Studio por Common Query Services */

PROC SQL;
CREATE TABLE WORK.SUMA_SALDO_VALIDA_&sufijo
AS
SELECT SUM(FIN_SALDO_CTA)
AS SUMA_SALDO_FINAL_&sufijo
FROM WORK.SABANA_VALIDA_&sufijo;
QUIT;

%web_open_table(WORK.SUMA_SALDO_VALIDA_&sufijo);
%mend suma_saldo;

%suma_saldo(CTE);
%suma_saldo(AHO);

/* Etiqueta: Campo inconsistencia por producto */
%macro marca_codex_saldo(sufijo);
/*INICIA CÓDIGO*/
data work.temporal;
set WORK.INCONS_CODEX_INVALIDO_&sufijo;
INCONSISTENCIA='CODEX INVALIDO';
run;

data WORK.RECHAZO_CODEX_&sufijo;
set work.temporal;
run;

proc delete data=work.temporal;
run;

data work.temporal;
set WORK.INCONS_SALDO_NEG_&sufijo;
INCONSISTENCIA='SALDO NEGATIVO';
run;

data WORK.RECHAZO_SALDO_&sufijo;
set work.temporal;
run;

proc delete data=work.temporal;
run;
/*FIN CÓDIGO*/
%mend marca_codex_saldo;

%marca_codex_saldo(CTE);
%marca_codex_saldo(AHO);

/* Etiqueta: Conteo de rechazos por regla */
PROC SQL;
CREATE TABLE WORK.CONTEO_CODEX_SALDO AS
SELECT 'CTE CODEX' AS REGLA, COUNT(*) AS NRO_RECHAZOS FROM WORK.RECHAZO_CODEX_CTE
OUTER UNION CORR
SELECT 'CTE SALDO NEG' AS REGLA, COUNT(*) AS NRO_RECHAZOS FROM WORK.RECHAZO_SALDO_CTE
OUTER UNION CORR
SELECT 'AHO CODEX' AS REGLA, COUNT(*) AS NRO_RECHAZOS FROM WORK.RECHAZO_CODEX_AHO
OUTER UNION CORR
SELECT 'AHO SALDO NEG' AS REGLA, COUNT(*) AS NRO_RECHAZOS FROM WORK.RECHAZO_SALDO_AHO;
QUIT;

/* Etiqueta: Exportar rechazos CTE */
PROC EXPORT DATA=WORK.RECHAZO_CODEX_CTE
OUTFILE='/work_sasstudio/pcfiles/RECHAZO_CODEX_CTE.csv'
DBMS=DLM REPLACE;
DELIMITER=';';
PUTNAMES=NO;
RUN;

PROC EXPORT DATA=WORK.RECHAZO_SALDO_CTE
OUTFILE='/work_sasstudio/pcfiles/RECHAZO_SALDO_CTE.csv'
DBMS=DLM REPLACE;
DELIMITER=';';
PUTNAMES=NO;
RUN;

/* Etiqueta: Exportar rechazos AHO */
PROC EXPORT DATA=WORK.RECHAZO_CODEX_AHO
OUTFILE='/work_sasstudio/pcfiles/RECHAZO_CODEX_AHO.csv'
DBMS=DLM REPLACE;
DELIMITER=';';
PUTNAMES=NO;
RUN;

PROC EXPORT DATA=WORK.RECHAZO_SALDO_AHO
OUTFILE='/work_sasstudio/pcfiles/RECHAZO_SALDO_AHO.csv'
DBMS=DLM REPLACE;
DELIMITER=';';
PUTNAMES=NO;
RUN;
