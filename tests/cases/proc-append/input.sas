data destino;
    set inicial;
run;
proc append base=destino data=nuevos;
run;
