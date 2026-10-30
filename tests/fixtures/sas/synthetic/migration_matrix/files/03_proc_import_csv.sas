/* priority: P1 */
proc import datafile='/example/data/transactions.csv' out=work.transactions dbms=csv replace; getnames=yes; guessingrows=100; run;
