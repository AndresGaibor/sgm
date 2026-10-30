/* priority: P0 */
proc sort data=work.transactions out=work.transactions_sorted; by region descending transaction_date customer_id; run;
