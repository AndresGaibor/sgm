/* priority: P1 */
proc export data=work.monthly_report outfile='/example/out/monthly.xlsx' dbms=xlsx replace; sheet='Summary'; run;
