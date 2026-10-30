/* priority: P1 | Lee dos CSV, limpia, cruza con clientes por clave y exporta el resultado a CSV. */
%let dir_in = C:\datos\entrada;
%let dir_out = C:\datos\salida;

/* Lectura de pedidos con infile. */
data work.pedidos_raw;
  infile "&dir_in\pedidos.csv" dsd firstobs=2 truncover;
  length cliente $12 producto $20 canal $8 fecha_txt $10;
  input cliente $ producto $ canal $ cantidad precio fecha_txt $;
run;

/* Filtro, columnas calculadas y renombrado. */
data work.pedidos_ok;
  set work.pedidos_raw;
  where cantidad > 0 and not missing(precio);
  length prefijo $3;
  prefijo = substr(producto, 1, 3);
  importe = round(cantidad * precio, 0.01);
  if canal = 'WEB' then descuento = 0.05;
  else if canal = 'TIENDA' then descuento = 0.02;
  else descuento = 0;
  importe_neto = importe * (1 - descuento);
  rename cliente = cod_cliente producto = cod_producto;
run;

/* Duplicados por cliente y producto: se conserva una fila. */
proc sort data=work.pedidos_ok out=work.pedidos_dedup nodupkey;
  by cod_cliente cod_producto;
run;

/* Lectura del maestro de clientes con proc import. */
proc import datafile="&dir_in\clientes.csv" out=work.clientes dbms=csv replace;
  getnames=yes;
run;

proc sort data=work.clientes;
  by cod_cliente;
run;

proc sort data=work.pedidos_dedup;
  by cod_cliente;
run;

/* Cruce por clave: solo pedidos con cliente conocido. */
data work.pedidos_region;
  merge work.pedidos_dedup(in=p) work.clientes(in=c keep=cod_cliente nombre region);
  by cod_cliente;
  if p and c;
run;

/* Salida a CSV. */
proc export data=work.pedidos_region
  outfile="&dir_out\pedidos_region.csv"
  dbms=csv replace;
run;
