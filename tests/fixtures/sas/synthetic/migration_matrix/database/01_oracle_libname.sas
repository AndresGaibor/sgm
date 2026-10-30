/* priority: P1 */
libname ora oracle path='EXAMPLE' schema=DEMO;
data work.open_orders; set ora.orders; where order_status='OPEN'; run;
