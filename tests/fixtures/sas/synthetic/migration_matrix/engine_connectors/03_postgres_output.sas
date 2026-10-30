/* priority: P1 */
libname pg postgres server='example.invalid' database=demo schema=public;
data pg.customer_snapshot; set work.customer_snapshot; run;
