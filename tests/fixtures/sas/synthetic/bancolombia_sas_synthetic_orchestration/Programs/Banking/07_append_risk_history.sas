/* priority: P1 | synthetic: append, sort and final file output */
proc import datafile="data/prior_risk_history.csv"
    out=work.risk_history
    dbms=csv replace;
    delimiter=';';
    getnames=yes;
    guessingrows=max;
run;

proc import datafile="data/stage/current_risk_report.csv"
    out=work.current_risk_report
    dbms=csv replace;
    delimiter=';';
    getnames=yes;
    guessingrows=max;
run;

proc append base=work.risk_history data=work.current_risk_report force;
run;

proc sort data=work.risk_history;
    by report_month customer_id;
run;

proc export data=work.risk_history
    outfile="output/risk_history.csv"
    dbms=csv replace;
    delimiter=';';
    putnames=yes;
run;
