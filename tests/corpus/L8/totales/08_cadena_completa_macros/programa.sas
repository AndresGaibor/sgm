/* Caso L8-08: cadena completa para CTE y AHO con una macro por producto.                  */
/* Encadena los temas 1 a 5: duplicados, correcciones, sábana, totales y conciliación,    */
/* y la fecha del Excel en el nombre del archivo de salida. Datos ficticios (SIM...).      */
/* Orden como en el original: primero se quitan duplicados exactos, después se corrige.   */
/* Supuestos del caso (no del SAS): por corregir = TIPO_CTA fuera de 01, 02, 03;            */
/* corregida = TIPO_DOC CEDULA (pasa a CC). Tolerancia de conciliación 0.01.                */

/* Etiqueta: Macrovariables generales */
%let tolerancia = 0.01;

/* Etiqueta: Importar Validación Fecha */
PROC IMPORT DATAFILE='/work_sasstudio/pcfiles/Validacion_fecha.xlsx'
DBMS=EXCELCS OUT=WORK.VALIDACION_FECHA REPLACE;
SHEET='';
RUN;

/* Etiqueta: Macrovariables de fecha de validación */
PROC SQL;
SELECT 'AÑO'n INTO :ANIO FROM WORK.VALIDACION_FECHA;
SELECT MES INTO :MES FROM WORK.VALIDACION_FECHA;
SELECT DIA INTO :DIA FROM WORK.VALIDACION_FECHA;
QUIT;

/* Etiqueta: Texto de fecha de validación */
data WORK.FECHA_TEXTO;
set WORK.VALIDACION_FECHA;
MES_TXT = PUT(MES, Z2.);
DIA_TXT = PUT(DIA, Z2.);
run;

PROC SQL;
SELECT MES_TXT INTO :MES_TXT FROM WORK.FECHA_TEXTO;
SELECT DIA_TXT INTO :DIA_TXT FROM WORK.FECHA_TEXTO;
QUIT;

/* Etiqueta: Concatenar fecha de validación */
%let FECHA = &ANIO.&MES_TXT.&DIA_TXT.;

