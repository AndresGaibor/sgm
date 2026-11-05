/* Etiqueta: Macrovariables */
/* Caso ficticio L8 v04. Tipo de cuenta por lista de valores y GMF por rango. Datos inventados. */
%let Servidor_LZ = lz_ficticia_04;
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
SELECT DETALLE_&sufijo..VAR4 AS RELACION, DETALLE_&sufijo..VAR6 AS TIPO_CTA,
DETALLE_&sufijo..VAR7 AS NRO_CTA, DETALLE_&sufijo..VAR8 AS LLAVE_NOMBRE,
DETALLE_&sufijo..VAR9 AS TIPO_DOC, DETALLE_&sufijo..VAR10 AS NRO_DOC,
DETALLE_&sufijo..VAR11 AS GMF_TXT, DETALLE_&sufijo..VAR23 AS FIN_SALDO_CTA
FROM WORK.DETALLE_&sufijo DETALLE_&sufijo;
QUIT;

%web_open_table(WORK.SABANA_&sufijo);
%mend nombres_columnas;

%nombres_columnas(CTE);
%nombres_columnas(AHO);

/* Etiqueta: Convierte GMF a numero */
%macro convierte_gmf(sufijo);
/* Un texto que no es numero ("XX") queda faltante, con nota en el log de SAS. */
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

/* Etiqueta: Tipo cuenta invalido por producto */
%macro tipo_cta_invalido(sufijo);
%web_drop_table(WORK.INCONS_TIPO_CTA_INVALIDO_&sufijo);

/* Código de query generado para SAS Studio por Common Query Services */

PROC SQL;
CREATE TABLE WORK.INCONS_TIPO_CTA_INVALIDO_&sufijo
AS
SELECT SABANA_&sufijo..RELACION, SABANA_&sufijo..TIPO_CTA, SABANA_&sufijo..NRO_CTA,
SABANA_&sufijo..LLAVE_NOMBRE, SABANA_&sufijo..TIPO_DOC, SABANA_&sufijo..NRO_DOC,
SABANA_&sufijo..GMF
FROM WORK.SABANA_&sufijo SABANA_&sufijo
WHERE
   ( SABANA_&sufijo..TIPO_CTA NOT IN ( '1', '2', '3', '4', '5' ) ) ;
QUIT;

%web_open_table(WORK.INCONS_TIPO_CTA_INVALIDO_&sufijo);
%mend tipo_cta_invalido;

%tipo_cta_invalido(CTE);
%tipo_cta_invalido(AHO);

/* Etiqueta: Sabana sin tipo cuenta invalido */
%macro sin_tipo_cta(sufijo);
%web_drop_table(WORK.SABANA_TIPO_CTA_OK_&sufijo);

/* Código de query generado para SAS Studio por Common Query Services */

PROC SQL;
CREATE TABLE WORK.SABANA_TIPO_CTA_OK_&sufijo
AS
SELECT SABANA_&sufijo..RELACION, SABANA_&sufijo..TIPO_CTA, SABANA_&sufijo..NRO_CTA,
SABANA_&sufijo..LLAVE_NOMBRE, SABANA_&sufijo..TIPO_DOC, SABANA_&sufijo..NRO_DOC,
SABANA_&sufijo..GMF, SABANA_&sufijo..FIN_SALDO_CTA
FROM WORK.SABANA_&sufijo SABANA_&sufijo
WHERE
   ( SABANA_&sufijo..TIPO_CTA IN ( '1', '2', '3', '4', '5' ) ) ;
QUIT;

%web_open_table(WORK.SABANA_TIPO_CTA_OK_&sufijo);
%mend sin_tipo_cta;

%sin_tipo_cta(CTE);
%sin_tipo_cta(AHO);

/* Etiqueta: GMF invalido por producto */
%macro gmf_invalido(sufijo);
%web_drop_table(WORK.INCONS_GMF_INVALIDO_&sufijo);

/* Código de query generado para SAS Studio por Common Query Services */

PROC SQL;
CREATE TABLE WORK.INCONS_GMF_INVALIDO_&sufijo
AS
SELECT SABANA_TIPO_CTA_OK_&sufijo..RELACION, SABANA_TIPO_CTA_OK_&sufijo..TIPO_CTA,
SABANA_TIPO_CTA_OK_&sufijo..NRO_CTA, SABANA_TIPO_CTA_OK_&sufijo..LLAVE_NOMBRE,
SABANA_TIPO_CTA_OK_&sufijo..TIPO_DOC, SABANA_TIPO_CTA_OK_&sufijo..NRO_DOC,
SABANA_TIPO_CTA_OK_&sufijo..GMF,
CASE
   WHEN SABANA_TIPO_CTA_OK_&sufijo..GMF IS MISSING THEN 'GMF NO NUMERICO'
   ELSE 'GMF FUERA DE RANGO'
END AS MOTIVO
FROM WORK.SABANA_TIPO_CTA_OK_&sufijo SABANA_TIPO_CTA_OK_&sufijo
WHERE
   ( SABANA_TIPO_CTA_OK_&sufijo..GMF IS MISSING ) OR
   ( SABANA_TIPO_CTA_OK_&sufijo..GMF NOT BETWEEN 1 AND 10 ) ;
QUIT;

%web_open_table(WORK.INCONS_GMF_INVALIDO_&sufijo);
%mend gmf_invalido;

