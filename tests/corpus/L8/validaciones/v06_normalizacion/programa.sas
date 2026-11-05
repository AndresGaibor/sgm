/* Etiqueta: Macrovariables */
/* Caso ficticio L8 v06. Normalizacion de nombres y montos de texto. Datos inventados. */
%let Servidor_LZ = lz_ficticia_06;
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
SELECT DETALLE_&sufijo..VAR1 AS ANIO_PROCESO, DETALLE_&sufijo..VAR4 AS RELACION,
DETALLE_&sufijo..VAR7 AS NRO_CTA, DETALLE_&sufijo..VAR8 AS LLAVE_NOMBRE,
DETALLE_&sufijo..VAR9 AS TIPO_DOC, DETALLE_&sufijo..VAR11 AS GMF_TXT,
DETALLE_&sufijo..VAR12 AS VAL_CRED_TXT, DETALLE_&sufijo..VAR23 AS FIN_SALDO_TXT
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

/* Etiqueta: Campo VAL_CRED_MES a numero sin espacios */
%macro convierte_valor(sufijo);
/* left quita blancos a la izquierda; input lee el valor; compress quita todos los blancos. */
data work.temporal;
format VAL_CRED_MES 20.;
set WORK.SABANA_&sufijo;
VAL_CRED_MES=input(left(VAL_CRED_TXT), 20.);
VAL_CRED_LIMPIO=COMPRESS(VAL_CRED_TXT);
run;

data WORK.SABANA_&sufijo;
set work.temporal;
run;

proc delete data=work.temporal;
run;
%mend convierte_valor;

%convierte_valor(CTE);
%convierte_valor(AHO);

/* Etiqueta: Normaliza nombre de titular */
%macro normaliza_nombre(sufijo);
%web_drop_table(WORK.SABANA_NORM_&sufijo);

/* Código de query generado para SAS Studio por Common Query Services */

PROC SQL;
CREATE TABLE WORK.SABANA_NORM_&sufijo
AS
SELECT SABANA_&sufijo..RELACION, SABANA_&sufijo..NRO_CTA, SABANA_&sufijo..TIPO_DOC,
SABANA_&sufijo..GMF, SABANA_&sufijo..VAL_CRED_MES, SABANA_&sufijo..VAL_CRED_LIMPIO,
SABANA_&sufijo..FIN_SALDO_TXT,
COMPBL(STRIP(UPCASE(SABANA_&sufijo..LLAVE_NOMBRE))) AS LLAVE_NORMALIZADA
FROM WORK.SABANA_&sufijo SABANA_&sufijo;
QUIT;

%web_open_table(WORK.SABANA_NORM_&sufijo);
%mend normaliza_nombre;

%normaliza_nombre(CTE);
%normaliza_nombre(AHO);

/* Etiqueta: Motivo de normalizacion por producto */
%macro motivo_normalizacion(sufijo);
%web_drop_table(WORK.MOTIVO_NORM_&sufijo);

/* Código de query generado para SAS Studio por Common Query Services */

PROC SQL;
CREATE TABLE WORK.MOTIVO_NORM_&sufijo
AS
SELECT SABANA_&sufijo..LLAVE_NOMBRE,
CASE
   WHEN SABANA_&sufijo..LLAVE_NOMBRE <> COMPBL(STRIP(SABANA_&sufijo..LLAVE_NOMBRE))
        THEN 'ESPACIOS EN NOMBRE'
   WHEN SABANA_&sufijo..LLAVE_NOMBRE CONTAINS 'Ñ' THEN 'NOMBRE CON ENIE'
   WHEN SABANA_&sufijo..LLAVE_NOMBRE CONTAINS 'Í' THEN 'NOMBRE CON TILDES'
   WHEN SABANA_&sufijo..LLAVE_NOMBRE <> UPCASE(SABANA_&sufijo..LLAVE_NOMBRE)
        THEN 'NOMBRE EN MINUSCULAS'
   WHEN SABANA_&sufijo..VAL_CRED_TXT <> COMPRESS(SABANA_&sufijo..VAL_CRED_TXT)
        THEN 'VALOR CON ESPACIOS'
   ELSE 'SIN CAMBIO'
END AS MOTIVO
FROM WORK.SABANA_&sufijo SABANA_&sufijo;
QUIT;

%web_open_table(WORK.MOTIVO_NORM_&sufijo);
%mend motivo_normalizacion;

%motivo_normalizacion(CTE);
%motivo_normalizacion(AHO);

/* Etiqueta: Conteo de motivos CTE */
PROC SQL;
CREATE TABLE WORK.CONTEO_MOTIVO_CTE AS
SELECT MOTIVO, COUNT(*) AS NRO_FILAS
FROM WORK.MOTIVO_NORM_CTE
GROUP BY MOTIVO
ORDER BY MOTIVO;
QUIT;

/* Etiqueta: Conteo de motivos AHO */
PROC SQL;
CREATE TABLE WORK.CONTEO_MOTIVO_AHO AS
SELECT MOTIVO, COUNT(*) AS NRO_FILAS
FROM WORK.MOTIVO_NORM_AHO
GROUP BY MOTIVO
ORDER BY MOTIVO;
QUIT;

/* Etiqueta: Valores normalizados sin faltantes */
PROC SQL;
CREATE TABLE WORK.SIN_FALTANTES_CTE AS
SELECT *
FROM WORK.SABANA_NORM_CTE
WHERE VAL_CRED_MES IS NOT MISSING;
QUIT;

PROC SQL;
CREATE TABLE WORK.SIN_FALTANTES_AHO AS
SELECT *
FROM WORK.SABANA_NORM_AHO
WHERE VAL_CRED_MES IS NOT MISSING;
QUIT;

/* Etiqueta: Suma de valor de credito normalizado */
PROC SQL;
CREATE TABLE WORK.SUMA_VALOR_NORM AS
SELECT 'CTE' AS PRODUCTO, SUM(VAL_CRED_MES) AS SUMA_VAL_CRED
FROM WORK.SIN_FALTANTES_CTE
OUTER UNION CORR
SELECT 'AHO' AS PRODUCTO, SUM(VAL_CRED_MES) AS SUMA_VAL_CRED
FROM WORK.SIN_FALTANTES_AHO;
QUIT;

/* Etiqueta: Exportar normalizacion CTE */
PROC EXPORT DATA=WORK.SABANA_NORM_CTE
OUTFILE='/work_sasstudio/pcfiles/SABANA_NORM_CTE.csv'
DBMS=DLM REPLACE;
DELIMITER=';';
PUTNAMES=NO;
RUN;

/* Etiqueta: Exportar normalizacion AHO */
PROC EXPORT DATA=WORK.SABANA_NORM_AHO
OUTFILE='/work_sasstudio/pcfiles/SABANA_NORM_AHO.csv'
DBMS=DLM REPLACE;
DELIMITER=';';
PUTNAMES=NO;
RUN;

/* Etiqueta: Limpiar tablas de paso */
proc delete data=WORK.SIN_FALTANTES_CTE;
run;

proc delete data=WORK.SIN_FALTANTES_AHO;
run;
