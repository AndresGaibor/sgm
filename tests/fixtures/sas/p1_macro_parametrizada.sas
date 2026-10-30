/* priority: P1 | sintético: macro con parámetros, bucle %DO y condicional */
%macro extraer_mes(tabla=, desde=, hasta=);
  %do m = &desde. %to &hasta.;
    %if &m. < 10 %then %let mm = 0&m.; %else %let mm = &m.;
    proc sql;
      create table work.&tabla._&mm. as
      select * from dwh.&tabla.
      where month(fecha) = &m.;
    quit;
  %end;
%mend extraer_mes;

%extraer_mes(tabla=ventas, desde=1, hasta=12);
