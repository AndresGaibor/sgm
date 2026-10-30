/* priority: P1 | ELT en Oracle: el cálculo se hace dentro de la base de datos, no se sacan filas a SAS. */
options nocenter;

/* Conexión de lectura/escritura al almacén. Las credenciales llegan del entorno, no se escriben aquí. */
libname dw oracle user=etl_dw path='ORCLDW' schema=stg_ventas connection=shared;

/* %include "&ruta_comun/limpieza_comun.sas";  */

/* Paso 1: resumen diario dentro de Oracle (pass-through). */
proc sql;
  connect to oracle (user=etl_dw path='ORCLDW');
  execute (
    create table stg_ventas.ventas_dia as
    select v.fecha,
           v.tienda_id,
           sum(v.importe) as importe_total,
           count(*) as n_tickets
    from stg_ventas.ventas_raw v
    where v.estado = 'CERRADA'
    group by v.fecha, v.tienda_id
  ) by oracle;

  /* Paso 2: catálogo de tiendas activas, también dentro de Oracle. */
  execute (
    create table stg_ventas.tiendas_activas as
    select t.tienda_id, t.region, t.nombre_tienda
    from stg_ventas.tiendas t
    where t.activa = 'S'
  ) by oracle;

  disconnect from oracle;
quit;

/* Paso 3: se limpia la tabla temporal de la corrida anterior (sentencia de mantenimiento). */
proc sql;
  connect to oracle (user=etl_dw path='ORCLDW');
  execute (drop table stg_ventas.tmp_ventas_ajuste purge) by oracle;
  disconnect from oracle;
quit;

/* Paso 4: cruce entre tablas de la misma libname; SAS solo emite el SQL. */
proc sql;
  create table dw.resumen_region as
  select t.region,
         count(distinct d.tienda_id) as n_tiendas,
         sum(d.importe_total) as importe_region,
         sum(d.n_tickets) as tickets_region
  from dw.ventas_dia d
       inner join dw.tiendas_activas t
       on d.tienda_id = t.tienda_id
  group by t.region;
quit;

/* Paso 5: ranking de tiendas dentro de la misma base. */
proc sql;
  create table dw.ranking_tiendas as
  select d.tienda_id,
         d.importe_total,
         monotonic() as posicion
  from dw.ventas_dia d
  order by d.importe_total desc;
quit;

/* Paso 6: vista de control; no cambia datos. */
proc sql;
  connect to oracle (user=etl_dw path='ORCLDW');
  execute (
    create or replace view stg_ventas.v_control_cierre as
    select fecha, count(*) as tiendas_cerradas
    from stg_ventas.ventas_dia
    group by fecha
  ) by oracle;
  disconnect from oracle;
quit;

/* Comprobación de conteos al final, solo lectura. */
proc sql noprint;
  select count(*) into :n_region trimmed from dw.resumen_region;
quit;
%put NOTE: regiones calculadas = &n_region;
