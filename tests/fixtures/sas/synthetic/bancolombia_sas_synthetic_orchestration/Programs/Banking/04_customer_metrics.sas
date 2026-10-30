/* priority: P0 | synthetic: SQL aggregation, GROUP BY, HAVING and context */
%let minimum_customer_volume = 300;

proc import datafile="data/stage/transactions_enriched.csv"
    out=work.transactions_enriched
    dbms=csv replace;
    delimiter=';';
    getnames=yes;
    guessingrows=max;
run;

proc sql;
    create table work.customer_metrics as
    select customer_id,
           customer_name,
           region,
           sum(amount) as total_amount,
           count(*) as transaction_count,
           max(amount) as largest_transaction
      from work.transactions_enriched
     group by customer_id, customer_name, region
    having calculated total_amount >= &minimum_customer_volume.;
quit;

proc export data=work.customer_metrics
    outfile="data/stage/customer_metrics.csv"
    dbms=csv replace;
    delimiter=';';
    putnames=yes;
run;
