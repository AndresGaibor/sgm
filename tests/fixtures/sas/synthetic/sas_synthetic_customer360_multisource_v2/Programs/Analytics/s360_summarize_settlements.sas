/* priority: P0 | INNER join of accounts and settlements; group by customer */
proc import datafile="Data/Stage/account_open.csv"
    out=work.account_open
    dbms=csv
    replace;
    delimiter=';';
    getnames=yes;
    guessingrows=max;
run;

proc import datafile="Data/Stage/settlement_accepted.csv"
    out=work.settlement_accepted
    dbms=csv
    replace;
    delimiter=';';
    getnames=yes;
    guessingrows=max;
run;

proc sql;
    create table work.customer_payment_summary as
    select a.customer_id,
           count(p.payment_id) as settled_payment_count,
           sum(p.amount) as total_settled_amount
      from work.account_open as a
      inner join work.settlement_accepted as p
        on a.account_id = p.account_id
     group by a.customer_id;
quit;

proc export data=work.customer_payment_summary
    outfile="Data/Stage/customer_payment_summary.csv"
    dbms=csv
    replace;
    delimiter=';';
    putnames=yes;
run;
