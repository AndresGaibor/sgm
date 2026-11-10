data work.registros;
infile '/datos/registros.dat' lrecl=80;
input codigo $ 1-10 region $ 11-12 importe 13-24;
run;
