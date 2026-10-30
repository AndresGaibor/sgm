/* priority: P0 | CRM source, active customer filter and annual income */
%let minimum_monthly_income = 1800;

proc import datafile="Data/CRM/customer_master.csv"
    out=work.customer_raw
    dbms=csv
    replace;
    delimiter=',';
    getnames=yes;
    guessingrows=max;
run;

data work.customer_active;
    set work.customer_raw;
    if customer_status = 'ACTIVE' and monthly_income >= &minimum_monthly_income.;
    annual_income = monthly_income * 12;
run;

proc export data=work.customer_active
    outfile="Data/Stage/customer_active.csv"
    dbms=csv
    replace;
    delimiter=';';
    putnames=yes;
run;
