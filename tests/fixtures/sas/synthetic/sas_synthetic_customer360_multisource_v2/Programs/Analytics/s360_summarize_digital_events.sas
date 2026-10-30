/* priority: P0 | Event aggregation by customer */
proc import datafile="Data/Stage/event_consented.csv"
    out=work.event_consented
    dbms=csv
    replace;
    delimiter=';';
    getnames=yes;
    guessingrows=max;
run;

proc sql;
    create table work.customer_event_summary as
    select customer_id,
           count(event_id) as digital_event_count
      from work.event_consented
     group by customer_id;
quit;

proc export data=work.customer_event_summary
    outfile="Data/Stage/customer_event_summary.csv"
    dbms=csv
    replace;
    delimiter=';';
    putnames=yes;
run;
