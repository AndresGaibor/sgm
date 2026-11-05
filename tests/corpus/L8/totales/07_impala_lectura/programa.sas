/* Caso L8-07: lectura de Impala simulada. Último día de ingestión de la tabla maestra de    */
/* clientes y pase de ese día a WORK. Rebanada de "Filtro Master Customer" y de              */
/* "Validación ult día ingestión mcd" de client_large.sas.                                  */
/* Las tablas de Impala son CSV cargados en un Impala de contenedor (ver ddl.sql).           */
/* Datos ficticios (SIM...). En el original el periodo viene de WORK.VALIDACION_FECHA; aquí  */
/* se fija para que el caso no dependa de otro archivo.                                     */

/* Etiqueta: Macrovariables de periodo */
%let ANIO = 2026;
%let MES = 9;

/* Etiqueta: Validación ult día ingestión mcd */
proc sql;

connect to IMPALA (DSN = IMPALAP);
create table WORK.MAXDIA as
select * from connection to IMPALA
(
select MAX(ingestion_day) as Mday from resultados_vspc_clientes.master_customer_data AS B
where B.YEAR=&ANIO. AND B.MONTH=&MES.)
;
disconnect from IMPALA;
quit;

/* Etiqueta: Valor del último día */
proc sql;
SELECT MDAY INTO :MDAY FROM WORK.MAXDIA;
quit;

%put NOTE: ultimo dia de ingestion para &ANIO./&MES.: &MDAY.;

/* Etiqueta: Filtro Master Customer */
proc sql;

connect to IMPALA (DSN = IMPALAP);
create table WORK.MCD_ULTIMO_DIA as
select * from connection to IMPALA
(
select B.YEAR, B.MONTH, B.ingestion_day, B.cod_tipo_doc, B.num_doc, B.nombre_cli
from resultados_vspc_clientes.master_customer_data AS B
where B.YEAR=&ANIO. AND B.MONTH=&MES. AND B.ingestion_day='&MDAY.')
;
disconnect from IMPALA;
quit;

/* Etiqueta: Conteo del último día */
proc sql;
create table WORK.MCD_CONTEO as
select COUNT(*) as NRO_FILAS_ULTIMO_DIA
from WORK.MCD_ULTIMO_DIA;
quit;

/* Etiqueta: Conteo de la tabla MCDQ en Impala */
proc sql;

connect to IMPALA (DSN = IMPALAP);
create table WORK.MCDQ_CONTEO as
select * from connection to IMPALA
(
select COUNT(*) as NRO_FILAS_MCDQ
from proceso_vspc_finanzas.mcdq)
;
disconnect from IMPALA;
quit;

/* Etiqueta: Filas de la tabla MCDQ que coinciden con el último día */
proc sql;

connect to IMPALA (DSN = IMPALAP);
create table WORK.MCDQ_MISMO_DIA as
select * from connection to IMPALA
(
select COUNT(*) as NRO_MCDQ_ULTIMO_DIA
from proceso_vspc_finanzas.mcdq AS M
where M.ingestion_day='&MDAY.')
;
disconnect from IMPALA;
quit;

/* Etiqueta: Control de lectura Impala */
proc sql;
create table WORK.CONTROL_IMPALA as
select M.NRO_FILAS_ULTIMO_DIA,
       C.NRO_FILAS_MCDQ,
       D.NRO_MCDQ_ULTIMO_DIA
from WORK.MCD_CONTEO M,
     WORK.MCDQ_CONTEO C,
     WORK.MCDQ_MISMO_DIA D;
quit;

%web_open_table(WORK.CONTROL_IMPALA);

/* Etiqueta: Clientes del último día, por tipo de documento */
proc sql;
create table WORK.CLIENTES_POR_TIPO_DOC as
select cod_tipo_doc, COUNT(*) as NRO_CLIENTES
from WORK.MCD_ULTIMO_DIA
group by cod_tipo_doc;
quit;

/* Etiqueta: Limpieza de tablas auxiliares */
proc datasets lib=WORK nolist;
delete MAXDIA;
quit;

/* Etiqueta: Validar que el último día cae en el periodo */
%macro valida_maxdia(anio=, mes=, dia=);
   %if %length(&dia.) = 10 %then %do;
      %put NOTE: el ultimo dia &dia. es una fecha de 10 caracteres;
   %end;
   %else %do;
      %put WARNING: el ultimo dia &dia. no tiene forma AAAA-MM-DD;
   %end;
%mend valida_maxdia;

%valida_maxdia(anio=&ANIO., mes=&MES., dia=&MDAY.);

/* Etiqueta: Clientes del último día sin tipo de documento */
proc sql;
create table WORK.CLIENTES_SIN_TIPO_DOC as
select COUNT(*) as NRO_SIN_TIPO_DOC
from WORK.MCD_ULTIMO_DIA
where cod_tipo_doc is missing or cod_tipo_doc = '';
quit;

/* Etiqueta: Conteo de clientes por mes del maestro (control) */
proc sql;

connect to IMPALA (DSN = IMPALAP);
create table WORK.MASTER_POR_MES as
select * from connection to IMPALA
(
select B.MONTH, COUNT(*) as NRO_FILAS
from resultados_vspc_clientes.master_customer_data AS B
where B.YEAR=&ANIO.
group by B.MONTH)
;
disconnect from IMPALA;
quit;
