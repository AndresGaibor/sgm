/* Caso L8-05: conciliación origen contra válidos más rechazados, por producto.             */
/* Rebanada de "Calculo conciliacion registros", "Calculo conciliacion saldos" y             */
/* "Conciliacion final" de client_large.sas. Datos ficticios (SIM...).                      */
/* Plantado: CTE concilia; AHO tiene una fila perdida de 5.00 y NO concilia.                */
/* Supuesto del caso (pendiente con el equipo): tolerancia de 0.01 en saldo.                */

/* Etiqueta: Macrovariables de conciliación */
%let tolerancia = 0.01;
%let tipos_validos = 'CC', 'TI', 'CE', 'PA';

/* Etiqueta: Importar origen CTE */
proc import datafile='/work_sasstudio/pcfiles/origen_cte.csv' out=WORK.IMPORT_ORIGEN_CTE
dbms=dlm replace;
delimiter=';';
getnames=NO;
run;

/* Etiqueta: Importar origen AHO */
proc import datafile='/work_sasstudio/pcfiles/origen_aho.csv' out=WORK.IMPORT_ORIGEN_AHO
dbms=dlm replace;
delimiter=';';
getnames=NO;
run;

/* Etiqueta: Nombres de columnas CTE */
PROC SQL;
CREATE TABLE WORK.ORIGEN_CTE AS
SELECT VAR1 AS ANIO_PROCESO, VAR2 AS MES_PROCESO, VAR3 AS CODIGO_OFICINA,
       VAR4 AS RELACION, VAR5 AS CODIGO_SUCURSAL, VAR6 AS TIPO_CTA,
       VAR7 AS NRO_CTA, VAR8 AS LLAVE_NOMBRE, VAR9 AS TIPO_DOC,
       VAR10 AS NRO_DOC, VAR11 AS GMF, VAR12 AS VAL_CRED_MES,
       VAR13 AS NRO_CRED_MES, VAR14 AS PROM_CRED_MES, VAR15 AS MED_CRED_MES,
       VAR16 AS VAL_DEB_MES, VAR17 AS NRO_DEB_MES, VAR18 AS PROM_DEB_MES,
       VAR19 AS MED_SALDO_CTA, VAR20 AS PROM_SALDO_CTA, VAR21 AS MAX_SALDO_CTA,
       VAR22 AS MIN_SALDO_CTA, VAR23 AS FIN_SALDO_CTA
FROM WORK.IMPORT_ORIGEN_CTE;
QUIT;

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

/* Etiqueta: Saldo numérico CTE */
data WORK.ORIGEN_CTE;
set WORK.ORIGEN_CTE;
FORM_FIN_SALDO_CTA = input(left(FIN_SALDO_CTA), 20.);
run;

/* Etiqueta: Saldo numérico AHO */
data WORK.ORIGEN_AHO;
set WORK.ORIGEN_AHO;
FORM_FIN_SALDO_CTA = input(left(FIN_SALDO_CTA), 20.);
run;

/* Etiqueta: Válidos y rechazados CTE */
PROC SQL;
CREATE TABLE WORK.VALIDOS_CTE AS
SELECT *
FROM WORK.ORIGEN_CTE
WHERE TIPO_DOC IN (&tipos_validos.) AND NRO_CTA <> '';
CREATE TABLE WORK.RECHAZADOS_CTE AS
SELECT *
FROM WORK.ORIGEN_CTE
WHERE TIPO_DOC NOT IN (&tipos_validos.) AND TIPO_DOC <> '';
QUIT;

/* Etiqueta: Válidos y rechazados AHO */
PROC SQL;
CREATE TABLE WORK.VALIDOS_AHO AS
SELECT *
FROM WORK.ORIGEN_AHO
WHERE TIPO_DOC IN (&tipos_validos.) AND NRO_CTA <> '';
CREATE TABLE WORK.RECHAZADOS_AHO AS
SELECT *
FROM WORK.ORIGEN_AHO
WHERE TIPO_DOC NOT IN (&tipos_validos.) AND TIPO_DOC <> '';
QUIT;

/* Etiqueta: Totales de conciliación CTE */
PROC SQL;
CREATE TABLE WORK.TOTALES_CONC_CTE AS
SELECT
   (SELECT COUNT(*) FROM WORK.ORIGEN_CTE) AS NRO_ORIGEN,
   (SELECT COUNT(*) FROM WORK.VALIDOS_CTE) AS NRO_VALIDOS,
   (SELECT COUNT(*) FROM WORK.RECHAZADOS_CTE) AS NRO_RECHAZADOS,
   (SELECT SUM(FORM_FIN_SALDO_CTA) FROM WORK.ORIGEN_CTE) AS SUMA_ORIGEN,
   (SELECT SUM(FORM_FIN_SALDO_CTA) FROM WORK.VALIDOS_CTE) AS SUMA_VALIDOS,
   (SELECT SUM(FORM_FIN_SALDO_CTA) FROM WORK.RECHAZADOS_CTE) AS SUMA_RECHAZADOS
