/* priority: P0 */
proc sql; create table work.joined as select a.id,b.name from work.accounts a inner join work.customers b on a.customer_id=b.id; quit;
