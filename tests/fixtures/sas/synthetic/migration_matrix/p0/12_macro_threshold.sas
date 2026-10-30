/* priority: P0 */
%let min_amount=25;
data work.large_sales; set work.sales; where amount>=&min_amount; run;
