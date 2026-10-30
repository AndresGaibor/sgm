/* priority: P1 */
libname pg postgres server='example.invalid' database=demo schema=public;
proc sql; create table work.active_customers as select customer_id from pg.customers where active='Y'; quit;
