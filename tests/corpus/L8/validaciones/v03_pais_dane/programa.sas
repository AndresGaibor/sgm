/* Etiqueta: Macrovariables */
/* Caso ficticio L8 v03. Pais y codigo DANE contra dos Excel de homologacion. Datos inventados. */
%let Servidor_LZ = lz_ficticia_03;
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

/* Etiqueta: Importar pais */
PROC IMPORT
DATAFILE='\\servidor_ficticio\ENTRADAS_CORPUS\Cod_pais.xlsx'
DBMS=EXCELCS OUT=WORK.IMPORT_CODIGOS_PAIS REPLACE;
TEXTSIZE=32767;
PORT=9621;
SERVER='servidor_ficticio';
SHEET='';
RUN;

/* Etiqueta: Importar codigos DANE */
PROC IMPORT
DATAFILE='\\servidor_ficticio\ENTRADAS_CORPUS\CODIGOS_DANE.xlsx'
DBMS=EXCELCS OUT=WORK.IMPORT_CODIGOS_DANE REPLACE;
TEXTSIZE=32767;
PORT=9621;
SERVER='servidor_ficticio';
SHEET='';
RUN;

/* Etiqueta: Formato de codigo pais */
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

/* Etiqueta: Organizar formato de Codigo DANE */
%web_drop_table(WORK.FORMATO_CODIGO_DANE);

/* Código de query generado para SAS Studio por Common Query Services */

PROC SQL;
CREATE TABLE WORK.FORMATO_CODIGO_DANE
AS
SELECT IMPORT_CODIGOS_DANE.CODIGO_DANE
FROM WORK.IMPORT_CODIGOS_DANE IMPORT_CODIGOS_DANE;
QUIT;

%web_open_table(WORK.FORMATO_CODIGO_DANE);

/* Etiqueta: Descargar detalle CTE */
%let server=servidor_ficticio 7551;
OPTIONS REMOTE=server COMAMID=TCP;
signon
user=&sysuserid pass='***';
RSUBMIT server;

/*PROCESO PARA CARGAR EL ARCHIVO DESDE PCFILE HACIA UNA RUTA TEMPORAL EN SAS*/
PROC DOWNLOAD INFILE='\\servidor_ficticio\ENTRADAS_CORPUS\DETALLE_CTE.csv'
OUTFILE='/work_sasstudio/pcfiles/DETALLE_CTE.csv';
PROC DOWNLOAD INFILE='\\servidor_ficticio\ENTRADAS_CORPUS\UBICACION_CTE.csv'
OUTFILE='/work_sasstudio/pcfiles/UBICACION_CTE.csv';
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
PROC DOWNLOAD INFILE='\\servidor_ficticio\ENTRADAS_CORPUS\UBICACION_AHO.csv'
OUTFILE='/work_sasstudio/pcfiles/UBICACION_AHO.csv';
endrsubmit;
signoff;
run;

/* Etiqueta: Importar detalle y ubicacion por producto */
%macro importa_archivo(nombre);
proc import datafile="/work_sasstudio/pcfiles/&nombre..csv"
out=WORK.&nombre replace dbms=dlm;
delimiter=';';
getnames=NO;
run;
%mend importa_archivo;

%importa_archivo(DETALLE_CTE);
%importa_archivo(UBICACION_CTE);
%importa_archivo(DETALLE_AHO);
%importa_archivo(UBICACION_AHO);

/* Etiqueta: Nombre columnas de detalle por producto */
%macro nombres_detalle(sufijo);
%web_drop_table(WORK.SABANA_&sufijo);

/* Código de query generado para SAS Studio por Common Query Services */

PROC SQL;
CREATE TABLE WORK.SABANA_&sufijo
AS
SELECT DETALLE_&sufijo..VAR1 AS ANIO_PROCESO, DETALLE_&sufijo..VAR2 AS MES_PROCESO,
DETALLE_&sufijo..VAR4 AS RELACION, DETALLE_&sufijo..VAR6 AS TIPO_CTA,
DETALLE_&sufijo..VAR7 AS NRO_CTA, DETALLE_&sufijo..VAR8 AS LLAVE_NOMBRE,
DETALLE_&sufijo..VAR9 AS TIPO_DOC, DETALLE_&sufijo..VAR10 AS NRO_DOC
FROM WORK.DETALLE_&sufijo DETALLE_&sufijo;
QUIT;

%web_open_table(WORK.SABANA_&sufijo);
%mend nombres_detalle;

%nombres_detalle(CTE);
%nombres_detalle(AHO);

/* Etiqueta: Nombre columnas de ubicacion por producto */
%macro nombres_ubicacion(sufijo);
%web_drop_table(WORK.UBIC_&sufijo);

/* Código de query generado para SAS Studio por Common Query Services */

PROC SQL;
CREATE TABLE WORK.UBIC_&sufijo
AS
SELECT UBICACION_&sufijo..VAR1 AS LLAVE_NOMBRE, UBICACION_&sufijo..VAR2 AS PAIS,
UBICACION_&sufijo..VAR3 AS CODIGO_UBICACION, UBICACION_&sufijo..VAR4 AS DIRECCION
FROM WORK.UBICACION_&sufijo UBICACION_&sufijo;
QUIT;

%web_open_table(WORK.UBIC_&sufijo);
%mend nombres_ubicacion;

%nombres_ubicacion(CTE);
%nombres_ubicacion(AHO);

/* Etiqueta: Sabana con ubicacion por producto */
%macro une_ubicacion(sufijo);
%web_drop_table(WORK.SABANA_UBIC_&sufijo);

