/* priority: P2 | sintético: CALL EXECUTE, X, SYSTASK, referencias dinámicas */
data _null_;
  set work.tablas_a_procesar;
  call execute(cats('%nrstr(%procesar(tabla=', nombre, '))'));
run;

x 'cp /data/out/reporte.csv /archivo/historico/';
systask command "gzip /data/out/reporte.csv" wait;

%let n = 3;
%let t1 = ventas; %let t2 = pagos; %let t3 = clientes;
%macro bucle;
  %do i = 1 %to &n.;
    proc contents data=dwh.&&t&i.; run;
  %end;
%mend;
%bucle;
