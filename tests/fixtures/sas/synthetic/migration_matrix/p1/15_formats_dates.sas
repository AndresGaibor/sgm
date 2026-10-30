/* priority: P1 */
data work.period; set work.events; length period $6; period=put(event_date,yymmn6.); format event_date date9.; run;