FROM WORK.ORIGEN_CTE (OBS=1);
QUIT;

/* Etiqueta: Totales de conciliación AHO */
PROC SQL;
CREATE TABLE WORK.TOTALES_CONC_AHO AS
SELECT
   (SELECT COUNT(*) FROM WORK.ORIGEN_AHO) AS NRO_ORIGEN,
   (SELECT COUNT(*) FROM WORK.VALIDOS_AHO) AS NRO_VALIDOS,
   (SELECT COUNT(*) FROM WORK.RECHAZADOS_AHO) AS NRO_RECHAZADOS,
   (SELECT SUM(FORM_FIN_SALDO_CTA) FROM WORK.ORIGEN_AHO) AS SUMA_ORIGEN,
   (SELECT SUM(FORM_FIN_SALDO_CTA) FROM WORK.VALIDOS_AHO) AS SUMA_VALIDOS,
   (SELECT SUM(FORM_FIN_SALDO_CTA) FROM WORK.RECHAZADOS_AHO) AS SUMA_RECHAZADOS
FROM WORK.ORIGEN_AHO (OBS=1);
QUIT;

/* Etiqueta: Diferencias de conciliación CTE */
PROC SQL;
CREATE TABLE WORK.CONCILIACION_CTE AS
SELECT NRO_ORIGEN,
       NRO_ORIGEN - (NRO_VALIDOS + NRO_RECHAZADOS) AS DIF_FILAS,
       ROUND(SUMA_ORIGEN - (SUMA_VALIDOS + SUMA_RECHAZADOS), 0.01) AS DIF_SALDO,
       SUMA_ORIGEN
FROM WORK.TOTALES_CONC_CTE;
QUIT;

/* Etiqueta: Diferencias de conciliación AHO */
PROC SQL;
CREATE TABLE WORK.CONCILIACION_AHO AS
SELECT NRO_ORIGEN,
       NRO_ORIGEN - (NRO_VALIDOS + NRO_RECHAZADOS) AS DIF_FILAS,
       ROUND(SUMA_ORIGEN - (SUMA_VALIDOS + SUMA_RECHAZADOS), 0.01) AS DIF_SALDO,
       SUMA_ORIGEN
FROM WORK.TOTALES_CONC_AHO;
QUIT;

/* Etiqueta: Estado de conciliación CTE */
PROC SQL NOPRINT;
SELECT CASE
          WHEN ABS(DIF_SALDO) <= &tolerancia. AND DIF_FILAS = 0 THEN 'CONCILIA'
          ELSE 'NO CONCILIA'
       END
INTO :ESTADO_CTE
FROM WORK.CONCILIACION_CTE;
QUIT;

/* Etiqueta: Estado de conciliación AHO */
PROC SQL NOPRINT;
SELECT CASE
          WHEN ABS(DIF_SALDO) <= &tolerancia. AND DIF_FILAS = 0 THEN 'CONCILIA'
          ELSE 'NO CONCILIA'
       END
INTO :ESTADO_AHO
FROM WORK.CONCILIACION_AHO;
QUIT;

/* Etiqueta: Mensaje final de conciliación */
%put NOTE: CONCILIACION CTE: &ESTADO_CTE.;
%put NOTE: CONCILIACION AHO: &ESTADO_AHO.;

%macro mensaje_final(producto=, estado=);
   %if &estado. = CONCILIA %then %do;
      %put NOTE: &producto. concilia con la tolerancia &tolerancia.;
   %end;
   %else %do;
      %put WARNING: &producto. NO concilia; revisar filas perdidas y saldos;
   %end;
%mend mensaje_final;

/* Etiqueta: Mensaje final por producto */
%mensaje_final(producto=CTE, estado=&ESTADO_CTE.);
%mensaje_final(producto=AHO, estado=&ESTADO_AHO.);

/* Etiqueta: Conciliacion final por producto */
%web_drop_table(WORK.CONCILIACION_FINAL);

PROC SQL;
CREATE TABLE WORK.CONCILIACION_FINAL AS
SELECT 'CTE' AS PRODUCTO, DIF_FILAS, DIF_SALDO
FROM WORK.CONCILIACION_CTE
OUTER UNION CORR
SELECT 'AHO' AS PRODUCTO, DIF_FILAS, DIF_SALDO
FROM WORK.CONCILIACION_AHO;
QUIT;

%web_open_table(WORK.CONCILIACION_FINAL);

/* Etiqueta: Limpieza de tablas auxiliares */
PROC DELETE DATA=WORK.TOTALES_CONC_CTE;
RUN;

PROC DELETE DATA=WORK.TOTALES_CONC_AHO;
RUN;
