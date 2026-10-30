/* priority: P1 */
libname mysql mysql server='example.invalid' database=demo;
data work.active_products; set mysql.products; where enabled=1; run;
