/* priority: P2 | salida agregada del proyecto sintético Customer 360. */
%let snapshot_period = 202610;

proc import datafile="Data/Stage/customer_active.csv"
    out=work.customer_active
    dbms=csv
    replace;
    delimiter=';';
    getnames=yes;
    guessingrows=max;
run;

proc import datafile="Data/Stage/customer_payment_summary.csv"
    out=work.payment_summary
    dbms=csv
    replace;
    delimiter=';';
    getnames=yes;
    guessingrows=max;
run;

proc import datafile="Data/Stage/customer_event_summary.csv"
    out=work.event_summary
    dbms=csv
    replace;
    delimiter=';';
    getnames=yes;
    guessingrows=max;
run;

proc sql;
    create table work.customer360_base as
    select c.customer_id,
           c.customer_name,
           c.segment,
           c.region,
           c.annual_income,
           coalesce(p.settled_payment_count, 0) as settled_payment_count,
           coalesce(p.total_settled_amount, 0) as total_settled_amount,
           coalesce(e.digital_event_count, 0) as digital_event_count
      from work.customer_active as c
      left join work.payment_summary as p
        on c.customer_id = p.customer_id
      left join work.event_summary as e
        on c.customer_id = e.customer_id;
quit;

data work.customer360_snapshot;
    set work.customer360_base;
    activity_score = total_settled_amount + (digital_event_count * 10);
    period_code = "&snapshot_period.";
run;

proc export data=work.customer360_snapshot
    outfile="Output/customer360_snapshot.csv"
    dbms=csv
    replace;
    delimiter=';';
    putnames=yes;
run;
