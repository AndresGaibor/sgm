/* priority: P1 */
proc sort data=work.month_rows; by customer_id; run;
proc transpose data=work.month_rows out=work.month_columns prefix=month_; by customer_id; id month_no; var monthly_amount; run;
