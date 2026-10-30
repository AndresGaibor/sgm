/* priority: P1 | synthetic: report month context, sort and file output */
%let report_month = 202610;

proc import datafile="data/stage/customer_risk_scores.csv"
    out=work.customer_risk_scores
    dbms=csv replace;
    delimiter=';';
    getnames=yes;
    guessingrows=max;
run;

data work.current_risk_report;
    set work.customer_risk_scores;
    report_month = &report_month.;
    keep report_month customer_id customer_name region total_amount
         transaction_count debt_ratio utilization_ratio risk_score risk_level;
run;

proc sort data=work.current_risk_report;
    by descending risk_score customer_id;
run;

proc export data=work.current_risk_report
    outfile="data/stage/current_risk_report.csv"
    dbms=csv replace;
    delimiter=';';
    putnames=yes;
run;
