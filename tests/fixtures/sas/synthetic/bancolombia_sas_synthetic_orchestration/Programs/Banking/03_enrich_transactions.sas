/* priority: P0 | synthetic: input, dedupe, INNER/LEFT joins and filters */
%let posted_status_code = 1;
%let minimum_transaction_amount = 100;

proc import datafile="data/transactions.csv"
    out=work.transaction_input
    dbms=csv replace;
    delimiter=';';
    getnames=yes;
    guessingrows=max;
run;

proc import datafile="data/stage/accounts_active.csv"
    out=work.accounts_active
    dbms=csv replace;
    delimiter=';';
    getnames=yes;
    guessingrows=max;
run;

proc import datafile="data/stage/customers_active.csv"
    out=work.customers_active
    dbms=csv replace;
    delimiter=';';
    getnames=yes;
    guessingrows=max;
run;

proc import datafile="data/merchant_categories.csv"
    out=work.merchant_categories
    dbms=csv replace;
    delimiter=';';
    getnames=yes;
    guessingrows=max;
run;

proc sort data=work.transaction_input out=work.transaction_unique nodupkey;
    by transaction_id;
run;

proc sql;
    create table work.transactions_enriched as
    select t.transaction_id,
           a.customer_id,
           c.customer_name,
           c.region,
           c.segment,
           t.transaction_date,
           t.merchant_category,
           m.category_description,
           t.amount,
           t.channel
      from work.transaction_unique as t
      inner join work.accounts_active as a
        on t.account_id = a.account_id
      inner join work.customers_active as c
        on a.customer_id = c.customer_id
      left join work.merchant_categories as m
        on t.merchant_category = m.merchant_category
     where t.status_code = &posted_status_code.
       and t.amount >= &minimum_transaction_amount.;
quit;

proc export data=work.transactions_enriched
    outfile="data/stage/transactions_enriched.csv"
    dbms=csv replace;
    delimiter=';';
    putnames=yes;
run;
