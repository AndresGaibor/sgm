/* priority: P0 | sintético: %INCLUDE estático y llamadas a macro */
%include 'inc/macros_comunes.sas';
libname dwh '/data/dwh';

%cargar(clientes);

data work.clientes_norm;
  set work.clientes;
  %limpiar_texto(nombre)
run;
