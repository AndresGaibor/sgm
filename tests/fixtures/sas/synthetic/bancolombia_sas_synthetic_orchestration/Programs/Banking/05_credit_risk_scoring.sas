/* priority: P1 | synthetic: multi-input SQL, context and row conditionals */
%let active_status_code = 1;
%let high_spend_threshold = 1000;
%let high_debt_ratio = 0.25;
%let high_utilization_ratio = 0.80;
%let risk_band_threshold = 25;

proc import datafile="data/stage/customer_metrics.csv"
    out=work.customer_metrics
    dbms=csv replace;
    delimiter=';';
    getnames=yes;
    guessingrows=max;
run;

proc import datafile="data/customers.csv"
    out=work.customer_source
    dbms=csv replace;
    delimiter=';';
    getnames=yes;
    guessingrows=max;
run;

proc import datafile="data/accounts.csv"
    out=work.account_source
    dbms=csv replace;
    delimiter=';';
    getnames=yes;
    guessingrows=max;
run;

proc sql;
    create table work.risk_base as
    select m.customer_id,
           m.customer_name,
           m.region,
           m.total_amount,
           m.transaction_count,
           c.annual_income,
           c.monthly_debt,
           a.balance,
           a.credit_limit
      from work.customer_metrics as m
      inner join work.customer_source as c
        on m.customer_id = c.customer_id
      inner join work.account_source as a
        on m.customer_id = a.customer_id
     where c.status_code = &active_status_code.
       and a.status_code = &active_status_code.;
quit;

data work.customer_risk_scores;
    set work.risk_base;
    length risk_level $8;
    debt_ratio = monthly_debt / (annual_income / 12);
    utilization_ratio = balance / credit_limit;
    risk_score = 0;
    if total_amount >= &high_spend_threshold. then risk_score = risk_score + 40;
    if debt_ratio >= &high_debt_ratio. then risk_score = risk_score + 35;
    if utilization_ratio >= &high_utilization_ratio. then risk_score = risk_score + 25;
    if risk_score >= 60 then risk_level = 'HIGH';
    else if risk_score >= &risk_band_threshold. then risk_level = 'MEDIUM';
    else risk_level = 'LOW';
run;

proc export data=work.customer_risk_scores
    outfile="data/stage/customer_risk_scores.csv"
    dbms=csv replace;
    delimiter=';';
    putnames=yes;
run;
