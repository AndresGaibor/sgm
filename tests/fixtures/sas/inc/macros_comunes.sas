/* priority: P0 | sintético: definición de macros incluidas */
%macro limpiar_texto(var);
  &var = upcase(strip(&var));
%mend limpiar_texto;

%macro cargar(tabla, destino=work);
  data &destino..&tabla.;
    set dwh.&tabla.;
  run;
%mend cargar;
