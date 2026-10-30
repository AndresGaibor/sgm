/* priority: P1 */
libname db2lib db2 database=EXAMPLE schema=DEMO;
data db2lib.processed_events; set work.events; run;
