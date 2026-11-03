/* Programa sintético independiente: inventario mensual de sucursales.
   No se usó para diseñar reglas; sirve para comprobar que el compilador generaliza. */
%let mes = 202501;

data work.existencias;
  set src.existencias;
  where sucursal ne '';
  stock_neto = cantidad - devoluciones;
run;

proc sort data=work.existencias out=work.existencias_ord;
  by sucursal producto;
run;

data work.precios_vigentes;
  merge work.existencias_ord(in=en_stock) src.precios(in=en_precio);
  by sucursal producto;
  if en_stock and en_precio;
  valor = stock_neto * precio;
run;

proc means data=work.precios_vigentes noprint;
  class sucursal;
  var valor;
  output out=work.resumen_sucursal sum=valor_total;
run;

data out.inventario_&mes;
  set work.resumen_sucursal;
run;
