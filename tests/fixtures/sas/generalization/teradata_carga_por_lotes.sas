/* priority: P1 | Carga por lotes a Teradata: troceo, comandos de sistema, espera y mensajes de control. */
%let ruta_lotes = /data/lotes/td;
%let filas_lote = 500000;
%let usuario_td = etl_ops;

libname td teradata server=tdprod user=&usuario_td database=dwh_ops;
libname src "/data/lz";

%macro cargar_tabla(origen=, destino=);
  %local n_lotes i inicio fin filas_td;
  %let t0 = %sysfunc(datetime());

  /* Número de lotes según el tamaño del origen. */
  proc sql noprint;
    select ceil(count(*) / &filas_lote) into :n_lotes trimmed from &origen;
  quit;

  /* Troceo por lotes: cada vuelta inserta un rango de filas. */
  %do i = 1 %to &n_lotes;
    %let inicio = %eval((&i - 1) * &filas_lote);
    proc sql;
      insert into td.&destino
      select * from &origen (firstobs=%eval(&inicio + 1) obs=%eval(&inicio + &filas_lote));
    quit;
  %end;

  /* Validación externa por línea de comandos. */
  %let cmd = sh /opt/etl/validar_carga.sh &destino;
  x "&cmd";

  /* Espera de la validación externa: sondeo con sleep. */
  %let fin = 0;
  %do %while (&fin = 0);
    data _null_;
      rc = sleep(2);
      call symputx('fin', 1);
    run;
  %end;

  /* Listado de lotes generados, leído por filename pipe. */
  filename lista pipe "ls &ruta_lotes";
  data _null_;
    infile lista;
    input nombre_lote $ 1-200;
    put "lote: " nombre_lote;
  run;

  proc sql noprint;
    select count(*) into :filas_td trimmed from td.&destino;
  quit;

  %put NOTE: &destino cargada con &filas_td filas;
  %put NOTE: tiempo total %sysevalf(%sysfunc(datetime()) - &t0) segundos;
%mend cargar_tabla;

/* Tres cargas contra la misma base: mismo bloque, distintas tablas. */
%cargar_tabla(origen=src.clientes_lz, destino=clientes);
%cargar_tabla(origen=src.productos_lz, destino=productos);
%cargar_tabla(origen=src.facturas_lz, destino=facturas);

%put NOTE: cargas a Teradata finalizadas;
