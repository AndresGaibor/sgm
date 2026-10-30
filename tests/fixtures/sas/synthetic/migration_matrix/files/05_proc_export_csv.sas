/* priority: P1 */
proc export data=work.customer_summary outfile='/example/out/customer_summary.csv' dbms=csv replace; putnames=yes; run;
