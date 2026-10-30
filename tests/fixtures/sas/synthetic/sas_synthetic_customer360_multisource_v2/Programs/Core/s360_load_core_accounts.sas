/* priority: P0 | Core source, account filter, calculation and deduplication */
proc import datafile="Data/Core/accounts.tsv"
    out=work.account_raw
    dbms=tab
    replace;
    getnames=yes;
    guessingrows=max;
run;

data work.account_open;
    set work.account_raw;
    if account_status = 'OPEN';
    utilization_pct = (balance / credit_limit) * 100;
run;

proc sort data=work.account_open out=work.account_unique nodupkey;
    by account_id;
run;

proc export data=work.account_unique
    outfile="Data/Stage/account_open.csv"
    dbms=csv
    replace;
    delimiter=';';
    putnames=yes;
run;
