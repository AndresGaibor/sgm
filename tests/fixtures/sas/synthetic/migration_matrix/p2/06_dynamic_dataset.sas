/* priority: P2 */
%let suffix=%sysfunc(today(),yymmddn8.);
data work.snapshot_&suffix; set work.source; run;
