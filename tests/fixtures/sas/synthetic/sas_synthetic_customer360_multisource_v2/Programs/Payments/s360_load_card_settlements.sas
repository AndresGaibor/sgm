/* priority: P0 | Payment source, deduplication and amount/status filters */
%let min_settlement_amount = 20;

proc import datafile="Data/Payments/card_settlements.psv"
    out=work.settlement_raw
    dbms=dlm
    replace;
    delimiter='|';
    getnames=yes;
    guessingrows=max;
run;

proc sort data=work.settlement_raw out=work.settlement_unique nodupkey;
    by payment_id;
run;

data work.settlement_accepted;
    set work.settlement_unique;
    if settlement_status = 'SETTLED' and amount >= &min_settlement_amount.;
run;

proc export data=work.settlement_accepted
    outfile="Data/Stage/settlement_accepted.csv"
    dbms=csv
    replace;
    delimiter=';';
    putnames=yes;
run;
