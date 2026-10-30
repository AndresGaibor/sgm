/* priority: P1 */
proc format; value statusfmt 1='OPEN' 2='CLOSED' other='UNKNOWN'; run;
data work.labeled; set work.accounts; status_label=put(status_code,statusfmt.); run;
