title "Reporte";
%put traza de ejecucion;
ods html close;
ods rtf (id=web) close;
data b;
  set a;
  z = 1;
run;
