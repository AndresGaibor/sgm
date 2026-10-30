/* priority: P0 | synthetic: file input, filter, sort and dedupe */
%let active_status_code = 1;

proc import datafile="data/accounts.csv"
    out=work.account_input
    dbms=csv replace;
    delimiter=';';
    getnames=yes;
    guessingrows=max;
run;

data work.account_active;
    set work.account_input;
    if status_code = &active_status_code.;
    if credit_limit > 0;
    utilization_ratio = balance / credit_limit;
run;

proc sort data=work.account_active out=work.account_unique nodupkey;
    by account_id;
run;

proc export data=work.account_unique
    outfile="data/stage/accounts_active.csv"
    dbms=csv replace;
    delimiter=';';
    putnames=yes;
run;
