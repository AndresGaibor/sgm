/* priority: P1 */
proc freq data=work.customer_status; tables region*status / missing out=work.status_frequency; run;
