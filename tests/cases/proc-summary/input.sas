proc summary data=ventas out=resumen;
  class region;
  var importe;
run;