%gmf_invalido(CTE);
%gmf_invalido(AHO);

/* Etiqueta: Sabana final valida por producto */
%macro sabana_valida(sufijo);
%web_drop_table(WORK.SABANA_VALIDA_&sufijo);

/* Código de query generado para SAS Studio por Common Query Services */

PROC SQL;
CREATE TABLE WORK.SABANA_VALIDA_&sufijo
AS
SELECT DISTINCT SABANA_TIPO_CTA_OK_&sufijo..RELACION, SABANA_TIPO_CTA_OK_&sufijo..TIPO_CTA,
SABANA_TIPO_CTA_OK_&sufijo..NRO_CTA, SABANA_TIPO_CTA_OK_&sufijo..LLAVE_NOMBRE,
SABANA_TIPO_CTA_OK_&sufijo..TIPO_DOC, SABANA_TIPO_CTA_OK_&sufijo..NRO_DOC,
SABANA_TIPO_CTA_OK_&sufijo..GMF, SABANA_TIPO_CTA_OK_&sufijo..FIN_SALDO_CTA
FROM WORK.SABANA_TIPO_CTA_OK_&sufijo SABANA_TIPO_CTA_OK_&sufijo
LEFT JOIN WORK.INCONS_GMF_INVALIDO_&sufijo INCONS_GMF_INVALIDO_&sufijo
ON
   ( SABANA_TIPO_CTA_OK_&sufijo..LLAVE_NOMBRE = INCONS_GMF_INVALIDO_&sufijo..LLAVE_NOMBRE )
WHERE INCONS_GMF_INVALIDO_&sufijo..LLAVE_NOMBRE IS MISSING ;
QUIT;

%web_open_table(WORK.SABANA_VALIDA_&sufijo);
%mend sabana_valida;

%sabana_valida(CTE);
%sabana_valida(AHO);

/* Etiqueta: Campo inconsistencia por producto */
%macro marca_cuenta(sufijo);
/*INICIA CÓDIGO*/
data work.temporal;
set WORK.INCONS_TIPO_CTA_INVALIDO_&sufijo;
INCONSISTENCIA='TIPO CTA INVALIDO';
run;

data WORK.RECHAZO_CUENTA_&sufijo;
set work.temporal;
run;

proc delete data=work.temporal;
run;
/*FIN CÓDIGO*/
%mend marca_cuenta;

%marca_cuenta(CTE);
%marca_cuenta(AHO);

/* Etiqueta: Consolidar rechazos de cuenta y GMF */
PROC SQL;
   CREATE TABLE WORK.INCONS_CUENTA_CTE AS
   SELECT RELACION, TIPO_CTA, LLAVE_NOMBRE, GMF, 'TIPO CTA INVALIDO' AS INCONSISTENCIA
      FROM WORK.INCONS_TIPO_CTA_INVALIDO_CTE
   OUTER UNION CORR
   SELECT RELACION, TIPO_CTA, LLAVE_NOMBRE, GMF, MOTIVO AS INCONSISTENCIA
      FROM WORK.INCONS_GMF_INVALIDO_CTE;
QUIT;

PROC SQL;
   CREATE TABLE WORK.INCONS_CUENTA_AHO AS
   SELECT RELACION, TIPO_CTA, LLAVE_NOMBRE, GMF, 'TIPO CTA INVALIDO' AS INCONSISTENCIA
      FROM WORK.INCONS_TIPO_CTA_INVALIDO_AHO
   OUTER UNION CORR
   SELECT RELACION, TIPO_CTA, LLAVE_NOMBRE, GMF, MOTIVO AS INCONSISTENCIA
      FROM WORK.INCONS_GMF_INVALIDO_AHO;
QUIT;

/* Etiqueta: Conteo de rechazos por producto */
PROC SQL;
CREATE TABLE WORK.CONTEO_CUENTA AS
SELECT 'CTE' AS PRODUCTO, COUNT(*) AS NRO_RECHAZOS FROM WORK.INCONS_CUENTA_CTE
OUTER UNION CORR
SELECT 'AHO' AS PRODUCTO, COUNT(*) AS NRO_RECHAZOS FROM WORK.INCONS_CUENTA_AHO;
QUIT;

/* Etiqueta: Conteo de validos por producto */
PROC SQL;
CREATE TABLE WORK.CONTEO_CUENTA_VALIDA AS
SELECT 'CTE' AS PRODUCTO, COUNT(*) AS NRO_VALIDOS FROM WORK.SABANA_VALIDA_CTE
OUTER UNION CORR
SELECT 'AHO' AS PRODUCTO, COUNT(*) AS NRO_VALIDOS FROM WORK.SABANA_VALIDA_AHO;
QUIT;

/* Etiqueta: Exportar rechazos de cuenta CTE */
PROC EXPORT DATA=WORK.INCONS_CUENTA_CTE
OUTFILE='/work_sasstudio/pcfiles/INCONS_CUENTA_CTE.csv'
DBMS=DLM REPLACE;
DELIMITER=';';
PUTNAMES=NO;
RUN;

/* Etiqueta: Exportar rechazos de cuenta AHO */
PROC EXPORT DATA=WORK.INCONS_CUENTA_AHO
OUTFILE='/work_sasstudio/pcfiles/INCONS_CUENTA_AHO.csv'
DBMS=DLM REPLACE;
DELIMITER=';';
PUTNAMES=NO;
RUN;
