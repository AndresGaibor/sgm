/* priority: P1 */
libname ora oracle path='EXAMPLE' schema=DEMO;
data ora.migrated_orders; set work.valid_orders; run;
