/* priority: P0 | synthetic: file input, context, filter and derived field */
%let active_status_code = 1;

proc import datafile="data/customers.csv"
    out=work.customer_input
    dbms=csv replace;
    delimiter=';';
    getnames=yes;
    guessingrows=max;
run;

data work.customer_active;
    set work.customer_input;
    if status_code = &active_status_code.;
    annual_net_income = annual_income - (monthly_debt * 12);
run;

proc export data=work.customer_active
    outfile="data/stage/customers_active.csv"
    dbms=csv replace;
    delimiter=';';
    putnames=yes;
run;
