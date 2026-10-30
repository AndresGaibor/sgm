/* priority: P0 | sintético: PROC SQL join + group by, %LET */
%let anio = 2025;
libname dwh '/data/dwh';

proc sql;
  create table work.ventas_resumen as
  select c.region,
         p.categoria,
         sum(v.monto) as total_monto,
         count(distinct v.cliente_id) as clientes
  from dwh.ventas v
       inner join dwh.clientes c on v.cliente_id = c.id
       left join dwh.productos p on v.producto_id = p.id
  where year(v.fecha) = &anio.
  group by c.region, p.categoria
  having calculated total_monto > 1000;
quit;
