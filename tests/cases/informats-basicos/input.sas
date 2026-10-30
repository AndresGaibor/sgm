data b;
  set a;
  n = input(texto, 8.);
  d = input(fecha_txt, yymmdd8.);
  c = put(valor, $10.);
run;
