proc import datafile="/data/clientes.csv" out=work.clientes dbms=csv replace;
run;
proc sql;
  create table work.limpio as select id from work.clientes where saldo > 10;
quit;
proc export data=work.limpio outfile="/data/salida.csv" dbms=csv replace;
run;