/* Código de query generado para SAS Studio por Common Query Services */

PROC SQL;
CREATE TABLE WORK.SABANA_UBIC_&sufijo
AS
SELECT t1.RELACION, t1.TIPO_CTA, t1.NRO_CTA, t1.LLAVE_NOMBRE, t1.TIPO_DOC, t1.NRO_DOC,
t2.PAIS, t2.CODIGO_UBICACION, t2.DIRECCION
FROM WORK.SABANA_&sufijo t1
LEFT JOIN WORK.UBIC_&sufijo t2
ON ( t1.LLAVE_NOMBRE = t2.LLAVE_NOMBRE );
QUIT;

%web_open_table(WORK.SABANA_UBIC_&sufijo);
%mend une_ubicacion;

%une_ubicacion(CTE);
%une_ubicacion(AHO);

/* Etiqueta: Reg ubicacion invalida por producto */
%macro ubicacion_invalida(sufijo);
%web_drop_table(WORK.INCONS_UBICACION_&sufijo);

/* Código de query generado para SAS Studio por Common Query Services */

PROC SQL;
CREATE TABLE WORK.INCONS_UBICACION_&sufijo
AS
SELECT t1.LLAVE_NOMBRE, t1.RELACION, t1.TIPO_DOC, t1.NRO_DOC, t1.PAIS,
t1.CODIGO_UBICACION, t1.DIRECCION,
CASE
   WHEN t3.Codigo_Pais IS MISSING THEN 'PAIS NO HOMOLOGADO'
   WHEN t1.PAIS = '900' AND t2.CODIGO_DANE IS MISSING THEN 'DANE NO HOMOLOGADO'
   WHEN t1.PAIS <> '900' AND t1.CODIGO_UBICACION IS NOT MISSING
        THEN 'UBICACION EXTRANJERA CON CODIGO'
   ELSE 'DIRECCION INVALIDA'
END AS INCONSISTENCIA
FROM WORK.SABANA_UBIC_&sufijo t1
LEFT JOIN WORK.FORMATO_CODIGO_DANE t2
ON ( t1.CODIGO_UBICACION = t2.CODIGO_DANE )
LEFT JOIN WORK.IMPORT_CODIGOS_PAIS t3
ON ( t1.PAIS = t3.Codigo_Pais )
WHERE t3.Codigo_Pais IS MISSING
   OR ( t1.PAIS = '900' AND t2.CODIGO_DANE IS MISSING )
   OR ( t1.PAIS <> '900' AND t1.CODIGO_UBICACION IS NOT MISSING )
   OR LENGTH(t1.DIRECCION) < 8
   OR UPPER(t1.DIRECCION) CONTAINS UPPER('sin dir');
QUIT;

%web_open_table(WORK.INCONS_UBICACION_&sufijo);
%mend ubicacion_invalida;

%ubicacion_invalida(CTE);
%ubicacion_invalida(AHO);

/* Etiqueta: Ubicacion valida por producto */
%macro ubicacion_valida(sufijo);
%web_drop_table(WORK.UBIC_VALIDA_&sufijo);

/* Código de query generado para SAS Studio por Common Query Services */

PROC SQL;
CREATE TABLE WORK.UBIC_VALIDA_&sufijo
AS
SELECT t1.LLAVE_NOMBRE, t1.RELACION, t1.TIPO_DOC, t1.NRO_DOC, t1.PAIS,
t1.CODIGO_UBICACION, t1.DIRECCION
FROM WORK.SABANA_UBIC_&sufijo t1
WHERE t1.LLAVE_NOMBRE NOT IN
   ( SELECT t4.LLAVE_NOMBRE FROM WORK.INCONS_UBICACION_&sufijo t4 );
QUIT;

%web_open_table(WORK.UBIC_VALIDA_&sufijo);
%mend ubicacion_valida;

%ubicacion_valida(CTE);
%ubicacion_valida(AHO);

/* Etiqueta: Conteo de rechazos de ubicacion */
PROC SQL;
CREATE TABLE WORK.CONTEO_UBICACION AS
SELECT 'CTE' AS PRODUCTO, COUNT(*) AS NRO_RECHAZOS
FROM WORK.INCONS_UBICACION_CTE
OUTER UNION CORR
SELECT 'AHO' AS PRODUCTO, COUNT(*) AS NRO_RECHAZOS
FROM WORK.INCONS_UBICACION_AHO;
QUIT;

/* Etiqueta: Conteo de validos de ubicacion */
PROC SQL;
CREATE TABLE WORK.CONTEO_UBICACION_VALIDA AS
SELECT 'CTE' AS PRODUCTO, COUNT(*) AS NRO_VALIDOS
FROM WORK.UBIC_VALIDA_CTE
OUTER UNION CORR
SELECT 'AHO' AS PRODUCTO, COUNT(*) AS NRO_VALIDOS
FROM WORK.UBIC_VALIDA_AHO;
QUIT;

/* Etiqueta: Exportar rechazos de ubicacion CTE */
PROC EXPORT DATA=WORK.INCONS_UBICACION_CTE
OUTFILE='/work_sasstudio/pcfiles/INCONS_UBICACION_CTE.csv'
DBMS=DLM REPLACE;
DELIMITER=';';
PUTNAMES=NO;
RUN;

/* Etiqueta: Exportar rechazos de ubicacion AHO */
PROC EXPORT DATA=WORK.INCONS_UBICACION_AHO
OUTFILE='/work_sasstudio/pcfiles/INCONS_UBICACION_AHO.csv'
DBMS=DLM REPLACE;
DELIMITER=';';
PUTNAMES=NO;
RUN;
