/* priority: P0 */
proc sort data=work.payments out=work.unique nodupkey; by payment_id; run;
