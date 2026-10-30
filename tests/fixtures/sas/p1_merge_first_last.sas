/* priority: P1 | sintético: MERGE BY, FIRST./LAST., RETAIN, ARRAY, formatos, fechas, missing */
proc format;
  value $tramo low-<30='Joven' 30-<60='Adulto' 60-high='Mayor';
run;

proc sort data=work.pagos; by cliente_id fecha_pago; run;
proc sort data=work.clientes; by cliente_id; run;

data work.pagos_cliente;
  merge work.clientes(in=a) work.pagos(in=b);
  by cliente_id;
  if a;
  retain acumulado 0;
  array m{3} mes1-mes3;
  if first.cliente_id then acumulado = 0;
  acumulado + coalesce(monto, 0);
  if missing(monto) then flag_sin_pago = 1;
  dias = intck('day', fecha_pago, today());
  mes_pago = put(fecha_pago, yymmn6.);
  tramo = put(edad, tramo.);
  if last.cliente_id then output;
run;
