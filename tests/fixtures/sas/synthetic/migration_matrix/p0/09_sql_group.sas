/* priority: P0 */
proc sql; create table work.totals as select customer_id,count(*) as n,sum(amount) as total from work.sales group by customer_id; quit;
