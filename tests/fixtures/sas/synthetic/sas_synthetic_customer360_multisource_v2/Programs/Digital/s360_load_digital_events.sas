/* priority: P0 | Digital source, consent filter and deduplication */
%let required_consent = Y;

proc import datafile="Data/Digital/digital_events.csv"
    out=work.event_raw
    dbms=csv
    replace;
    delimiter=';';
    getnames=yes;
    guessingrows=max;
run;

data work.event_consented;
    set work.event_raw;
    if consent = "&required_consent.";
run;

proc sort data=work.event_consented out=work.event_unique nodupkey;
    by event_id;
run;

proc export data=work.event_unique
    outfile="Data/Stage/event_consented.csv"
    dbms=csv
    replace;
    delimiter=';';
    putnames=yes;
run;
