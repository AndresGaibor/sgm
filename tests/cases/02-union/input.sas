proc import datafile='a.csv' out=work.a dbms=csv; run;
proc import datafile='b.csv' out=work.b dbms=csv; run;
proc append base=work.a data=work.b;
run;
