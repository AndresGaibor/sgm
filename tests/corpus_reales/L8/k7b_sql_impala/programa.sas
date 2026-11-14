/* Etiqueta: Filtro Master Customer */
proc sql;

SELECT AÑO INTO: ANIO FROM WORK.VALIDACION_FECHA;
SELECT MES INTO: MES FROM WORK.VALIDACION_FECHA;
SELECT DIA INTO: DIA FROM WORK.VALIDACION_FECHA;

connect to IMPALA (DSN = IMPALAP);
create table WORK.MAXDIA as
select * from connection to IMPALA
(     
select MAX(ingestion_day)as Mday from resultados_vspc_clientes.master_customer_data AS B
where B.YEAR=&ANIO. AND B.MONTH=&MES.)
;
disconnect from IMPALA;  
quit;

proc sql;

SELECT AÑO INTO: ANIO FROM WORK.VALIDACION_FECHA;
SELECT MES INTO: MES FROM WORK.VALIDACION_FECHA;
SELECT MDAY INTO: MDAY FROM WORK.MAXDIA;

connect to IMPALA (DSN = IMPALAP);
EXECUTE BY IMPALA (
create table proceso_vspc_finanzas.mcdq stored as parquet as
select i.cod_tipo_doc,
   i.num_doc,
   i.nombre_cli,
   i.long_nombre1,
   i.long_nombre2,
   i.long_apellido1,
   i.long_apellido2,
   i.dir_p,
   i.cod_ciudad_dirp,
   i.cod_pais_dirp,
   i.YEAR AS YEAR,
   i.MONTH AS MONTH,
   i.ingestion_day,
   i.llave_sistema,
   i.cod_tipo_dirp

from resultados_vspc_clientes.master_customer_data as i
where i.YEAR=&ANIO. AND i.MONTH=&MES. and i.ingestion_day=&MDAY.)
;
disconnect from IMPALA;  
quit;
