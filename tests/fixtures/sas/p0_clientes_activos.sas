/* priority: P0 | sintético: DATA step, LIBNAME, PROC SORT */
libname dwh '/data/dwh';
libname stg '/data/staging';

data stg.clientes_activos(keep=cliente_id nombre saldo segmento);
  set dwh.clientes(rename=(id=cliente_id));
  where estado = 'A' and saldo > 0;
  length segmento $8;
  if saldo >= 100000 then segmento = 'ALTO';
  else if saldo >= 10000 then segmento = 'MEDIO';
  else segmento = 'BAJO';
  drop estado;
run;

proc sort data=stg.clientes_activos out=stg.clientes_activos_ord nodupkey;
  by cliente_id;
run;
