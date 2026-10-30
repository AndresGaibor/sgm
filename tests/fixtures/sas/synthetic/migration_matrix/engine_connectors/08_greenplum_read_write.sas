/* priority: P1 */
libname gp greenplm server='example.invalid' database=demo schema=public;
data work.gp_customers; set gp.customers; run;
data gp.customer_snapshot; set work.gp_customers; run;
