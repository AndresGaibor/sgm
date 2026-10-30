/* priority: P1 | Cruce de cuatro tablas con SQL; el resultado intermedio se consume desde WORK. */
libname ventas "/data/ventas";
libname cat "/data/catalogos";

/* Paso 1: cuentas con movimientos del trimestre, con oficina y segmento. */
proc sql;
  create table work.base_cuentas as
  select c.cuenta_id,
         c.nombre,
         c.segmento,
         o.oficina_nombre,
         s.descripcion as desc_segmento,
         count(distinct m.mov_id) as n_mov,
         sum(case when m.tipo = 'R' then m.monto else 0 end) as total_retiros,
         sum(case when m.tipo = 'D' then m.monto else 0 end) as total_depositos
  from ventas.cuentas c
       inner join ventas.movimientos m
         on m.cuenta_id = c.cuenta_id
       left join cat.oficinas o
         on o.oficina_id = c.oficina_id
       left join cat.segmentos s
         on s.segmento_cod = c.segmento
  where m.fecha between '01JAN2026'd and '31MAR2026'd
  group by c.cuenta_id, c.nombre, c.segmento, o.oficina_nombre, s.descripcion
  having count(distinct m.mov_id) > 0;
quit;

/* Paso 2: alertas sobre el intermedio de WORK, a un archivo persistente. */
proc sql;
  create table cat.alertas_trimestre as
  select b.cuenta_id,
         b.nombre,
         b.oficina_nombre,
         b.total_retiros / b.total_depositos as ratio_retiro,
         case
           when b.total_retiros > b.total_depositos then 'ALTO'
           when b.total_retiros > 0.5 * b.total_depositos then 'MEDIO'
           else 'BAJO'
         end as nivel
  from work.base_cuentas b
  where b.total_depositos > 0
  order by ratio_retiro desc;
quit;

/* Paso 3: resumen por oficina sobre el mismo intermedio. */
proc sql;
  select oficina_nombre,
         count(*) as n_cuentas,
         sum(n_mov) as movimientos
  from work.base_cuentas
  group by oficina_nombre;
quit;
