proc export data=work.origen outfile='salida.xlsx' dbms=xlsx replace;
  sheet='Resumen';
run;