/* Etiqueta: Macro de cadena por producto */
%macro procesa_producto(prod=, suf=);

   /* Etiqueta: Importar origen */
   proc import datafile="/work_sasstudio/pcfiles/origen_&suf..csv"
   out=WORK.IMPORT_&prod.
   dbms=dlm replace;
   delimiter=';';
   getnames=NO;
   run;

   /* Etiqueta: Nombres de columnas por producto */
   PROC SQL;
   CREATE TABLE WORK.ORIGEN_&prod. AS
   SELECT VAR1 AS ANIO_PROCESO, VAR2 AS MES_PROCESO, VAR3 AS CODIGO_OFICINA,
          VAR4 AS RELACION, VAR5 AS CODIGO_SUCURSAL, VAR6 AS TIPO_CTA,
          VAR7 AS NRO_CTA, VAR8 AS LLAVE_NOMBRE, VAR9 AS TIPO_DOC,
          VAR10 AS NRO_DOC, VAR11 AS GMF, VAR12 AS VAL_CRED_MES,
          VAR13 AS NRO_CRED_MES, VAR14 AS PROM_CRED_MES, VAR15 AS MED_CRED_MES,
          VAR16 AS VAL_DEB_MES, VAR17 AS NRO_DEB_MES, VAR18 AS PROM_DEB_MES,
          VAR19 AS MED_SALDO_CTA, VAR20 AS PROM_SALDO_CTA, VAR21 AS MAX_SALDO_CTA,
          VAR22 AS MIN_SALDO_CTA, VAR23 AS FIN_SALDO_CTA
   FROM WORK.IMPORT_&prod.;
   QUIT;

   /* Etiqueta: Saldo numérico por producto */
   data WORK.ORIGEN_&prod.;
   set WORK.ORIGEN_&prod.;
   FORM_FIN_SALDO_CTA = input(left(FIN_SALDO_CTA), 20.);
   run;

   /* Etiqueta: Duplicados exactos por producto */
   PROC SORT DATA=WORK.ORIGEN_&prod. OUT=WORK.UNICOS_&prod. NODUPREC;
   BY _ALL_;
   RUN;

   /* Etiqueta: Campo inconsistencia por producto */
   data WORK.MARCA_&prod.;
   set WORK.UNICOS_&prod.;
   length INCONSISTENCIA $ 40 CORREGIDA $ 2;
   INCONSISTENCIA = '';
   CORREGIDA = 'NO';
   if TIPO_CTA not in ('01', '02', '03') then INCONSISTENCIA = 'TIPO_CTA_INVALIDO';
   if INCONSISTENCIA = '' and TIPO_DOC = 'CEDULA' then do;
      TIPO_DOC = 'CC';
      CORREGIDA = 'SI';
   end;
   run;

   /* Etiqueta: Incons corregidas por producto */
   PROC SQL;
   CREATE TABLE WORK.CORREGIDAS_&prod. AS
   SELECT * FROM WORK.MARCA_&prod. WHERE CORREGIDA = 'SI';
   QUIT;

   /* Etiqueta: Incons por corregir por producto */
   PROC SQL;
   CREATE TABLE WORK.INCONS_DEP_&prod. AS
   SELECT * FROM WORK.MARCA_&prod. WHERE INCONSISTENCIA NE '';
   QUIT;

   /* Etiqueta: Archivo de inconsistencias por producto */
   PROC EXPORT DATA=WORK.INCONS_DEP_&prod.
      OUTFILE="/work_sasstudio/pcfiles/INCONS_DEP_&prod..csv"
      DBMS=CSV REPLACE;
   RUN;

   /* Etiqueta: Sabana final por producto */
   PROC SQL;
   CREATE TABLE WORK.SABANA_&prod. AS
   SELECT RELACION, TIPO_CTA, NRO_CTA, TIPO_DOC, NRO_DOC, GMF, FORM_FIN_SALDO_CTA
   FROM WORK.MARCA_&prod.
   WHERE INCONSISTENCIA = '';
   QUIT;

   /* Etiqueta: Totales por producto */
   PROC SQL;
   CREATE TABLE WORK.TOTALES_&prod. AS
   SELECT
      (SELECT COUNT(*) FROM WORK.ORIGEN_&prod.) AS NRO_ORIGEN,
      (SELECT COUNT(*) FROM WORK.UNICOS_&prod.) AS NRO_UNICOS,
      (SELECT COUNT(*) FROM WORK.CORREGIDAS_&prod.) AS NRO_CORREGIDAS,
      (SELECT COUNT(*) FROM WORK.INCONS_DEP_&prod.) AS NRO_POR_CORREGIR,
      (SELECT COUNT(*) FROM WORK.SABANA_&prod.) AS NRO_SABANA,
      (SELECT SUM(FORM_FIN_SALDO_CTA) FROM WORK.SABANA_&prod.) AS SUMA_SABANA
   FROM WORK.UNICOS_&prod. (OBS=1);
   QUIT;

   /* Etiqueta: Conciliacion por producto */
   PROC SQL;
   CREATE TABLE WORK.CONCILIACION_&prod. AS
   SELECT NRO_ORIGEN - (NRO_UNICOS + NRO_POR_CORREGIR) AS DIF_SIN_DUPLICADOS_EXACTOS,
          NRO_ORIGEN - (NRO_SABANA + NRO_POR_CORREGIR + (NRO_ORIGEN - NRO_UNICOS))
             AS DIF_TOTAL
   FROM WORK.TOTALES_&prod.;
   QUIT;

   /* Etiqueta: Estado de conciliación por producto */
   PROC SQL NOPRINT;
   SELECT CASE WHEN ABS(DIF_TOTAL) <= &tolerancia. THEN 'CONCILIA' ELSE 'NO CONCILIA' END
   INTO :ESTADO_&prod.
   FROM WORK.CONCILIACION_&prod.;
   QUIT;

   %put NOTE: &prod. estado de conciliacion: &&ESTADO_&prod..;

   /* Etiqueta: Resultado de cierre por producto */
   PROC EXPORT DATA=WORK.SABANA_&prod.
      OUTFILE="/work_sasstudio/pcfiles/CIERRE_&prod._&FECHA..csv"
      DBMS=CSV REPLACE;
   RUN;

%mend procesa_producto;

/* Etiqueta: Cadena CTE */
%procesa_producto(prod=CTE, suf=cte);

/* Etiqueta: Cadena AHO */
%procesa_producto(prod=AHO, suf=aho);

/* Etiqueta: Resumen de la cadena */
PROC SQL;
CREATE TABLE WORK.RESUMEN_CADENA AS
SELECT 'CTE' AS PRODUCTO, NRO_SABANA, SUMA_SABANA FROM WORK.TOTALES_CTE
OUTER UNION CORR
SELECT 'AHO' AS PRODUCTO, NRO_SABANA, SUMA_SABANA FROM WORK.TOTALES_AHO;
QUIT;

%web_open_table(WORK.RESUMEN_CADENA);

/* Etiqueta: Limpieza de tablas auxiliares */
PROC DELETE DATA=WORK.FECHA_TEXTO;
RUN;
