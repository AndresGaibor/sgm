/* priority: P1 | Reporte de ventas: una macro usada una vez (se expande en línea) y otra usada tres veces. */
libname rep "/data/reportes";

/* Usada una sola vez: solo fija título y pie. */
%macro encabezado(titulo);
  title "&titulo";
  footnote "Generado el %sysfunc(today(), date9.)";
%mend encabezado;

/* Usada tres veces con parámetros distintos. */
%macro resumen_region(region=, medida=, salida=);
  proc sort data=rep.ventas(where=(region = "&region")) out=rep.orden_&salida;
    by sucursal;
  run;

  proc means data=rep.orden_&salida noprint nway;
    class sucursal;
    var &medida;
    output out=rep.res_&salida sum=total mean=promedio;
  run;
%mend resumen_region;

%encabezado(Ventas por region);

%resumen_region(region=NORTE, medida=importe, salida=norte);
%resumen_region(region=SUR, medida=importe, salida=sur);
%resumen_region(region=ESTE, medida=unidades, salida=este);

/* Listado final del resumen norte. */
proc print data=rep.res_norte noobs;
  var sucursal total promedio;
run;

/* Comentario sin efecto: %macro pendiente de retirar.
%resumen_region(region=OESTE, medida=importe, salida=oeste);
*/
